import os
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request
from psycopg2.extras import DictCursor

from database.connection import get_db_connection
from models.schemas import AddAlert, CreateAlert


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


def require_alert_user(cursor, auth0_sub: str) -> dict[str, Any]:
    cursor.execute(
        "SELECT name, email FROM users WHERE auth0_sub = %s",
        (auth0_sub,),
    )
    row = cursor.fetchone()
    if not row or not row["email"]:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


def require_backend_auth(request: Request) -> None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")


@router.post("/alerts")
@router.post("/add_alert")
async def add_alert(record: CreateAlert, request: Request):
    require_backend_auth(request)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        data = record.model_dump()
        user = require_alert_user(cursor, data["auth0_sub"])
        data["email"] = user["email"].strip().casefold()
        data["name"] = str(user["name"] or "").strip()
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

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Unable to save alert")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/alerts")
async def list_alerts(auth0_sub: str, request: Request):
    require_backend_auth(request)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        user = require_alert_user(cursor, auth0_sub)
        cursor.execute(
            """
            SELECT alert_id, country, seniority, sport_list, skills,
                   remote_office, hours, industry, type, job_area
            FROM alerts
            WHERE LOWER(email) = %s
            ORDER BY alert_id DESC
            """,
            (user["email"].strip().casefold(),),
        )
        return [dict(row) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to list alerts")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int, auth0_sub: str, request: Request):
    require_backend_auth(request)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        user = require_alert_user(cursor, auth0_sub)
        cursor.execute(
            "DELETE FROM alerts WHERE alert_id = %s AND LOWER(email) = %s RETURNING alert_id",
            (alert_id, user["email"].strip().casefold()),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Alert not found")
        conn.commit()
        return {"deleted": True, "alert_id": alert_id}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Unable to delete alert")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
