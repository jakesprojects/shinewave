import csv
import os
import sqlite3

import pandas as pd


APP_HANDLER_PATH = '/srv/node_app/handlers'
APP_DATA_PATH = f'{APP_HANDLER_PATH}/data'
DATABASE = f'{APP_DATA_PATH}/test_db.db'

def run_query(sql, return_data_format=list, commit=False, database_connection_type='sqlite', database=DATABASE):
    with sqlite3.connect(database) as conn:
        cur = conn.cursor()
        cur.execute(sql)

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
        
        create_and_insert_statement = f'{create_statement}\n{insert_statement}'

        run_query_kwargs = {
            'commit': True,
            'database_connection_type': 'sqlite',
            'database': DATABASE
        }
        print(drop_statement)
        run_query(drop_statement, **run_query_kwargs)
        print(create_and_insert_statement)
        run_query(create_and_insert_statement, **run_query_kwargs)
