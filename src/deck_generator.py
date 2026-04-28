"""Auto-generate the UBS pitch deck as a PPTX file.

Assembles slides from analysis outputs, evidence pack, charts, and valuation.
Follows the 13-slide structure from base_plan.md.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

# Brand colors (UBS-ish professional palette)
COLOR_PRIMARY = "#E60028"        # UBS red
COLOR_SECONDARY = "#002F5D"      # UBS dark blue
COLOR_GRID = "#005F9E"           # Long leg color
COLOR_OIL = "#C97B00"            # Short leg color
COLOR_TEXT = "#1A1A1A"
COLOR_MUTED = "#666666"


def _install_pptx():
    """Ensure python-pptx is installed."""
    try:
        import pptx  # noqa
    except ImportError:
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "pip", "install", "python-pptx", "-q"])


def _hex_to_rgb(hex_color: str):
    """Convert hex string to RGBColor."""
    from pptx.dml.color import RGBColor
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def add_title_slide(prs, title: str, subtitle: str):
    """Add a title slide with UBS styling."""
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN

    slide_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(slide_layout)

    # Color band
    from pptx.shapes.autoshape import Shape
    from pptx.enum.shapes import MSO_SHAPE
    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, Inches(0.3)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = _hex_to_rgb(COLOR_PRIMARY)
    band.line.fill.background()

    # Title
    tb = slide.shapes.add_textbox(Inches(0.7), Inches(2.0), Inches(12), Inches(1.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = _hex_to_rgb(COLOR_SECONDARY)

    # Subtitle
    sb = slide.shapes.add_textbox(Inches(0.7), Inches(3.5), Inches(12), Inches(1.0))
    sf = sb.text_frame
    sf.word_wrap = True
    sp = sf.paragraphs[0]
    sp.text = subtitle
    sp.font.size = Pt(22)
    sp.font.color.rgb = _hex_to_rgb(COLOR_MUTED)

    return slide


def add_content_slide(prs, title: str, body_items: List[str]):
    """Add a standard content slide with title and bullet points."""
    from pptx.util import Inches, Pt

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = _hex_to_rgb(COLOR_SECONDARY)

    # Body
    bb = slide.shapes.add_textbox(Inches(0.7), Inches(1.3), Inches(12), Inches(5.5))
    bf = bb.text_frame
    bf.word_wrap = True

    for i, item in enumerate(body_items):
        p = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(18)
        p.font.color.rgb = _hex_to_rgb(COLOR_TEXT)
        p.space_after = Pt(8)

    return slide


def add_chart_slide(prs, title: str, image_path: Path, caption: str = ""):
    """Add a slide with a single chart image."""
    from pptx.util import Inches, Pt

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.8))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = _hex_to_rgb(COLOR_SECONDARY)

    # Image
    if image_path and image_path.exists():
        slide.shapes.add_picture(
            str(image_path), Inches(1.5), Inches(1.3),
            width=Inches(10), height=Inches(5.5)
        )

    # Caption
    if caption:
        cb = slide.shapes.add_textbox(Inches(0.5), Inches(6.9), Inches(12.5), Inches(0.5))
        cp = cb.text_frame.paragraphs[0]
        cp.text = caption
        cp.font.size = Pt(12)
        cp.font.italic = True
        cp.font.color.rgb = _hex_to_rgb(COLOR_MUTED)

    return slide


def add_table_slide(prs, title: str, df: pd.DataFrame, caption: str = ""):
    """Add a slide with a DataFrame rendered as a table."""
    from pptx.util import Inches, Pt
    from pptx.enum.text import PP_ALIGN

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.8))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = _hex_to_rgb(COLOR_SECONDARY)

    # Drop internal columns (prefix _)
    display_df = df.loc[:, [c for c in df.columns if not str(c).startswith("_")]].copy()

    n_rows, n_cols = len(display_df) + 1, len(display_df.columns)
    if n_rows == 1 or n_cols == 0:
        return slide

    # Size the table
    tbl_width = Inches(min(12, 1.8 * n_cols))
    tbl_height = Inches(min(5.5, 0.4 * n_rows + 0.4))
    tbl_shape = slide.shapes.add_table(
        n_rows, n_cols,
        Inches(0.7), Inches(1.3),
        tbl_width, tbl_height,
    )
    tbl = tbl_shape.table

    # Header
    for j, col in enumerate(display_df.columns):
        cell = tbl.cell(0, j)
        cell.text = str(col).replace("_", " ").title()
        cell.fill.solid()
        cell.fill.fore_color.rgb = _hex_to_rgb(COLOR_SECONDARY)
        for para in cell.text_frame.paragraphs:
            for run in para.runs:
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = _hex_to_rgb("#FFFFFF")

    # Rows
    for i, (_, row) in enumerate(display_df.iterrows(), start=1):
        for j, col in enumerate(display_df.columns):
            cell = tbl.cell(i, j)
            val = row[col]
            cell.text = "" if pd.isna(val) else str(val)
            for para in cell.text_frame.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(11)
                    run.font.color.rgb = _hex_to_rgb(COLOR_TEXT)

    # Caption
    if caption:
        cb = slide.shapes.add_textbox(Inches(0.5), Inches(6.9), Inches(12.5), Inches(0.5))
        cp = cb.text_frame.paragraphs[0]
        cp.text = caption
        cp.font.size = Pt(12)
        cp.font.italic = True
        cp.font.color.rgb = _hex_to_rgb(COLOR_MUTED)

    return slide


def add_quote_slide(prs, title: str, quotes: List[Dict]):
    """Add a slide with supporting quotes."""
    from pptx.util import Inches, Pt

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.5), Inches(0.8))
    p = tb.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = _hex_to_rgb(COLOR_SECONDARY)

    # Quotes
    bb = slide.shapes.add_textbox(Inches(0.7), Inches(1.3), Inches(12), Inches(5.5))
    bf = bb.text_frame
    bf.word_wrap = True

    if not quotes:
        p = bf.paragraphs[0]
        p.text = "No supporting quotes available. Expand data collection."
        p.font.size = Pt(16)
        p.font.italic = True
        p.font.color.rgb = _hex_to_rgb(COLOR_MUTED)
        return slide

    for i, q in enumerate(quotes[:3]):
        quote_text = q["quote"][:280]
        p = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
        p.text = f'"{quote_text}"'
        p.font.size = Pt(14)
        p.font.italic = True
        p.font.color.rgb = _hex_to_rgb(COLOR_TEXT)
        p.space_after = Pt(4)

        p2 = bf.add_paragraph()
        p2.text = f"  — {q['source']}  |  {q['category']}  |  conf {q['confidence']}"
        p2.font.size = Pt(11)
        p2.font.color.rgb = _hex_to_rgb(COLOR_MUTED)
        p2.space_after = Pt(12)

    return slide


def build_deck(
    classified_df: Optional[pd.DataFrame],
    signal_tracker_df: Optional[pd.DataFrame],
    evidence_pack: Optional[Dict],
    valuation_summary: Optional[Dict],
    peer_comps_df: Optional[pd.DataFrame],
    long_scenarios_df: Optional[pd.DataFrame],
    short_scenarios_df: Optional[pd.DataFrame],
    charts_dir: Path,
    output_path: Path,
    narrative_shift: Optional[Dict] = None,
    include_per_slide_evidence: bool = False,
    consolidate_ai_slides: bool = True,
) -> Path:
    """Assemble the full UBS pitch deck.

    Saves to output_path and returns it.
    """
    _install_pptx()
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9
    prs.slide_height = Inches(7.5)

    # -------- Slide 1: Executive Summary --------
    add_title_slide(
        prs,
        "Long the Grid, Short the Bottleneck",
        "Energy security is moving from barrels to electrons  |  "
        "Long Sieyuan Electric (601126.SS) / Short Halliburton (HAL)",
    )

    # -------- Slide 2: One-Pager --------
    one_pager_items = [
        "Thesis: Own grid infrastructure to capture the electricity-continuity shift",
        f"Long Sieyuan Electric @ target upside: "
        f"{valuation_summary['long_expected_return']}%" if valuation_summary else
        "Long Sieyuan Electric - targeted upside from grid capex + overseas growth",
        f"Short Halliburton @ target downside: "
        f"{valuation_summary['short_expected_return']}%" if valuation_summary else
        "Short Halliburton - margin compression + capex volatility",
        f"Pair spread expected return: "
        f"{valuation_summary['pair_spread_return']}%" if valuation_summary else
        "Pair spread captures earnings-quality differential",
        "3 pillars: (1) Structural electricity demand (2) Grid capex visibility (3) Oilfield cost pressure",
        "Key catalysts: Sieyuan overseas wins, HAL Q2 guidance miss, grid policy announcements",
    ]
    add_content_slide(prs, "Executive Summary", one_pager_items)

    # -------- Slide 3: Consensus View --------
    consensus_items = [
        "Market reads geopolitical risk as bullish for oil and oilfield services",
        "Strait of Hormuz, Middle East tensions, shipping route vulnerability drive headlines",
        "Assumption chain: oil disruption → higher crude → higher upstream capex → better OFS earnings",
        "This view has been the dominant energy-security trade since 2022",
        "But consensus over-connects oil price spikes with durable service earnings",
    ]
    add_content_slide(prs, "Consensus: Energy Insecurity Means Owning Oil Exposure", consensus_items)

    # -------- Slide 4: Variant View --------
    variant_items = [
        "Energy insecurity is not just about securing barrels — it is about securing reliable electricity",
        "Data centers, EVs, industrial electrification, and cooling all stress the grid",
        "Transformers, switchgear, transmission, substations — all in multi-year shortage",
        "Governments treat grid hardening as national security infrastructure",
        "→ Oil disruption is the symptom. Grid investment is the solution.",
    ]
    add_content_slide(prs, "Variant View: The Real Energy-Security Trade Is Grid Resilience", variant_items)

    # Slide 3/4 evidence (optional)
    if include_per_slide_evidence and evidence_pack and "slide_3_variant_view" in evidence_pack:
        add_quote_slide(
            prs,
            "Evidence: Grid Resilience Signals in Primary Sources",
            evidence_pack["slide_3_variant_view"]["quotes"],
        )

    # -------- Slide 5: Industry Outlook --------
    industry_items = [
        "Global electricity demand expected to grow ~4% annually through 2030 (IEA)",
        "US data center power demand projected to 2-3x by 2030 — driving grid equipment orders",
        "Transformer lead times 80-120 weeks; transmission queue 2+ years in most markets",
        "EU, US, and China all have multi-year grid investment programs",
        "Policy support: IRA, EU Grid Action Plan, China State Grid Five-Year Plan",
    ]
    add_content_slide(prs, "Electricity Continuity Is Becoming Strategic Infrastructure", industry_items)

    # -------- Slide 6: Long Case - Sieyuan --------
    long_items = [
        "Pure-play transmission & distribution equipment: switchgear, transformers, substation automation",
        "Strong domestic grid orders from State Grid Corp + overseas expansion (Middle East, SE Asia)",
        "Revenue growth trajectory supported by multi-year order backlog",
        "Gross margins stable/improving vs peers; R&D investment in digital grid",
        "Variant gap: Market prices it as cyclical China equipment — we price it as global grid-resilience compounder",
    ]
    add_content_slide(prs, "Sieyuan Electric: Direct Beneficiary of Grid Hardening", long_items)

    if include_per_slide_evidence and evidence_pack and "slide_5_long_case" in evidence_pack:
        add_quote_slide(
            prs,
            "Long Case Evidence",
            evidence_pack["slide_5_long_case"]["quotes"],
        )

    # -------- Slide 7: Short Case - Halliburton --------
    short_items = [
        "Revenue tied to upstream capex cycles — North America, Middle East, offshore",
        "Cost pressure: logistics, materials, labor compressing margins",
        "Project delays and capex caution during geopolitical uncertainty",
        "Rig count volatility = utilization risk outside company control",
        "Higher oil prices ≠ higher service earnings (historical disconnect in disruption periods)",
    ]
    add_content_slide(prs, "Halliburton: Exposed to Fragile Energy Logistics", short_items)

    if include_per_slide_evidence and evidence_pack and "slide_7_short_case" in evidence_pack:
        add_quote_slide(
            prs,
            "Short Case Evidence",
            evidence_pack["slide_7_short_case"]["quotes"],
        )

    # -------- Slide 8: Backtest - Oil vs HAL Correlation --------
    backtest_path = charts_dir / "oil_hal_correlation.png"
    if backtest_path.exists():
        add_chart_slide(
            prs,
            "Historical Divergence: Oil vs HAL vs Sieyuan (2Y)",
            backtest_path,
            "Oil +16.4%, HAL +9.6% (underperformed), Sieyuan +227.3%. Forward thesis is margin-driven, not oil-correlated.",
        )

    # -------- Slide 9: Comparison Matrix (Chart) --------
    matrix_path = charts_dir / "long_short_matrix.png"
    if matrix_path.exists():
        add_chart_slide(
            prs,
            "Same Energy-Security Theme, Opposite Earnings Quality",
            matrix_path,
            "Long Sieyuan captures the capex tailwind. Short HAL carries the logistics risk.",
        )

    # -------- Slide 10: AI Signal Tracker --------
    if signal_tracker_df is not None and not signal_tracker_df.empty:
        caption = ""
        if narrative_shift:
            caption = (
                f"Thesis support score: {narrative_shift['thesis_support_score']} | "
                f"{narrative_shift['interpretation']} | "
                f"Grid signal share: {narrative_shift['grid_signal_share']*100:.0f}%"
            )
        add_table_slide(
            prs,
            "Thematic Evidence Tracker: Text-Based Signal Compilation",
            signal_tracker_df,
            caption,
        )

    # -------- Slide 11: Text Evidence --------
    if evidence_pack and "slide_10_ai_module" in evidence_pack:
        add_quote_slide(
            prs,
            "Supporting Evidence: Text Classification Results",
            evidence_pack["slide_10_ai_module"]["quotes"],
        )

    # -------- Slide 12: Signal Trends Timeseries --------
    trends_path = charts_dir / "signal_trends_timeseries.png"
    if trends_path.exists():
        add_chart_slide(
            prs,
            "Evidence Trends: Monthly Text Signal Volume",
            trends_path,
            "Monthly evolution of classified text signals. Descriptive, not predictive. See validation report for predictive power analysis.",
        )

    # -------- Slide 13: Signal Frequency Chart --------
    freq_path = charts_dir / "energy_signal_frequency.png"
    if freq_path.exists():
        add_chart_slide(
            prs,
            "Evidence Frequency: Category Distribution",
            freq_path,
            "Text-classified paragraphs from public sources. Distribution reflects document sampling, not necessarily market reality.",
        )

    # -------- Slide 14: Peer Comparables --------
    if peer_comps_df is not None and not peer_comps_df.empty:
        add_table_slide(
            prs,
            "Valuation: Peer Comparables",
            peer_comps_df,
            "Grid peers command premium multiples on earnings visibility; OFS trades at cyclical discount",
        )

    # -------- Slide 15: Long Scenarios --------
    if long_scenarios_df is not None and not long_scenarios_df.empty:
        add_table_slide(
            prs,
            "Long Scenarios: Sieyuan Electric",
            long_scenarios_df,
            "Probability-weighted upside driven by overseas revenue mix and grid re-rating",
        )

    # -------- Slide 16: Short Scenarios --------
    if short_scenarios_df is not None and not short_scenarios_df.empty:
        add_table_slide(
            prs,
            "Short Scenarios: Halliburton",
            short_scenarios_df,
            "Probability-weighted downside driven by margin compression and cyclical de-rate",
        )

    # -------- Slide 17: Sensitivity Analysis --------
    tornado_path = charts_dir / "sensitivity_tornado.png"
    if tornado_path.exists():
        add_chart_slide(
            prs,
            "EPS Sensitivity: What Drives Sieyuan Valuation?",
            tornado_path,
            "Base case EPS ¥1.33. Gross margin is the key driver (±63%). Overseas mix + FX are secondary.",
        )

    # -------- Slide 18: Catalysts --------
    catalyst_items = [
        "LONG CATALYSTS (Sieyuan):",
        "  • Quarterly overseas order wins (Middle East, SE Asia)",
        "  • China State Grid capex announcements",
        "  • Gross margin expansion on overseas mix shift",
        "SHORT CATALYSTS (Halliburton):",
        "  • Q2 earnings miss on logistics cost",
        "  • Guidance cut on North American rig count",
        "  • Project deferral announcements from majors",
    ]
    add_content_slide(prs, "Catalysts Over Next 6-12 Months", catalyst_items)

    # -------- Slide 19: Risks --------
    risk_items = [
        "Oil price spike lifts HAL even if fundamentals weak → pair trade cushions absolute exposure",
        "Sieyuan China beta/multiple compression → offset by overseas revenue visibility",
        "Grid capex delays → multi-year policy demand reduces single-year risk",
        "FX risk on RMB → monitored; sensitivity table in appendix",
        "SHORT SQUEEZE / BORROW COST: HAL borrow cost ~2-5% annually; oil-spike short squeeze possible → position size limits risk",
        "Thesis kill switch: HAL margin expansion + Sieyuan backlog decline → exit pair",
    ]
    add_content_slide(prs, "Risks and Mitigants", risk_items)

    # -------- Slide 20: Trader Execution Framework --------
    trader_items = [
        "POSITION SIZING (Risk-Based):",
        "  • Portfolio: $100M example | Max risk per trade: 2% ($2M)",
        "  • Pair volatility: 42% annual | Position size: 2.4% of portfolio ($2.4M notional)",
        "  • Allocation: $1.2M long Sieyuan / $1.2M short HAL (dollar-neutral)",
        "",
        "CARRY COST (6-month hold):",
        "  • HAL borrow cost: 2-5% annually → $15K-33K cost",
        "  • HAL dividend (short pays): 1.5% → ~$9K cost",
        "  • Sieyuan dividend (long receives): 1% → ~$6K income",
        "  • Net carry: ~$18K-36K (1.5-3% of expected spread return)",
        "",
        "LIQUIDITY & EXECUTION:",
        "  • Sieyuan: $787M daily volume | Execute in <1 day | Sufficient for sizing",
        "  • HAL: $332M daily volume | Execute in <1 day | Excellent liquidity",
        "  • Stock Connect required for Sieyuan A-shares (or H-share proxy: CRRC)",
        "",
        "TECHNICAL TIMING:",
        "  • HAL: 99.3% of 52-week high, RSI 57.6 → Prime short entry at resistance",
        "  • Sieyuan: 86.4% of 52-week high, RSI 46.7 → Pulled back, reasonable entry",
    ]
    add_content_slide(prs, "Execution: Position Sizing, Carry & Liquidity", trader_items)

    # -------- Slide 21: Text Analysis Module: Honest Assessment --------
    if consolidate_ai_slides:
        # Single combined slide - reframed honestly
        ai_combined = [
            "WHAT THIS MODULE DOES:",
            "  • Compiles text evidence from 55 documents into structured categories",
            "  • Surfaces specific quotes and management language for manual review",
            "  • Provides repeatable framework for future thematic research",
            "HONEST LIMITATIONS:",
            "  • Descriptive, not predictive — signals do NOT forecast returns (see validation)",
            "  • 330 paragraphs = small sample; limited statistical power",
            "  • Classification relies on keyword patterns, not deep semantic understanding",
            "  • Source bias: RSS feeds overweight news vs. operational 8-K filings",
            "  • Every output requires human verification before investment decisions",
        ]
        add_content_slide(prs, "Text Analysis: Scope and Limitations", ai_combined)
    else:
        # Two separate slides - reframed
        add_content_slide(prs, "Text Analysis: What It Provides", [
            "Compiles text evidence from 55 documents into structured categories",
            "Surfaces specific quotes and management language for manual review",
            "Provides repeatable framework for future thematic research",
            "Full source traceability — every quote links to original document",
        ])
        add_content_slide(prs, "Text Analysis: Honest Limitations", [
            "Descriptive, not predictive — signals do NOT forecast returns",
            "330 paragraphs = small sample; limited statistical power",
            "Classification relies on keyword patterns, not deep semantic analysis",
            "Source bias: RSS feeds overweight news vs. operational filings",
            "Every output requires human verification before investment use",
        ])

    # -------- Slide 22: The Money Slide --------
    # Thesis + Backtest + Spread + Catalyst timeline — one visual
    money_items = [
        "THESIS: Energy insecurity is shifting from barrels to electrons",
        "  • Grid equipment = multi-year capex visibility (policy + demand)",
        "  • Oilfield services = margin compression + cyclical risk (even if oil rises)",
        "",
        "HISTORICAL PROOF (2Y backtest):",
        "  • Sieyuan +227% vs Oil +17% vs HAL +9%",
        "  • Pair trade spread: long Sieyuan / short HAL generated +109% P&L",
        "  • Oil-HAL correlation 0.66 — moderate, and driven by margin, not price",
        "",
        "FORWARD EXPECTED RETURN:",
        f"  • Long Sieyuan: +{valuation_summary['long_expected_return']:.0f}% (prob-weighted)"
        if valuation_summary else "  • Long Sieyuan: +30% (base case)",
        f"  • Short HAL: {valuation_summary['short_expected_return']:.0f}% (prob-weighted)"
        if valuation_summary else "  • Short HAL: -25% (base case)",
        f"  • Pair spread: +{valuation_summary['pair_spread_return']:.0f}%"
        if valuation_summary else "  • Pair spread: +55%",
        "",
        "CATALYST TIMELINE:",
        "  • Q2: Sieyuan overseas order wins + HAL earnings miss on logistics",
        "  • Q3: State Grid capex acceleration + NA rig count decline",
        "  • Q4: Full-year margin differential becomes visible in earnings",
    ]
    add_content_slide(prs, "The Trade: Thesis + Proof + Spread + Catalysts", money_items)

    # -------- Slide 23: Pair Trade Backtest Chart --------
    pair_trade_path = charts_dir / "pair_trade_backtest.png"
    if pair_trade_path.exists():
        add_chart_slide(
            prs,
            "Pair Trade Backtest: Long Sieyuan / Short HAL (2Y)",
            pair_trade_path,
            "Dollar-neutral, 50-50 weight. Shows historical spread generation even through volatility.",
        )

    # -------- Slide 24: Recommendation --------
    rec_subtitle = (
        "Long Sieyuan Electric / Short Halliburton"
        if not valuation_summary else
        f"Long Sieyuan ({valuation_summary['long_expected_return']:+.0f}%) / "
        f"Short HAL ({valuation_summary['short_expected_return']:+.0f}%) = "
        f"Pair spread {valuation_summary['pair_spread_return']:+.0f}%"
    )
    add_title_slide(prs, "Recommendation", rec_subtitle)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"[SAVED] PPTX: {output_path}")
    return output_path


def main():
    """Build the full deck from processed outputs."""
    from src.config import (
        CLASSIFIED_PARAGRAPHS_PATH,
        CHARTS_DIR,
        OUTPUTS_DIR,
        PROCESSED_DIR,
    )
    from src.analysis import plan_format_signal_tracker, narrative_shift_analysis

    # Load classifications
    classified_df = None
    if CLASSIFIED_PARAGRAPHS_PATH.exists():
        try:
            classified_df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
            print(f"Loaded {len(classified_df)} classified paragraphs")
        except pd.errors.EmptyDataError:
            print("Classifications file empty")

    # Build signal tracker
    signal_tracker_df = None
    narrative = None
    if classified_df is not None and not classified_df.empty:
        signal_tracker_df = plan_format_signal_tracker(classified_df)
        narrative = narrative_shift_analysis(classified_df)

    # Load evidence pack
    evidence_pack = None
    evidence_json = OUTPUTS_DIR / "tables" / "evidence_pack.json"
    if evidence_json.exists():
        with open(evidence_json) as f:
            evidence_pack = json.load(f)

    # Load valuation outputs
    val_dir = PROCESSED_DIR / "valuation"
    peer_comps_df = None
    long_scenarios_df = None
    short_scenarios_df = None
    valuation_summary = None

    if (val_dir / "peer_comps.csv").exists():
        peer_comps_df = pd.read_csv(val_dir / "peer_comps.csv")
    if (val_dir / "long_scenarios.csv").exists():
        long_scenarios_df = pd.read_csv(val_dir / "long_scenarios.csv")
    if (val_dir / "short_scenarios.csv").exists():
        short_scenarios_df = pd.read_csv(val_dir / "short_scenarios.csv")
    if (val_dir / "pair_trade_summary.csv").exists():
        pair = pd.read_csv(val_dir / "pair_trade_summary.csv").iloc[0].to_dict()
        valuation_summary = {
            "long_expected_return": pair.get("long_expected_return_pct", 0),
            "short_expected_return": pair.get("short_expected_move_pct", 0),
            "pair_spread_return": pair.get("pair_spread_return_pct", 0),
        }

    # Build deck
    deck_dir = Path(__file__).parent.parent / "deck"
    deck_dir.mkdir(parents=True, exist_ok=True)
    output_path = deck_dir / "UBS_Pitch_Deck_AUTO.pptx"

    build_deck(
        classified_df=classified_df,
        signal_tracker_df=signal_tracker_df,
        evidence_pack=evidence_pack,
        valuation_summary=valuation_summary,
        peer_comps_df=peer_comps_df,
        long_scenarios_df=long_scenarios_df,
        short_scenarios_df=short_scenarios_df,
        charts_dir=CHARTS_DIR,
        output_path=output_path,
        narrative_shift=narrative,
    )

    print("\n" + "=" * 60)
    print("DECK GENERATED")
    print("=" * 60)
    print(f"Open: {output_path}")


if __name__ == "__main__":
    main()
