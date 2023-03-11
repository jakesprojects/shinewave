import json


def test():
    return 'TEST SUCCESSFUL!'


def tree_dict_to_json(tree_dict, tree_type):
    json_list = [
        {'text': 'New Folder', 'icon': 'jstree-ok'}
    ]

    for parent_node in tree_dict:

        children_list = [
            {'text': f'New {tree_type}', 'icon': 'jstree-ok'},
            {'text': f'Rename Folder "{parent_node}"', 'icon': 'jstree-ok'},
            {'text': f'Delete Folder "{parent_node}"', 'icon': 'jstree-ok'}
        ]

        for child_node_name, child_node_id in tree_dict[parent_node]:
            if child_node_name is not None:
                children_list.append(
                    {
                        'text': child_node_name,
                        'id': child_node_id,
                        'icon': 'jstree-file',
                        'children': [
                            {'text': f'Edit {tree_type} "{child_node_name}"', 'icon': 'jstree-ok'},
                            {'text': f'Rename {tree_type} "{child_node_name}"', 'icon': 'jstree-ok'},
                            {'text': f'Delete {tree_type} "{child_node_name}"', 'icon': 'jstree-ok'}
                        ]
                    }
                )

        json_list.append({'text': parent_node, 'children': children_list})

    return json.dumps(json_list)
