from jakenode.nodes.trigger.trigger_node import TriggerNode


class InboundWorkflowChange(TriggerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Inbound Workflow Change'

    def __init__(self):
        super(InboundWorkflowChange, self).__init__(has_input=False)

        self.template_data = {}
        self.set_property('color', (255, 255, 255))

    def get_display_info(self):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        display_text = """
            <p>This is an entry point for recipients sent from another workflow</p>
        """

        return node_name, display_text

    def validate_node(self):
        """
            Validates that a template is selected and node has an upstream trigger.
        """
        self.validate_has_downstream_outreach()
