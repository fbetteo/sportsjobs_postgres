from fastapi import APIRouter, HTTPException, Request
import os
from database.connection import get_db_connection
from typing import Optional, List
from datetime import datetime, timezone
from models.schemas import GetBlog, AddBlog, WebhookPayload

router = APIRouter()


@router.post("/blog")
async def get_blogposts(query_options: GetBlog, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = query_options.model_dump()
        # Base query
        query = "SELECT * FROM blog WHERE 1=1"
        params = []

        # Add filters if they exist
        if query_options.filters:
            for key, value in query_options.filters.items():
                if value:
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
        blogposts = cur.fetchall()

        # Get column names
        columns = [desc[0] for desc in cur.description]

        # Convert to list of dictionaries
        result = []
        for post in blogposts:
            post_dict = {columns[i]: value for i, value in enumerate(post)}
            # Format the response similar to Airtable format
            result.append(
                # "id": job_dict["job_id"],
                # "fields":
                post_dict
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


@router.post("/add_blog")
async def post_blog(blog_data: AddBlog, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO blog (
                    title,
                    content,
                    content_image,
                    cover,
                    short_description,
                    creation_date,
                    last_modified,
                    post_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING blog_id;
            """

            values = (
                blog_data.title,
                blog_data.content,
                blog_data.content_image,
                blog_data.cover,
                blog_data.short_description,
                blog_data.creation_date,
                blog_data.last_modified,
                blog_data.post_date,
            )

            cursor.execute(insert_query, values)
            blog_id = cursor.fetchone()[0]
            conn.commit()

            return {"message": "Blog post created successfully", "blog_id": blog_id}

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


@router.post("/webhook")
async def blog_webhook(webhook_payload: WebhookPayload, request: Request):
    """
    Webhook endpoint to receive published articles and insert them into the blog table.
    Uses Bearer token authentication with WEBHOOK_ACCESS_TOKEN environment variable.
    """
    # Validate access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid access token")

    token = auth_header.split(" ")[1]
    expected_token = os.getenv('OUTRANK_HEADER_AUTHORIZATION')
    if not expected_token or token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid access token")

    # Validate event type
    if webhook_payload.event_type != "publish_articles":
        raise HTTPException(status_code=400, detail="Unsupported event type")

    try:
        conn = get_db_connection()
        inserted_articles = []

        with conn.cursor() as cursor:
            for article in webhook_payload.data.articles:
                # Parse the created_at timestamp
                try:
                    created_at = datetime.fromisoformat(
                        article.created_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    # Fallback to current time if parsing fails
                    created_at = datetime.now(timezone.utc)

                insert_query = """
                    INSERT INTO blog (
                        title,
                        content,
                        content_image,
                        cover,
                        short_description,
                        creation_date,
                        last_modified,
                        post_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING blog_id;
                """

                values = (
                    article.title,
                    article.content_markdown,  # Using content_markdown for content
                    None,  # content_image not provided in webhook
                    article.image_url,  # Using image_url for cover
                    article.meta_description,  # Using meta_description for short_description
                    created_at,  # Using created_at from webhook
                    datetime.now(timezone.utc),  # Current time for last_modified
                    created_at.date(),  # Using created_at date for post_date
                )

                cursor.execute(insert_query, values)
                blog_id = cursor.fetchone()[0]

                inserted_articles.append(
                    {
                        "blog_id": blog_id,
                        "original_id": article.id,
                        "title": article.title,
                        "slug": article.slug,
                    }
                )

        conn.commit()

        return {
            "message": "Webhook processed successfully",
            "event_type": webhook_payload.event_type,
            "processed_articles": len(inserted_articles),
            "articles": inserted_articles,
        }

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error processing webhook: {str(e)}"
        )

    finally:
        if conn:
            conn.close()
