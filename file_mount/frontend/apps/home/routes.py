# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound


@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if template.endswith('.html'):
            template_name = template.rsplit('.html', 1)[0]
        else:
            template_name = template
            template += '.html'

        special_formatting = handle_special_template(template_name)

        # Detect the current page
        segment = get_segment(request)

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


def handle_special_template(template_name):
    def _workflow_tree_dict_to_json(workflow_tree_dict):
        json_list = []

        for parent_node in workflow_tree_dict:

            children_list = []

            for child_node_name, child_node_id in workflow_tree_dict[parent_node]:
                children_list.append({'text': child_node_name, 'id': child_node_id})

            json_list.append({'text': parent_node, 'children': children_list})

        return json.dumps(json_list)

    if template_name == 'workflow-builder':

        tree_format = {
            'Parent Node Test 1': [('child node 1', 1), ('child node 2', 2)],
            'Parent Node Test 2': [('child node 3', 3), ('child node 4', 4)]
        }

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

        return {'tree_format_text': tree_format_text, 'tree_format_code': tree_format_code}
    else:
        return {}
