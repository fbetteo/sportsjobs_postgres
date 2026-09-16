from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional


class AddUser(BaseModel):
    name: str
    email: str
    plan: str
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnsureUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)
    email: str = Field(..., min_length=1)
    name: Optional[str] = None
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")
    stripe_checkout_session_id: Optional[str] = Field(
        default=None, alias="stripeCheckoutSessionId"
    )
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    signup_funnel_answers_json: Optional[Dict[str, Any]] = Field(
        default=None, alias="signupFunnelAnswers"
    )
    signup_funnel_completed_at: Optional[datetime] = Field(
        default=None, alias="signupFunnelCompletedAt"
    )
    paid_product_acknowledged_at: Optional[datetime] = Field(
        default=None, alias="paidProductAcknowledgedAt"
    )


class SignupFunnel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    email: str = Field(..., min_length=1)
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")
    source: Optional[str] = None
    onboarding: "OnboardingAnswers"


class PaidProductAcknowledgement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(..., min_length=1)
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")
    paid_product_acknowledged_at: datetime = Field(
        ..., alias="paidProductAcknowledgedAt"
    )


class CheckoutSync(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., alias="sessionId", min_length=1)
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")


class SignupFunnelClaim(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")
    email: Optional[str] = None
    name: Optional[str] = None
    final_email: Optional[str] = Field(default=None, alias="finalEmail")
    final_name: Optional[str] = Field(default=None, alias="finalName")
    checkout_email: Optional[str] = Field(default=None, alias="checkoutEmail")
    stripe_customer_id: Optional[str] = Field(default=None, alias="stripeCustomerId")
    stripe_subscription_id: Optional[str] = Field(
        default=None, alias="stripeSubscriptionId"
    )


SPORTS_INTEREST_IDS = {
    "football",
    "soccer",
    "basketball",
    "hockey",
    "baseball",
    "tennis",
    "golf",
    "formula_1",
    "betting_fantasy",
    "esports",
}

JOB_SEARCH_DURATION_IDS = {
    "just_started",
    "few_weeks",
    "few_months",
    "feels_like_forever",
}

HARDEST_PART_IDS = {
    "not_hearing_back",
    "not_getting_interviews",
    "too_much_competition",
    "not_enough_jobs",
    "lack_of_great_offers",
}

ROLE_INTEREST_IDS = {
    "data_analyst",
    "data_scientist",
    "data_engineer",
    "business_intelligence",
    "analytics_engineer",
    "software_engineer",
    "machine_learning_ai",
    "product_analyst",
    "quant_betting_analyst",
    "internship",
}


class OnboardingAnswers(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sports_interests: List[str] = Field(..., alias="sportsInterests", min_length=1)
    job_search_duration: str = Field(..., alias="jobSearchDuration", min_length=1)
    hardest_part: str = Field(..., alias="hardestPart", min_length=1)
    country: Optional[str] = None
    role_interests: List[str] = Field(..., alias="roleInterests")
    role_unsure: bool = Field(..., alias="roleUnsure")

    @field_validator("sports_interests")
    @classmethod
    def validate_sports_interests(cls, value):
        invalid_values = sorted(set(value) - SPORTS_INTEREST_IDS)
        if invalid_values:
            raise ValueError(f"Invalid sportsInterests values: {invalid_values}")
        return value

    @field_validator("job_search_duration")
    @classmethod
    def validate_job_search_duration(cls, value):
        if value not in JOB_SEARCH_DURATION_IDS:
            raise ValueError("Invalid jobSearchDuration value")
        return value

    @field_validator("hardest_part")
    @classmethod
    def validate_hardest_part(cls, value):
        if value not in HARDEST_PART_IDS:
            raise ValueError("Invalid hardestPart value")
        return value

    @field_validator("role_interests")
    @classmethod
    def validate_role_interests(cls, value):
        invalid_values = sorted(set(value) - ROLE_INTEREST_IDS)
        if invalid_values:
            raise ValueError(f"Invalid roleInterests values: {invalid_values}")
        return value

    @model_validator(mode="after")
    def validate_role_choice(self):
        if not self.role_unsure and not self.role_interests:
            raise ValueError("roleInterests can be empty only when roleUnsure is true")
        return self


class OnboardingUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)
    onboarding: OnboardingAnswers


class LinkedinUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)
    linkedin_url: Optional[str] = Field(default=None, alias="linkedinUrl", max_length=500)

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value):
        if value is None or not value.strip():
            return None
        from urllib.parse import urlparse

        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in {"linkedin.com", "www.linkedin.com"}:
            raise ValueError("Enter a LinkedIn https:// URL")
        return value


class CvUploadRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)
    s3_key: str = Field(..., alias="s3Key", min_length=1)
    filename: str = Field(..., min_length=1, max_length=255)
    size_bytes: int = Field(..., alias="sizeBytes", gt=0, le=5 * 1024 * 1024)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub")
    email: str
    name: Optional[str] = None
    signup_funnel_id: Optional[str] = Field(default=None, alias="signupFunnelId")
    stripe_checkout_session_id: Optional[str] = Field(
        default=None, alias="stripeCheckoutSessionId"
    )
    plan: str
    subscription_status: str = Field(..., alias="subscriptionStatus")
    onboarding_completed_at: Optional[datetime] = Field(
        default=None, alias="onboardingCompletedAt"
    )
    onboarding: Dict[str, Any] = Field(default_factory=dict)
    signup_funnel_answers: Optional[Dict[str, Any]] = Field(
        default=None, alias="signupFunnelAnswers"
    )
    signup_funnel_completed_at: Optional[datetime] = Field(
        default=None, alias="signupFunnelCompletedAt"
    )
    paid_product_acknowledged_at: Optional[datetime] = Field(
        default=None, alias="paidProductAcknowledgedAt"
    )


class AddAlert(BaseModel):
    name: str = Field(default="")
    email: str = Field(default="")
    country: Optional[List[str]] = Field(default_factory=list)
    seniority: Optional[List[str]] = Field(default_factory=list)
    sport_list: Optional[List[str]] = Field(default_factory=list)
    skills: Optional[List[str]] = Field(default_factory=list)
    remote_office: Optional[List[str]] = Field(default_factory=list)
    hours: Optional[List[str]] = Field(default_factory=list)
    industry: Optional[List[str]] = Field(default_factory=list)
    type: Optional[List[str]] = Field(default_factory=list)
    job_area: Optional[List[str]] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_alert_name(cls, value):
        return str(value or "").strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_alert_email(cls, value):
        return str(value or "").strip().casefold()

    @field_validator(
        "country",
        "seniority",
        "sport_list",
        "skills",
        "remote_office",
        "hours",
        "industry",
        "type",
        "job_area",
        mode="before",
    )
    @classmethod
    def normalize_alert_filters(cls, value):
        if value is None:
            return []
        values = value if isinstance(value, (list, tuple, set)) else [value]
        unique_values = {}
        for item in values:
            cleaned = str(item or "").strip()
            if cleaned:
                unique_values.setdefault(cleaned.casefold(), cleaned)
        return sorted(unique_values.values(), key=str.casefold)


class CreateAlert(AddAlert):
    model_config = ConfigDict(populate_by_name=True)

    auth0_sub: str = Field(..., alias="auth0Sub", min_length=1)


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


class PublishPendingJob(BaseModel):
    stripe_session_id: str


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


class AddTestimonial(BaseModel):
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    content: str
    avatar_url: Optional[str] = None
    rating: Optional[int] = None  # 1-5


class ApproveTestimonial(BaseModel):
    approved: bool = True


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
