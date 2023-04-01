from jakenode.database_connector import run_query
from jakenode.nodes.outreach.outreach_node import OutreachNode

class OutboundWorkflowChange(OutreachNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.outreach'

    # initial default node name.
    NODE_NAME = 'Outbound Workflow Change'

    def __init__(self):
        super(OutboundWorkflowChange, self).__init__(has_output=False)

        self.template_data = {}
        self.set_property('color', (255, 203, 203))

    def get_node_template_data(self, template_id=None):
        if self.account_id is None:
            raise AttributeError('account_id has not been set.')
        if self.workflow_category_id is None:
            raise AttributeError('workflow_category_id has not been set.')

        # lookup_where_clause = f"""
        #     WHERE
        #         account_id = ?
        #         AND id != ?
        #         AND active = 'TRUE'
        # """

        # if template_id is not None:
        #     lookup_where_clause += f' AND id = {template_id}'
        # else:
        #     lookup_where_clause += f'-- AND id != {template_id}'

        template_data = run_query(
            f"""
                SELECT
                    NULL AS workflow_category,
                    *
                FROM workflows
                WHERE
                    account_id = ?
                    AND id != ?
                    AND active = 'TRUE'
            """,
            sql_parameters=[self.account_id, self.workflow_id],
            return_data_format=dict
        )

        return template_data

    def load_templates(self):
        all_template_data = self.get_node_template_data()
        for template_name in all_template_data['name']:
            individual_template_dict = {}
            for key in ['workflow_category', 'id']:
                individual_template_dict[key] = all_template_data[key].pop(0)

            self.template_data[template_name] = individual_template_dict

        self.add_combo_menu(
            'workflow_templates', 'Workflows', items=[' ' * 15] + list(self.template_data.keys())
        )


    def set_template_id_from_name(self):
        if not self.allow_forced_template_id_changes:
            return None

        template_name = self.get_property('workflow_templates')
        template_details = self.template_data.get(template_name, {})
        if template_details:
            template_id = template_details['id']
            self.safe_set_property('template_id', template_id)

    def set_template_name_from_id(self):
        template_id = self.get_property('template_id')
        if template_id:
            for template_name, template_details in self.template_data.items():
                if template_details['id'] == template_id:
                    self.set_property('workflow_templates', template_name)
                    return None

    def get_display_info(self):
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

        selected_template = self.get_property('workflow_templates')

        display_text = f"""
            <h3>Outbound Workflow Change</h3>
            <p>At this point, a recipient will be sent to the following workflow: {selected_template}</p>
        """

        return node_name, display_text

    def validate_has_template_selected(self):
        """
            Validates that a template is selected.
        """
        if self.template_data == {}:
            raise ValueError(
                'Template data is not set. Ensure that at least one other workflow exists.'
            )
        elif self.get_property('workflow_templates').strip() == '':
            raise ValueError('A target workflow has not been selected for this node.')


    def validate_node(self):
        """
            Validates that a template is selected and node has an upstream trigger.
        """
        self.validate_has_template_selected()

        self.validate_has_upstream_trigger()
