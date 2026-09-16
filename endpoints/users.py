import os

from fastapi import APIRouter, HTTPException, Request
from psycopg2 import sql
from psycopg2.extras import Json, RealDictCursor

from database.connection import get_db_connection
from models.schemas import (
    AddUser,
    EnsureUser,
    LinkedinUpdate,
    CvUploadRecord,
    OnboardingUpdate,
    PaidProductAcknowledgement,
    SignupFunnelClaim,
    SignupFunnel,
)

router = APIRouter()


def _require_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")


def _normalize_email(email: str):
    return email.strip().lower()


def _checkout_session_id(record: EnsureUser):
    return record.stripe_checkout_session_id or record.session_id


def _row_id(row):
    if isinstance(row, dict):
        return row["id"]
    return row[0]


def _find_user_for_signup_funnel(cursor, signup_funnel_id=None, email=None):
    if signup_funnel_id:
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE signup_funnel_id = %s
            LIMIT 1;
            """,
            (signup_funnel_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if email:
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
            ORDER BY auth0_sub IS NULL, id DESC
            LIMIT 1;
            """,
            (_normalize_email(email),),
        )
        return cursor.fetchone()

    return None


def _find_user_for_auth_link(
    cursor, auth0_sub=None, signup_funnel_id=None, stripe_checkout_session_id=None, email=None
):
    if auth0_sub:
        cursor.execute(
            "SELECT id FROM users WHERE auth0_sub = %s LIMIT 1;",
            (auth0_sub,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if signup_funnel_id:
        cursor.execute(
            "SELECT id FROM users WHERE signup_funnel_id = %s LIMIT 1;",
            (signup_funnel_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_checkout_session_id:
        cursor.execute(
            "SELECT id FROM users WHERE stripe_checkout_session_id = %s LIMIT 1;",
            (stripe_checkout_session_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if email:
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = %s
            ORDER BY auth0_sub IS NULL, id DESC
            LIMIT 1;
            """,
            (_normalize_email(email),),
        )
        return cursor.fetchone()

    return None


def _find_user_for_claim(
    cursor,
    auth0_sub=None,
    stripe_checkout_session_id=None,
    signup_funnel_id=None,
    stripe_customer_id=None,
    stripe_subscription_id=None,
    checkout_email=None,
):
    if auth0_sub:
        cursor.execute(
            "SELECT id, auth0_sub FROM users WHERE auth0_sub = %s LIMIT 1;",
            (auth0_sub,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_checkout_session_id:
        cursor.execute(
            """
            SELECT id, auth0_sub
            FROM users
            WHERE stripe_checkout_session_id = %s
            LIMIT 1;
            """,
            (stripe_checkout_session_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if signup_funnel_id:
        cursor.execute(
            """
            SELECT id, auth0_sub
            FROM users
            WHERE signup_funnel_id = %s
            LIMIT 1;
            """,
            (signup_funnel_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_customer_id:
        cursor.execute(
            """
            SELECT id, auth0_sub
            FROM users
            WHERE stripe_customer_id = %s
            LIMIT 1;
            """,
            (stripe_customer_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_subscription_id:
        cursor.execute(
            """
            SELECT id, auth0_sub
            FROM users
            WHERE stripe_subscription_id = %s
            LIMIT 1;
            """,
            (stripe_subscription_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if checkout_email:
        cursor.execute(
            """
            SELECT id, auth0_sub
            FROM users
            WHERE LOWER(email) = %s
            ORDER BY auth0_sub IS NULL, id DESC
            LIMIT 1;
            """,
            (_normalize_email(checkout_email),),
        )
        return cursor.fetchone()

    return None


def _profile_response(row):
    onboarding = row.get("answers_json") or {}
    return {
        "auth0Sub": row["auth0_sub"],
        "email": row["email"],
        "name": row.get("name"),
        "linkedinUrl": row.get("linkedin_url"),
        "signupFunnelId": row.get("signup_funnel_id"),
        "stripeCheckoutSessionId": row.get("stripe_checkout_session_id"),
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
            u.signup_funnel_id,
            u.stripe_checkout_session_id,
            u.plan,
            u.subscription_status,
            u.signup_funnel_answers_json,
            u.signup_funnel_completed_at,
            u.paid_product_acknowledged_at,
            p.onboarding_completed_at,
            p.linkedin_url,
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


def _billing_response(row):
    return {
        "auth0_sub": row["auth0_sub"],
        "email": row["email"],
        "stripe_customer_id": row.get("stripe_customer_id"),
        "stripe_subscription_id": row.get("stripe_subscription_id"),
        "plan": row.get("plan") or "free",
        "subscription_status": row.get("subscription_status") or "none",
    }


def _fetch_billing(cursor, auth0_sub: str):
    cursor.execute(
        """
        SELECT
            auth0_sub,
            email,
            stripe_customer_id,
            stripe_subscription_id,
            plan,
            subscription_status
        FROM users
        WHERE auth0_sub = %s;
        """,
        (auth0_sub,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return _billing_response(row)


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
            user = _find_user_for_signup_funnel(
                cursor, record.signup_funnel_id, normalized_email
            )

            if user:
                cursor.execute(
                    """
                    UPDATE users
                    SET name = COALESCE(%s, name),
                        email = %s,
                        signup_funnel_id = COALESCE(signup_funnel_id, %s),
                        signup_funnel_answers_json = %s,
                        signup_funnel_completed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        record.name,
                        normalized_email,
                        record.signup_funnel_id,
                        Json(answers_json),
                        _row_id(user),
                    ),
                )
                user_id = _row_id(user)
            else:
                cursor.execute(
                    """
                    INSERT INTO users (
                        name,
                        email,
                        signup_funnel_id,
                        plan,
                        subscription_status,
                        creation_date,
                        signup_date,
                        signup_funnel_answers_json,
                        signup_funnel_completed_at,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, 'free', 'none', NOW(), CURRENT_DATE, %s, NOW(), NOW(), NOW())
                    RETURNING id;
                    """,
                    (
                        record.name,
                        normalized_email,
                        record.signup_funnel_id,
                        Json(answers_json),
                    ),
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
            user = _find_user_for_signup_funnel(
                cursor, record.signup_funnel_id, normalized_email
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            cursor.execute(
                """
                UPDATE users
                SET paid_product_acknowledged_at = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (record.paid_product_acknowledged_at, _row_id(user)),
            )

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


@router.post("/users/signup_funnel/claim")
async def claim_signup_funnel(record: SignupFunnelClaim, request: Request):
    _require_auth(request)

    raw_final_email = record.final_email or record.email or record.checkout_email
    final_email = _normalize_email(raw_final_email) if raw_final_email else None
    final_name = record.final_name or record.name

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            user = _find_user_for_claim(
                cursor,
                auth0_sub=record.auth0_sub,
                stripe_checkout_session_id=record.session_id,
                signup_funnel_id=record.signup_funnel_id,
                stripe_customer_id=record.stripe_customer_id,
                stripe_subscription_id=record.stripe_subscription_id,
                checkout_email=record.checkout_email,
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            existing_auth0_sub = user.get("auth0_sub")
            if existing_auth0_sub and existing_auth0_sub != record.auth0_sub:
                raise HTTPException(
                    status_code=409,
                    detail="Paid signup row is already linked to another Auth0 subject",
                )

            cursor.execute(
                """
                UPDATE users
                SET auth0_sub = %s,
                    email = COALESCE(%s, email),
                    name = COALESCE(%s, name),
                    signup_funnel_id = COALESCE(signup_funnel_id, %s),
                    stripe_checkout_session_id = COALESCE(stripe_checkout_session_id, %s),
                    stripe_customer_id = COALESCE(stripe_customer_id, %s),
                    stripe_subscription_id = COALESCE(stripe_subscription_id, %s),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    record.auth0_sub,
                    final_email,
                    final_name,
                    record.signup_funnel_id,
                    record.session_id,
                    record.stripe_customer_id,
                    record.stripe_subscription_id,
                    user["id"],
                ),
            )
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


@router.get("/users/billing")
async def get_user_billing(auth0_sub: str, request: Request):
    _require_auth(request)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            billing = _fetch_billing(cursor, auth0_sub)
            if not billing:
                raise HTTPException(status_code=404, detail="User not found")
            return billing

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
            normalized_email = _normalize_email(record.email)
            checkout_session_id = _checkout_session_id(record)
            user = _find_user_for_auth_link(
                cursor,
                record.auth0_sub,
                record.signup_funnel_id,
                checkout_session_id,
                normalized_email,
            )

            if user:
                cursor.execute(
                    """
                    UPDATE users
                    SET auth0_sub = COALESCE(auth0_sub, %s),
                        email = %s,
                        name = %s,
                        signup_funnel_id = COALESCE(signup_funnel_id, %s),
                        stripe_checkout_session_id = COALESCE(stripe_checkout_session_id, %s),
                        signup_funnel_answers_json = COALESCE(%s, signup_funnel_answers_json),
                        signup_funnel_completed_at = COALESCE(%s, signup_funnel_completed_at),
                        paid_product_acknowledged_at = COALESCE(%s, paid_product_acknowledged_at),
                        updated_at = NOW()
                    WHERE id = %s
                      AND (auth0_sub IS NULL OR auth0_sub = %s);
                    """,
                    (
                        record.auth0_sub,
                        normalized_email,
                        record.name,
                        record.signup_funnel_id,
                        checkout_session_id,
                        Json(record.signup_funnel_answers_json)
                        if record.signup_funnel_answers_json is not None
                        else None,
                        record.signup_funnel_completed_at,
                        record.paid_product_acknowledged_at,
                        _row_id(user),
                        record.auth0_sub,
                    ),
                )
                if cursor.rowcount == 0:
                    raise HTTPException(
                        status_code=409,
                        detail="Matched user is already linked to another Auth0 subject",
                    )
            else:
                cursor.execute(
                    """
                    INSERT INTO users (
                        auth0_sub,
                        email,
                        name,
                        signup_funnel_id,
                        stripe_checkout_session_id,
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
                    VALUES (%s, %s, %s, %s, %s, 'free', 'none', NOW(), CURRENT_DATE, %s, %s, %s, NOW(), NOW());
                    """,
                    (
                        record.auth0_sub,
                        normalized_email,
                        record.name,
                        record.signup_funnel_id,
                        checkout_session_id,
                        Json(record.signup_funnel_answers_json)
                        if record.signup_funnel_answers_json is not None
                        else None,
                        record.signup_funnel_completed_at,
                        record.paid_product_acknowledged_at,
                    ),
                )

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


@router.patch("/users/me/linkedin")
async def update_linkedin(record: LinkedinUpdate, request: Request):
    _require_auth(request)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, linkedin_url)
                SELECT id, %s FROM users WHERE auth0_sub = %s
                ON CONFLICT (user_id) DO UPDATE
                SET linkedin_url = EXCLUDED.linkedin_url, updated_at = NOW();
                """,
                (record.linkedin_url, record.auth0_sub),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            conn.commit()
            return _fetch_profile(cursor, record.auth0_sub)
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Could not save LinkedIn URL")
    finally:
        if conn:
            conn.close()


@router.get("/users/me/cv")
async def get_cv(auth0_sub: str, request: Request):
    _require_auth(request)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT c.id, c.s3_key, c.filename, c.size_bytes, c.created_at
                FROM cv_uploads c JOIN users u ON u.id = c.user_id
                WHERE u.auth0_sub = %s
                ORDER BY c.created_at DESC, c.id DESC LIMIT 1;
                """,
                (auth0_sub,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute(
                """
                SELECT c.s3_key FROM cv_uploads c
                JOIN users u ON u.id = c.user_id
                WHERE u.auth0_sub = %s;
                """,
                (auth0_sub,),
            )
            return {**dict(row), "all_keys": [item["s3_key"] for item in cursor.fetchall()]}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not load resume")
    finally:
        if conn:
            conn.close()


@router.post("/users/me/cv")
async def save_cv(record: CvUploadRecord, request: Request):
    _require_auth(request)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE auth0_sub = %s FOR UPDATE;", (record.auth0_sub,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            cursor.execute("SELECT s3_key FROM cv_uploads WHERE user_id = %s;", (user["id"],))
            old_keys = [row["s3_key"] for row in cursor.fetchall()]
            cursor.execute("DELETE FROM cv_uploads WHERE user_id = %s;", (user["id"],))
            cursor.execute(
                """
                INSERT INTO cv_uploads (user_id, s3_key, filename, content_type, size_bytes)
                VALUES (%s, %s, %s, 'application/pdf', %s)
                RETURNING id, filename, size_bytes, created_at;
                """,
                (user["id"], record.s3_key, record.filename, record.size_bytes),
            )
            saved = dict(cursor.fetchone())
            conn.commit()
            return {"cv": saved, "oldKeys": old_keys}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Could not save resume")
    finally:
        if conn:
            conn.close()


@router.delete("/users/me/cv")
async def delete_cv(auth0_sub: str, request: Request):
    _require_auth(request)
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                DELETE FROM cv_uploads c USING users u
                WHERE c.user_id = u.id AND u.auth0_sub = %s
                RETURNING c.s3_key;
                """,
                (auth0_sub,),
            )
            keys = [row["s3_key"] for row in cursor.fetchall()]
            conn.commit()
            return {"keys": keys}
    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Could not delete resume")
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
