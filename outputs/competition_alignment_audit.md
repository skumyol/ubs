# UBS 2026 Finance Challenge Alignment Audit

Generated: 2026-04-30

## Official Requirements Checked

- Team of 3.
- Hong Kong or Mainland China track.
- One designated AI analyst.
- Pair trade: one long and one short.
- One stock must be from the official stock pool.
- The other stock should be from the same sector and outside the provided list.
- Presentation must be in English and no more than 20 pages, excluding appendices.
- Presentation must explain long-short strategy, industry outlook, company fundamentals, valuation comparison, and investment recommendation.
- Must include at least one AI-assisted analysis module and explain AI advantages and limitations.
- Cover page must include track, sector, all team members' names, universities, and expected graduation dates.
- Submission deadline: 2026-04-30 23:59 Hong Kong time.

## Current Alignment Verdict

Current package is analytically strong. The deck has now been cut to the 20-page limit, but stock-pool interpretation and team metadata still need human confirmation.

## Critical Issues

| Severity | Issue | Current State | Required Fix |
|---|---|---|---|
| Critical | Stock-pool compliance | Current pair is Long Dongfang / Short Jereh. Both are official Energy Transition pool stocks. | Confirm with UBS if two pool stocks are allowed. If not, keep Dongfang as pool anchor and replace Jereh with a non-pool same-sector short. |
| Resolved | Slide count | `deck/UBS_Pitch_Deck_AUTO.pptx` has 20 slides. | No further action unless appendices are added. |
| Critical | Cover page | Slide 1 includes Hong Kong Track and Energy Transition, but lacks team names, universities, and expected graduation dates. | Add required team metadata before submission. |
| High | Generated report references missing source deck markdown | `outputs/submission_report.md` lists `deck/UBS_PITCH_DECK.md`, but that file does not exist. | Either generate the markdown file or remove this row. |
| High | Submission checklist is unchecked | `outputs/submission/submission_readiness_checklist.md` still uses `[ ]` placeholders. | Generate checked status from actual file existence and quality gates. |

## Content Issues To Fix Before Submission

| File | Issue | Fix |
|---|---|---|
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Resolved: Dongfang wording no longer says pure-play T&D. | No action. |
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Resolved: stale EPS sensitivity slide removed from the 20-slide main deck. | Keep sensitivity output in appendix/report if needed. |
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Resolved: execution slide now pulls pair volatility and recommended notional from `trader_analysis.csv`. | No action. |
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Resolved: AI module slide now pulls current document and paragraph counts. | No action. |
| `deck/UBS_Pitch_Deck_AUTO.pptx` | Some slides use global US/EU grid facts that are less central to the Hong Kong track China energy-transition thesis. | Keep China/State Grid/Dongfang/Jereh evidence dominant. |
| `README.md` | Still describes old Sieyuan/Halliburton thesis. | Update or exclude from submission package. |
| `run_pipeline_report.py` | Still references old HAL/Sieyuan artifacts. | Mark as obsolete or update if it will be shared. |
| `outputs/tables/llm_generated/*.json` | Some LLM-generated content contains aggressive or stale phrasing such as "100%+ spread target" and unsupported large claims. | Do not use these files directly in final deck unless regenerated/edited. |

## What Is Working

- `run_full_pipeline.sh` is the single execution entrypoint.
- Current report and Q&A correctly frame the idea as empirical and predictive, not historically validated.
- Data quality gates pass: 47 documents, 426 paragraphs, 426 classified paragraphs, 11 unique dates, 0 invalid/future dates.
- Evidence pack is aligned to Dongfang/Jereh and no longer Sieyuan/Halliburton.
- Predictive scorecard correctly separates adverse historical backtest from forward setup.
- AI module exists and includes limitations.
- Valuation, DCF cross-check, risk memo, trader analysis, and catalysts exist.

## Competition Fit Assessment

| Dimension | Status | Notes |
|---|---|---|
| Sector selection | Pass | Energy Transition is an official sector. |
| Long-short strategy | Pass | Clear long Dongfang / short Jereh framework. |
| Stock pool rule | At risk | Both stocks are from pool; official Chinese brief says the non-anchor cannot be from the pool. |
| Same-sector requirement | Pass | Both are Energy Transition / related industrials. |
| English presentation | Pass | Deck is English. |
| <=20 pages | Pass | Current deck has 20 slides. |
| Cover page metadata | Partial | Track and sector included; team names, universities, and graduation dates still need adding. |
| Industry outlook | Pass | Present, but should be more China-focused. |
| Company fundamentals | Pass | Present with 2025 figures. |
| Valuation comparison | Pass | Scenario, peer comps, DCF cross-check included. |
| AI module | Pass | Present with advantages/limitations, but exact counts need updating. |
| Submission readiness | Partial | Core artifacts exist; checklist and deck compliance need correction. |

## Recommended Next Action

Before any further polishing, resolve the stock-pool interpretation:

1. If UBS allows both legs from the official pool, keep Dongfang/Jereh and use the current 20-slide deck.
2. If UBS enforces the Chinese wording strictly, keep Dongfang as the pool anchor and replace Jereh with a non-pool same-sector short immediately.

If keeping Dongfang/Jereh, the fastest compliant deck cut is:

1. Cover with required metadata.
2. Executive summary.
3. Variant view / why now.
4. Industry outlook.
5. Dongfang long case.
6. Jereh short case.
7. Comparison table.
8. Empirical predictive scorecard.
9. AI module methodology.
10. AI module outputs and limitations.
11. Valuation summary.
12. DCF / sensitivity summary.
13. Catalysts.
14. Risks and kill switches.
15. Execution and sizing.
16. Recommendation.

Keep detailed evidence, charts, and raw backtest in appendices only if allowed by the final PDF/page handling.
