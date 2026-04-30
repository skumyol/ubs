#!/usr/bin/env python3
"""Single entrypoint for the UBS pitch pipeline.

This orchestrator owns the full execution path:
1. Refresh raw document index and LLM classifications
2. Run valuation, risk, backtest, and sensitivity outputs
3. Generate LLM-assisted thesis, evidence, and Q&A content
4. Build submission report, submission pack, and PPTX deck

The shell wrapper `run_full_pipeline.sh` should be treated as the only
user-facing execution surface. Everything else is a module behind it.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import (
    CLASSIFIED_PARAGRAPHS_PATH,
    CHARTS_DIR,
    DOCUMENT_INDEX_PATH,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
)
from src.pair_config import (
    DECK_SUBTITLE,
    DECK_TITLE,
    LONG_LEG,
    SHORT_LEG,
    VALUATION_FALLBACK,
)


def step(num: str, title: str) -> None:
    print(f"\n{'=' * 60}\nSTEP {num}: {title}\n{'=' * 60}")


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _clear_path(path: Path) -> None:
    """Remove a file or directory if it exists."""
    try:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    except Exception as exc:
        print(f"[WARN] Could not clear {path}: {exc}")


def _load_pair_summary(val_dir: Path) -> dict:
    pair_path = val_dir / "pair_trade_summary.csv"
    if pair_path.exists():
        try:
            pair = pd.read_csv(pair_path).iloc[0].to_dict()
            return {
                "long_expected_return": pair.get("long_expected_return_pct", VALUATION_FALLBACK["long_expected_return"]),
                "short_expected_return": pair.get("short_expected_move_pct", VALUATION_FALLBACK["short_expected_return"]),
                "pair_spread_return": pair.get("pair_spread_return_pct", VALUATION_FALLBACK["pair_spread_return"]),
            }
        except Exception:
            pass
    return dict(VALUATION_FALLBACK)


def _print_summary(deck_path: Path, qna_path: Path, val_dir: Path, quality_summary: Optional[dict], narrative: Optional[dict]) -> None:
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print("\nDeliverables:")
    print(f"  PPTX Deck:        {deck_path}")
    print(f"  Q&A Defense:      {qna_path}")
    print(f"  Submission Report: {OUTPUTS_DIR / 'submission_report.md'}")
    print(f"  Evidence Pack:    {TABLES_DIR / 'evidence_pack.md'}")
    print(f"  Submission Pack:  {OUTPUTS_DIR / 'submission' / 'submission_readiness_checklist.md'}")
    if quality_summary:
        print(f"  Data Quality:     {quality_summary.get('report_path')}")
    print(f"  Charts:           {CHARTS_DIR}")
    print(f"  Pair:             {LONG_LEG.name} / {SHORT_LEG.name}")
    if narrative:
        print(f"\nThesis score: {narrative.get('thesis_support_score', 'N/A')} — {narrative.get('interpretation', 'N/A')}")


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the UBS pitch pipeline end-to-end.")
    parser.add_argument("--skip-data-fetch", action="store_true", help="Skip market data refresh and text reclassification.")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM content generation.")
    parser.add_argument("--skip-deck", action="store_true", help="Skip PPTX deck generation.")
    args = parser.parse_args(argv)

    print("=" * 60)
    print("UBS ENERGY TRANSITION PIPELINE")
    print("=" * 60)
    print(f"Long: {LONG_LEG.name} ({LONG_LEG.ticker})")
    print(f"Short: {SHORT_LEG.name} ({SHORT_LEG.ticker})")
    print(f"Deck title: {DECK_TITLE}")
    print(f"Subtitle: {DECK_SUBTITLE}")

    # Step 0: Refresh text inputs and classifications if requested.
    if not args.skip_data_fetch:
        step("0", "Refresh document index and classifications")
        # Clear stale artifacts first so the rerun is guaranteed to rebuild
        # from the active Dongfang/Jereh thesis instead of reusing old outputs.
        _clear_path(CLASSIFIED_PARAGRAPHS_PATH)
        _clear_path(TABLES_DIR / "evidence_pack.json")
        _clear_path(TABLES_DIR / "evidence_pack.md")
        _clear_path(TABLES_DIR / "llm_generated")
        _clear_path(OUTPUTS_DIR / "submission")
        _clear_path(PROCESSED_DIR / "valuation")

        try:
            from src.data_gatherer import main as data_gatherer_main

            data_gatherer_main()
        except Exception as exc:
            print(f"[WARN] data_gatherer failed: {exc}")

        try:
            from src.rebuild_index import rebuild_index, rebuild_paragraph_dataset

            rebuild_index()
            rebuild_paragraph_dataset()
        except Exception as exc:
            print(f"[WARN] rebuild_index failed: {exc}")

        print(f"[OK] Cleared old classifications: {CLASSIFIED_PARAGRAPHS_PATH}")

        try:
            from src.run_classifier_pitch import main as run_classifier_pitch_main

            run_classifier_pitch_main()
        except Exception as exc:
            print(f"[WARN] run_classifier_pitch failed: {exc}")

    # Step 1: Load classifications.
    step("1", "Load classified paragraphs")
    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        print(f"[ERROR] {CLASSIFIED_PARAGRAPHS_PATH} not found.")
        print("Run the classifier step first or allow the pipeline to refresh data.")
        return

    try:
        classified_df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    except pd.errors.EmptyDataError:
        print("[ERROR] Classifications file is empty.")
        return

    print(f"Loaded {len(classified_df)} classified paragraphs")

    # Step 2: Analysis and charting.
    step("2", "Run analysis and regenerate charts")
    from src.analysis import build_signal_tracker, category_counts, narrative_shift_analysis, plan_format_signal_tracker
    from src.charts import (
        create_category_bar_chart,
        create_long_short_matrix_table,
        create_sentiment_comparison,
        create_signal_heatmap,
        create_signal_trends_timeseries,
    )
    from src.data_quality import build_data_quality_report

    signal_tracker_plan = plan_format_signal_tracker(classified_df)
    narrative = narrative_shift_analysis(classified_df)
    counts = category_counts(classified_df)
    full_tracker = build_signal_tracker(classified_df)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    signal_tracker_plan.to_csv(TABLES_DIR / "signal_tracker_plan_format.csv", index=False)
    counts.to_csv(TABLES_DIR / "category_counts.csv", index=False)
    full_tracker.to_csv(TABLES_DIR / "ai_signal_tracker.csv", index=False)

    chart_df = classified_df[classified_df["category"] != "Not Relevant"].copy()
    create_category_bar_chart(counts, str(CHARTS_DIR / "energy_signal_frequency.png"))
    create_sentiment_comparison(chart_df, str(CHARTS_DIR / "sentiment_comparison.png"))
    if len(full_tracker) > 0:
        create_signal_heatmap(full_tracker, str(CHARTS_DIR / "signal_heatmap.png"))
    create_long_short_matrix_table(str(CHARTS_DIR / "long_short_matrix.png"))
    if "date" in classified_df.columns:
        create_signal_trends_timeseries(classified_df, str(CHARTS_DIR / "signal_trends_timeseries.png"))
    else:
        print("[WARN] Skipping signal trends chart: classified data has no date column")

    print(f"Signal tracker built with {len(signal_tracker_plan)} clusters")
    print(f"Narrative shift: {narrative.get('interpretation', 'N/A')}")

    # Step 3: Evidence pack.
    step("3", "Extract evidence pack")
    from src.evidence_extractor import build_evidence_pack

    evidence_pack = build_evidence_pack(classified_df, TABLES_DIR / "evidence_pack")
    print(f"Generated evidence for {len(evidence_pack)} slides")

    evidence_json = TABLES_DIR / "evidence_pack.json"
    evidence_pack_loaded = None
    if evidence_json.exists():
        with open(evidence_json, "r", encoding="utf-8") as f:
            evidence_pack_loaded = json.load(f)

    # Step 4: Valuation and risk.
    step("4", "Build valuation, trader, backtest, and sensitivity")
    from src.valuation import save_valuation_outputs
    from src.trader_analysis import main as run_trader_analysis
    from src.backtest import main as run_backtest
    from src.sensitivity import main as run_sensitivity_analysis

    val_dir = PROCESSED_DIR / "valuation"
    val_dir.mkdir(parents=True, exist_ok=True)
    valuation_summary = _load_pair_summary(val_dir)

    try:
        valuation_summary = save_valuation_outputs(val_dir)
    except Exception as exc:
        print(f"[WARN] Valuation failed, using fallback values: {exc}")

    try:
        run_trader_analysis()
    except Exception as exc:
        print(f"[WARN] Trader analysis failed: {exc}")

    try:
        run_backtest()
    except Exception as exc:
        print(f"[WARN] Backtest failed: {exc}")

    try:
        run_sensitivity_analysis()
    except Exception as exc:
        print(f"[WARN] Sensitivity analysis failed: {exc}")

    # Step 5: Data quality.
    step("5", "Run data quality audit")
    quality_summary = build_data_quality_report()

    # Step 6: LLM-assisted content generation.
    if not args.skip_llm:
        step("6", "Generate LLM-assisted content")
        from src.llm_content_generator import save_llm_outputs

        try:
            llm_outputs = save_llm_outputs()
            print(f"Generated {len(llm_outputs)} LLM content artifacts")
        except Exception as exc:
            print(f"[WARN] LLM content generation failed: {exc}")

    # Step 7: Submission pack and report.
    step("7", "Build submission pack and report")
    from src.submission_pack import build_submission_pack
    from src.generate_submission_report import main as generate_submission_report_main
    from src.qna_defense import build_qna_doc

    submission_outputs = build_submission_pack()
    generate_submission_report_main()

    qna_path = Path(__file__).parent.parent / "docs" / "qna_defense.md"
    build_qna_doc(classified_df, valuation_summary, narrative, qna_path, evidence_pack_path=evidence_json)

    # Step 8: Deck generation.
    deck_path = Path(__file__).parent.parent / "deck" / "UBS_Pitch_Deck_AUTO.pptx"
    if not args.skip_deck:
        step("8", "Generate PPTX deck")
        from src.deck_generator import build_deck

        peer_comps_df = _safe_read_csv(val_dir / "peer_comps.csv")
        dcf_df = _safe_read_csv(val_dir / "dcf_cross_check.csv")
        long_sc = _safe_read_csv(val_dir / "long_scenarios.csv")
        short_sc = _safe_read_csv(val_dir / "short_scenarios.csv")

        build_deck(
            classified_df=classified_df,
            signal_tracker_df=signal_tracker_plan,
            evidence_pack=evidence_pack_loaded,
            valuation_summary=valuation_summary,
            peer_comps_df=peer_comps_df if not peer_comps_df.empty else None,
            dcf_df=dcf_df if not dcf_df.empty else None,
            long_scenarios_df=long_sc if not long_sc.empty else None,
            short_scenarios_df=short_sc if not short_sc.empty else None,
            charts_dir=CHARTS_DIR,
            output_path=deck_path,
            narrative_shift=narrative,
        )

    _print_summary(deck_path, qna_path, val_dir, quality_summary, narrative)
    if submission_outputs:
        print(f"Submission pack: {submission_outputs.get('readiness_checklist', 'N/A')}")


if __name__ == "__main__":
    main()
