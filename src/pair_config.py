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
    name="Yantai Jereh",
    ticker="002353.SZ",
    ticker_cn="002353.SZ",
    sector="Oilfield Services",
    role="SHORT",
)

PAIR_NAME = "Dongfang Electric / Yantai Jereh"
PAIR_TAGLINE = "Energy security is moving from barrels to electrons"
PAIR_ONE_LINER = (
    "We recommend LONG Dongfang Electric / SHORT Yantai Jereh because "
    "Dongfang is leveraged to China's new-type power system buildout, while "
    "Jereh remains tied to fossil-adjacent oilfield services with weaker structural upside."
)

DECK_TITLE = "Long the Grid, Short the Bottleneck"
DECK_SUBTITLE = (
    f"{PAIR_TAGLINE}  |  Long {LONG_LEG.name} ({LONG_LEG.ticker}) / "
    f"Short {SHORT_LEG.name} ({SHORT_LEG.ticker})"
)

SLIDE_TITLES = {
    "variant_view": "Variant View: The Real Energy-Security Trade Is Grid Resilience",
    "industry": "Electricity Continuity Is Becoming Strategic Infrastructure",
    "long_case": "Dongfang Electric: Grid Tech Leader with RMB 140B Backlog",
    "short_case": "Yantai Jereh: Fossil-Cyclical with Policy Headwinds",
    "comparison": "Same Energy-Security Theme, Opposite Earnings Quality",
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
    "Jereh order updates and oilfield activity commentary",
]

DCF_ASSUMPTIONS = {
    "dongfang": {
        "fcf0_rmb_bn": 3.4,
        "growth_rate": 0.18,
        "terminal_growth": 0.04,
        "wacc": 0.085,
        "years": 5,
        "shares_outstanding_bn": COMPANY_FACTS["dongfang"]["shares_outstanding_bn"],
    },
    "jereh": {
        "fcf0_rmb_bn": 2.2,
        "growth_rate": 0.08,
        "terminal_growth": 0.03,
        "wacc": 0.095,
        "years": 5,
        "shares_outstanding_bn": COMPANY_FACTS["jereh"]["shares_outstanding_bn"],
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
