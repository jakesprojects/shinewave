from pathlib import Path

import pandas as pd

APP_HANDLER_PATH = '/srv/node_app'
APP_DATA_PATH = f'{APP_HANDLER_PATH}/data'
TEMPLATES_PATH = f'{APP_DATA_PATH}/templates'


def send_file_upload(account_id, upload_id, upload_file, upload_type, local_parent_folder=f'{APP_DATA_PATH}/file_uploads'):
    if local_parent_folder:
        local_folder = f'{local_parent_folder}/{account_id}/{upload_type}'
        Path(local_folder).mkdir(parents=True, exist_ok=True)

        file_path = f'{local_folder}/{upload_id}'
        if isinstance(upload_file, str):
            with open(file_path, 'w+') as file:
                file.write(upload_file)
        else:
            upload_file.save(file_path)


def read_upload(account_id, upload_id, upload_type, local_parent_folder=f'{APP_DATA_PATH}/file_uploads'):
    if local_parent_folder:
        with open(f'{local_parent_folder}/{account_id}/{upload_type}/{upload_id}', 'r') as file:
            return file.read()


def edit_template(
    contents, node_parent_type, node_detail_type, workflow_category, template_id, templates_folder_path=TEMPLATES_PATH
):
    template_filepath_components = [templates_folder_path, node_parent_type, node_detail_type, workflow_category]

    template_filepath = '/'.join(template_filepath_components)
    Path(template_filepath).mkdir(parents=True, exist_ok=True)
    template_filepath += f'/{template_id}.txt'

    with open(template_filepath, 'w+') as template_file:
        template_file.write(contents)


def fetch_template(
    node_parent_type, node_detail_type, workflow_category, template_id, templates_folder_path=TEMPLATES_PATH
):
    template_filepath_components = [
        templates_folder_path, node_parent_type, node_detail_type, workflow_category, str(template_id)
    ]

    template_filepath = '/'.join(template_filepath_components) + '.txt'
    with open(template_filepath, 'r') as template_file:
        template_file_contents = template_file.read()
    return template_file_contents
