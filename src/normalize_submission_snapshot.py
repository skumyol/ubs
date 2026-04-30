#!/usr/bin/env python3
"""Normalize generated datasets to the active Dongfang/Sungrow submission snapshot.

This script does not rerun collection or classification. It reconciles the
final processed CSVs against the current paragraph dataset so final-facing
artifacts are built from one coherent snapshot.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pair_config import SHORT_LEG


ROOT = Path("/Users/skumyol/Documents/GitHub/ubs")
DATA = ROOT / "data" / "processed"


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _normalize_sector(value: str) -> str:
    text = str(value or "").strip()
    if text == "Oilfield Services":
        return SHORT_LEG.sector
    return text


def main() -> None:
    paragraph_path = DATA / "paragraph_level_dataset.csv"
    classified_path = DATA / "classified_paragraphs.csv"
    document_index_path = DATA / "document_index.csv"

    paragraphs = _read(paragraph_path)
    classified = _read(classified_path)
    index_df = _read(document_index_path)

    if paragraphs.empty or classified.empty:
        raise SystemExit("Paragraph and classified datasets must exist before normalization.")

    paragraphs["sector"] = paragraphs["sector"].map(_normalize_sector)
    if "theme" in paragraphs.columns:
        paragraphs["theme"] = paragraphs["theme"].replace(
            {"Jereh Financials": "Sungrow Financials"}
        )

    current_ids = set(paragraphs["paragraph_id"].astype(str))
    classified = classified[classified["paragraph_id"].astype(str).isin(current_ids)].copy()

    join_cols = [
        c for c in [
            "paragraph_id",
            "doc_id",
            "source_name",
            "title",
            "company",
            "sector",
            "document_type",
            "theme",
            "source_method",
            "url",
            "date",
            "text",
            "char_count",
        ] if c in paragraphs.columns
    ]
    base = paragraphs[join_cols].copy()

    meta_cols = [c for c in join_cols if c != "paragraph_id"]
    classified = classified.drop(columns=[c for c in meta_cols if c in classified.columns], errors="ignore")
    classified = classified.merge(base, on="paragraph_id", how="left")
    classified["sector"] = classified["sector"].map(_normalize_sector)
    if "theme" in classified.columns:
        classified["theme"] = classified["theme"].replace(
            {"Jereh Financials": "Sungrow Financials"}
        )

    if not index_df.empty:
        index_df["sector"] = index_df["sector"].map(_normalize_sector)
        if "theme" in index_df.columns:
            index_df["theme"] = index_df["theme"].replace(
                {"Jereh Financials": "Sungrow Financials"}
            )
        index_df.to_csv(document_index_path, index=False)

    paragraphs.to_csv(paragraph_path, index=False)
    classified.to_csv(classified_path, index=False)

    print(f"[SAVED] {paragraph_path}")
    print(f"[SAVED] {classified_path}")
    print(f"[SAVED] {document_index_path}")
    print(f"[INFO] Normalized classified rows: {len(classified)}")


if __name__ == "__main__":
    main()
