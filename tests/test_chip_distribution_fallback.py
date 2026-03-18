from types import SimpleNamespace

import pandas as pd

from data_provider.base import BaseFetcher, DataFetcherManager
from data_provider.hscloud_fetcher import HSCloudFetcher
from data_provider.realtime_types import ChipDistribution, get_chip_circuit_breaker
from data_provider.wencai_fetcher import WencaiFetcher


class _DummyChipFetcher(BaseFetcher):
    def __init__(self, name: str, calls: list[str], chip: ChipDistribution | None = None, err: Exception | None = None):
        self.name = name
        self.priority = 1
        self._calls = calls
        self._chip = chip
        self._err = err

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame()

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        return df

    def get_chip_distribution(self, stock_code: str):
        self._calls.append(self.name)
        if self._err is not None:
            raise self._err
        return self._chip


def test_chip_distribution_fallback_order(monkeypatch):
    calls: list[str] = []
    hs = _DummyChipFetcher("HSCloudFetcher", calls, chip=None)
    wc_chip = ChipDistribution(code="000001", source="wencai", profit_ratio=0.56)
    wc = _DummyChipFetcher("WencaiFetcher", calls, chip=wc_chip)
    ak = _DummyChipFetcher(
        "AkshareFetcher",
        calls,
        chip=ChipDistribution(code="000001", source="akshare", profit_ratio=0.42),
    )

    manager = DataFetcherManager(fetchers=[hs, wc, ak])
    monkeypatch.setattr("src.config.get_config", lambda: SimpleNamespace(enable_chip_distribution=True))
    get_chip_circuit_breaker().reset()

    chip = manager.get_chip_distribution("000001")
    assert chip is wc_chip
    assert calls == ["HSCloudFetcher", "WencaiFetcher"]


def test_chip_distribution_respects_disable_switch(monkeypatch):
    calls: list[str] = []
    hs = _DummyChipFetcher("HSCloudFetcher", calls, chip=None)
    wc = _DummyChipFetcher("WencaiFetcher", calls, chip=None)
    ak = _DummyChipFetcher("AkshareFetcher", calls, chip=None)

    manager = DataFetcherManager(fetchers=[hs, wc, ak])
    monkeypatch.setattr("src.config.get_config", lambda: SimpleNamespace(enable_chip_distribution=False))
    get_chip_circuit_breaker().reset()

    chip = manager.get_chip_distribution("000001")
    assert chip is None
    assert calls == []


def test_hscloud_mapping_uses_ratio_normalization(monkeypatch):
    cfg = SimpleNamespace(
        hscloud_base_url="https://sandbox.hscloud.cn",
        hscloud_auth_token="token-123",
        hscloud_cookie="",
        hscloud_timeout_seconds=8,
    )
    monkeypatch.setattr("data_provider.hscloud_fetcher.get_config", lambda: cfg)
    fetcher = HSCloudFetcher()

    sample_response = {
        "error_no": "OK",
        "chip_grp": [
            {
                "prod_code": "000001",
                "hq_type_code": "XSHE",
                "profit_ratio": 900,  # 万分比 9%
                "average_cost": 23.75,
                "chip_ratio_grp": [
                    {"chip_ratio": 70, "chip_concentration": 1065},
                    {"chip_ratio": 90, "chip_concentration": 2080},
                ],
            }
        ],
    }
    monkeypatch.setattr(fetcher, "_post_json", lambda url, payload, headers: sample_response)

    chip = fetcher.get_chip_distribution("000001")

    assert chip is not None
    assert chip.source == "hscloud"
    assert round(chip.profit_ratio, 4) == 0.09
    assert round(chip.concentration_70, 4) == 0.1065
    assert round(chip.concentration_90, 4) == 0.208


def test_wencai_dict_payload_parsing(monkeypatch):
    cfg = SimpleNamespace(
        wencai_cookie="cookie-123",
        wencai_user_agent="Mozilla/5.0",
    )
    monkeypatch.setattr("data_provider.wencai_fetcher.get_config", lambda: cfg)
    fetcher = WencaiFetcher()

    barline_df = pd.DataFrame(
        [
            {"平均成本": 11.38, "收盘获利": 17.535, "股票代码": "000001.SZ", "时间区间": "20260316"},
            {"平均成本": 11.37, "收盘获利": 26.629, "股票代码": "000001.SZ", "时间区间": "20260317"},
        ]
    )
    payload = {
        "barline3": barline_df,
        "txt1": "<p>平安银行最新股价为10.96元，平均成本为11.37，90%股民成本价在10.80-11.73，有21.86%的人收盘是盈利的。</p>",
    }

    chip = fetcher._build_chip_from_result("000001", payload)
    assert chip is not None
    assert chip.source == "wencai"
    assert round(chip.avg_cost, 2) == 11.37
    assert round(chip.profit_ratio, 4) == 0.2186
    assert round(chip.cost_90_low, 2) == 10.80
    assert round(chip.cost_90_high, 2) == 11.73
    assert chip.concentration_90 > 0
