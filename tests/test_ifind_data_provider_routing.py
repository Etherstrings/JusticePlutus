from datetime import date
from types import SimpleNamespace

import pandas as pd

from data_provider.base import BaseFetcher, DataFetcherManager, DataSourceUnavailableError
from data_provider.realtime_types import RealtimeSource, UnifiedRealtimeQuote
from src.ifind.schemas import IFindFinancialPack, ValuationPack


def _sample_daily_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-03-28",
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 101.0,
                "volume": 100000,
                "amount": 10100000.0,
                "pct_chg": 1.0,
            },
            {
                "date": "2026-03-31",
                "open": 101.0,
                "high": 103.0,
                "low": 100.5,
                "close": 102.5,
                "volume": 120000,
                "amount": 12300000.0,
                "pct_chg": 1.49,
            },
        ]
    )


class _DummyDailyFetcher(BaseFetcher):
    def __init__(self, name: str, calls: list[str], df: pd.DataFrame | None = None, err: Exception | None = None):
        self.name = name
        self.priority = 1
        self._calls = calls
        self._df = df
        self._err = err

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame()

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        return df

    def get_daily_data(self, stock_code: str, start_date: str | None = None, end_date: str | None = None, days: int = 30):
        self._calls.append(self.name)
        if self._err is not None:
            raise self._err
        return self._df


class _DummyRealtimeFetcher(_DummyDailyFetcher):
    def __init__(self, name: str, calls: list[str], quote: UnifiedRealtimeQuote | None = None, err: Exception | None = None):
        super().__init__(name=name, calls=calls, err=err)
        self._quote = quote

    def get_realtime_quote(self, stock_code: str, source: str | None = None):
        self._calls.append(self.name if source is None else f"{self.name}:{source}")
        if self._err is not None:
            raise self._err
        return self._quote


class _DummyIFindFetcher(_DummyDailyFetcher):
    name = "IFindFetcher"

    def __init__(
        self,
        calls: list[str],
        daily_df: pd.DataFrame | None = None,
        realtime_quote: UnifiedRealtimeQuote | None = None,
        daily_error: Exception | None = None,
        realtime_error: Exception | None = None,
        supports_daily: bool = True,
        supports_realtime: bool = True,
        stock_name: str = "",
    ):
        super().__init__(name="IFindFetcher", calls=calls, df=daily_df, err=daily_error)
        self.priority = -1
        self._realtime_quote = realtime_quote
        self._realtime_error = realtime_error
        self._supports_daily = supports_daily
        self._supports_realtime = supports_realtime
        self._stock_name = stock_name

    def supports_daily_data(self) -> bool:
        return self._supports_daily

    def supports_realtime_quote(self) -> bool:
        return self._supports_realtime

    def get_realtime_quote(self, stock_code: str):
        self._calls.append(self.name)
        if self._realtime_error is not None:
            raise self._realtime_error
        return self._realtime_quote

    def get_stock_name(self, stock_code: str):
        self._calls.append(f"{self.name}:stock_name")
        return self._stock_name


class _DummyNamedFetcher(_DummyDailyFetcher):
    def __init__(self, name: str, calls: list[str], stock_name: str):
        super().__init__(name=name, calls=calls)
        self._stock_name = stock_name

    def get_stock_name(self, stock_code: str):
        self._calls.append(f"{self.name}:stock_name")
        return self._stock_name


def test_daily_data_prefers_ifind_fetcher_when_ths_mode_enabled(monkeypatch):
    calls: list[str] = []
    ifind = _DummyIFindFetcher(calls=calls, daily_df=_sample_daily_df())
    fallback = _DummyDailyFetcher(name="EfinanceFetcher", calls=calls, df=_sample_daily_df())
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(enable_ths_pro_data=True, enable_ifind=False),
    )

    df, source = manager.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31")

    assert source == "IFindFetcher"
    assert list(df["close"]) == [101.0, 102.5]
    assert calls == ["IFindFetcher"]


def test_realtime_quote_falls_back_when_ifind_fetcher_unavailable(monkeypatch):
    calls: list[str] = []
    ifind = _DummyIFindFetcher(
        calls=calls,
        supports_realtime=True,
        realtime_error=DataSourceUnavailableError("not entitled"),
    )
    fallback = _DummyRealtimeFetcher(
        name="EfinanceFetcher",
        calls=calls,
        quote=UnifiedRealtimeQuote(
            code="600519",
            source=RealtimeSource.EFINANCE,
            price=123.45,
        ),
    )
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(
            enable_ths_pro_data=True,
            enable_ifind=False,
            enable_realtime_quote=True,
            realtime_source_priority="efinance",
        ),
    )

    quote = manager.get_realtime_quote("600519")

    assert quote is not None
    assert quote.source == RealtimeSource.EFINANCE
    assert quote.price == 123.45
    assert calls == ["IFindFetcher", "EfinanceFetcher"]


def test_realtime_quote_prefers_ifind_market_metrics_before_external_supplement(monkeypatch):
    calls: list[str] = []
    ifind = _DummyIFindFetcher(
        calls=calls,
        supports_realtime=True,
        realtime_quote=UnifiedRealtimeQuote(
            code="600519",
            source=RealtimeSource.IFIND,
            price=1459.44,
            turnover_rate=0.23257871704630456,
            amplitude=1.18,
            pb_ratio=7.109509,
        ),
    )
    ifind.service = SimpleNamespace(
        get_financial_pack=lambda stock_code, stock_name=None: IFindFinancialPack(
            stock_code=stock_code,
            valuation=ValuationPack(
                stock_code=stock_code,
                as_of_date=date.today().isoformat(),
                volume_ratio=0.858,
                pe_ttm=21.21,
                pb=7.1094,
                total_market_value=1827613242579.6,
                circulating_market_value=1827613200000.0,
            ),
        )
    )
    fallback = _DummyRealtimeFetcher(
        name="EfinanceFetcher",
        calls=calls,
        quote=UnifiedRealtimeQuote(
            code="600519",
            source=RealtimeSource.EFINANCE,
            price=1459.44,
            volume_ratio=0.86,
            turnover_rate=0.23,
            pe_ratio=20.3,
            pb_ratio=7.11,
            total_mv=1827000000000.0,
            circ_mv=1827000000000.0,
        ),
    )
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(
            enable_ths_pro_data=True,
            enable_ifind=False,
            enable_ifind_analysis_enhancement=True,
            enable_realtime_quote=True,
            realtime_source_priority="efinance",
        ),
    )

    quote = manager.get_realtime_quote("600519")

    assert quote is not None
    assert quote.source == RealtimeSource.IFIND
    assert quote.volume_ratio == 0.858
    assert quote.pe_ratio == 21.21
    assert quote.total_mv == 1827613242579.6
    assert quote.circ_mv == 1827613200000.0
    assert calls == ["IFindFetcher"]


def test_realtime_quote_accepts_previous_trading_day_ifind_metrics_before_open(monkeypatch):
    class _FakeDate:
        @staticmethod
        def today():
            class _Today:
                @staticmethod
                def isoformat():
                    return "2026-04-02"

            return _Today()

    class _FakeDateTime:
        @classmethod
        def now(cls):
            class _Now:
                hour = 0
                minute = 26

            return _Now()

    calls: list[str] = []
    ifind = _DummyIFindFetcher(
        calls=calls,
        supports_realtime=True,
        realtime_quote=UnifiedRealtimeQuote(
            code="600519",
            source=RealtimeSource.IFIND,
            price=1459.44,
            turnover_rate=0.23257871704630456,
            amplitude=1.18,
            pb_ratio=7.109509,
        ),
    )
    ifind.service = SimpleNamespace(
        get_financial_pack=lambda stock_code, stock_name=None: IFindFinancialPack(
            stock_code=stock_code,
            valuation=ValuationPack(
                stock_code=stock_code,
                as_of_date="2026-04-01",
                volume_ratio=0.858,
                pe_ttm=21.21,
                pb=7.1094,
                total_market_value=1827613242579.6,
                circulating_market_value=1827613200000.0,
            ),
        )
    )
    fallback = _DummyRealtimeFetcher(
        name="EfinanceFetcher",
        calls=calls,
        quote=UnifiedRealtimeQuote(
            code="600519",
            source=RealtimeSource.EFINANCE,
            price=1459.44,
            volume_ratio=0.86,
            turnover_rate=0.23,
            pe_ratio=20.3,
            pb_ratio=7.11,
            total_mv=1827000000000.0,
            circ_mv=1827000000000.0,
        ),
    )
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr("data_provider.base.date", _FakeDate)
    monkeypatch.setattr("data_provider.base.datetime", _FakeDateTime)
    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(
            enable_ths_pro_data=True,
            enable_ifind=False,
            enable_ifind_analysis_enhancement=True,
            enable_realtime_quote=True,
            realtime_source_priority="efinance",
        ),
    )

    quote = manager.get_realtime_quote("600519")

    assert quote is not None
    assert quote.source == RealtimeSource.IFIND
    assert quote.volume_ratio == 0.858
    assert quote.pe_ratio == 21.21
    assert quote.total_mv == 1827613242579.6
    assert quote.circ_mv == 1827613200000.0
    assert calls == ["IFindFetcher"]


def test_stock_name_prefers_ifind_lookup_before_external_when_static_missing(monkeypatch):
    calls: list[str] = []
    ifind = _DummyIFindFetcher(calls=calls, stock_name="贵州茅台")
    fallback = _DummyNamedFetcher(name="EfinanceFetcher", calls=calls, stock_name="外部名称")
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr("data_provider.base.STOCK_NAME_MAP", {})
    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(enable_ths_pro_data=True, enable_ifind=False),
    )

    name = manager.get_stock_name("600519", allow_realtime=False)

    assert name == "贵州茅台"
    assert calls == ["IFindFetcher:stock_name"]
