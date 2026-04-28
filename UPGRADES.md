# Pitch-Winning Upgrades — Summary

Six upgrades applied on top of the base research pipeline to move the project from "good data gatherer" to "competition-ready pitch artifact."

## 1. Targeted Data Sources
**File:** `sources/seed_urls.csv`
- Added Sieyuan Electric (investor/about/product pages)
- Added Halliburton quarterly results page
- Added SLB quarterly results page
- Added grid-equipment peers: GE Vernova, Quanta, Eaton, Hitachi Energy, Siemens Energy
- Added policy sources: OPEC, CSIS, Atlantic Council

## 2. Valuation Engine (`src/valuation.py`)
Three-method framework from `base_plan.md` §4:
- **Peer comparables** via yfinance: P/E, EV/EBITDA, revenue growth, margins
- **Scenario valuation**: Bull/Base/Bear with probability-weighted target prices
- **Pair trade summary**: Long return + Short leg P&L → pair spread

**Live numbers (as of run):**
- Long Sieyuan (002028.SZ @ ¥222, 55x P/E) → Base case ¥265 (+19%), prob-weighted +19.3%
- Short HAL ($28 @ 22x P/E) → Base case $15 (-26%), prob-weighted -29.8%
- **Pair spread expected return: +49.1%**

## 3. Evidence Extractor (`src/evidence_extractor.py`)
Killer quotes mapped to each slide. Scoring heuristic rewards:
- Quantification (`%`, `$`, numbers)
- Named entities
- Moderate length (80-400 chars)
- High classifier confidence

Outputs `outputs/tables/evidence_pack.json` + `.md` for copy-paste into speaker notes.

## 4. Plan-Compliant Signal Tracker (`src/analysis.py`)
- `plan_format_signal_tracker()` produces the exact `High/Medium/Low` table from base_plan.md §3.5
- `narrative_shift_analysis()` quantifies thesis support score:
  - Grid signal share vs Oil signal share
  - Grid positive-sentiment rate
  - Oil negative-sentiment rate
  - Composite thesis score with interpretation band

**Current result:** thesis score **0.267** — "Moderate support for variant thesis" (Grid 43%, Oil 3% of signals).

## 5. PPTX Auto-Generator (`src/deck_generator.py`)
Builds `deck/UBS_Pitch_Deck_AUTO.pptx` — **24 slides**:

| # | Slide |
|---|-------|
| 1 | Title: Long the Grid, Short the Bottleneck |
| 2 | Executive Summary (with live pair spread %) |
| 3 | Consensus View |
| 4 | Variant View |
| 5 | Industry Outlook |
| 6 | Long Case: Sieyuan |
| 7 | Short Case: Halliburton |
| 8 | **Historical Backtest**: Oil vs HAL vs Sieyuan (2Y) |
| 9 | **Pair Trade Backtest Chart**: Long Sieyuan / Short HAL |
| 10 | Comparison Matrix (chart) |
| 11 | AI Signal Tracker Table |
| 12 | AI-Extracted Evidence |
| 13 | **Signal Trends Timeseries** |
| 14 | Signal Frequency Chart |
| 15 | Peer Comparables Table |
| 16 | Long Scenarios Table |
| 17 | Short Scenarios Table |
| 18 | **EPS Sensitivity Analysis** (tornado chart) |
| 19 | Catalysts |
| 20 | Risks (+ borrow cost / short squeeze) |
| 21 | **Trader Execution Framework**: Position sizing, carry cost, liquidity, technical timing |
| 22 | AI Advantages + Limitations |
| 23 | **💰 Money Slide**: Thesis + Proof + Spread + Catalysts |
| 24 | Recommendation (with live numbers) |

Branded with UBS palette (red/dark-blue), 16:9, tables auto-styled.

## 6. Q&A Defense Generator (`src/qna_defense.py`)
Auto-builds `docs/qna_defense.md` with:
- Key numbers section (memorize these)
- 8 anticipated questions with base answers + cited evidence
- Appendix: top quote per category

Every "Supporting Evidence" citation pulled from actual classified paragraphs with confidence scores.

## 7. Backtest Analysis (`src/backtest.py`)
Historical correlation analysis of oil prices vs HAL/Sieyuan:
- Fetches 2-year price data via yfinance
- Calculates rolling correlation (6-month window)
- Shows divergence between oil and oilfield services

**Results:**
- Oil +16.4%, HAL +9.6% (underperformed), Sieyuan +227.3% (massive outperformance)
- Oil-HAL correlation: 0.66 (moderate, but forward thesis is about margins, not correlation)

Output: `outputs/charts/oil_hal_correlation.png`

## 8. EPS Sensitivity Analysis (`src/sensitivity.py`)
Sieyuan EPS model with 5-variable sensitivity:
- Overseas revenue mix (%)
- Gross margin (%)
- R&D spend (% of revenue)
- SG&A spend (% of revenue)
- CNY/USD FX rate

**Base case EPS: ¥2.42** (updated to reflect market-implied forward estimate)

| Variable | ±20% Impact |
|----------|-------------|
| Gross margin | **±55%** (highest sensitivity) |
| SG&A | ±17.8% |
| R&D | ±9.7% |
| FX rate | ±9.1% |
| Overseas mix | ±2.5% |

Outputs: Tornado chart + 2D sensitivity matrix

## 9. ANEWFN Market Data Client (`src/anewfn_client.py`)
Real-time market data API integration:
- Historical bars (OHLCV)
- Live quotes
- Market news
- Symbol search

Auth: `ANEWFN_API_KEY` from `.env`

## 10. Trader Risk & Execution Analysis (`src/trader_analysis.py`)
PM-focused implementation details:

**Position Sizing (Risk-Based):**
- Max portfolio risk: 2% per trade
- Pair volatility: 42% annualized
- Recommended position: 2.4% of portfolio ($2.4M notional on $100M book)
- Allocation: $1.2M long Sieyuan / $1.2M short HAL (dollar-neutral)

**Carry Cost Analysis:**
| Cost Component | 6-Month Impact |
|----------------|----------------|
| HAL borrow (2-5%) | $15K - $33K |
| HAL dividend (short pays) | ~$9K |
| Sieyuan dividend (long receives) | ~$6K |
| **Net carry cost** | **$18K - $36K** (1.5-3% of expected return) |

**Technical Timing Signals:**
- HAL: **99.3% of 52-week high** + RSI 57.6 → Prime short entry at resistance
- Sieyuan: 86.5% of 52-week high + RSI 46.7 → Pulled back, reasonable entry

**Liquidity Assessment:**
- Sieyuan: $787M daily volume → Execute in <1 day
- HAL: $332M daily volume → Execute in <1 day
- Both liquid for target sizing

**Key Risk:** China A-share access (Stock Connect required) or use H-share proxy

Output: `data/processed/valuation/trader_analysis.csv`

## Orchestrator: `run_pipeline_report.py`
One command runs everything post-classification:
```bash
./run_prod.sh --check  # verify nothing already running
python run_pipeline_report.py
```

Sequence (10 steps):
1. Rebuild document index
2. Extract killer quotes (evidence pack)
3. Run analysis (signal tracker, narrative shift)
4. Generate charts (time-series signal trends)
5. Fetch market data + build valuation
6. Generate Q&A defense doc
7. Run backtest analysis (oil vs HAL/Sieyuan)
8. Run sensitivity analysis (Sieyuan EPS)
9. Run trader risk & execution analysis
10. Build pitch deck + generate pipeline report

## Test Coverage
**188 tests, 93.5% coverage** — maintained above 90% threshold.

New test files:
- `tests/test_valuation.py` (23 tests)
- `tests/test_evidence_extractor.py` (14 tests)
- `tests/test_analysis_extras.py` (8 tests)
- `tests/test_qna_defense.py` (9 tests)

## What's Still Missing (for full competition readiness)
1. **More raw data** — ✅ NOW HAVE 330 classified paragraphs. Target achieved.
2. **Real Sieyuan transcripts** — ✅ Extracted 1.1M chars from HKEX filing + OCR'd audit report.
3. **Time-series narrative shift** — ✅ Added monthly signal trends chart.
4. **Oil price vs HAL/Sieyuan backtest** — ✅ Implemented in `src/backtest.py`.
5. **Sensitivity tables** — ✅ Implemented in `src/sensitivity.py` with 5-variable EPS model.
6. **Chart polish** — Charts regenerated with full dataset.

**Status: COMPETITION-READY** 🎯

## How to Iterate
To improve scores:
1. Add more raw documents: drop `.txt`/`.pdf` into `data/raw/` subfolders
2. Rebuild index: `.venv/bin/python -m src.rebuild_index`
3. Classify new paragraphs: `.venv/bin/python -m src.run_classifier_pitch`
4. Re-run full pipeline: `python run_pipeline_report.py`

Each iteration auto-updates the deck, Q&A, charts, backtest, and sensitivity analysis.
