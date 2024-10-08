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
TABLE_NAME = os.getenv("AIRTABLE_USERS_TABLE")

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
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASSWORD, host=DB_HOST)
cur = conn.cursor()


# Insert data into PostgreSQL
for record in records:
    fields = record['fields']
    insert_query = '''
    INSERT INTO users (name, email, notes, plan, creation_date, latest_plan_start_date, signup_date)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    '''
    cur.execute(insert_query, (fields.get('Name'), fields.get('email'), fields.get('Notes'), fields.get('plan'), fields.get('creation_date'), fields.get('latest_plan_start_date'), fields.get('signup_date')))

conn.commit()
cur.close()
conn.close()
