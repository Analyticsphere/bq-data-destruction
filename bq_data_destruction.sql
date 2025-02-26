/*
BigQuery Data Destruction Implemented as Scheduled Query

Objective:
  - Remove derived participant data from BigQuery tables when flagged for destruction.
  - Ensure that deletions only occur **after the DevOps team has destroyed the data in Firestore**.
  - This query is scheduled to run once daily.

Approach:
  - Maintain code in GitHub; DO NOT edit in directly in UI
  - Do not hardcode project to enable CI/CD for dev, stg, prod. BQ will use current project by default.
  - Extend easily by adding additional DDL statements as needed.
  - Cannot use CTEs with DELETE statments
  - Cannot CREATE temporary tables and DROP them within Scheduled Queries
*/

-----------------------------------------------------------------------------------------------
-- DDL 1: DELETE ROI Physical Actity Data for Participants that have Requested Data Destruction
-----------------------------------------------------------------------------------------------
DELETE FROM ROI.physical_activity
WHERE Connect_ID IN (
  SELECT CAST(Connect_ID AS STRING)
  FROM Connect.participants
  WHERE d_831041022 = 353358909  -- "Destroy Data" flag is "Yes"
    AND d_861639549 = 353358909  -- "Data Has Been Destroyed" flag is "Yes"; Ensures DevOps code has run first.
);
