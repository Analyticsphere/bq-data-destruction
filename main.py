"""
Cloud Function: run_bq_data_destruction

Description:
This Google Cloud Function deletes rows from a predefined BigQuery table based on a list of `Connect_IDs`. 
It supports a limited set of protocols to prevent unauthorized data deletions.

Usage:
- Endpoint: **POST /run_bq_data_destruction**
- Required JSON body:
    {
      "protocol": "roi_physical_activity",
      "connect_ids": ["123456789", "987654321"]
    }

For full API documentation, response codes, and examples, see the README.md file.
"""



import json
import functions_framework
from google.cloud import bigquery

# Define allowed protocols with associated function names. 
# Note: I use this supported_protocols object so that I can extend it to include future use cases such as "mask_fields" 
#       where the data destruction protocol requires specified fields to be set to NULL for each participant rather than deleting the whole row.
supported_protocols = {
    "roi_physical_activity": {
        "dataset": "ForTestingOnly",
        "table": "physical_activity",
        "function": "delete_row"  # Specifies the function to call
    }
}


# Initialize BigQuery client
client = bigquery.Client()

@functions_framework.http
def run_bq_data_destruction(request):
    """Cloud Function to delete rows from a specified BigQuery table based on Connect_IDs."""
    
    try:
        # Parse request JSON
        request_json = request.get_json(silent=True)
        protocol = request_json.get("protocol")
        connect_ids = request_json.get("connect_ids")

        # Validate inputs
        if not protocol or not isinstance(protocol, str):
            return json.dumps({"error": "Missing or invalid parameter: protocol (str)"}), 400
        if protocol not in supported_protocols:
            return json.dumps({"error": f"'{protocol}' is not a supported protocol. Allowed: {list(supported_protocols.keys())}"}), 400
        if not connect_ids or not isinstance(connect_ids, list):
            return json.dumps({"error": "connect_ids must be a non-empty list"}), 400

        # Retrieve protocol config
        protocol_config = supported_protocols[protocol]
        function_name = protocol_config["function"]

        # Check which function to call explicitly instead of using globals()
        if function_name == "delete_row":
            return delete_row(protocol_config["dataset"], protocol_config["table"], connect_ids)
        else:
            return json.dumps({"error": f"Function '{function_name}' not implemented"}), 500

    except Exception as e:
        return json.dumps({"error": str(e)}), 500


def delete_row(dataset: str, table: str, connect_ids: list):
    """Deletes rows from the specified BigQuery dataset/table based on Connect_IDs."""

    try:
        project = client.project

        # Query to find existing Connect_IDs
        check_query = f"""
        SELECT Connect_ID FROM `{project}.{dataset}.{table}`
        WHERE Connect_ID IN UNNEST(@connect_ids)
        """
        check_job = client.query(check_query, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("connect_ids", "STRING", connect_ids)]
        ))
        existing_ids = {row["Connect_ID"] for row in check_job.result()}

        # Determine IDs that were not found
        not_found_ids = list(set(connect_ids) - existing_ids)

        if not existing_ids:
            return json.dumps({"message": "No matching Connect_IDs found", "not_found": not_found_ids}), 200

        # Delete records using a parameterized query (more secure)
        delete_query = f"""
        DELETE FROM `{project}.{dataset}.{table}`
        WHERE Connect_ID IN UNNEST(@connect_ids)
        """
        delete_job = client.query(delete_query, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("connect_ids", "STRING", list(existing_ids))]
        ))
        delete_job.result()  # Wait for query to complete

        return json.dumps({
            "message": f"Deleted {len(existing_ids)} records from {project}.{dataset}.{table}",
            "deleted_ids": list(existing_ids),
            "not_found": not_found_ids
        }), 200

    except Exception as e:
        return json.dumps({"error": str(e)}), 500
