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

cur.execute("DROP TABLE IF EXISTS blog;")

# Create table in PostgreSQL (if not exists)
create_table_query = """
    CREATE TABLE blog (
    blog_id INT PRIMARY KEY,                   -- Use job_id as the primary key
    title VARCHAR(255),                        -- Job title (e.g., 'Senior Site Reliability Engineer')
    content TEXT,                          -- Start date (e.g., 'September 20, 2024')
    content_image TEXT,                                 -- Job URL link
    short_description TEXT,                    -- Location (e.g., 'Lausanne, Vaud, Switzerland')
    creation_date TIMESTAMPTZ,                 -- Country (e.g., 'Switzerland')
    last_modified TIMESTAMPTZ,                    -- Seniority level (e.g., 'With Experience')
    post_date DATE                         -- Job description
);

"""

cur.execute(create_table_query)

# Create a Sequence: A sequence in PostgreSQL is a database object that generates unique numbers. You can create one that starts from the current highest job_id in your table.
create_sequence_query = '''
DROP SEQUENCE IF EXISTS blog_id_seq;
CREATE SEQUENCE blog_id_seq START WITH 1 ;
SELECT setval('blog_id_seq', (SELECT MAX(blog_id) FROM blog) + 1);
''' 

# Alter the Table to Use the Sequence for job_id: Once you're ready to switch from Airtable IDs to auto-generated job_ids, you can alter the table to default to using the sequence.

alter_table_query = '''
ALTER TABLE blog ALTER COLUMN blog_id SET DEFAULT nextval('blog_id_seq');
'''
cur.execute(create_sequence_query)

cur.execute(alter_table_query)
conn.commit()


cur.close()
conn.close()

