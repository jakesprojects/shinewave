import random

from jakenode.nodes.outreach.outreach_node import OutreachNode

class SMSOutreach(OutreachNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.outreach'

    # initial default node name.
    NODE_NAME = 'SMS Outreach'

    def __init__(self):
        super(SMSOutreach, self).__init__(has_output=True)

        self.generate_sms_templates()

        sms_templates = self.sms_templates
        template_names = [''] + [i.name for i in sms_templates]
        self.add_combo_menu(
            'sms_templates', 'SMS Templates', items=['', 'Same Day Appt Reminder', 'Prescription Reminder']
        )
        self.set_property('color', (151, 219, 179))

    def generate_sms_templates(self):
        self.sms_templates = [SMSTemplate(), SMSTemplate()]

class SMSTemplate():
    def __init__(self, location=''):
        self.name = f'SMS Template {random.randint(0, 100)}'
        self.summary = f"summary line 1\n{self.name}"
