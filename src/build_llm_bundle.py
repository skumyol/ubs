#!/usr/bin/env python3
"""Build a single LLM-friendly bundle file from current submission artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("/Users/skumyol/Documents/GitHub/ubs")
OUT = ROOT / "outputs" / "submission"


def _read_text(path: Path) -> str:
    if not path.exists():
        return f"[Missing file: {path}]"
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> str:
    if not path.exists():
        return f"[Missing file: {path}]"
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, ensure_ascii=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bundle_path = OUT / "LLM_SUBMISSION_BUNDLE.md"

    sections = [
        "# LLM Submission Bundle",
        "",
        "This file consolidates the current Dongfang Electric / Sungrow submission artifacts into one LLM-friendly document.",
        "",
        "## Pair",
        "",
        "- Long: Dongfang Electric (1072.HK / 600875.SH)",
        "- Short: Sungrow (300274.SZ)",
        "- Theme: From Clean-Tech Growth to Grid-Backbone Value",
        "",
        "## Submission Report",
        "",
        "```md",
        _read_text(ROOT / "outputs" / "submission_report.md"),
        "```",
        "",
        "## Predictive Scorecard",
        "",
        "```md",
        _read_text(ROOT / "outputs" / "tables" / "predictive_scorecard.md"),
        "```",
        "",
        "## Evidence Pack",
        "",
        "```md",
        _read_text(ROOT / "outputs" / "tables" / "evidence_pack.md"),
        "```",
        "",
        "## Q&A Defense",
        "",
        "```md",
        _read_text(ROOT / "docs" / "qna_defense.md"),
        "```",
        "",
        "## LLM Long Thesis JSON",
        "",
        "```json",
        _read_json(ROOT / "outputs" / "tables" / "llm_generated" / "long_thesis.json"),
        "```",
        "",
        "## LLM Short Thesis JSON",
        "",
        "```json",
        _read_json(ROOT / "outputs" / "tables" / "llm_generated" / "short_thesis.json"),
        "```",
        "",
        "## LLM AI Analyst Module JSON",
        "",
        "```json",
        _read_json(ROOT / "outputs" / "tables" / "llm_generated" / "ai_analyst_module.json"),
        "```",
        "",
        "## LLM Slide Content JSON",
        "",
        "```json",
        _read_json(ROOT / "outputs" / "tables" / "llm_generated" / "slide_content.json"),
        "```",
        "",
        "## LLM Q&A Responses JSON",
        "",
        "```json",
        _read_json(ROOT / "outputs" / "tables" / "llm_generated" / "qa_responses.json"),
        "```",
        "",
        "## Source Manifest",
        "",
        "```md",
        _read_text(ROOT / "outputs" / "submission" / "sources" / "SOURCE_MANIFEST.md"),
        "```",
        "",
    ]

    bundle_path.write_text("\n".join(sections), encoding="utf-8")
    print(f"[SAVED] {bundle_path}")


if __name__ == "__main__":
    main()
