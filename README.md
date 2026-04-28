# UBS Stock Pitch: Long the Grid, Short the Bottleneck

> **TL;DR:** Energy security isn't about oil anymore—it's about keeping the lights on. We're long Sieyuan Electric (China's grid equipment leader) and short Halliburton (oilfield services). The market hasn't figured out this shift yet.

---

## What's This Project?

This is an **AI-powered stock pitch pipeline** that reads thousands of news articles, earnings transcripts, and industry reports to find evidence for a contrarian trade.

Instead of manually reading 50+ documents, we use AI to:
- **Extract** text from PDFs, websites, and transcripts
- **Classify** paragraphs into themes (grid demand vs oilfield pressure)
- **Score** sentiment (bullish/bearish) for each theme
- **Generate** charts and killer quotes for the pitch deck

---

## The Trade

| Leg | Company | Ticker | Why? |
|-----|---------|--------|------|
| **LONG** | Sieyuan Electric | 002028.SZ | Builds transformers, switchgear, and grid equipment. Benefits from China's $100B+ grid hardening push + AI datacenter power demand. |
| **SHORT** | Halliburton | HAL | Oilfield services exposed to logistics disruptions, margin pressure, and cyclical capex cuts. Vulnerable to "higher oil =/= higher service earnings" reality. |

**The Variant View:** Most investors think energy security = long oil. We think it's long *electricity continuity* (grid infrastructure).

---

## Quick Start (One Command)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the entire pipeline
python run_pipeline_report.py
```

This generates:
- `deck/UBS_Pitch_Deck_AUTO.pptx` — The final pitch deck
- `docs/qna_defense.md` — Q&A cheat sheet for judges
- `outputs/tables/evidence_pack.md` — Best quotes by slide
- `outputs/charts/signal_trends_timeseries.png` — Signal momentum chart
- `data/processed/valuation/peer_comps.csv` — P/E, EV/EBITDA, ROIC comparisons

---

## Project Structure (Simple Version)

```
ubs/
├── data/
│   ├── raw/text/          # Downloaded articles & transcripts
│   ├── raw/pdf/           # PDF reports (Sieyuan annual reports, etc.)
│   └── processed/         # Cleaned data ready for analysis
├── src/
│   ├── rebuild_index.py   # Rebuilds document index from raw files
│   ├── evidence_extractor.py  # Finds "killer quotes" for each slide
│   ├── analysis.py        # Builds signal tracker & narrative scores
│   ├── valuation.py       # Peer comps & scenario analysis
│   ├── charts.py          # Generates charts for deck
│   └── qna_defense.py     # Auto-generates Q&A defense document
├── deck/
│   └── UBS_Pitch_Deck_AUTO.pptx  # Final output
├── docs/
│   └── qna_defense.md     # Judge Q&A cheat sheet
├── outputs/
│   ├── charts/            # PNG charts
│   └── tables/            # CSV data tables
└── run_pipeline_report.py # ONE SCRIPT TO RUN THEM ALL
```

---

## How It Works (Step by Step)

### 1. **Data Collection**
- Downloaded Halliburton & SLB earnings transcripts (Motley Fool)
- Extracted Sieyuan's HKEX filing (1.1M characters) and audit report via OCR
- Scraped 50+ energy news articles (IEA, EIA, industry sources)

### 2. **Text Processing**
- Split documents into 2,435 paragraphs
- Extracted dates from filenames (Q3_2025 → 2025-07-01)
- Classified each paragraph by sector (Grid vs Oilfield)

### 3. **AI Classification**
- Used DeepSeek/Qwen LLMs to classify 330 paragraphs into 6 categories:
  - Grid Resilience | Electricity Demand | Policy-Backed Capex
  - Oil Supply Disruption | Oilfield Cost Pressure | Margin/Earnings Risk
- Scored sentiment (positive/bullish vs negative/bearish)

### 4. **Evidence Extraction**
- Found "killer quotes" with specific numbers ("$45M loan", "35% growth")
- Filtered out boilerplate text
- Deduplicated across slides
- Selected top 11 quotes for 6 key slides

### 5. **Analysis & Valuation**
- **Signal Tracker:** Grid "Electricity demand" = High, Oilfield "Margin pressure" = High
- **Thesis Score:** 0.164 (moderate support for variant view)
- **Peer Comps:** Added ROIC calculation (new!) alongside P/E and EV/EBITDA
- **Scenarios:** 27.1% expected return (long) + -29.8% (short) = 56.9% pair spread

### 6. **Deck Generation**
- Auto-generated PowerPoint with charts, tables, and killer quotes
- Created Q&A defense doc with evidence citations

---

## The Numbers That Matter

| Metric | Value | What It Means |
|--------|-------|---------------|
| **Grid Signal Share** | 34.2% | 1/3 of all signals about grid infrastructure |
| **Oil Signal Share** | 27.9% | Less than grid (good for our thesis) |
| **Thesis Support Score** | 0.164 | Moderate support—market is shifting but not there yet |
| **Pair Spread Return** | 56.9% | Combined long + short expected return |
| **Documents Analyzed** | 55 | News articles, transcripts, reports |
| **Paragraphs Classified** | 330 | Each scored for category + sentiment |

---

## Key Output Files

| File | What It Is | Why It Matters |
|------|-----------|----------------|
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Final pitch deck | What the judges see |
| `docs/qna_defense.md` | Q&A cheat sheet | Answers to expected judge questions |
| `outputs/tables/evidence_pack.md` | Best quotes by slide | "Killer quotes" with citations |
| `data/processed/valuation/peer_comps.csv` | Peer comparison table | P/E, EV/EBITDA, **ROIC** (new!) |
| `outputs/charts/signal_trends_timeseries.png` | Signal momentum chart | Shows grid vs oilfield trends over time |
| `data/raw/text/DOC_Sieyuan_HKEX_Filing.txt` | 1.1M chars extracted | Primary source for China long leg |

---

## Running Individual Steps

```bash
# Just rebuild the document index
python src/rebuild_index.py

# Just extract killer quotes
python src/evidence_extractor.py

# Just update valuation models
python src/valuation.py

# Just regenerate Q&A defense
python src/qna_defense.py

# Just regenerate charts
python src/charts.py

# Just regenerate deck
python src/deck_generator.py
```

---

## Environment Setup

Create `.env` file with API keys:

```bash
# For AI classification (DeepSeek)
DEEPSEEK_API_KEY=sk-d0bb...

# For OCR (Qwen Vision)
DASHSCOPE_API_KEY=sk-5f1c...

# Alternative LLM provider
OPENROUTER_API_KEY=sk-or-v1...
```

---

## For Developers

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_valuation.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Adding New Data
1. Drop text files into `data/raw/text/`
2. Name format: `DOC_<id>_<description>.txt` or `hal_Q3_2025_transcript.txt`
3. Run `python src/rebuild_index.py`
4. Run `python run_pipeline_report.py`

---

## What's Different About This Approach?

**Traditional equity research:** Read 10-Ks, build Excel models, write 40-page reports.

**Our approach:**
- AI reads 55 documents → 2,435 paragraphs
- Auto-classifies into themes
- Extracts quantified evidence
- Generates data-driven deck

**Result:** More evidence, faster iteration, traceable citations.

---

## Need Help?

- **Read the thesis:** `base_plan.md`
- **See the data process:** `data_process.md`
- **Check sources:** `sources.md`
- **Review Q&A prep:** `docs/qna_defense.md`

---

## License & Ethics

- Do not scrape paid databases without permission
- All AI outputs are reviewed before use
- Every quote is traceable to original source
- This is for educational/competition purposes
