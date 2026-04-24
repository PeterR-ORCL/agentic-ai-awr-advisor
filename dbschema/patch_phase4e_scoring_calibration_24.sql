-- Phase 4E scoring calibration patch for the 24-case mixed AWR validation pack.
-- Scope:
--   1. Remove SMART_SCAN_FLAG from pressure scoring for AWR_WEIGHTED_CORE.
--   2. Add conservative MEMORY scoring rows if missing.
--   3. Document required ADG normalization follow-up when ranges are controlled
--      only in loader defaults rather than SQL seed rows.
--
-- Constraints:
--   - Idempotent
--   - Does not touch Phase 4G
--   - Does not modify READ_LATENCY_MS
--   - Does not modify LOG_FILE_SYNC_MS


-- ============================================================================
-- 1. Remove SMART_SCAN_FLAG from pressure scoring for AWR_WEIGHTED_CORE
-- ----------------------------------------------------------------------------
-- SMART_SCAN_FLAG is currently contributing EXADATA pressure points in the
-- deterministic score model. For the 24-case pack it behaves as platform noise
-- rather than actionable pressure, so remove only that seeded row.
-- ============================================================================

spool patch_phase4e_scoring_calibration_24.log

DELETE FROM AWR_SCORING_WEIGHT
WHERE SCORING_MODEL_ID IN (
    SELECT m.SCORING_MODEL_ID
    FROM AWR_SCORING_MODEL m
    WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
      AND m.MODEL_VERSION = '1.0.0'
)
  AND FEATURE_CODE = 'SMART_SCAN_FLAG';


-- ============================================================================
-- 2. Add conservative MEMORY scoring rows if missing
-- ----------------------------------------------------------------------------
-- These features are already produced by the loader, but the seeded
-- deterministic model does not currently assign them MEMORY-domain weights.
-- The weights below are intentionally conservative to restore coverage without
-- making MEMORY dominant by default.
-- ============================================================================

INSERT INTO AWR_SCORING_WEIGHT (
    SCORING_MODEL_ID,
    FEATURE_CODE,
    FEATURE_NAME,
    FEATURE_DOMAIN,
    FEATURE_PATH,
    WEIGHT_VALUE,
    NORMALIZATION_METHOD,
    TRANSFORM_METHOD,
    POLARITY,
    NOTES
)
SELECT
    m.SCORING_MODEL_ID,
    'PGA_SPILL_PRESSURE',
    'PGA Spill Pressure',
    'MEMORY',
    '$.PGA_SPILL_PRESSURE',
    0.08,
    'MINMAX',
    'NONE',
    'HIGH_BAD',
    'Conservative MEMORY pressure weight for PGA spill pressure'
FROM AWR_SCORING_MODEL m
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND NOT EXISTS (
      SELECT 1
      FROM AWR_SCORING_WEIGHT w
      WHERE w.SCORING_MODEL_ID = m.SCORING_MODEL_ID
        AND w.FEATURE_CODE = 'PGA_SPILL_PRESSURE'
  );

INSERT INTO AWR_SCORING_WEIGHT (
    SCORING_MODEL_ID,
    FEATURE_CODE,
    FEATURE_NAME,
    FEATURE_DOMAIN,
    FEATURE_PATH,
    WEIGHT_VALUE,
    NORMALIZATION_METHOD,
    TRANSFORM_METHOD,
    POLARITY,
    NOTES
)
SELECT
    m.SCORING_MODEL_ID,
    'TEMP_SPILL_PCT',
    'Temp Spill Percentage',
    'MEMORY',
    '$.TEMP_SPILL_PCT',
    0.05,
    'MINMAX',
    'NONE',
    'HIGH_BAD',
    'Conservative MEMORY pressure weight for temp spill percentage'
FROM AWR_SCORING_MODEL m
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND NOT EXISTS (
      SELECT 1
      FROM AWR_SCORING_WEIGHT w
      WHERE w.SCORING_MODEL_ID = m.SCORING_MODEL_ID
        AND w.FEATURE_CODE = 'TEMP_SPILL_PCT'
  );

INSERT INTO AWR_SCORING_WEIGHT (
    SCORING_MODEL_ID,
    FEATURE_CODE,
    FEATURE_NAME,
    FEATURE_DOMAIN,
    FEATURE_PATH,
    WEIGHT_VALUE,
    NORMALIZATION_METHOD,
    TRANSFORM_METHOD,
    POLARITY,
    NOTES
)
SELECT
    m.SCORING_MODEL_ID,
    'SORTS_DISK_PCT',
    'Disk Sort Percentage',
    'MEMORY',
    '$.SORTS_DISK_PCT',
    0.04,
    'MINMAX',
    'NONE',
    'HIGH_BAD',
    'Conservative MEMORY pressure weight for disk sort percentage'
FROM AWR_SCORING_MODEL m
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND NOT EXISTS (
      SELECT 1
      FROM AWR_SCORING_WEIGHT w
      WHERE w.SCORING_MODEL_ID = m.SCORING_MODEL_ID
        AND w.FEATURE_CODE = 'SORTS_DISK_PCT'
  );

INSERT INTO AWR_SCORING_WEIGHT (
    SCORING_MODEL_ID,
    FEATURE_CODE,
    FEATURE_NAME,
    FEATURE_DOMAIN,
    FEATURE_PATH,
    WEIGHT_VALUE,
    NORMALIZATION_METHOD,
    TRANSFORM_METHOD,
    POLARITY,
    NOTES
)
SELECT
    m.SCORING_MODEL_ID,
    'WORKAREA_MULTIPASS_PCT',
    'Workarea Multipass Percentage',
    'MEMORY',
    '$.WORKAREA_MULTIPASS_PCT',
    0.07,
    'MINMAX',
    'NONE',
    'HIGH_BAD',
    'Conservative MEMORY pressure weight for multipass workarea pressure'
FROM AWR_SCORING_MODEL m
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND NOT EXISTS (
      SELECT 1
      FROM AWR_SCORING_WEIGHT w
      WHERE w.SCORING_MODEL_ID = m.SCORING_MODEL_ID
        AND w.FEATURE_CODE = 'WORKAREA_MULTIPASS_PCT'
  );

INSERT INTO AWR_SCORING_WEIGHT (
    SCORING_MODEL_ID,
    FEATURE_CODE,
    FEATURE_NAME,
    FEATURE_DOMAIN,
    FEATURE_PATH,
    WEIGHT_VALUE,
    NORMALIZATION_METHOD,
    TRANSFORM_METHOD,
    POLARITY,
    NOTES
)
SELECT
    m.SCORING_MODEL_ID,
    'HARD_PARSES_PER_SEC',
    'Hard Parses Per Second',
    'MEMORY',
    '$.HARD_PARSES_PER_SEC',
    0.03,
    'MINMAX',
    'NONE',
    'HIGH_BAD',
    'Conservative MEMORY pressure weight for parse churn'
FROM AWR_SCORING_MODEL m
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND NOT EXISTS (
      SELECT 1
      FROM AWR_SCORING_WEIGHT w
      WHERE w.SCORING_MODEL_ID = m.SCORING_MODEL_ID
        AND w.FEATURE_CODE = 'HARD_PARSES_PER_SEC'
  );


-- ============================================================================
-- 3. ADG normalization follow-up note
-- ----------------------------------------------------------------------------
-- TRANSPORT_LAG_SEC and APPLY_LAG_SEC seeded scoring rows already exist, but
-- their effective normalization ranges are controlled in
-- src/ingest/awr_adb_loader.py via SCORING_NORMALIZATION_DEFAULTS:
--   TRANSPORT_LAG_SEC max = 3600
--   APPLY_LAG_SEC max = 3600
--
-- Those ranges are not represented in the SQL seed rows themselves, so this
-- patch intentionally does not modify Python. Manual follow-up required:
--   - TRANSPORT_LAG_SEC max should be updated to 600
--   - APPLY_LAG_SEC max should be updated to 1200
--
-- That loader-default follow-up is required if you want hundreds of seconds of
-- DG lag to produce meaningful DG/ADG points in 4E scoring.
-- ============================================================================


-- ============================================================================
-- Verification query
-- ----------------------------------------------------------------------------
-- Show the current AWR_WEIGHTED_CORE rows relevant to this calibration patch.
-- ============================================================================
SELECT
    m.MODEL_CODE,
    m.MODEL_VERSION,
    w.FEATURE_CODE,
    w.FEATURE_DOMAIN,
    w.WEIGHT_VALUE,
    w.NORMALIZATION_METHOD,
    w.TRANSFORM_METHOD,
    w.POLARITY,
    w.NOTES
FROM AWR_SCORING_WEIGHT w
JOIN AWR_SCORING_MODEL m
  ON m.SCORING_MODEL_ID = w.SCORING_MODEL_ID
WHERE m.MODEL_CODE = 'AWR_WEIGHTED_CORE'
  AND m.MODEL_VERSION = '1.0.0'
  AND w.FEATURE_CODE IN (
      'SMART_SCAN_FLAG',
      'PGA_SPILL_PRESSURE',
      'TEMP_SPILL_PCT',
      'SORTS_DISK_PCT',
      'WORKAREA_MULTIPASS_PCT',
      'HARD_PARSES_PER_SEC',
      'TRANSPORT_LAG_SEC',
      'APPLY_LAG_SEC'
  )
ORDER BY w.FEATURE_CODE;

spool off
