import argparse
from threading import Lock

from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import requests

from run_node_app import run_node_app


parser = argparse.ArgumentParser()
parser.add_argument("-aid", "--account-id", dest="account_id", default="1", help="Account ID")
parser.add_argument(
    "-wcid", "--workflow-category-id", dest="workflow_category_id", default="1", help="Workflow Category ID"
)

args = parser.parse_args()
account_id = int(args.account_id)
workflow_category_id = int(args.workflow_category_id)

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

def run_two_window_app(
    socketio=socketio, thread_lock=thread_lock, account_id=account_id, workflow_category_id=workflow_category_id
):


    def background_thread(socketio=socketio, account_id=account_id, workflow_category_id=workflow_category_id):
        run_node_app(socketio=socketio)

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