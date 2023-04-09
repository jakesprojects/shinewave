import html
from itertools import chain

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import ViewerEnum
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
from Qt import QtCore, QtWidgets

from jakenode.database_connector import fetch_template, run_query


class WorkflowNode(BaseNode):
    """
    A basic node used to construct workflows.
    """

    # unique node identifier.
    __identifier__ = 'nodes.workflow'

    # initial default node name.
    NODE_NAME = 'Workflow Base'

    def __init__(
        self,
        has_output,
        has_input,
        database_connection_type='sqlite3',
        database_connection_kwargs={}
    ):
        super(WorkflowNode, self).__init__()

        self.allow_forced_template_id_changes = True

        if has_output:
            self.add_output('output', multi_output=True)
        if has_input:
            self.add_input('input', multi_input=True)

        self.set_account_id()
        self.set_workflow_category_id()
        self.set_workflow_id()

        node_type = self.get_property('type_')

        self.node_master_type, self.node_parent_type, self.node_detail_type = node_type.split('.')

    def set_account_id(self, account_id=None):
        self.account_id = account_id

    def set_workflow_category_id(self, workflow_category_id=None):
        self.workflow_category_id = workflow_category_id

    def set_workflow_id(self, workflow_id=None):
        self.workflow_id = workflow_id

    def get_node_name(self, html_safe=False):
        node_name = self.get_property('name')
        if html_safe:
            return html.escape(node_name)
        else:
            return node_name

    def get_node_template_data(self, template_id=None):
        if self.account_id is None:
            raise AttributeError('account_id has not been set.')
        if self.workflow_category_id is None:
            raise AttributeError('workflow_category_id has not been set.')

        lookup_where_clause = f"""
            WHERE
                t.account_id={self.account_id}
                AND t.workflow_category_id={self.workflow_category_id}
                AND t.template_type='{self.get_property('type_')}'
                AND t.active='TRUE'
        """

        if template_id is not None:
            lookup_where_clause += f' AND t.id={template_id}'

        template_data = run_query(
            f"""
                SELECT
                    wc.name AS workflow_category,
                    t.*
                FROM templates t
                INNER JOIN workflow_categories wc ON t.workflow_category_id=wc.id
                {lookup_where_clause}
            """,
            return_data_format=dict
        )

        return template_data

    def get_node_template_contents(self, template_id, workflow_category=None):
        if workflow_category is None:
            template_data = self.get_node_template_data(template_id)
            workflow_category = template_data['workflow_category']

        if isinstance(workflow_category, list) and len(workflow_category) > 0:
            workflow_category = workflow_category[0]
        elif not isinstance(workflow_category, str):
            raise ValueError(f'Workflow data not found for template id {template_id}')

        return fetch_template(self.node_parent_type, self.node_detail_type, workflow_category, template_id)

    def get_node_chain(self, direction):
        """
            Universal method for getting all upstream or downstream nodes.
        """

        if direction == 'upstream':
            connection_method = 'connected_input_nodes'
        elif direction == 'downstream':
            connection_method = 'connected_output_nodes'
        else:
            raise ValueError('Parameter "direction" must be either "upstream" or "downstream"')

        def _get_node_chain(current_nodes, prior_nodes, connection_method):
            all_connected = []
            for current_node in current_nodes:
                get_direct_connections = getattr(current_node, connection_method)
                current_connected = get_direct_connections()
                current_connected = chain(*current_connected.values())
                current_connected = [i for i in current_connected if i not in prior_nodes]
                prior_nodes.append(current_node)
            all_connected += current_connected
            return all_connected, prior_nodes

        current_nodes = [self]
        prior_nodes = []
        while current_nodes:
            current_nodes, prior_nodes = _get_node_chain(current_nodes, prior_nodes, connection_method)

        del prior_nodes[0]

        return prior_nodes

    def get_upstream_nodes(self):
        return self.get_node_chain('upstream')

    def get_downstream_nodes(self):
        return self.get_node_chain('downstream')

    def validate_has_upstream_trigger(self, custom_error_message=None):
        if not custom_error_message:
            error_message = 'Node is orphaned (lacks an upstream trigger node).'
        else:
            error_message = custom_error_message

        upstream_nodes = self.get_upstream_nodes()
        upstream_node_parent_types = [i.node_parent_type for i in upstream_nodes]
        if 'trigger' not in upstream_node_parent_types:
            raise ValueError(error_message)

    def validate_has_downstream_outreach(self, custom_error_message=None):
        if not custom_error_message:
            error_message = 'Node is orphaned (lacks a downstream outreach node).'
        else:
            error_message = custom_error_message

        downstream_nodes = self.get_downstream_nodes()
        downstream_node_parent_types = [i.node_parent_type for i in downstream_nodes]
        if 'outreach' not in downstream_node_parent_types:
            raise ValueError(error_message)

    def safe_set_property(self, property_name, value):
        """
        """
        if self.has_property(property_name):
            self.set_property(property_name, value)
        else:
            self.create_property(property_name, value)

    def get_html_warning(self, text):
        return f'<p style="background-color:red;">{text}</p>'

    def get_html_validation_text(self, validation_method):
        try:
            validation_method()
        except ValueError as exception:
            return self.get_html_warning(exception)

    def get_blank_menu_item(self):
        node_name = self.get_node_name(html_safe=True)
        return ' ' * (len(node_name) + 5)

    # Dummy methods to prevent breakages if methods are called on node types that don't support them

    def get_display_info(self, node_templates_root=None):
        return '', ''

    def load_templates(self):
        pass

    def set_template_id_from_name(self):
        pass

    def set_template_name_from_id(self):
        pass

    def validate_node(self):
        pass


class NodeTextEdit(NodeBaseWidget):
    """
    Displays as a ``QTextEdit`` in a node.

    **Inherited from:** :class:`NodeBaseWidget`

    .. note::
        `To embed a` ``QLineEdit`` `in a node see func:`
        :meth:`NodeGraphQt.BaseNode.add_text_input`
    """

    def __init__(self, parent=None, name='', label='', text='', is_read_only=False):
        super(NodeTextEdit, self).__init__(parent, name, label)
        plt = self.palette()
        bg_color = plt.alternateBase().color().getRgb()
        text_color = plt.text().color().getRgb()
        text_sel_color = plt.highlightedText().color().getRgb()
        style_dict = {
            'QTextEdit': {
                'background': 'rgba({0},{1},{2},20)'.format(*bg_color),
                'border': '1px solid rgb({0},{1},{2})'
                          .format(*ViewerEnum.GRID_COLOR.value),
                'border-radius': '3px',
                'color': 'rgba({0},{1},{2},150)'.format(*text_color),
                'selection-background-color': 'rgba({0},{1},{2},100)'
                                              .format(*text_sel_color),
            }
        }
        stylesheet = ''
        for css_class, css in style_dict.items():
            style = '{} {{\n'.format(css_class)
            for elm_name, elm_val in css.items():
                style += '  {}:{};\n'.format(elm_name, elm_val)
            style += '}\n'
            stylesheet += style
        ledit = QtWidgets.QTextEdit()
        ledit.setText(text)
        ledit.setStyleSheet(stylesheet)
        ledit.setAlignment(QtCore.Qt.AlignCenter)
        ledit.setReadOnly(is_read_only)
        # ledit.textChanged.connect(self.on_value_changed)
        ledit.clearFocus()
        self.set_custom_widget(ledit)
        self.widget().setMaximumWidth(140)
