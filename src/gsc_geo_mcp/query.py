# Runs sql/pages_losing_ai_referral_traffic.sql against BigQuery and
# returns the flagged pages. Shared by run_query.py and the MCP server
# so both run the exact same SQL. Authenticates the same way as
# seed_test_data.py: Application Default Credentials on this machine.

import os
import re
from pathlib import Path

from google.cloud import bigquery

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "pages_losing_ai_referral_traffic.sql"
DEFAULT_DATASET_ID = "gsc_geo_mcp_test"

# Project and dataset names only ever contain these characters. Checking
# stops a typo in .env from turning into broken or unintended SQL.
SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def load_settings():
    project_id = os.environ.get("BIGQUERY_PROJECT_ID")
    dataset_id = os.environ.get("BIGQUERY_DATASET_ID") or DEFAULT_DATASET_ID
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID is not set. Copy .env.example to .env and fill it in.")
    for name, value in (("BIGQUERY_PROJECT_ID", project_id), ("BIGQUERY_DATASET_ID", dataset_id)):
        if not SAFE_NAME.match(value):
            raise RuntimeError(f"{name} has unexpected characters: {value!r}")
    return project_id, dataset_id


def pages_losing_ai_referral_traffic():
    project_id, dataset_id = load_settings()
    sql = SQL_FILE.read_text()
    sql = sql.replace("YOUR_PROJECT_ID", project_id).replace("YOUR_DATASET_ID", dataset_id)
    client = bigquery.Client(project=project_id)
    rows = client.query(sql).result()
    return {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "pages": [dict(row) for row in rows],
    }
