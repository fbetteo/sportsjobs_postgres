import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path("sportsjobs_postgres") / ".env"
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

cur.execute("DROP TABLE IF EXISTS newsletter_signups;")

# Create table in PostgreSQL (if not exists)
create_table_query = """
    CREATE TABLE newsletter_signups (
    id SERIAL PRIMARY KEY,                     -- Auto-increment primary key
    email VARCHAR(255) UNIQUE NOT NULL,       -- Email address (unique and required)
    name VARCHAR(255),                        -- Name (nullable)
    signup_date TIMESTAMPTZ DEFAULT NOW(),    -- Signup timestamp with timezone (defaults to current time)
    source VARCHAR(255),                      -- UTM tracking source
    welcome_sent TIMESTAMPTZ,                 -- Welcome email sent timestamp (nullable)
    day2_sent TIMESTAMPTZ,                    -- Day 2 email sent timestamp (nullable)
    day4_sent TIMESTAMPTZ,                    -- Day 4 email sent timestamp (nullable)
    day6_sent TIMESTAMPTZ,                    -- Day 6 email sent timestamp (nullable)
    converted_to_premium BOOLEAN DEFAULT FALSE, -- Premium conversion status (default false)
    unsubscribed BOOLEAN DEFAULT FALSE        -- Unsubscribe status (default false)
);

"""

cur.execute(create_table_query)
conn.commit()

cur.close()
conn.close()
