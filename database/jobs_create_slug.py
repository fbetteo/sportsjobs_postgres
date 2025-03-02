import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
import re

""" This was run ONCE to generate slugs for existing jobs. The idea was to have unique urls which weren't only the numeric job_id which was guessable by anyone.
This shouldn't be needed to run again. Even if we recreate the database, the slugs are already in the schema and we should be able to populate form backup"""

env_path = Path('sportsjobs_postgres') / '.env' 
load_dotenv(dotenv_path=env_path)

# PostgreSQL configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

def slugify(text):
    """Convert job name to a URL-friendly slug"""
    if not text:
        return ""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Replace multiple hyphens with a single one
    slug = re.sub(r'-+', '-', slug)
    return slug

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASSWORD, host=DB_HOST)
    cur = conn.cursor()
    
    # Get all jobs without slugs
    cur.execute("SELECT job_id, name FROM jobs WHERE slug IS NULL")
    jobs = cur.fetchall()
    
    for job_id, name in jobs:
        # Create a slug from job name + random string
        base_slug = slugify(name)
        if not base_slug:
            base_slug = "job"
        
        # Add a unique identifier to ensure uniqueness
        # unique_id = str(uuid.uuid4())[:8]
        slug = f"{job_id}-{base_slug}"
        
        # Update the job with the new slug
        cur.execute("UPDATE jobs SET slug = %s WHERE job_id = %s", (slug, job_id))
    
    conn.commit()
    print(f"Generated slugs for {len(jobs)} jobs")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()