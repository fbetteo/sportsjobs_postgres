from fastapi import APIRouter, HTTPException, Request
import os
from database.connection import get_db_connection
from typing import Optional, List
from datetime import datetime
from models.schemas import GetBlog, AddBlog

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
