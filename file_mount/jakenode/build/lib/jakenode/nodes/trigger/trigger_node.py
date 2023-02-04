from jakenode.nodes.workflow_node import WorkflowNode


class TriggerNode(WorkflowNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Trigger'

    def __init__(self, has_input):
        super(TriggerNode, self).__init__(has_output=True, has_input=has_input)
