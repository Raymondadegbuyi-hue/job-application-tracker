-- Deletes the table if it already exists, then creates it fresh.
-- WARNING: running this again erases every saved application.
DROP TABLE IF EXISTS applications;

CREATE TABLE applications (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  company       TEXT NOT NULL,
  role          TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'Saved'
                CHECK (status IN ('Saved', 'Applied', 'Interviewing', 'Offer', 'Rejected', 'Withdrawn')),
  date_applied  TEXT,             -- YYYY-MM-DD; empty while status is 'Saved'
  location      TEXT,
  job_url       TEXT,
  salary_min    INTEGER,          -- whole dollars, e.g. 20
  salary_max    INTEGER,          -- whole dollars, e.g. 25
  salary_period TEXT CHECK (salary_period IN ('hour', 'year')),
  notes         TEXT,
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- The minimum can't be bigger than the maximum
  CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);
