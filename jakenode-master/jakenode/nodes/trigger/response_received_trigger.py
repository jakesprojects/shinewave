import html

from jakenode.nodes.trigger.trigger_node import TriggerNode


"""
TO DO:
    * Add checkboxes to simple response, allowing for case-insensitivity and stripping special characters
    * Build templatized and fuzzy responses
"""


class ResponseReceivedTrigger(TriggerNode):
    """
        Generic node type designed to be a parent to more-specific response-received nodes.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Response Received'

    def __init__(self):
        super(ResponseReceivedTrigger, self).__init__(has_input=True)

    def validate_has_upstream_sms(self):
        upstream_node_types = [i.get_property('type_') for i in self.get_upstream_nodes()]
        if not 'nodes.outreach.SMSOutreach' in upstream_node_types:
            raise ValueError('SMS response triggers require an upstream SMS outrach, but none was found.')


class ExactResponseReceivedTrigger(ResponseReceivedTrigger):
    """
        Node type designed to handle exact SMS responses. Takes free text, checks if response is an exact match, then
        processes it accordingly.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Exact Response Received'

    def __init__(self):
        super(ExactResponseReceivedTrigger, self).__init__()

        self.add_text_input('exact_response', 'Exact Response')

        self.set_property('color', (219, 245, 152))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        try:
            self.validate_has_text_entered()
        except ValueError as exception:
            return node_name, f'<p style="background-color:red;">{exception}</p>'

        exact_response = html.escape(self.get_property('exact_response'))

        display_text = f"""
            <p>
                The next node will be triggered if an SMS response is received that exactly matches the following text:
                <br>
                <b>{exact_response}</b>
            </p>
        """

        return node_name, display_text

    def validate_has_text_entered(self):
        exact_response = self.get_property('exact_response').strip()
        if not exact_response:
            raise ValueError('No response to match has been entered. Please type a response in the box.')
        elif len(exact_response) > 160:
            error_message = f'The entered response is limited to {max_len} characters, but you have entered '
            error_message += '{len(exact_response)} characters. Please enter a shorter response in the box.'
            raise ValueError(error_message)

    def validate_node(self):
        self.validate_has_text_entered()
        self.validate_has_upstream_sms()


class FuzzyResponseReceivedTrigger(ResponseReceivedTrigger):
    """
        Node type designed to handle fuzzy SMS responses. Takes a response template, checks if response is a match, then
        processes it accordingly.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Fuzzy Response Received'

    def __init__(self):
        super(FuzzyResponseReceivedTrigger, self).__init__(has_input=True)

        self.add_combo_menu('response_template', 'Response Template', items=[''])

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


class TemplatizedResponseReceivedTrigger(ResponseReceivedTrigger):
    """
        Node type designed to handle templatized SMS responses. Takes a response template, checks if response is a
        match, then processes it accordingly.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Templatized Response Received'

    def __init__(self):
        super(FuzzyResponseReceivedTrigger, self).__init__(has_input=True)

        self.add_combo_menu('response_template', 'Response Template', items=[''])

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
