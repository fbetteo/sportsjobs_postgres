from pydantic import BaseModel, Field
from datetime import datetime, timezone, date
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


class AddBlog(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_image: Optional[str] = None
    cover: Optional[str] = None
    short_description: Optional[str] = None
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    post_date: Optional[date] = Field(
        default_factory=lambda: datetime.now(timezone.utc).date()
    )


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
    logo_permanent_url: Optional[str] = (
        "https://cdn.sportsjobs.online/blogposts/images/sportsjobs_logo.png"
    )
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    slug: Optional[str] = None


class GetJob(BaseModel):
    limit: Optional[int] = (100,)
    filters: Optional[dict] = None
    sort_by: str = "creation_date"
    sort_direction: str = "desc"


class GetBlog(BaseModel):
    limit: Optional[int] = (100,)
    filters: Optional[dict] = None
    sort_by: str = "creation_date"
    sort_direction: str = "desc"


class AddNewsletterSignup(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = None


class GetCompanies(BaseModel):
    limit: Optional[int] = (100,)


# Webhook schemas
class WebhookArticle(BaseModel):
    id: str
    title: str
    content_markdown: str
    content_html: str
    meta_description: str
    created_at: str
    image_url: Optional[str] = None
    slug: str
    tags: List[str]


class WebhookData(BaseModel):
    articles: List[WebhookArticle]


class WebhookPayload(BaseModel):
    event_type: str
    timestamp: str
    data: WebhookData
