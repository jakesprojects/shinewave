from collections import OrderedDict

def get_context_menu_commands():
        """
            Returns a menu in the following format:
                {
                    <MENU_COMMAND_NAME>: (
                        <FUNCTION_NAME> !must match a method from graph_modifier!,
                        <KEYBOARD_SHORTCUT>
                    )
                }
            Sub-menus can be added by duplicating the above format within the dictionary key, and can recurse multiple
            times. Separators are added by providing an arbitrary key with a value of None.
        """

        return OrderedDict({
            'Save...': ('save_to_database', 'Ctrl+S'),
            '&Edit': OrderedDict({
                'Clear Undo History': ('clear_undo', ''),
                'Show Undo History': ('show_undo_view', ''),
                'separator_1': None,
                'Copy': ('copy_nodes', 'QtGui.QKeySequence.Copy'),
                'Cut': ('cut_nodes', 'QtGui.QKeySequence.Cut'),
                'Paste': ('paste_nodes', 'QtGui.QKeySequence.Paste'),
                'Delete': ('delete_nodes', 'QtGui.QKeySequence.Delete'),
                'separator_2': None,
                'Select All': ('select_all_nodes', 'Ctrl+A'),
                'Unselect All': ('clear_node_selection', 'Ctrl+Shift+A'),
                'Enable/Disable': ('disable_nodes', 'D'),
                'Duplicate': ('duplicate_nodes', 'Alt+C'),
                'Fit to Selection': ('fit_to_selection', 'F'),
                'separator_3': None,
                'Zoom In': ('zoom_in', '='),
                'Zoom Out': ('zoom_out', '-'),
                'Reset Zoom': ('reset_zoom', 'H')
            }),
            'separator_1': None,
            '&Add Node': OrderedDict({
                '&Outreach': OrderedDict({
                    'API': ('add_node_api_outreach', ''),
                    'Email': ('add_node_email_outreach', ''),
                    # 'IVR': ('add_node_ivr_outreach', ''),
                    'SMS': ('add_node_sms_outreach', ''),
                    'Workflow Change': ('add_node_workflow_change_outreach', '')
                }),
                '&Trigger': OrderedDict({
                    'API': ('add_node_api_trigger', ''),
                    'File Upload': ('add_node_file_upload_trigger', ''),
                    'At Time': ('add_node_at_time_trigger', ''),
                    '&Response Received': OrderedDict({
                        'Exact Response': ('add_node_exact_response_received_trigger', ''),
                        'Fuzzy Response': ('add_node_fuzzy_response_received_trigger', ''),
                        'Templatized Response': ('add_node_templatized_response_received_trigger', '')
                    }),
                    'Time Elapsed': ('add_node_time_elapsed_trigger', ''),
                    'Workflow Change': ('add_node_workflow_change_trigger', '')
                })
            }),
            'separator_2': None,
            '&Nodes': OrderedDict({
                'Auto Layout Up Stream': ('layout_graph_up', 'L'),
                'Auto Layout Down Stream': ('layout_graph_down', 'Ctrl+L'),
                'separator_1': None
            }),
            '&Pipes': OrderedDict({
                'Curved': ('curved_pipe', ''),
                'Straight': ('straight_pipe', ''),
                'Angle': ('angle_pipe', '')
            })
        })

def build_context_menu(graph):
    context_menu = graph.get_context_menu('graph')
    commands = get_context_menu_commands()
    functions_container = graph_modifier()

    def _add_commands_from_odict(context_menu, commands, functions_container=functions_container):
        for name, instructions in commands.items():
            if instructions is None:
                context_menu.add_separator()
            elif isinstance(instructions, tuple):
                function_name, shortcut = instructions
                function = getattr(functions_container, function_name)
                menu_item_kwargs = {'func': function, 'shortcut': shortcut}
                context_menu.add_command(name=name, **menu_item_kwargs)
            elif isinstance(instructions, OrderedDict):
                sub_menu = context_menu.add_menu(name)
                _add_commands_from_odict(sub_menu, instructions)

    _add_commands_from_odict(context_menu, commands)


class graph_modifier():

    def __init__(self):
        pass

    def zoom_in(self, graph):
        """
        Set the node graph to zoom in by 0.1
        """
        zoom = graph.get_zoom() + 0.1
        graph.set_zoom(zoom)


    def zoom_out(self, graph):
        """
        Set the node graph to zoom in by 0.1
        """
        zoom = graph.get_zoom() - 0.2
        graph.set_zoom(zoom)


    def reset_zoom(self, graph):
        """
        Reset zoom level.
        """
        graph.reset_zoom()


    def layout_h_mode(self, graph):
        """
        Set node graph layout direction to horizontal.
        """
        graph.set_layout_direction(0)


    def layout_v_mode(self, graph):
        """
        Set node graph layout direction to vertical.
        """
        graph.set_layout_direction(1)


    def open_session(self, graph):
        """
        Prompts a file open dialog to load a session.
        """
        current = graph.current_session()
        file_path = graph.load_dialog(current)
        if file_path:
            graph.load_session(file_path)


    def import_session(self, graph):
        """
        Prompts a file open dialog to load a session.
        """
        current = graph.current_session()
        file_path = graph.load_dialog(current)
        if file_path:
            graph.import_session(file_path)


    def save_session(self, graph):
        """
        Prompts a file save dialog to serialize a session if required.
        """
        try:
            graph.validate_graph()
            current = graph.current_session()
            if current:
                graph.save_session(current)
                msg = 'Session layout saved:\n{}'.format(current)
                viewer = graph.viewer()
                viewer.message_dialog(msg, title='Session Saved')
            else:
                _save_session_as(graph)
        except ValueError as e:
            msg = "Changes could not be saved.\n\n"
            msg += str(e)
            msg += '\n\nCorrect these errors and try again.'
            viewer = graph.viewer()
            viewer.message_dialog(msg, title='Save Failed')



    def save_session_as(self, graph):
        """
        Prompts a file save dialog to serialize a session.
        """
        current = graph.current_session()
        file_path = graph.save_dialog(current)
        if file_path:
            graph.save_session(file_path)


    def new_session(self, graph):
        """
        Prompts a warning dialog to new a node graph session.
        """
        if graph.question_dialog('Clear Current Session?', 'Clear Session'):
            graph.clear_session()


    def clear_undo(self, graph):
        """
        Prompts a warning dialog to clear undo.
        """
        viewer = graph.viewer()
        msg = 'Clear all undo history, Are you sure?'
        if viewer.question_dialog('Clear Undo History', msg):
            graph.clear_undo_stack()


    def copy_nodes(self, graph):
        """
        Copy nodes to the clipboard.
        """
        graph.copy_nodes()


    def cut_nodes(self, graph):
        """
        Cut nodes to the clip board.
        """
        graph.cut_nodes()


    def paste_nodes(self, graph):
        """
        Pastes nodes copied from the clipboard.
        """
        graph.paste_nodes()


    def delete_nodes(self, graph):
        """
        Delete selected node.
        """
        graph.delete_nodes(graph.selected_nodes())


    def select_all_nodes(self, graph):
        """
        Select all nodes.
        """
        graph.select_all()


    def clear_node_selection(self, graph):
        """
        Clear node selection.
        """
        graph.clear_selection()


    def disable_nodes(self, graph):
        """
        Toggle disable on selected nodes.
        """
        graph.disable_nodes(graph.selected_nodes())


    def duplicate_nodes(self, graph):
        """
        Duplicated selected nodes.
        """
        graph.duplicate_nodes(graph.selected_nodes())


    def expand_group_node(self, graph):
        """
        Expand selected group node.
        """
        selected_nodes = graph.selected_nodes()
        if not selected_nodes:
            graph.message_dialog('Please select a "GroupNode" to expand.')
            return
        graph.expand_group_node(selected_nodes[0])


    def fit_to_selection(self, graph):
        """
        Sets the zoom level to fit selected nodes.
        """
        graph.fit_to_selection()


    def show_undo_view(self, graph):
        """
        Show the undo list widget.
        """
        graph.undo_view.show()


    def curved_pipe(self, graph):
        """
        Set node graph pipes layout as curved.
        """
        from NodeGraphQt.constants import PipeLayoutEnum
        graph.set_pipe_style(PipeLayoutEnum.CURVED.value)


    def straight_pipe(self, graph):
        """
        Set node graph pipes layout as straight.
        """
        from NodeGraphQt.constants import PipeLayoutEnum
        graph.set_pipe_style(PipeLayoutEnum.STRAIGHT.value)


    def angle_pipe(self, graph):
        """
        Set node graph pipes layout as angled.
        """
        from NodeGraphQt.constants import PipeLayoutEnum
        graph.set_pipe_style(PipeLayoutEnum.ANGLE.value)


    def bg_grid_none(self, graph):
        """
        Turn off the background patterns.
        """
        from NodeGraphQt.constants import ViewerEnum
        graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)


    def bg_grid_dots(self, graph):
        """
        Set background node graph background with grid dots.
        """
        from NodeGraphQt.constants import ViewerEnum
        graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_DOTS.value)


    def bg_grid_lines(self, graph):
        """
        Set background node graph background with grid lines.
        """
        from NodeGraphQt.constants import ViewerEnum
        graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_LINES.value)


    def layout_graph_down(self, graph):
        """
        Auto layout the nodes down stream.
        """
        nodes = graph.selected_nodes() or graph.all_nodes()
        graph.auto_layout_nodes(nodes=nodes, down_stream=True)


    def layout_graph_up(self, graph):
        """
        Auto layout the nodes up stream.
        """
        nodes = graph.selected_nodes() or graph.all_nodes()
        graph.auto_layout_nodes(nodes=nodes, down_stream=False)


    def toggle_node_search(self, graph):
        """
        show/hide the node search widget.
        """
        graph.toggle_node_search()


    # OUTREACH NODE CREATION FUNCTIONS

    def add_node_api_outreach(self, graph):
        pass


    def add_node_email_outreach(self, graph):
        graph.create_node('nodes.outreach.EmailOutreach')


    def add_node_ivr_outreach(self, graph):
        pass


    def add_node_sms_outreach(self, graph):
        graph.create_node('nodes.outreach.SMSOutreach')


    def add_node_workflow_change_outreach(self, graph):
        graph.create_node('nodes.outreach.OutboundWorkflowChange')


    # TRIGGER NODE CREATION FUNCTIONS

    def add_node_api_trigger(self, graph):
        graph.create_node('nodes.trigger.APITrigger')


    def add_node_at_time_trigger(self, graph):
        graph.create_node('nodes.trigger.AtTimeTrigger')


    def add_node_exact_response_received_trigger(self, graph):
        graph.create_node('nodes.trigger.ExactResponseReceivedTrigger')


    def add_node_file_upload_trigger(self, graph):
        pass


    def add_node_fuzzy_response_received_trigger(self, graph):
        graph.create_node('nodes.trigger.FuzzyResponseReceivedTrigger')


    def add_node_templatized_response_received_trigger(self, graph):
        pass


    def add_node_time_elapsed_trigger(self, graph):
        graph.create_node('nodes.trigger.TimeElapsedTrigger')


    def add_node_workflow_change_trigger(self, graph):
        graph.create_node('nodes.trigger.InboundWorkflowChange')

    def save_to_database(self, graph):
        try:
            graph.validate_graph()
            graph.save_graph_to_database()
            viewer = graph.viewer()
            viewer.message_dialog('Save Successful!', title='Workflow Saved')
        except ValueError as e:
            msg = "Changes could not be saved.\n\n"
            msg += str(e)
            msg += '\n\nCorrect these errors and try again.'
            viewer = graph.viewer()
            viewer.message_dialog(msg, title='Save Failed')
