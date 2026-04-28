# Signal-Return Predictive Analysis Report

## Sample Overview

- **Total paragraphs**: 226
- **Unique dates**: 4
- **Date range**: 2025-06-01 00:00:00 to 2026-06-01 00:00:00

## Test 1: Historical Thesis Alignment (2023-2025)

Tests if narrative signals match long-term price divergence. Grid signals should be positive; Oilfield signals should be negative. Sieyuan (grid proxy) should outperform HAL (oilfield proxy).

- **Period**: 2023-01-01 to 2025-12-31
- **HAL 3Y return**: -19.0%
- **Sieyuan 3Y return**: 302.9%
- **Price divergence** (Sieyuan - HAL): 321.9%
- **Grid signal sentiment**: 0.40
- **Oilfield signal sentiment**: -0.28
- **Thesis signal score**: 0.68
- **Alignment**: CONSISTENT

**Interpretation**: Thesis signals and price divergence are directionally aligned. Grid sentiment: 0.40, Oilfield sentiment: -0.28, Price divergence: 321.9%

## Test 2: Event Study Analysis

Tests returns around document publication dates. Windows: pre_7d (control), post_7d, post_30d, post_90d.

### hal

- **Number of events**: 3

| Window | Mean Return | Std Dev | N | t-stat | p-value | Significant? |
|--------|-------------|---------|---|--------|---------|--------------|
| pre_7d | -0.71% | 1.80% | 3 | -0.68 | 0.565 | No |
| post_7d | 2.12% | 5.29% | 3 | 0.69 | 0.559 | No |
| post_30d | 7.60% | 1.91% | 3 | 6.91 | 0.02 | Yes |
| post_90d | 16.15% | 2.28% | 3 | 12.29 | 0.007 | Yes |

### sieyuan

- **Number of events**: 3

| Window | Mean Return | Std Dev | N | t-stat | p-value | Significant? |
|--------|-------------|---------|---|--------|---------|--------------|
| pre_7d | -0.42% | 5.09% | 3 | -0.14 | 0.899 | No |
| post_7d | 0.48% | 1.78% | 2 | 0.38 | 0.768 | No |
| post_30d | 8.96% | 9.15% | 3 | 1.7 | 0.232 | No |
| post_90d | 34.84% | 13.64% | 3 | 4.42 | 0.047 | Yes |

## Test 3: Monthly Lead-Lag Correlations

Overlapping months: 3

### grid_sentiment_vs_hal

**Error**: Insufficient aligned data points

### grid_sentiment_vs_sieyuan

**Error**: Insufficient aligned data points

## Verdict

WEAK BUT NON-ZERO PREDICTIVE POWER: 4/7 tests significant at 5% level. Historical alignment: CONSISTENT. Signals may contain marginal forward info, but exploitable alpha is likely swamped by noise.

## Methodology Notes

1. **Historical Alignment**: Tests if narrative sentiment matches 3-year price divergence. This is NOT predictive—it tests if the story matches history, not if it forecasts future returns.

2. **Event Study**: Tests returns around document dates. Post-event windows test if signals have contemporaneous or short-term predictive power. Small sample (6 dates) limits statistical power.

3. **Lead-Lag Correlation**: Tests if month-T signals predict month-T+1 returns. Requires >= 3 overlapping months for meaningful results.

4. **Significance**: p < 0.05 (two-tailed t-test). Bonferroni correction NOT applied— this is exploratory analysis, not confirmatory.

5. **Limitations**: Sparse signal dates (only 6 unique dates), mixed document types (news, reports, transcripts), forward-looking dates in some documents.
