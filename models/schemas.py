from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional

class AddUser(BaseModel):
    name: str
    email: str
    plan: str
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AddAlert(BaseModel):
    name: str = Field(default="")
    email: str = Field(default="")
    country: Optional[List[str]] = Field(default_factory=list)
    seniority: Optional[List[str]] = Field(default_factory=list)
    sport_list: Optional[List[str]] = Field(default_factory=list)
    skills: Optional[List[str]] = Field(default_factory=list)
    remote_office: Optional[List[str]] = Field(default_factory=list)
    hours: Optional[List[str]] = Field(default_factory=list)

class AddJob(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    seniority: Optional[str] = None
    description: Optional[str] = None
    sport_list: Optional[str] = None
    skills: Optional[List[str]] = None
    remote_office: Optional[str] = None
    salary: Optional[str] = None
    language: Optional[List[str]] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    hours: Optional[str] = None
    featured: Optional[str] = "1 - regular"
    logo_permanent_url: Optional[str] = "https://cdn.sportsjobs.online/blogposts/images/sportsjobs_logo.png"
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GetJob(BaseModel):
    limit: Optional[int] = 100,
    filters: Optional[dict] = None
    sort_by: str = "creation_date"
    sort_direction: str = "desc"

class GetBlog(BaseModel):
    limit: Optional[int] = 100,
    filters: Optional[dict] = None
    sort_by: str = "creation_date"
    sort_direction: str = "desc"

class GetCompanies(BaseModel):
    limit: Optional[int] = 100,