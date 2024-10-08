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

cur.execute("DROP TABLE IF EXISTS jobs;")

# Create table in PostgreSQL (if not exists)
create_table_query = '''
    CREATE TABLE jobs (
    job_id INT PRIMARY KEY,                   -- Use job_id as the primary key
    name VARCHAR(255),                        -- Job title (e.g., 'Senior Site Reliability Engineer')
    status VARCHAR(50),                       -- Job status (e.g., 'Open')
    start_date DATE,                          -- Start date (e.g., 'September 20, 2024')
    url TEXT,                                 -- Job URL link
    location VARCHAR(255),                    -- Location (e.g., 'Lausanne, Vaud, Switzerland')
    country VARCHAR(100),                     -- Country (e.g., 'Switzerland')
    country_code VARCHAR(5),                  -- Country code (e.g., 'CH')
    seniority VARCHAR(50),                    -- Seniority level (e.g., 'With Experience')
    description TEXT,                         -- Job description
    sport_list VARCHAR(100),                  -- Sport list (e.g., 'Basketball')
    skills TEXT[],                            -- Array of skills (e.g., ['Python', 'Sports', 'Machine'])
    remote BOOLEAN,                           -- Whether the job is remote (Yes/No converted to boolean)
    remote_office VARCHAR(100),               -- Remote office description (e.g., 'Remote')
    salary VARCHAR(100),                      -- Salary details
    language TEXT[],                    -- Language (e.g., 'English')
    tags TEXT[],                              -- Tags (e.g., array of tags)
    company VARCHAR(255),                     -- Company name (e.g., 'Genius Sports')
    industry VARCHAR(100),                    -- Industry (e.g., 'Sports')
    job_type VARCHAR(100),                    -- Job type (e.g., 'Permanent')
    hours VARCHAR(50),                        -- Hours (e.g., 'Fulltime')
    logo_permanent_url TEXT,                  -- URL for the company's logo
    job_area VARCHAR(255),                     -- Job area (e.g., 'DS/ML/AI')
    post_duration INT,
    creation_date TIMESTAMPTZ,                 -- Creation date with time zone for storing both date and time
    post_tier VARCHAR(50),
    featured VARCHAR(50)

);


'''
cur.execute(create_table_query)

# Create a Sequence: A sequence in PostgreSQL is a database object that generates unique numbers. You can create one that starts from the current highest job_id in your table.
create_sequence_query = '''
DROP SEQUENCE IF EXISTS job_id_seq;
CREATE SEQUENCE job_id_seq START WITH 1 ;
SELECT setval('job_id_seq', (SELECT MAX(job_id) FROM jobs) + 1);
''' 

# Alter the Table to Use the Sequence for job_id: Once you're ready to switch from Airtable IDs to auto-generated job_ids, you can alter the table to default to using the sequence.

alter_table_query = '''
ALTER TABLE jobs ALTER COLUMN job_id SET DEFAULT nextval('job_id_seq');
'''
cur.execute(create_sequence_query)

cur.execute(alter_table_query)
conn.commit()


cur.close()
conn.close()
