import os

import stripe
from fastapi import APIRouter, HTTPException, Request

from database.connection import get_db_connection
from models.schemas import CheckoutSync

router = APIRouter()


SUBSCRIPTION_STATUSES = {"trialing", "active", "past_due", "canceled"}
PAST_DUE_STATUSES = {"incomplete", "incomplete_expired", "past_due", "unpaid"}


def _require_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")


def _to_dict(stripe_object):
    if hasattr(stripe_object, "to_dict_recursive"):
        return stripe_object.to_dict_recursive()
    return stripe_object


def _nested(value, *keys):
    current = value or {}
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _stripe_id(value):
    if isinstance(value, dict):
        return value.get("id")
    return value


def _price_plan_map():
    return {
        os.getenv("STRIPE_MONTHLY_PRICE_ID"): "monthly_subscription",
        os.getenv("STRIPE_YEARLY_PRICE_ID"): "yearly_subscription",
        os.getenv("STRIPE_LIFETIME_PRICE_ID"): "lifetime",
    }


def _plan_from_price(price_id):
    if not price_id:
        return None
    return _price_plan_map().get(price_id)


def _plan_from_name(plan_name):
    if not plan_name:
        return None

    normalized = plan_name.lower()
    if "lifetime" in normalized:
        return "lifetime"
    if "year" in normalized or "annual" in normalized:
        return "yearly_subscription"
    if "month" in normalized:
        return "monthly_subscription"
    return None


def _subscription_status(stripe_status):
    if stripe_status in SUBSCRIPTION_STATUSES:
        return stripe_status
    if stripe_status in PAST_DUE_STATUSES:
        return "past_due"
    return "none"


def _first_subscription_price(subscription):
    item = _nested(subscription, "items", "data")
    if not item:
        return None
    return _nested(item[0], "price", "id")


def _find_user(
    cursor,
    auth0_sub=None,
    signup_funnel_id=None,
    stripe_checkout_session_id=None,
    stripe_customer_id=None,
    email=None,
):
    if auth0_sub:
        cursor.execute("SELECT id, plan FROM users WHERE auth0_sub = %s;", (auth0_sub,))
        user = cursor.fetchone()
        if user:
            return user

    if signup_funnel_id:
        cursor.execute(
            "SELECT id, plan FROM users WHERE signup_funnel_id = %s;",
            (signup_funnel_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_checkout_session_id:
        cursor.execute(
            "SELECT id, plan FROM users WHERE stripe_checkout_session_id = %s;",
            (stripe_checkout_session_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if stripe_customer_id:
        cursor.execute(
            "SELECT id, plan FROM users WHERE stripe_customer_id = %s;",
            (stripe_customer_id,),
        )
        user = cursor.fetchone()
        if user:
            return user

    if email:
        cursor.execute(
            """
            SELECT id, plan
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            ORDER BY auth0_sub IS NULL, id DESC
            LIMIT 1;
            """,
            (email,),
        )
        return cursor.fetchone()

    return None


def _upsert_user_from_checkout(cursor, session):
    metadata = session.get("metadata") or {}
    auth0_sub = metadata.get("auth0_sub")
    signup_funnel_id = metadata.get("signup_funnel_id") or metadata.get("signupFunnelId")
    stripe_checkout_session_id = session.get("id")
    email = (
        metadata.get("email")
        or _nested(session, "customer_details", "email")
        or session.get("customer_email")
    )
    name = _nested(session, "customer_details", "name")
    stripe_customer_id = _stripe_id(session.get("customer"))
    stripe_subscription_id = _stripe_id(session.get("subscription"))
    price_id = metadata.get("priceId")
    plan = _plan_from_price(price_id) or _plan_from_name(metadata.get("planName"))

    if (
        not auth0_sub
        and not signup_funnel_id
        and not stripe_checkout_session_id
        and not stripe_customer_id
        and not email
    ):
        return

    user = _find_user(
        cursor,
        auth0_sub=auth0_sub,
        signup_funnel_id=signup_funnel_id,
        stripe_checkout_session_id=stripe_checkout_session_id,
        stripe_customer_id=stripe_customer_id,
        email=email,
    )
    subscription_status = "active" if plan == "lifetime" else "active"

    if user:
        cursor.execute(
            """
            UPDATE users
            SET auth0_sub = COALESCE(auth0_sub, %s),
                email = COALESCE(%s, email),
                name = COALESCE(%s, name),
                signup_funnel_id = COALESCE(signup_funnel_id, %s),
                stripe_checkout_session_id = COALESCE(stripe_checkout_session_id, %s),
                stripe_customer_id = COALESCE(%s, stripe_customer_id),
                stripe_subscription_id = COALESCE(%s, stripe_subscription_id),
                plan = COALESCE(%s, plan, 'free'),
                subscription_status = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (
                auth0_sub,
                email,
                name,
                signup_funnel_id,
                stripe_checkout_session_id,
                stripe_customer_id,
                stripe_subscription_id,
                plan,
                subscription_status,
                user[0],
            ),
        )
        return

    cursor.execute(
        """
        INSERT INTO users (
            auth0_sub,
            email,
            name,
            signup_funnel_id,
            stripe_checkout_session_id,
            stripe_customer_id,
            stripe_subscription_id,
            plan,
            subscription_status,
            creation_date,
            signup_date,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, 'free'), %s, NOW(), CURRENT_DATE, NOW(), NOW());
        """,
        (
            auth0_sub,
            email,
            name,
            signup_funnel_id,
            stripe_checkout_session_id,
            stripe_customer_id,
            stripe_subscription_id,
            plan,
            subscription_status,
        ),
    )


def _apply_subscription_update(cursor, subscription, force_canceled=False):
    metadata = subscription.get("metadata") or {}
    auth0_sub = metadata.get("auth0_sub")
    signup_funnel_id = metadata.get("signup_funnel_id") or metadata.get("signupFunnelId")
    stripe_customer_id = _stripe_id(subscription.get("customer"))
    stripe_subscription_id = subscription.get("id")
    price_id = _first_subscription_price(subscription)
    mapped_plan = _plan_from_price(price_id) or _plan_from_name(metadata.get("planName"))
    status = "canceled" if force_canceled else _subscription_status(subscription.get("status"))

    user = _find_user(
        cursor,
        auth0_sub=auth0_sub,
        signup_funnel_id=signup_funnel_id,
        stripe_customer_id=stripe_customer_id,
    )
    if not user:
        return

    current_plan = user[1]
    if status == "canceled":
        next_plan = "lifetime" if current_plan == "lifetime" else "free"
    else:
        next_plan = mapped_plan or current_plan or "free"

    cursor.execute(
        """
        UPDATE users
        SET auth0_sub = COALESCE(auth0_sub, %s),
            signup_funnel_id = COALESCE(signup_funnel_id, %s),
            stripe_customer_id = COALESCE(%s, stripe_customer_id),
            stripe_subscription_id = COALESCE(%s, stripe_subscription_id),
            plan = %s,
            subscription_status = %s,
            updated_at = NOW()
        WHERE id = %s;
        """,
        (
            auth0_sub,
            signup_funnel_id,
            stripe_customer_id,
            stripe_subscription_id,
            next_plan,
            status,
            user[0],
        ),
    )


def _apply_invoice_status(cursor, invoice, status):
    stripe_customer_id = _stripe_id(invoice.get("customer"))
    stripe_subscription_id = _stripe_id(invoice.get("subscription"))
    user = _find_user(cursor, stripe_customer_id=stripe_customer_id)
    if not user:
        return

    cursor.execute(
        """
        UPDATE users
        SET stripe_subscription_id = COALESCE(%s, stripe_subscription_id),
            subscription_status = %s,
            updated_at = NOW()
        WHERE id = %s;
        """,
        (stripe_subscription_id, status, user[0]),
    )


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Stripe payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event = _to_dict(event)
    event_type = event.get("type")
    data_object = _to_dict(_nested(event, "data", "object")) or {}

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if event_type == "checkout.session.completed":
                _upsert_user_from_checkout(cursor, data_object)
            elif event_type in {
                "customer.subscription.created",
                "customer.subscription.updated",
            }:
                _apply_subscription_update(cursor, data_object)
            elif event_type == "customer.subscription.deleted":
                _apply_subscription_update(cursor, data_object, force_canceled=True)
            elif event_type == "invoice.payment_failed":
                _apply_invoice_status(cursor, data_object, "past_due")
            elif event_type in {"invoice.payment_succeeded", "customer.subscription.resumed"}:
                _apply_invoice_status(cursor, data_object, "active")

            conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()

    return {"received": True}
