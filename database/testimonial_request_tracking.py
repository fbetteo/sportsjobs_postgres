"""Add a per-user timestamp for the one-time testimonial request."""

from pathlib import Path

from dotenv import load_dotenv

from connection import get_db_connection


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS testimonial_request_sent_at TIMESTAMPTZ"
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
