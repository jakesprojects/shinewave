import sqlite3

NODE_TYPES_DICT = {
    'nodes.trigger.APITrigger': {
        'lookup_property': 'api_presets',
        'lookup_column': 'name',
        'display_data': {
            'title': 'name',
            'description_format': ''

        }
    },
    'nodes.outreach.SMSOutreach': {
        'lookup_property': 'sms_templates',
        'lookup_column': 'name',
        'display_data': {
            'title': 'name',
            'description_format': '{definition_file_contents}'

        }
    }
}

DATABASE='./data/test_db.db'
NODE_TEMPLATES_PATH = './data/templates'

def fetch_node_display_info(
    node, node_types_dict=NODE_TYPES_DICT, database=DATABASE, node_templates_path=NODE_TEMPLATES_PATH
):
    node_type = node.get_property('type_')

    node_master_type, node_parent_type, node_detail_type = node_type.split('.')

    fetch_data_dict = node_types_dict.get(node_type)
    if fetch_data_dict:
        display_data = fetch_data_dict.get('display_data')
        lookup_property = fetch_data_dict.get('lookup_property')
        lookup_key = node.get_property(lookup_property)
        lookup_column = fetch_data_dict.get('lookup_column')

        if not lookup_key:
            return 'No Value Selected', ''

        title = ''
        description = ''

        with sqlite3.connect(database) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                    SELECT *
                    FROM templates
                    WHERE {lookup_column} = '{lookup_key}'
                """
            )
            node_data = cur.fetchone()
            field_names = [i[0] for i in cur.description]
            node_dict = {i[0]:i[1] for i in zip(field_names, node_data)}

            title = node_dict.get(display_data.get('title'))
            description_format = display_data.get('description_format')

        if '{definition_file_contents}' in description_format:
            with open(
                f"{node_templates_path}/{node_parent_type}/{node_detail_type}/{node_dict['definition_file']}",
                'r'
            ) as definition_file:
                definition_file_contents = definition_file.read()
        else:
            definition_file_contents = ''

        description = description_format.format(definition_file_contents=definition_file_contents)

        return title, description



