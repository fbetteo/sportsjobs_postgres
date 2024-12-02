from fastapi import APIRouter, HTTPException
import os
from database.connection import get_db_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "API is running"}


@router.get("/db-health")
async def db_health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        return {
            "status": "healthy",
            "database": "connected",
            "details": {
                "host": os.getenv("DB_HOST"),
                "database": os.getenv("DB_NAME"),
                "port": 5432
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()   