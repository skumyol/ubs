#!/usr/bin/env python3
"""Rebuild document index from existing raw text files."""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.config import RAW_TEXT_DIR, PROCESSED_DIR, DOCUMENT_INDEX_PATH, PARAGRAPH_DATASET_PATH
from src.data_gatherer import clean_text, split_into_paragraphs, load_existing_index, save_document_index


MIN_DOC_CHARS = 500
MIN_VALID_YEAR = 2018
MAX_VALID_YEAR_OFFSET = 1
STALE_SOURCE_MARKERS = [
    "halliburton",
    "schlumberger",
    "slb",
    "baker_hughes",
    "baker hughes",
    "nov",
    "hal_",
]


def parse_filename(filename: str) -> dict:
    """Parse document ID and title from filename."""
    # Pattern: DOC_<hash>_<title>.txt
    match = re.match(r'(DOC_[a-f0-9]+)_(.+)\.txt$', filename)
    if match:
        return {
            "doc_id": match.group(1),
            "title": match.group(2).replace('_', ' '),
        }
    stem = Path(filename).stem
    safe_stem = re.sub(r"[^a-zA-Z0-9]+", "_", stem).strip("_").lower()
    return {"doc_id": f"DOC_{safe_stem[:24]}", "title": stem.replace('_', ' ')}


def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename using various patterns."""
    fname = filename.lower()
    
    # Pattern 1: Q1-Q4 + year (e.g., hal_Q1_2025_transcript.txt)
    quarter_match = re.search(r'q[1-4]_(\d{4})', fname)
    if quarter_match:
        year = quarter_match.group(1)
        quarter = re.search(r'q([1-4])', fname).group(1)
        quarter_months = {'1': '01', '2': '04', '3': '07', '4': '10'}
        return f"{year}-{quarter_months[quarter]}-01"
    
    # Pattern 2: Year only (e.g., Company_2024_Annual_Report.txt)
    year_match = re.search(r'_(\d{4})_', fname)
    if year_match:
        return f"{year_match.group(1)}-06-01"  # Default to mid-year
    
    # Pattern 3: Year at start (e.g., 2025_Q1_...)
    year_start = re.match(r'(\d{4})[\-_]', fname)
    if year_start:
        return f"{year_start.group(1)}-06-01"
    
    # Pattern 4: DOC with year in title
    doc_year = re.search(r'doc_[a-f0-9]+_(\d{4})', fname)
    if doc_year:
        return f"{doc_year.group(1)}-06-01"
    
    return ""


def extract_date_from_content(content: str) -> str:
    """Extract a likely publication date from document content.
    
    Searches for common date patterns in the first 2000 characters.
    Returns the most recent valid year found (2020-2027) with default month.
    """
    # Search first 2000 chars for year mentions
    text_sample = content[:2000]

    explicit_date = re.search(
        r'(?:Published|Date|Last Updated|as of|As of):\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        text_sample,
        re.IGNORECASE,
    )
    if explicit_date:
        year, month, day = explicit_date.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    
    # Look for explicit month-year patterns
    month_year = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text_sample, re.IGNORECASE)
    if month_year:
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        month = month_map[month_year.group(1).lower()]
        year = month_year.group(2)
        return f"{year}-{month}-01"
    
    # Look for "Month DD, YYYY" or "Month YYYY"
    date_patterns = re.findall(r'(\d{4})', text_sample)
    valid_years = [y for y in date_patterns if 2020 <= int(y) <= 2027]
    if valid_years:
        # Use most recent year found, default to mid-year
        return f"{max(valid_years)}-06-01"
    
    return ""


def _validate_iso_date(date_str: str) -> str:
    """Validate/normalize ISO date and reject impossible ranges."""
    parsed = pd.to_datetime(date_str, errors="coerce")
    if pd.isna(parsed):
        return ""

    min_date = pd.Timestamp(f"{MIN_VALID_YEAR}-01-01")
    # Accept dates up to today; reject future dates only.
    max_date = pd.Timestamp(datetime.utcnow().date())
    if parsed < min_date or parsed > max_date:
        return ""

    return parsed.strftime("%Y-%m-%d")


def infer_metadata(title: str, text: str) -> dict:
    """Infer metadata from title and content."""
    title_lower = title.lower()
    text_lower = text.lower()

    if "dongfang" in title_lower or "dongfang electric" in text_lower or "dec-ltd" in text_lower:
        sector = "Grid Infrastructure"
    elif "sungrow" in title_lower or "sungrowpower" in text_lower or "pv inverter" in text_lower:
        sector = "Inverter & Storage Equipment"
    # Oilfield Services takes priority (explicit transcript markers override generic keywords)
    else:
        short_leg_markers = [
            'halliburton', 'schlumberger', 'slb', 'hal ', 'baker hughes',
            'sungrow', 'inverter', 'battery storage', 'energy storage system', 'solar inverter',
            'storage margin', 'price war', 'ess', 'pcs',
        ]
        if any(k in title_lower or k in text_lower for k in short_leg_markers):
            sector = "Inverter & Storage Equipment"
    # Grid Infrastructure comes second (grid equipment, power)
        elif any(k in title_lower or k in text_lower for k in [
            'ge vernova', 'siemens energy', 'hitachi energy', 'abb',
            'data center', 'grid', 'transmission', 'substation', 'hydropower',
            'power equipment', 'electricity', 'battery', 'solar', 'wind',
            'renewable', 'transformer', 'switchgear',
        ]):
            sector = "Grid Infrastructure"
    # Residual oil/gas content
        elif any(k in title_lower or k in text_lower for k in ['oil', 'gas', 'lng', 'petroleum']):
            sector = "Oilfield Services"
        else:
            sector = "Other"

    # Infer theme based on keywords
    if "dongfang" in title_lower:
        theme = "Dongfang Financials"
    elif "sungrow" in title_lower:
        theme = "Sungrow Financials"
    elif "pair analysis" in title_lower:
        theme = "Pair Analysis"
    elif any(k in title_lower for k in ['data center', 'datacenter', 'ai', 'cloud']):
        theme = "AI/Data Center Demand"
    elif any(k in title_lower for k in ['transmission', 'grid', 'substation', 'cable']):
        theme = "Grid Investment"
    elif any(k in title_lower for k in ['hydropower', 'dam', 'pumped storage']):
        theme = "Renewable/Hydro"
    elif any(k in title_lower for k in ['lng', 'liquefied', 'natural gas']):
        theme = "LNG/Gas"
    elif any(k in title_lower for k in ['oil', 'crude', 'petroleum']):
        theme = "Oil Supply"
    else:
        theme = "General Energy"

    # Infer document type
    if 'report' in title_lower:
        doc_type = "Report"
    elif 'earnings' in title_lower or 'investor' in title_lower:
        doc_type = "Earnings"
    elif 'news' in title_lower or 'article' in title_lower:
        doc_type = "News"
    else:
        doc_type = "Article"

    return {
        "sector": sector,
        "theme": theme,
        "document_type": doc_type,
    }


def rebuild_index():
    """Rebuild document index from raw text files."""
    print("=== Rebuilding Document Index ===")

    text_dir = RAW_TEXT_DIR
    if not text_dir.exists():
        print(f"Text directory not found: {text_dir}")
        return

    # Load existing index to preserve original published dates from GDELT
    existing_index = {}
    if DOCUMENT_INDEX_PATH.exists():
        existing_df = pd.read_csv(DOCUMENT_INDEX_PATH)
        for _, row in existing_df.iterrows():
            existing_index[row['doc_id']] = {
                'published': row.get('published', ''),
                'url': row.get('url', ''),
            }
        print(f"Loaded {len(existing_index)} existing doc metadata")

    # Clear existing index first
    if DOCUMENT_INDEX_PATH.exists():
        DOCUMENT_INDEX_PATH.unlink()

    rows = []
    skipped_low_quality = 0
    skipped_bad_dates = 0
    txt_files = list(text_dir.glob("*.txt"))
    print(f"Found {len(txt_files)} text files")

    for text_file in sorted(txt_files):
        if text_file.name.startswith('.'):
            continue

        lowered_name = text_file.name.lower()
        if any(marker in lowered_name for marker in STALE_SOURCE_MARKERS):
            continue

        parsed = parse_filename(text_file.name)
        doc_id = parsed["doc_id"]
        title = parsed["title"]

        # Read content for metadata inference and quality filtering
        try:
            content = text_file.read_text(encoding='utf-8', errors='ignore')
            if len(content.strip()) < MIN_DOC_CHARS:
                skipped_low_quality += 1
                continue
            sample = content[:500]
        except Exception:
            continue

        sample_lower = sample.lower()
        if any(marker in sample_lower for marker in STALE_SOURCE_MARKERS):
            continue

        metadata = infer_metadata(title, content[:3000])

        # Try to get original published date from existing index
        original_published = existing_index.get(doc_id, {}).get('published', '')
        original_url = existing_index.get(doc_id, {}).get('url', '')
        
        # Use published date if available and valid, otherwise extract from filename
        date_source = "filename_inferred"
        if isinstance(original_published, str) and len(original_published) >= 8:
            # GDELT format: YYYYMMDDHHMMSS
            try:
                candidate = f"{original_published[:4]}-{original_published[4:6]}-{original_published[6:8]}"
                date_str = _validate_iso_date(candidate)
                if date_str:
                    date_source = "published_field"
                else:
                    date_str = extract_date_from_filename(text_file.name)
            except Exception:
                date_str = extract_date_from_filename(text_file.name)
        else:
            date_str = extract_date_from_filename(text_file.name)
            # Fallback: try to extract date from content if filename has no date
            if not date_str:
                date_str = extract_date_from_content(content)
                if date_str:
                    date_source = "content_inferred"

        validated_date = _validate_iso_date(date_str)
        if validated_date:
            date_str = validated_date
            date_quality = "high" if date_source == "published_field" else "medium"
        else:
            # Accept undated docs for coverage but flag them
            date_str = ""
            date_quality = "low"
            date_source = "undated"

        company = "Various"
        if "dongfang" in title.lower() or "dongfang electric" in content[:1000].lower():
            company = "Dongfang Electric"
        elif "sungrow" in title.lower() or "sungrowpower" in content[:1000].lower():
            company = "Sungrow"

        rows.append({
            "doc_id": doc_id,
            "source_name": title if company != "Various" else "GDELT/RSS",
            "url": original_url,
            "file_path": str(text_file),
            "title": title,
            "company": company,
            "sector": metadata["sector"],
            "document_type": metadata["document_type"],
            "theme": metadata["theme"],
            "source_method": "rebuild",
            "date": date_str,
            "date_source": date_source,
            "date_quality": date_quality,
            "published": original_published,
            "char_count": len(content),
        })

    if rows:
        # Write directly to avoid deduping
        df = pd.DataFrame(rows)
        df.to_csv(DOCUMENT_INDEX_PATH, index=False)
        print(f"[SAVED] Document index: {len(rows)} documents")
        print(f"[FILTER] Skipped low-quality docs (<{MIN_DOC_CHARS} chars): {skipped_low_quality}")
        dq = df["date_quality"].value_counts().to_dict()
        print(f"[DATE QUALITY] {dq}")
    else:
        print("No documents found")


def rebuild_paragraph_dataset():
    """Rebuild paragraph dataset from index."""
    print("\n=== Rebuilding Paragraph Dataset ===")

    import pandas as pd
    from tqdm import tqdm
    from src.data_gatherer import split_into_paragraphs, clean_text
    from src.config import DOCUMENT_INDEX_PATH, PARAGRAPH_DATASET_PATH

    if not DOCUMENT_INDEX_PATH.exists():
        print("[ERROR] No document_index.csv found.")
        return

    index_df = pd.read_csv(DOCUMENT_INDEX_PATH)
    rows = []

    for _, row in tqdm(index_df.iterrows(), total=len(index_df)):
        file_path = Path(str(row.get("file_path", "")))

        if not file_path.exists():
            continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        cleaned = clean_text(text)
        # Use lower threshold (60 chars) for these articles
        paragraphs = split_into_paragraphs(cleaned, min_chars=60, max_chars=800)

        for i, paragraph in enumerate(paragraphs):
            paragraph_id = f"{row['doc_id']}_P{i+1:04d}"

            rows.append({
                "paragraph_id": paragraph_id,
                "doc_id": row.get("doc_id", ""),
                "source_name": row.get("source_name", ""),
                "title": row.get("title", ""),
                "company": row.get("company", ""),
                "sector": row.get("sector", ""),
                "document_type": row.get("document_type", ""),
                "theme": row.get("theme", ""),
                "source_method": row.get("source_method", ""),
                "url": row.get("url", ""),
                "date": row.get("date", ""),
                "text": paragraph,
                "char_count": len(paragraph),
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(PARAGRAPH_DATASET_PATH, index=False)
    print(f"[SAVED] Paragraph dataset: {len(rows)} paragraphs")


def main():
    rebuild_index()
    rebuild_paragraph_dataset()

    # Print summary
    print("\n=== SUMMARY ===")
    if DOCUMENT_INDEX_PATH.exists():
        docs = pd.read_csv(DOCUMENT_INDEX_PATH)
        print(f"Documents: {len(docs)}")
        print("\nBy sector:")
        print(docs["sector"].value_counts())
        print("\nBy theme:")
        print(docs["theme"].value_counts().head(10))

    if PARAGRAPH_DATASET_PATH.exists():
        try:
            paras = pd.read_csv(PARAGRAPH_DATASET_PATH)
            print(f"\nParagraphs: {len(paras)}")
        except pd.errors.EmptyDataError:
            print("\nParagraphs: 0 (empty dataset)")


if __name__ == "__main__":
    main()
