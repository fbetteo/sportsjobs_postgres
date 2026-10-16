import asyncio
import sqlite3
import unittest
from unittest.mock import patch

from starlette.requests import Request

from endpoints.jobs import get_jobs
from models.schemas import GetJob


class SqliteCursor:
    """Runs the endpoint's psycopg2-style SQL against an in-memory SQLite table."""

    def __init__(self, conn):
        self.cursor = conn.cursor()

    def execute(self, query, params):
        self.cursor.execute(query.replace("%s", "?"), params)

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def description(self):
        return self.cursor.description

    def close(self):
        pass


class SqliteConnection:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            """CREATE TABLE jobs (
                job_id INTEGER, slug TEXT, name TEXT, creation_date TEXT, company TEXT,
                location TEXT, salary TEXT, country TEXT, seniority TEXT, remote INTEGER,
                remote_office TEXT, sport_list TEXT, job_area TEXT,
                logo_permanent_url TEXT, description TEXT, url TEXT
            )"""
        )

    def add_job(self, job_id, creation_date, company="Acme"):
        self.conn.execute(
            "INSERT INTO jobs (job_id, name, creation_date, company, description, url)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, f"Job {job_id}", creation_date, company, "long text", "https://apply"),
        )

    def cursor(self):
        return SqliteCursor(self.conn)

    def close(self):
        pass


def fetch_jobs(conn, **options):
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer test-token")]})
    with patch.dict("os.environ", {"HEADER_AUTHORIZATION": "test-token"}), patch(
        "endpoints.jobs.get_db_connection", return_value=conn
    ):
        return asyncio.run(get_jobs(GetJob(**options), request))


class GetJobsPaginationTests(unittest.TestCase):
    def test_pages_cover_every_job_once_when_creation_dates_tie(self):
        conn = SqliteConnection()
        for job_id in range(1, 8):
            conn.add_job(job_id, "2026-10-01")  # Bulk insert: identical timestamps.

        pages = [fetch_jobs(conn, limit=3, offset=offset) for offset in (0, 3, 6)]

        self.assertEqual(
            [[job["job_id"] for job in page] for page in pages],
            [[7, 6, 5], [4, 3, 2], [1]],
        )

    def test_offset_applies_after_filters(self):
        conn = SqliteConnection()
        conn.add_job(1, "2026-10-01", company="Acme")
        conn.add_job(2, "2026-10-02", company="Other")
        conn.add_job(3, "2026-10-03", company="Acme")

        jobs = fetch_jobs(conn, limit=10, offset=1, filters={"company": "acme"})

        self.assertEqual([job["job_id"] for job in jobs], [1])

    def test_list_fields_only_omits_description_and_apply_url(self):
        conn = SqliteConnection()
        conn.add_job(1, "2026-10-01")

        [list_job] = fetch_jobs(conn, limit=1, list_fields_only=True)
        [full_job] = fetch_jobs(conn, limit=1)

        self.assertEqual(list_job["name"], "Job 1")
        self.assertNotIn("description", list_job)
        self.assertNotIn("url", list_job)
        self.assertEqual(full_job["description"], "long text")
        self.assertEqual(full_job["url"], "https://apply")


if __name__ == "__main__":
    unittest.main()
