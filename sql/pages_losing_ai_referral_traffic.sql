-- Finds pages that may be losing AI-referral traffic.
-- Definition locked in sprint/LOG.md on 2026-09-22: impressions flat or
-- up, clicks down, trailing 7 days vs preceding 7 days, by page.
--
-- Column names (data_date, url, impressions, clicks) are confirmed
-- against Google's own bulk export schema reference for the
-- searchdata_url_impression table, not guessed from memory.
--
-- Window logic matches geo-visibility-tracker/weekly_diff.py's
-- window_bounds(): trailing is the 7 days ending today, preceding is
-- the 7 days directly before that, applied here by page instead of by
-- brand.
--
-- Before running: replace YOUR_PROJECT_ID with the BigQuery project you
-- pointed the export at, and YOUR_DATASET_ID with the dataset name
-- Search Console created for this property (BigQuery console -> that
-- project -> the dataset named after the verified property).

WITH trailing AS (
  SELECT
    url,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM `YOUR_PROJECT_ID.YOUR_DATASET_ID.searchdata_url_impression`
  WHERE data_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 6 DAY)
                       AND CURRENT_DATE()
  GROUP BY url
),

preceding AS (
  SELECT
    url,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM `YOUR_PROJECT_ID.YOUR_DATASET_ID.searchdata_url_impression`
  WHERE data_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 13 DAY)
                       AND DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  GROUP BY url
)

SELECT
  COALESCE(trailing.url, preceding.url) AS url,
  COALESCE(preceding.impressions, 0) AS preceding_impressions,
  COALESCE(trailing.impressions, 0) AS trailing_impressions,
  COALESCE(preceding.clicks, 0) AS preceding_clicks,
  COALESCE(trailing.clicks, 0) AS trailing_clicks,
  COALESCE(trailing.impressions, 0) - COALESCE(preceding.impressions, 0) AS impressions_change,
  COALESCE(trailing.clicks, 0) - COALESCE(preceding.clicks, 0) AS clicks_change
FROM trailing
FULL OUTER JOIN preceding USING (url)
WHERE COALESCE(trailing.impressions, 0) >= COALESCE(preceding.impressions, 0)
  AND COALESCE(trailing.clicks, 0) < COALESCE(preceding.clicks, 0)
ORDER BY clicks_change ASC;
