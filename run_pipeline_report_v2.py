#!/usr/bin/env python3
"""Improved pipeline runner with better error handling and progress tracking."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os
import concurrent.futures
import json

sys.path.insert(0, str(Path(__file__).parent))

class PipelineRunner:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def run_step(self, name, cmd, critical=True):
        """Run a pipeline step with error handling."""
        print(f"\n{'='*60}")
        print(f"STEP: {name} {'[CRITICAL]' if critical else '[OPTIONAL]'}")
        print('='*60)
        
        step_start = datetime.now()
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            success = result.returncode == 0
            output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            error = result.stderr[-300:] if result.stderr else ''
            print(output)
            if error and not success:
                print(f"ERRORS: {error}")
        except subprocess.TimeoutExpired:
            success = False
            output = ""
            error = "TIMEOUT: Step exceeded 5 minutes"
            print(error)
        except Exception as e:
            success = False
            output = ""
            error = str(e)
            print(f"EXCEPTION: {error}")
            
        duration = (datetime.now() - step_start).total_seconds()
        
        self.results.append({
            "name": name, 
            "success": success, 
            "critical": critical,
            "output": output, 
            "error": error,
            "duration": duration
        })
        return success
    
    def run_inline_step(self, name, func, critical=True):
        """Run a Python function as a pipeline step."""
        print(f"\n{'='*60}")
        print(f"STEP: {name} {'[CRITICAL]' if critical else '[OPTIONAL]'}")
        print('='*60)
        
        step_start = datetime.now()
        try:
            output = func()
            success = True
            error = ""
            print(output[:2000] if len(output) > 2000 else output)
        except Exception as e:
            success = False
            output = ""
            error = str(e)
            print(f"EXCEPTION: {error}")
            
        duration = (datetime.now() - step_start).total_seconds()
        
        self.results.append({
            "name": name,
            "success": success,
            "critical": critical,
            "output": output,
            "error": error,
            "duration": duration
        })
        return success

def signal_tracker_step():
    """Run signal tracker analysis."""
    import pandas as pd
    from src.analysis import plan_format_signal_tracker, narrative_shift_analysis
    df = pd.read_csv('data/processed/classified_paragraphs.csv')
    tracker = plan_format_signal_tracker(df)
    output = ['=== SIGNAL TRACKER ===', tracker.to_string()]
    narrative = narrative_shift_analysis(df)
    output.append('\n=== NARRATIVE SHIFT ===')
    for k, v in narrative.items():
        output.append(f'  {k}: {v}')
    return '\n'.join(output)

def charts_step():
    """Generate charts."""
    os.makedirs('outputs/charts', exist_ok=True)
    from src.charts import create_signal_trends_timeseries
    import pandas as pd
    df = pd.read_csv('data/processed/classified_paragraphs.csv')
    create_signal_trends_timeseries(df, 'outputs/charts/signal_trends_timeseries.png')
    return 'Charts generated:\n- signal_trends_timeseries.png'

def main():
    runner = PipelineRunner()
    
    # Phase 1: Data Preparation (Critical)
    print("\n" + "="*60)
    print("PHASE 1: DATA PREPARATION")
    print("="*60)
    
    runner.run_step("Rebuild Index", 
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/rebuild_index.py")
    
    runner.run_step("Sanitize Classifications",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/sanitize_classifications.py")
    
    # Phase 2: Analysis
    print("\n" + "="*60)
    print("PHASE 2: ANALYSIS")
    print("="*60)
    
    runner.run_inline_step("Signal Tracker", signal_tracker_step)
    runner.run_step("Valuation", 
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/valuation.py")
    runner.run_step("Evidence Extraction",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/evidence_extractor.py")
    
    # Phase 3: Validation
    print("\n" + "="*60)
    print("PHASE 3: VALIDATION")
    print("="*60)
    
    runner.run_step("Blind Classification Validation",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/validation.py", critical=False)
    runner.run_step("Backtest Analysis",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/backtest.py", critical=False)
    runner.run_step("Signal-Return Analysis",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/signal_return_analysis.py", critical=False)
    
    # Phase 4: Charts & Reports
    print("\n" + "="*60)
    print("PHASE 4: CHARTS & REPORTS")
    print("="*60)
    
    runner.run_inline_step("Charts Generation", charts_step, critical=False)
    runner.run_step("Sensitivity Analysis",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/sensitivity.py", critical=False)
    runner.run_step("Data Quality Audit",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/data_quality.py", critical=False)
    
    # Phase 5: Final Outputs
    print("\n" + "="*60)
    print("PHASE 5: FINAL OUTPUTS")
    print("="*60)
    
    runner.run_step("Trader Analysis",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/trader_analysis.py")
    runner.run_step("Q&A Defense",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/qna_defense.py")
    runner.run_step("Submission Pack",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/submission_pack.py")
    runner.run_step("Deck Generation",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/deck_generator.py")
    runner.run_step("Generate Submission Report",
        "PYTHONPATH=/Users/skumyol/Documents/GitHub/ubs .venv/bin/python src/generate_submission_report.py")
    
    # Summary
    total_time = (datetime.now() - runner.start_time).total_seconds()
    passed = sum(1 for r in runner.results if r['success'])
    failed = sum(1 for r in runner.results if not r['success'])
    critical_failures = sum(1 for r in runner.results if not r['success'] and r['critical'])
    
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Total Steps: {len(runner.results)}")
    print(f"Passed: {passed} | Failed: {failed}")
    print(f"Critical Failures: {critical_failures}")
    print(f"Total Time: {total_time:.1f}s")
    
    if critical_failures > 0:
        print("\nCRITICAL FAILURES:")
        for r in runner.results:
            if not r['success'] and r['critical']:
                print(f"  - {r['name']}: {r['error'][:100]}")
    
    # Save JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_steps": len(runner.results),
        "passed": passed,
        "failed": failed,
        "critical_failures": critical_failures,
        "total_time": total_time,
        "steps": runner.results
    }
    Path("outputs/pipeline_report_v2.json").write_text(json.dumps(report, indent=2, default=str))
    print("\n[SAVED] outputs/pipeline_report_v2.json")
    
    return critical_failures == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
