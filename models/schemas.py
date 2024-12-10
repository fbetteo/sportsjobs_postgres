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