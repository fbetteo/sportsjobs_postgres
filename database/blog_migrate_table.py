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
TABLE_NAME = os.getenv("AIRTABLE_BLOG_TABLE")

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# Fetch data from Airtable
api = Api(AIRTABLE_TOKEN)
airtable = api.table(BASE_ID, TABLE_NAME)
records = airtable.all(sort=["creation_date"])

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASSWORD, host=DB_HOST)
    cur = conn.cursor()



    # Insert data into PostgreSQL
    for record in records:
        fields = record['fields']
        insert_query = '''
        INSERT INTO blog (blog_id, title, content, short_description, creation_date, last_modified, post_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        '''
        cur.execute(insert_query, (fields.get('id'), fields.get('Title'), fields.get('content'), fields.get('short_description'), fields.get('creation_date'), fields.get('last_modified'), fields.get('post_date')))

    conn.commit()
except Exception as e:
    print(e)
    conn.rollback()
finally:
    cur.close()
    conn.close()
