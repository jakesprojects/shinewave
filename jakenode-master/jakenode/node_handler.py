from jakenode.nodes.outreach.email_outreach import EmailOutreach
from jakenode.nodes.outreach.sms_outreach import SMSOutreach
from jakenode.nodes.outreach.workflow_change import OutboundWorkflowChange
from jakenode.nodes.trigger.api_trigger import APITrigger
from jakenode.nodes.trigger.at_time_trigger import AtTimeTrigger
from jakenode.nodes.trigger.time_elapsed_trigger import TimeElapsedTrigger
from jakenode.nodes.trigger.workflow_change import InboundWorkflowChange


def fetch_all_node_types():
    return [
        APITrigger,
        AtTimeTrigger,
        TimeElapsedTrigger,
        EmailOutreach,
        SMSOutreach,
        OutboundWorkflowChange,
        InboundWorkflowChange
    ]


def fetch_node_display_info(node):
    return node.get_display_info()


def fetch_node_text_color(node_type):
    default_color = '#FFFFFF'  # White
    node_color_dict = {
        'nodes.trigger.TimeElapsedTrigger': '#000000',
        'nodes.trigger.AtTimeTrigger': '#000000',
        'nodes.trigger.InboundWorkflowChange': '#000000'
    }
    return node_color_dict.get(node_type, default_color)
