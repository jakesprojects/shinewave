from datetime import datetime

from jakenode import node_handler
from NodeGraphQt import NodeGraph

class GraphHandler(NodeGraph):

    def __init__(self, queue=None, socketio=None, parent=None):
        self.queue = queue
        self.socketio = socketio
        self.init_time = datetime.now()
        self.display_delay_seconds = 2
        super(GraphHandler, self).__init__(parent)

        # properties bin widget.
        # self._prop_bin = PropertiesBinWidget(node_graph=self)
        # self._prop_bin.setWindowFlags(QtCore.Qt.Tool)

        # wire signal.
        self.node_selection_changed.connect(self.handle_node_selected)
        self.property_changed.connect(self.handle_property_change)

    def handle_node_selected(self, node):
        if (datetime.now() - self.init_time).seconds > self.display_delay_seconds:
            for sub_node in self.all_nodes():
                if sub_node.view.isSelected():
                    self.display_node_info(sub_node)

    def handle_property_change(self, node):
        if (datetime.now() - self.init_time).seconds > self.display_delay_seconds:
            if node.view.isSelected():
                properties = node.properties()
                node_type = properties.get('type_')
                self.display_node_info(node)

    def display_node_info(self, node):
        title, description = node_handler.fetch_node_display_info(node)
        if self.socketio is not None:
            self.socketio.emit(
                'info_update',
                {'title': title, 'description': description}
            )
        if self.queue is not None:
            self.queue.put((title, description))
        else:
            print(title, description)
