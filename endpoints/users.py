from fastapi import APIRouter, HTTPException, Request
from models.schemas import AddUser
from psycopg2 import sql
import os
from database.connection import get_db_connection

router = APIRouter()


@router.post("/add_user")
async def add_user(record: AddUser, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Example query to update a user's plan based on email
        data = record.model_dump()
        query = sql.SQL("INSERT INTO users (name, email, plan, creation_date) VALUES ({}) RETURNING *").format(
            sql.SQL(", ").join(sql.Placeholder() * len(data))
            )
        print(query.as_string(conn))
        # Execute the query with values as parameters
        cursor.execute(query, tuple(data.values()))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")

        created_record = cursor.fetchone()
        conn.commit()

        return {"message": "Usert  created successfully", "record": created_record}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()