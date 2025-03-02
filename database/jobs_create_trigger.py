import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

""" This script creates a trigger in PostgreSQL to automatically generate slugs for new jobs. Needed to be applied if we recreate the DB from scratch"""

env_path = Path('sportsjobs_postgres') / '.env' 
load_dotenv(dotenv_path=env_path)

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# SQL to create trigger
trigger_sql = """
CREATE OR REPLACE FUNCTION generate_job_slug()
RETURNS TRIGGER AS $$
DECLARE
    base_slug TEXT;
    final_slug TEXT;
BEGIN
    -- Create base slug from job name, or use 'job' if name is NULL
    IF NEW.name IS NOT NULL THEN
        base_slug := LOWER(REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9]', '-', 'g'));
        base_slug := REGEXP_REPLACE(base_slug, '-+', '-', 'g');
        base_slug := TRIM(BOTH '-' FROM base_slug);
    ELSE
        base_slug := 'job';
    END IF;
    

    final_slug := NEW.job_id || '-' || base_slug;
    
    -- Set the slug
    NEW.slug := final_slug;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS before_insert_job ON jobs;

CREATE TRIGGER before_insert_job
BEFORE INSERT ON jobs
FOR EACH ROW
WHEN (NEW.slug IS NULL)
EXECUTE FUNCTION generate_job_slug();
"""

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                           password=DB_PASSWORD, host=DB_HOST)
    cur = conn.cursor()
    
    cur.execute(trigger_sql)
    conn.commit()
    print("Slug generation trigger created successfully")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()