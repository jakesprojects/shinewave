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

        # properties bin widget.
        # self._prop_bin = PropertiesBinWidget(node_graph=self)
        # self._prop_bin.setWindowFlags(QtCore.Qt.Tool)

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