"""Chart generation for stock pitch deck outputs."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict


def create_category_bar_chart(
    df: pd.DataFrame,
    output_path: str,
    figsize: tuple = (10, 6),
    dpi: int = 300,
) -> None:
    """Create grouped bar chart of category mentions by sector.

    Args:
        df: DataFrame with 'category', 'sector', 'count' columns.
        output_path: File path to save PNG.
        figsize: Matplotlib figure size.
        dpi: Resolution for saved image.
    """
    pivot = df.pivot(index="category", columns="sector", values="count").fillna(0)

    ax = pivot.plot(kind="bar", figsize=figsize, width=0.7)
    ax.set_title("Energy Security Signal Frequency", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Number of Mentions", fontsize=12)
    ax.legend(title="Sector", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def create_signal_heatmap(
    tracker_df: pd.DataFrame,
    output_path: str,
    figsize: tuple = (10, 6),
    dpi: int = 300,
) -> None:
    """Create heatmap comparing Grid vs Oilfield signals.

    Args:
        tracker_df: Output from analysis.build_signal_tracker().
        output_path: File path to save PNG.
        figsize: Matplotlib figure size.
        dpi: Resolution for saved image.
    """
    # Extract count columns
    count_cols = [c for c in tracker_df.columns if c.endswith("_count")]
    heatmap_data = tracker_df.set_index("category")[count_cols]
    heatmap_data.columns = [c.replace("_count", "") for c in heatmap_data.columns]

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(heatmap_data.columns)))
    ax.set_xticklabels(heatmap_data.columns)
    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_yticklabels(heatmap_data.index)

    # Add text annotations
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            text = ax.text(
                j, i, int(heatmap_data.iloc[i, j]),
                ha="center", va="center", color="black", fontweight="bold",
            )

    ax.set_title("Energy Security Signal Heatmap", fontsize=14, fontweight="bold")
    fig.colorbar(im, ax=ax, label="Mention Count")

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def create_sentiment_comparison(
    df: pd.DataFrame,
    output_path: str,
    figsize: tuple = (10, 6),
    dpi: int = 300,
) -> None:
    """Create grouped bar chart of sentiment scores by category and sector.

    Args:
        df: DataFrame with 'category', 'sector', 'sentiment_score'.
        output_path: File path to save PNG.
        figsize: Matplotlib figure size.
        dpi: Resolution for saved image.
    """
    sentiment = (
        df.groupby(["category", "sector"])["sentiment"]
        .apply(lambda s: s.map({"positive": 1, "neutral": 0, "negative": -1}).mean())
        .reset_index(name="avg_sentiment")
    )

    pivot = sentiment.pivot(index="category", columns="sector", values="avg_sentiment").fillna(0)

    ax = pivot.plot(kind="bar", figsize=figsize, width=0.7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Sentiment by Category and Sector", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Average Sentiment Score", fontsize=12)
    ax.legend(title="Sector", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def create_long_short_matrix_table(
    output_path: str,
    figsize: tuple = (12, 6),
    dpi: int = 300,
) -> None:
    """Create the Long/Short comparison matrix as a formatted table image.

    This is Slide 9: the slide judges remember.
    """
    data = {
        "Dimension": [
            "Energy-security role",
            "Demand visibility",
            "Policy support",
            "Geopolitical exposure",
            "Margin risk",
            "Valuation risk",
            "Catalyst",
        ],
        "Long Sieyuan": [
            "Builds resilient power infrastructure",
            "Multi-year grid capex",
            "High",
            "Demand tailwind",
            "Competition / materials",
            "Re-rating potential",
            "Grid orders, overseas growth",
        ],
        "Short Oilfield-Service": [
            "Exposed to disrupted fuel infrastructure",
            "Cyclical upstream capex",
            "Medium / indirect",
            "Operating risk",
            "Logistics / utilization / delays",
            "Cyclical de-rating risk",
            "Cost warning, capex delay, rig weakness",
        ],
    }

    df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="left",
        loc="center",
        colColours=["#1f4e79"] * 3,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)

    # Style header
    for i in range(3):
        table[(0, i)].set_text_props(color="white", fontweight="bold")

    # Alternate row colors
    for i in range(1, len(df) + 1):
        color = "#f2f2f2" if i % 2 == 0 else "white"
        for j in range(3):
            table[(i, j)].set_facecolor(color)

    ax.set_title(
        "Same Energy-Security Theme, Opposite Earnings Quality",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()


def create_signal_trends_timeseries(
    df: pd.DataFrame,
    output_path: str,
    figsize: tuple = (12, 6),
    dpi: int = 300,
) -> None:
    """Create time-series line chart of signal trends by month.

    Shows the evolution of key signal categories over time,
    revealing narrative shifts and momentum trends.

    Args:
        df: DataFrame with 'date', 'category', 'sector', 'sentiment' columns.
        output_path: File path to save PNG.
        figsize: Matplotlib figure size.
        dpi: Resolution for saved image.
    """
    import numpy as np

    # Convert date to datetime and filter valid dates
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    if len(df) == 0:
        print("[WARNING] No valid dates found for time-series chart")
        return

    # Extract year-month for aggregation
    df['year_month'] = df['date'].dt.to_period('M')

    # Focus on key thesis categories
    thesis_categories = {
        'Grid Resilience': 'Grid Infrastructure',
        'Electricity Demand': 'Grid Infrastructure',
        'Policy-Backed Capex': 'Grid Infrastructure',
        'Oil Supply Disruption': 'Oilfield Services',
        'Margin/Earnings Risk': 'Oilfield Services',
        'Oilfield Cost Pressure': 'Oilfield Services',
    }

    # Sentiment scoring
    sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
    df['sentiment_score'] = df['sentiment'].map(sentiment_map).fillna(0)

    # Group by month and category
    monthly_signals = (
        df.groupby(['year_month', 'category'])
        .agg({
            'sentiment_score': 'mean',
            'paragraph_id': 'count'
        })
        .reset_index()
    )
    monthly_signals.columns = ['year_month', 'category', 'avg_sentiment', 'count']

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Color scheme for categories
    colors = {
        'Grid Resilience': '#2E7D32',  # Green
        'Electricity Demand': '#1976D2',  # Blue
        'Policy-Backed Capex': '#7B1FA2',  # Purple
        'Oil Supply Disruption': '#C62828',  # Red
        'Margin/Earnings Risk': '#F57C00',  # Orange
        'Oilfield Cost Pressure': '#6D4C41',  # Brown
    }

    # Plot each category
    for category in thesis_categories.keys():
        cat_data = monthly_signals[monthly_signals['category'] == category]
        if len(cat_data) > 1:  # Need at least 2 points for a line
            x_vals = [str(ym) for ym in cat_data['year_month']]
            # Normalize count for visibility (0-100 scale)
            counts = cat_data['count'].values
            normalized = 50 + (counts - counts.min()) / (counts.max() - counts.min() + 0.1) * 50

            ax.plot(
                range(len(x_vals)),
                normalized,
                marker='o',
                linewidth=2.5,
                markersize=8,
                label=category,
                color=colors.get(category, '#666666'),
            )

    # Styling
    ax.set_title("Signal Trends Over Time\n(Volume-Weighted by Month)",
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Signal Volume Index (normalized)", fontsize=12)

    # X-axis labels
    all_months = sorted(df['year_month'].unique())
    ax.set_xticks(range(len(all_months)))
    ax.set_xticklabels([str(m) for m in all_months], rotation=45, ha='right')

    # Legend
    ax.legend(
        title="Signal Category",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9,
    )

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 105)

    # Add annotation for grid vs oilfield
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.text(0.02, 0.98, "Grid signals (Green/Blue/Purple)\nOilfield signals (Red/Orange/Brown)",
            transform=ax.transAxes, fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] Time-series chart: {output_path}")
