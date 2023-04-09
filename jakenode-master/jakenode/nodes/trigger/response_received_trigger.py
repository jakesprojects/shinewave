import html

from jakenode.nodes.trigger.trigger_node import TriggerNode
from jakenode.regex import regex_templates


"""
TO DO:
    * Add checkboxes to simple response, allowing for case-insensitivity and stripping special characters
    * Build templatized responses
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
            raise ValueError('SMS response triggers require an upstream SMS outreach, but none was found.')


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
        max_len = 160
        exact_response = self.get_property('exact_response').strip()
        if not exact_response:
            raise ValueError('No response to match has been entered. Please type a response in the box.')
        elif len(exact_response) > max_len:
            error_message = f'The entered response is limited to {max_len} characters, but you have entered '
            error_message += f'{len(exact_response)} characters. Please enter a shorter response in the box.'
            raise ValueError(error_message)

    def validate_node(self):
        self.validate_has_text_entered()
        self.validate_has_upstream_sms()
        self.validate_has_downstream_outreach()


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
        super(FuzzyResponseReceivedTrigger, self).__init__()

        self.regex_templates = regex_templates()
        self.regex_template_names = self.regex_templates.get_all_templates()

        self.add_combo_menu(
            'response_template', 'Response Template', items=[self.get_blank_menu_item()] + self.regex_template_names
        )

        self.set_property('color', (245, 194, 152))

    def get_display_info(self, node_templates_root=None):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)
        warning = self.get_html_validation_text(self.validate_has_template_selected)
        if warning:
            display_text = warning
        else:
            response_template_name = self.get_property('response_template').strip()
            leading_example_text = '<br>&nbsp;&nbsp;&nbsp;'
            examples = self.regex_templates.get_examples(response_template_name)
            examples = f'\n                    {leading_example_text}'.join(examples)
            display_text = f"""
                <p>
                    The next node will be triggered if an SMS response is received that looks like 
                    "{response_template_name}". Some examples include:
                    {leading_example_text}{examples}
                </p>
            """

        return node_name, display_text

    def validate_has_template_selected(self):
        """
            Validates that a template is selected.
        """
        response_template = self.get_property('response_template').strip()
        if not response_template:
            raise ValueError('A response type has not been selected for this node.')


    def validate_node(self):
        self.validate_has_template_selected()
        self.validate_has_upstream_sms()
        self.validate_has_downstream_outreach()


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
        super(FuzzyResponseReceivedTrigger, self).__init__()

        self.add_combo_menu('response_template', 'Response Template', items=[''])

        self.set_property('color', (227, 152, 245))

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
        self.validate_has_upstream_sms()
        self.validate_has_downstream_outreach()
