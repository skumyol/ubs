"""Unified data gatherer for UBS energy-security research pipeline.

Collects from:
- Seed URLs (IEA, company IR pages, etc.)
- RSS feeds (industry news)
- GDELT news API (free, no key)
- Local PDFs (annual reports, filings)

Outputs:
- data/raw/text/*.txt (extracted content)
- data/processed/document_index.csv (master registry)
- data/processed/paragraph_level_dataset.csv (split paragraphs)
"""

import os
import re
import json
import time
import hashlib
import urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
import pandas as pd
import feedparser
import trafilatura
import pdfplumber
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.config import (
    ROOT,
    DATA_DIR,
    RAW_TEXT_DIR,
    RAW_PDF_DIR,
    PROCESSED_DIR,
    DOCUMENT_INDEX_PATH,
    PARAGRAPH_DATASET_PATH,
    SEED_URLS_PATH,
    RSS_FEEDS_PATH,
    USER_AGENT,
)
from src.text_cleaner import clean_text, split_into_paragraphs


# ============================================================
# STARTER SOURCES
# ============================================================

STARTER_URLS = [
    {
        "source_name": "IEA Electricity 2026",
        "url": "https://www.iea.org/reports/electricity-2026",
        "company": "IEA",
        "sector": "Grid Infrastructure",
        "document_type": "Industry Report",
        "theme": "Electricity Demand",
    },
    {
        "source_name": "IEA Electricity 2026 - Grids",
        "url": "https://www.iea.org/reports/electricity-2026/grids",
        "company": "IEA",
        "sector": "Grid Infrastructure",
        "document_type": "Industry Report",
        "theme": "Grid Resilience",
    },
    {
        "source_name": "Halliburton Investor Relations",
        "url": "https://ir.halliburton.com/",
        "company": "Halliburton",
        "sector": "Oilfield Services",
        "document_type": "Investor Page",
        "theme": "Oilfield Services",
    },
    {
        "source_name": "SLB Investor Relations",
        "url": "https://investorcenter.slb.com/",
        "company": "SLB",
        "sector": "Oilfield Services",
        "document_type": "Investor Page",
        "theme": "Oilfield Services",
    },
    {
        "source_name": "Baker Hughes Investor Relations",
        "url": "https://investors.bakerhughes.com/",
        "company": "Baker Hughes",
        "sector": "Oilfield Services",
        "document_type": "Investor Page",
        "theme": "Oilfield Services",
    },
    {
        "source_name": "NOV Investor Relations",
        "url": "https://investors.nov.com/",
        "company": "NOV",
        "sector": "Oilfield Services",
        "document_type": "Investor Page",
        "theme": "Oilfield Services",
    },
]

STARTER_RSS = [
    {
        "source_name": "IEA News",
        "feed_url": "https://www.iea.org/rss/news.xml",
        "sector": "Energy",
        "theme": "Energy Policy",
    },
    {
        "source_name": "EIA Today in Energy",
        "feed_url": "https://www.eia.gov/rss/todayinenergy.xml",
        "sector": "Energy",
        "theme": "Energy Market",
    },
    {
        "source_name": "Offshore Energy",
        "feed_url": "https://www.offshore-energy.biz/feed/",
        "sector": "Oilfield Services",
        "theme": "Oil Logistics",
    },
    {
        "source_name": "Power Engineering",
        "feed_url": "https://www.power-eng.com/feed/",
        "sector": "Grid Infrastructure",
        "theme": "Grid Resilience",
    },
    {
        "source_name": "Data Center Dynamics",
        "feed_url": "https://www.datacenterdynamics.com/en/rss/",
        "sector": "Data Centers",
        "theme": "Electricity Demand",
    },
]

GDELT_QUERIES = [
    {
        "query": '"grid investment" OR "grid resilience" OR "transmission upgrade"',
        "sector": "Grid Infrastructure",
        "theme": "Grid Resilience",
    },
    {
        "query": '"data center power demand" OR "AI electricity demand"',
        "sector": "Data Centers",
        "theme": "Electricity Demand",
    },
    {
        "query": '"Strait of Hormuz" oil disruption OR "Middle East" energy infrastructure attack',
        "sector": "Oilfield Services",
        "theme": "Oil Supply Disruption",
    },
    {
        "query": '"oilfield services" logistics cost OR project delays OR supply chain',
        "sector": "Oilfield Services",
        "theme": "Oilfield Cost Pressure",
    },
    {
        "query": '"transformer shortage" OR "substation equipment" OR "switchgear demand"',
        "sector": "Grid Infrastructure",
        "theme": "Grid Equipment Demand",
    },
]


# ============================================================
# HELPERS
# ============================================================

def safe_filename(text: str, max_len: int = 90) -> str:
    text = str(text)
    text = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())
    return text[:max_len].strip("_") or "untitled"


def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


def fetch_html(url: str, timeout: int = 25) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[FETCH ERROR] {url} | {e}")
        return None


def extract_readable_text(html: str, url: str) -> str:
    text = trafilatura.extract(html, url=url)

    if text and len(text.strip()) > 300:
        return clean_text(text)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return clean_text(text)


def save_text_file(doc_id: str, title: str, text: str) -> str:
    filename = f"{doc_id}_{safe_filename(title)}.txt"
    path = RAW_TEXT_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return str(path)


def load_existing_index() -> pd.DataFrame:
    if DOCUMENT_INDEX_PATH.exists():
        return pd.read_csv(DOCUMENT_INDEX_PATH)
    return pd.DataFrame()


def save_document_index(new_rows: List[Dict]) -> None:
    if not new_rows:
        print("[INFO] No new rows to save.")
        return

    new_df = pd.DataFrame(new_rows)
    old_df = load_existing_index()

    if len(old_df) > 0:
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    dedupe_cols = ["url"] if "url" in final_df.columns else ["doc_id"]
    final_df = final_df.drop_duplicates(subset=dedupe_cols, keep="last")
    final_df.to_csv(DOCUMENT_INDEX_PATH, index=False)

    print(f"[SAVED] Document index: {DOCUMENT_INDEX_PATH}")
    print(f"[SAVED] Documents in index: {len(final_df)}")


def ensure_seed_files() -> None:
    if not SEED_URLS_PATH.exists():
        RAW_TEXT_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        SEED_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(STARTER_URLS).to_csv(SEED_URLS_PATH, index=False)
        print(f"[CREATED] {SEED_URLS_PATH}")

    if not RSS_FEEDS_PATH.exists():
        RSS_FEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(STARTER_RSS).to_csv(RSS_FEEDS_PATH, index=False)
        print(f"[CREATED] {RSS_FEEDS_PATH}")


# ============================================================
# GATHER FROM SEED URLS
# ============================================================

def gather_seed_urls() -> List[Dict]:
    ensure_seed_files()

    df = pd.read_csv(SEED_URLS_PATH)
    rows = []

    print("\n=== Gathering seed URLs ===")

    for _, row in tqdm(df.iterrows(), total=len(df)):
        url = row["url"]
        html = fetch_html(url)

        if not html:
            continue

        text = extract_readable_text(html, url)

        if not text or len(text) < 300:
            print(f"[LOW TEXT] {url}")
            continue

        doc_id = f"DOC_{hash_text(url)}"
        file_path = save_text_file(doc_id, row.get("source_name", "source"), text)

        rows.append({
            "doc_id": doc_id,
            "source_name": row.get("source_name", ""),
            "title": row.get("source_name", ""),
            "url": url,
            "company": row.get("company", ""),
            "sector": row.get("sector", ""),
            "document_type": row.get("document_type", ""),
            "theme": row.get("theme", ""),
            "source_method": "seed_url",
            "file_path": file_path,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "char_count": len(text),
            "status": "success",
        })

        time.sleep(1)

    return rows


# ============================================================
# GATHER FROM RSS
# ============================================================

def fetch_article_text(url: str) -> Optional[str]:
    html = fetch_html(url)
    if not html:
        return None

    text = trafilatura.extract(html, url=url)
    if text and len(text) > 300:
        return text

    return None


def gather_rss(max_articles_per_feed: int = 15) -> List[Dict]:
    ensure_seed_files()

    feeds = pd.read_csv(RSS_FEEDS_PATH)
    rows = []

    print("\n=== Gathering RSS feeds ===")

    for _, feed_row in tqdm(feeds.iterrows(), total=len(feeds)):
        feed_url = feed_row["feed_url"]

        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[RSS ERROR] {feed_url} | {e}")
            continue

        entries = parsed.entries[:max_articles_per_feed]

        for entry in entries:
            url = entry.get("link")
            title = entry.get("title", "Untitled")
            published = entry.get("published", "")

            if not url:
                continue

            text = fetch_article_text(url)

            if not text or len(text) < 300:
                continue

            doc_id = f"DOC_{hash_text(url)}"
            file_path = save_text_file(doc_id, title, text)

            rows.append({
                "doc_id": doc_id,
                "source_name": feed_row.get("source_name", ""),
                "title": title,
                "url": url,
                "company": "",
                "sector": feed_row.get("sector", ""),
                "document_type": "RSS Article",
                "theme": feed_row.get("theme", ""),
                "published": published,
                "source_method": "rss",
                "file_path": file_path,
                "date_collected": datetime.now().strftime("%Y-%m-%d"),
                "char_count": len(text),
                "status": "success",
            })

            time.sleep(1)

    return rows


# ============================================================
# GATHER FROM GDELT
# ============================================================

def gdelt_search(query: str, max_records: int = 25, days_back: int = 90) -> List[Dict]:
    end = datetime.utcnow()
    start = end - timedelta(days=days_back)

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "sort": "HybridRel",
        "startdatetime": start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.strftime("%Y%m%d%H%M%S"),
    }

    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"[GDELT ERROR] {query} | {e}")
        return []


def gather_gdelt_news(max_records_per_query: int = 15, days_back: int = 120) -> List[Dict]:
    rows = []

    print("\n=== Gathering GDELT news ===")

    for q in tqdm(GDELT_QUERIES):
        articles = gdelt_search(
            q["query"],
            max_records=max_records_per_query,
            days_back=days_back,
        )

        for article in articles:
            url = article.get("url")
            title = article.get("title", "Untitled")
            source_name = article.get("sourceCommonName", "")
            published = article.get("seendate", "")

            if not url:
                continue

            text = fetch_article_text(url)

            if not text or len(text) < 300:
                continue

            doc_id = f"DOC_{hash_text(url)}"
            file_path = save_text_file(doc_id, title, text)

            rows.append({
                "doc_id": doc_id,
                "source_name": source_name,
                "title": title,
                "url": url,
                "company": "",
                "sector": q.get("sector", ""),
                "document_type": "GDELT News Article",
                "theme": q.get("theme", ""),
                "published": published,
                "source_method": "gdelt",
                "file_path": file_path,
                "date_collected": datetime.now().strftime("%Y-%m-%d"),
                "char_count": len(text),
                "status": "success",
            })

            time.sleep(1)

    return rows


# ============================================================
# LOCAL PDF INGESTION
# ============================================================

def extract_pdf_text(pdf_path: Path) -> str:
    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

    return clean_text("\n\n".join(pages))


def gather_local_pdfs() -> List[Dict]:
    pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))
    rows = []

    print("\n=== Gathering local PDFs ===")

    if not pdf_files:
        print(f"[INFO] No PDFs found in {RAW_PDF_DIR}")
        return rows

    for pdf_path in tqdm(pdf_files):
        try:
            text = extract_pdf_text(pdf_path)
        except Exception as e:
            print(f"[PDF ERROR] {pdf_path.name} | {e}")
            continue

        if not text or len(text) < 300:
            print(f"[LOW PDF TEXT] {pdf_path.name}")
            continue

        doc_id = f"DOC_{hash_text(str(pdf_path.resolve()))}"
        file_path = save_text_file(doc_id, pdf_path.stem, text)

        rows.append({
            "doc_id": doc_id,
            "source_name": pdf_path.stem,
            "title": pdf_path.stem,
            "url": "",
            "company": "",
            "sector": "",
            "document_type": "PDF",
            "theme": "",
            "published": "",
            "source_method": "local_pdf",
            "file_path": file_path,
            "original_pdf": str(pdf_path),
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "char_count": len(text),
            "status": "success",
        })

    return rows


# ============================================================
# BUILD PARAGRAPH DATASET
# ============================================================

def build_paragraph_dataset() -> None:
    if not DOCUMENT_INDEX_PATH.exists():
        print("[ERROR] No document_index.csv found. Run data gathering first.")
        return

    index_df = pd.read_csv(DOCUMENT_INDEX_PATH)
    rows = []

    print("\n=== Building paragraph dataset ===")

    for _, row in tqdm(index_df.iterrows(), total=len(index_df)):
        file_path = Path(str(row.get("file_path", "")))

        if not file_path.exists():
            continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        paragraphs = split_into_paragraphs(text)

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
                "text": paragraph,
                "char_count": len(paragraph),
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(PARAGRAPH_DATASET_PATH, index=False)

    print(f"[SAVED] Paragraph dataset: {PARAGRAPH_DATASET_PATH}")
    print(f"[SAVED] Total paragraphs: {len(out_df)}")


# ============================================================
# SUMMARY
# ============================================================

def print_summary() -> None:
    print("\n=== SUMMARY ===")

    if DOCUMENT_INDEX_PATH.exists():
        docs = pd.read_csv(DOCUMENT_INDEX_PATH)
        print(f"Documents: {len(docs)}")
        print("\nBy source method:")
        print(docs["source_method"].value_counts(dropna=False))

        print("\nBy theme:")
        print(docs["theme"].value_counts(dropna=False).head(20))

    if PARAGRAPH_DATASET_PATH.exists():
        paras = pd.read_csv(PARAGRAPH_DATASET_PATH)
        print(f"\nParagraphs: {len(paras)}")

        print("\nParagraphs by theme:")
        print(paras["theme"].value_counts(dropna=False).head(20))


# ============================================================
# MAIN
# ============================================================

def main():
    all_rows = []

    all_rows.extend(gather_seed_urls())
    all_rows.extend(gather_rss(max_articles_per_feed=10))
    all_rows.extend(gather_gdelt_news(max_records_per_query=10, days_back=120))
    all_rows.extend(gather_local_pdfs())

    save_document_index(all_rows)
    build_paragraph_dataset()
    print_summary()


if __name__ == "__main__":
    main()
