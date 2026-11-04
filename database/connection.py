import psycopg2
import os

from opentelemetry.instrumentation.dbapi import instrument_connection


def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=5432
    )
    # Wrapping the connection traces every cursor, including ones opened with
    # cursor_factory=RealDictCursor, which the psycopg2 instrumentor skips.
    return instrument_connection("psycopg2", conn, database_system="postgresql")