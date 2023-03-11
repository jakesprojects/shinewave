from collections import OrderedDict
from datetime import datetime
import html
import re

from jakenode.nodes.trigger.trigger_node import TriggerNode


"""
TO DO:
    Build the thing
"""

class ExactResponseReceivedTrigger(TriggerNode):
    """
    	Node type designed to handle exact SMS responses. Takes free text, checks if response is an exact match, then
    	processes it accordingly.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Exact Response Received'

    def __init__(self):
        super(BasicResponseReceivedTrigger, self).__init__(has_input=True)

        self.add_text_input('exact_response', 'Exact Response')

        # self.set_property('color', (215, 254, 203))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        display_text = ''

        return node_name, display_text

    def validate_node(self):
        """
        """


class FuzzyResponseReceivedTrigger(TriggerNode):
    """
    	Node type designed to handle fuzzy SMS responses. Takes a response template, checks if response is a match, then
    	processes it accordingly.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Fuzzy Response Received'

    def __init__(self):
        super(BasicResponseReceivedTrigger, self).__init__(has_input=True)

        self.add_text_input('response_template', 'Response Template')

        # self.set_property('color', (215, 254, 203))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        display_text = ''

        return node_name, display_text

    def validate_node(self):
        """
        """
