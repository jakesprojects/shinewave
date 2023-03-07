from datetime import datetime
from itertools import chain
import json
from multiprocessing import Process, Queue
import re
import subprocess

from flask import Flask, request

from jakenode.database_connector import run_query
# from run_two_window_app import run_two_window_app

ACCOUNT_ID = 1
LAUNCHER_PORT = 49151

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
            AND active = 'TRUE'
    """
    
def fetch_taken_addresses(column_types, destination_server):
            
    query = generate_fetch_query(column_types.keys(), destination_server)
    
    taken_addresses = run_query(query, return_data_format=dict)
    filtered_taken_addresses = {}
    for column_name, address_type in column_types.items():
        filtered_taken_addresses.setdefault(address_type, [])
        filtered_taken_addresses[address_type] += [i for i in taken_addresses[column_name] if isinstance(i, int)]

    return filtered_taken_addresses

def fetch_address_info(account_id, workflow_id):
    workflow_info = run_query(
        f"""
            SELECT *
            FROM workflows
            WHERE
                account_id = ?
                AND active = 'TRUE'
                AND id = ?
        """,
        sql_parameters=(account_id, workflow_id),
        return_data_format=list
    )

    if not workflow_info:
        raise ValueError("No workflow exists for provided IDs")

    address_info = run_query(
        f"""
            SELECT *
            FROM workflow_routes
            WHERE
                account_id = ?
                AND active = 'TRUE'
                AND workflow_id = ?
        """,
        sql_parameters=(account_id, workflow_id),
        return_data_format=dict
    )
    return address_info

def assign_next_port(workflow_id, destination_server):
    
    address_search_ranges = {
        'ports': (49152, 65535),
        'websockets': (49152, 65535),
        'x11_displays': (80, 1000)
    }
    
    address_types = {
        'ports': ['xpra_port', 'info_panel_port'],
        'websockets': ['websocket'],
        'x11_displays': ['x11_display']
    }
    
    column_types = invert_address_types(address_types)

    workflow_addresses = run_query(
        f"""
            {generate_fetch_query(chain(*address_types.values()), destination_server)}
            AND workflow_id = ?
        """,
        sql_parameters=[workflow_id],
        return_data_format=dict
    )

    taken_address_dict = fetch_taken_addresses(column_types, destination_server)
    print(taken_address_dict)
    update_column_dict = {}
    
    if not list(chain(*workflow_addresses.values())):
        # If no values are returned by query, do this:
        for column_name in workflow_addresses:
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
                    taken_address_dict[address_type].append(assigned_address)
                else:
                    current_address += 1
            update_column_dict[column_name] = assigned_address
        return update_column_dict

# Functions for Flask app
def extract_ip_address():
    ifconfig = subprocess.check_output('ifconfig eth0', shell=True).decode()
    extracted_text = re.findall(r'\Winet ([0-9]{3}\.[0-9]{2}(?:\.[0-9]{3}){2})\W', ifconfig)
    return extracted_text[0]


def run_xpra_window(queue, account_id, workflow_category_id, x11_screen, xpra_target_port, info_panel_port, workflow_id):
    base_script_flags = [
        f'--account-id {account_id}',
        f'--workflow-category-id {workflow_category_id}',
        f'--workflow-id {workflow_id}',
        f'--info-panel-port {info_panel_port}'
    ]
    base_script_flags = ' '.join(base_script_flags)

    script_target = f'run_two_window_app.py {base_script_flags}'
    user = 'myuser'
    
    current_working_directory = subprocess.check_output('pwd')
    current_working_directory = current_working_directory.decode().strip()
    script_filepath = f'{current_working_directory}/{script_target}'

    base_command = f'xpra start :{x11_screen}'
    flags = [
        f'--bind-tcp=0.0.0.0:{xpra_target_port}',
        '--mdns=no',
        '--webcam=no',
        '--pulseaudio=no',
        '--min-quality=90',
        '--sharing=yes',
        '--file-transfer=off',
        '--window-close=ignore',
        '--tray=no',
        '--system-tray=off',
        '--video-scaling=100',
        f'--start="python3 {script_filepath}"'
    ]
    
    flags = ' '.join(flags)
     
    command = f"su myuser -c '{base_command} {flags}'"
    print(command)
    subprocess.call(command, shell=True)
    return extract_ip_address()

APP_HANDLER_PATH = '/srv/node_app/handlers'
DATABASE = f'{APP_HANDLER_PATH}/data/test_db.db'

app = Flask('app_launcher')

@app.route('/app_launcher', methods=["POST"])
def app_launcher():
    request_data = json.loads(request.data)
    account_id = ACCOUNT_ID
    workflow_id = request_data.get('workflow_id')
    workflow_category_id = run_query(
        sql="""
            SELECT workflow_category_id
            FROM workflows
            WHERE
                active = 'TRUE'
                AND id = ?
                AND account_id = ?
        """,
        sql_parameters=(workflow_id, account_id),
        return_data_format=list
    )[0][0]

    # Not implemented yet, but will be needed
    security_token = request_data.get('security_token')

    address_info = fetch_address_info(account_id, workflow_id)
    if not list(chain(*address_info.values())):
        """
            If no values are returned by query, we will:
                1. Insert a row into the workflow_routes table
                2. Launch the corresponding app instance
        """
        app_server_address = extract_ip_address()
        insert_columns = ['id', 'account_id', 'workflow_id', 'app_server_address', 'active', 'last_activity']
        insert_values = [account_id, workflow_id, app_server_address, 'TRUE', str(datetime.now())]

        assign_port_dict = assign_next_port(workflow_id, app_server_address)
        for column_name, value in assign_port_dict.items():
            insert_columns.append(column_name)
            insert_values.append(value)
        
        insert_substitutions = ['?' for i in insert_values]

        insert_statement = f"""
            INSERT INTO workflow_routes ({', '.join(insert_columns)})
            VALUES (
                (SELECT MAX(id) + 1 FROM workflow_routes),
                {', '.join(insert_substitutions)}
            )
        """

        # Create entry in DB for app instance
        run_query(insert_statement, sql_parameters=insert_values, commit=True)

        # LAUNCH APP HERE
        run_xpra_window(
            queue=None,
            account_id=account_id,
            workflow_category_id=workflow_category_id,
            x11_screen=assign_port_dict['x11_display'],
            xpra_target_port=assign_port_dict['xpra_port'],
            info_panel_port=assign_port_dict['info_panel_port'],
            workflow_id=workflow_id
        )
        # END LAUNCH APP

        assign_port_dict['app_server_address'] = app_server_address
        return json.dumps(assign_port_dict)
    else:
        address_info = {key: value[0] for key, value in address_info.items()}
        return json.dumps(address_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=LAUNCHER_PORT)
