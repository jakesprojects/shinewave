import random

from jakenode.nodes.outreach.outreach_node import OutreachNode

class SMSOutreach(WorkflowNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.event'

    # initial default node name.
    NODE_NAME = 'SMS Outreach'

    def __init__(self):
        super(TriggerNode, self).__init__(has_output=True, has_input=True)

        self.generate_api_presets()

        sms_templates = self.sms_templates
        template_names = [''] + [i.name for i in sms_templates]
        self.add_combo_menu('sms_templates', 'SMS Templates', items=template_names)

    def generate_sms_templates(self):
        self.sms_templates = [APIPreset(), APIPreset()]

class SMSTemplate():
    def __init__(self, location=''):
        self.name = f'SMS Template {random.randint(0, 100)}'
        self.summary = f"summary line 1\n{self.name}"
