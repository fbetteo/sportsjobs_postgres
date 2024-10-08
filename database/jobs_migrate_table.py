from pyairtable import Api
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('sportsjobs') / '.env' 
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
        INSERT INTO jobs (job_id, name, status, start_date, url, location, country, country_code, seniority, description, sport_list, skills, remote, remote_office, salary, language, tags, company, industry, job_type, hours, logo_permanent_url, job_area, post_duration, creation_date, post_tier, featured)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s);
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
    fields.get('sport_list'),
    fields.get('skills'),
    fields.get('remote'),
    fields.get('remote_office'),
    fields.get('salary'),
    fields.get('language'),
    fields.get('tags'),
    fields.get('company'),
    fields.get('industry'),
    fields.get('job_type'),
    fields.get('hours'),
    fields.get('logo_permanent_url'),
    fields.get('job_area'),
    fields.get('post_duration'),
    fields.get('creation_date'),
    fields.get('post_tier'),
    fields.get('featured')
)
        cur.execute(insert_query, data)

    conn.commit()
except Exception as e:
    print(e)
    conn.rollback()
finally:
    cur.close()
    conn.close()
