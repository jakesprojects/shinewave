import argparse
from itertools import chain
from threading import Lock

from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import requests

from jakenode.database_connector import run_query
from run_node_app import run_node_app


parser = argparse.ArgumentParser()
parser.add_argument("-aid", "--account-id", dest="account_id", default="1", help="Account ID")
parser.add_argument(
    "-wcid", "--workflow-category-id", dest="workflow_category_id", default="1", help="Workflow Category ID"
)
parser.add_argument(
    "-wid", "--workflow-id", dest="workflow_id", default="1", help="Workflow ID"
)

args = parser.parse_args()
account_id = int(args.account_id)
workflow_category_id = int(args.workflow_category_id)
workflow_id = int(args.workflow_id)

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# Functions to handle port assignment
def invert_address_types(address_types):
    column_types = {}
    for address_type, column_list in address_types.items():
        for column_name in column_list:
            column_types[column_name] = address_type
    return column_types


def generate_fetch_query(columns, destination_server):
    address_select_clause = f",\n            ".join(columns)

    return f"""
        SELECT
            {address_select_clause}
        FROM workflow_routes
        WHERE
            app_server_address='{destination_server}'
    """


def fetch_taken_addresses(column_types, destination_server):
            
    query = generate_fetch_query(column_types.keys(), destination_server)
    
    taken_addresses = run_query(query, return_data_format=dict)
    filtered_taken_addresses = {}
    for column_name, address_type in column_types.items():
        filtered_taken_addresses.setdefault(address_type, [])
        filtered_taken_addresses[address_type] += [i for i in taken_addresses[column_name] if isinstance(i, int)]

    return filtered_taken_addresses


def assign_next_port(workflow_id):
    DESTINATION_SERVER = 'localhost'
    
    address_search_ranges = {
        'ports': (49152, 65535),
        'websockets': (49152, 65535),
        'x11_displays': (0, 99)
    }
    
    address_types = {
        'ports': ['xpra_port', 'info_panel_port'],
        'websockets': ['websocket'],
        'x11_displays': ['x11_display']
    }
    
    column_types = invert_address_types(address_types)

    workflow_addresses = run_query(
        f"""
            {generate_fetch_query(chain(*address_types.values()), DESTINATION_SERVER)}
            AND workflow_id={workflow_id}
        """,
        return_data_format=dict
    )
    
    taken_address_dict = fetch_taken_addresses(column_types, DESTINATION_SERVER)
    update_column_dict = {}

    for column_name in column_types:
        if not workflow_addresses[column_name][0]:
            address_type = column_types[column_name]
            taken_addresses = taken_address_dict[address_type]
            current_address, max_allowable_address = address_search_ranges[address_type]
            assigned_address = None
            
            max_value_err_msg = f'Cannot assign {address_type}.'
            max_value_err_msg += f'All values {current_address}-{max_allowable_address} already taken.'
            
            while assigned_address is None:
                if current_address > max_allowable_address:
                    raise Exception(max_value_err_msg)
                elif current_address not in taken_addresses:
                    assigned_address = current_address
                else:
                    current_address += 1
            update_column_dict[column_name] = assigned_address
            

    if update_column_dict:
        set_clause = []
        for column_name, set_value in update_column_dict.items():
            set_clause.append(f'{column_name}={set_value}')
        set_clause = ',\n            '.join(set_clause)
        update_statement = f"""
            UPDATE workflow_routes
            SET
                {set_clause}
            ;
        """
        print(update_statement)
        run_query(update_statement, commit=True)


def run_two_window_app(
    socketio=socketio,
    thread_lock=thread_lock,
    account_id=account_id,
    workflow_category_id=workflow_category_id,
    workflow_id=workflow_id
):


    def background_thread(
        socketio=socketio, account_id=account_id, workflow_category_id=workflow_category_id, workflow_id=workflow_id
    ):
        run_node_app(
            socketio=socketio, account_id=account_id, workflow_category_id=workflow_category_id, workflow_id=workflow_id
        )

    @app.route('/')
    def index():
        return render_template('index.html', async_mode=socketio.async_mode)

    @socketio.event
    def my_event(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('info_update', {'data': message['data'], 'count': session['receive_count']})

    # Receive the test request from client and send back a test response
    @socketio.on('test_message')
    def handle_message(data):
        print('received message: ' + str(data))
        emit('test_response', {'data': 'Test response sent'})

    # Broadcast a message to all clients
    @socketio.on('broadcast_message')
    def handle_broadcast(data):
        print('received: ' + str(data))
        emit('broadcast_response', {'data': 'Broadcast sent'}, broadcast=True)

    @socketio.event
    def connect():
        global thread
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(background_thread)
        emit('my_response', {'data': 'Connected', 'count': 0})

    socketio.run(app, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_two_window_app()