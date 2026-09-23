# Runs the lost-AI-referral-traffic query once and prints the flagged
# pages. Reads BIGQUERY_PROJECT_ID and BIGQUERY_DATASET_ID from .env.
# The dataset defaults to the synthetic gsc_geo_mcp_test data.
#
# Run: uv run --env-file .env run_query.py

from gsc_geo_mcp.query import pages_losing_ai_referral_traffic


def main():
    result = pages_losing_ai_referral_traffic()
    print(f"Dataset: {result['project_id']}.{result['dataset_id']}")
    print(f"Pages flagged: {len(result['pages'])}")
    for page in result["pages"]:
        print(f"- {page['url']}")
        print(f"    clicks: {page['preceding_clicks']} -> {page['trailing_clicks']} ({page['clicks_change']:+d})")
        print(f"    impressions: {page['preceding_impressions']} -> {page['trailing_impressions']} ({page['impressions_change']:+d})")


if __name__ == "__main__":
    main()
