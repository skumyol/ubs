Below is a practical **local development stack + Git repo structure** for the UBS stock-pitch research workflow.

```md
# Tech Stack & Git Repository Plan
## Project: Long the Grid, Short the Bottleneck

---

# 1. Development Goal

Build a lightweight research pipeline that supports the stock-pitch deck:

1. Collect public text sources
2. Clean and structure the data
3. Run AI-assisted classification
4. Produce charts / tables for the deck
5. Maintain source traceability
6. Support team collaboration through Git

This is not a production software product.  
It should be simple, reproducible, and presentation-oriented.

---

# 2. Recommended Tech Stack

## 2.1 Core Stack

| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.11+ | Main research and analysis language |
| Environment | Conda / venv | Dependency isolation |
| Data processing | pandas, numpy | Cleaning, tables, basic calculations |
| Text processing | regex, nltk / spaCy optional | Text splitting, keyword cleaning |
| AI / LLM | OpenAI API / Claude / Gemini / local Qwen optional | Classification, summarization, extraction |
| Embeddings | sentence-transformers / OpenAI embeddings | Similarity search, clustering |
| Visualization | matplotlib, plotly | Charts and heatmaps |
| Notebook | Jupyter / VS Code notebooks | Exploratory analysis |
| Data storage | CSV / Parquet / SQLite | Simple local research database |
| Deck output | PowerPoint manual + exported charts | Final UBS deck |
| Version control | Git + GitHub | Collaboration and version history |

---

# 3. Simple Stack Option

Use this if you want speed over engineering complexity.

## Stack

```text
Python
pandas
Jupyter Notebook
OpenAI / Claude / Gemini
matplotlib
Excel / CSV
PowerPoint
GitHub
```

## Best for

* Fast competition workflow
* Small team
* 300–500 documents
* Easy manual review
* Deck-first output

This is probably the best option for your UBS challenge.

---

# 4. More Advanced Stack Option

Use this if you want a cleaner research tool that feels more like an internal analyst system.

## Stack

```text
Python
FastAPI
SQLite
pandas
sentence-transformers
OpenAI / Claude / Gemini
Streamlit
Plotly
GitHub
```

## Added features

* Small dashboard
* Searchable document database
* Classification review interface
* AI output audit trail
* Exportable charts

This is useful if you want to reuse the system for future pitches.

---

# 5. Recommended Repository Structure

```text
ubs-energy-security-pitch/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── data/
│   ├── raw/
│   │   ├── company_transcripts/
│   │   ├── annual_reports/
│   │   ├── news/
│   │   ├── policy_reports/
│   │   └── energy_reports/
│   │
│   ├── interim/
│   │   ├── cleaned_text.csv
│   │   ├── document_index.csv
│   │   └── paragraph_level_dataset.csv
│   │
│   └── processed/
│       ├── classified_paragraphs.csv
│       ├── keyword_frequency.csv
│       ├── ai_signal_tracker.csv
│       ├── valuation_inputs.csv
│       └── source_master.csv
│
├── notebooks/
│   ├── 01_data_collection_check.ipynb
│   ├── 02_text_cleaning.ipynb
│   ├── 03_ai_classification.ipynb
│   ├── 04_signal_analysis.ipynb
│   ├── 05_valuation_model.ipynb
│   └── 06_chart_export.ipynb
│
├── src/
│   ├── __init__.py
│   │
│   ├── config.py
│   ├── data_loader.py
│   ├── text_cleaner.py
│   ├── classifier.py
│   ├── validation.py
│   ├── analysis.py
│   ├── charts.py
│   └── utils.py
│
├── prompts/
│   ├── classification_prompt.md
│   ├── extraction_prompt.md
│   ├── summary_prompt.md
│   └── limitation_prompt.md
│
├── outputs/
│   ├── charts/
│   │   ├── energy_signal_heatmap.png
│   │   ├── keyword_frequency.png
│   │   ├── long_short_matrix.png
│   │   └── valuation_sensitivity.png
│   │
│   ├── tables/
│   │   ├── peer_comps.xlsx
│   │   ├── valuation_summary.xlsx
│   │   └── source_audit_table.xlsx
│   │
│   └── deck_exports/
│       ├── slide_charts/
│       └── final_figures/
│
├── deck/
│   ├── working_deck.pptx
│   ├── final_submission_deck.pptx
│   └── speaker_notes.md
│
├── docs/
│   ├── investment_thesis.md
│   ├── research_plan.md
│   ├── ai_methodology.md
│   ├── source_log.md
│   ├── risk_questions.md
│   └── qna_defense.md
│
└── tests/
    ├── test_text_cleaner.py
    ├── test_classifier_output.py
    └── test_data_schema.py
```

---

# 6. What Each Folder Does

## `data/raw/`

Stores original source files.

Examples:

```text
Halliburton_Q1_2026_transcript.txt
Sieyuan_2025_annual_report.pdf
IEA_electricity_report.txt
Reuters_oil_disruption_article.txt
```

Do not edit raw files.

---

## `data/interim/`

Stores cleaned but not final data.

Examples:

```text
cleaned_text.csv
paragraph_level_dataset.csv
```

This is where raw documents are split into usable paragraphs.

---

## `data/processed/`

Stores final analysis-ready data.

Examples:

```text
classified_paragraphs.csv
ai_signal_tracker.csv
keyword_frequency.csv
valuation_inputs.csv
```

These files feed directly into charts and slides.

---

## `notebooks/`

Used for exploration and team review.

Recommended notebook flow:

1. `01_data_collection_check.ipynb`
   Check whether source coverage is enough.
2. `02_text_cleaning.ipynb`
   Clean documents and split into paragraphs.
3. `03_ai_classification.ipynb`
   Run AI classification.
4. `04_signal_analysis.ipynb`
   Create signal tracker and heatmaps.
5. `05_valuation_model.ipynb`
   Build valuation scenarios.
6. `06_chart_export.ipynb`
   Export final charts for PPT.

---

## `src/`

Stores reusable Python functions.

This prevents notebooks from becoming messy.

Example:

```python
from src.text_cleaner import clean_text, split_into_paragraphs
from src.classifier import classify_paragraph
from src.charts import create_signal_heatmap
```

---

## `prompts/`

Stores all AI prompts.

This is important because UBS may ask how you used AI.
You need to show the process was controlled and repeatable.

Example files:

```text
classification_prompt.md
extraction_prompt.md
summary_prompt.md
limitation_prompt.md
```

---

## `outputs/`

Stores final charts and tables used in the deck.

Everything in this folder should be deck-ready.

---

## `deck/`

Stores PowerPoint files and speaker notes.

Recommended naming:

```text
v01_thesis_structure.pptx
v02_with_ai_module.pptx
v03_with_valuation.pptx
v04_final_rehearsal.pptx
final_submission_ubs_energy_security.pptx
```

---

## `docs/`

Stores written reasoning.

Important files:

```text
investment_thesis.md
ai_methodology.md
risk_questions.md
qna_defense.md
```

This helps the team stay aligned.

---

# 7. Data Schema

## 7.1 `document_index.csv`

```csv
doc_id,source_name,date,document_type,company,sector,url,file_path,notes
DOC001,Halliburton Q1 Transcript,2026-04-21,Transcript,Halliburton,Oilfield Services,URL,data/raw/company_transcripts/halliburton_q1.txt,
DOC002,IEA Electricity Report,2026-02-01,Report,IEA,Grid Infrastructure,URL,data/raw/energy_reports/iea_electricity.txt,
```

---

## 7.2 `paragraph_level_dataset.csv`

```csv
paragraph_id,doc_id,company,sector,date,text
P0001,DOC001,Halliburton,Oilfield Services,2026-04-21,"We experienced higher logistics costs..."
P0002,DOC002,IEA,Grid Infrastructure,2026-02-01,"Global electricity demand is expected..."
```

---

## 7.3 `classified_paragraphs.csv`

```csv
paragraph_id,doc_id,category,sentiment,confidence,reason,human_review_status
P0001,DOC001,Oilfield Cost Pressure,Negative,5,"Mentions logistics cost pressure.",Approved
P0002,DOC002,Electricity Demand,Positive,5,"Mentions structural demand growth.",Approved
```

---

## 7.4 `ai_signal_tracker.csv`

```csv
category,grid_equipment_count,oilfield_services_count,grid_sentiment_score,oilfield_sentiment_score
Grid Resilience,120,12,0.72,0.08
Oilfield Cost Pressure,8,95,-0.10,-0.64
Electricity Demand,88,15,0.69,0.12
Policy-Backed Capex,75,20,0.62,0.20
```

---

# 8. AI Classification Categories

```text
1. Oil Supply Disruption
2. Oilfield Cost Pressure
3. Grid Resilience
4. Electricity Demand
5. Policy-Backed Capex
6. Margin / Earnings Risk
```

Each paragraph should receive:

```text
category
sentiment
confidence score
one-sentence reason
human review status
```

---

# 9. Prompt Template

Save this as:

```text
prompts/classification_prompt.md
```

```md
You are assisting an equity research team.

Classify the following paragraph into one or more categories:

1. Oil Supply Disruption
2. Oilfield Cost Pressure
3. Grid Resilience
4. Electricity Demand
5. Policy-Backed Capex
6. Margin / Earnings Risk

Return your answer in JSON format:

{
  "category": "",
  "sentiment": "positive / neutral / negative",
  "confidence": 1-5,
  "reason": ""
}

Rules:
- Do not invent facts.
- Only classify based on the paragraph.
- If the paragraph is irrelevant, return "Irrelevant".
- Keep the reason under 20 words.

Paragraph:
[INSERT TEXT]
```

---

# 10. Basic Python Modules

## `src/text_cleaner.py`

```python
import re
from typing import List

def clean_text(text: str) -> str:
    """Clean raw text from filings, transcripts, or articles."""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\x00", "")
    return text.strip()

def split_into_paragraphs(text: str, min_length: int = 80) -> List[str]:
    """Split text into usable paragraph chunks."""
    raw_paragraphs = re.split(r"\n{2,}|(?<=\.)\s{2,}", text)
    paragraphs = [p.strip() for p in raw_paragraphs if len(p.strip()) >= min_length]
    return paragraphs
```

---

## `src/classifier.py`

```python
import json
from typing import Dict

def build_classification_prompt(paragraph: str, template: str) -> str:
    return template.replace("[INSERT TEXT]", paragraph)

def parse_ai_response(response_text: str) -> Dict:
    """Parse AI JSON response safely."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "category": "Parse Error",
            "sentiment": "neutral",
            "confidence": 0,
            "reason": "AI response could not be parsed."
        }
```

---

## `src/analysis.py`

```python
import pandas as pd

def category_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Count categories by sector."""
    return (
        df.groupby(["sector", "category"])
        .size()
        .reset_index(name="count")
    )

def sentiment_score(sentiment: str) -> int:
    mapping = {
        "positive": 1,
        "neutral": 0,
        "negative": -1
    }
    return mapping.get(str(sentiment).lower(), 0)
```

---

## `src/charts.py`

```python
import pandas as pd
import matplotlib.pyplot as plt

def create_category_bar_chart(df: pd.DataFrame, output_path: str):
    pivot = df.pivot(index="category", columns="sector", values="count").fillna(0)
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Energy Security Signal Frequency")
    ax.set_xlabel("")
    ax.set_ylabel("Number of Mentions")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
```

---

# 11. Git Branching Model

Keep it simple.

```text
main
├── research/industry
├── research/sieyuan
├── research/short-candidate
├── ai/signal-tracker
├── valuation/model
└── deck/final-polish
```

## Branch rules

| Branch                       | Owner          | Purpose                     |
| ---------------------------- | -------------- | --------------------------- |
| `main`                     | Team lead      | Clean, stable version       |
| `research/industry`        | Macro lead     | Industry sources and charts |
| `research/sieyuan`         | Company lead   | Long case research          |
| `research/short-candidate` | Company lead   | Short case research         |
| `ai/signal-tracker`        | AI analyst     | Classification and outputs  |
| `valuation/model`          | Valuation lead | Financial model             |
| `deck/final-polish`        | Deck lead      | Final PPT and narrative     |

---

# 12. Git Commit Style

Use clear commits.

Good examples:

```text
Add IEA electricity demand source notes
Clean Halliburton transcript paragraphs
Add AI classification prompt v1
Export grid resilience heatmap
Update Sieyuan peer comps
Revise short case risk matrix
Add valuation sensitivity table
```

Bad examples:

```text
update
stuff
final
new new final
try again
```

---

# 13. Pull Request Template

Create:

```text
.github/pull_request_template.md
```

```md
## What changed?

Briefly describe the update.

## Which slide does this support?

Example: Slide 4 — Industry Outlook

## Data source

List source files or URLs used.

## Has this been reviewed?

- [ ] Source checked
- [ ] Numbers checked
- [ ] AI output human-reviewed
- [ ] Chart exported
- [ ] Ready for deck
```

---

# 14. `.gitignore`

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
.env

# Jupyter
.ipynb_checkpoints/

# Raw large files
data/raw/**/*.pdf
data/raw/**/*.xlsx
data/raw/**/*.docx

# Temporary exports
outputs/temp/
*.tmp

# OS files
.DS_Store

# API keys
.env
```

Important: do not upload private broker PDFs or licensed databases if you do not have permission.

---

# 15. `requirements.txt`

```txt
pandas
numpy
matplotlib
plotly
openpyxl
python-dotenv
jupyter
tqdm
scikit-learn
sentence-transformers
```

Optional:

```txt
spacy
streamlit
fastapi
uvicorn
pdfplumber
beautifulsoup4
requests
```

---

# 16. Optional Streamlit Dashboard

If you want a simple review dashboard:

```text
streamlit_app/
├── app.py
├── pages/
│   ├── 1_Document_Review.py
│   ├── 2_AI_Classification.py
│   ├── 3_Signal_Tracker.py
│   └── 4_Charts_for_Deck.py
```

## Dashboard features

* Upload cleaned CSV
* View classified paragraphs
* Filter by company / category / sentiment
* Mark AI outputs as approved or rejected
* Export heatmaps
* Export final tables

This is optional. For a competition deadline, notebooks may be faster.

---

# 17. Recommended Workflow

## Step 1 — Create repository

```bash
mkdir ubs-energy-security-pitch
cd ubs-energy-security-pitch
git init
```

---

## Step 2 — Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 3 — Add source files

Put raw files into:

```text
data/raw/
```

Update:

```text
data/processed/source_master.csv
```

---

## Step 4 — Run notebooks in order

```text
01_data_collection_check.ipynb
02_text_cleaning.ipynb
03_ai_classification.ipynb
04_signal_analysis.ipynb
05_valuation_model.ipynb
06_chart_export.ipynb
```

---

## Step 5 — Export charts

Save final charts to:

```text
outputs/charts/
```

Use only those charts in PowerPoint.

---

## Step 6 — Build deck

Use:

```text
deck/working_deck.pptx
```

Then export final:

```text
deck/final_submission_deck.pptx
```

---

# 18. Team Roles in Git

## Member 1 — Industry Lead

Owns:

```text
data/raw/energy_reports/
docs/research_plan.md
notebooks/01_data_collection_check.ipynb
notebooks/04_signal_analysis.ipynb
```

---

## Member 2 — Company / Valuation Lead

Owns:

```text
data/raw/company_transcripts/
notebooks/05_valuation_model.ipynb
outputs/tables/peer_comps.xlsx
outputs/tables/valuation_summary.xlsx
```

---

## Member 3 — AI / Deck Lead

Owns:

```text
prompts/
src/classifier.py
notebooks/03_ai_classification.ipynb
outputs/charts/
deck/
```

---

# 19. Minimum Viable Version

If you only have limited time, build this:

```text
ubs-energy-security-pitch/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── source_master.csv
│   │   ├── classified_paragraphs.csv
│   │   └── valuation_summary.xlsx
├── notebooks/
│   ├── 01_ai_signal_tracker.ipynb
│   ├── 02_valuation_model.ipynb
│   └── 03_chart_export.ipynb
├── prompts/
│   └── classification_prompt.md
├── outputs/
│   ├── charts/
│   └── tables/
└── deck/
    ├── working_deck.pptx
    └── final_submission_deck.pptx
```

This is enough.

---

# 20. Final Recommendation

For this competition, I recommend:

```text
Simple stack:
Python + pandas + Jupyter + LLM API + matplotlib + Excel + PowerPoint + GitHub
```

Do not over-engineer.
The goal is not to build a perfect app.
The goal is to create a credible, traceable, AI-assisted research workflow that produces 3–5 sharp charts for the deck.

The winning standard is:

> Clear thesis, hard evidence, quantified gap, clean deck.

```

```
