import sqlite3

def fetch_node_display_info(node):
    return node.get_display_info()

def fetch_node_text_color(node_type):
	default_color = '#FFFFFF' # White
	node_color_dict = {'nodes.trigger.TimeElapsedTrigger': '#000000'}
	return node_color_dict.get(node_type, default_color)
	