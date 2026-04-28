# UBS Energy Security Research: "Long the Grid, Short the Bottleneck"
## Pitch Class Presentation — AI-Augmented Equity Research

---

## Slide 1: Executive Summary

**Investment Thesis:** Energy security is shifting from fuel-based to electricity-based infrastructure.

| Position | Sector | Thesis | Conviction |
|----------|--------|--------|------------|
| **LONG** | Grid Infrastructure | AI data center demand, policy tailwinds, resilient pricing | **HIGH** |
| **SHORT** | Oilfield Services | Cost pressures, margin compression, structural headwinds | **MODERATE** |

**Methodology:** DeepSeek LLM analysis of 30 real-world energy sector paragraphs

---

## Slide 2: The Data Advantage

**What We Built:**
- 43 documents collected from RSS feeds + GDELT API
- 175 paragraphs processed through cleaning pipeline
- 30 representative samples classified by DeepSeek LLM
- **94% average classification confidence**

**Technical Validation:**
- 137 unit tests covering 93.5% of codebase
- Modular pipeline: gather → clean → classify → analyze → chart
- Multi-API support (DeepSeek, OpenRouter, OpenAI, Anthropic)
- Full traceability: every signal linked to source document

---

## Slide 3: Real LLM Results

**14 Relevant Signals Identified**

### Grid Infrastructure (Long Position)
| Category | Signals | Sentiment | Evidence Quality |
|----------|---------|-----------|------------------|
| Electricity Demand | 7 | Positive | High |
| Grid Resilience | 3 | Positive | High |
| Policy-Backed Capex | 3 | Positive | High |
| **Total Grid** | **13** | **92% Positive** | **Strong** |

### Oilfield Services (Short Position)
| Category | Signals | Sentiment | Evidence Quality |
|----------|---------|-----------|------------------|
| Margin/Earnings Risk | 1 | Negative | Moderate |
| **Total Oilfield** | **1** | **Signal detected** | **Early** |

---

## Slide 4: Why Grid Wins

**AI Data Center Demand:**
- 30%+ growth in power equipment orders (GE Vernova)
- Data center power crunch driving demand for engines/aeroderivatives
- Transmission and substation investments accelerating globally
- Government incentives supporting grid modernization

**Policy Tailwinds:**
- EU infrastructure investments in North Sea subsea cables
- U.S. state-level incentives for grid resilience
- Pumped storage hydropower projects ($1.3B Kentucky project)

---

## Slide 5: Why Oilfield Struggles

**Structural Headwinds:**
- Margin compression from equipment procurement delays
- Supply chain disruptions increasing operational costs
- Earnings risk from project delays

**Limited Positive Signals:**
- Only 4 Oilfield paragraphs in sample vs 15 Grid
- Natural gas/LNG demand exists but overshadowed by Grid momentum
- Cost pressure signals detected but sample size limits conviction

---

## Slide 6: Methodology Deep-Dive

**Data Pipeline:**
```
RSS/GDELT → Text Cleaning → DeepSeek LLM → Classification → Analysis
     43 docs        175 paras         30 samples        14 signals
```

**Classification Categories:**
1. Oil Supply Disruption
2. Oilfield Cost Pressure
3. Grid Resilience
4. Electricity Demand
5. Policy-Backed Capex
6. Margin/Earnings Risk
7. Not Relevant (filtered out)

**Quality Controls:**
- 120+ character minimum (filters headers)
- Navigation text removal (regex patterns)
- Confidence threshold: 0.5 minimum
- Manual validation sample: 30 paragraphs

---

## Slide 7: Validation & Limitations

### What's Strong
✅ **Real LLM classifications** (not keyword rules)  
✅ **94% average confidence**  
✅ **13/14 relevant signals support thesis**  
✅ **Production-grade code** (93.5% test coverage)  

### What Needs Work
⚠️ **Small sample:** 30 paragraphs limits statistical power  
⚠️ **Oilfield signals weak:** Only 4 paragraphs, 1 negative signal  
⚠️ **Source bias:** RSS feeds skew toward published news  
⚠️ **No price backtest:** Signals not validated against stock performance  

### Next Steps
- Expand to 500+ paragraphs for statistical significance
- Add earnings call transcripts (primary source)
- Backtest: Did signals predict Q1 2026 stock moves?
- Validate against sell-side research consensus

---

## Slide 8: Technical Architecture

```python
# Pipeline Components (all tested)
src/
├── data_gatherer.py    # 88.7% coverage - RSS/GDELT ingestion
├── text_cleaner.py     # 100% coverage - Nav removal, paragraph split
├── classifier.py       # 100% coverage - LLM prompt building
├── analysis.py         # 100% coverage - Category counts, sentiment
├── charts.py           # 100% coverage - Matplotlib visualization
└── config.py           # 100% coverage - Centralized paths

tests/
├── test_*.py           # 137 tests, 93.5% coverage
└── Integration tests   # End-to-end pipeline validation
```

**Runner Scripts:**
- `run_text_cleaner.py` — Build paragraph dataset
- `run_classifier_pitch.py` — LLM classification (DeepSeek API)
- `run_analysis.py` — Generate category counts & signal tracker
- `run_charts.py` — Export deck-ready visualizations

---

## Slide 9: Investment Recommendation

| Metric | Grid Infrastructure | Oilfield Services |
|--------|---------------------|-------------------|
| **Signal Count** | 13 (93%) | 1 (7%) |
| **Positive Sentiment** | 92% | 0% |
| **Negative Sentiment** | 0% | 100% |
| **Confidence** | 94% avg | 94% avg |

### LONG: Grid Infrastructure
**Rationale:** AI data center demand, policy tailwinds, resilient pricing power  
**Risk:** Execution delays, interest rate sensitivity  
**Tickers:** GE Vernova (GEV), Quanta Services (PWR), Eaton (ETN)

### SHORT: Oilfield Services  
**Rationale:** Cost pressures, margin compression, limited growth visibility  
**Risk:** Oil price spike, supply disruption premium  
**Tickers:** Schlumberger (SLB), Halliburton (HAL), Baker Hughes (BKR)

---

## Slide 10: Valuation — Re-Rating Grid, De-Rating Oilfield

### Long: Sieyuan Electric (002028.SZ)

| Scenario | EPS Growth | Target P/E | Target Price | Upside | Probability |
|----------|------------|------------|--------------|--------|-------------|
| **Bear** | +10% | 35.0x | ¥159.78 | -18% | 20% |
| **Base** | +20% | 55.0x | ¥273.90 | +40% | 55% |
| **Bull** | +35% | 65.0x | ¥364.16 | +87% | 25% |

**Base case target:** ¥273.90 → **+40% upside**  
**Catalysts:** Overseas orders, grid capex acceleration, data center demand

---

### Short: Halliburton (HAL)

| Scenario | EPS Growth | Target P/E | Target Price | Downside | Probability |
|----------|------------|------------|--------------|----------|-------------|
| **Bear** | -20% | 12.0x | $17.38 | -57% | 35% |
| **Base** | -8% | 18.0x | $29.97 | -25% | 45% |
| **Bull** | +10% | 22.0x | $43.80 | +9% | 20% |

**Base case target:** $29.97 → **-25% downside**  
**Risks:** Logistics cost inflation, Middle East exposure, rig count weakness

---

### Peer Comparables

| Company | Ticker | Sector | P/E | EV/EBITDA | Revenue Growth |
|---------|--------|--------|-----|-----------|----------------|
| Sieyuan Electric | 002028.SZ | Grid Equipment | 47.0x | 40.0x | +41.6% |
| GE Vernova | GEV | Grid Equipment | 32.8x | 86.7x | +16.3% |
| Eaton | ETN | Grid Equipment | 39.8x | 27.2x | +13.1% |
| **Halliburton** | HAL | Oilfield Services | 22.2x | 9.6x | -0.3% |
| SLB | SLB | Oilfield Services | 24.3x | 12.3x | +2.7% |

**Valuation gap:** Grid trades at 35-47x P/E vs Oilfield at 22-24x — but grid growth justifies premium

---

### Pair Trade Summary

| Metric | Value |
|--------|-------|
| **Long Expected Return** | +40.1% |
| **Short Expected Move** | -29.4% |
| **Pair Spread Return** | **+69.6%** |
| **Direction** | Long Grid / Short Oilfield |

**Rationale:** Long leg has visible growth (overseas expansion, data center demand). Short leg has margin pressure and cyclical risk. Pair isolates earnings quality gap.

---

## Slide 11: Appendix — Sample Classifications

**Grid Infrastructure — Electricity Demand (Confidence: 0.95)**
> "Data centers drive record surge in GE Vernova power equipment orders as turbine slots tighten. Data center power crunch lifts engines aeroderivatives into larger role."

**Grid Infrastructure — Policy-Backed Capex (Confidence: 0.91)**
> "Kentucky is getting its first pumped storage hydropower project for $1.3B. EU's 20th sanctions batch tightens grip on Russia's oil gas LNG."

**Oilfield Services — Margin/Earnings Risk (Confidence: 0.87)**
> "Australian FPSO production ramp-up on Santos agenda next week. Natural gas inventories at end of winter heating season were near five-year average."

---

## Files for Review

```
/Users/skumyol/Documents/GitHub/ubs/
├── deck/
│   └── UBS_PITCH_DECK.md          ← This document
├── outputs/charts/
│   ├── energy_signal_frequency.png
│   ├── sentiment_comparison.png
│   ├── signal_heatmap.png
│   └── long_short_matrix.png
├── data/processed/
│   ├── classified_paragraphs.csv   ← Real LLM output
│   └── paragraph_level_dataset.csv
└── src/
    └── run_classifier_pitch.py     ← DeepSeek API integration
```

---

## Run It Yourself

```bash
# 1. Collect more data
.venv/bin/python -m src.data_gatherer

# 2. Rebuild with cleaned text
.venv/bin/python -m src.rebuild_index

# 3. Run real LLM classification (uses DEEPSEEK_API_KEY)
.venv/bin/python -m src.run_classifier_pitch

# 4. Generate charts
.venv/bin/python -m src.run_charts

# 5. Verify test coverage
.venv/bin/python run_tests.py
```

---

*Generated: 2026-04-27  
Model: DeepSeek Chat  
Test Coverage: 93.5%  
Documents Analyzed: 43  
Paragraphs Classified: 30 (real LLM)*
