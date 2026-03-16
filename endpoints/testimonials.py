from fastapi import APIRouter, HTTPException, Request
from models.schemas import AddTestimonial, ApproveTestimonial
from database.connection import get_db_connection
import os

router = APIRouter()


@router.post("/testimonials")
async def create_testimonial(record: AddTestimonial):
    """Public endpoint to collect testimonials pending approval."""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
                INSERT INTO testimonials (name, email, role, company, content, avatar_url, rating)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """

        values = (
            record.name,
            record.email,
            record.role,
            record.company,
            record.content,
            record.avatar_url,
            record.rating,
        )

        cursor.execute(insert_query, values)
        testimonial_id = cursor.fetchone()[0]
        conn.commit()

        return {"status": "ok", "id": testimonial_id}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/testimonials")
async def get_approved_testimonials(limit: int = 100):
    """Public endpoint to fetch approved testimonials for display."""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
                SELECT id, name, email, role, company, content, avatar_url, rating, created_at
                FROM testimonials
                WHERE approved = TRUE
                ORDER BY created_at DESC
                LIMIT %s;
            """

        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [{columns[i]: value for i, value in enumerate(row)} for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/admin/testimonials")
async def get_all_testimonials(
    request: Request, approved: bool | None = None, limit: int = 100
):
    """Admin endpoint to list testimonials, optionally filtered by approval status."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        base_query = """
                SELECT id, name, email, role, company, content, avatar_url, rating, approved, created_at
                FROM testimonials
            """
        params = []

        if approved is None:
            base_query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
        else:
            base_query += " WHERE approved = %s ORDER BY created_at DESC LIMIT %s"
            params.extend([approved, limit])

        cursor.execute(base_query, tuple(params))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        return [{columns[i]: value for i, value in enumerate(row)} for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/admin/testimonials/{testimonial_id}/approve")
async def approve_testimonial(
    testimonial_id: int,
    approval: ApproveTestimonial,
    request: Request,
):
    """Admin endpoint to approve or unapprove a testimonial."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        update_query = """
            UPDATE testimonials
            SET approved = %s
            WHERE id = %s
            RETURNING id, approved;
        """

        cursor.execute(update_query, (approval.approved, testimonial_id))
        updated = cursor.fetchone()

        if not updated:
            raise HTTPException(status_code=404, detail="Testimonial not found")

        conn.commit()

        return {"status": "ok", "id": updated[0], "approved": updated[1]}

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
