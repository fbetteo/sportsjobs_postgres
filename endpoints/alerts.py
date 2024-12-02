from fastapi import APIRouter, HTTPException, Request
from models.schemas import AddAlert
from psycopg2 import sql
import os
from database.connection import get_db_connection

router = APIRouter()

@router.post("/add_alert")
async def add_alert(record: AddAlert, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        data = record.model_dump()
        query = sql.SQL("INSERT INTO alerts (name, email, country, seniority, sport_list, skills, remote_office, hours) VALUES ({}) RETURNING *").format(
            sql.SQL(", ").join(sql.Placeholder() * len(data))
        )
        cursor.execute(query, tuple(data.values()))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")

        created_record = cursor.fetchone()
        conn.commit()

        return {"message": "Alert created successfully", "record": created_record}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()