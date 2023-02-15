import random

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

        if self.template_data == {}:
            return None, None

        selected_template = self.get_property('sms_templates')
        if selected_template == '':
            return None, None

        workflow_category = self.template_data[selected_template]['workflow_category']
        template_id = self.template_data[selected_template]['id']

        template_filepath_components = [
            node_templates_root, self.node_parent_type, self.node_detail_type, workflow_category, str(template_id)
        ]

        template_filepath = '/'.join(template_filepath_components) + '.txt'
        with open(template_filepath, 'r') as template_file:
            template_file_contents = template_file.read()

        return selected_template, template_file_contents



class SMSTemplate():
    def __init__(self, location=''):
        self.name = f'SMS Template {random.randint(0, 100)}'
        self.summary = f"summary line 1\n{self.name}"
