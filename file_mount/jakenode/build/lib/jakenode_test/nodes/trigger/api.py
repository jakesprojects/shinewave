from jakenode_test.nodes.trigger.trigger_node import TriggerNode


class TriggerAPI(TriggerNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'API Trigger'

    def __init__(self):
        super(TriggerAPI, self).__init__()

        # create node outputs.
        # self.add_output('output_1')