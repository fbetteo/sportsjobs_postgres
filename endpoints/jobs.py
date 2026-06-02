import os
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from psycopg2.errors import UniqueViolation
from psycopg2.extras import Json

from database.connection import get_db_connection
from models.schemas import AddJob, GetJob, PublishPendingJob

router = APIRouter()


def _insert_job(cursor, job_data: AddJob) -> int:
    insert_query = """
        INSERT INTO jobs (
            name,
            url,
            location,
            country,
            seniority,
            description,
            sport_list,
            skills,
            remote_office,
            salary,
            language,
            company,
            industry,
            hours,
            featured,
            logo_permanent_url,
            creation_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING job_id;
    """

    values = (
        job_data.name,
        job_data.url,
        job_data.location,
        job_data.country,
        job_data.seniority,
        job_data.description,
        job_data.sport_list,
        job_data.skills,
        job_data.remote_office,
        job_data.salary,
        job_data.language,
        job_data.company,
        job_data.industry,
        job_data.hours,
        job_data.featured,
        job_data.logo_permanent_url,
        job_data.creation_date,
    )

    cursor.execute(insert_query, values)
    return cursor.fetchone()[0]


@router.post("/jobs")
async def get_jobs(query_options: GetJob, request: Request):
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

        # Define string columns that should use case-insensitive comparison. I have other string columns as filters but currently no need to lower as the regular parameter is in the right format. Maybe I should do it anyway??
        string_columns = ["company"]

        # Add filters if they exist
        if query_options.filters:
            for key, value in query_options.filters.items():
                if value:
                    if key in string_columns:
                        query += f" AND LOWER({key}) = LOWER(%s)"
                    else:
                        query += f" AND {key} = %s"
                    params.append(value)

        # Add sorting
        query += (
            f" ORDER BY {query_options.sort_by} {query_options.sort_direction.upper()}"
        )

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


@router.post("/add_job")
async def post_jobs(job_data: AddJob, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            job_id = _insert_job(cursor, job_data)
            conn.commit()

            return {"message": "Job created successfully", "job_id": job_id}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.post("/pending_job_postings")
async def create_pending_job_posting(job_data: AddJob, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()
        pending_job_id = uuid4()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pending_job_postings (id, job_data)
                VALUES (%s, %s);
                """,
                (str(pending_job_id), Json(job_data.model_dump(mode="json"))),
            )
            conn.commit()

        return {"pending_job_id": str(pending_job_id)}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.post("/pending_job_postings/{pending_job_id}/publish")
async def publish_pending_job_posting(
    pending_job_id: UUID, publish_data: PublishPendingJob, request: Request
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT job_data, published_job_id
                FROM pending_job_postings
                WHERE id = %s
                FOR UPDATE;
                """,
                (str(pending_job_id),),
            )
            pending_job = cursor.fetchone()

            if not pending_job:
                raise HTTPException(status_code=404, detail="Pending job posting not found")

            job_data, published_job_id = pending_job
            if published_job_id is not None:
                conn.commit()
                return {"job_id": published_job_id}

            job_id = _insert_job(cursor, AddJob.model_validate(job_data))
            cursor.execute(
                """
                UPDATE pending_job_postings
                SET published_at = NOW(),
                    published_job_id = %s,
                    stripe_session_id = %s
                WHERE id = %s;
                """,
                (job_id, publish_data.stripe_session_id, str(pending_job_id)),
            )
            conn.commit()

            return {"job_id": job_id}

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except UniqueViolation:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=409, detail="Stripe session has already been used"
        )

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.get("/similar_jobs")
async def get_similar_jobs(
    request: Request,
    exclude_id: int,
    country: Optional[str] = None,
    sport: Optional[str] = None,
    seniority: Optional[str] = None,
):
    """
    Get 3 random similar jobs based on filters while excluding a specific job.
    Uses database-level randomization for efficiency.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Base query with random ordering
        query = "SELECT * FROM jobs WHERE job_id != %s AND creation_date >= NOW() - INTERVAL '1 month'"
        params = [exclude_id]

        # Add filters if they exist
        if country:
            query += " AND country = %s"
            params.append(country)

        if sport:
            query += " AND sport_list = %s"
            params.append(sport)

        if seniority:
            query += " AND seniority = %s"
            params.append(seniority)

        # Use PostgreSQL's RANDOM() for database-level randomization
        # Limit to 3 results
        query += " ORDER BY RANDOM() LIMIT 3"

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
            result.append(job_dict)

        return {"jobs": result, "count": len(result)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()
