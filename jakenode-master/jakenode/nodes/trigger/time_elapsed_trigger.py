import html
import re

from jakenode.nodes.trigger.trigger_node import TriggerNode


class TimeElapsedTrigger(TriggerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Time Elapsed Trigger'

    def __init__(self):
        super(TimeElapsedTrigger, self).__init__(has_input=True)

        self.add_combo_menu(
            'time_units', 'Time Units', items=['minutes', 'hours', 'days', 'weeks', 'months']
        )

        self.add_text_input('time_number', 'Number of Time Units')

        self.set_property('color', (255, 252, 201))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        try:
            time_number = self.get_time_number()
        except ValueError as exception:
            return node_name, f'<p style="background-color:red;">{exception}</p>'

        time_units = self.get_property('time_units')

        if time_number == 1:
            time_units_text = f'{time_number} {time_units[:-1]} passes'
        else:
            time_units_text = f'{time_number} {time_units} pass'

        display_text = f'<p>The next step in the workflow will be triggered if {time_units_text} without any other'
        display_text += ' downstream event occurring.</p>'

        return node_name, display_text

    def get_time_number(self):
        time_number = self.get_property('time_number').strip()
        time_number = html.escape(time_number)[:150]

        if time_number == '':
            raise ValueError('"Number of Time Units" is blank.')
        elif re.sub('[0-9]', '', time_number):
            error_msg = '"Number of Time Units" must be a positive, whole number, entered without commas.'
            error_msg += f' You have entered "{time_number}".'
            raise ValueError(error_msg)
        elif time_number.startswith('0'):
            raise ValueError(
                f'"Number of Time Units" must not be zero or start with zero. You have entered "{time_number}".'
            )

        time_number = int(time_number)
        if time_number > 10000:
            raise ValueError(
                f'"Number of Time Units" must be at or below 10000. You have entered "{time_number}".'
            )

        return time_number

    def validate_node(self):
        """
            Raises a ValueError if an invalid value has been entered in the "Number of Time Units" free-text field
        """

        upstream_trigger_error_msg = 'This node type must be downstream from one of the following:'
        for upstream_node_type in ['API Trigger', 'File Upload Trigger', 'At Time Trigger']:
            upstream_trigger_error_msg += f'\n    {upstream_node_type}'

        self.get_time_number()
        self.validate_has_upstream_trigger(custom_error_message=upstream_trigger_error_msg)
        self.validate_has_downstream_outreach()
