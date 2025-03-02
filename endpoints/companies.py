from fastapi import APIRouter, HTTPException, Request
import os
from database.connection import get_db_connection
from typing import Optional, List
from datetime import datetime
from models.schemas import GetCompanies

router = APIRouter()

@router.post("/companies")
async def get_companies(
    query_options: GetCompanies ,request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = query_options.model_dump()
        # Base query
        query = """SELECT company, count(*) FROM jobs WHERE company IS NOT NULL 
            GROUP BY company 
            ORDER BY company ASC"""

        # Execute query
        cur.execute(query)
        
        # Fetch results
        companies = cur.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cur.description]
        
        # Convert to list of dictionaries
        result = []
        for company in companies:
            company_dict = {columns[i]: value for i, value in enumerate(company)}
            # Format the response similar to Airtable format
            result.append(
                # "id": job_dict["job_id"],
                # "fields":
                  company_dict
            )


        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()