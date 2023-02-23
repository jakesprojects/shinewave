from collections import OrderedDict
from datetime import datetime
import html
import re

from jakenode.nodes.trigger.trigger_node import TriggerNode


"""
TO DO:
    * validate that dates are in future
    * add timezone support (Maybe via dropdown?)
    * Automatically add some time if just a date is selected (Midnight isn't a great default time)
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

        self.add_text_input('execution_date', 'Execution Date/Time')

        self.set_property('color', (215, 254, 203))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        try:
            execution_date = self.get_execution_date()
        except ValueError as exception:
            return node_name, f'<p style="background-color:red;">{exception}</p>'

        display_text = f'<p>The next step in the workflow will be triggered at {execution_date} if no other downstream'
        display_text += ' event occurs first.</p>'

        return node_name, display_text

    def get_execution_date(self):

        format_dict = OrderedDict(
            {
                '%Y/%m/%d %H:%M': 'YYYY/MM/DD HOUR:MINUTE',
                '%Y-%m-%d %H:%M': 'YYYY-MM-DD HOUR:MINUTE',
                '%Y/%m/%d': 'YYYY/MM/DD',
                '%Y-%m-%d': 'YYYY-MM-DD'
            }
        )

        execution_date_text = self.get_property('execution_date').strip()
        execution_date_text = html.escape(execution_date_text)

        if execution_date_text == '':
            raise ValueError('"Execution Date/Time" is blank.')
        
        error_msg = ''

        python_format_list = list(format_dict.copy().keys())
        execution_date = None

        while execution_date is None and python_format_list:
            python_format = python_format_list.pop(0)
            try:
                execution_date = datetime.strptime(execution_date_text, python_format)
            except ValueError:
                execution_date = None
                error_msg += f'<br>    {format_dict[python_format]}'

        if execution_date is None:
            error_msg = '"Execution Date/Time" must be provided in one of the following formats:' + error_msg
            error_msg += f'<br>You have entered "{execution_date_text}"'
            raise ValueError(error_msg)

        return execution_date

    def validate_node(self):
        """
            Raises a ValueError if an invalid value has been entered in the "Number of Time Units" free-text field
        """

        self.get_execution_date()
