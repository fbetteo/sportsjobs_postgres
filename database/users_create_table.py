import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('sportsjobs') / '.env' 
load_dotenv(dotenv_path=env_path)

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")


# Connect to PostgreSQL
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASSWORD, host=DB_HOST)
cur = conn.cursor()

# Create table in PostgreSQL (if not exists)
create_table_query = '''
CREATE TABLE users (
    id SERIAL PRIMARY KEY,         -- Assuming 'id' as an auto-increment primary key
    name VARCHAR(255),             -- Name column as a string
    email VARCHAR(255) UNIQUE,     -- Email as a unique string
    notes TEXT,                    -- Notes as a text field
    plan VARCHAR(100),             -- Plan column as a string (weekly_subscription)
    creation_date TIMESTAMPTZ,     -- Creation date with time zone for storing both date and time
    latest_plan_start_date TIMESTAMPTZ,  -- Plan start date with time zone
    signup_date DATE               -- Signup date as a date only (without time)
);

'''
cur.execute(create_table_query)
conn.commit()
cur.close()
conn.close()
