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

    def __init__(self, has_output, has_input):
        super(WorkflowNode, self).__init__()
        if has_output:
            self.add_output('output')
        if has_input:
            self.add_input('input')
        
        # self.set_port_deletion_allowed(True)

    # def adjust_port(self, direction, steps=1):
    #     if direction == 'out':
    #         ports = len(self.output_ports())
    #         increment_method = self.add_output
    #         decrement_method = self.delete_output
    #     elif direction == 'in':
    #         ports = len(self.input_ports())
    #         increment_method = self.add_input
    #         decrement_method = self.delete_input

    #     for step in range(abs(steps)):
    #         if steps > 0:
    #             ports += 1
    #             increment_method(f'{direction}_{ports}')
    #         else:
    #             print(ports)
    #             ports -= 1
    #             decrement_method(ports)

    # def add_label(self, name, label='', text='', tab=None):
    #     """
    #     """
    #     self.label_name = name
    #     text = text.replace('\n', '<br>')
    #     self.create_property(
    #         name,
    #         value=text,
    #         widget_type=NodePropWidgetEnum.QTEXT_EDIT.value,
    #         tab=tab
    #     )
    #     widget = NodeTextEdit(self.view, name, label, text, is_read_only=True)
    #     widget.value_changed.connect(lambda k, v: self.set_property(k, v))
    #     self.view.add_widget(widget)
    #     #: redraw node to address calls outside the "__init__" func.
    #     self.view.draw_node()

    # def update_label(self, text=''):
    #     """
    #     """
    #     self.set_property(self.label_name, text)
    #     self.view.draw_node()
    # # def decrement_output(self, steps=1):
    # #     for step in range(steps):
    # #         output_number = len(self.output_ports()) + 1
    # #         self.add_output(f'output_{output_number}')

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