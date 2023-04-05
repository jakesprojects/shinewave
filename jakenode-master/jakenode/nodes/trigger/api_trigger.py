import hashlib
import json
import random

from jakenode.database_connector import run_query
from jakenode.nodes.trigger.trigger_node import TriggerNode


class APITrigger(TriggerNode):
    """
    A node triggered by an API call.
    """

    # unique node identifier.
    __identifier__ = 'nodes.trigger'

    # initial default node name.
    NODE_NAME = 'API Trigger'

    def __init__(self):
        super(APITrigger, self).__init__(has_input=False)

    def fetch_api_data(self):
        api_data = run_query(
            """
                WITH filtered_workflow_nodes AS (
                    SELECT
                        wn.workflow_version,
                        wn.custom_data,
                        wn.workflow_id,
                        wn.node_type
                    FROM workflow_nodes wn
                    INNER JOIN workflows w ON
                        wn.workflow_id = w.id
                        AND wn.active = w.active
                    WHERE
                        wn.active = 'TRUE'
                        AND w.account_id = ?
                )
                    SELECT
                        custom_data,
                        1 AS workflow_version
                    FROM filtered_workflow_nodes
                    WHERE
                        node_type = ?
                UNION
                    SELECT
                        '{}' AS custom_data,
                        MAX(workflow_version) AS workflow_version
                    FROM filtered_workflow_nodes
                    WHERE workflow_id = ?
            """,
            sql_parameters=[self.account_id, self.get_property('type_'), self.workflow_id],
            return_data_format=dict
        )

        if not api_data:
            workflow_version = 1
            existing_api_endpoints = []
        else:
            workflow_versions = api_data.get('workflow_version') + [1]
            workflow_version = max(workflow_versions)
            custom_data = [json.loads(i) for i in api_data['custom_data']]
            existing_api_endpoints = [i['api_endpoint'] for i in custom_data if i.get('api_endpoint')]

        return {'workflow_version': workflow_version, 'existing_api_endpoints': existing_api_endpoints}

    def generate_api_endpoint(self):
        existing_api_data = self.fetch_api_data()

        random_key = random.randint(0, 9999)
        key_values = [
            self.account_id,
            self.workflow_id,
            existing_api_data['workflow_version'],
            self.get_property('id'),
            f'{random_key:04}'
        ]
        key_values = [str(i) for i in key_values]
        uncompressed_key = '-'.join(key_values)
        compressed_key = hashlib.md5(uncompressed_key.encode()).hexdigest()
        if compressed_key in existing_api_data['existing_api_endpoints']:
            return generate_api_endpoint()
        else:
            return compressed_key

    def load_templates(self):
        self.safe_set_property('api_endpoint', self.generate_api_endpoint())

    def get_display_info(self):
        """
            Broadcasts the info to be displayed in the display_window. Output should be a tuple composed of:
                1. The Node's Name
                2. An HTML block to display
        """

        node_name = self.get_node_name(html_safe=True)

        api_endpoint = self.get_property('api_endpoint')

        display_text = f"""
            <p>
                This node will trigger when the following api_endpoint is hit:
                <br>&nbsp;&nbsp;{{'api_endpoint': '{api_endpoint}'}}
            </p>
            <p style="background-color:red;"><b>Caution!</b> Deleting this node will delete the API endpoint.</p>
        """

        return node_name, display_text

    def validate_node(self):
        """
        """
        self.validate_has_downstream_outreach()
