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
TABLE_NAME = os.getenv("AIRTABLE_ALERTS_TABLE")

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# Fetch data from Airtable
api = Api(AIRTABLE_TOKEN)
airtable = api.table(BASE_ID, TABLE_NAME)
records = airtable.all()

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASSWORD, host=DB_HOST)
    cur = conn.cursor()



    # Insert data into PostgreSQL
    for record in records:
        fields = record['fields']
        insert_query = '''
        INSERT INTO alerts (name, email, notes, country, seniority, sport_list, skills, remote_office, industry, type, hours, job_area)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        cur.execute(insert_query, (fields.get('Name'), fields.get('email'), fields.get('Notes'), fields.get('country'), fields.get('seniority'), fields.get('sport_list'), fields.get('skills'),fields.get('remote_office'), fields.get('industry'), fields.get('type'), fields.get('hours'), fields.get('job_area') ))

    conn.commit()
except Exception as e:
    print(e)
    conn.rollback()
finally:
    cur.close()
    conn.close()






# sudo ufw allow from 35.160.120.126 to any port 5432
# sudo ufw allow from 44.233.151.27 to any port 5432
# sudo ufw allow from 34.211.200.85 to any port 5432


