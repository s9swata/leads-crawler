"""Lead repository for CRUD operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.models import Lead as LeadModel


class LeadRepository:
    """Repository for lead CRUD operations."""

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        self._session = session

    def add(self, lead: "Lead") -> "Lead":
        """Insert a lead and return with database ID."""
        model = self._lead_to_model(lead)
        self._session.add(model)
        self._session.flush()
        return self._row_to_lead(model)

    def find_by_email(self, email: str) -> Optional["Lead"]:
        """Find a lead by email address."""
        stmt = select(LeadModel).where(LeadModel.email == email.lower())
        result = self._session.execute(stmt).scalar_one_or_none()
        return self._row_to_lead(result) if result else None

    def find_by_website(self, url: str) -> Optional["Lead"]:
        """Find a lead by website URL (exact domain match)."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = (parsed.netloc or parsed.path).lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Find leads with matching domain in website field
        stmt = select(LeadModel).where(LeadModel.website.isnot(None))
        results = self._session.execute(stmt).scalars().all()

        for lead in results:
            if lead.website:
                lead_parsed = urlparse(lead.website)
                lead_domain = (lead_parsed.netloc or lead_parsed.path).lower()
                if lead_domain.startswith("www."):
                    lead_domain = lead_domain[4:]
                if lead_domain == domain:
                    return self._row_to_lead(lead)
        return None

    def list_all(self, limit: int = 100, offset: int = 0) -> list["Lead"]:
        """List all leads with pagination."""
        stmt = (
            select(LeadModel)
            .order_by(LeadModel.discovered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        results = self._session.execute(stmt).scalars().all()
        return [self._row_to_lead(r) for r in results]

    def count(self) -> int:
        """Get total lead count."""
        stmt = select(LeadModel)
        return len(self._session.execute(stmt).scalars().all())

    def _lead_to_model(self, lead: "Lead") -> LeadModel:
        """Convert Pydantic Lead to SQLAlchemy model."""
        return LeadModel(
            id=lead.id,
            company_name=lead.company_name,
            email=lead.email.lower() if lead.email else None,
            website=lead.website,
            phone=lead.phone,
            linkedin=lead.linkedin,
            address=lead.address,
            business_category=lead.business_category,
            source=lead.source,
            source_url=lead.source_url,
            discovered_at=lead.discovered_at,
            scraped_at=lead.scraped_at,
        )

    def _row_to_lead(self, row: Optional[LeadModel]) -> Optional["Lead"]:
        """Convert SQLAlchemy row to Pydantic Lead."""
        if row is None:
            return None

        from src.core.types import Lead

        return Lead(
            id=row.id,
            company_name=row.company_name,
            email=row.email,
            website=row.website,
            phone=row.phone,
            linkedin=row.linkedin,
            address=row.address,
            business_category=row.business_category,
            source=row.source,
            source_url=row.source_url,
            discovered_at=row.discovered_at,
            scraped_at=row.scraped_at,
        )
