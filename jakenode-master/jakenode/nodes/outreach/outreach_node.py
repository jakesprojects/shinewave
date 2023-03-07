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
        upstream_nodes = self.get_upstream_nodes()
        upstream_node_parent_types = [i.node_parent_type for i in upstream_nodes]
        if 'trigger' not in upstream_node_parent_types:
            raise ValueError('Outreach node is orphaned (lacks an upstream trigger node).')
