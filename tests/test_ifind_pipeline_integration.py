from src.core.pipeline import StockAnalysisPipeline
from src.ifind.schemas import (
    FinancialQualitySummary,
    FinancialStatementPack,
    IFindFinancialPack,
    ValuationPack,
)


class DummyConfig:
    def __init__(self, enable_ifind, enable_ifind_analysis_enhancement):
        self.enable_ifind = enable_ifind
        self.enable_ifind_analysis_enhancement = enable_ifind_analysis_enhancement


class FakeIFindService:
    def __init__(self, pack):
        self.pack = pack
        self.calls = []

    def get_financial_pack(self, stock_code, stock_name=None):
        self.calls.append((stock_code, stock_name))
        return self.pack


def _build_pack():
    return IFindFinancialPack(
        stock_code="600519",
        stock_name="贵州茅台",
        financials=FinancialStatementPack(
            stock_code="600519",
            stock_name="贵州茅台",
            report_period="2025-12-31",
            revenue=187170000000.0,
            roe=34.1,
        ),
        valuation=ValuationPack(
            stock_code="600519",
            stock_name="贵州茅台",
            as_of_date="2026-03-30",
            pe_ttm=23.6,
            pb=8.1,
        ),
        quality_summary=FinancialQualitySummary(
            profit_quality="strong",
            cashflow_health="healthy",
            leverage_risk="low",
            growth_visibility="medium",
        ),
    )


def test_pipeline_injects_ifind_context_when_flags_enabled():
    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(enable_ifind=True, enable_ifind_analysis_enhancement=True)
    pipeline.ifind_service = FakeIFindService(_build_pack())

    enhanced = pipeline._attach_ifind_context(
        {"code": "600519", "stock_name": "贵州茅台"},
        code="600519",
        stock_name="贵州茅台",
    )

    assert enhanced["ifind_financials"]["report_period"] == "2025-12-31"
    assert enhanced["ifind_valuation"]["pe_ttm"] == 23.6
    assert enhanced["ifind_quality_summary"]["profit_quality"] == "strong"
    assert pipeline.ifind_service.calls == [("600519", "贵州茅台")]


def test_pipeline_skips_ifind_when_feature_disabled():
    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(enable_ifind=False, enable_ifind_analysis_enhancement=False)
    pipeline.ifind_service = FakeIFindService(_build_pack())

    enhanced = pipeline._attach_ifind_context(
        {"code": "600519", "stock_name": "贵州茅台"},
        code="600519",
        stock_name="贵州茅台",
    )

    assert "ifind_financials" not in enhanced
    assert pipeline.ifind_service.calls == []


def test_pipeline_skips_ifind_when_service_unavailable():
    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(enable_ifind=True, enable_ifind_analysis_enhancement=True)
    pipeline.ifind_service = None

    original = {"code": "600519", "stock_name": "贵州茅台"}
    enhanced = pipeline._attach_ifind_context(
        original,
        code="600519",
        stock_name="贵州茅台",
    )

    assert enhanced == original
