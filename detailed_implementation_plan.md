# Detailed Implementation Plan
## UBS Stock Pitch: Long the Grid, Short the Bottleneck

---

## 0. Project Overview

| Field | Value |
|-------|-------|
| **Thesis** | Long Sieyuan Electric / Short Oilfield-Service Peer |
| **Core Idea** | Energy security is shifting from "protecting fuel supply" to "protecting electricity continuity" |
| **Consensus** | Energy insecurity is bullish for oil-exposed cyclicals |
| **Variant View** | The more durable trade is to own grid infrastructure |
| **Target Deliverable** | Maximum 20-page English PowerPoint stock pitch deck |

---

## Phase 1: Infrastructure Setup (Day 1)

### 1.1 Repository Structure

```
ubs-energy-security-pitch/
├── data/
│   ├── raw/
│   │   ├── text/              # Scraped web content
│   │   └── pdf/               # Downloaded PDFs
│   ├── interim/               # Cleaned but not final data
│   └── processed/             # Final analysis-ready data
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── text_cleaner.py
│   ├── classifier.py
│   ├── analysis.py
│   └── charts.py
├── prompts/
│   └── classification_prompt.md
├── outputs/
│   ├── charts/
│   └── tables/
├── deck/
├── docs/
└── notebooks/
```

### 1.2 Environment Setup Commands

```bash
# Create project directory
mkdir ubs-energy-security-pitch && cd ubs-energy-security-pitch

# Initialize Python environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install requests beautifulsoup4 pandas trafilatura feedparser pdfplumber tqdm python-dateutil matplotlib plotly openpyxl jupyter
```

### 1.3 Data Gatherer Deployment

Deploy the data gatherer from `data_gatherer.md`.

| Component | Purpose |
|-----------|---------|
| Seed URL crawler | Scrape predefined sources (IEA, company IR pages) |
| RSS feed aggregator | Auto-collect from industry news sources |
| GDELT news API | Free news search for energy/grid/oil topics |
| PDF processor | Extract text from annual reports |

**Seed Sources to Configure** (from `sources.md`):

| Category | Key Sources |
|----------|-------------|
| Grid Infrastructure | IEA Electricity 2026, Power Engineering RSS |
| Long Company | Sieyuan Electric financial reports, HKEX filings |
| Short Candidates | Halliburton, SLB, Baker Hughes, NOV investor pages |
| Oilfield Disruption | Reuters, Offshore Energy RSS |

---

## Phase 2: Data Collection (Days 1-2)

### 2.1 Document Collection Targets

Collect 300-500 documents across these categories:

| Category | Sources | Target Count |
|----------|---------|--------------|
| Company Transcripts | Halliburton, SLB, Sieyuan earnings calls | 20-30 |
| Annual/Interim Reports | PDF filings from all companies | 15-25 |
| Industry Reports | IEA, EIA grid and electricity reports | 10-15 |
| News Articles | GDELT + RSS feeds | 200-300 |
| Policy Announcements | Government grid investment plans | 20-30 |

### 2.2 Output Files After Collection

| File | Description |
|------|-------------|
| `data/processed/document_index.csv` | Master document registry |
| `data/processed/paragraph_level_dataset.csv` | Split into paragraphs for AI analysis |

---

## Phase 3: AI Text Classification (Days 2-3)

### 3.1 Classification Categories

Each paragraph classified into:

| # | Category | Description | Example Keywords |
|---|----------|-------------|----------------|
| 1 | Oil Supply Disruption | War, sanctions, attacks, shipping | Strait of Hormuz, Middle East, production cuts |
| 2 | Oilfield Cost Pressure | Freight, materials, delays, logistics | supply chain, cost inflation, project delay |
| 3 | Grid Resilience | Transmission, substations, transformers | grid upgrade, transmission, switchgear |
| 4 | Electricity Demand | Data centers, EVs, AI, cooling | data center power, EV charging, electrification |
| 5 | Policy-Backed Capex | Government infrastructure investment | grid investment, national security, policy |
| 6 | Margin/Earnings Risk | Cost pressure, pricing, utilization | margin pressure, earnings risk, guidance |

### 3.2 AI Classification Prompt

Create `prompts/classification_prompt.md`:

```markdown
You are assisting an equity research team.

Classify the following paragraph into one or more categories:
1. Oil Supply Disruption
2. Oilfield Cost Pressure
3. Grid Resilience
4. Electricity Demand
5. Policy-Backed Capex
6. Margin / Earnings Risk

Return JSON:
{
  "category": "",
  "sentiment": "positive / neutral / negative",
  "confidence": 1-5,
  "reason": ""
}

Rules:
- Do not invent facts
- If irrelevant, return "Irrelevant"
- Keep reason under 20 words

Paragraph:
[INSERT TEXT]
```

### 3.3 Classification Pipeline

1. Load `paragraph_level_dataset.csv`
2. Batch paragraphs through AI classifier
3. Store results in `data/processed/classified_paragraphs.csv`
4. **Mandatory:** Human review of 10-15% samples for quality control

---

## Phase 4: Signal Analysis & Visualization (Days 3-4)

### 4.1 Analysis Outputs

| File | Purpose |
|------|---------|
| `ai_signal_tracker.csv` | Category frequency by sector with sentiment scores |
| `keyword_frequency.csv` | Trending terms over time |
| `long_short_matrix.csv` | Comparison table for Slide 9 |

### 4.2 Required Charts for Deck

| Chart | Slide | Purpose |
|-------|-------|---------|
| Energy Signal Heatmap | Slide 10 | Compare grid vs oilfield signal frequency |
| Keyword Timeline | Slide 3-4 | Show shift in language from oil to grid |
| Category Frequency Bar | Slide 10 | Visual proof of thesis |
| Long/Short Comparison Matrix | Slide 9 | The "slide judges remember" |

---

## Phase 5: Valuation Model (Days 4-5)

### 5.1 Long Valuation: Sieyuan Electric

**Method 1 — Comparable Multiples:**
- China power equipment peers
- Global grid equipment peers
- Metrics: P/E, EV/EBITDA, PEG, Revenue growth, EBITDA margin, ROE

**Method 2 — Scenario-Based P/E:**

| Case | Assumption | Valuation Impact |
|------|------------|----------------|
| Bear | Domestic grid demand slows, margin pressure | Low multiple |
| Base | Stable grid capex, overseas growth continues | Current/modest premium |
| Bull | Overseas growth accelerates, grid theme re-rates | Higher multiple |

**Method 3 — Earnings Sensitivity:**
- Model impact of: revenue growth, overseas mix, gross margin, R&D/SG&A, FX, raw materials

### 5.2 Short Valuation: Oilfield-Service Peer

**Method 1 — Historical Multiple Comparison:**
- 5-year average, cycle peak, cycle trough vs peers

**Method 2 — Margin Sensitivity:**
- Model downside from: logistics cost increase, lower utilization, delayed projects, regional disruption

**Method 3 — Oil Price vs Earnings Disconnect:**
- Show that higher oil prices do not equal immediate earnings upside for services

### 5.3 Pair Trade Output Table

| Stock | Current Price | Target Price | Upside/Downside | Key Driver |
|-------|---------------|--------------|-----------------|------------|
| Sieyuan Electric | TBD | TBD | +X% | Grid capex + overseas growth |
| Oilfield Peer | TBD | TBD | -X% | Margin pressure + capex delay |
| **Pair Spread** | -- | -- | **+X%** | Re-rating differential |

---

## Phase 6: Deck Construction (Days 5-8)

### 6.1 Slide-by-Slide Content Map

| Slide | Title | Key Content | Owner |
|-------|-------|-------------|-------|
| 1 | Executive Summary | Long/Short, thesis, pillars, upside/downside | Team Lead |
| 2 | Consensus View | Oil disruption = bullish for oil cyclicals | Industry Lead |
| 3 | Variant View | Energy security = grid resilience | Industry Lead |
| 4 | Industry Outlook | Electricity continuity as strategic infrastructure | Industry Lead |
| 5 | Long Case: Sieyuan | Product exposure, demand drivers, financial proof | Company Lead |
| 6 | Sieyuan Differentiation | Overseas growth, not just China proxy | Company Lead |
| 7 | Short Case: Oilfield | Revenue by region/business, geopolitical exposure | Company Lead |
| 8 | Short: Why Upside Overstated | Oil price does not equal earnings for services | Company Lead |
| 9 | Long/Short Matrix | Comparison matrix (the key slide) | Team Lead |
| 10 | AI Signal Tracker | Heatmap, keyword analysis, signal shifts | AI Lead |
| 11 | Valuation | Framework, scenarios, targets | Valuation Lead |
| 12 | Catalysts | 3-5 catalysts for each leg | Team Lead |
| 13 | Risks | Risk matrix with mitigants | Team Lead |
| 14-15 | AI Advantages/Limitations | Transparent AI methodology | AI Lead |

### 6.2 Slide-Writing Rules

Every slide must have:
1. **Sharp title** (not "Industry Overview")
2. **One main message**
3. **One visual proof**
4. **One investment implication**

---

## Phase 7: Quality Assurance (Days 8-10)

### 7.1 Red Team Review Checklist

- [ ] Is the short too risky?
- [ ] Is the long too consensus?
- [ ] Is the AI module actually useful?
- [ ] Is valuation too aggressive?
- [ ] Are we proving earnings impact or just telling a macro story?
- [ ] Can every chart be explained in 20 seconds?

### 7.2 Final Submission Checklist

- [ ] Deck is less than or equal to 20 pages
- [ ] One stock from UBS stock pool
- [ ] Long and short from same sector
- [ ] Clear one-sentence thesis
- [ ] Consensus view stated
- [ ] Variant view different
- [ ] Long case company-specific
- [ ] Short case company-specific
- [ ] AI module visible and useful
- [ ] AI limitations discussed
- [ ] Valuation supports trade
- [ ] Risks balanced
- [ ] Catalysts specific
- [ ] Sources cited
- [ ] Q&A answers prepared

---

## Technical Components to Build

### 1. Data Gatherer Module
- **File:** `src/data_gatherer.py`
- **Status:** Already provided in `data_gatherer.md` -- ready to deploy

### 2. Text Cleaner Module
- **File:** `src/text_cleaner.py`
- **Functions:** `clean_text()`, `split_into_paragraphs()`

### 3. AI Classifier Module
- **File:** `src/classifier.py`
- **Functions:** `build_classification_prompt()`, `parse_ai_response()`

### 4. Analysis Module
- **File:** `src/analysis.py`
- **Functions:** `category_counts()`, `sentiment_score()`

### 5. Charts Module
- **File:** `src/charts.py`
- **Functions:** `create_category_bar_chart()`, `create_signal_heatmap()`

---

## Immediate Next Steps

1. Create repository structure and initialize Git
2. Deploy data gatherer with seed URLs from `sources.md`
3. Run initial collection to validate sources (~2-3 hours)
4. Build classification pipeline with AI prompts
5. Start collecting Sieyuan and Halliburton/SLB transcripts

---

## Critical Success Factors

| Factor | How to Achieve |
|--------|----------------|
| Clear disagreement with consensus | Slide 2 vs Slide 3 contrast |
| Company-specific thesis | Not just "energy is the future" |
| Quantified variant view | AI signal tracker + valuation |
| AI module with limitations | Show methodology, admit constraints |
| Professional deck | 20 pages max, sharp titles, one message per slide |

**Winning Formula:** Clear thesis, hard evidence, quantified gap, clean deck.
