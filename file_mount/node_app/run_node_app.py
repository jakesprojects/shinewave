#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from imp import reload
import os
import signal
from time import sleep

from NodeGraphQt import NodesPaletteWidget, NodesTreeWidget, PropertiesBinWidget
from Qt import QtCore, QtWidgets

from jakenode.graph_handler import GraphHandler
from jakenode.nodes.pre_built import basic_nodes, custom_ports_node, group_node, widget_nodes
from jakenode.nodes.trigger.api_trigger import APITrigger
from jakenode.nodes.trigger.time_elapsed_trigger import TimeElapsedTrigger
from jakenode.nodes.outreach.sms_outreach import SMSOutreach

ACCOUNT_ID = 1
WORKFLOW_CATEGORY_ID = 1

def run_node_app(queue=None, socketio=None, account_id=ACCOUNT_ID, workflow_category_id=WORKFLOW_CATEGORY_ID):
    init_time = datetime.now()
    print(init_time)
    print(datetime.now() - init_time)

    # handle SIGINT to make the app terminate on CTRL+C
#     signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])

    # create graph controller.
    graph = GraphHandler(queue=queue, socketio=socketio)

    # set up context menu for the node graph.
    graph.set_context_menu_from_file('./config/master_config.json')

    # registered nodes.
    graph.register_nodes([
        APITrigger,
        TimeElapsedTrigger,
        SMSOutreach
    ])

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(900, 600)
    graph_widget.show()
    
    graph.set_account_properties(account_id=account_id, workflow_category_id=workflow_category_id)

    # Create Trigger Node
    api_trigger = graph.create_node(
        'nodes.trigger.APITrigger', text_color='#feab20'
    )


    sms_outreach = graph.create_node(
        'nodes.outreach.SMSOutreach', text_color='#feab20'
    )
    
    time_elapsed_trigger = graph.create_node(
        'nodes.trigger.TimeElapsedTrigger', text_color='#feab20'
    )
    # make node connections.

    sms_outreach.set_input(0, api_trigger.output(0))


    # auto layout nodes.
    graph.auto_layout_nodes()


    # fit nodes to the viewer.
    graph.clear_selection()
    graph.fit_to_selection()
    graph.viewer().showMaximized()

    # Custom builtin widgets from NodeGraphQt
    # ---------------------------------------

    # create a node properties bin widget.
    properties_bin = PropertiesBinWidget(node_graph=graph)
    properties_bin.setWindowFlags(QtCore.Qt.Tool)

#     # example show the node properties bin widget when a node is double clicked.
#     def display_properties_bin(node):
#         if not properties_bin.isVisible():
#             properties_bin.show()

#     # wire function to "node_double_clicked" signal.
#     graph.node_double_clicked.connect(display_properties_bin)

    # create a nodes tree widget.
    nodes_tree = NodesTreeWidget(node_graph=graph)
    nodes_tree.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_tree.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_tree.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_tree.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_tree.set_category_label('nodes.group', 'Group Nodes')
    # nodes_tree.show()

    # create a node palette widget.
    nodes_palette = NodesPaletteWidget(node_graph=graph)
    nodes_palette.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_palette.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_palette.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_palette.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_palette.set_category_label('nodes.group', 'Group Nodes')
    # nodes_palette.show()
    
    # Maximize Windows (There's probably a much better way to do this)
    [i.setWindowState(QtCore.Qt.WindowMaximized) for i in app.allWindows()]

    app.exec_()
    
if __name__ == '__main__':
    run_node_app()