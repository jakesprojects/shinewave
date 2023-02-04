from NodeGraphQt import BaseNode


class TriggerNode(BaseNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Trigger'

    def __init__(self):
        super(TriggerNode, self).__init__()

        # create node outputs.
        self.add_output('output_1')