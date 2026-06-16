import os

from fastapi import APIRouter, HTTPException, Request
from psycopg2 import sql
from psycopg2.extras import Json, RealDictCursor

from database.connection import get_db_connection
from models.schemas import (
    AddUser,
    EnsureUser,
    OnboardingUpdate,
    PaidProductAcknowledgement,
    SignupFunnel,
)

router = APIRouter()


def _require_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")


def _normalize_email(email: str):
    return email.strip().lower()


def _profile_response(row):
    onboarding = row.get("answers_json") or {}
    return {
        "auth0Sub": row["auth0_sub"],
        "email": row["email"],
        "name": row.get("name"),
        "plan": row.get("plan") or "free",
        "subscriptionStatus": row.get("subscription_status") or "none",
        "onboardingCompletedAt": row.get("onboarding_completed_at"),
        "onboarding": onboarding,
        "signupFunnelAnswers": row.get("signup_funnel_answers_json"),
        "signupFunnelCompletedAt": row.get("signup_funnel_completed_at"),
        "paidProductAcknowledgedAt": row.get("paid_product_acknowledged_at"),
    }


def _fetch_profile(cursor, auth0_sub: str):
    cursor.execute(
        """
        SELECT
            u.id,
            u.auth0_sub,
            u.email,
            u.name,
            u.plan,
            u.subscription_status,
            u.signup_funnel_answers_json,
            u.signup_funnel_completed_at,
            u.paid_product_acknowledged_at,
            p.onboarding_completed_at,
            p.answers_json
        FROM users u
        LEFT JOIN user_profiles p ON p.user_id = u.id
        WHERE u.auth0_sub = %s;
        """,
        (auth0_sub,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return _profile_response(row)


def _upsert_user_profile(cursor, user_id, onboarding, answers_json):
    cursor.execute(
        """
        INSERT INTO user_profiles (
            user_id,
            sports_interests,
            job_search_duration,
            hardest_part,
            country,
            role_interests,
            role_unsure,
            onboarding_completed_at,
            answers_json,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, NOW(), NOW())
        ON CONFLICT (user_id)
        DO UPDATE SET
            sports_interests = EXCLUDED.sports_interests,
            job_search_duration = EXCLUDED.job_search_duration,
            hardest_part = EXCLUDED.hardest_part,
            country = EXCLUDED.country,
            role_interests = EXCLUDED.role_interests,
            role_unsure = EXCLUDED.role_unsure,
            onboarding_completed_at = NOW(),
            answers_json = EXCLUDED.answers_json,
            updated_at = NOW();
        """,
        (
            user_id,
            onboarding.sports_interests,
            onboarding.job_search_duration,
            onboarding.hardest_part,
            onboarding.country,
            onboarding.role_interests,
            onboarding.role_unsure,
            Json(answers_json),
        ),
    )


@router.post("/users/signup_funnel")
async def save_signup_funnel(record: SignupFunnel, request: Request):
    _require_auth(request)

    normalized_email = _normalize_email(record.email)
    onboarding = record.onboarding
    answers_json = {
        **onboarding.model_dump(mode="json", by_alias=True),
        "source": record.source,
    }

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = %s
                ORDER BY auth0_sub IS NULL, id DESC
                LIMIT 1;
                """,
                (normalized_email,),
            )
            user = cursor.fetchone()

            if user:
                cursor.execute(
                    """
                    UPDATE users
                    SET name = COALESCE(%s, name),
                        email = %s,
                        signup_funnel_answers_json = %s,
                        signup_funnel_completed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (record.name, normalized_email, Json(answers_json), user[0]),
                )
                user_id = user[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO users (
                        name,
                        email,
                        plan,
                        subscription_status,
                        creation_date,
                        signup_date,
                        signup_funnel_answers_json,
                        signup_funnel_completed_at,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, 'free', 'none', NOW(), CURRENT_DATE, %s, NOW(), NOW(), NOW());
                    RETURNING id;
                    """,
                    (record.name, normalized_email, Json(answers_json)),
                )
                user_id = cursor.fetchone()[0]

            _upsert_user_profile(cursor, user_id, onboarding, answers_json)

            conn.commit()
            return {"success": True}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.patch("/users/signup_funnel/paid-product-acknowledgement")
async def acknowledge_paid_product(
    record: PaidProductAcknowledgement, request: Request
):
    _require_auth(request)

    normalized_email = _normalize_email(record.email)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET paid_product_acknowledged_at = %s,
                    updated_at = NOW()
                WHERE id = (
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = %s
                    ORDER BY auth0_sub IS NULL, id DESC
                    LIMIT 1
                );
                """,
                (record.paid_product_acknowledged_at, normalized_email),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

            conn.commit()
            return {"success": True}

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.get("/users/me")
async def get_current_user(auth0_sub: str, request: Request):
    _require_auth(request)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            profile = _fetch_profile(cursor, auth0_sub)
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            return profile

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.post("/users/ensure")
async def ensure_user(record: EnsureUser, request: Request):
    _require_auth(request)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    auth0_sub,
                    email,
                    name,
                    plan,
                    subscription_status,
                    creation_date,
                    signup_date,
                    signup_funnel_answers_json,
                    signup_funnel_completed_at,
                    paid_product_acknowledged_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'free',
                    'none',
                    NOW(),
                    CURRENT_DATE,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (auth0_sub)
                WHERE auth0_sub IS NOT NULL
                DO UPDATE SET
                    email = EXCLUDED.email,
                    name = EXCLUDED.name,
                    signup_funnel_answers_json = COALESCE(
                        EXCLUDED.signup_funnel_answers_json,
                        users.signup_funnel_answers_json
                    ),
                    signup_funnel_completed_at = COALESCE(
                        EXCLUDED.signup_funnel_completed_at,
                        users.signup_funnel_completed_at
                    ),
                    paid_product_acknowledged_at = COALESCE(
                        EXCLUDED.paid_product_acknowledged_at,
                        users.paid_product_acknowledged_at
                    ),
                    updated_at = NOW()
                WHERE users.email IS DISTINCT FROM EXCLUDED.email
                   OR users.name IS DISTINCT FROM EXCLUDED.name
                   OR (
                        EXCLUDED.signup_funnel_answers_json IS NOT NULL
                        AND users.signup_funnel_answers_json IS DISTINCT FROM EXCLUDED.signup_funnel_answers_json
                   )
                   OR (
                        EXCLUDED.signup_funnel_completed_at IS NOT NULL
                        AND users.signup_funnel_completed_at IS DISTINCT FROM EXCLUDED.signup_funnel_completed_at
                   )
                   OR (
                        EXCLUDED.paid_product_acknowledged_at IS NOT NULL
                        AND users.paid_product_acknowledged_at IS DISTINCT FROM EXCLUDED.paid_product_acknowledged_at
                   )
                RETURNING id;
                """,
                (
                    record.auth0_sub,
                    record.email,
                    record.name,
                    Json(record.signup_funnel_answers_json)
                    if record.signup_funnel_answers_json is not None
                    else None,
                    record.signup_funnel_completed_at,
                    record.paid_product_acknowledged_at,
                ),
            )
            cursor.fetchone()
            conn.commit()

            profile = _fetch_profile(cursor, record.auth0_sub)
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            return profile

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.patch("/users/me/onboarding")
async def update_onboarding(record: OnboardingUpdate, request: Request):
    _require_auth(request)

    onboarding = record.onboarding
    answers_json = onboarding.model_dump(mode="json", by_alias=True)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE auth0_sub = %s;",
                (record.auth0_sub,),
            )
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            _upsert_user_profile(cursor, user["id"], onboarding, answers_json)
            conn.commit()

            profile = _fetch_profile(cursor, record.auth0_sub)
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            return profile

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.post("/add_user")
async def add_user(record: AddUser, request: Request):
    _require_auth(request)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        data = record.model_dump()
        query = sql.SQL(
            "INSERT INTO users (name, email, plan, creation_date) VALUES ({}) RETURNING *"
        ).format(sql.SQL(", ").join(sql.Placeholder() * len(data)))
        cursor.execute(query, tuple(data.values()))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")

        created_record = cursor.fetchone()
        conn.commit()

        return {"message": "User created successfully", "record": created_record}

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()
