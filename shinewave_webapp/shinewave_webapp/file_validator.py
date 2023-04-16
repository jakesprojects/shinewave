from datetime import datetime, timedelta
import html
from io import StringIO
import json
import re

import pandas as pd

from shinewave_webapp import time_parser


"""
    TO DO:
        * Add workflow_name, workflow_id, and timezones
        * Delete invalid fields, or whole rows if names are missing
        * Add check for new column names
        * Render file invalid if all rows are invalid
        * Implement count of valid vs. invalid rows
"""


class FileValidator():

    def __init__(self, file_contents, upload_id):
        self.file_contents = file_contents
        self.upload_id = upload_id
        self.upload_table = None
        self.column_lookup_function = None
        self.header = None
        self.footer = None
        self.column_validation_succeeded = False
        self.row_validation_succeeded = False
        self.column_lookup_json = None
        self.display_table = None

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

    def validate_is_date(self, value):
        if value is None:
            raise ValueError('Date not provided in valid format.')

        return value

    def validate_is_time(self, value):
        if value is None:
            raise ValueError('Time not provided in valid format.')

        return value

    def validate_columns(self):
        """
            This section needs heavy cleanup. Note to self: figure out how to reduce nesting here, and reduce the number
            of similar iterables.
        """

        def _dedupe_character(text, character):
            duped_char = character * 2
            while duped_char in text:
                text = text.replace(duped_char, character)

            return text

        def _generate_alias_transformations(alias):
            alias = alias.strip()
            alias_transformations = [
                re.sub('[^0-9a-zA-Z]', '', alias),
                re.sub('[^0-9a-zA-Z]', '_', alias),
                re.sub('[^0-9a-zA-Z ]', '', alias).replace(' ', '_')
            ]

            return [_dedupe_character(i, '_').lower() for i in alias_transformations]

        upload_file = StringIO(self.file_contents)
        upload_df = pd.read_csv(upload_file)
        base_columns = [
            'id',
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
            transformed_columns[alias] = _generate_alias_transformations(alias)

        for column in column_aliases:
            for alias, transformed_names in transformed_columns.items():
                if (not column_aliases[column]) and (column in transformed_names):
                    column_aliases[column] = alias

        # This nesting is disgusting, FIX LATER
        if not column_aliases['id']:
            for alias, transformed_names in transformed_columns.items():
                for alternative_name in ['member_id', 'provider_id', 'user_id', 'uuid', 'person_id']:
                    if alternative_name in transformed_names:
                        column_aliases['id'] = alias

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

    def format_tooltiped_value(self, value, tooltip, style_field='color:red;'):
        if style_field:
            style_tag = f'style="{style_field}"'
        else:
            style_tag = ''
        return f'<div {style_tag}>{value}<div class="icon-information" title="{tooltip}"></div></div>'

    def tag_invalid_row_value(self, value, validation_method):
        try:
            # Is Valid
            return (True, validation_method(value))
        except ValueError as e:
            # Is Not Valid
            return (False, self.format_tooltiped_value(value, e))

    def tag_invalid_row(self, row):
        if not (row['first_name'][0] and row['last_name'][0]):
            is_valid = False
            validation_failure_reason = 'First name and last name are required.'
        elif not (row['phone_number'][0] or row['email'][0]):
            is_valid = False
            validation_failure_reason = 'A phone number or an email address is required.'
        else:
            return True

        return self.format_tooltiped_value(is_valid, validation_failure_reason)

    def validate_rows(self):
        self.standardize_key_datetimes()

        original_columns = list(self.upload_table.columns)

        validation_methods_dict = {
            'phone_number': self.validate_us_phone_number,
            'email': self.validate_email_address,
            'first_name': self.validate_is_not_blank,
            'last_name': self.validate_is_not_blank,
            'key_date': self.validate_is_date,
            'key_time': self.validate_is_time
        }

        display_table = self.upload_table.copy()

        display_table['All Fields Valid'] = True
        for column_name, validation_method in validation_methods_dict.items():

            self.upload_table[column_name] = self.upload_table[column_name].map(
                lambda value: self.tag_invalid_row_value(value, validation_method)
            )

            display_table[column_name] = display_table[column_name].map(
                lambda value: self.tag_invalid_row_value(value, validation_method)
            )
            display_table['All Fields Valid'] = display_table.apply(
                lambda row: all([row['All Fields Valid'], row[column_name][0]]), axis=1
            )

        display_table['Row is Valid'] = display_table.apply(lambda row: self.tag_invalid_row(row), axis=1)
        self.upload_table = self.upload_table[display_table['Row is Valid'] == True]



        if all(display_table['All Fields Valid']):
            self.row_validation_succeeded = True
            del display_table['All Fields Valid']
            del display_table['Row is Valid']
        else:
            self.row_validation_succeeded = False
            display_table = display_table[['Row is Valid', 'All Fields Valid'] + original_columns]

            invalid_values_message = 'Some fields failed validation.'
            invalid_values_message += ' These will not be uploaded, but the rest of the row will be kept.'

            self.column_lookup_json['All Fields Valid'] = {
                'msg': invalid_values_message, 'lvl': 'info', 'color': 'grey'
            }
            self.column_lookup_json['Row is Valid'] = {
                'msg': 'Some rows failed validation. These rows will be discarded.', 'lvl': 'info', 'color': 'grey'
            }

        for column_name in validation_methods_dict:
            self.upload_table[column_name] = self.upload_table[column_name].map(
                lambda value: value[1] if value[0] else None
            )
            display_table[column_name] = display_table[column_name].map(lambda value: value[1])

        self.display_table = display_table

    def standardize_key_datetimes(self):

        def _extract_time_from_datetime(existing_time, datetime_text, formats):

            if existing_time is not None:
                return existing_time

            datetime_text = datetime_text.strip()
            for python_format in formats:
                try:
                    found_datetime = datetime.strptime(datetime_text, python_format)
                    return datetime.strftime(found_datetime, '%H:%M')
                except:
                    pass

            return None

        def _extract_date_from_datetime(datetime_text, formats):
            datetime_text = datetime_text.strip()
            for python_format in formats:
                try:
                    found_datetime = datetime.strptime(datetime_text, python_format)
                    return datetime.strftime(found_datetime, '%Y-%m-%d')
                except:
                    pass

            return None

        for column in ['key_date', 'key_time']:
            if column not in self.upload_table.columns:
                self.upload_table[column] = None

        datetime_formats = list(time_parser.get_format_dict('datetime').keys())
        time_formats = [i.split(' ')[-1] for i in datetime_formats]
        date_formats = list(time_parser.get_format_dict('date').keys())

        datetimes_df = self.upload_table[['key_date', 'key_time']].copy()
        for column in datetimes_df:
            datetimes_df[column] = datetimes_df[column].map(lambda text: text.strip())

        datetimes_df['key_time'] = datetimes_df['key_time'].map(
            lambda datetime_text: _extract_time_from_datetime(
                existing_time=None, datetime_text=datetime_text, formats=time_formats
            )
        )
        datetimes_df['key_time'] = datetimes_df.apply(
            lambda row: _extract_time_from_datetime(
                existing_time=row['key_time'], datetime_text=row['key_date'], formats=datetime_formats
            ),
            axis=1
        )

        datetimes_df['key_date'] = datetimes_df['key_date'].map(
            lambda datetime_text: _extract_date_from_datetime(
                datetime_text=datetime_text, formats=(datetime_formats + date_formats)
            )
        )

        self.upload_table['key_time'] = datetimes_df['key_time']
        self.upload_table['key_date'] = datetimes_df['key_date']

    def prepare_file_for_upload(self):
        base_columns = [
            'id',
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

        custom_columns = []

        for column in self.upload_table.columns:
            if column not in base_columns:
                custom_columns.append(column)

        custom_data_rows = self.upload_table[custom_columns].to_dict('records')
        self.upload_table['custom_data'] = custom_data_rows
        self.upload_table['custom_data'] = self.upload_table['custom_data'].map(json.dumps)
        self.upload_table = self.upload_table[base_columns + ['custom_data']]
        

    def validate_file(self):
        self.validate_columns()
        self.validate_rows()
        self.prepare_file_for_upload()

        row_count = len(self.display_table)
        row_error_count = len(self.display_table[self.display_table['All Fields Valid'] == False])
        invalid_row_count = len(self.display_table[self.display_table['Row is Valid'] != True])
        row_error_count -= invalid_row_count

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
        forward_button = f"""
            <a href="/rm-file-upload-overwrite-settings?upload_id={self.upload_id}" class="btn btn-success">
                Looks Good!<br>Continue...
            </a>
        """
        if not self.column_validation_succeeded:
            self.header = f"""
                <br>
                File validation failed. Please fix the red columns and re-upload.{pre_button_spacing}
                {back_button_opening_tag}Go Back</a>
            """
            self.footer = ''
        elif not self.row_validation_succeeded:
            self.header = f"""
                <br>
                Some rows failed validation. You may submit the file and exclude them, or go back and re-upload.
                {pre_button_spacing}
                {forward_button}
                {back_button_opening_tag}I Want to Make Changes.<br>Go Back</a>
            """

            self.footer = f"""
                <p>
                    <br>
                    {invalid_row_count} out of {row_count} rows were invalid and will not be uploaded.
                    <br>
                    {row_error_count} rows had errors in individual fields, but their valid fields will be uploaded.
                </p>
            """
        else:
            self.header = f"""
                Recipient Upload{pre_button_spacing}
                {forward_button}
                {back_button_opening_tag}I Want to Make Changes.<br>Go Back</a>
            """

            self.footer = f"""
                <p>
                    <br>
                    {len(self.display_table)} rows will be uploaded.
                </p>
            """
