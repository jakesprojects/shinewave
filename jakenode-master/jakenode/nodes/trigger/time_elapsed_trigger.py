from jakenode.nodes.trigger.trigger_node import TriggerNode


class TimeElapsedTrigger(TriggerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'Time Elapsed Trigger'

    def __init__(self):
        super(TimeElapsedTrigger, self).__init__(has_input=True)

        self.add_combo_menu(
            'time_units', 'Time Units', items=['minutes', 'hours', 'days', 'weeks', 'months']
        )

        self.add_text_input('time_number', 'Number of Time Units')

        self.set_property('color', (255, 252, 201))
