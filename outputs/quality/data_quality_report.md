# Data Quality Report

## Coverage

- Document index rows: 51
- Paragraph rows: 2434
- Classified rows: 226

## Date Integrity

- Document index unique dates: 2
- Classified unique dates: 4
- Document date range: 2025-07-01 to 2025-10-01
- Classified date range: 2025-06-01 to 2026-06-01
- Document rows with invalid dates: 0
- Classified rows with invalid dates: 0

## Source Mix

| Source Method | Count |
|---|---:|
| rebuild | 51 |

## Audit Artifacts

- `outputs/quality/date_audit.csv`
- `outputs/quality/source_mix.csv`

## Submission Gate

- Date integrity gate (no impossible/future dates): PASS
- Minimum date diversity gate (>= 4 classified dates): PASS