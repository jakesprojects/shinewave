# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

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
    if template_name == 'workflow-builder':
        tree_format_text = ''
        tree_format_code = """
            [
                { "text" : "Root node", "children" : [
                        { "text" : "Child node 1", "id" : 1 },
                        { "text" : "Child node 2" },
                        { "text" : "Child node 3" }
                ]}
            ]
        """
        return {'tree_format_text': tree_format_text, 'tree_format_code': tree_format_code}
    else:
        return {}
