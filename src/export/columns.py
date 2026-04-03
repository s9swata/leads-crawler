"""Column definitions for CSV export."""

from enum import Enum


class LeadColumns(Enum):
    """Available columns for CSV export."""

    ID = "id"
    COMPANY_NAME = "company_name"
    EMAIL = "email"
    WEBSITE = "website"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    SOURCE = "source"
    SOURCE_URL = "source_url"
    DISCOVERED_AT = "discovered_at"
    SCRAPED_AT = "scraped_at"


COLUMN_MAPPING = {
    "id": "id",
    "company": "company_name",
    "company_name": "company_name",
    "email": "email",
    "website": "website",
    "url": "website",
    "phone": "phone",
    "telephone": "phone",
    "linkedin": "linkedin",
    "source": "source",
    "source_url": "source_url",
    "url_found": "source_url",
    "discovered": "discovered_at",
    "discovered_at": "discovered_at",
    "scraped": "scraped_at",
    "scraped_at": "scraped_at",
}


AVAILABLE_COLUMNS = [col.value for col in LeadColumns]


DEFAULT_COLUMNS = [
    "company_name",
    "email",
    "website",
    "phone",
    "source",
    "discovered_at",
]


def normalize_columns(columns: list[str]) -> list[str]:
    """Normalize column names to internal field names.

    Args:
        columns: List of column names (friendly or internal)

    Returns:
        List of normalized internal field names
    """
    normalized = []
    for col in columns:
        col_lower = col.lower().strip()
        if col_lower in COLUMN_MAPPING:
            normalized.append(COLUMN_MAPPING[col_lower])
        else:
            normalized.append(col_lower)
    return normalized
