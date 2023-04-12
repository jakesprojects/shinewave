from datetime import datetime
from itertools import chain
import json

from jakenode import node_handler
from jakenode.context_menu import build_context_menu
from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import ViewerEnum
from shinewave_webapp.database_connector import run_query


class GraphHandler(NodeGraph):

    def __init__(
        self, queue=None, socketio=None, parent=None, account_id=None, workflow_category_id=None, workflow_id=None
    ):
        self.queue = queue
        self.socketio = socketio
        self.init_time = datetime.now()
        self.display_delay_seconds = 2
        super(GraphHandler, self).__init__(parent)

        # wire signal.
        self.node_selection_changed.connect(self.handle_node_selected)
        self.property_changed.connect(self.handle_property_change)
        self.set_account_properties(
            account_id=account_id, workflow_category_id=workflow_category_id, workflow_id=workflow_id
        )

        node_types = node_handler.fetch_all_node_types()
        self.register_nodes(node_types)
        self.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)
        self.set_grid_color(105, 105, 105)
        self.set_background_color(112, 112, 112)
        build_context_menu(self)

    def update_workflow_activity(self):
        if self.account_id and self.workflow_id:
            run_query(
                """
                    UPDATE workflow_routes SET last_activity = datetime()
                    WHERE
                        account_id = ?
                        AND workflow_id = ?
                        AND active = 'TRUE'
                """,
                sql_parameters=[self.account_id, self.workflow_id],
                commit=True
            )

    def handle_node_selected(self, node):
        self.update_workflow_activity()
        if (datetime.now() - self.init_time).seconds > self.display_delay_seconds:
            for sub_node in self.all_nodes():
                if sub_node.view.isSelected():
                    self.display_node_info(sub_node)

    def handle_property_change(self, node):
        self.update_workflow_activity()
        if (datetime.now() - self.init_time).seconds > self.display_delay_seconds:
            if node.view.isSelected():
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

    def set_account_properties(self, account_id, workflow_category_id, workflow_id):
        self.account_id = account_id
        self.workflow_category_id = workflow_category_id
        self.workflow_id = workflow_id

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
        self.update_workflow_activity()
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
        node.set_workflow_id(workflow_id=self.workflow_id)
        node.load_templates()

        return node

    def validate_graph(self):
        validation_errors = {}

        # Validate individual nodes, note if graph is empty
        graph_empty = True
        unique_nodes = ['nodes.trigger.InboundWorkflowChange']
        unique_node_registry = {}

        for node in self.all_nodes():
            graph_empty = False

            node_type = node.get_property('type_')

            if node_type in unique_nodes:
                unique_node_registry.setdefault(node_type, [])
                unique_node_registry[node_type].append(node.name())

            try:
                node.validate_node()
            except ValueError as e:
                validation_errors[node.name()] = str(e)

        # Validate that unique nodes don't have duplicates
        for node_type, node_name_list in unique_node_registry.items():
            node_count = len(node_name_list)
            if node_count > 1:
                for node_name in node_name_list:
                    validation_errors[node_name] = 'Only one node of this type is allowed, but '
                    validation_errors[node_name] += f'{node_count} were found in workflow.'

        # Compile all validation errors
        compiled_error_msg = ['The following validation errors occurred:']

        if graph_empty:
            compiled_error_msg.append('The workspace is empty.')
        elif validation_errors:
            for node_name, error in validation_errors.items():
                compiled_error_msg.append(f'  {node_name}: {error}')
        else:
            compiled_error_msg = []

        # Raise errors if found
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

            node.allow_forced_template_id_changes = False
            for prop_name, prop_value in node_custom_properties.items():
                node.safe_set_property(prop_name, prop_value)

            node.set_template_name_from_id()
            node.allow_forced_template_id_changes = True

            prior_nodes[object_id] = node

        for details in graph_dict.get('connections', []):
            port_object_id, port_type = details['in']
            upstream_node_id = details['out'][0]

            node = prior_nodes[port_object_id]
            upstream_node = prior_nodes[upstream_node_id]

            node.set_input(0, upstream_node.output(0))

    def get_blank_json(self):
        blank_json = {
            "graph": {
                "acyclic": True,
                "pipe_collision": False
            },
            "nodes": {}
        }

        return json.dumps(blank_json)

    def save_graph_to_database(self):
        """
            Allows for saving directly to a SQL database, rather than the built-in behavior of saving to a JSON. Assumes
            database has a table named 'workflow_nodes' that conforms to the following schema:
                id: INTEGER
                workflow_id: INTEGER
                workflow_version: INTEGER
                object_id: TEXT
                name: TEXT
                node_type: TEXT
                inputs: TEXT
                outputs: TEXT
                custom_data: TEXT
                active: TEXT
        """
        if self.workflow_id is None:
            raise AttributeError('workflow_id has not been set.')

        max_id = run_query(
            """
                SELECT
                    COALESCE(MAX(id), 0) as max_id
                FROM workflow_nodes
            """,
            return_data_format=dict
        )
        current_id = max_id['max_id'][0]

        max_version = run_query(
            """
                SELECT
                    COALESCE(MAX(workflow_version), 0) as max_version
                FROM workflow_nodes
                WHERE workflow_id = ?
            """,
            sql_parameters=[self.workflow_id],
            return_data_format=dict
        )
        workflow_version = max_version['max_version'][0] + 1

        node_property_aliases = {'object_id': 'id', 'node_type': 'type_', 'custom_data': 'custom', 'name': 'name'}
        node_methods = {'inputs': 'connected_input_nodes', 'outputs': 'connected_output_nodes'}
        fixed_columns = {'workflow_id': self.workflow_id, 'workflow_version': workflow_version, 'active': 'TRUE'}
        data_columns = list(chain(node_property_aliases, node_methods, fixed_columns))
        data_columns += ['id']
        data_rows = []

        for node in self.all_nodes():
            node.set_template_id_from_name()
            current_row = []
            current_id += 1
            node_properties = node.properties()
            for column_name in data_columns:
                if column_name in node_property_aliases:
                    alias = node_property_aliases[column_name]
                    property_value = node_properties.get(alias)
                elif column_name in node_methods:
                    connected_node_method = getattr(node, node_methods[column_name])
                    connected_nodes = connected_node_method()
                    connected_nodes = chain(*connected_nodes.values())
                    property_value = [i.get_property('id') for i in connected_nodes]
                elif column_name in fixed_columns:
                    property_value = fixed_columns[column_name]
                elif column_name == 'id':
                    property_value = current_id
                else:
                    property_value = None

                if type(property_value) in (dict, list):
                    property_value = json.dumps(property_value)

                current_row.append(property_value)
            data_rows.append(current_row)

        if not data_rows:
            return None

        insert_parameters = []
        data_placeholder = ['?'] * len(data_columns)
        data_placeholder = ', '.join(data_placeholder)
        data_placeholder = f'\n({data_placeholder}),'
        data_columns_text = ', '.join(data_columns)
        insert_statement = f'INSERT INTO workflow_nodes ({data_columns_text}) VALUES'
        for row in data_rows:
            insert_statement += data_placeholder
            insert_parameters += row
        insert_statement = insert_statement[:-1]

        run_query(
            """
                UPDATE workflow_nodes
                SET active = 'FALSE'
                WHERE workflow_id = ?
            """,
            sql_parameters=[self.workflow_id],
            commit=True
        )
        run_query(insert_statement, sql_parameters=insert_parameters, commit=True)

    def load_graph_from_database(self):
        if self.workflow_id is None:
            raise AttributeError('workflow_id has not been set.')

        node_data = run_query(
            """
                SELECT
                    object_id,
                    node_type,
                    name,
                    inputs,
                    outputs,
                    custom_data
                FROM workflow_nodes
                WHERE
                    workflow_id = ?
                    AND active = 'TRUE'
            """,
            sql_parameters=[self.workflow_id],
            return_data_format=list
        )

        prior_nodes = {}
        all_inputs = {}

        for object_id, node_type, node_name, inputs, outputs, node_custom_properties in node_data:

            inputs = json.loads(inputs)
            outputs = json.loads(outputs)
            if node_custom_properties:
                node_custom_properties = json.loads(node_custom_properties)
            else:
                node_custom_properties = {}

            node = self.create_node(node_type=node_type, name=node_name)

            node.allow_forced_template_id_changes = False
            for prop_name, prop_value in node_custom_properties.items():
                node.safe_set_property(prop_name, prop_value)

            node.set_template_name_from_id()
            node.allow_forced_template_id_changes = True

            prior_nodes[object_id] = node
            all_inputs[object_id] = inputs

        for object_id, input_object_list in all_inputs.items():
            node = prior_nodes[object_id]
            for input_object_id in input_object_list:
                upstream_node = prior_nodes[input_object_id]
                node.set_input(0, upstream_node.output(0))

    def get_entry_points(self):
        entry_points = []
        for node in self.all_nodes():
            if not node.connected_input_nodes():
                entry_points.append(node)
        return entry_points

    def get_paths(self):
        def _get_paths(explored_paths, unexplored_paths):
            if unexplored_paths:
                current_path = unexplored_paths.pop(0)
                current_node = current_path[-1]
                output_nodes = current_node.connected_output_nodes().values()
                children = list(chain(*output_nodes))
                if children:
                    for child in children:
                        unexplored_paths.append(current_path + [child])
                    current_path = []
                else:
                    explored_paths.append(current_path)
                    current_path = []
            if unexplored_paths:
                return _get_paths(explored_paths, unexplored_paths)
            else:
                return explored_paths

        entry_points = self.get_entry_points()
        
        return _get_paths([], [entry_points])
