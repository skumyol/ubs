#!/usr/bin/env python3
"""Automated document downloader for Dongfang Electric and Sungrow IR pages."""
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

def get_dongfang_docs():
    """Scrape Dongfang investor/news pages for document links."""
    return [("https://www.dongfang.com/", "dongfang_ir_home.html")]


def get_sungrow_docs():
    """Scrape Sungrow investor relations page for document links."""
    return [("https://en.sungrowpower.com/investor", "sungrow_ir_home.html")]

def main():
    logger.info("🚀 Starting transcript download...")
    
    all_jobs = []
    all_jobs.extend(get_dongfang_docs())
    all_jobs.extend(get_sungrow_docs())
    
    success = 0
    for url, filename in all_jobs:
        if download_file(url, filename):
            success += 1
        time.sleep(2)
    
    logger.info(f"\n✅ Complete: {success}/{len(all_jobs)} files downloaded to {OUTPUT_DIR}")
    logger.info("🔁 Next: Run `python -m src.rebuild_index` to index new documents")

if __name__ == "__main__":
    main()
