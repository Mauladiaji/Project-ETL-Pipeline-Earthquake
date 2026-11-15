-- 002: quarantine table, one row per record rejected by validate_record.
-- Rejected records are kept with the reasons, never silently dropped.

CREATE TABLE IF NOT EXISTS quarantine (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- surrogate key, set by the database

    source_feed TEXT        NOT NULL,   -- which feed the record came from
    ingested_at TIMESTAMPTZ NOT NULL,   -- when the run that rejected it fetched it (UTC)

    -- The record exactly as received. JSONB, not typed columns: a rejected record may be
    -- missing fields or hold values of the wrong type, so it cannot fit the earthquakes columns.
    record      JSONB       NOT NULL,

    -- validate_record returns a LIST of reasons; a text array keeps them separate and queryable.
    reasons     TEXT[]      NOT NULL CHECK (cardinality(reasons) > 0),   -- a rejection always has a reason

    -- When the row was written here. Unlike ingested_at (set by the pipeline run), this one
    -- is the database's own clock, so a default is appropriate.
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
