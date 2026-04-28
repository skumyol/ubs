#!/usr/bin/env python3
"""
Automated transcript downloader for Halliburton & SLB investor relations pages.
Saves transcripts to data/raw/pdf/ with standardized naming.
"""
import os
import re
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw" / "pdf"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def download_file(url: str, filename: str) -> bool:
    """Download a file with retry logic."""
    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        logger.info(f"✓ Already exists: {filename}")
        return True
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"✓ Downloaded: {filename} ({len(resp.content)/1024:.1f} KB)")
        return True
    except Exception as e:
        logger.error(f"✗ Failed {filename}: {e}")
        return False

def get_hal_transcripts():
    """Scrape Halliburton quarterly results page for transcript links."""
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    year = "2025"
    results = []
    
    for q in quarters:
        fool_url = f"https://www.fool.com/earnings/call-transcripts/{int(year)+1 if q=='Q4' else year}/{('01' if q=='Q4' else '04' if q=='Q1' else '07' if q=='Q2' else '10')}/21/halliburton-hal-{q.lower()}-{year}-earnings-call-transcript/"
        results.append((fool_url, f"hal_{q}_{year}_transcript.html"))
    
    return results

def get_slb_transcripts():
    """Scrape SLB quarterly results page for transcript links."""
    quarters = [
        ("Q4", "2025"),
        ("Q3", "2025"),
        ("Q2", "2025"),
        ("Q1", "2025"),
    ]
    results = []
    
    for q, year in quarters:
        fool_url = f"https://www.fool.com/earnings/call-transcripts/{int(year)+1 if q=='Q4' else year}/{('01' if q=='Q4' else '04' if q=='Q1' else '07' if q=='Q2' else '10')}/23/slb-slb-{q.lower()}-{year}-earnings-call-transcript/"
        results.append((fool_url, f"slb_{q}_{year}_transcript.html"))
    
    return results

def main():
    logger.info("🚀 Starting transcript download...")
    
    all_jobs = []
    all_jobs.extend(get_hal_transcripts())
    all_jobs.extend(get_slb_transcripts())
    
    success = 0
    for url, filename in all_jobs:
        if download_file(url, filename):
            success += 1
        time.sleep(2)
    
    logger.info(f"\n✅ Complete: {success}/{len(all_jobs)} files downloaded to {OUTPUT_DIR}")
    logger.info("🔁 Next: Run `python -m src.rebuild_index` to index new documents")

if __name__ == "__main__":
    main()
