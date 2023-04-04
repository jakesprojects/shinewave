#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os

from NodeGraphQt import NodesPaletteWidget, NodesTreeWidget, PropertiesBinWidget
from Qt import QtCore, QtWidgets

from jakenode.graph_handler import GraphHandler

ACCOUNT_ID = 1
WORKFLOW_CATEGORY_ID = 1
WORKFLOW_ID = 17
WORKFLOW_DATA_FOLDER = './data/workflows'


def run_node_app(
    queue=None,
    socketio=None,
    account_id=ACCOUNT_ID,
    workflow_category_id=WORKFLOW_CATEGORY_ID,
    workflow_id=WORKFLOW_ID,
    workflow_data_folder=WORKFLOW_DATA_FOLDER
):
    init_time = datetime.now()
    print(init_time)

    # handle SIGINT to make the app terminate on CTRL+C
#     signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication([])

    # create graph controller.
    graph = GraphHandler(queue=queue, socketio=socketio)

    # registered nodes.

    # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(900, 600)
    graph_widget.show()

    graph.set_account_properties(
        account_id=account_id, workflow_category_id=workflow_category_id, workflow_id=workflow_id
    )

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

    # create a node palette widget.
    nodes_palette = NodesPaletteWidget(node_graph=graph)
    nodes_palette.set_category_label('nodeGraphQt.nodes', 'Builtin Nodes')
    nodes_palette.set_category_label('nodes.custom.ports', 'Custom Port Nodes')
    nodes_palette.set_category_label('nodes.widget', 'Widget Nodes')
    nodes_palette.set_category_label('nodes.basic', 'Basic Nodes')
    nodes_palette.set_category_label('nodes.group', 'Group Nodes')

    # Maximize Windows (There's probably a much better way to do this)
    [i.setWindowState(QtCore.Qt.WindowMaximized) for i in app.allWindows()]

    graph.load_graph_from_database()
    nodes = graph.all_nodes()
    graph.auto_layout_nodes(nodes=nodes, down_stream=False)
    graph.fit_to_selection()

    # workflow_file_path = f'{workflow_data_folder}/{workflow_id}.json'

    # if os.path.isfile(workflow_file_path):
    #     with open(workflow_file_path, 'r+') as file:
    #         print(f'~~~~LOADING FILE: {workflow_file_path}')
    #         definition_json = file.read()
    #         definition_dict = json.loads(definition_json)

    #         file.seek(0)
    #         file.write(graph.get_blank_json())
    #         file.truncate()
    #         graph.load_session(workflow_file_path)

    #         if definition_dict.get('nodes', {}):
    #             graph.load_graph_from_dict(definition_dict)

    #         graph.auto_layout_nodes()
    #         graph.save_session(workflow_file_path)
    # else:
    #     graph.save_session(workflow_file_path)
    #     graph.load_session(workflow_file_path)

    app.exec_()
