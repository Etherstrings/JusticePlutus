import pandas as pd

from data_provider.ifind_fetcher import IFindFetcher
from data_provider.realtime_types import RealtimeSource


class _FakeIFindService:
    def __init__(self, daily_payload=None, realtime_payload=None, stock_name=""):
        self.daily_payload = daily_payload
        self.realtime_payload = realtime_payload
        self.stock_name = stock_name

    def supports_daily_data(self):
        return True

    def supports_realtime_quote(self):
        return True

    def get_daily_data(self, stock_code, start_date, end_date):
        return self.daily_payload

    def get_realtime_quote(self, stock_code):
        return self.realtime_payload

    def get_stock_name(self, stock_code):
        return self.stock_name


def test_ifind_fetcher_normalizes_official_history_payload():
    fetcher = IFindFetcher(
        _FakeIFindService(
            daily_payload={
                "tables": [
                    {
                        "thscode": "600519.SH",
                        "time": ["2026-03-28", "2026-03-31"],
                        "table": {
                            "open": [100.0, 101.0],
                            "high": [102.0, 103.0],
                            "low": [99.0, 100.5],
                            "close": [101.0, 102.5],
                            "volume": [100000, 120000],
                            "amount": [10100000.0, 12300000.0],
                            "changeRatio": [1.0, 1.49],
                        },
                    }
                ]
            }
        )
    )

    df = fetcher.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31")

    assert isinstance(df, pd.DataFrame)
    assert list(df["close"]) == [101.0, 102.5]
    assert list(df["pct_chg"]) == [1.0, 1.49]
    assert str(df.iloc[0]["date"].date()) == "2026-03-28"


def test_ifind_fetcher_maps_official_realtime_payload_to_unified_quote():
    fetcher = IFindFetcher(
        _FakeIFindService(
            realtime_payload={
                "tables": [
                    {
                        "thscode": "600519.SH",
                        "time": ["2026-04-01 15:00:00"],
                        "table": {
                            "open": [1464.49],
                            "high": [1469.99],
                            "low": [1452.88],
                            "latest": [1459.44],
                            "changeRatio": [0.6510344827586245],
                            "change": [9.44],
                            "preClose": [1450.0],
                            "volume": [29125.0],
                            "amount": [4256185500.0],
                            "turnoverRatio": [0.23257871704630456],
                            "volumeRatio": [None],
                            "amplitude": [1.179999999999993],
                            "pb": [7.109509],
                        },
                    }
                ]
            }
        )
    )

    quote = fetcher.get_realtime_quote("600519")

    assert quote.code == "600519"
    assert quote.source == RealtimeSource.IFIND
    assert quote.price == 1459.44
    assert quote.change_pct == 0.6510344827586245
    assert quote.pre_close == 1450.0
    assert quote.volume == 2912500
    assert quote.turnover_rate == 0.23257871704630456
    assert quote.volume_ratio is None
    assert quote.pb_ratio == 7.109509


def test_ifind_fetcher_gets_stock_name_from_ifind_service():
    fetcher = IFindFetcher(
        _FakeIFindService(stock_name="贵州茅台")
    )

    name = fetcher.get_stock_name("600519")

    assert name == "贵州茅台"
