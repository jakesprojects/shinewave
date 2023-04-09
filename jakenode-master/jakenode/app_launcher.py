import subprocess


LAUNCH_SCRIPT_FILEPATH = '/srv/node_app/run_two_window_app.py'

ACCOUNT_ID = 1
WORKFLOW_CATEGORY_ID = 2
WORKFLOW_ID = 2
X11_SCREEN = 80
XPRA_TARGET_PORT = '8080'
USER = 'myuser'


def run_xpra_window(
    queue=None,
    account_id=ACCOUNT_ID,
    workflow_category_id=WORKFLOW_CATEGORY_ID,
    workflow_id=WORKFLOW_ID,
    x11_screen=X11_SCREEN,
    xpra_target_port=XPRA_TARGET_PORT,
    user=USER,
    launch_script_filepath=LAUNCH_SCRIPT_FILEPATH
):
    script_target_flags = [
        f'--account-id {account_id}',
        f'--workflow-category-id {workflow_category_id}',
        f'--workflow-id {workflow_id}'
    ]

    script_target_flags = ' '.join(script_target_flags)
    script_target = f'{launch_script_filepath} {script_target_flags}'

    current_working_directory = subprocess.check_output('pwd')
    current_working_directory = current_working_directory.decode().strip()
    script_filepath = f'{current_working_directory}/{script_target}'

    base_command = f'xpra start :{x11_screen}'
    flags = [
        f'--bind-tcp=0.0.0.0:{xpra_target_port}',
        '--mdns=no',
        '--webcam=no',
        '--encoding=h264',
        '--auto-refresh-delay=.01',
        '--input-method=keep',
        # '--no-daemon',
        '--pulseaudio=no',
        '--min-quality=90',
        f'--start="python3 {script_filepath}"'
    ]

    flags = ' '.join(flags)

    command = f"su myuser -c '{base_command} {flags}'"
    print(command)
    subprocess.call(command, shell=True)


run_xpra_window(None)
