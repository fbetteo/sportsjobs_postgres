import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('sportsjobs_postgres') / '.env' 
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
create_view_query = """
    CREATE OR REPLACE VIEW jobs_for_newsletter_view AS
SELECT 
    job_id, start_date,     name,
    company,
    'www.sportsjobs.online/jobs/' || job_id || '?source=newsletter' AS job_url

FROM jobs
ORDER BY start_date desc
;

"""

cur.execute(create_view_query)
conn.commit()


cur.close()
conn.close()

# conn.rollback()