import random

from jakenode.nodes.trigger.trigger_node import TriggerNode


class APITrigger(TriggerNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'API Trigger'

    def __init__(self):
        super(APITrigger, self).__init__(has_input=False)

        self.generate_api_presets()

        api_presets = self.api_presets
        preset_names = [''] + [i.name for i in api_presets]
        self.add_combo_menu('api_presets', 'API Presets', items=preset_names)

        # self.add_label(
        #     name='api_summary', label='Trigger Summary', text=api_presets[0].summary
        # )

    def generate_api_presets(self):
        self.api_presets = [APIPreset(), APIPreset()]

    def fetch_api_preset_summary(self, preset_name):
        for api_preset in self.api_presets:
            if api_preset.name == preset_name:
                return api_preset.summary

    def validate_node(self):
        """
        """
        self.validate_has_downstream_outreach()


class APIPreset():
    def __init__(self, location=''):
        self.name = f'API Preset {random.randint(0, 100)}'
        self.summary = f"summary line 1\n{self.name}"
