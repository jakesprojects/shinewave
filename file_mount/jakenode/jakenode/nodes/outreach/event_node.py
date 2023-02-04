from jakenode.nodes.workflow_node import WorkflowNode


class OutreachNode(WorkflowNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.outreach'

    # initial default node name.
    NODE_NAME = 'Outreach'

    def __init__(self):
        super(TriggerNode, self).__init__(has_output=True, has_input=True)