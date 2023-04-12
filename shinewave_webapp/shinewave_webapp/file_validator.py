import html
from io import StringIO
import re


import pandas as pd

"""
    TO DO:
        * Add dates, times, and timezones
        * Delete invalid fields, or whole rows if names are missing
        * Add check for new column names
"""


class FileValidator():

    def __init__(self, file_contents):
        self.file_contents = file_contents
        self.upload_table = None
        self.column_lookup_function = None
        self.header = None
        self.column_validation_succeeded = False
        self.row_validation_succeeded = False
        self.column_lookup_json = None
        self.display_table = None

    def dedupe_character(self, text, character):
        duped_char = character * 2
        while duped_char in text:
            text = text.replace(duped_char, character)

        return text

    def validate_us_phone_number(self, phone_number):
        phone_number = str(phone_number).strip()
        regex_pattern = r'\(?\+?1?\)?[-\. ]?\(?[0-9]{3}\)?[-\. ]?[0-9]{3}[-\. ]?[0-9]{4}'
        if re.sub(regex_pattern, '' , phone_number, 1):
            raise ValueError('Not a valid US phone number')

        phone_number = re.sub('[^0-9]', '', phone_number)
        if phone_number.startswith('1'):
            phone_number = phone_number[1:]

        return f'+1 ({phone_number[0:3]}) {phone_number[3:6]}-{phone_number[6:10]}'


    def validate_email_address(self, email_address):
        email_address = str(email_address).strip()
        regex_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.sub(regex_pattern, '' , email_address, 1):
            raise ValueError('Not a valid email address')

        return email_address

    def validate_is_not_blank(self, value):
        value = str(value).strip()
        if not value.strip():
            raise ValueError('Field is blank.')

        return value

    def validate_columns(self):
        upload_file = StringIO(self.file_contents)
        upload_df = pd.read_csv(upload_file)
        base_columns = [
            'provider_id',
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'key_date',
            'key_time',
            'time_zone',
            'workflow_id',
            'workflow_name'
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

        if not validation_failed:
            self.column_validation_succeeded = True

        self.upload_table = upload_df
        self.column_lookup_json = column_lookup_json

    def tag_invalid_row_value(self, value, validation_method):
        try:
            return (
                True,
                validation_method(value)
            )
        except ValueError as e:
            return (
                False,
                f'<div style="color:red;">{value}<div class="icon-information" title="{e}"></div></div>'
            )

    def validate_rows(self):
        display_table = self.upload_table.copy()
        original_columns = list(display_table.columns)

        display_table['Row Validated'] = True

        validation_methods_dict = {
            'phone_number': self.validate_us_phone_number,
            'email': self.validate_email_address,
            'first_name': self.validate_is_not_blank,
            'last_name': self.validate_is_not_blank
        }

        for column_name, validation_method in validation_methods_dict.items():
            display_table[column_name] = display_table[column_name].map(
                lambda value: self.tag_invalid_row_value(value, validation_method)
            )
            display_table['Row Validated'] = display_table.apply(
                lambda row: all([row['Row Validated'], row[column_name][0]]), axis=1
            )
            display_table[column_name] = display_table[column_name].map(lambda value: value[1])


        if all(display_table['Row Validated']):
            self.row_validation_succeeded = True
            del display_table['Row Validated']
        else:
            self.row_validation_succeeded = False
            display_table = display_table[['Row Validated'] + original_columns]
            self.column_lookup_json['Row Validated'] = {
                'msg': 'Some rows failed validation', 'lvl': 'info', 'color': 'grey'
            }

        self.display_table = display_table
        

    def validate_file(self):
        self.validate_columns()
        self.validate_rows()
        self.display_table = self.display_table.to_html(
            table_id='basic-datatables',
            border=0,
            classes=['display', 'table', 'table-striped', 'table-hover'],
            index=False,
            escape=False,
            justify='inherit'
        )

        self.column_lookup_function = f"""
            function getColumnInfo(column, info_type) {{
                const columnLookupJSON = {self.column_lookup_json};
                var columnInfo = columnLookupJSON[column];
                return columnInfo[info_type];
            }};
        """
        
        pre_button_spacing = '&nbsp;' * 5
        back_button_opening_tag = '<a href="/rm-file-upload" class="btn btn-danger">'
        if not self.column_validation_succeeded:
            self.header = f"""
                <br>
                File validation failed. Please fix the red columns and re-upload.{pre_button_spacing}
                {back_button_opening_tag}Go Back</a>
            """
        elif not self.row_validation_succeeded:
            self.header = f"""
                <br>
                Some rows failed validation. You may submit the file and exclude them, or go back and re-upload.{pre_button_spacing}
                <button class="btn btn-success">Looks Good!<br>Submit</button>
                {back_button_opening_tag}I Want to Make Changes.<br>Go Back</a>
            """
        else:
            self.header = f"""
                Recipient Upload{pre_button_spacing}
                <button class="btn btn-success">Looks Good!<br>Submit</button>
                {back_button_opening_tag}I Want to Make Changes.<br>Go Back</a>
            """
