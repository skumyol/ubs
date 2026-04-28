# Blind Classification Validation Report

## Test Design

- **Sample size**: 50 paragraphs (stratified by category)
- **Method**: Strip all source metadata (company names, source titles, sector tags)
- **Goal**: Test whether the classifier reads semantic content or pattern-matches on metadata

## Baseline Comparison

| Classifier | Accuracy | Kappa | Macro F1 |
|------------|----------|-------|----------|
| Random | 0.120 | -0.027 | 0.125 |
| Majority class | 0.140 | 0.000 | 0.035 |
| Keyword heuristic | 0.340 | 0.232 | 0.262 |
| AI (ceiling estimate) | 1.000 | 1.000 | 1.000 |

## Per-Class Metrics (Keyword Baseline)

| Category | Precision | Recall | F1 | Support |
|----------|-----------|--------|----|---------|
| Electricity Demand | 0.25 | 0.143 | 0.182 | 7 |
| Grid Resilience | 0.538 | 1.0 | 0.7 | 7 |
| Margin/Earnings Risk | 0.273 | 0.429 | 0.333 | 7 |
| Not Relevant | 0.0 | 0.0 | 0.0 | 7 |
| Oil Supply Disruption | 0.357 | 0.714 | 0.476 | 7 |
| Oilfield Cost Pressure | 0.0 | 0.0 | 0.0 | 8 |
| Policy-Backed Capex | 0.143 | 0.143 | 0.143 | 7 |

## Interpretation

The keyword baseline achieves only FAIR agreement. The classification task has genuine semantic complexity. The AI has potential to add value if it can outperform simple heuristics in a blind test.

## Required Next Step

To get a true AI classifier accuracy estimate:
1. Load `blind_validation_sample.csv`
2. Send each `blind_text` to the LLM with a fresh prompt (no sector hints)
3. Compare LLM predictions against `category` column
4. If accuracy < keyword baseline + 10pp, the classifier is not adding value
