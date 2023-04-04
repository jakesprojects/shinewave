#!/usr/bin/python

# ------------------------------------------------------------------------------
# menu command functions
# ------------------------------------------------------------------------------


def zoom_in(graph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() + 0.1
    graph.set_zoom(zoom)


def zoom_out(graph):
    """
    Set the node graph to zoom in by 0.1
    """
    zoom = graph.get_zoom() - 0.2
    graph.set_zoom(zoom)


def reset_zoom(graph):
    """
    Reset zoom level.
    """
    graph.reset_zoom()


def layout_h_mode(graph):
    """
    Set node graph layout direction to horizontal.
    """
    graph.set_layout_direction(0)


def layout_v_mode(graph):
    """
    Set node graph layout direction to vertical.
    """
    graph.set_layout_direction(1)


def open_session(graph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    file_path = graph.load_dialog(current)
    if file_path:
        graph.load_session(file_path)


def import_session(graph):
    """
    Prompts a file open dialog to load a session.
    """
    current = graph.current_session()
    file_path = graph.load_dialog(current)
    if file_path:
        graph.import_session(file_path)


def save_session(graph):
    """
    Prompts a file save dialog to serialize a session if required.
    """
    try:
        graph.validate_nodes()
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



def save_session_as(graph):
    """
    Prompts a file save dialog to serialize a session.
    """
    current = graph.current_session()
    file_path = graph.save_dialog(current)
    if file_path:
        graph.save_session(file_path)


def new_session(graph):
    """
    Prompts a warning dialog to new a node graph session.
    """
    if graph.question_dialog('Clear Current Session?', 'Clear Session'):
        graph.clear_session()


def clear_undo(graph):
    """
    Prompts a warning dialog to clear undo.
    """
    viewer = graph.viewer()
    msg = 'Clear all undo history, Are you sure?'
    if viewer.question_dialog('Clear Undo History', msg):
        graph.clear_undo_stack()


def copy_nodes(graph):
    """
    Copy nodes to the clipboard.
    """
    graph.copy_nodes()


def cut_nodes(graph):
    """
    Cut nodes to the clip board.
    """
    graph.cut_nodes()


def paste_nodes(graph):
    """
    Pastes nodes copied from the clipboard.
    """
    graph.paste_nodes()


def delete_nodes(graph):
    """
    Delete selected node.
    """
    graph.delete_nodes(graph.selected_nodes())


def select_all_nodes(graph):
    """
    Select all nodes.
    """
    graph.select_all()


def clear_node_selection(graph):
    """
    Clear node selection.
    """
    graph.clear_selection()


def disable_nodes(graph):
    """
    Toggle disable on selected nodes.
    """
    graph.disable_nodes(graph.selected_nodes())


def duplicate_nodes(graph):
    """
    Duplicated selected nodes.
    """
    graph.duplicate_nodes(graph.selected_nodes())


def expand_group_node(graph):
    """
    Expand selected group node.
    """
    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        graph.message_dialog('Please select a "GroupNode" to expand.')
        return
    graph.expand_group_node(selected_nodes[0])


def fit_to_selection(graph):
    """
    Sets the zoom level to fit selected nodes.
    """
    graph.fit_to_selection()


def show_undo_view(graph):
    """
    Show the undo list widget.
    """
    graph.undo_view.show()


def curved_pipe(graph):
    """
    Set node graph pipes layout as curved.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.CURVED.value)


def straight_pipe(graph):
    """
    Set node graph pipes layout as straight.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.STRAIGHT.value)


def angle_pipe(graph):
    """
    Set node graph pipes layout as angled.
    """
    from NodeGraphQt.constants import PipeLayoutEnum
    graph.set_pipe_style(PipeLayoutEnum.ANGLE.value)


def bg_grid_none(graph):
    """
    Turn off the background patterns.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)


def bg_grid_dots(graph):
    """
    Set background node graph background with grid dots.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_DOTS.value)


def bg_grid_lines(graph):
    """
    Set background node graph background with grid lines.
    """
    from NodeGraphQt.constants import ViewerEnum
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_LINES.value)


def layout_graph_down(graph):
    """
    Auto layout the nodes down stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=True)


def layout_graph_up(graph):
    """
    Auto layout the nodes up stream.
    """
    nodes = graph.selected_nodes() or graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=False)


def toggle_node_search(graph):
    """
    show/hide the node search widget.
    """
    graph.toggle_node_search()


# OUTREACH NODE CREATION FUNCTIONS

def add_node_api_outreach(graph):
    pass


def add_node_email_outreach(graph):
    graph.create_node('nodes.outreach.EmailOutreach')


def add_node_ivr_outreach(graph):
    pass


def add_node_sms_outreach(graph):
    graph.create_node('nodes.outreach.SMSOutreach')


def add_node_workflow_change_outreach(graph):
    graph.create_node('nodes.outreach.OutboundWorkflowChange')


# TRIGGER NODE CREATION FUNCTIONS

def add_node_api_trigger(graph):
    graph.create_node('nodes.trigger.APITrigger')


def add_node_at_time_trigger(graph):
    graph.create_node('nodes.trigger.AtTimeTrigger')


def add_node_exact_response_received_trigger(graph):
    graph.create_node('nodes.trigger.ExactResponseReceivedTrigger')


def add_node_file_upload_trigger(graph):
    pass


def add_node_fuzzy_response_received_trigger(graph):
    pass


def add_node_templatized_response_received_trigger(graph):
    pass


def add_node_time_elapsed_trigger(graph):
    graph.create_node('nodes.trigger.TimeElapsedTrigger')


def add_node_workflow_change_trigger(graph):
    graph.create_node('nodes.trigger.InboundWorkflowChange')

def save_to_database(graph):
    try:
        graph.validate_nodes()
        graph.save_graph_to_database()
        viewer = graph.viewer()
        viewer.message_dialog('Save Successful!', title='Workflow Saved')
    except ValueError as e:
        msg = "Changes could not be saved.\n\n"
        msg += str(e)
        msg += '\n\nCorrect these errors and try again.'
        viewer = graph.viewer()
        viewer.message_dialog(msg, title='Save Failed')
