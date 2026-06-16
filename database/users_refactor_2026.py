import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
)
cur = conn.cursor()

statements = [
    """
    ALTER TABLE users
        ADD COLUMN IF NOT EXISTS auth0_sub TEXT,
        ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
        ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
        ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'none',
        ADD COLUMN IF NOT EXISTS signup_funnel_answers_json JSONB,
        ADD COLUMN IF NOT EXISTS signup_funnel_completed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS paid_product_acknowledged_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
    """,
    """
    UPDATE users
    SET plan = COALESCE(plan, 'free'),
        subscription_status = COALESCE(subscription_status, 'none'),
        created_at = COALESCE(created_at, creation_date, NOW()),
        updated_at = COALESCE(updated_at, creation_date, NOW());
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS users_auth0_sub_unique_idx
    ON users (auth0_sub)
    WHERE auth0_sub IS NOT NULL;
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS users_stripe_customer_id_unique_idx
    ON users (stripe_customer_id)
    WHERE stripe_customer_id IS NOT NULL;
    """,
    """
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        sports_interests TEXT[] NOT NULL DEFAULT '{}',
        job_search_duration TEXT,
        hardest_part TEXT,
        country TEXT,
        role_interests TEXT[] NOT NULL DEFAULT '{}',
        role_unsure BOOLEAN NOT NULL DEFAULT FALSE,
        onboarding_completed_at TIMESTAMPTZ,
        answers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    ALTER TABLE user_profiles
        ADD COLUMN IF NOT EXISTS sports_interests TEXT[] NOT NULL DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS job_search_duration TEXT,
        ADD COLUMN IF NOT EXISTS hardest_part TEXT,
        ADD COLUMN IF NOT EXISTS country TEXT,
        ADD COLUMN IF NOT EXISTS role_interests TEXT[] NOT NULL DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS role_unsure BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS answers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    """,
    """
    CREATE TABLE IF NOT EXISTS saved_jobs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        job_id INTEGER NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
        notes TEXT,
        status VARCHAR(50) NOT NULL DEFAULT 'saved',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, job_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS saved_searches (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        filters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        alert_frequency TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cv_uploads (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        s3_key TEXT NOT NULL UNIQUE,
        filename TEXT NOT NULL,
        content_type TEXT,
        size_bytes BIGINT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cv_reviews (
        id SERIAL PRIMARY KEY,
        cv_upload_id INTEGER NOT NULL REFERENCES cv_uploads(id) ON DELETE CASCADE,
        review_status VARCHAR(50) NOT NULL DEFAULT 'pending',
        review_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS saved_jobs_user_id_idx ON saved_jobs (user_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS saved_searches_user_id_idx ON saved_searches (user_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS cv_uploads_user_id_idx ON cv_uploads (user_id);
    """,
]

for statement in statements:
    cur.execute(statement)

conn.commit()
cur.close()
conn.close()
