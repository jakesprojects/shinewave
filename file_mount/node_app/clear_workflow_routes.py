from shinewave_webapp.database_connector import run_query 
api_data = run_query(
    "DELETE FROM workflow_routes",
    sql_parameters=[],
    commit=True
)