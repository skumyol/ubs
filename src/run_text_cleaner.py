"""Build paragraph-level dataset from document index."""

import pandas as pd
from pathlib import Path
from tqdm import tqdm

from src.config import DOCUMENT_INDEX_PATH, PARAGRAPH_DATASET_PATH
from src.text_cleaner import clean_text, split_into_paragraphs


def main():
    if not DOCUMENT_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Document index not found: {DOCUMENT_INDEX_PATH}\n"
            "Run data_gatherer.py first."
        )

    index_df = pd.read_csv(DOCUMENT_INDEX_PATH)
    rows = []

    print(f"Processing {len(index_df)} documents...")

    for _, row in tqdm(index_df.iterrows(), total=len(index_df)):
        file_path = Path(str(row.get("file_path", "")))

        if not file_path.exists():
            print(f"[WARNING] Missing file: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = clean_text(f.read())
        except Exception as e:
            print(f"[ERROR] Reading {file_path}: {e}")
            continue

        paragraphs = split_into_paragraphs(text)

        for i, paragraph in enumerate(paragraphs):
            paragraph_id = f"{row['doc_id']}_P{i + 1:04d}"

            rows.append({
                "paragraph_id": paragraph_id,
                "doc_id": row.get("doc_id", ""),
                "source_name": row.get("source_name", ""),
                "title": row.get("title", ""),
                "company": row.get("company", ""),
                "sector": row.get("sector", ""),
                "document_type": row.get("document_type", ""),
                "theme": row.get("theme", ""),
                "url": row.get("url", ""),
                "text": paragraph,
                "char_count": len(paragraph),
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(PARAGRAPH_DATASET_PATH, index=False)

    print(f"\nSaved: {PARAGRAPH_DATASET_PATH}")
    print(f"Total paragraphs: {len(out_df)}")
    print(f"\nBy sector:")
    print(out_df["sector"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
