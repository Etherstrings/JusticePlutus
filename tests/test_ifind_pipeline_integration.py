import src.core.pipeline as pipeline_module
from data_provider.ifind_fetcher import IFindFetcher
from src.core.pipeline import StockAnalysisPipeline
from src.ifind.schemas import (
    FinancialQualitySummary,
    FinancialStatementPack,
    IFindFinancialPack,
    ValuationPack,
)


class DummyConfig:
    def __init__(
        self,
        enable_ifind,
        enable_ifind_analysis_enhancement,
        enable_ths_pro_data=False,
    ):
        self.enable_ths_pro_data = enable_ths_pro_data
        self.enable_ifind = enable_ifind
        self.enable_ifind_analysis_enhancement = enable_ifind_analysis_enhancement


class FakeIFindService:
    def __init__(self, pack):
        self.pack = pack
        self.calls = []

    def get_financial_pack(self, stock_code, stock_name=None):
        self.calls.append((stock_code, stock_name))
        return self.pack


class _InitConfig:
    max_workers = 1
    save_context_snapshot = False
    report_output_dir = None
    bocha_api_keys = []
    tavily_api_keys = []
    brave_api_keys = []
    serpapi_keys = []
    minimax_api_keys = []
    news_max_age_days = 3
    enable_realtime_quote = False
    enable_chip_distribution = False
    realtime_source_priority = "efinance"


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


def test_pipeline_backfills_realtime_with_same_day_ifind_valuation(monkeypatch):
    class _FakeDate:
        @staticmethod
        def today():
            class _Today:
                @staticmethod
                def isoformat():
                    return "2026-04-02"

            return _Today()

    pack = _build_pack()
    pack.valuation = ValuationPack(
        stock_code="600519",
        stock_name="贵州茅台",
        as_of_date="2026-04-01",
        volume_ratio=0.858,
        turnover_rate=0.233,
        pe_ttm=23.6,
        pb=8.1,
        total_market_value=1_820_000_000_000.0,
        circulating_market_value=980_000_000_000.0,
    )

    monkeypatch.setattr(pipeline_module, "date", _FakeDate)

    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(enable_ifind=True, enable_ifind_analysis_enhancement=True)
    pipeline.ifind_service = FakeIFindService(pack)

    enhanced = pipeline._attach_ifind_context(
        {
            "code": "600519",
            "stock_name": "贵州茅台",
            "date": "2026-04-01",
            "realtime": {
                "price": 1459.44,
                "pb_ratio": 7.109509,
            },
        },
        code="600519",
        stock_name="贵州茅台",
    )

    assert enhanced["realtime"]["pe_ratio"] == 23.6
    assert enhanced["realtime"]["volume_ratio"] == 0.858
    assert enhanced["realtime"]["volume_ratio_desc"] == "正常"
    assert enhanced["realtime"]["turnover_rate"] == 0.233
    assert enhanced["realtime"]["pb_ratio"] == 7.109509
    assert enhanced["realtime"]["total_mv"] == 1_820_000_000_000.0
    assert enhanced["realtime"]["circ_mv"] == 980_000_000_000.0


def test_pipeline_skips_realtime_backfill_when_ifind_valuation_is_stale(monkeypatch):
    class _FakeDate:
        @staticmethod
        def today():
            class _Today:
                @staticmethod
                def isoformat():
                    return "2026-04-01"

            return _Today()

    monkeypatch.setattr(pipeline_module, "date", _FakeDate)

    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(enable_ifind=True, enable_ifind_analysis_enhancement=True)
    pipeline.ifind_service = FakeIFindService(_build_pack())

    enhanced = pipeline._attach_ifind_context(
        {
            "code": "600519",
            "stock_name": "贵州茅台",
            "realtime": {
                "price": 1459.44,
            },
        },
        code="600519",
        stock_name="贵州茅台",
    )

    assert "pe_ratio" not in enhanced["realtime"]
    assert "total_mv" not in enhanced["realtime"]
    assert "circ_mv" not in enhanced["realtime"]


def test_pipeline_injects_ifind_context_when_ths_pro_mode_enabled():
    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(
        enable_ths_pro_data=True,
        enable_ifind=False,
        enable_ifind_analysis_enhancement=True,
    )
    pipeline.ifind_service = FakeIFindService(_build_pack())

    enhanced = pipeline._attach_ifind_context(
        {"code": "600519", "stock_name": "贵州茅台"},
        code="600519",
        stock_name="贵州茅台",
    )

    assert enhanced["ifind_financials"]["report_period"] == "2025-12-31"
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


def test_pipeline_passes_ifind_fetcher_to_manager_when_service_available(monkeypatch):
    captured = {}
    fake_service = object()

    class FakeManager:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

    class FakeSearchService:
        def __init__(self, *args, **kwargs):
            self.is_available = False

    monkeypatch.setattr(pipeline_module.StockAnalysisPipeline, "_build_ifind_service", lambda self: fake_service)
    monkeypatch.setattr(pipeline_module, "DataFetcherManager", FakeManager)
    monkeypatch.setattr(pipeline_module, "get_db", lambda: object())
    monkeypatch.setattr(pipeline_module, "StockTrendAnalyzer", lambda: object())
    monkeypatch.setattr(pipeline_module, "GeminiAnalyzer", lambda: object())
    monkeypatch.setattr(pipeline_module, "NotificationService", lambda source_message=None: object())
    monkeypatch.setattr(pipeline_module, "SearchService", FakeSearchService)

    pipeline_module.StockAnalysisPipeline(config=_InitConfig())

    assert isinstance(captured["ifind_fetcher"], IFindFetcher)
    assert captured["ifind_fetcher"].service is fake_service
