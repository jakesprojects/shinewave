from collections import OrderedDict
from datetime import datetime, timedelta
import html

import pytz

from jakenode.nodes.trigger.trigger_node import TriggerNode


"""
TO DO:
    * validate that dates are in future
"""

class AtTimeTrigger(TriggerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'At Time Trigger'

    def __init__(self):
        super(AtTimeTrigger, self).__init__(has_input=True)
        timezones = list(self.get_timezones().keys())

        self.add_text_input('execution_date', 'Execution Date/Time')
        self.add_combo_menu(
            'timezone',
            'Time Zone',
            items=timezones
        )

        self.set_property('color', (215, 254, 203))
        self.set_property('timezone', 'Pacific')


    def get_timezones(self):
        return OrderedDict(
            {
                'Hawaii': 'US/Hawaii',
                'Alaska': 'US/Alaska',
                'Pacific': 'US/Pacific',
                'Mountain': 'US/Mountain',
                'Central': 'US/Central',
                'Eastern': 'US/Eastern',
                'UTC': 'UTC',
                'Local to Recipient Area Code': None,
                'Defined by Recipient Data': None
            }
        )

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        try:
            execution_date = self.get_execution_date()
            execution_timezone = self.get_property('timezone')
        except ValueError as exception:
            return node_name, f'<p style="background-color:red;">{exception}</p>'

        if execution_date == 'target':
            execution_date = 'the date/time associated with the individual recipients (uploaded via file or API).'
            if execution_timezone == 'Defined by Recipient Data':
                execution_timezone = 'The timezone will also be read from the recipient data.'
            else:
                execution_timezone = f'The timezone will be assumed to be {execution_timezone}.'
            execution_timezone += ' This event will be triggered '
        elif execution_timezone in ['Defined by Recipient Data', 'Local to Recipient Area Code']:
            execution_timezone = f'(timezone {execution_timezone.lower()})'

        display_text = f'<p>The next step in the workflow will be triggered at {execution_date} {execution_timezone} '
        display_text += 'if no other downstream event occurs first.</p>'

        return node_name, display_text

    def get_execution_date(self):

        datetime_format_dict = OrderedDict(
            {'%Y/%m/%d %H:%M': 'YYYY/MM/DD HOUR:MINUTE', '%Y-%m-%d %H:%M': 'YYYY-MM-DD HOUR:MINUTE'}
        )

        date_format_dict = OrderedDict(
            {'%Y/%m/%d': 'YYYY/MM/DD', '%Y-%m-%d': 'YYYY-MM-DD'}
        )

        format_dict = datetime_format_dict.copy()
        format_dict.update(date_format_dict)

        execution_date_text = self.get_property('execution_date').strip().lower()
        execution_date_text = html.escape(execution_date_text)

        if execution_date_text.lower() == 'target':
            return 'target'

        if execution_date_text == '':
            raise ValueError('"Execution Date/Time" is blank.')
        
        error_msg = ''

        python_format_list = list(format_dict.copy().keys())
        execution_date = None

        while execution_date is None and python_format_list:
            python_format = python_format_list.pop(0)
            try:
                execution_date = datetime.strptime(execution_date_text, python_format)
                if python_format in date_format_dict:
                    execution_date += timedelta(hours=7)
            except ValueError:
                execution_date = None
                error_msg += f'<br>    {format_dict[python_format]}'

        if execution_date is None:
            error_msg = '"Execution Date/Time" must be provided in one of the following formats:' + error_msg
            error_msg += '<br>You may also enter "target" to use a date/time associated with the individual recipients'
            error_msg += '(uploaded via file or API).'
            error_msg += f'<br>You have entered "{execution_date_text}"'
            raise ValueError(error_msg)

        return execution_date

    def validate_node(self):
        """
            Raises a ValueError if an invalid value has been entered in the "Number of Time Units" free-text field
        """

        execution_date = self.get_execution_date()
        self.validate_has_downstream_outreach()

        timezones = self.get_timezones()
        execution_timezone = self.get_property('timezone')
        pytz_timezone_name = timezones[execution_timezone]
        if isinstance(execution_date, datetime) and pytz_timezone_name is not None:
            if execution_date.astimezone(pytz.timezone(pytz_timezone_name)) < datetime.now(pytz.timezone('UTC')):
                raise ValueError('Execution Date/Time must be in the future.')
