from jakenode.nodes.workflow_node import WorkflowNode


class OutreachNode(WorkflowNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.outreach'

    # initial default node name.
    NODE_NAME = 'Outreach'

    def __init__(self, has_output):
        super(OutreachNode, self).__init__(has_output=has_output, has_input=True)

    def validate_has_upstream_trigger(self):
        super().validate_has_upstream_trigger(
            custom_error_message='Outreach node is orphaned (lacks an upstream trigger node).'
        )
