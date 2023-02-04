from jakenode.nodes.workflow_node import WorkflowNode


class EventNode(WorkflowNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.event'

    # initial default node name.
    NODE_NAME = 'Event'

    def __init__(self):
        super(TriggerNode, self).__init__(has_output=True, has_input=True)
