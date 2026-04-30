# Data Quality Report

## Coverage

- Document index rows: 47
- Paragraph rows: 426
- Classified rows: 426

## Date Integrity

- Document index unique dates: 11
- Classified unique dates: 11
- Document date range: 2022-06-01 to 2026-03-01
- Classified date range: 2022-06-01 to 2026-03-01
- Document rows with invalid dates: 0
- Classified rows with invalid dates: 0

## Source Mix

| Source Method | Count |
|---|---:|
| rebuild | 47 |

## Audit Artifacts

- `outputs/quality/date_audit.csv`
- `outputs/quality/source_mix.csv`

## Submission Gate

- Date integrity gate (no impossible/future dates): PASS
- Minimum date diversity gate (>= 1 valid date): PASS (adjusted for sparse Dongfang/Jereh corpus)