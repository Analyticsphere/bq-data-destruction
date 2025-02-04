# BigQuery Data Destruction Cloud Function

## Overview
This Google Cloud Function (`run_bq_data_destruction`) allows authorized users to delete rows from a predefined BigQuery table based on a list of `Connect_IDs`. It enforces strict protocol validation to prevent accidental or unauthorized data deletion. Future extensions can include soft deletions (`mask_fields`) where certain fields are nullified instead of deleting rows.

## API Endpoint
- **URL:** `POST /run_bq_data_destruction`
- **Authentication:** Requires a Bearer token if IAM authentication is enabled.

## Request Format
### **Headers**
```http
Content-Type: application/json
Authorization: Bearer <TOKEN>
```

### **Body (JSON)**
```json
{
  "protocol": "roi_physical_activity",
  "connect_ids": ["123456789", "987654321"]
}
```

## Supported Protocols
Currently, the function supports the following protocol(s):

| Protocol Name          | Dataset | Table               | Operation |
|------------------------|---------|---------------------|------------|
| `roi_physical_activity` | ROI     | physical_activity  | Deletes rows |

## Response Codes & Examples

| HTTP Code | Meaning |
|-----------|------------------------------------------------|
| **200** OK | Successful deletion or no matching `Connect_IDs` found. |
| **400** Bad Request | Missing parameters, incorrect data types, or unsupported protocol. |
| **500** Internal Server Error | Unexpected processing error. |

### **Success - Rows Deleted**
```json
{
  "message": "Deleted 2 records from PROJECT_ID.ROI.physical_activity",
  "deleted_ids": ["123456789", "987654321"],
  "not_found": []
}
```

### **Success - No Matching Records**
```json
{
  "message": "No matching Connect_IDs found",
  "not_found": ["555555555"]
}
```

### **Failure - Invalid Protocol**
```json
{
  "error": "'random_protocol' is not a supported protocol. Allowed: ['roi_physical_activity']"
}
```

### **Failure - Internal Server Error**
```json
{
  "error": "Database connection failed"
}
```

## Deployment & CI/CD
This function is deployed as a **Google Cloud Function** and is integrated with **Cloud Build** for CI/CD.
- When a pull request is merged into `dev`, `stg`, or `main`, Cloud Build triggers a deployment.
- The function automatically infers the GCP project environment (`dev`, `stg`, or `prod`).

## Security Considerations
- The function only allows deletions for **predefined datasets and tables**.
- It does **not** accept arbitrary dataset/table names to prevent unintended data loss.


