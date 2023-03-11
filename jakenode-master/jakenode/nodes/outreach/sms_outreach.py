from jakenode.nodes.outreach.outreach_node import OutreachNode

class SMSOutreach(OutreachNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.outreach'

    # initial default node name.
    NODE_NAME = 'SMS Outreach'

    def __init__(self):
        super(SMSOutreach, self).__init__(has_output=True)

        self.template_data = {}
        self.set_property('color', (151, 219, 179))

    def load_templates(self):
        all_template_data = self.get_node_template_data()
        for template_name in all_template_data['name']:
            individual_template_dict = {}
            for key in ['workflow_category', 'id']:
                individual_template_dict[key] = all_template_data[key].pop(0)

            self.template_data[template_name] = individual_template_dict

        self.add_combo_menu(
            'sms_templates', 'SMS Templates', items=[''] + list(self.template_data.keys())
        )

    def get_display_info(self, node_templates_root='./data/templates'):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        try:
            self.validate_has_template_selected()
        except ValueError as exception:
            return node_name, f'<p style="background-color:red;">{exception}</p>'

        selected_template = self.get_property('sms_templates')

        workflow_category = self.template_data[selected_template]['workflow_category']
        template_id = self.template_data[selected_template]['id']

        template_filepath_components = [
            node_templates_root, self.node_parent_type, self.node_detail_type, workflow_category, str(template_id)
        ]

        template_filepath = '/'.join(template_filepath_components) + '.txt'
        with open(template_filepath, 'r') as template_file:
            template_file_contents = template_file.read()

        display_text = f"""
            <h3>SMS Template: {selected_template}</h3>
            <p>{template_file_contents}</p>
        """

        return node_name, display_text

    def validate_has_template_selected(self):
        """
            Validates that a template is selected.
        """
        if self.template_data == {}:
            raise ValueError(
                'Template data is not set. Ensure that at least one SMS template exists for this workflow category.'
            )
        elif self.get_property('sms_templates') == '':
            raise ValueError('An SMS template has not been selected for this node.')


    def validate_node(self):
        """
            Validates that a template is selected and node has an upstream trigger.
        """
        self.validate_has_template_selected()

        self.validate_has_upstream_trigger()
