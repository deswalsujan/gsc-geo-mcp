-- Finds pages that may be losing AI-referral traffic.
-- Definition locked in sprint/LOG.md on 2026-09-22: impressions flat or
-- up, clicks down, trailing 7 days vs preceding 7 days, by page.
--
-- Column names (data_date, url, impressions, clicks) are confirmed
-- against Google's own bulk export schema reference for the
-- searchdata_url_impression table, not guessed from memory.
--
-- Window logic matches geo-visibility-tracker/weekly_diff.py's
-- window_bounds(): trailing is the 7 days ending on the anchor date,
-- preceding is the 7 days directly before that, applied here by page
-- instead of by brand.
--
-- The anchor is MAX(data_date) from the table itself, not today's
-- date. Two reasons: data_date is stamped in Pacific Time per Google's
-- own docs, while a literal "today" in BigQuery defaults to UTC, so
-- they don't line up; and bulk exports typically lag 2-3 days behind
-- the real date, so today and yesterday will usually have zero rows
-- whenever this actually runs.
--
-- Before running: replace YOUR_PROJECT_ID with the BigQuery project you
-- pointed the export at, and YOUR_DATASET_ID with the dataset name
-- Search Console created for this property (BigQuery console -> that
-- project -> the dataset named after the verified property).

WITH latest AS (
  SELECT MAX(data_date) AS latest_date
  FROM `YOUR_PROJECT_ID.YOUR_DATASET_ID.searchdata_url_impression`
),

trailing AS (
  SELECT
    url,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM `YOUR_PROJECT_ID.YOUR_DATASET_ID.searchdata_url_impression`
  CROSS JOIN latest
  WHERE data_date BETWEEN DATE_SUB(latest_date, INTERVAL 6 DAY)
                       AND latest_date
  GROUP BY url
),

preceding AS (
  SELECT
    url,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM `YOUR_PROJECT_ID.YOUR_DATASET_ID.searchdata_url_impression`
  CROSS JOIN latest
  WHERE data_date BETWEEN DATE_SUB(latest_date, INTERVAL 13 DAY)
                       AND DATE_SUB(latest_date, INTERVAL 7 DAY)
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
