from NodeGraphQt import BaseNode
from NodeGraphQt.constants import ViewerEnum, NodePropWidgetEnum
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget, NodeLineEdit
from Qt import QtCore, QtWidgets

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
        workflow_category=None,
        database_connection_type='sqlite3',
        database_connection_kwargs={}
    ):
        super(WorkflowNode, self).__init__()

        if has_output:
            self.add_output('output')
        if has_input:
            self.add_input('input')
        self.workflow_category = workflow_category
        self.set_database_connection_info()

        node_type = self.get_property('type_')

        self.node_master_type, self.node_parent_type, self.node_detail_type = node_type.split('.')

    def set_database_connection_info(
        self, account_id=None, database_connection_type='sqlite3', database_connection_kwargs={}
    ):
        self.account_id = account_id
        self.database_connection_type = database_connection_type
        self.database_connection_kwargs = database_connection_kwargs

    def get_node_template_data(self, template_id=None):
        if self.account_id is None:
            raise AttributeError('account_id has not been set.')

        if self.database_connection_type is None:
            return None

        lookup_where_clause = f"WHERE account_id={self.account_id} AND active='TRUE'"
        if template_id is not None:
            lookup_where_clause += f' AND id={template_id}'

        if self.database_connection_type == 'sqlite3':
            import sqlite3
            connection_function = sqlite3.connect

        with connection_function(**self.database_connection_kwargs) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM templates {lookup_where_clause}")
            node_data = cur.fetchall()
            field_names = [i[0] for i in cur.description]

        template_data = {}
        for n, field in enumerate(field_names):
            template_data[field] = []
            for row in node_data:
                template_data[field].append(row[n])
        return template_data



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