from fastapi import APIRouter, HTTPException, Request
import os
from database.connection import get_db_connection
from typing import Optional, List
from datetime import datetime
from models.schemas import GetJob

router = APIRouter()

@router.post("/jobs")
async def get_jobs(
    query_options: GetJob ,request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = query_options.model_dump()
        # Base query
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        # Add filters if they exist
        if query_options.filters:
            for key, value in query_options.filters.items():
                if value:
                    query += f" AND {key} = %s"
                    params.append(value)

        # Add sorting
        query += f" ORDER BY {query_options.sort_by} {query_options.sort_direction.upper()}"
        
        # Add limit
        query += " LIMIT %s"
        params.append(query_options.limit)

        # Execute query
        cur.execute(query, tuple(params))
        
        # Fetch results
        jobs = cur.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cur.description]
        
        # Convert to list of dictionaries
        result = []
        for job in jobs:
            job_dict = {columns[i]: value for i, value in enumerate(job)}
            # Format the response similar to Airtable format
            result.append(
                # "id": job_dict["job_id"],
                # "fields":
                  job_dict
            )


        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()