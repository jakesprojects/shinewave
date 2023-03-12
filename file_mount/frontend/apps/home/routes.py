# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
import sqlite3
from time import sleep
import urllib
import subprocess

from apps.home import blueprint
from flask import render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_login import login_required
from jinja2 import TemplateNotFound
import requests

from jakenode import database_connector

ACCOUNT_ID = 1
APP_HANDLER_PATH = '/srv/node_app/handlers'
DATABASE = f'{APP_HANDLER_PATH}/data/test_db.db'
LAUNCHER_APP_ADDRESS = 'http://localhost:49151/app_launcher'

def get_validation_failure_codes(node_type):
    return {
        '1': 'The submitted folder name already exists. Names must be unique.',
        '2': f'The submitted {node_type} name already exists in this folder. Names must be unique.',
        '3': 'Folders containing workflows cannot be deleted. Delete workflows first.',
        '4': f'The submitted {node_type} name was greater than the 150-character limit.'
    }


def tree_dict_to_json(tree_dict, tree_type, include_folder_operations, include_rename_operations):
    json_list = []
    if include_folder_operations:
        json_list.append({'text': 'New Folder', 'icon': 'jstree-ok'})

    for parent_node in tree_dict:

        children_list = [{'text': f'New {tree_type}', 'icon': 'jstree-ok'}]

        if include_folder_operations:
            children_list += [
                {'text': f'Rename Folder "{parent_node}"', 'icon': 'jstree-ok'},
                {'text': f'Delete Folder "{parent_node}"', 'icon': 'jstree-ok'}
            ]

        for child_node_name, child_node_id in tree_dict[parent_node]:
            if child_node_name is not None:
                operations = ['Edit']
                if include_rename_operations:
                    operations.append('Rename')
                operations.append('Delete')

                children_sub_list = []
                for operation in operations:
                    children_sub_list.append(
                        {'text': f'{operation} {tree_type} "{child_node_name}"', 'icon': 'jstree-ok'}
                    )

                children_list.append(
                    {'text': child_node_name, 'id': child_node_id, 'icon': 'jstree-file', 'children': children_sub_list}
                )

        json_list.append({'text': parent_node, 'children': children_list})

    full_json = {
        'core' : {
            'multiple' : False,
            'data' : json_list
        }
    }

    return json.dumps(full_json)


def get_validation_error_card(validation_error_text):
    if validation_error_text:
        return f"""
            <div class="card">
                <div class="card-header">
                    <h4 style="color:red">{validation_error_text}</h4>
                </div>
            </div>
        """
    else:
        return ''


def get_workflow_id_by_name(account_id, workflow_name, folder_name):
    query_results_dict = database_connector.run_query(
        """
            SELECT w.id
            FROM workflows w
            INNER JOIN workflow_categories wc ON
                w.workflow_category_id=wc.id
                AND w.account_id=wc.account_id
            WHERE
                w.account_id = ?
                AND w.name=?
                AND wc.name = ?
                AND w.active = 'TRUE'
        """,
        sql_parameters=[account_id, workflow_name, folder_name],
        return_data_format=dict
    )

    id_list = query_results_dict.get('id', [])
    if id_list:
        return id_list[0]


def get_template_id_by_name(account_id, template_name, folder_name):
    query_results_dict = database_connector.run_query(
        """
            SELECT t.id
            FROM templates t
            INNER JOIN workflow_categories wc ON
                t.workflow_category_id=wc.id
                AND t.account_id=wc.account_id
            WHERE
                t.account_id = ?
                AND t.name=?
                AND wc.name = ?
                AND t.active = 'TRUE'
        """,
        sql_parameters=[account_id, template_name, folder_name],
        return_data_format=dict
    )

    id_list = query_results_dict.get('id', [])
    if id_list:
        return id_list[0]


@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/wb-workflow-builder.html')
@blueprint.route('/wb-workflow-builder', methods=["GET"])
@login_required
def workflow_builder():
    tree_format = {}
    workflow_data = database_connector.run_query(
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

    tree_format_code = tree_dict_to_json(
        tree_format, tree_type='Workflow', include_folder_operations=True, include_rename_operations=True
    )

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

    validation_failure_code_dict = get_validation_failure_codes('workflow')

    validation_failure_code = request.args.get('validation_failure_code')
    validation_failure_text = validation_failure_code_dict.get(validation_failure_code, '')

    return render_template(
        'home/wb-workflow-builder.html',
        tree_format_text=tree_format_text,
        tree_format_code=tree_format_code,
        validation_error_card=get_validation_error_card(validation_failure_text),
        segment=get_segment(request)
    )



@blueprint.route('/template_submit', methods=["GET", "POST"])
@login_required
def template_submit():
    account_id = ACCOUNT_ID

    if request.method == "POST":
        template_name = request.form.get('template_name')
        template_contents = request.form.get('template_contents')
        template_id = request.form.get('template_id')
        database_connector.run_query(
            sql="""
                UPDATE templates
                SET name = ?
                WHERE
                    id = ?
                    AND account_id = ?
                    AND active = 'TRUE'
            """,
            sql_parameters=[template_name, template_id, account_id],
            commit=True
        )
        template_data = database_connector.run_query(
            sql="""
                SELECT
                    t.template_type,
                    wc.name AS workflow_category
                FROM templates t
                INNER JOIN workflow_categories wc ON t.workflow_category_id=wc.id
                WHERE
                    t.name = ?
                    AND t.id = ?
                    AND t.account_id = ?
                    AND t.active = 'TRUE'
            """,
            sql_parameters=[template_name, template_id, account_id],
            return_data_format=dict
        )
        template_type = template_data.get('template_type', [None])[0]
        workflow_category = template_data.get('workflow_category', [None])[0]
        if template_type and workflow_category:
            node_master_type, node_parent_type, node_detail_type = template_type.split('.')
            database_connector.edit_template(
                contents=template_contents,
                node_parent_type=node_parent_type,
                node_detail_type=node_detail_type,
                workflow_category=workflow_category,
                template_id=template_id
            )

    return redirect(url_for('home_blueprint.edit_templates'))

@blueprint.route('/builder_submit', methods=["GET", "POST"])
@login_required
def builder_submit():
    if request.method == "POST":

        folder = request.form.get('folder')
        node_type = request.form.get('node_type')
        operation = request.form.get('operation')
        submitted_name = request.form.get('submitted_name')
        workflow = request.form.get('workflow')
        template = request.form.get('template')
        template_type = request.form.get('template_type')

        query_library = {
            "Rename Folder": {
                'execution': {
                    'sql': """
                        UPDATE workflow_categories
                        SET name = ?
                        WHERE
                            account_id = ?
                            AND active = 'TRUE'
                            AND name = ?
                    """,
                    'sql_parameters': (submitted_name, ACCOUNT_ID, folder)
                }
            },
            "Rename Workflow": {
                'execution': {
                    'sql': """
                        UPDATE workflows
                        SET name = ?
                        WHERE
                            account_id = ?
                            AND active = 'TRUE'
                            AND name = ?
                            AND workflow_category_id IN (
                                SELECT id FROM workflow_categories WHERE name = ? AND active = 'TRUE'
                            )
                    """,
                    'sql_parameters': (submitted_name, ACCOUNT_ID, workflow, folder)
                }
            },
            "New Folder": {
                'execution': {
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
                'validation': {
                    'sql': """
                        SELECT id
                        FROM workflow_categories
                        WHERE
                            active = 'TRUE'
                            AND account_id = ?
                            AND name = ?
                    """,
                    'sql_parameters': (ACCOUNT_ID, submitted_name)
                },
                'validation_failure_code': 1
            },
            "New Workflow": {
                'execution': {
                    'sql': """
                        INSERT INTO workflows (id, account_id, name, workflow_category_id, active)
                        VALUES (
                            (SELECT MAX(id) + 1 FROM workflows),
                            ?,
                            ?,
                            (SELECT id FROM workflow_categories WHERE name = ? AND active = 'TRUE'),
                            'TRUE'
                        )
                    """,
                    'sql_parameters': (ACCOUNT_ID, submitted_name, folder)
                },
                'validation': {
                    'sql': """
                        SELECT w.id
                        FROM workflows w
                        INNER JOIN workflow_categories wc ON w.workflow_category_id = wc.id
                        WHERE
                            w.account_id = ?
                            AND w.name = ?
                            AND wc.name = ?
                            AND w.active = 'TRUE'
                    """,
                    'sql_parameters': (ACCOUNT_ID, submitted_name, folder)
                },
                'validation_failure_code': 2
            },
            "Delete Folder": {
                'execution': {
                    'sql': """
                        UPDATE workflow_categories
                        SET active = 'FALSE'
                        WHERE
                            account_id = ?
                            AND name = ?
                    """,
                    'sql_parameters': (ACCOUNT_ID, folder)
                },
                'validation': {
                    'sql': """
                        SELECT w.id
                        FROM workflows w
                        INNER JOIN workflow_categories wc ON w.workflow_category_id = wc.id
                        WHERE
                            w.account_id = ?
                            AND wc.name = ?
                            AND w.active = 'TRUE'
                    """,
                    'sql_parameters': (ACCOUNT_ID, folder)
                },
                'validation_failure_code': 3
            },
            "Delete Workflow": {
                'execution': {
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
            },
            "New Template": {
                'execution': {
                    'sql': """
                        INSERT INTO templates (id, account_id, template_type, name, workflow_category_id, active)
                        VALUES (
                            (SELECT MAX(id) + 1 FROM templates),
                            ?,
                            ?,
                            ?,
                            (SELECT id FROM workflow_categories WHERE name = ? AND active = 'TRUE'),
                            'TRUE'
                        )
                    """,
                    'sql_parameters': (ACCOUNT_ID, template_type, submitted_name, folder)
                },
                'validation': {
                    'sql': """
                        SELECT t.id
                        FROM templates t
                        INNER JOIN workflow_categories wc ON t.workflow_category_id = wc.id
                        WHERE
                            t.account_id = ?
                            AND t.name = ?
                            AND wc.name = ?
                            AND t.active = 'TRUE'
                    """,
                    'sql_parameters': (ACCOUNT_ID, submitted_name, folder)
                },
                'validation_failure_code': 2
            },
            "Delete Template": {
                'execution': {
                    'sql': """
                        UPDATE templates
                        SET active = 'FALSE'
                        WHERE
                            account_id = ?
                            AND active = 'TRUE'
                            AND name = ?
                            AND workflow_category_id IN (SELECT id FROM workflow_categories WHERE name = ?)
                    """,
                    'sql_parameters': (ACCOUNT_ID, template, folder)
                }
            }
        }

        if node_type == 'Workflow':
            redirect_page = 'home_blueprint.workflow_builder'
        elif node_type == 'Template':
            redirect_page = 'home_blueprint.edit_templates'
        else:
            return render_template('home/page-404.html'), 404

        query_sub_dict = query_library.get(f'{operation} {node_type}', {})
        validation_dict = query_sub_dict.get('validation')

        if validation_dict and len(submitted_name) > 150:
            validation_failure_code = 4
        elif validation_dict and database_connector.run_query(commit=False, **validation_dict):
            validation_failure_code = query_sub_dict['validation_failure_code']
        else:
            validation_failure_code = None

        if validation_failure_code is not None:
            return redirect(
                url_for(redirect_page, validation_failure_code=validation_failure_code)
            )

        if query_sub_dict:
            execution_dict = query_sub_dict['execution']
            database_connector.run_query(commit=True, **execution_dict)
            if node_type == 'Workflow':
                workflow = submitted_name
            elif node_type == 'Template':
                template = submitted_name

        if operation in ['Edit', 'New'] and node_type == 'Workflow':
            workflow_id = get_workflow_id_by_name(
                account_id=ACCOUNT_ID, workflow_name=workflow, folder_name=folder
            )
            return redirect(url_for('home_blueprint.workflow_builder_loading_screen', workflow_id=workflow_id))
        elif operation in ['Edit', 'New'] and node_type == 'Template':
            template_id = get_template_id_by_name(
                account_id=ACCOUNT_ID, template_name=template, folder_name=folder
            )
            return redirect(
                url_for('home_blueprint.edit_templates_app', template_id=template_id, template_type=template_type)
            )

    return redirect(url_for(redirect_page))


@blueprint.route('/wb-loading-screen.html', methods=['GET'])
@blueprint.route('/wb-loading-screen', methods=['GET'])
@login_required
def workflow_builder_loading_screen():
    workflow_id = request.args.get('workflow_id')
    return render_template(
        'home/wb-loading-screen.html',
        redirect_url=url_for('home_blueprint.workflow_builder_app', workflow_id=workflow_id),
        segment=get_segment(request)
    )


@blueprint.route('/wb-reload.html', methods=['GET'])
@blueprint.route('/wb-reload', methods=['GET'])
@login_required
def workflow_builder_reload():
    account_id = ACCOUNT_ID
    workflow_id = request.args.get('workflow_id')

    database_connector.run_query(
        """
            UPDATE workflow_routes
            SET active = 'FALSE'
            WHERE
                active = 'TRUE'
                AND account_id = ?
                AND workflow_id = ?
        """,
        sql_parameters=[account_id, workflow_id],
        commit=True
    )

    subprocess.call(f'killall -u appuser_{account_id}_{workflow_id}', shell=True)

    return render_template(
        'home/wb-loading-screen.html',
        redirect_url=url_for('home_blueprint.workflow_builder_app', workflow_id=workflow_id),
        segment=get_segment(request)
    )


@blueprint.route('/wb-workflow-builder-app.html', methods=['GET'])
@blueprint.route('/wb-workflow-builder-app', methods=['GET'])
@login_required
def workflow_builder_app():
    workflow_id = request.args.get('workflow_id')
    account_id = ACCOUNT_ID
    workflow_id = database_connector.run_query(
        f"""
            SELECT
                id
            FROM workflows
            WHERE
                account_id=?
                AND active='TRUE'
                AND id=?
        """,
        sql_parameters=[account_id, workflow_id],
        return_data_format=list
    )
    if not workflow_id:
        return render_template('home/page-404.html'), 404

    workflow_id = workflow_id[0][0]

    launcher_api_response = requests.post(
        LAUNCHER_APP_ADDRESS, json={'account_id': str(ACCOUNT_ID), 'workflow_id': str(workflow_id)}
    )
    address_info = json.loads(launcher_api_response.content)
    app_server_address = address_info['app_server_address']
    xpra_port = address_info['xpra_port']
    info_panel_port = address_info['info_panel_port']

    app_loaded = False
    time_elapsed = 0
    timeout = False
    while (not app_loaded) and (not timeout):
        try:
            requests.get(f'http://{app_server_address}:{info_panel_port}')
            app_loaded = True
        except requests.ConnectionError:
            sleep(0.5)
            time_elapsed += 0.5
        if time_elapsed > 30:
            timeout = True

    if timeout:
        return render_template('home/page-500.html'), 500
    else:
        return render_template(
            'home/wb-workflow-builder-app.html',
            app_server_address=app_server_address,
            xpra_port=xpra_port,
            info_panel_port=info_panel_port,
            workflow_id=workflow_id,
            segment=get_segment(request)
        )


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


@blueprint.route('/et-edit-templates.html', methods=['GET'])
@blueprint.route('/et-edit-templates', methods=['GET'])
@login_required
def edit_templates():
    return render_template_editor(None)


@blueprint.route('/et-edit-sms-templates.html', methods=['GET'])
@blueprint.route('/et-edit-sms-templates', methods=['GET'])
@login_required
def edit_sms_templates():
    return render_template_editor()


def render_template_editor(outbound_template_types=['nodes.outreach.SMSOutreach'], inbound_template_types=[]):
    account_id = ACCOUNT_ID
    def _generate_formatted_tree(account_id, template_types):
        template_type_substitutions = ['?' for i in template_types]
        template_type_substitutions = ', '.join(template_type_substitutions)
        template_data = database_connector.run_query(
            f"""
                SELECT
                    wc.name AS workflow_category,
                    t.name,
                    t.id
                FROM workflow_categories wc
                LEFT JOIN templates t ON
                    wc.id=t.workflow_category_id
                    AND wc.active=t.active
                WHERE
                    wc.account_id = ?
                    AND wc.active='TRUE'
                    AND t.template_type IN ({template_type_substitutions})
                ORDER BY wc.name, t.name
            """,
            sql_parameters=[account_id] + template_types,
            return_data_format=list
        )

        tree_format = {}
        for workflow_category, template_name, template_id in template_data:
            tree_format.setdefault(workflow_category, [])
            tree_format[workflow_category].append((template_name, template_id))

        return tree_dict_to_json(
            tree_format, tree_type='Template', include_folder_operations=False, include_rename_operations=False
        )

    tree_format_code = _generate_formatted_tree(account_id, outbound_template_types)

    validation_failure_code_dict = get_validation_failure_codes('template')

    validation_failure_code = request.args.get('validation_failure_code')
    validation_failure_text = validation_failure_code_dict.get(validation_failure_code, '')

    return render_template(
        'home/et-edit-templates.html',
        validation_error_card=get_validation_error_card(validation_failure_text),
        tree_format_text='',
        tree_format_code=tree_format_code,
        template_type='nodes.outreach.SMSOutreach',
        segment=get_segment(request)
    )


@blueprint.route('/et-edit-templates-app.html', methods=['GET'])
@blueprint.route('/et-edit-templates-app', methods=['GET'])
@login_required
def edit_templates_app():
    account_id = ACCOUNT_ID
    template_id = request.args.get('template_id')
    template_data = database_connector.run_query(
        f"""
            SELECT
                wc.name AS workflow_category,
                t.name AS template_name
            FROM workflow_categories wc
            LEFT JOIN templates t ON
                wc.id=t.workflow_category_id
                AND wc.active=t.active
            WHERE
                wc.account_id=?
                AND wc.active='TRUE'
                AND t.id=?
        """,
        sql_parameters=[account_id, template_id],
        return_data_format=dict
    )

    folder_name = template_data.get('workflow_category')
    template_name = template_data.get('template_name')

    if template_name and folder_name:
        folder_name = folder_name[0]
        template_name = template_name[0]
        try:
            template_contents = database_connector.fetch_template(
                node_parent_type='outreach',
                node_detail_type='SMSOutreach',
                workflow_category=folder_name,
                template_id=template_id
            )
        except FileNotFoundError:
            template_contents = ''
        return render_template(
            'home/et-edit-templates-app.html',
            folder_name=folder_name,
            template_name=template_name,
            template_contents=template_contents,
            template_id=template_id,
            segment=get_segment(request)
        )
    else:
        return render_template('home/page-404.html'), 404


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
