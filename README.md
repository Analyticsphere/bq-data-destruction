# BigQuery Data Destruction Cloud Function

## Overview
This Google Cloud Function deletes rows from a specified BigQuery table based on a list of `Connect_IDs`. The function dynamically infers the GCP project it is running in, making it suitable for **dev, stg, and prod** environments.

## Use Case
The initial use case is to allow DevOps to trigger data destruction for the `ROI.physical_activity` table when a participant requests data destruction. The code simply deletes all rows from the table associated with the `Connect_ID` as no data must be retained for this use case.

This function can be modified to incorporate future use cases, but a separate REST API call must be made with the appropriate `dataset` and `table`. This will allow for more complex workflows for future use cases if required.

---

## **Usage**
To invoke the function, send a **POST** request with the required parameters.

### **Base Endpoint**
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export FUNCTION_URL="https://$REGION-$PROJECT_ID.cloudfunctions.net/run_bq_data_destruction"
```

### Consider the following example table for `ROI.physical_activity`

| Connect_ID   | d_449038410 | d_205380968 | d_416831581           |
|-------------|-------------|-------------|------------------------|
| 4806091014  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 8576196328  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 4800072280  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 3860352953  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 9824541704  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 9177068756  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 4335003653  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 3344744505  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 6019020541  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |
| 6759772253  | 104593854   | 104430631   | 2025-01-27T20:24:58.961Z |


### **Example Request**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "protocol": "roi_physical_activity",
  "connect_ids": ["4806091014", "8576196328", "4800072280"]
}'
```

### **Example Response**
```json
{
  "message": "Deleted records for 3 participants from nih-nci-dceg-connect-dev.ForTestingOnly.roi_physical_activity",
  "deleted_ids": ["4800072280", "4806091014", "8576196328"],
  "not_found": []
}
```

---

## **Test Cases**

### **1. Deleting Existing Connect_IDs**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity", "connect_ids": ["4806091014", "8576196328", "4800072280"]}'
```

Expected Response:
```json
{
  "message": "Deleted records for 3 participants from nih-nci-dceg-connect-dev.ForTestingOnly.roi_physical_activity",
  "deleted_ids": ["4800072280", "4806091014", "8576196328"],
  "not_found": []
}
```

---

### **2. Some IDs Exist, Some Do Not**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity", "connect_ids": ["3344744505", "3860352953", "0000000000"]}'
```

Expected Response:
```json
{
  "message": "Deleted records for 2 participants from nih-nci-dceg-connect-dev.ForTestingOnly.roi_physical_activity",
  "deleted_ids": ["3344744505", "3860352953"],
  "not_found": ["0000000000"]
}
```

---

### **3. No Matching IDs in the Table**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity", "connect_ids": ["0000000000", "1111111111", "2222222222"]}'
```

Expected Response:
```json
{
  "message": "No matching Connect_IDs found",
  "not_found": ["0000000000", "2222222222", "1111111111"]
}
```

---

### **4. Empty `connect_ids` List (Health Check)**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity", "connect_ids": []}'
```

Expected Response:
```json
{
  "message": "No matching Connect_IDs found",
  "not_found": []
}
```

---

### **5. Invalid Protocol**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "invalid_protocol", "connect_ids": ["4806091014", "8576196328", "4800072280"]}'
```

Expected Response:
```json
{
  "error": "'invalid_protocol' is not a supported protocol. Allowed: ['roi_physical_activity']"
}
```

---

### **6. Missing `connect_ids` Field**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity"}'
```

Expected Response:
```json
{
  "error": "connect_ids must be a list of strings"
}
```

---

### **7. Invalid `connect_ids` Type (Not a List)**
```bash
curl -X POST "$FUNCTION_URL" \
-H "Authorization: Bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{"protocol": "roi_physical_activity", "connect_ids": "4806091014"}'
```

Expected Response:
```json
{
  "error": "connect_ids must be a list of strings"
}
```

---

## **CI/CD and Deployment**
This REST API is deployed as a Cloud Function via Cloud Run, and the deployment is configured within `cloudbuild.yaml` along with a Cloud Build trigger in each environment, which handles environment variables. The Cloud Build is triggered when a PR is merged with the `dev`, `stg`, or `main` branch.
