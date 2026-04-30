#!/usr/bin/env python3
"""Download investor materials for the Dongfang/Sungrow pair.

Fetches documents from:
- Dongfang Electric: www.dongfang.com
- Sungrow: sungrowpower.com

Saves to data/raw/pdf/ for processing by rebuild_index.
"""

import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from src.config import RAW_PDF_DIR

# Try to import optional dependencies
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("[WARN] requests/beautifulsoup4 not installed. Install with: pip install requests beautifulsoup4")


# Company configurations
COMPANIES = {
    "dongfang": {
        "name": "Dongfang Electric",
        "ticker": "1072.HK",
        "ir_url": "https://www.dongfang.com/",
        "transcripts_url": "https://www.dongfang.com/",
        "file_pattern": r"report|announcement|annual|quarter|earnings|20(24|25|26)",
    },
    "sungrow": {
        "name": "Sungrow",
        "ticker": "300274.SZ",
        "ir_url": "https://en.sungrowpower.com/investor",
        "transcripts_url": "https://en.sungrowpower.com/investor",
        "file_pattern": r"report|announcement|annual|quarter|earnings|20(24|25|26)",
    },
}

# Request headers to mimic browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


def fetch_page(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch HTML content from URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None if failed
    """
    if not HAS_DEPS:
        print(f"[ERROR] Cannot fetch {url}: requests not installed")
        return None

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return None


def extract_pdf_links(html: str, base_url: str, pattern: str) -> List[Dict]:
    """Extract PDF links from HTML content.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links
        pattern: Regex pattern to match relevant filenames

    Returns:
        List of dicts with url, filename, and title
    """
    if not HAS_DEPS:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []
    regex = re.compile(pattern, re.IGNORECASE)

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        # Resolve relative URLs
        full_url = urljoin(base_url, href)

        # Check if it's a PDF
        if not full_url.lower().endswith(".pdf"):
            continue

        # Get filename from URL
        parsed = urlparse(full_url)
        filename = Path(parsed.path).name

        # Check if filename matches pattern
        if not regex.search(filename) and not regex.search(link.get_text(strip=True)):
            continue

        # Clean up the URL (remove tracking params)
        clean_url = full_url.split("?")[0]

        links.append({
            "url": clean_url,
            "filename": filename,
            "title": link.get_text(strip=True) or filename,
            "company": "",  # To be filled by caller
        })

    return links


def download_pdf(url: str, output_path: Path, timeout: int = 60) -> bool:
    """Download PDF file from URL.

    Args:
        url: PDF URL
        output_path: Where to save the file
        timeout: Download timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    if not HAS_DEPS:
        print(f"[ERROR] Cannot download {url}: requests not installed")
        return False

    try:
        print(f"  Downloading: {url[:60]}...")
        response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        response.raise_for_status()

        # Verify it's a PDF
        content_type = response.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            print(f"    [SKIP] Not a PDF (Content-Type: {content_type})")
            return False

        # Check file size (skip if too small - probably a redirect page)
        content_length = int(response.headers.get("Content-Length", 0))
        if content_length > 0 and content_length < 10000:  # Less than 10KB
            print(f"    [SKIP] File too small ({content_length} bytes)")
            return False

        # Save file
        output_path.write_bytes(response.content)
        print(f"    [SAVED] {output_path.name} ({len(response.content)} bytes)")
        return True

    except requests.RequestException as e:
        print(f"    [ERROR] Download failed: {e}")
        return False
    except Exception as e:
        print(f"    [ERROR] Unexpected error: {e}")
        return False


def download_company_transcripts(company_key: str, max_files: int = 8) -> int:
    """Download transcripts for a specific company.

    Args:
        company_key: Key from COMPANIES dict
        max_files: Maximum files to download

    Returns:
        Number of files downloaded
    """
    if company_key not in COMPANIES:
        print(f"[ERROR] Unknown company: {company_key}")
        return 0

    config = COMPANIES[company_key]
    print(f"\n[PROCESSING] {config['name']} ({config['ticker']})")
    print(f"  IR URL: {config['ir_url']}")

    # Fetch news/releases page
    html = fetch_page(config["transcripts_url"])
    if not html:
        # Try main IR page as fallback
        html = fetch_page(config["ir_url"])
        if not html:
            print(f"  [SKIP] Could not fetch any page for {config['name']}")
            return 0

    # Extract PDF links
    links = extract_pdf_links(html, config["transcripts_url"], config["file_pattern"])
    print(f"  Found {len(links)} potential PDF links")

    # Deduplicate by URL
    seen_urls = set()
    unique_links = []
    for link in links:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            link["company"] = config["name"]
            unique_links.append(link)

    # Limit to max_files
    unique_links = unique_links[:max_files]

    # Download each PDF
    downloaded = 0
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

    for link in unique_links:
        # Create safe filename
        safe_name = re.sub(r'[^\w\-_.]', '_', link["filename"])
        if not safe_name.endswith(".pdf"):
            safe_name += ".pdf"

        # Add company prefix
        prefix = f"{config['ticker']}_"
        if not safe_name.startswith(prefix):
            safe_name = prefix + safe_name

        output_path = RAW_PDF_DIR / safe_name

        # Skip if already exists
        if output_path.exists():
            print(f"  [SKIP] Already exists: {safe_name}")
            continue

        # Download
        if download_pdf(link["url"], output_path):
            downloaded += 1
            time.sleep(1)  # Be polite to server

    print(f"  Downloaded {downloaded} new files for {config['name']}")
    return downloaded


def download_all_transcripts(max_per_company: int = 8) -> Dict[str, int]:
    """Download transcripts for all configured companies.

    Args:
        max_per_company: Maximum files per company

    Returns:
        Dict mapping company name to download count
    """
    if not HAS_DEPS:
        print("[ERROR] Required dependencies not installed:")
        print("  pip install requests beautifulsoup4")
        return {}

    results = {}
    print("=" * 60)
    print("TRANSCRIPT DOWNLOADER")
    print("=" * 60)

    for company_key in COMPANIES:
        count = download_company_transcripts(company_key, max_per_company)
        results[COMPANIES[company_key]["name"]] = count
        time.sleep(2)  # Be polite between companies

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = 0
    for company, count in results.items():
        print(f"  {company}: {count} files")
        total += count
    print(f"  Total: {total} files")
    print(f"\nSaved to: {RAW_PDF_DIR}")

    return results


def verify_downloads() -> List[Path]:
    """Verify downloaded PDFs are valid.

    Returns:
        List of valid PDF paths
    """
    if not RAW_PDF_DIR.exists():
        return []

    valid_pdfs = []
    for pdf_path in RAW_PDF_DIR.glob("*.pdf"):
        content = pdf_path.read_bytes()[:10]
        # PDF magic number: %PDF-
        if content.startswith(b"%PDF-"):
            valid_pdfs.append(pdf_path)
        else:
            print(f"[WARN] {pdf_path.name} is not a valid PDF")

    return valid_pdfs


def print_manual_download_guide():
    """Print instructions for manually downloading transcripts."""
    print("\n" + "=" * 60)
    print("MANUAL DOWNLOAD GUIDE (When Sites Block Automated Requests)")
    print("=" * 60)

    print("\n[DONGFANG ELECTRIC]")
    print("  1. Visit: https://www.dongfang.com/")
    print("  2. Look for annual reports, announcements, and investor updates")
    print("  3. Download documents and save to: data/raw/pdf/")
    print("  4. Rename with prefix: DONGFANG_")

    print("\n[YANTAI JEREH]")
    print("  1. Visit: https://www.jereh.com/cn/investor/Investor-relations")
    print("  2. Look for annual reports, announcements, and investor updates")
    print("  3. Download documents and save to: data/raw/pdf/")
    print("  4. Rename with prefix: JEREH_")

    print("\n[FREE EIA/IEA REPORTS]")
    print("  1. EIA Annual Energy Outlook: https://www.eia.gov/outlooks/aeo/")
    print("  2. IEA Electricity Report: https://www.iea.org/reports/electricity-2026")
    print("  3. Download PDFs → data/raw/pdf/ (no rename needed)")

    print("\n[GE VERNOVA PEER COMP]")
    print("  1. Visit: https://www.gevernova.com/investors")
    print("  2. Download investor presentations (Q1-Q4 2024-2025)")
    print("  3. Save to data/raw/pdf/ with prefix: GEV_")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Try automated download first
    results = download_all_transcripts(max_per_company=8)

    # Verify downloads (includes existing PDFs)
    print("\n[VERIFYING DOWNLOADS]")
    valid_pdfs = verify_downloads()
    print(f"  Valid PDFs: {len(valid_pdfs)}")
    for pdf in valid_pdfs:
        print(f"    - {pdf.name}")

    # If no new downloads, show manual guide
    total_new = sum(results.values())
    if total_new == 0:
        print("\n[!] Automated download blocked by websites (anti-bot protection)")
        print_manual_download_guide()
    else:
        print("\n[RECOMMENDED NEXT STEPS]")
        print("  1. Rebuild document index:")
        print("     .venv/bin/python -m src.rebuild_index")
        print("  2. Run classifier:")
        print("     .venv/bin/python -m src.run_classifier_pitch")
        print("  3. Regenerate deck:")
        print("     .venv/bin/python -m src.run_full_pipeline")
