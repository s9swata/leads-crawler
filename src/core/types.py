"""Lead schema with validation."""

import re
from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    model_validator,
)


class Lead(BaseModel):
    """Lead data schema with validation."""

    id: str
    company_name: str
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    address: Optional[str] = None
    business_category: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    discovered_at: datetime = datetime.utcnow()
    scraped_at: Optional[datetime] = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source is in allowed values."""
        allowed = ["search", "scrape", "manual", "batch"]
        if v not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format and add https:// if missing."""
        if v is None:
            return v
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # port
            r"(?:/[^\s]*)?$",  # path
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    @field_validator("linkedin")
    @classmethod
    def validate_linkedin(cls, v: Optional[str]) -> Optional[str]:
        """Validate LinkedIn URL contains linkedin.com domain."""
        if v is None:
            return v
        v = v.strip()
        if "linkedin.com" not in v.lower():
            raise ValueError("linkedin must be a LinkedIn URL")
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        """Normalize phone to digits only."""
        if v is None:
            return v
        return re.sub(r"\D", "", v)

    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_contact(cls, values: dict) -> dict:
        """Ensure at least one contact method exists."""
        if not any(
            values.get(field) for field in ["email", "website", "phone", "linkedin"]
        ):
            raise ValueError(
                "At least one contact method (email, website, phone, or linkedin) is required"
            )
        return values

    class Config:
        """Pydantic model config."""

        json_schema_extra = {
            "example": {
                "id": "lead-123",
                "company_name": "Acme Corp",
                "email": "contact@acme.com",
                "website": "https://acme.com",
                "phone": "+1234567890",
                "linkedin": "https://linkedin.com/company/acme",
                "source": "search",
                "source_url": "https://search.example.com/results",
            }
        }
