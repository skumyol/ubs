"""Single source of truth for the active UBS pitch pair."""

from dataclasses import dataclass

from src.company_facts import COMPANY_FACTS


@dataclass(frozen=True)
class PairLeg:
    name: str
    ticker: str
    ticker_cn: str
    sector: str
    role: str


LONG_LEG = PairLeg(
    name="Dongfang Electric",
    ticker="1072.HK",
    ticker_cn="600875.SH",
    sector="Grid Infrastructure",
    role="LONG",
)

SHORT_LEG = PairLeg(
    name="Sungrow",
    ticker="300274.SZ",
    ticker_cn="300274.SZ",
    sector="Inverter & Storage Equipment",
    role="SHORT",
)

PAIR_NAME = "Dongfang Electric / Sungrow"
PAIR_TAGLINE = "From Clean-Tech Growth to Grid-Backbone Value"
PAIR_ONE_LINER = (
    "We recommend LONG Dongfang Electric / SHORT Sungrow because "
    "Dongfang offers underappreciated order visibility and infrastructure-backed earnings durability, "
    "while Sungrow's premium multiple is vulnerable to inverter/storage demand normalization and margin compression."
)

DECK_TITLE = "Long the Grid, Short the Bottleneck"
DECK_SUBTITLE = (
    f"{PAIR_TAGLINE}  |  Long {LONG_LEG.name} ({LONG_LEG.ticker}) / "
    f"Short {SHORT_LEG.name} ({SHORT_LEG.ticker})"
)
TEAM_LINE = "Serkan Kumyol | Kirill Shatilov | Hong Kong University of Science and Technology"

SLIDE_TITLES = {
    "variant_view": "Variant View: From Clean-Tech Growth to Grid-Backbone Value",
    "industry": "Energy Transition Shifts from Capacity to System Reliability",
    "long_case": "Dongfang Electric: Grid Tech Leader with RMB 140B Backlog",
    "short_case": "Sungrow: High-Expectation Inverter Leader Facing Demand Normalization",
    "comparison": "Same Energy-Transition Theme, Opposite Cycle Position",
    "ai_module": "Thematic Evidence Tracker: Text-Based Signal Compilation",
}

VALUATION_FALLBACK = {
    "long_expected_return": 96.8,
    "short_expected_return": -5.4,
    "pair_spread_return": 102.2,
}

TRADER_FALLBACK = {
    "recommended_notional_mm": 2.3,
    "recommended_position_pct": 2.3,
    "pair_vol_annual": 35.0,
}

CATALYSTS = [
    "State Grid RMB 4T capex over the 15th FYP period",
    "Dongfang synchronous condenser orders and grid flexibility wins",
    "Sungrow inverter/storage demand normalization and margin pressure visibility",
]

DCF_ASSUMPTIONS = {
    "dongfang": {
        "fcf0_rmb_bn": 2.8,  # Normalized FCF base (adjusted for working capital swings)
        "growth_rate": 0.17,  # 17% FCF CAGR (backlog conversion + grid capex)
        "terminal_growth": 0.04,  # 4% terminal growth
        "wacc": 0.085,  # 8.5% WACC
        "years": 5,
        "shares_outstanding_bn": COMPANY_FACTS["dongfang"]["shares_outstanding_bn"],
    },
    "sungrow": {
        "fcf0_rmb_bn": 8.0,  # Higher historical FCF but pressured in 2026
        "growth_rate": 0.08,  # 8% FCF CAGR (demand normalization)
        "terminal_growth": 0.03,  # 3% terminal growth
        "wacc": 0.095,  # 9.5% WACC (higher cyclical/competition risk)
        "years": 5,
        "shares_outstanding_bn": COMPANY_FACTS["sungrow"]["shares_outstanding_bn"],
    },
}

DCF_NOTE = (
    "Use the DCF as a normalization cross-check against the scenario-based valuation; "
    "working-capital volatility is significant in equipment makers, so normalized FCF is preferred."
)

QNA_DEFAULTS = {
    "long_name": LONG_LEG.name,
    "short_name": SHORT_LEG.name,
    "long_ticker": LONG_LEG.ticker,
    "short_ticker": SHORT_LEG.ticker,
}
