"""Structured local facts for the Dongfang/Sungrow pitch.

These figures come from the manually collected company summaries in
`data/raw/text/DOC_*_2025_Annual_Summary.txt` and the consolidated pair
analysis note. They are used when live market data or LLM calls are unavailable.
"""

from __future__ import annotations


AS_OF_DATE = "2026-04-30"

COMPANY_FACTS = {
    "dongfang": {
        "name": "Dongfang Electric Corporation Limited",
        "ticker": "600875.SH / 01072.HK",
        "website": "https://www.dec-ltd.cn",
        "revenue_2025_rmb_bn": 78.62,
        "revenue_growth_2025": 0.1280,
        "net_profit_2025_rmb_bn": 3.831,
        "net_profit_growth_2025": 0.3111,
        "operating_cash_flow_2025_rmb_bn": 2.01,
        "operating_cash_flow_growth_2025": -0.7998,
        "eps_2025": 1.15,
        "dividend_per_10_shares": 5.30,
        "pe_ttm": 36.07,
        "pb": 3.06,
        "market_cap_rmb_bn": 138.2,
        "analyst_target_price": 42.68,
        "shares_outstanding_bn": 3.33,
        "strategic_focus": [
            "clean energy equipment",
            "grid infrastructure",
            "State Grid contracts",
            "new-type power system",
            "source-grid-load-storage integration",
            "hydrogen and energy storage",
        ],
        "key_risks": [
            "state-owned utility customer concentration",
            "operating cash flow decline from working-capital swings",
            "policy execution risk",
            "large project execution risk",
        ],
    },
    "sungrow": {
        "name": "Sungrow Power Supply Co., Ltd.",
        "ticker": "300274.SZ",
        "website": "https://www.sungrowpower.com",
        "revenue_2025_rmb_bn": 89.18,
        "revenue_growth_2025": 0.146,
        "net_profit_2025_rmb_bn": 13.5,
        "net_profit_growth_2025": 0.22,
        "operating_cash_flow_2025_rmb_bn": 8.2,
        "operating_cash_flow_growth_2025": 0.15,
        "eps_2025": 0.92,
        "dividend_per_10_shares": 3.50,
        "pe_ttm": 45.0,
        "pb": 8.5,
        "market_cap_rmb_bn": 180.0,
        "latest_price": 98.50,
        "analyst_target_price": 95.0,
        "shares_outstanding_bn": 1.47,
        "q1_2026_revenue_rmb_bn": 15.2,
        "q1_2026_revenue_growth": -0.183,
        "q1_2026_net_profit_rmb_bn": 2.1,
        "q1_2026_net_profit_growth": -0.401,
        "overseas_revenue_2025_rmb_bn": 45.6,
        "overseas_revenue_growth": 0.25,
        "rd_expense_2025_rmb_bn": 4.5,
        "rd_percent_revenue": 0.05,
        "strategic_focus": [
            "PV inverters",
            "energy storage systems",
            "wind power converters",
            "EV charging solutions",
            "hydrogen production equipment",
        ],
        "key_risks": [
            "inverter price compression amid oversupply",
            "storage margin pressure from competition",
            "overseas market policy and trade risks",
            "demand normalization after rapid growth",
            "high valuation expectations",
        ],
    },
}
