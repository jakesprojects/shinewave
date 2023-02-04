from datetime import datetime

from NodeGraphQt import NodeGraph

class GraphHandler(NodeGraph):

    def __init__(self, parent=None):
        self.init_time = datetime.now()
        self.display_delay_seconds = 5
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
        node_types_dict = {
            'nodes.trigger.APITrigger': {'lookup_key': 'api_presets'}
        }
        node_type = node.get_property('type_')
        fetch_data_dict = node_types_dict.get(node_type)
        if fetch_data_dict:
            lookup_key = fetch_data_dict.get('lookup_key')
            print(node.get_property(lookup_key))
