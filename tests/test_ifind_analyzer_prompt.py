from src.analyzer import GeminiAnalyzer


def test_prompt_includes_ifind_section_when_pack_available():
    analyzer = GeminiAnalyzer()

    prompt = analyzer._format_prompt(
        {
            "code": "600519",
            "stock_name": "贵州茅台",
            "date": "2026-03-30",
            "today": {},
            "ifind_financials": {
                "report_period": "2025-12-31",
                "revenue": 187170000000.0,
                "net_profit": 86230000000.0,
                "roe": 34.1,
            },
            "ifind_valuation": {
                "as_of_date": "2026-03-30",
                "pe_ttm": 23.6,
                "pb": 8.1,
                "total_market_value": 1964000000000.0,
            },
            "ifind_forecast": {
                "expected_growth_rate": 14.2,
                "periods": [
                    {"period_end": "2026-12-31", "net_profit": 95215849886.11},
                    {"period_end": "2027-12-31", "net_profit": 100687506345.25},
                ],
            },
            "ifind_quality_summary": {
                "profit_quality": "strong",
                "cashflow_health": "healthy",
                "leverage_risk": "low",
                "growth_visibility": "medium",
            },
        },
        "贵州茅台",
        news_context=None,
    )

    assert "## 基本面与估值增强" in prompt
    assert "最新财报期" in prompt
    assert "ROE" in prompt
    assert "一致预期净利润增速" in prompt
    assert "盈利质量" in prompt


def test_prompt_omits_ifind_section_when_no_ifind_data():
    analyzer = GeminiAnalyzer()

    prompt = analyzer._format_prompt(
        {
            "code": "600519",
            "stock_name": "贵州茅台",
            "today": {},
        },
        "贵州茅台",
    )

    assert "## 基本面与估值增强" not in prompt
