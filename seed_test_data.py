# Loads synthetic rows into gsc_geo_mcp_test.searchdata_url_impression,
# shaped like the real bulk export table, so the trailing-vs-preceding
# query in sql/pages_losing_ai_referral_traffic.sql can be tested without
# waiting on real GSC traffic. Never touches the real searchconsole
# dataset. Safe to re-run: rebuilds the table from scratch each time.
#
# Run: uv run seed_test_data.py

from datetime import date, timedelta

from google.cloud import bigquery

PROJECT_ID = "sujandeswal-gsc"
DATASET_ID = "gsc_geo_mcp_test"
TABLE_ID = "searchdata_url_impression"

# Anchor date stands in for "today" (MAX(data_date) in the query).
# Trailing window: ANCHOR - 6 .. ANCHOR. Preceding: ANCHOR - 13 .. ANCHOR - 7.
# Matches the same window math as sql/pages_losing_ai_referral_traffic.sql.
ANCHOR = date(2026, 9, 22)
TRAILING_START = ANCHOR - timedelta(days=6)
PRECEDING_START = ANCHOR - timedelta(days=13)
PRECEDING_END = ANCHOR - timedelta(days=7)


def daily_rows(url, start, end, impressions_per_day, clicks_per_day):
    rows = []
    day = start
    while day <= end:
        rows.append({
            "data_date": day.isoformat(),
            "url": url,
            "impressions": impressions_per_day,
            "clicks": clicks_per_day,
        })
        day += timedelta(days=1)
    return rows


def build_rows():
    rows = []

    # Case A: should get flagged. Impressions up, clicks down.
    url_a = "https://example.com/page-a-should-flag"
    rows += daily_rows(url_a, PRECEDING_START, PRECEDING_END, impressions_per_day=100, clicks_per_day=10)
    rows += daily_rows(url_a, TRAILING_START, ANCHOR, impressions_per_day=110, clicks_per_day=4)

    # Case B: should not get flagged. Both windows roughly stable.
    url_b = "https://example.com/page-b-stable"
    rows += daily_rows(url_b, PRECEDING_START, PRECEDING_END, impressions_per_day=80, clicks_per_day=12)
    rows += daily_rows(url_b, TRAILING_START, ANCHOR, impressions_per_day=80, clicks_per_day=12)

    # Case C: should not get flagged. No rows at all in the preceding
    # window. Tests that a brand-new page with nothing to compare
    # against isn't treated as a click drop from zero.
    url_c = "https://example.com/page-c-new-no-history"
    rows += daily_rows(url_c, TRAILING_START, ANCHOR, impressions_per_day=50, clicks_per_day=5)

    return rows


def main():
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    schema = [
        bigquery.SchemaField("data_date", "DATE"),
        bigquery.SchemaField("url", "STRING"),
        bigquery.SchemaField("impressions", "INTEGER"),
        bigquery.SchemaField("clicks", "INTEGER"),
    ]
    job_config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE")

    rows = build_rows()
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()

    print(f"Loaded {len(rows)} rows into {table_ref}")


if __name__ == "__main__":
    main()
