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

cur.execute("DROP TABLE IF EXISTS alerts;")

# Create table in PostgreSQL (if not exists)
create_table_query = """
    CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,                   
    name VARCHAR(255),                        
    email VARCHAR(150),                          
    notes TEXT,                                
    country TEXT[],                  
    seniority TEXT[],                
    sport_list TEXT[],                 
    skills TEXT[],
    remote_office TEXT[],
    industry TEXT[],
    type TEXT[],
    hours TEXT[],
    job_area TEXT[]                        
);

"""

cur.execute(create_table_query)
conn.commit()


cur.close()
conn.close()

# conn.rollback()