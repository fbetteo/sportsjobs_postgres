import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")


# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
)
cur = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS pending_job_postings (
    id UUID PRIMARY KEY,
    job_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    published_job_id BIGINT,
    stripe_session_id TEXT UNIQUE
);
"""

cur.execute(create_table_query)
conn.commit()

cur.close()
conn.close()
