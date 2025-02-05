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
"""

import json
import functions_framework
from google.cloud import bigquery
import logging

# Define allowed protocols with associated function names.
supported_protocols = {
    "roi_physical_activity": {
        "dataset": "ForTestingOnly",      # TODO: Change to "ROI" after testing
        "table": "roi_physical_activity", # TODO: Change to "physical_activity" after testing
        "function": "delete_row"  
    }
}

# Initialize BigQuery client
client = bigquery.Client()

def json_response(message, status=200):
    """Standardized JSON response format."""
    return json.dumps(message), status

@functions_framework.http
def run_bq_data_destruction(request):
    """Cloud Function to delete rows from a specified BigQuery table based on Connect_IDs."""
    
    try:
        # Validate request
        validation_result = validate_request(request)
        if isinstance(validation_result, tuple):
            protocol, connect_ids = validation_result  
        else:
            return validation_result  

        # Retrieve protocol config
        protocol_config = supported_protocols.get(protocol)
        if not protocol_config:
            logging.error(f"Unsupported protocol: {protocol}")
            return json_response({"error": f"Unsupported protocol: {protocol}"}, 400)

        function_name = protocol_config["function"]

        # Call the appropriate function based on protocol
        if function_name == "delete_row":
            return delete_row(protocol_config["dataset"], protocol_config["table"], connect_ids)
        else:
            logging.error(f"Function '{function_name}' not implemented.")
            return json_response({"error": f"Function '{function_name}' not implemented"}, 500)

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return json_response({"error": str(e)}, 500)

def validate_request(request):
    """Validates request payload for required parameters and correct types."""
    
    # Parse request JSON
    request_json = request.get_json(silent=True)
    if request_json is None:
        logging.error("Invalid JSON request received.")
        return json_response({"error": "Invalid JSON format"}, 400)

    protocol = request_json.get("protocol")
    connect_ids = request_json.get("connect_ids")

    # Validate protocol
    if not isinstance(protocol, str):
        logging.error(f"Invalid or missing protocol: {protocol}")
        return json_response({"error": "Missing or invalid parameter: protocol (str)"}, 400)
    if protocol not in supported_protocols:
        logging.error(f"Unsupported protocol: {protocol}")
        return json_response({"error": f"'{protocol}' is not a supported protocol. Allowed: {list(supported_protocols.keys())}"}, 400)

    # Validate connect_ids
    if not isinstance(connect_ids, list):  
        logging.error(f"Invalid connect_ids type: {type(connect_ids)} - Value: {connect_ids}")
        return json_response({"error": "connect_ids must be a list of strings"}, 400)

    # Convert all items to strings (ensuring correct data type for BigQuery)
    connect_ids = [str(id).strip() for id in connect_ids]

    logging.info(f"Validated request - Protocol: {protocol}, Connect_IDs: {connect_ids}")

    return protocol, connect_ids

def delete_row(dataset: str, table: str, connect_ids: list):
    """Deletes rows from the specified BigQuery dataset/table based on Connect_IDs."""
    
    connect_ids = [str(id).strip() for id in connect_ids]

    try:
        project = client.project

        # Query to find existing Connect_IDs
        check_query = f"""
        SELECT TRIM(Connect_ID) AS Connect_ID 
        FROM `{project}.{dataset}.{table}`
        WHERE TRIM(Connect_ID) IN UNNEST(@connect_ids)
        """
        check_job = client.query(check_query, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("connect_ids", "STRING", connect_ids)]
        ))

        existing_ids = {row["Connect_ID"] for row in check_job.result()}
        logging.info(f"Existing IDs found: {existing_ids}")

        # Determine IDs that were not found
        not_found_ids = list(set(connect_ids) - existing_ids)

        if not existing_ids:
            logging.info("No matching Connect_IDs found.")
            return json_response({"message": "No matching Connect_IDs found", "not_found": not_found_ids}, 200)

        # Proceed with delete operation
        delete_query = f"""
        DELETE FROM `{project}.{dataset}.{table}`
        WHERE TRIM(Connect_ID) IN UNNEST(@connect_ids)
        """
        delete_job = client.query(delete_query, job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("connect_ids", "STRING", list(existing_ids))]
        ))
        delete_job.result()

        return json_response({
            "message": f"Deleted {len(existing_ids)} records from {project}.{dataset}.{table}",
            "deleted_ids": list(existing_ids),
            "not_found": not_found_ids
        }, 200)

    except Exception as e:
        logging.error(f"Query failed: {str(e)}")
        return json_response({"error": f"Query execution failed: {str(e)}"}, 500)
