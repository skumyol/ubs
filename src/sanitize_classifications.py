#!/usr/bin/env python3
"""Sanitize classified paragraphs against rebuilt paragraph dataset.

- Removes classifications whose paragraph_id no longer exists
- Refreshes date from paragraph dataset (source of truth)
- Drops rows with invalid dates
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import CLASSIFIED_PARAGRAPHS_PATH, PARAGRAPH_DATASET_PATH


MIN_VALID_YEAR = 2018


def sanitize_classifications() -> dict:
    if not PARAGRAPH_DATASET_PATH.exists() or not CLASSIFIED_PARAGRAPHS_PATH.exists():
        return {
            "status": "skipped",
            "reason": "missing input files",
        }

    paragraphs = pd.read_csv(PARAGRAPH_DATASET_PATH)
    classified = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)

    before = len(classified)

    if "paragraph_id" not in paragraphs.columns or "paragraph_id" not in classified.columns:
        return {
            "status": "skipped",
            "reason": "missing paragraph_id",
        }

    # Filter out future/current year dates (data integrity)
    current_year = datetime.now().year
    max_allowed_date = f"{current_year - 1}-12-31"  # Only last year and earlier
    classified = classified[classified["date"] <= max_allowed_date]

    valid_ids = set(paragraphs["paragraph_id"].astype(str).tolist())
    id_mask = classified["paragraph_id"].astype(str).isin(valid_ids)
    retained_ratio = float(id_mask.mean()) if len(id_mask) > 0 else 1.0

    # Safety guard: if ID drift is too large after a rebuild, avoid mass deletion.
    if retained_ratio >= 0.80:
        classified = classified[id_mask].copy()

    date_map = paragraphs.set_index("paragraph_id")["date"].to_dict() if "date" in paragraphs.columns else {}
    if date_map:
        mapped = classified["paragraph_id"].map(date_map)
        classified["date"] = mapped.fillna(classified.get("date"))

    # Fallback date refresh by doc_id for rows not found by paragraph_id
    if "doc_id" in paragraphs.columns and "doc_id" in classified.columns and "date" in paragraphs.columns:
        doc_date_map = paragraphs.groupby("doc_id")["date"].first().to_dict()
        missing_date = classified["date"].isna() if "date" in classified.columns else pd.Series([True] * len(classified))
        classified.loc[missing_date, "date"] = classified.loc[missing_date, "doc_id"].map(doc_date_map)

    parsed = pd.to_datetime(classified.get("date", pd.Series(dtype="object")), errors="coerce")
    min_date = pd.Timestamp(f"{MIN_VALID_YEAR}-01-01")
    max_date = pd.Timestamp.now().normalize() + pd.Timedelta(days=366)
    valid_date_mask = parsed.notna() & (parsed >= min_date) & (parsed <= max_date)
    classified = classified[valid_date_mask].copy()
    classified["date"] = pd.to_datetime(classified["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    classified = classified.drop_duplicates(subset=["paragraph_id"], keep="last")
    classified.to_csv(CLASSIFIED_PARAGRAPHS_PATH, index=False)

    after = len(classified)
    return {
        "status": "ok",
        "before_rows": before,
        "after_rows": after,
        "removed_rows": before - after,
        "id_retained_ratio": round(retained_ratio, 3),
        "unique_dates": int(classified["date"].nunique()) if "date" in classified.columns else 0,
    }


if __name__ == "__main__":
    summary = sanitize_classifications()
    print("=" * 60)
    print("CLASSIFICATION SANITIZATION")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k}: {v}")
