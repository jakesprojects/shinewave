from datetime import datetime

from jakenode import node_handler
from NodeGraphQt import NodeGraph

class GraphHandler(NodeGraph):

    def __init__(self, queue=None, socketio=None, parent=None, account_id=None, workflow_category_id=None):
        self.queue = queue
        self.socketio = socketio
        self.init_time = datetime.now()
        self.display_delay_seconds = 2
        super(GraphHandler, self).__init__(parent)

        # wire signal.
        self.node_selection_changed.connect(self.handle_node_selected)
        self.property_changed.connect(self.handle_property_change)
        self.set_account_properties(account_id=account_id, workflow_category_id=workflow_category_id)

        node_types = node_handler.fetch_all_node_types()
        self.register_nodes(node_types)

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

    def set_account_properties(self, account_id, workflow_category_id):
        self.account_id = account_id
        self.workflow_category_id = workflow_category_id

    def create_node(
        self,
        node_type,
        name=None,
        selected=True,
        # color=None,
        text_color=None,
        pos=None,
        push_undo=True,
    ):
        if not text_color:
            text_color = node_handler.fetch_node_text_color(node_type)

        node = super().create_node(
            node_type=node_type,
            name=name,
            selected=selected,
            # color=color,
            text_color=text_color,
            pos=pos,
            push_undo=push_undo
        )

        node.set_account_id(account_id=self.account_id)
        node.set_workflow_category_id(workflow_category_id=self.workflow_category_id)
        node.load_templates()

        return node

    def validate_nodes(self):
        validation_errors = {}
        graph_empty = True
        compiled_error_msg = ['The following validation errors occurred:']

        for node in self.all_nodes():
            graph_empty = False
            try:
                node.validate_node()
            except ValueError as e:
                validation_errors[node.name()] = str(e)

        if graph_empty:
            compiled_error_msg.append('The workspace is empty.')
        elif validation_errors:
            for node_name, error in validation_errors.items():
                compiled_error_msg.append(f'  {node_name}: {error}')
        else:
            compiled_error_msg = []

        if compiled_error_msg:
            compiled_error_msg = '\n\n'.join(compiled_error_msg)
            raise ValueError(compiled_error_msg)

    def load_graph_from_dict(self, graph_dict):
        """
            Overwrites default deserialization behavior, because custom properties are not well-supported. This method
            creates a new graph from scratch, using the deserialized JSON that NodeGraphQt saves by default to do so.
            Parameters
            ----------
            graph_dict : dict
                Deserialized JSON as saved by the NodeGraphQt library. Tip: Use json.loads before calling this method if
                reading in a file.
        """

        prior_nodes = {}

        for object_id, details in graph_dict.get('nodes', {}).items():
            node_type = details['type_']
            node_name = details['name']
            node_custom_properties = details['custom']

            node = self.create_node(node_type=node_type, name=node_name)
            print()
            for prop_name, prop_value in node_custom_properties.items():
                node.set_property(prop_name, prop_value)

            prior_nodes[object_id] = node

        for details in graph_dict.get('connections', []):
            port_object_id, port_type = details['in']
            upstream_node_id = details['out'][0]

            node = prior_nodes[port_object_id]
            upstream_node = prior_nodes[upstream_node_id]

            node.set_input(0, upstream_node.output(0))
