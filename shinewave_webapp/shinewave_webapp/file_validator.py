import html
from io import StringIO
import re


import pandas as pd


class FileValidator():

    def __init__(self, file_contents):
        self.file_contents = file_contents
        self.upload_table = None
        self.column_lookup_function = None
        self.header = None

    def dedupe_character(self, text, character):
        duped_char = character * 2
        while duped_char in text:
            text = text.replace(duped_char, character)
        return text

    def validate_file(self):
        upload_file = StringIO(self.file_contents)
        upload_df = pd.read_csv(upload_file)
        base_columns = [
            'provider_id', 'first_name', 'last_name', 'phone_number', 'email', 'key_date', 'key_time', 'time_zone'
        ]

        column_aliases = {i: '' for i in base_columns}

        upload_column_list = list(upload_df.columns)
        for column in column_aliases:
            if column in upload_column_list:
                column_aliases[column] = column

        transformed_columns = {}

        for alias in upload_column_list:
            transformed_column_versions = [
                re.sub('[^0-9a-zA-Z]', '', alias),
                re.sub('[^0-9a-zA-Z]', '_', alias),
                re.sub('[^0-9a-zA-Z ]', '', alias).replace(' ', '_')
            ]
            transformed_column_versions = [self.dedupe_character(i, '_') for i in transformed_column_versions]
            transformed_columns[alias] = transformed_column_versions

        for column in column_aliases:
            for alias, transformed_names in transformed_columns.items():
                if (not column_aliases[column]) and (column in transformed_names):
                    column_aliases[column] = alias

        column_validation_notes = {}
        rename_dict = {}
        validation_failed = False
        for column, alias in column_aliases.items():
            if not alias:
                if column in ['first_name', 'last_name']:
                    validation_failed = True
                    message_level = 'failure'
                elif column in ['phone_number', 'email']:
                    message_level = 'warning'
                else:
                    message_level = 'missing'

                column_validation_notes[column] = (f'Column {column} not found in upload', message_level)
                upload_df[column] = None

            elif column != alias:
                rename_dict[alias] = column
                column_validation_notes[column] = (f'Column auto-renamed from "{alias}"', 'info')
            else:
                rename_dict[column] = column

        upload_df = upload_df.rename(columns=rename_dict)
        upload_df.fillna('', inplace=True)
        column_lookup_json = {}
        color_lookup_json = {'failure': 'red', 'warning': 'yellow', 'info': 'green', 'missing': 'grey'}
        for column in upload_df.columns:
            upload_df[column] = upload_df[column].astype(str)
            upload_df[column] = upload_df[column].map(html.escape)
            message, message_level = column_validation_notes.get(column, ('', ''))
            column_lookup_json[column] = {
                'msg': message, 'lvl': message_level, 'color': color_lookup_json.get(message_level, '')
            }
            if column not in base_columns:
                base_columns.append(column)

        upload_df = upload_df[base_columns]

        column_lookup_function = f"""
            function getColumnInfo(column, info_type) {{
                const columnLookupJSON = {column_lookup_json};
                var columnInfo = columnLookupJSON[column];
                return columnInfo[info_type];
            }};
        """

        if validation_failed:
            header = """
                <br>
                File validation failed. Please fix the red columns and re-upload.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <button class="btn btn-danger">Go Back</button>
            """
        else:
            header = """
                Recipient Upload&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <button class="btn btn-success">Looks Good!<br>Submit</button>
                <button class="btn btn-danger">I Want to Make Changes.<br>Go Back</button>
            """

        upload_table = upload_df.to_html(
            table_id='basic-datatables',
            border=0,
            classes=['display', 'table', 'table-striped', 'table-hover'],
            index=False,
            escape=False,
            justify='inherit'
        )

        self.upload_table = upload_table
        self.column_lookup_function = column_lookup_function
        self.header = header
