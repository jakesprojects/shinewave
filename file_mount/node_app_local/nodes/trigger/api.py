from NodeGraphQt import BaseNode


class TriggerAPI(BaseNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.basic'

    # initial default node name.
    NODE_NAME = 'API Trigger'

    def __init__(self):
        super(TriggerAPI, self).__init__()

        # create node outputs.
        self.add_output('output_1')