"""Query builder for filtering and sorting leads."""

from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.storage.models import Lead as LeadModel


def build_leads_query(
    session: Session,
    has_email: Optional[bool] = None,
    has_phone: Optional[bool] = None,
    has_website: Optional[bool] = None,
    source: Optional[str] = None,
    sort_by: str = "discovered_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
) -> list:
    """Build and execute a query with filters, sorting, and pagination.

    Args:
        session: SQLAlchemy session
        has_email: Filter by email presence
        has_phone: Filter by phone presence
        has_website: Filter by website presence
        source: Filter by source
        sort_by: Field to sort by (discovered_at, source, company_name, scraped_at)
        sort_order: Sort order (asc, desc)
        limit: Number of results
        offset: Offset for pagination

    Returns:
        List of Lead objects
    """
    conditions = []

    if has_email is not None:
        if has_email:
            conditions.append(LeadModel.email.isnot(None))
        else:
            conditions.append(LeadModel.email.is_(None))

    if has_phone is not None:
        if has_phone:
            conditions.append(LeadModel.phone.isnot(None))
        else:
            conditions.append(LeadModel.phone.is_(None))

    if has_website is not None:
        if has_website:
            conditions.append(LeadModel.website.isnot(None))
        else:
            conditions.append(LeadModel.website.is_(None))

    if source:
        conditions.append(LeadModel.source == source)

    stmt = select(LeadModel)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    sort_column = getattr(LeadModel, sort_by, LeadModel.discovered_at)
    if sort_order.lower() == "desc":
        stmt = stmt.order_by(sort_column.desc())
    else:
        stmt = stmt.order_by(sort_column.asc())

    stmt = stmt.limit(limit).offset(offset)

    results = session.execute(stmt).scalars().all()

    from src.core.types import Lead

    return [
        Lead(
            id=row.id,
            company_name=row.company_name,
            email=row.email,
            website=row.website,
            phone=row.phone,
            linkedin=row.linkedin,
            source=row.source,
            source_url=row.source_url,
            discovered_at=row.discovered_at,
            scraped_at=row.scraped_at,
        )
        for row in results
    ]
