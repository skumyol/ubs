"""Configuration constants for the UBS energy-security research pipeline."""

from pathlib import Path

# Root paths - based on this file's location (src/config.py -> project root)
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_TEXT_DIR = DATA_DIR / "raw" / "text"
RAW_PDF_DIR = DATA_DIR / "raw" / "pdf"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
SRC_DIR = ROOT / "src"
PROMPTS_DIR = ROOT / "prompts"
OUTPUTS_DIR = ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
TABLES_DIR = OUTPUTS_DIR / "tables"

# Output files
DOCUMENT_INDEX_PATH = PROCESSED_DIR / "document_index.csv"
PARAGRAPH_DATASET_PATH = PROCESSED_DIR / "paragraph_level_dataset.csv"
CLASSIFIED_PARAGRAPHS_PATH = PROCESSED_DIR / "classified_paragraphs.csv"
CATEGORY_COUNTS_PATH = PROCESSED_DIR / "category_counts.csv"
SIGNAL_TRACKER_PATH = PROCESSED_DIR / "ai_signal_tracker.csv"
KEYWORD_FREQUENCY_PATH = PROCESSED_DIR / "keyword_frequency.csv"

# Source files
SEED_URLS_PATH = ROOT / "sources" / "seed_urls.csv"
RSS_FEEDS_PATH = ROOT / "sources" / "rss_feeds.csv"
CLASSIFICATION_PROMPT_PATH = PROMPTS_DIR / "classification_prompt.md"

# Parameters
MIN_PARAGRAPH_CHARS = 120
MAX_PARAGRAPH_CHARS = 1800
USER_AGENT = "Mozilla/5.0 research-bot/1.0 for academic equity research"
LLM_DELAY_SECONDS = 1.0

# Chart outputs
CATEGORY_BAR_CHART_PATH = CHARTS_DIR / "energy_signal_frequency.png"
SIGNAL_HEATMAP_PATH = CHARTS_DIR / "signal_heatmap.png"
SENTIMENT_COMPARISON_PATH = CHARTS_DIR / "sentiment_comparison.png"
LONG_SHORT_MATRIX_PATH = CHARTS_DIR / "long_short_matrix.png"
