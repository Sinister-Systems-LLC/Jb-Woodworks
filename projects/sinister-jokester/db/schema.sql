-- Sinister Jokester — intake DB schema
-- Author: RKOJ-ELENO :: 2026-05-26
-- Composes with vault/SCHEMA.md (human-readable doc of the same shape).

CREATE TABLE IF NOT EXISTS intake_items (
    id                   TEXT PRIMARY KEY,
    source_url           TEXT NOT NULL UNIQUE,
    source_type          TEXT NOT NULL CHECK (source_type IN ('github','ig_audio','direct_input','telegram','local_path')),
    intake_ts            TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','analyzing','decided')),
    verdict              TEXT CHECK (verdict IN ('ADOPT','WATCH','REJECT')),
    decision_md_path     TEXT,
    fleet_overlap_score  REAL DEFAULT 0.0,
    fleet_overlap_assets TEXT DEFAULT '[]',
    tags                 TEXT DEFAULT '',
    title                TEXT,
    short_summary        TEXT,
    raw_metadata_json    TEXT DEFAULT '{}',
    reviewed_by          TEXT,
    decided_ts           TEXT
);

CREATE INDEX IF NOT EXISTS idx_intake_items_verdict ON intake_items(verdict);
CREATE INDEX IF NOT EXISTS idx_intake_items_type    ON intake_items(source_type);
CREATE INDEX IF NOT EXISTS idx_intake_items_status  ON intake_items(status);
CREATE INDEX IF NOT EXISTS idx_intake_items_intake  ON intake_items(intake_ts);

CREATE TABLE IF NOT EXISTS intake_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    ts_utc  TEXT NOT NULL,
    event   TEXT NOT NULL,
    detail  TEXT,
    FOREIGN KEY (item_id) REFERENCES intake_items(id)
);

CREATE INDEX IF NOT EXISTS idx_intake_log_item ON intake_log(item_id);
CREATE INDEX IF NOT EXISTS idx_intake_log_ts   ON intake_log(ts_utc);
