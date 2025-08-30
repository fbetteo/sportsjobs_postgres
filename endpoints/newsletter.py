from fastapi import APIRouter, HTTPException, Request
from models.schemas import AddNewsletterSignup
from psycopg2 import sql
import os
from database.connection import get_db_connection

router = APIRouter()


@router.post("/add_newsletter_signup")
async def add_newsletter_signup(record: AddNewsletterSignup, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        check_query = "SELECT id FROM newsletter_signups WHERE email = %s"
        cursor.execute(check_query, (record.email,))
        existing_record = cursor.fetchone()

        if existing_record:
            raise HTTPException(
                status_code=409, detail="Email already exists in newsletter signups"
            )

        # Insert new newsletter signup
        data = record.model_dump()
        # Filter out None values to let database defaults work
        data = {k: v for k, v in data.items() if v is not None}

        columns = list(data.keys())
        placeholders = [sql.Placeholder() for _ in data.values()]

        query = sql.SQL(
            "INSERT INTO newsletter_signups ({}) VALUES ({}) RETURNING *"
        ).format(
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(placeholders),
        )

        cursor.execute(query, tuple(data.values()))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not created")

        created_record = cursor.fetchone()
        conn.commit()

        return {
            "message": "Newsletter signup created successfully",
            "record": created_record,
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
