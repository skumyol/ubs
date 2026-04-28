#!/usr/bin/env python3
"""Run the complete UBS pitch pipeline end-to-end.

Orchestrates:
1. Rebuild document index from raw text
2. Run analysis (signal tracker, narrative shift)
3. Build evidence pack
4. Fetch valuation data
5. Generate PPTX deck
6. Build Q&A defense doc

Assumes data has been gathered and classified (run data_gatherer + run_classifier_pitch first).
"""

import pandas as pd
from pathlib import Path
from src.config import (
    CLASSIFIED_PARAGRAPHS_PATH,
    CHARTS_DIR,
    OUTPUTS_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
)


def step(num, title):
    print(f"\n{'='*60}\nSTEP {num}: {title}\n{'='*60}")


def main():
    print("=" * 60)
    print("UBS PITCH PIPELINE — FULL RUN")
    print("=" * 60)

    # --- Step 1: Load classifications ---
    step(1, "Load classified paragraphs")
    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        print(f"[ERROR] {CLASSIFIED_PARAGRAPHS_PATH} not found.")
        print("Run first: python -m src.run_classifier_pitch")
        return

    try:
        classified_df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    except pd.errors.EmptyDataError:
        print("[ERROR] Classifications file empty")
        return

    print(f"Loaded {len(classified_df)} classified paragraphs")

    # --- Step 2: Analysis ---
    step(2, "Run analysis (signal tracker, narrative shift)")
    from src.analysis import (
        plan_format_signal_tracker,
        narrative_shift_analysis,
        category_counts,
        build_signal_tracker,
    )

    signal_tracker_plan = plan_format_signal_tracker(classified_df)
    narrative = narrative_shift_analysis(classified_df)
    counts = category_counts(classified_df)
    full_tracker = build_signal_tracker(classified_df)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    signal_tracker_plan.to_csv(TABLES_DIR / "signal_tracker_plan_format.csv", index=False)
    counts.to_csv(TABLES_DIR / "category_counts.csv", index=False)
    full_tracker.to_csv(TABLES_DIR / "ai_signal_tracker.csv", index=False)

    print(f"Signal tracker (plan format):")
    print(signal_tracker_plan[["signal_cluster", "Grid Equipment", "Oilfield Services"]].to_string(index=False))
    print(f"\nNarrative shift: {narrative['interpretation']}")
    print(f"  Thesis score: {narrative['thesis_support_score']}")
    print(f"  Grid share: {narrative['grid_signal_share']*100:.0f}%  Oil share: {narrative['oil_signal_share']*100:.0f}%")

    # --- Step 3: Charts ---
    step(3, "Regenerate charts")
    from src.charts import (
        create_category_bar_chart,
        create_sentiment_comparison,
        create_signal_heatmap,
        create_long_short_matrix_table,
    )
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Filter Not Relevant for charts
    chart_df = classified_df[classified_df["category"] != "Not Relevant"].copy()

    try:
        create_category_bar_chart(counts, str(CHARTS_DIR / "energy_signal_frequency.png"))
        print("  [OK] energy_signal_frequency.png")
    except Exception as e:
        print(f"  [SKIP] category bar chart: {e}")

    try:
        create_sentiment_comparison(chart_df, str(CHARTS_DIR / "sentiment_comparison.png"))
        print("  [OK] sentiment_comparison.png")
    except Exception as e:
        print(f"  [SKIP] sentiment comparison: {e}")

    try:
        if len(full_tracker) > 0:
            create_signal_heatmap(full_tracker, str(CHARTS_DIR / "signal_heatmap.png"))
            print("  [OK] signal_heatmap.png")
    except Exception as e:
        print(f"  [SKIP] signal heatmap: {e}")

    try:
        create_long_short_matrix_table(str(CHARTS_DIR / "long_short_matrix.png"))
        print("  [OK] long_short_matrix.png")
    except Exception as e:
        print(f"  [SKIP] long/short matrix: {e}")

    # --- Step 4: Evidence Pack ---
    step(4, "Extract killer quotes (evidence pack)")
    from src.evidence_extractor import build_evidence_pack
    evidence_pack = build_evidence_pack(
        classified_df,
        TABLES_DIR / "evidence_pack",
    )
    total_quotes = sum(len(s["quotes"]) for s in evidence_pack.values())
    print(f"  {total_quotes} evidence quotes across {len(evidence_pack)} slides")

    # --- Step 5: Valuation ---
    step(5, "Fetch market data & build valuation")
    from src.valuation import save_valuation_outputs
    val_dir = PROCESSED_DIR / "valuation"
    try:
        valuation_summary = save_valuation_outputs(val_dir)
        print(f"  Pair spread return: {valuation_summary.get('pair_spread_return')}%")
    except Exception as e:
        print(f"  [WARN] Valuation failed: {e}")
        valuation_summary = None

    # --- Step 6: Data Quality Audit ---
    step(6, "Run data quality audit")
    from src.data_quality import build_data_quality_report
    quality_summary = build_data_quality_report()

    # --- Step 7: Submission Pack ---
    step(7, "Build submission artifacts")
    from src.submission_pack import build_submission_pack
    submission_outputs = build_submission_pack()

    # --- Step 8: Q&A Defense ---
    step(8, "Generate Q&A defense document")
    from src.qna_defense import build_qna_doc
    qna_path = Path(__file__).parent.parent / "docs" / "qna_defense.md"

    val_dict = None
    pair_path = val_dir / "pair_trade_summary.csv"
    if pair_path.exists():
        pair = pd.read_csv(pair_path).iloc[0].to_dict()
        val_dict = {
            "long_expected_return": pair.get("long_expected_return_pct", 0),
            "short_expected_return": pair.get("short_expected_move_pct", 0),
            "pair_spread_return": pair.get("pair_spread_return_pct", 0),
        }

    build_qna_doc(classified_df, val_dict, narrative, qna_path)

    # --- Step 9: PPTX Deck ---
    step(9, "Generate PPTX deck")
    from src.deck_generator import build_deck
    import json

    evidence_json = TABLES_DIR / "evidence_pack.json"
    evidence_pack_loaded = None
    if evidence_json.exists():
        with open(evidence_json) as f:
            evidence_pack_loaded = json.load(f)

    peer_comps_df = pd.read_csv(val_dir / "peer_comps.csv") if (val_dir / "peer_comps.csv").exists() else None
    long_sc = pd.read_csv(val_dir / "long_scenarios.csv") if (val_dir / "long_scenarios.csv").exists() else None
    short_sc = pd.read_csv(val_dir / "short_scenarios.csv") if (val_dir / "short_scenarios.csv").exists() else None

    deck_path = Path(__file__).parent.parent / "deck" / "UBS_Pitch_Deck_AUTO.pptx"
    build_deck(
        classified_df=classified_df,
        signal_tracker_df=signal_tracker_plan,
        evidence_pack=evidence_pack_loaded,
        valuation_summary=val_dict,
        peer_comps_df=peer_comps_df,
        long_scenarios_df=long_sc,
        short_scenarios_df=short_sc,
        charts_dir=CHARTS_DIR,
        output_path=deck_path,
        narrative_shift=narrative,
    )

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"\nDeliverables:")
    print(f"  📊 PPTX Deck:        {deck_path}")
    print(f"  📝 Q&A Defense:      {qna_path}")
    print(f"  💬 Evidence Pack:    {TABLES_DIR / 'evidence_pack.md'}")
    print(f"  ✅ Data Quality:     {quality_summary.get('report_path')}")
    print(f"  📦 Submission Pack:  {submission_outputs.get('readiness_checklist')}")
    print(f"  📈 Signal Tracker:   {TABLES_DIR / 'signal_tracker_plan_format.csv'}")
    print(f"  💰 Peer Comps:       {val_dir / 'peer_comps.csv'}")
    print(f"  🎯 Charts:           {CHARTS_DIR}")

    if narrative:
        print(f"\n🎯 Thesis score: {narrative['thesis_support_score']} — {narrative['interpretation']}")
    if val_dict:
        print(f"💵 Pair spread expected return: {val_dict['pair_spread_return']}%")


if __name__ == "__main__":
    main()
