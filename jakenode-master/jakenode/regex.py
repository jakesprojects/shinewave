import re

class regex_templates():

    def __init__(self):
        self.templates_dict = {
            'Yes': {'template': r'\by(es)?\b', 'examples': ['Yes', 'y']},
            'No': {'template': r'\bn(o)?\b', 'examples': ['No', 'n']},
            'Sí': {'template': r'\bs(í|i)\b', 'examples': ['Si', 'sí']}
        }

    def get_all_templates(self):
        return sorted(list(self.templates_dict))

    def get_examples(self, template_name):
        return self.templates_dict[template_name]['examples']

    def get_template(self, template_name):
        template = self.templates_dict[template_name]['template']
        return re.compile(return_info, re.IGNORECASE)
