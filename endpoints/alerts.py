import os
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request
from psycopg2.extras import DictCursor

from database.connection import get_db_connection
from models.schemas import AddAlert


router = APIRouter()

ALERT_FILTER_FIELDS = (
    "country",
    "seniority",
    "sport_list",
    "skills",
    "remote_office",
    "hours",
    "industry",
    "type",
    "job_area",
)


def alert_signature(record: Mapping[str, Any]) -> tuple[tuple[str, ...], ...]:
    """Return an order- and case-insensitive signature for duplicate detection."""
    normalized = AddAlert.model_validate(
        {
            "name": record.get("name"),
            "email": record.get("email"),
            **{field: record.get(field) for field in ALERT_FILTER_FIELDS},
        }
    )
    data = normalized.model_dump()
    return tuple(
        tuple(sorted((str(value).casefold() for value in data[field])))
        for field in ALERT_FILTER_FIELDS
    )


@router.post("/add_alert")
async def add_alert(record: AddAlert, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        data = record.model_dump()
        requested_signature = alert_signature(data)

        # Keep the duplicate check and insert atomic for concurrent requests
        # targeting the same normalized email address.
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (data["email"],),
        )

        cursor.execute(
            """
            SELECT alert_id, name, email, country, seniority, sport_list,
                   skills, remote_office, hours, industry, type, job_area
            FROM alerts
            WHERE LOWER(email) = %s
            ORDER BY alert_id
            """,
            (data["email"],),
        )
        for existing in cursor.fetchall():
            existing_record = dict(existing)
            if alert_signature(existing_record) == requested_signature:
                cursor.execute(
                    """
                    UPDATE alerts
                    SET name = %s, email = %s
                    WHERE alert_id = %s
                    RETURNING *
                    """,
                    (data["name"], data["email"], existing_record["alert_id"]),
                )
                result = dict(cursor.fetchone())
                conn.commit()
                return {
                    "message": "Alert already exists",
                    "record": result,
                    "duplicate": True,
                }

        cursor.execute(
            """
            INSERT INTO alerts (
                name, email, country, seniority, sport_list,
                skills, remote_office, hours, industry, type, job_area
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["name"],
                data["email"],
                data["country"],
                data["seniority"],
                data["sport_list"],
                data["skills"],
                data["remote_office"],
                data["hours"],
                data["industry"],
                data["type"],
                data["job_area"],
            ),
        )
        result = dict(cursor.fetchone())
        conn.commit()
        return {
            "message": "Alert created successfully",
            "record": result,
            "duplicate": False,
        }

    except Exception as error:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
