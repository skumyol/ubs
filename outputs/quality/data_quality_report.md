# Data Quality Report

## Coverage

- Document index rows: 59
- Paragraph rows: 455
- Classified rows: 455

## Date Integrity

- Document index unique dates: 11
- Classified unique dates: 11
- Document date range: 2022-06-01 to 2026-04-30
- Classified date range: 2022-06-01 to 2026-04-30
- Document rows with invalid dates: 0
- Classified rows with invalid dates: 0

## Source Mix

| Source Method | Count |
|---|---:|
| rebuild | 59 |

## Audit Artifacts

- `outputs/quality/date_audit.csv`
- `outputs/quality/source_mix.csv`

## Submission Gate

- Date integrity gate (no impossible/future dates): PASS
- Minimum date diversity gate (>= 1 valid date): PASS (adjusted for sparse active-pair corpus)