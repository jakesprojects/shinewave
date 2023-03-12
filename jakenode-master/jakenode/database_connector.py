import csv
import os
from pathlib import Path
import sqlite3

import pandas as pd


APP_HANDLER_PATH = '/srv/node_app'
APP_DATA_PATH = f'{APP_HANDLER_PATH}/data'
DATABASE = f'{APP_DATA_PATH}/test_db.db'
TEMPLATES_PATH = f'{APP_DATA_PATH}/templates'

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

def edit_template(
    contents, node_parent_type, node_detail_type, workflow_category, template_id, templates_folder_path=TEMPLATES_PATH
):
    template_filepath_components = [templates_folder_path, node_parent_type, node_detail_type, workflow_category]

    template_filepath = '/'.join(template_filepath_components)
    Path(template_filepath).mkdir(parents=True, exist_ok=True)
    template_filepath += f'/{template_id}.txt'

    with open(template_filepath, 'w+') as template_file:
        template_file.write(contents)

def run_query(
    sql, return_data_format=list, commit=False, database_connection_type='sqlite', database=DATABASE, sql_parameters=[]
):
    if database_connection_type == 'sqlite':
        with sqlite3.connect(database) as conn:
            cur = conn.cursor()
            cur.execute(sql, sql_parameters)

            if commit == True:
                conn.commit()
                return None

            rows = cur.fetchall()
            column_names = [i[0] for i in cur.description]

        if return_data_format is list:
            return rows

        elif return_data_format is dict:
            results_dict = {}
            for n, column_name in enumerate(column_names):
                results_dict[column_name] = []
                for row in rows:
                    results_dict[column_name].append(row[n])
            return results_dict

def build_dummy_data(database_connection_type='sqlite', app_data_path=APP_DATA_PATH, database=DATABASE):

    table_csv_path = f'{app_data_path}/table_csvs'
    schema_files = []
    data_files = []

    for folder, subfolders, files in os.walk(table_csv_path):
        for filename in files:
            if filename.endswith('_data.csv'):
                data_files.append(filename)
            elif filename.endswith('.csv'):
                schema_files.append(filename)
                
    for schema_filename in schema_files:
        table_name = schema_filename.rsplit('.csv', 1)[0]
        data_filename = f'{table_name}_data.csv'
        df = pd.read_csv(f'{table_csv_path}/{schema_filename}')
        df = df.unstack().unstack()
        df.columns = ['col_type']
        
        create_statement_rows = []
        insert_statement_rows = []
        
        drop_statement = f'DROP TABLE IF EXISTS {table_name};'
        for i in df.index:
            create_statement_rows.append(f"    {i} {df.loc[i,'col_type']}")
        create_statement_rows = ',\n'.join(create_statement_rows)
        create_statement = f'CREATE TABLE {table_name} (\n{create_statement_rows}\n);'

        if data_filename in data_files:
            with open(f'{table_csv_path}/{data_filename}', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    row = "', '".join(row)
                    row = f"('{row}')"
                    insert_statement_rows.append(row)
            insert_statement_rows = insert_statement_rows[1:]
            insert_statement_rows = ',\n'.join(insert_statement_rows)
            insert_statement = f'INSERT INTO {table_name} VALUES\n{insert_statement_rows}\n;'
        else:
            insert_statement = ''

        run_query_kwargs = {
            'commit': True,
            'database_connection_type': 'sqlite',
            'database': DATABASE
        }
        print(drop_statement)
        run_query(drop_statement, **run_query_kwargs)
        print(create_statement)
        run_query(create_statement, **run_query_kwargs)
        print(insert_statement)
        run_query(insert_statement, **run_query_kwargs)
