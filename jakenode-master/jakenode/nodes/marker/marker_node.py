from NodeGraphQt.constants import NodePropWidgetEnum

from jakenode.nodes.workflow_node import NodeTextEdit, WorkflowNode


class MarkerNode(WorkflowNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.marker'

    # initial default node name.
    NODE_NAME = 'Marker'

    def __init__(self, marker_type='Generic'):
        super(MarkerNode, self).__init__(has_output=False, has_input=True)

        self.label_name = 'marker_type'
        widget = NodeTextEdit(self.view, 'marker_type', 'Marker Type', marker_type, is_read_only=True)
        widget.value_changed.connect(lambda k, v: self.set_property(k, v))
        self.view.add_widget(widget)
        self.view.draw_node()

    def validate_has_upstream_trigger(self):
        super().validate_has_upstream_trigger(
            custom_error_message='Marker node is orphaned (lacks an upstream trigger node).'
        )

    def validate_node(self):
        """
            Validates that node has an upstream trigger.
        """

        self.validate_has_upstream_trigger()


class Converted(MarkerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.marker'

    # initial default node name.
    NODE_NAME = 'Converted'

    def __init__(self):
        super(Converted, self).__init__(marker_type='Converted')
        self.set_property('color', (6, 64, 0))


class NotConverted(MarkerNode):
    """
    """

    # unique node identifier.
    __identifier__ = 'nodes.marker'

    # initial default node name.
    NODE_NAME = 'Not Converted'

    def __init__(self):
        super(NotConverted, self).__init__(marker_type='Not Converted')
        self.set_property('color', (64, 0, 0))
