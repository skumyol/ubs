"""Structured local facts for the Dongfang/Jereh pitch.

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
    "jereh": {
        "name": "Jereh Oilfield Services Group Co., Ltd.",
        "ticker": "002353.SZ",
        "website": "https://www.jereh.com",
        "revenue_2025_rmb_bn": 16.22,
        "revenue_growth_2025": 0.2148,
        "net_profit_2025_rmb_bn": 2.680,
        "net_profit_growth_2025": 0.0203,
        "operating_cash_flow_2025_rmb_bn": 5.378,
        "operating_cash_flow_growth_2025": 1.0737,
        "eps_2025": 2.64,
        "dividend_per_10_shares": 7.00,
        "pe_ttm": 46.48,
        "pb": 5.55,
        "market_cap_rmb_bn": 130.3,
        "latest_price": 127.78,
        "analyst_target_price": 128.12,
        "shares_outstanding_bn": 1.02,
        "q1_2026_revenue_rmb_bn": 3.29,
        "q1_2026_revenue_growth": 0.2248,
        "q1_2026_net_profit_rmb_bn": 0.588,
        "q1_2026_net_profit_growth": 0.2632,
        "overseas_revenue_2025_rmb_bn": 7.84,
        "overseas_revenue_growth": 0.2985,
        "rd_expense_2025_rmb_bn": 0.551,
        "rd_percent_revenue": 0.034,
        "strategic_focus": [
            "oil and gas equipment",
            "international oilfield services",
            "new energy battery materials",
            "AI-driven equipment modernization",
        ],
        "key_risks": [
            "oil and gas price cyclicality",
            "geopolitical export risk",
            "high customer concentration",
            "project execution and cost overrun risk",
            "margin pressure from revenue growing faster than profit",
        ],
    },
}

