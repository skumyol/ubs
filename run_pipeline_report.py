#!/usr/bin/env python3
"""Run the full pipeline and generate a summary report."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).parent))


def run_step(name, cmd):
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    success = result.returncode == 0
    output = result.stdout[-2500:] if len(result.stdout) > 2500 else result.stdout
    error = result.stderr[-500:] if result.stderr else ''
    print(output)
    if error and not success:
        print(f"ERRORS: {error}")
    return {"name": name, "success": success, "output": output, "error": error}


results = []

# Step 1: Rebuild Index
results.append(run_step("Rebuild Index",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/rebuild_index.py"))

# Step 2: Sanitize Classifications
results.append(run_step("Sanitize Classifications",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/sanitize_classifications.py"))

# Step 3: Evidence Extraction
results.append(run_step("Evidence Extraction",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/evidence_extractor.py"))

# Step 4: Analysis - Signal Tracker (run inline)
print(f"\n{'='*60}")
print("STEP: Analysis - Signal Tracker & Narrative Shift")
print('='*60)
import pandas as pd
from src.analysis import plan_format_signal_tracker, narrative_shift_analysis
df = pd.read_csv('data/processed/classified_paragraphs.csv')
tracker = plan_format_signal_tracker(df)
print('=== SIGNAL TRACKER ===')
print(tracker.to_string())
narrative = narrative_shift_analysis(df)
print('\n=== NARRATIVE SHIFT ===')
narrative_output = []
for k, v in narrative.items():
    line = f'  {k}: {v}'
    print(line)
    narrative_output.append(line)
results.append({"name": "Analysis - Signal Tracker", "success": True, 
                "output": tracker.to_string() + '\n' + '\n'.join(narrative_output), "error": ""})

# Step 5: Valuation
results.append(run_step("Valuation",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/valuation.py"))

# Step 6: Q&A Defense
results.append(run_step("Q&A Defense",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/qna_defense.py"))

# Step 7: Charts (run inline)
print(f"\n{'='*60}")
print("STEP: Charts")
print('='*60)
os.makedirs('outputs/charts', exist_ok=True)
from src.charts import create_signal_trends_timeseries
df = pd.read_csv('data/processed/classified_paragraphs.csv')
create_signal_trends_timeseries(df, 'outputs/charts/signal_trends_timeseries.png')
print('Charts generated successfully')
results.append({"name": "Charts", "success": True, 
                "output": "Time-series chart generated at outputs/charts/signal_trends_timeseries.png", "error": ""})

# Step 8: Backtest Analysis (Oil vs HAL/Sieyuan)
results.append(run_step("Backtest Analysis",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/backtest.py"))

# Step 9: Blind Classification Validation
results.append(run_step("Blind Classification Validation",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/validation.py"))

# Step 10: Signal-Return Predictive Analysis
results.append(run_step("Signal-Return Analysis",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/signal_return_analysis.py"))

# Step 11: Data Quality Audit
results.append(run_step("Data Quality Audit",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/data_quality.py"))

# Step 12: Sensitivity Analysis (Sieyuan EPS)
results.append(run_step("Sensitivity Analysis",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/sensitivity.py"))

# Step 13: Trader Risk & Execution Analysis
results.append(run_step("Trader Analysis",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/trader_analysis.py"))

# Step 14: Submission Pack
results.append(run_step("Submission Pack",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/submission_pack.py"))

# Step 15: Deck Generation
results.append(run_step("Deck Generation",
    "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/deck_generator.py"))

# Generate Markdown Report
report_lines = [
    "# UBS Pitch Pipeline Execution Report",
    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    "## Summary",
    f"- **Total Steps:** {len(results)}",
    f"- **Passed:** {sum(1 for r in results if r['success'])}",
    f"- **Failed:** {sum(1 for r in results if not r['success'])}",
    "",
    "## Pipeline Results",
    "",
]

for r in results:
    status = "PASS" if r["success"] else "FAIL"
    report_lines.append(f"### {r['name']} - {status}")
    report_lines.append("")
    report_lines.append("```")
    report_lines.append(r["output"][-1000:] if len(r["output"]) > 1000 else r["output"])
    report_lines.append("```")
    report_lines.append("")

# Add key outputs
report_lines.extend([
    "## Key Output Files",
    "",
    "| File | Description |",
    "|------|-------------|",
    "| `deck/UBS_Pitch_Deck_AUTO.pptx` | Final pitch deck (with honest text analysis framing) |",
    "| `docs/qna_defense.md` | Q&A defense sheet |",
    "| `outputs/tables/evidence_pack.md` | Supporting quotes by slide |",
    "| `outputs/tables/evidence_pack.json` | Evidence pack (JSON) |",
    "| `outputs/validation/validation_report.md` | Blind classification validation test |",
    "| `outputs/validation/blind_validation_sample.csv` | Held-out sample for external validation |",
    "| `outputs/signal_return/signal_return_report.md` | Predictive power analysis (do signals forecast returns?) |",
    "| `outputs/quality/data_quality_report.md` | Data integrity and date QA report |",
    "| `outputs/submission/trade_construction.md` | Execution plan (sizing, rebalance, constraints) |",
    "| `outputs/submission/risk_memo.md` | Risk limits, carry, and kill-switch memo |",
    "| `outputs/submission/catalyst_calendar.md` | 180-day catalyst timeline and thesis checks |",
    "| `outputs/submission/valuation_assumptions.md` | Valuation assumptions and scenario tables |",
    "| `outputs/submission/submission_readiness_checklist.md` | Submission hardening checklist |",
    "| `data/processed/valuation/peer_comps.csv` | Peer comparison (P/E, EV/EBITDA, ROIC) |",
    "| `data/processed/valuation/oil_hal_backtest.csv` | Oil vs HAL/Sieyuan backtest results |",
    "| `data/processed/valuation/sensitivity_summary.csv` | Sieyuan EPS sensitivity tables |",
    "| `data/processed/valuation/trader_analysis.csv` | Position sizing, carry, liquidity |",
    "| `outputs/charts/sensitivity_tornado.png` | EPS sensitivity tornado chart |",
    "| `outputs/charts/sensitivity_matrix_overseas_margin.png` | 2D sensitivity matrix |",
    "| `outputs/charts/signal_trends_timeseries.png` | Time-series signal trends chart |",
    "| `outputs/charts/oil_hal_correlation.png` | Oil-HAL correlation divergence chart |",
    "| `data/raw/text/DOC_Sieyuan_HKEX_Filing.txt` | 1.1M chars extracted from HKEX filing |",
    "",
])

report_text = "\n".join(report_lines)
Path("outputs/pipeline_report.md").write_text(report_text)
print("\n" + "="*60)
print("[SAVED] outputs/pipeline_report.md")
