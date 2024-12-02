# from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
# import psycopg2
# from psycopg2 import sql
# from pydantic import BaseModel, Field
# import os
from dotenv import load_dotenv
# from datetime import datetime, timezone
from endpoints import health, users, alerts, jobs
# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()


# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(alerts.router)
app.include_router(jobs.router)
# # Database connection setup
# def get_db_connection():
#     return psycopg2.connect(
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         host=os.getenv("DB_HOST"),
#         port=5432  # Default PostgreSQL port
#     )


# @app.get("/health")
# async def health_check():
#     return {"status": "API is running"}


# @app.get("/db-health")
# async def db_health_check():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute('SELECT 1')
#         cursor.fetchone()
#         return {
#             "status": "healthy",
#             "database": "connected",
#             "details": {
#                 "host": os.getenv("DB_HOST"),
#                 "database": os.getenv("DB_NAME"),
#                 "port": 5432
#             }
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=503,
#             detail=f"Database connection failed: {str(e)}"
#         )
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()    

# Pydantic model for request body
# class AddUser(BaseModel):
#     name: str
#     email: str
#     plan: str
#     creation_date: datetime =  Field(default_factory=lambda: datetime.now(timezone.utc))

# class AddAlert(BaseModel):
#     name: str = Field(default="")
#     email: str = Field(default="")
#     country: Optional[List[str]] = Field(default_factory=list)
#     seniority: Optional[List[str]] = Field(default_factory=list)
#     sport_list: Optional[List[str]] = Field(default_factory=list)
#     skills: Optional[List[str]] = Field(default_factory=list)
#     remote_office: Optional[List[str]] = Field(default_factory=list)
#     hours: Optional[List[str]] = Field(default_factory=list)

# @app.post("/add_user")
# async def add_user(record: AddUser, request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
#         raise HTTPException(status_code=403, detail="Unauthorized")
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Example query to update a user's plan based on email
#         data = record.model_dump()
#         query = sql.SQL("INSERT INTO users (name, email, plan, creation_date) VALUES ({}) RETURNING *").format(
#             sql.SQL(", ").join(sql.Placeholder() * len(data))
#             )
#         print(query.as_string(conn))
#         # Execute the query with values as parameters
#         cursor.execute(query, tuple(data.values()))

#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Record not found")

#         created_record = cursor.fetchone()
#         conn.commit()

#         return {"message": "Usert  created successfully", "record": created_record}

#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         cursor.close()
#         conn.close()



# @app.post("/add_alert")
# async def add_alert(record: AddAlert, request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or auth_header != f"Bearer {os.getenv('HEADER_AUTHORIZATION')}":
#         raise HTTPException(status_code=403, detail="Unauthorized")
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Example query to update a user's plan based on email
#         data = record.model_dump()
#         query = sql.SQL("INSERT INTO alerts (name, email, country, seniority, sport_list, skills, remote_office, hours)  VALUES ({}) RETURNING *").format(
#             sql.SQL(", ").join(sql.Placeholder() * len(data))
#             )
#         print(query.as_string(conn))
#         # Execute the query with values as parameters
#         cursor.execute(query, tuple(data.values()))

#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Record not found")

#         created_record = cursor.fetchone()
#         conn.commit()

#         return {"message": "Alert created successfully", "record": created_record}

#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         cursor.close()
#         conn.close()

