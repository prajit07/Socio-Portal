-- ============================================================
-- SOCIETAL INNOVATION PORTAL — full schema snapshot (PostgreSQL 14+)
-- File: backend/schema.sql
--
-- Source of truth: backend/app/models/*.py (SQLAlchemy). This file is a
-- POINT-IN-TIME snapshot for manual rebuilds — if models change, update
-- this file (or regenerate) before reusing it.
--
-- Usage:
--   psql "$DATABASE_URL" -f backend/schema.sql
--   # or paste into the Neon SQL Editor (single statement batch works;
--   # the script is one transaction).
--
-- After running on a DB that Alembic manages, stamp the version table so
-- future `alembic upgrade head` runs don't try to rebuild everything:
--   alembic stamp head
--
-- Notes:
--  * IDs are app-generated (Python secrets); only the three log tables
--    (problem_tags, routing_logs, notifications) use SERIAL keys.
--  * created_at-style defaults are in the DB (DEFAULT now()); updated_at
--    auto-refresh and Python-side default= values live in the app —
--    inserts must come through the API/app, which generates them.
--  * Relationship cascades (delete-orphan) are ORM-level, not DB ON DELETE.
--  * Extra indexes on problems(status, created_at, ai_category,
--    submitter_id) are intentional (analytics performance); the models
--    don't declare them.
--  * Table order matters for FK validation on a fresh DB: teams (§5) is
--    created BEFORE solutions (§3 references teams.id).
-- ============================================================
BEGIN;

-- ---------- 0. Extensions ----------
CREATE EXTENSION IF NOT EXISTS "vector";   -- pgvector, for problems.embedding
-- (Neon ships pgvector. Self-hosted PG needs: apt install postgresql-XX-pgvector)

-- ---------- 1. Enum types (guarded; CREATE TYPE has no IF NOT EXISTS) ----------
DO $$ BEGIN CREATE TYPE role_enum AS ENUM (
  'citizen','university_admin','student','faculty','industry','government','admin'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE problem_status_enum AS ENUM (
  'pending_validation','validated','rejected','duplicate','open','in_review',
  'proposal_submitted','in_collaboration','prototype','pilot','implemented','closed'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE priority_enum AS ENUM (
  'low','medium','high','critical'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE evidence_type_enum AS ENUM (
  'image','video','audio','document','text'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE solution_status_enum AS ENUM (
  'draft','submitted','under_review','accepted','rejected'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE routing_type_enum AS ENUM ('university','industry');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE notification_type_enum AS ENUM (
  'problem_routed','proposal_received','status_updated','duplicate_flagged','generic'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- 2. Independent tables ----------
CREATE TABLE IF NOT EXISTS users (
  id            VARCHAR(20)  PRIMARY KEY,
  name          VARCHAR(120) NOT NULL,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role          role_enum    NOT NULL,
  phone         VARCHAR(32),
  domain_tags   JSON,
  is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS otp (
  id         VARCHAR(20)   PRIMARY KEY,
  identifier VARCHAR(255)  NOT NULL,
  purpose    VARCHAR(20)   NOT NULL,
  code_hash  VARCHAR(255)  NOT NULL,
  expires_at TIMESTAMPTZ   NOT NULL,
  attempts   INTEGER       NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_otp_identifier ON otp (identifier);

CREATE TABLE IF NOT EXISTS tags (
  id          VARCHAR(40)  PRIMARY KEY,
  name        VARCHAR(120) NOT NULL UNIQUE,
  parent_id   VARCHAR(40)  REFERENCES tags (id),
  description TEXT
);

CREATE TABLE IF NOT EXISTS universities (
  id              VARCHAR(20)  PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  registration_no VARCHAR(100),
  address         VARCHAR(500),
  district        VARCHAR(100),
  state           VARCHAR(100),
  verified        BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- 3. Problems + solutions ----------
CREATE TABLE IF NOT EXISTS problems (
  id                 VARCHAR(20)          PRIMARY KEY,
  title              VARCHAR(200)         NOT NULL,
  description        TEXT                 NOT NULL,
  evidence_urls      JSON,
  evidence_text      TEXT,
  latitude           DOUBLE PRECISION,
  longitude          DOUBLE PRECISION,
  address            VARCHAR(500),
  tags               JSON,
  ai_tags            JSON,
  ai_category        VARCHAR(100),
  ai_priority        priority_enum,
  ai_duplicate_check BOOLEAN,
  ai_duplicate_of    VARCHAR(20),
  embedding          vector(384),
  status             problem_status_enum  NOT NULL,
  assigned_to_id     VARCHAR(20)          REFERENCES users (id),
  submitter_id       VARCHAR(20)          NOT NULL REFERENCES users (id),
  created_at         TIMESTAMPTZ          NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ          NOT NULL DEFAULT now(),
  deleted_at         TIMESTAMPTZ,
  deletion_reason    TEXT,
  deleted_by_id      VARCHAR(20)
);
CREATE INDEX IF NOT EXISTS ix_problems_status      ON problems (status);
CREATE INDEX IF NOT EXISTS ix_problems_created_at  ON problems (created_at);
CREATE INDEX IF NOT EXISTS ix_problems_ai_category ON problems (ai_category);
CREATE INDEX IF NOT EXISTS ix_problems_submitter   ON problems (submitter_id);

CREATE TABLE IF NOT EXISTS evidence (
  id             VARCHAR(20)        PRIMARY KEY,
  problem_id     VARCHAR(20)        NOT NULL REFERENCES problems (id),
  type           evidence_type_enum NOT NULL,
  file_url       VARCHAR(500),
  transcript     TEXT,
  meta           TEXT,
  uploaded_by_id VARCHAR(20)        REFERENCES users (id),
  created_at     TIMESTAMPTZ        NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_evidence_problem_id ON evidence (problem_id);

CREATE TABLE IF NOT EXISTS problem_tags (
  id         SERIAL PRIMARY KEY,
  problem_id VARCHAR(20) NOT NULL REFERENCES problems (id),
  tag_id     VARCHAR(40) NOT NULL REFERENCES tags (id),
  confidence DOUBLE PRECISION,
  CONSTRAINT uq_problem_tag UNIQUE (problem_id, tag_id)
);
CREATE INDEX IF NOT EXISTS ix_problem_tags_problem_id ON problem_tags (problem_id);
CREATE INDEX IF NOT EXISTS ix_problem_tags_tag_id     ON problem_tags (tag_id);

-- ---------- 4. Routing + notifications ----------
CREATE TABLE IF NOT EXISTS routing_logs (
  id             SERIAL PRIMARY KEY,
  problem_id     VARCHAR(20)       NOT NULL REFERENCES problems (id),
  routed_to_type routing_type_enum NOT NULL,
  routed_to_id   VARCHAR(20)       NOT NULL REFERENCES users (id),
  reason         VARCHAR(255),
  created_at     TIMESTAMPTZ       NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_routing_logs_problem_id   ON routing_logs (problem_id);
CREATE INDEX IF NOT EXISTS ix_routing_logs_routed_to_id ON routing_logs (routed_to_id);

CREATE TABLE IF NOT EXISTS notifications (
  id           SERIAL PRIMARY KEY,
  user_id      VARCHAR(20)            NOT NULL REFERENCES users (id),
  type         notification_type_enum,
  message      TEXT                   NOT NULL,
  reference_id VARCHAR(20),
  is_read      BOOLEAN                NOT NULL DEFAULT FALSE,
  created_at   TIMESTAMPTZ            NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);

-- ---------- 5. University org + teams (BEFORE solutions: solutions.team_id FK) ----------
CREATE TABLE IF NOT EXISTS university_members (
  id            VARCHAR(20)  PRIMARY KEY,
  university_id VARCHAR(20)  NOT NULL REFERENCES universities (id),
  user_id       VARCHAR(20)  NOT NULL REFERENCES users (id),
  member_role   VARCHAR(20)  NOT NULL,
  department    VARCHAR(100),
  roll_number   VARCHAR(50),
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS teams (
  id            VARCHAR(20)  PRIMARY KEY,
  problem_id    VARCHAR(20)  NOT NULL REFERENCES problems (id),
  university_id VARCHAR(20)  REFERENCES universities (id),
  name          VARCHAR(200) NOT NULL,
  created_by    VARCHAR(20)  NOT NULL REFERENCES users (id),
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS team_members (
  id         VARCHAR(20) PRIMARY KEY,
  team_id    VARCHAR(20) NOT NULL REFERENCES teams (id),
  user_id    VARCHAR(20) NOT NULL REFERENCES users (id),
  role       VARCHAR(40),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS solutions (
  id                 VARCHAR(20)          PRIMARY KEY,
  title              VARCHAR(200)         NOT NULL,
  description        TEXT                 NOT NULL,
  approach           TEXT,
  tech_stack         JSON,
  estimated_timeline VARCHAR(100),
  estimated_budget   VARCHAR(100),
  status             solution_status_enum NOT NULL,
  github_url         VARCHAR(500),
  demo_url           VARCHAR(500),
  document_urls      JSON,
  problem_id         VARCHAR(20)          NOT NULL REFERENCES problems (id),
  team_id            VARCHAR(20)          REFERENCES teams (id),
  author_id          VARCHAR(20)          NOT NULL REFERENCES users (id),
  created_at         TIMESTAMPTZ          NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ          NOT NULL DEFAULT now()
);

-- ---------- 6. Industry + collaborations ----------
CREATE TABLE IF NOT EXISTS industries (
  id              VARCHAR(20)  PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  registration_no VARCHAR(100),
  type            VARCHAR(40),
  address         VARCHAR(500),
  district        VARCHAR(100),
  state           VARCHAR(100),
  latitude        DOUBLE PRECISION,
  longitude       DOUBLE PRECISION,
  domain_tags     JSON,
  verified        BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS collaborations (
  id          VARCHAR(20) PRIMARY KEY,
  proposal_id VARCHAR(20) NOT NULL REFERENCES solutions (id),
  industry_id VARCHAR(20) NOT NULL REFERENCES industries (id),
  stage       VARCHAR(20) NOT NULL,
  notes       TEXT,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS milestones (
  id               VARCHAR(20)  PRIMARY KEY,
  collaboration_id VARCHAR(20)  NOT NULL REFERENCES collaborations (id),
  title            VARCHAR(200) NOT NULL,
  description      TEXT,
  due_date         TIMESTAMPTZ,
  completed_at     TIMESTAMPTZ,
  status           VARCHAR(20)  NOT NULL,
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS deliverables (
  id           VARCHAR(20)  PRIMARY KEY,
  milestone_id VARCHAR(20)  NOT NULL REFERENCES milestones (id),
  file_url     VARCHAR(500),
  description  VARCHAR(300),
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ip_records (
  id               VARCHAR(20)  PRIMARY KEY,
  collaboration_id VARCHAR(20)  NOT NULL REFERENCES collaborations (id),
  type             VARCHAR(20),
  status           VARCHAR(20),
  reference_no     VARCHAR(100),
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS social_impact_reports (
  id                  VARCHAR(20)  PRIMARY KEY,
  collaboration_id    VARCHAR(20)  NOT NULL REFERENCES collaborations (id),
  beneficiaries_count INTEGER,
  impact_summary      TEXT,
  district            VARCHAR(100),
  state               VARCHAR(100),
  reported_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- 7. Engagement + audit ----------
CREATE TABLE IF NOT EXISTS comments (
  id          VARCHAR(20) PRIMARY KEY,
  entity_type VARCHAR(20) NOT NULL,
  entity_id   VARCHAR(20) NOT NULL,
  user_id     VARCHAR(20) NOT NULL REFERENCES users (id),
  content     TEXT        NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS upvotes (
  id         VARCHAR(20) PRIMARY KEY,
  problem_id VARCHAR(20) NOT NULL REFERENCES problems (id),
  user_id    VARCHAR(20) NOT NULL REFERENCES users (id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_upvote_problem_user UNIQUE (problem_id, user_id)
);

CREATE TABLE IF NOT EXISTS citizen_profiles (
  id       VARCHAR(20)  PRIMARY KEY,
  user_id  VARCHAR(20)  NOT NULL UNIQUE REFERENCES users (id),
  address  VARCHAR(500),
  district VARCHAR(100),
  state    VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id          VARCHAR(20)  PRIMARY KEY,
  user_id     VARCHAR(20)  REFERENCES users (id),
  action      VARCHAR(100) NOT NULL,
  entity_type VARCHAR(40),
  entity_id   VARCHAR(20),
  timestamp   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------- 8. Classification feedback / metrics ----------
CREATE TABLE IF NOT EXISTS classification_feedback (
  id                      VARCHAR(20)  PRIMARY KEY,
  problem_id              VARCHAR(20)  NOT NULL REFERENCES problems (id),
  ai_category_id          VARCHAR(100),
  ai_category_name        VARCHAR(100),
  ai_tags                 JSON,
  ai_priority             VARCHAR(20),
  corrected_category_id   VARCHAR(100) NOT NULL,
  corrected_category_name VARCHAR(100) NOT NULL,
  corrected_tags          JSON,
  corrected_priority      VARCHAR(20),
  user_id                 VARCHAR(20)  NOT NULL REFERENCES users (id),
  is_correction           BOOLEAN      NOT NULL DEFAULT TRUE,
  notes                   TEXT,
  created_at              TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_classification_feedback_problem_id
  ON classification_feedback (problem_id);

CREATE TABLE IF NOT EXISTS classification_metrics (
  id                  VARCHAR(20)  PRIMARY KEY,
  category_id         VARCHAR(100) NOT NULL,
  category_name       VARCHAR(100) NOT NULL,
  total_predictions   INTEGER      NOT NULL DEFAULT 0,
  correct_predictions INTEGER      NOT NULL DEFAULT 0,
  user_corrections    INTEGER      NOT NULL DEFAULT 0,
  priority_accuracy   JSON,
  updated_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_classification_metrics_category_id
  ON classification_metrics (category_id);

COMMIT;

-- ---------- 9. Verify (expect the 16 tables below) ----------
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
