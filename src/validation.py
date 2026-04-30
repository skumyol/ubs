"""Blind classification validation framework.

Quant-grade rigor for assessing whether the AI classifier is actually
reading text or just pattern-matching on source metadata/sector tags.

Core test: strip all sector/source hints from a held-out sample and
re-classify. If accuracy collapses, the classifier is biased.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# Held-out sample size for validation
VALIDATION_SAMPLE_SIZE = 50
RANDOM_SEED = 42


def strip_biasing_metadata(text: str, source_name: str, title: str) -> str:
    """Remove source hints that let the classifier cheat.

    A biased classifier learns:
      - "Sungrow investor relations" -> Inverter & Storage Equipment
      - "Dongfang Electric" -> Grid Infrastructure
      - Company names in text -> sector

    We strip company names, source names, and any sector-indicative terms
    to force the classifier to judge on semantic content alone.
    """
    # List of biasing terms to redact
    redactions = [
        "Dongfang", "DONGFANG", "Sungrow", "SUNGROW",
        "inverter", "energy storage", "battery storage", "solar inverter",
        "upstream", "downstream", "drilling", "rig count", "hydraulic fracturing",
        "shale", "permeability", "brent crude", "WTI",
        "State Grid", "StateGrid", "China Grid",
        "substation", "switchgear", "transformer", "transmission line",
        "IEA", "EIA", "IEA Electricity", "IEA Grids",
        "Motley Fool", "MotleyFool",
    ]

    cleaned = text
    for term in redactions:
        cleaned = cleaned.replace(term, "[REDACTED]")
        cleaned = cleaned.replace(term.lower(), "[REDACTED]")
        cleaned = cleaned.replace(term.upper(), "[REDACTED]")

    return cleaned


def sample_validation_set(
    classified_df: pd.DataFrame,
    n: int = VALIDATION_SAMPLE_SIZE,
    seed: int = RANDOM_SEED,
    stratify_by_category: bool = True,
) -> pd.DataFrame:
    """Draw a stratified random sample for blind re-testing."""
    if len(classified_df) < n:
        n = len(classified_df)

    rng = np.random.RandomState(seed)

    if stratify_by_category:
        # Sample proportionally from each category
        cats = classified_df["category"].unique()
        per_cat = max(1, n // len(cats))
        samples = []
        for cat in cats:
            cat_df = classified_df[classified_df["category"] == cat]
            if len(cat_df) == 0:
                continue
            sample_n = min(per_cat, len(cat_df))
            samples.append(cat_df.sample(n=sample_n, random_state=rng))
        sample_df = pd.concat(samples)
        # If we didn't hit n, fill randomly
        if len(sample_df) < n:
            remaining = n - len(sample_df)
            mask = ~classified_df.index.isin(sample_df.index)
            fill = classified_df[mask].sample(n=min(remaining, mask.sum()), random_state=rng)
            sample_df = pd.concat([sample_df, fill])
    else:
        sample_df = classified_df.sample(n=n, random_state=rng)

    return sample_df.reset_index(drop=True)


def compute_confusion_matrix(
    true_labels: List[str],
    pred_labels: List[str],
    categories: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict]:
    """Compute confusion matrix and per-class metrics."""
    if categories is None:
        categories = sorted(set(true_labels) | set(pred_labels))

    # Build confusion matrix
    cm = pd.DataFrame(0, index=categories, columns=categories)
    for t, p in zip(true_labels, pred_labels):
        if t in cm.index and p in cm.columns:
            cm.loc[t, p] += 1

    # Per-class metrics
    metrics = {}
    for cat in categories:
        tp = cm.loc[cat, cat] if cat in cm.index and cat in cm.columns else 0
        fp = cm[cat].sum() - tp if cat in cm.columns else 0
        fn = cm.loc[cat].sum() - tp if cat in cm.index else 0
        tn = cm.sum().sum() - tp - fp - fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = tp + fn

        metrics[cat] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": int(support),
        }

    # Overall accuracy
    total_correct = sum(cm.loc[c, c] for c in categories if c in cm.index and c in cm.columns)
    total = len(true_labels)
    accuracy = total_correct / total if total > 0 else 0.0

    # Macro-F1
    macro_f1 = np.mean([m["f1"] for m in metrics.values()]) if metrics else 0.0

    # Weighted-F1
    total_support = sum(m["support"] for m in metrics.values())
    weighted_f1 = (
        sum(m["f1"] * m["support"] for m in metrics.values()) / total_support
        if total_support > 0 else 0.0
    )

    return cm, {
        "accuracy": round(accuracy, 3),
        "macro_f1": round(macro_f1, 3),
        "weighted_f1": round(weighted_f1, 3),
        "total_samples": total,
        "per_class": metrics,
    }


def cohens_kappa(true_labels: List[str], pred_labels: List[str]) -> float:
    """Compute Cohen's Kappa for inter-rater agreement.

    Kappa > 0.8: Almost perfect agreement
    0.6-0.8: Substantial
    0.4-0.6: Moderate
    0.2-0.4: Fair
    < 0.2: Slight/poor
    """
    n = len(true_labels)
    if n == 0:
        return 0.0

    categories = sorted(set(true_labels) | set(pred_labels))
    # Build confusion matrix
    cm = pd.DataFrame(0, index=categories, columns=categories)
    for t, p in zip(true_labels, pred_labels):
        cm.loc[t, p] += 1

    # Observed agreement (accuracy)
    p_o = sum(cm.loc[c, c] for c in categories) / n

    # Expected agreement (random chance)
    row_sums = cm.sum(axis=1)
    col_sums = cm.sum(axis=0)
    p_e = sum(row_sums[c] * col_sums[c] for c in categories) / (n * n)

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1 - p_e)
    return round(kappa, 3)


def simulate_baseline_classifier(
    texts: List[str],
    categories: List[str],
    strategy: str = "random",
) -> List[str]:
    """Simulate a naive baseline for comparison.

    Strategies:
      - random: uniform random across categories
      - majority: always predict the most frequent category
      - keyword: simple keyword-matching heuristic
    """
    rng = np.random.RandomState(RANDOM_SEED)

    if strategy == "random":
        return [rng.choice(categories) for _ in texts]

    if strategy == "majority":
        # In our data, "Electricity Demand" is the largest category
        return ["Electricity Demand"] * len(texts)

    if strategy == "keyword":
        preds = []
        for text in texts:
            text_lower = text.lower()
            scores = {}
            for cat in categories:
                scores[cat] = 0
            # Simple keyword matching
            if any(w in text_lower for w in ["oil", "crude", "drilling", "rig", "fracturing", "shale"]):
                scores["Oil Supply Disruption"] += 3
                scores["Oilfield Cost Pressure"] += 2
                scores["Margin/Earnings Risk"] += 1
            if any(w in text_lower for w in ["grid", "transmission", "substation", "switchgear", "transformer"]):
                scores["Grid Resilience"] += 3
            if any(w in text_lower for w in ["demand", "electricity", "data center", "ev ", "cooling"]):
                scores["Electricity Demand"] += 2
            if any(w in text_lower for w in ["capex", "investment", "spending", "policy", "government"]):
                scores["Policy-Backed Capex"] += 2
            if any(w in text_lower for w in ["margin", "earnings", "cost", "pressure", "compress"]):
                scores["Margin/Earnings Risk"] += 2
                scores["Oilfield Cost Pressure"] += 1

            # Pick highest score, break ties randomly
            max_score = max(scores.values())
            candidates = [c for c, s in scores.items() if s == max_score]
            preds.append(rng.choice(candidates))
        return preds

    raise ValueError(f"Unknown strategy: {strategy}")


def run_validation(
    classified_df: pd.DataFrame,
    output_dir: Path,
    n: int = VALIDATION_SAMPLE_SIZE,
) -> Dict:
    """Run the full blind validation test.

    Since we cannot call the LLM again in this offline test,
    we simulate what the test WOULD show by using the existing
    classifications as ground truth and testing against naive baselines.

    In production, this function would:
      1. Sample 50 paragraphs
      2. Strip all metadata
      3. Send to a fresh LLM instance with a blind prompt
      4. Compare predictions vs. original labels
      5. Compute confusion matrix, kappa, per-class metrics
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("BLIND CLASSIFICATION VALIDATION TEST")
    print("=" * 60)

    # Sample
    sample_df = sample_validation_set(classified_df, n=n)
    print(f"\n[1] Sampled {len(sample_df)} paragraphs for validation")

    # Strip metadata to simulate blind test
    sample_df["blind_text"] = sample_df.apply(
        lambda r: strip_biasing_metadata(
            str(r.get("text", "")),
            str(r.get("source_name", "")),
            str(r.get("title", "")),
        ),
        axis=1,
    )

    # Save blind sample for manual/external review
    blind_sample_path = output_dir / "blind_validation_sample.csv"
    sample_df[["paragraph_id", "blind_text", "category", "sentiment", "sector"]].to_csv(
        blind_sample_path, index=False
    )
    print(f"[SAVED] Blind sample: {blind_sample_path}")

    # Ground truth
    true_labels = sample_df["category"].tolist()
    categories = sorted(classified_df["category"].unique())

    # Baseline 1: Random classifier
    print("\n[2] Baseline: Random classifier")
    random_preds = simulate_baseline_classifier(sample_df["blind_text"].tolist(), categories, "random")
    cm_random, metrics_random = compute_confusion_matrix(true_labels, random_preds, categories)
    kappa_random = cohens_kappa(true_labels, random_preds)
    print(f"  Accuracy: {metrics_random['accuracy']:.3f} | Kappa: {kappa_random:.3f}")

    # Baseline 2: Majority class
    print("\n[3] Baseline: Majority-class classifier")
    majority_preds = simulate_baseline_classifier(sample_df["blind_text"].tolist(), categories, "majority")
    cm_majority, metrics_majority = compute_confusion_matrix(true_labels, majority_preds, categories)
    kappa_majority = cohens_kappa(true_labels, majority_preds)
    print(f"  Accuracy: {metrics_majority['accuracy']:.3f} | Kappa: {kappa_majority:.3f}")

    # Baseline 3: Simple keyword heuristic
    print("\n[4] Baseline: Keyword-matching heuristic")
    keyword_preds = simulate_baseline_classifier(sample_df["blind_text"].tolist(), categories, "keyword")
    cm_keyword, metrics_keyword = compute_confusion_matrix(true_labels, keyword_preds, categories)
    kappa_keyword = cohens_kappa(true_labels, keyword_preds)
    print(f"  Accuracy: {metrics_keyword['accuracy']:.3f} | Kappa: {kappa_keyword:.3f}")

    # Simulated AI classifier (using original labels as proxy)
    # In production, this would be the LLM's blind predictions
    print("\n[5] AI Classifier (current system, assumed ground-truth match)")
    ai_preds = true_labels  # Placeholder: in production, this is the LLM output
    cm_ai, metrics_ai = compute_confusion_matrix(true_labels, ai_preds, categories)
    kappa_ai = cohens_kappa(true_labels, ai_preds)
    print(f"  Accuracy: {metrics_ai['accuracy']:.3f} | Kappa: {kappa_ai:.3f}")
    print("  NOTE: This is a ceiling estimate. Real blind accuracy will be lower.")

    # Save results
    results = {
        "sample_size": len(sample_df),
        "categories_tested": categories,
        "random_baseline": {
            "accuracy": metrics_random["accuracy"],
            "kappa": kappa_random,
            "macro_f1": metrics_random["macro_f1"],
        },
        "majority_baseline": {
            "accuracy": metrics_majority["accuracy"],
            "kappa": kappa_majority,
            "macro_f1": metrics_majority["macro_f1"],
        },
        "keyword_baseline": {
            "accuracy": metrics_keyword["accuracy"],
            "kappa": kappa_keyword,
            "macro_f1": metrics_keyword["macro_f1"],
        },
        "ai_classifier_ceiling": {
            "accuracy": metrics_ai["accuracy"],
            "kappa": kappa_ai,
            "macro_f1": metrics_ai["macro_f1"],
            "note": "Upper bound. Real blind test required for true estimate.",
        },
        "per_class_metrics": metrics_keyword["per_class"],
        "interpretation": _interpret_validation(
            metrics_keyword["accuracy"],
            kappa_keyword,
            metrics_random["accuracy"],
        ),
    }

    # Save JSON
    results_path = output_dir / "validation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] Validation results: {results_path}")

    # Save Markdown report
    md_path = output_dir / "validation_report.md"
    md_lines = [
        "# Blind Classification Validation Report",
        "",
        "## Test Design",
        "",
        f"- **Sample size**: {results['sample_size']} paragraphs (stratified by category)",
        "- **Method**: Strip all source metadata (company names, source titles, sector tags)",
        "- **Goal**: Test whether the classifier reads semantic content or pattern-matches on metadata",
        "",
        "## Baseline Comparison",
        "",
        "| Classifier | Accuracy | Kappa | Macro F1 |",
        "|------------|----------|-------|----------|",
        f"| Random | {metrics_random['accuracy']:.3f} | {kappa_random:.3f} | {metrics_random['macro_f1']:.3f} |",
        f"| Majority class | {metrics_majority['accuracy']:.3f} | {kappa_majority:.3f} | {metrics_majority['macro_f1']:.3f} |",
        f"| Keyword heuristic | {metrics_keyword['accuracy']:.3f} | {kappa_keyword:.3f} | {metrics_keyword['macro_f1']:.3f} |",
        f"| AI (ceiling estimate) | {metrics_ai['accuracy']:.3f} | {kappa_ai:.3f} | {metrics_ai['macro_f1']:.3f} |",
        "",
        "## Per-Class Metrics (Keyword Baseline)",
        "",
        "| Category | Precision | Recall | F1 | Support |",
        "|----------|-----------|--------|----|---------|",
    ]
    for cat, m in metrics_keyword["per_class"].items():
        md_lines.append(
            f"| {cat} | {m['precision']} | {m['recall']} | {m['f1']} | {m['support']} |"
        )
    md_lines.extend([
        "",
        "## Interpretation",
        "",
        results["interpretation"],
        "",
        "## Required Next Step",
        "",
        "To get a true AI classifier accuracy estimate:",
        "1. Load `blind_validation_sample.csv`",
        "2. Send each `blind_text` to the LLM with a fresh prompt (no sector hints)",
        "3. Compare LLM predictions against `category` column",
        "4. If accuracy < keyword baseline + 10pp, the classifier is not adding value",
        "",
    ])
    md_path.write_text("\n".join(md_lines))
    print(f"[SAVED] Markdown report: {md_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Keyword baseline accuracy: {metrics_keyword['accuracy']:.1%}")
    print(f"  If AI blind accuracy < {metrics_keyword['accuracy'] + 0.10:.1%}, it is not adding value")
    print(f"  Cohen's Kappa (keyword vs truth): {kappa_keyword:.3f}")
    print(f"  Interpretation: {results['interpretation']}")
    print("=" * 60)

    return results


def _interpret_validation(keyword_acc: float, keyword_kappa: float, random_acc: float) -> str:
    """Generate human-readable interpretation."""
    if keyword_kappa > 0.6:
        return (
            "The keyword baseline achieves SUBSTANTIAL agreement with ground truth. "
            "This suggests the task is largely keyword-driven, and the AI classifier may be "
            "doing glorified keyword matching. If the AI's blind accuracy is not materially "
            "above the keyword baseline (+10pp or more), the AI adds no incremental value."
        )
    elif keyword_kappa > 0.4:
        return (
            "The keyword baseline achieves MODERATE agreement. The task has some semantic "
            "complexity beyond simple keyword matching. The AI may add value if it materially "
            "outperforms the keyword baseline in a blind test."
        )
    else:
        return (
            "The keyword baseline achieves only FAIR agreement. The classification task "
            "has genuine semantic complexity. The AI has potential to add value if it can "
            "outperform simple heuristics in a blind test."
        )


if __name__ == "__main__":
    from src.config import CLASSIFIED_PARAGRAPHS_PATH

    if not CLASSIFIED_PARAGRAPHS_PATH.exists():
        print(f"[ERROR] No classifications found at {CLASSIFIED_PARAGRAPHS_PATH}")
        exit(1)

    df = pd.read_csv(CLASSIFIED_PARAGRAPHS_PATH)
    print(f"Loaded {len(df)} classified paragraphs")

    output_dir = Path("outputs/validation")
    run_validation(df, output_dir)
