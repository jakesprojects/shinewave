# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime
import html
from io import StringIO
import json
import re
from time import sleep
import subprocess

from apps.home import blueprint
from flask import current_app, render_template, request, redirect, url_for
from flask_login import login_required
from jinja2 import TemplateNotFound
import pandas as pd
import requests

from shinewave_webapp import database_connector, documentation_builder, file_storage_connector
from shinewave_webapp.file_validator import FileValidator

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
        'core': {
            'multiple': False,
            'data': json_list
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


def get_template_id_by_name(account_id, template_name, folder_name, template_type):
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
                AND t.template_type = ?
        """,
        sql_parameters=[account_id, template_name, folder_name, template_type],
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
        template_type_name = request.form.get('template_type_name')
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
            file_storage_connector.edit_template(
                contents=template_contents,
                node_parent_type=node_parent_type,
                node_detail_type=node_detail_type,
                workflow_category=workflow_category,
                template_id=template_id
            )
            print(f"""@@@file_storage_connector.edit_template(
                contents={template_contents},
                node_parent_type={node_parent_type},
                node_detail_type={node_detail_type},
                workflow_category={workflow_category},
                template_id={template_id}
                {request.form}
            )""")
        else:
            print('!!!', request.form)

    return redirect(url_for(f'home_blueprint.edit_{template_type_name.lower()}_templates'))


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
        template_type_name = request.form.get('template_type_name')

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
                            AND t.template_type = ?
                    """,
                    'sql_parameters': (ACCOUNT_ID, submitted_name, folder, template_type)
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
            redirect_page = f'home_blueprint.edit_{template_type_name.lower()}_templates'
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
                account_id=ACCOUNT_ID, template_name=template, folder_name=folder, template_type=template_type
            )
            return redirect(
                url_for(
                    'home_blueprint.edit_templates_app',
                    template_id=template_id,
                    template_type=template_type,
                    template_type_name=template_type_name
                )
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
    workflow_data = database_connector.run_query(
        """
            SELECT
                id,
                enabled
            FROM workflows
            WHERE
                account_id=?
                AND active='TRUE'
                AND id=?
        """,
        sql_parameters=[account_id, workflow_id],
        return_data_format=dict
    )
    if not workflow_data:
        return render_template('home/page-404.html'), 404

    workflow_id = workflow_data['id'][0]
    enabled = workflow_data['enabled'][0]

    if enabled is None or str(enabled).lower() != 'true':
        enabled_toggle = ''
    else:
        enabled_toggle = 'checked'

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
            segment=get_segment(request),
            enabled_toggle=enabled_toggle
        )


@blueprint.route('/<template>', methods=['POST'])
def route_api_endpoint(template):
    try:
        segment = get_segment(request)
        data = request.get_json()
        print(segment, data)
        endpoints_data = database_connector.run_query(
            """
                SELECT
                    wn.workflow_id,
                    wn.id AS node_id,
                    wn.custom_data
                FROM workflow_nodes wn
                INNER JOIN workflows w ON
                    wn.workflow_id = w.id
                    AND wn.active = w.active
                WHERE
                    w.account_id = ?
                    AND wn.node_type = 'nodes.trigger.APITrigger'
                    AND wn.active = 'TRUE'
            """,
            sql_parameters=[ACCOUNT_ID],
            return_data_format=dict
        )

        all_endpoints = []

        if not endpoints_data:
            return "Endpoint not found", 404

        for custom_data in endpoints_data.get('custom_data'):
            try:
                custom_data = json.loads(custom_data)
                all_endpoints.append(custom_data['api_endpoint'])
            except Exception as e:
                print(e)

        if segment not in all_endpoints:
            return "Endpoint not found", 404

        return json.dumps({'ok': True})
    except Exception as e:
        print(e)
        return "Bad Request", 400


@blueprint.route('/<template>', methods=['GET'])
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        segment = get_segment(request)

        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except Exception as e:
        print(e)
        return render_template('home/page-500.html'), 500


@blueprint.route('/et-edit-sms-templates.html', methods=['GET'])
@blueprint.route('/et-edit-sms-templates', methods=['GET'])
@login_required
def edit_sms_templates():
    return render_template_editor(
        template_type_name='SMS',
        outbound_template_type='nodes.outreach.SMSOutreach',
        inbound_template_type='nodes.trigger.TemplatizedResponseReceivedTrigger',
        disable_inbound_templates=False
    )


@blueprint.route('/et-edit-email-templates.html', methods=['GET'])
@blueprint.route('/et-edit-email-templates', methods=['GET'])
@login_required
def edit_email_templates():
    return render_template_editor(
        template_type_name='Email',
        outbound_template_type='nodes.outreach.EmailOutreach',
        inbound_template_type='',
        disable_inbound_templates=True
    )


def render_template_editor(
    template_type_name, outbound_template_type, inbound_template_type, disable_inbound_templates
):
    account_id = ACCOUNT_ID

    def _generate_formatted_tree(account_id, template_type):
        template_data = database_connector.run_query(
            """
                SELECT
                    wc.name AS workflow_category,
                    t.name,
                    t.id
                FROM workflow_categories wc
                LEFT JOIN templates t ON
                    wc.id=t.workflow_category_id
                    AND wc.active=t.active
                    AND t.template_type = ?
                WHERE
                    wc.account_id = ?
                    AND wc.active='TRUE'
                ORDER BY wc.name, t.name
            """,
            sql_parameters=[template_type, account_id],
            return_data_format=list
        )

        tree_format = {}
        for workflow_category, template_name, template_id in template_data:
            tree_format.setdefault(workflow_category, [])
            tree_format[workflow_category].append((template_name, template_id))

        return tree_dict_to_json(
            tree_format, tree_type='Template', include_folder_operations=False, include_rename_operations=False
        )

    outbound_tree_format_code = _generate_formatted_tree(account_id, outbound_template_type)
    inbound_tree_format_code = _generate_formatted_tree(account_id, inbound_template_type)

    validation_failure_code_dict = get_validation_failure_codes('template')

    validation_failure_code = request.args.get('validation_failure_code')
    validation_failure_text = validation_failure_code_dict.get(validation_failure_code, '')

    if disable_inbound_templates:
        edit_inbound_disabled_start = '<!--'
        edit_inbound_disabled_end = '-->'
    else:
        edit_inbound_disabled_start = ''
        edit_inbound_disabled_end = ''

    return render_template(
        'home/et-edit-templates.html',
        validation_error_card=get_validation_error_card(validation_failure_text),
        outbound_tree_format_text='',
        outbound_tree_format_code=outbound_tree_format_code,
        outbound_template_type=outbound_template_type,
        inbound_tree_format_text='',
        inbound_tree_format_code=inbound_tree_format_code,
        inbound_template_type=inbound_template_type,
        template_type_name=template_type_name,
        segment=get_segment(request),
        edit_inbound_disabled_start=edit_inbound_disabled_start,
        edit_inbound_disabled_end=edit_inbound_disabled_end
    )


@blueprint.route('/et-edit-templates-app.html', methods=['GET'])
@blueprint.route('/et-edit-templates-app', methods=['GET'])
@login_required
def edit_templates_app():
    account_id = ACCOUNT_ID
    template_id = request.args.get('template_id')
    template_type_name = request.args.get('template_type_name')
    template_data = database_connector.run_query(
        """
            SELECT
                wc.name AS workflow_category,
                t.name AS template_name,
                t.template_type
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
    template_type = template_data.get('template_type')

    if template_name and folder_name and template_type:
        folder_name = folder_name[0]
        template_name = template_name[0]
        template_type = template_type[0]
        node_master_type, node_parent_type, node_detail_type = template_type.split('.')
        try:
            template_contents = file_storage_connector.fetch_template(
                node_parent_type=node_parent_type,
                node_detail_type=node_detail_type,
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
            template_type_name=template_type_name,
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

    except Exception as e:
        print(e)
        return None


@blueprint.route('/process_active_toggle', methods=["POST"])
@login_required
def process_active_toggle():
    toggle_data = request.get_json()
    workflow_id = toggle_data.get('workflow_id')
    enabled = str(toggle_data.get('enabled')).upper()
    database_connector.run_query(
        """
            UPDATE workflows SET enabled = ?
            WHERE
                account_id = ?
                AND id = ?
                AND active = 'TRUE'
        """,
        sql_parameters=[enabled, ACCOUNT_ID, workflow_id],
        commit=True
    )
    return json.dumps({'ok': True})


@blueprint.route('/toggle-workflows')
@blueprint.route('/toggle-workflows.html')
@login_required
def toggle_workflows():
    def _wrap_toggle(workflow_id, enabled):
        if str(enabled).lower() == 'true':
            checked = 'checked'
        else:
            checked = ''

        toggle_switch_id = f'toggle-switch-{workflow_id}'

        toggle_switch_html = f"""
            <label
                class="toggle-switchy" for="{toggle_switch_id}" data-size="sm" data-style="rounded" data-color="green"
                data-text="false">
                    <input {checked} type="checkbox" id="{toggle_switch_id}">
                    <span class="toggle" onclick="toggleSwitch({workflow_id}, '{toggle_switch_id}')">
                        <span class="switch"></span>
                    </span>
            </label>
        """

        return toggle_switch_html.replace('\n', ' ')

    workflow_data = database_connector.run_query(
        """
            SELECT
                w.id AS "Workflow ID",
                wc.name AS "Workflow Category",
                w.name AS "Workflow Name",
                w.enabled AS "Enabled"
            FROM workflows w
            INNER JOIN workflow_categories wc ON w.workflow_category_id = wc.id
            WHERE
                w.account_id = ?
                AND w.active = 'TRUE'
        """,
        sql_parameters=[ACCOUNT_ID],
        return_data_format=dict
    )
    table_df = pd.DataFrame(workflow_data)

    for column in ['Workflow Category', 'Workflow Name']:
        table_df[column] = table_df[column].map(html.escape)

    table_df['Enabled'] = table_df.apply(lambda row: _wrap_toggle(row['Workflow ID'], row['Enabled']), axis=1)

    workflows_table = table_df.to_html(
        table_id='basic-datatables',
        border=0,
        classes=['display', 'table', 'table-striped', 'table-hover'],
        escape=False,
        index=False,
        justify='inherit'
    )

    return render_template('home/toggle-workflows.html', workflows_table=workflows_table, segment=get_segment(request))


@blueprint.route('/api-triggers')
@blueprint.route('/api-triggers.html')
@login_required
def api_triggers():

    def _construct_api_endpoint_info(custom_data):
        try:
            custom_data = json.loads(custom_data)
            return custom_data.get('api_endpoint', '')
        except TypeError as e:
            return ''

    workflow_data = database_connector.run_query(
        """
            SELECT
                wn.workflow_id AS "Workflow ID",
                wc.name AS "Workflow Category",
                w.name AS "Workflow Name",
                wn.name AS "Endpoint Name",
                wn.custom_data AS "API Endpoint",
                a.subdomain
            FROM workflow_nodes wn
            INNER JOIN workflows w ON
                wn.workflow_id = w.id
                AND wn.active = w.active
            INNER JOIN workflow_categories wc ON w.workflow_category_id = wc.id
            INNER JOIN account a ON w.account_id=a.id
            WHERE
                w.account_id = ?
                AND wn.node_type = 'nodes.trigger.APITrigger'
                AND wn.active = 'TRUE'
            ORDER BY wc.name, w.name, wn.name
        """,
        sql_parameters=[ACCOUNT_ID],
        return_data_format=dict
    )

    table_df = pd.DataFrame(workflow_data)

    table_df['API Endpoint'] = table_df['API Endpoint'].map(_construct_api_endpoint_info)
    table_df['API Endpoint'] = table_df.apply(
        lambda row: f"https://{row['subdomain']}.shinewave.io/{row['API Endpoint']}" if row['API Endpoint'] else '', axis=1)
    del table_df['subdomain']

    triggers_table = table_df.to_html(
        table_id='basic-datatables',
        border=0,
        classes=['display', 'table', 'table-striped', 'table-hover'],
        index=False,
        justify='inherit'
    )

    return render_template('home/api-triggers.html', triggers_table=triggers_table, segment=get_segment(request))


@blueprint.route('/api-outbound-templates')
@blueprint.route('/api-outbound-templates.html')
@login_required
def api_outbound_templates():
    return render_template('home/api-outbound-templates.html', triggers_table='x', segment=get_segment(request))


@blueprint.route('/rm-file-upload')
@blueprint.route('/rm-file-upload.html')
@login_required
def recipient_file_upload_ui():
    random_key = database_connector.get_random_key([datetime.now()])
    return render_template('home/rm-file-upload.html', segment=get_segment(request), upload_id=random_key)


@blueprint.route('/recipient-file-upload', methods=['POST', 'GET'])
@login_required
def recipient_file_upload():
    file = request.files.get('file')
    upload_id = request.args.get('upload_id')

    file_storage_connector.send_file_upload(
        account_id=ACCOUNT_ID, upload_id=upload_id, upload_file=file, upload_type='raw'
    )

    return json.dumps({'ok': True})


@blueprint.route('/rm-file-upload-validation')
@blueprint.route('/rm-file-upload-validation.html')
@login_required
def recipient_file_upload_validation():
    upload_id = request.args.get('upload_id')
    upload_file_contents = file_storage_connector.read_upload(
        account_id=ACCOUNT_ID, upload_id=upload_id, upload_type='raw'
    )
    file_validator = FileValidator(upload_file_contents, upload_id)
    file_validator.validate_file()
    in_process_file = file_validator.upload_table.to_csv(index=False)
    file_storage_connector.send_file_upload(
        account_id=ACCOUNT_ID, upload_id=upload_id, upload_file=in_process_file, upload_type='in_process'
    )

    return render_template(
        'home/rm-file-upload-validation.html',
        segment=get_segment(request),
        recipients_table=file_validator.display_table,
        column_lookup_function=file_validator.column_lookup_function,
        header=file_validator.header
    )


@blueprint.route('/rm-file-upload-overwrite-settings')
@blueprint.route('/rm-file-upload-overwrite-settings.html')
@login_required
def recipient_file_upload_overwrite_settings():
    upload_id = request.args.get('upload_id')
    upload_file_contents = file_storage_connector.read_upload(
        account_id=ACCOUNT_ID, upload_id=upload_id, upload_type='in_process'
    )
    upload_file = StringIO(upload_file_contents)
    upload_df = pd.read_csv(upload_file)
    upload_df['upload_id'] = upload_id

    database_connector.run_query(
        "DELETE FROM members_staging WHERE upload_id = ?", sql_parameters=[upload_id], commit=True
    )
    conn = database_connector.get_conn()
    try:
        upload_df.to_sql('members_staging', conn, if_exists='append', index=False)
        conn.close()
    except Exception as e:
        conn.close()
        raise ValueError(e)

    return render_template(
        'home/rm-file-upload-overwrite-settings.html',
        segment=get_segment(request),
        upload_id=upload_id
    )


@blueprint.route('/documentation')
@blueprint.route('/documentation.html')
@login_required
def documentation():
    section = request.args.get('section')
    subsection = request.args.get('subsection')

    return render_template(
        'home/documentation.html',
        segment=get_segment(request),
        header=documentation_builder.get_section_name(active_section=section),
        content='',
        documentation_menu=documentation_builder.build_documentation_nav(active_section=section)
    )