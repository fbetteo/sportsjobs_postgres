from pyairtable import Api
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('sportsjobs_postgres') / '.env' 
load_dotenv(dotenv_path=env_path)
# Airtable configuration
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE")
TABLE_NAME = os.getenv("AIRTABLE_JOBS_TABLE")

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# Fetch data from Airtable
api = Api(AIRTABLE_TOKEN)
airtable = api.table(BASE_ID, TABLE_NAME)

all_records = []

for page in airtable.iterate(sort=["creation_date"]):
    all_records.extend(page)

# Connect to PostgreSQL

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASSWORD, host=DB_HOST)
    cur = conn.cursor()


    # Insert data into PostgreSQL
    for record in all_records:
        fields = record['fields']
        insert_query = f"""
        INSERT INTO jobs (job_id, name, status, start_date, url, location, country, country_code, seniority, description, sport_list, skills, remote, remote_office, salary, language, tags, company, industry, job_type, hours, logo_permanent_url, job_area, post_duration, creation_date, post_tier, featured, airtable_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s);
"""
        data = (
    fields.get('id'),
    fields.get('Name'),
    fields.get('Status'),
    fields.get('Start date'),
    fields.get('url'),
    fields.get('location'),
    fields.get('country'),
    fields.get('country_code'),
    fields.get('seniority'),
    fields.get('desciption'),  # Ensure correct spelling ('description')
    fields.get('sport_list')[0] if fields.get('sport_list') else None,
    fields.get('skills'),
    fields.get('remote'),
    fields.get('remote_office'),
    fields.get('salary'),
    fields.get('language'),
    fields.get('tags'),
    fields.get('company'),
    fields.get('industry')[0] if fields.get('industry') else None,
    fields.get('type')[0] if fields.get('type') else None,
    fields.get('hours')[0] if fields.get('hours') else None,
    fields.get('logo_permanent_url'),
    fields.get('job_area'),
    fields.get('post_duration'),
    fields.get('creation_date'),
    fields.get('post_tier'),
    fields.get('featured'),
    record.get('id')
)
        cur.execute(insert_query, data)


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
    
    
    cur.execute("SELECT last_value FROM job_id_seq;")
    result = cur.fetchone()
    print(f' last sequence value : {result}')



except Exception as e:
    print(e)
    conn.rollback()
finally:
    cur.close()
    conn.close()
