import csv
from datetime import datetime
import hashlib
from itertools import chain
import os
from random import randint
import re
import sqlite3

import pandas as pd
from sqlalchemy import create_engine 


"""
To do:
    1. Fix bad parameterization of PSQL queries.
    2. Delete fixed passwords/usernames. Burn the old passwords.
"""

APP_HANDLER_PATH = '/srv/node_app'
APP_DATA_PATH = f'{APP_HANDLER_PATH}/data'

# New Settings - make sure to change all connection info before going to production
DEFAULT_CONNECTION_TYPE = 'postgres'
DATABASE = 'shinewavebackend'
HOST = ''
PASSWORD = ''
PORT = 5432
USERNAME = ''

# Old Settings
# DEFAULT_CONNECTION_TYPE = 'sqlite'
# DATABASE = f'{APP_DATA_PATH}/test_db.db'
# HOST = None
# PASSWORD = None
# PORT = None
# USERNAME = None


def sqlite_to_psql(sql):
    for char in '{}':
        sql = sql.replace(char, char * 2)

    master_quote_replacement_ptrn = r'(.*?\?)'
    quote_replacement_types = [('double', '"'), ('single', "'")]
    replacement_dict = {}

    for pattern_name, replacement_type in quote_replacement_types:
        replacement_ptrn = f'{replacement_type}{master_quote_replacement_ptrn}{replacement_type}'
        replacements = re.findall(replacement_ptrn, sql)
        replacement_count = 0
        while replacements:
            placeholder = f'{pattern_name}_{replacement_count}'
            replacement_dict[placeholder] = replacements.pop(0)
            sql = re.sub(replacement_ptrn, f'{replacement_type}{{{placeholder}}}{replacement_type}', sql, 1)
            replacement_count += 1
    sql = sql.replace('?', r'%s')
    return sql.format(**replacement_dict)


def get_random_key(value_list, random_value_digits=7):
    random_value_endcap = '9' * random_value_digits
    random_value_endcap = int(random_value_endcap)

    random_value = randint(1, random_value_endcap)
    random_value_formatter = f'{{:0{random_value_digits}d}}'
    random_value = random_value_formatter.format(random_value)
    
    value_list = [str(i) for i in value_list]
    value_list.append(random_value)
    random_str = '-'.join(value_list)
    random_str = random_str.encode()

    sha_key = hashlib.new('sha256')
    sha_key.update(random_str)
    return sha_key.hexdigest()


def get_conn(
    database_connection_type=DEFAULT_CONNECTION_TYPE,
    database=DATABASE,
    host=HOST,
    password=PASSWORD,
    port=PORT,
    username=USERNAME
):
    if database_connection_type == 'sqlite':
        return sqlite3.connect(database)
    elif database_connection_type == 'postgres':
        db_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        db = create_engine(db_string)
        return db.connect()


def run_query(
    sql,
    return_data_format=list,
    commit=False,
    database_connection_type=DEFAULT_CONNECTION_TYPE,
    database=DATABASE,
    host=HOST,
    password=PASSWORD,
    port=PORT,
    username=USERNAME,
    sql_parameters=[],
    print_debug_info=False
):
    exception = None
    rows = []
    column_names = []
    try:
        if database_connection_type == 'sqlite':
            with sqlite3.connect(database) as conn:
                cur = conn.cursor()
                cur.execute(sql, sql_parameters)

                if commit:
                    conn.commit()
                    return None

                rows = cur.fetchall()
                column_names = [i[0] for i in cur.description]
        elif database_connection_type == 'postgres':
            sql = sqlite_to_psql(sql)
            db_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
            db = create_engine(db_string)
            with db.connect() as conn:
                results = conn.execute(sql, sql_parameters, commit=commit)

                if commit:
                    return None

                rows = results.fetchall()
                column_names = list(results.keys())
        else:
            raise ValueError("Parameter database_connection_type must be either 'postgres' or 'sqlite'.")
    except Exception as e:
        exception = e

    if print_debug_info:
        for debug_component in [sql, sql_parameters, rows, column_names]:
            print(str(debug_component)[:1000])

    if exception is not None:
        raise exception

    if return_data_format is list:
        return rows

    elif return_data_format is dict:
        results_dict = {}
        for n, column_name in enumerate(column_names):
            results_dict[column_name] = []
            for row in rows:
                results_dict[column_name].append(row[n])
        return results_dict



def build_dummy_data(
    database_connection_type=DEFAULT_CONNECTION_TYPE,
    database=DATABASE,
    host=HOST,
    password=PASSWORD,
    port=PORT,
    username=USERNAME,
    app_data_path=APP_DATA_PATH
):

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
            rows = []
            with open(f'{table_csv_path}/{data_filename}', newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    rows.append(row)
                    placeholder = ['?' for i in row]
                    placeholder = ', '.join(placeholder)
                    placeholder = f"({placeholder})"
                    insert_statement_rows.append(placeholder)
            insert_statement_rows = insert_statement_rows[1:]
            insert_statement_rows = ',\n'.join(insert_statement_rows)
            insert_statement = f'INSERT INTO {table_name} VALUES\n{insert_statement_rows}\n;'
            rows = rows[1:]
            rows = list(chain(*rows))
            rows = [i if i != '' else None for i in rows]
        else:
            insert_statement = ''
            rows = []

        run_query_kwargs = {
            'commit': True,
            'database_connection_type': database_connection_type,
            'database': database,
            'host': host,
            'password': password,
            'port': port,
            'username': username,
            'print_debug_info': True,
            'sql_parameters': rows
        }

        for statement in [drop_statement, create_statement, insert_statement]:
            if statement:
                run_query(statement, **run_query_kwargs)
