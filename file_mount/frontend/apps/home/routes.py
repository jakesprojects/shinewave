# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
import sqlite3

from apps.home import blueprint
from flask import render_template, request, redirect, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound

from jakenode.database_connector import run_query


ACCOUNT_ID = 1
APP_HANDLER_PATH = '/srv/node_app/handlers'
DATABASE = f'{APP_HANDLER_PATH}/data/test_db.db'


@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/workflow-builder.html')
@blueprint.route('/workflow-builder')
@login_required
def workflow_builder():
    # request.args
    def _workflow_tree_dict_to_json(workflow_tree_dict):
        json_list = [
            {'text': 'New Folder', 'icon': 'jstree-ok'}
        ]

        for parent_node in workflow_tree_dict:

            children_list = [
                {'text': 'New Workflow', 'icon': 'jstree-ok'},
                {'text': f'Rename Folder "{parent_node}"', 'icon': 'jstree-ok'},
                {'text': f'Delete Folder "{parent_node}"', 'icon': 'jstree-ok'}
            ]

            for child_node_name, child_node_id in workflow_tree_dict[parent_node]:
                if child_node_name is not None:
                    children_list.append(
                        {
                            'text': child_node_name,
                            'id': child_node_id,
                            'icon': 'jstree-file',
                            'children': [
                                {'text': f'Edit Workflow "{child_node_name}"', 'icon': 'jstree-ok'},
                                {'text': f'Rename Workflow "{child_node_name}"', 'icon': 'jstree-ok'},
                                {'text': f'Delete Workflow "{child_node_name}"', 'icon': 'jstree-ok'}
                            ]
                        }
                    )

            json_list.append({'text': parent_node, 'children': children_list})

        return json.dumps(json_list)

    tree_format = {}
    workflow_data = run_query(
        f"""
            SELECT
                wc.name AS workflow_category,
                w.name,
                w.id
            FROM workflow_categories wc
            LEFT JOIN workflows w ON
                wc.id=w.workflow_category_id
                AND wc.active=w.active
            WHERE
                wc.account_id={ACCOUNT_ID}
                AND wc.active='TRUE'
            ORDER BY wc.name, w.name
        """,
        return_data_format=list
    )

    for workflow_category, workflow_name, workflow_id in workflow_data:
        tree_format.setdefault(workflow_category, [])
        tree_format[workflow_category].append((workflow_name, workflow_id))

    tree_format_code = _workflow_tree_dict_to_json(tree_format)

    # Not sure how this is used
    tree_format_text = """<!-- 
        <li data-jstree='{ "opened" : true }'>Root node
            <ul>
                <li data-jstree='{ "selected" : true }'>Child node 1</li>
                <li>Child node 2</li>
            </ul>
        </li>
    -->
    """

    return render_template(
        'home/workflow-builder.html', tree_format_text=tree_format_text, tree_format_code=tree_format_code
    )

      
@blueprint.route('/builder_submit', methods=["GET", "POST"])
@login_required
def builder_submit():
    if request.method == "POST":
        operationTypes = ["Rename", "New", "Delete", "Edit"]
        nodeTypes = ["Folder", "Workflow"]

        print('~~~', request.form)
        folder = request.form.get('folder')
        node_type = request.form.get('node_type')
        operation = request.form.get('operation')
        submitted_name = request.form.get('submitted_name')
        workflow = request.form.get('workflow')
        print('@@@', ACCOUNT_ID)
        query_library = {
            "Rename Folder": {
                'sql': """
                    UPDATE workflow_categories
                    SET name = ?
                    WHERE
                        account_id = ?
                        AND active = 'TRUE'
                        AND name = ?
                """,
                'sql_parameters': (submitted_name, ACCOUNT_ID, folder)
            },
            "Rename Workflow": {
                'sql': """
                    UPDATE workflows
                    SET name = ?
                    WHERE
                        account_id = ?
                        AND active = 'TRUE'
                        AND name = ?
                        AND workflow_category_id IN (SELECT id FROM workflow_categories WHERE name = ?)
                """,
                'sql_parameters': (submitted_name, ACCOUNT_ID, workflow, folder)
            },
            "New Folder": {
                'sql': """
                    INSERT INTO workflow_categories (id, account_id, name, active)
                    VALUES (
                        (SELECT MAX(id) + 1 FROM workflow_categories),
                        ?,
                        ?,
                        'TRUE'
                    )
                """,
                'sql_parameters': (ACCOUNT_ID, submitted_name)
            },
            "New Workflow": {
                'sql': """
                    INSERT INTO workflows (id, account_id, name, workflow_category_id, active)
                    VALUES (
                        (SELECT MAX(id) + 1 FROM workflows),
                        ?,
                        ?,
                        (SELECT id FROM workflow_categories WHERE name = ?),
                        'TRUE'
                    )
                """,
                'sql_parameters': (ACCOUNT_ID, submitted_name, folder)
            },
            "Delete Folder": {
                'sql': """
                    UPDATE workflow_categories
                    SET active = 'FALSE'
                    WHERE
                        account_id = ?
                        AND name = ?
                """,
                'sql_parameters': (ACCOUNT_ID, folder)
            },
            "Delete Workflow": {
                'sql': """
                    UPDATE workflows
                    SET active = 'FALSE'
                    WHERE
                        account_id = ?
                        AND active = 'TRUE'
                        AND name = ?
                        AND workflow_category_id IN (SELECT id FROM workflow_categories WHERE name = ?)
                """,
                'sql_parameters': (ACCOUNT_ID, workflow, folder)
            }
        }

        query_sub_dict = query_library.get(f'{operation} {node_type}')
        if query_sub_dict:
            run_query(commit=True, **query_sub_dict)
        elif operation == 'Edit':
            return redirect('/workflow-builder-app')

    return redirect(url_for('home_blueprint.workflow_builder'))

@blueprint.route('/workflow-builder-app.html', methods=['GET'])
@blueprint.route('/workflow-builder-app', methods=['GET'])
@login_required
def workflow_builder_app():
    # request.args
    return render_template('home/workflow-builder-app.html')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if template.endswith('.html'):
            template_name = template.rsplit('.html', 1)[0]
        else:
            template_name = template
            template += '.html'

        # special_formatting = handle_special_template(template_name)
        special_formatting = {}

        # Detect the current page
        segment = get_segment(request)

        import sys
        print(f'~SEGMENT~\n{segment}', file=sys.stderr)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, **special_formatting)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
