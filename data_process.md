Yes — below is a **working concrete data-gathering setup** you can drop into your repo. It collects public sources from:

1. **URLs you manually provide**
2. **Company transcript / report pages**
3. **RSS feeds / news pages**
4. **PDFs**
5. Outputs a clean `document_index.csv` and raw `.txt` files for the AI Signal Tracker.

```md
ubs-energy-security-pitch/
├── requirements.txt
├── .env
├── data/
│   ├── raw/
│   │   ├── html/
│   │   ├── pdf/
│   │   └── text/
│   └── processed/
│       └── document_index.csv
├── scripts/
│   ├── gather_urls.py
│   ├── gather_rss.py
│   ├── pdf_to_text.py
│   └── build_document_index.py
└── sources/
    ├── urls_energy_security.csv
    └── rss_feeds.csv
```

---

## 1. `requirements.txt`

```txt
requests
beautifulsoup4
pandas
python-dotenv
pdfplumber
feedparser
tqdm
trafilatura
```

Install:

```bash
pip install -r requirements.txt
```

---

## 2. `sources/urls_energy_security.csv`

Create this manually first. Add URLs from company reports, IEA, EIA, Reuters pages you can access, company investor pages, etc.

```csv
source_name,url,company,sector,document_type,theme
IEA Electricity 2026,https://www.iea.org/reports/electricity-2026,IEA,Grid Infrastructure,Report,Electricity Demand
IEA Grids,https://www.iea.org/reports/electricity-2026/grids,IEA,Grid Infrastructure,Report,Grid Resilience
Halliburton Investor Relations,https://ir.halliburton.com/,Halliburton,Oilfield Services,Investor Page,Oilfield Services
SLB Investor Relations,https://investorcenter.slb.com/,SLB,Oilfield Services,Investor Page,Oilfield Services
Baker Hughes Investor Relations,https://investors.bakerhughes.com/,Baker Hughes,Oilfield Services,Investor Page,Oilfield Services
```

---

## 3. `scripts/gather_urls.py`

This fetches normal webpages and extracts readable text.

```python
import os
import re
import time
import hashlib
import pandas as pd
import requests
import trafilatura
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

INPUT_CSV = "sources/urls_energy_security.csv"
OUTPUT_DIR = Path("data/raw/text")
INDEX_PATH = Path("data/processed/document_index.csv")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def safe_filename(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())
    return text[:max_len].strip("_")


def hash_url(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:10]


def fetch_html(url: str, timeout: int = 20) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 research-bot/1.0 "
            "for academic stock-pitch research"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None


def extract_text(html: str, url: str) -> str:
    """
    First use trafilatura for clean article extraction.
    Fall back to BeautifulSoup if extraction fails.
    """
    text = trafilatura.extract(html, url=url)

    if text and len(text.strip()) > 300:
        return text.strip()

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def main():
    df = pd.read_csv(INPUT_CSV)
    rows = []

    for i, row in tqdm(df.iterrows(), total=len(df)):
        url = row["url"]
        html = fetch_html(url)

        if not html:
            continue

        text = extract_text(html, url)

        if not text or len(text) < 300:
            print(f"[WARNING] Very little text extracted from {url}")
            continue

        doc_id = f"DOC_{hash_url(url)}"
        filename = f"{doc_id}_{safe_filename(row['source_name'])}.txt"
        file_path = OUTPUT_DIR / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        rows.append({
            "doc_id": doc_id,
            "source_name": row.get("source_name", ""),
            "url": url,
            "company": row.get("company", ""),
            "sector": row.get("sector", ""),
            "document_type": row.get("document_type", ""),
            "theme": row.get("theme", ""),
            "file_path": str(file_path),
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "char_count": len(text),
            "status": "success"
        })

        time.sleep(1)

    out_df = pd.DataFrame(rows)

    if INDEX_PATH.exists():
        old_df = pd.read_csv(INDEX_PATH)
        out_df = pd.concat([old_df, out_df], ignore_index=True)
        out_df = out_df.drop_duplicates(subset=["url"], keep="last")

    out_df.to_csv(INDEX_PATH, index=False)
    print(f"Saved document index to {INDEX_PATH}")
    print(f"Saved text files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/gather_urls.py
```

---

## 4. `sources/rss_feeds.csv`

This is useful for gathering news signals. Use RSS feeds where possible because they are cleaner and more stable than scraping search pages.

```csv
source_name,feed_url,sector,theme
IEA News,https://www.iea.org/rss/news.xml,Energy,Energy Policy
EIA Today in Energy,https://www.eia.gov/rss/todayinenergy.xml,Energy,Energy Market
Offshore Energy News,https://www.offshore-energy.biz/feed/,Oilfield Services,Oil Logistics
Power Engineering,https://www.power-eng.com/feed/,Grid Infrastructure,Grid Resilience
Data Center Dynamics,https://www.datacenterdynamics.com/en/rss/,Data Centers,Electricity Demand
```

---

## 5. `scripts/gather_rss.py`

This gathers article links from RSS feeds and saves article text where accessible.

```python
import re
import time
import hashlib
import feedparser
import pandas as pd
import requests
import trafilatura
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

INPUT_CSV = "sources/rss_feeds.csv"
OUTPUT_DIR = Path("data/raw/text")
INDEX_PATH = Path("data/processed/document_index.csv")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def safe_filename(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())
    return text[:max_len].strip("_")


def hash_url(url: str) -> str:
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:10]


def fetch_article_text(url: str) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 research-bot/1.0"
    }

    try:
        html = requests.get(url, headers=headers, timeout=20).text
        text = trafilatura.extract(html, url=url)

        if text and len(text.strip()) > 300:
            return text.strip()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    except Exception as e:
        print(f"[ERROR] Failed article fetch: {url} | {e}")
        return None


def main(max_articles_per_feed: int = 20):
    feeds = pd.read_csv(INPUT_CSV)
    rows = []

    for _, feed_row in tqdm(feeds.iterrows(), total=len(feeds)):
        feed_url = feed_row["feed_url"]
        parsed = feedparser.parse(feed_url)

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

            doc_id = f"DOC_{hash_url(url)}"
            filename = f"{doc_id}_{safe_filename(title)}.txt"
            file_path = OUTPUT_DIR / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

            rows.append({
                "doc_id": doc_id,
                "source_name": feed_row.get("source_name", ""),
                "title": title,
                "url": url,
                "company": "",
                "sector": feed_row.get("sector", ""),
                "document_type": "News / RSS Article",
                "theme": feed_row.get("theme", ""),
                "published": published,
                "file_path": str(file_path),
                "date_collected": datetime.now().strftime("%Y-%m-%d"),
                "char_count": len(text),
                "status": "success"
            })

            time.sleep(1)

    new_df = pd.DataFrame(rows)

    if INDEX_PATH.exists():
        old_df = pd.read_csv(INDEX_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
        final_df = final_df.drop_duplicates(subset=["url"], keep="last")
    else:
        final_df = new_df

    final_df.to_csv(INDEX_PATH, index=False)
    print(f"Saved {len(new_df)} RSS articles.")
    print(f"Updated index: {INDEX_PATH}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/gather_rss.py
```

---

## 6. `scripts/pdf_to_text.py`

Use this for annual reports, filings, downloaded PDFs, broker reports you are allowed to use, etc.

Put PDFs here:

```text
data/raw/pdf/
```

Then run this script.

```python
import re
import hashlib
import pdfplumber
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

PDF_DIR = Path("data/raw/pdf")
TEXT_DIR = Path("data/raw/text")
INDEX_PATH = Path("data/processed/document_index.csv")

TEXT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def safe_filename(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9_\-]+", "_", text.strip())
    return text[:max_len].strip("_")


def hash_file_path(path: Path) -> str:
    return hashlib.md5(str(path).encode("utf-8")).hexdigest()[:10]


def extract_pdf_text(pdf_path: Path) -> str:
    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

    text = "\n\n".join(pages)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def main():
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    rows = []

    if not pdf_files:
        print(f"No PDFs found in {PDF_DIR}")
        return

    for pdf_path in tqdm(pdf_files):
        try:
            text = extract_pdf_text(pdf_path)
        except Exception as e:
            print(f"[ERROR] Failed PDF extraction {pdf_path}: {e}")
            continue

        if not text or len(text) < 300:
            print(f"[WARNING] Low text extraction from {pdf_path.name}")
            continue

        doc_id = f"DOC_{hash_file_path(pdf_path)}"
        text_filename = f"{doc_id}_{safe_filename(pdf_path.stem)}.txt"
        text_path = TEXT_DIR / text_filename

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

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
            "file_path": str(text_path),
            "original_pdf": str(pdf_path),
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "char_count": len(text),
            "status": "success"
        })

    new_df = pd.DataFrame(rows)

    if INDEX_PATH.exists():
        old_df = pd.read_csv(INDEX_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
        final_df = final_df.drop_duplicates(subset=["doc_id"], keep="last")
    else:
        final_df = new_df

    final_df.to_csv(INDEX_PATH, index=False)
    print(f"Converted {len(new_df)} PDFs.")
    print(f"Updated index: {INDEX_PATH}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/pdf_to_text.py
```

---

## 7. Build paragraph-level dataset

This converts your raw text files into paragraph chunks for AI classification.

Create:

```text
scripts/build_paragraph_dataset.py
```

```python
import re
import pandas as pd
from pathlib import Path
from tqdm import tqdm

INDEX_PATH = Path("data/processed/document_index.csv")
OUTPUT_PATH = Path("data/processed/paragraph_level_dataset.csv")


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_paragraphs(text: str, min_chars: int = 120, max_chars: int = 1800):
    raw_chunks = re.split(r"\n{2,}", text)

    paragraphs = []

    for chunk in raw_chunks:
        chunk = chunk.strip()

        if len(chunk) < min_chars:
            continue

        if len(chunk) <= max_chars:
            paragraphs.append(chunk)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", chunk)
            buffer = ""

            for sentence in sentences:
                if len(buffer) + len(sentence) <= max_chars:
                    buffer += " " + sentence
                else:
                    if len(buffer.strip()) >= min_chars:
                        paragraphs.append(buffer.strip())
                    buffer = sentence

            if len(buffer.strip()) >= min_chars:
                paragraphs.append(buffer.strip())

    return paragraphs


def main():
    index_df = pd.read_csv(INDEX_PATH)
    rows = []

    for _, row in tqdm(index_df.iterrows(), total=len(index_df)):
        file_path = Path(row["file_path"])

        if not file_path.exists():
            print(f"[WARNING] Missing file: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = clean_text(f.read())

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
                "url": row.get("url", ""),
                "text": paragraph,
                "char_count": len(paragraph)
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved paragraph dataset: {OUTPUT_PATH}")
    print(f"Total paragraphs: {len(out_df)}")


if __name__ == "__main__":
    main()
```

Run:

```bash
python scripts/build_paragraph_dataset.py
```

---

## 8. Quick test script

Create:

```text
scripts/check_dataset.py
```

```python
import pandas as pd
from pathlib import Path

index_path = Path("data/processed/document_index.csv")
paragraph_path = Path("data/processed/paragraph_level_dataset.csv")

index_df = pd.read_csv(index_path)
paragraph_df = pd.read_csv(paragraph_path)

print("\n=== Document Index ===")
print(index_df.head())
print(f"\nDocuments: {len(index_df)}")

print("\n=== Paragraph Dataset ===")
print(paragraph_df.head())
print(f"\nParagraphs: {len(paragraph_df)}")

print("\n=== Paragraphs by Sector ===")
print(paragraph_df["sector"].value_counts(dropna=False))

print("\n=== Paragraphs by Theme ===")
print(paragraph_df["theme"].value_counts(dropna=False))
```

Run:

```bash
python scripts/check_dataset.py
```

---

## 9. Minimal run order

```bash
python scripts/gather_urls.py
python scripts/gather_rss.py
python scripts/pdf_to_text.py
python scripts/build_paragraph_dataset.py
python scripts/check_dataset.py
```

At the end, you should have:

```text
data/processed/document_index.csv
data/processed/paragraph_level_dataset.csv
data/raw/text/*.txt
```

That is enough to start your AI classification module.

---

## 10. Important note

Do **not** scrape paid databases, broker reports, or websites that block scraping. For those, download or copy text manually if you have legal access, then place the files in:

```text
data/raw/pdf/
```

or:

```text
data/raw/text/
```

Then run the paragraph-building script.
