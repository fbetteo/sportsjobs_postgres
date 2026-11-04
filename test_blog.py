import sqlite3
import unittest
from unittest.mock import patch

from starlette.requests import Request

from endpoints.blog import get_blogposts
from models.schemas import GetBlog


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
            """CREATE TABLE blog (
                blog_id INTEGER, airtable_id TEXT, title TEXT, content TEXT,
                content_image TEXT, short_description TEXT, cover TEXT,
                creation_date TEXT, last_modified TEXT, post_date TEXT
            )"""
        )
        self.conn.execute(
            "INSERT INTO blog (blog_id, title, content, short_description, creation_date)"
            " VALUES (1, 'Post', 'long article', 'Short summary', '2026-01-01')"
        )

    def cursor(self):
        return SqliteCursor(self.conn)

    def close(self):
        pass


def fetch_blogposts(**options):
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer test-token")]})
    with patch.dict("os.environ", {"HEADER_AUTHORIZATION": "test-token"}), patch(
        "endpoints.blog.get_db_connection", return_value=SqliteConnection()
    ):
        return get_blogposts(GetBlog(limit=10, **options), request)


class BlogListTests(unittest.TestCase):
    def test_list_fields_only_omits_content(self):
        [post] = fetch_blogposts(list_fields_only=True)

        self.assertNotIn("content", post)
        self.assertEqual(post["title"], "Post")
        self.assertEqual(post["short_description"], "Short summary")

    def test_default_returns_full_post(self):
        [post] = fetch_blogposts()

        self.assertEqual(post["content"], "long article")


if __name__ == "__main__":
    unittest.main()
