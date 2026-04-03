"""CSV export functionality."""

import csv
from typing import Optional

from src.export.columns import (
    DEFAULT_COLUMNS,
    AVAILABLE_COLUMNS,
    normalize_columns,
)
from src.core.types import Lead


def export_csv(
    leads: list[Lead],
    path: str,
    columns: Optional[list[str]] = None,
) -> int:
    """Export leads to CSV file.

    Args:
        leads: List of Lead objects to export
        path: Output CSV file path
        columns: List of column names to export (default: DEFAULT_COLUMNS)

    Returns:
        Number of rows exported
    """
    if not leads:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([])
        return 0

    selected_columns = columns if columns else DEFAULT_COLUMNS

    normalized_cols = normalize_columns(selected_columns)

    for col in normalized_cols:
        if col not in AVAILABLE_COLUMNS:
            raise ValueError(f"Unknown column: {col}")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=normalized_cols, extrasaction="ignore")
        writer.writeheader()

        for lead in leads:
            row = {}
            for col in normalized_cols:
                value = getattr(lead, col, None)
                if value is not None:
                    if hasattr(value, "isoformat"):
                        row[col] = value.isoformat()
                    else:
                        row[col] = str(value)
                else:
                    row[col] = ""
            writer.writerow(row)

    return len(leads)
