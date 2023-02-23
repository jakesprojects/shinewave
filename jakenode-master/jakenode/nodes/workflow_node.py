import html

from NodeGraphQt import BaseNode
from NodeGraphQt.constants import ViewerEnum, NodePropWidgetEnum
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget, NodeLineEdit
from Qt import QtCore, QtWidgets

from jakenode.database_connector import run_query

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

        if has_output:
            self.add_output('output')
        if has_input:
            self.add_input('input')

        self.set_account_id()
        self.set_workflow_category_id()

        node_type = self.get_property('type_')

        self.node_master_type, self.node_parent_type, self.node_detail_type = node_type.split('.')

    def set_account_id(self, account_id=None):
        self.account_id = account_id

    def set_workflow_category_id(self, workflow_category_id=None):
        self.workflow_category_id = workflow_category_id

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
                AND t.active='TRUE'
        """

        if template_id is not None:
            lookup_where_clause += f' AND id={template_id}'

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

    def load_templates(self):
        """
            Dummy method to prevent breakages if this is called on node types that don't support it
        """
        pass

    def validate_node(self):
        """
            Dummy method to prevent breakages if this is called on node types that don't need to be validated
        """
        pass

    def get_display_info(self, node_templates_root=None):
        """
            Dummy method to prevent breakages if this is called on node types that don't support it
        """
        return '', ''


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
