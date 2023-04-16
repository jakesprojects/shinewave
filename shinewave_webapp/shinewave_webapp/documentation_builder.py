from collections import OrderedDict

CONTENTS = OrderedDict({
        'Contents': None,
        'Workflow Builder': None,
        'Enable/Disable Workflows': None,
        'Message Templates': ['SMS Templates', 'Email Templates'],
        'API Settings': ['API Triggers', 'Outbound API Templates'],
        'Recipient Management': ['Recipient File Upload', 'Message Explorer'],
        'Workflow Journeys': None,
        'Tabular Reports': ['Message Volume by Workflow', 'Message Volume by Type'],
        'Graphs': ['Outbound Message Volume', 'Inbound Message Volume']

    })

ICONS = {
    'Contents': 'icon-book-open',
    'Workflow Builder': 'flaticon-diagram',
    'Enable/Disable Workflows': 'fas fa-toggle-on',
    'Message Templates': 'icon-speech',
    'API Settings': 'flaticon-cloud',
    'Recipient Management': 'icon-people',
    'Workflow Journeys': 'fas fa-code-branch',
    'Tabular Reports': 'fas fa-table',
    'Graphs': 'fas fa-chart-bar'

}

def build_documentation_nav(active_section, contents=CONTENTS, icons=ICONS):

    section_format = r"""
        <li class="nav-item {active_flag}">
            <a href="/documentation?section={section_link}">
                <i class="{icon}"></i>
                <p>{section_name}</p>
            </a>
        </li>
    """

    section_items = []
    for section_name, subsection_names in contents.items():
        section_link = section_name.lower().replace(' ', '-')
        icon = icons.get(section_name, '')

        if active_section == section_link:
            section_active_flag = 'active'
        else:
            section_active_flag = ''

        section = section_format.format(
            section_link=section_link,
            section_name=section_name,
            icon=icon,
            active_flag=section_active_flag
        )

        section_items.append(section)

    section_items = '\n'.join(section_items)

    return section_items

def get_section_name(active_section, contents=CONTENTS):
    for section_name in contents:
        section_link = section_name.lower().replace(' ', '-')
        if active_section == section_link:
            return section_name
    return 'Not Found'