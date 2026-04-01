from src.ifind.service import IFindService


def _smart_table(**columns):
    return {"tables": [{"table": columns}]}


class FakeIFindClient:
    def __init__(self, responses=None, errors=None, supported_capabilities=None):
        self.responses = responses or {}
        self.errors = errors or {}
        self.supported_capabilities = supported_capabilities or {}
        self.calls = []

    def smart_stock_picking(self, searchstring, searchtype="stock"):
        self.calls.append((searchstring, searchtype))
        for keyword, error in self.errors.items():
            if keyword in searchstring:
                raise error
        for keyword, payload in self.responses.items():
            if keyword in searchstring:
                return payload
        raise AssertionError(f"unexpected query: {searchstring}")

    def get_daily_data(self, stock_code, start_date, end_date):
        if not self.supported_capabilities.get("daily_data"):
            raise NotImplementedError("daily data unavailable")
        return {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "rows": [],
        }

    def get_realtime_quote(self, stock_code):
        if not self.supported_capabilities.get("realtime_quote"):
            raise NotImplementedError("realtime quote unavailable")
        return {"stock_code": stock_code, "price": 123.45}


def test_service_returns_partial_pack_when_forecast_call_fails():
    client = FakeIFindClient(
        responses={
            "营业总收入": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                        "营业总收入[20250930]": [130903889634.88],
                        "归属于母公司所有者的净利润[20250930]": [64626746712.18],
                        "扣除非经常性损益后的净利润[20250930]": [64680616431.2],
                        "销售毛利率[20250930]": ["91.2934"],
                        "销售净利率[20250930]": ["52.0801"],
                        "净资产收益率roe(加权,公布值)[20250930]": [24.64],
                        "资产负债率[20250930]": [12.8088],
                        "经营活动产生的现金流量净额[20250930]": [38196802155.27],
                        "存货[20250930]": [55858862716.48],
                    }
                }]
            },
            "总市值": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                        "市盈率(pe)[20260330]": ["20.637"],
                        "市净率(pb)[20260330]": ["6.917"],
                        "总市值[20260330]": [1964000000000.0],
                        "流通市值[20260330]": [1964000000000.0],
                    }
                }]
            },
        },
        errors={"预测净利润平均值": RuntimeError("forecast unavailable")},
    )
    service = IFindService(client=client)

    pack = service.get_financial_pack("600519")

    assert pack.stock_code == "600519"
    assert pack.financials is not None
    assert pack.financials.stock_name == "贵州茅台"
    assert pack.financials.report_period == "2025-09-30"
    assert pack.financials.revenue == 130903889634.88
    assert pack.valuation is not None
    assert pack.valuation.pe_ttm == 20.637
    assert pack.forecast is None
    assert "forecast" in pack.partial_failures
    assert pack.quality_summary is not None
    assert pack.quality_summary.cashflow_health == "moderate"


def test_service_reuses_per_stock_cache():
    client = FakeIFindClient(
        responses={
            "营业总收入": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                        "营业总收入[20250930]": [130903889634.88],
                    }
                }]
            },
            "总市值": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                        "市盈率(pe)[20260330]": ["20.637"],
                        "市净率(pb)[20260330]": ["6.917"],
                    }
                }]
            },
            "预测净利润平均值": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                        "预测净利润平均值[20261231]": [95215849886.1111],
                        "预测净利润平均值[20271231]": [100687506345.25],
                    }
                }]
            },
        }
    )
    service = IFindService(client=client)

    first = service.get_financial_pack("600519")
    second = service.get_financial_pack("600519")

    assert first is second
    assert len(client.calls) == 3


def test_service_maps_a_share_free_float_value_as_circulating_market_value():
    client = FakeIFindClient(
        responses={
            "营业总收入": _smart_table(股票代码=["300750.SZ"], 股票简称=["宁德时代"]),
            "总市值": {
                "tables": [{
                    "table": {
                        "股票代码": ["300750.SZ"],
                        "股票简称": ["宁德时代"],
                        "市盈率(pe)[20260401]": ["25.645"],
                        "市净率(pb)[20260401]": ["5.493"],
                        "量比[20260401]": ["0.864"],
                        "换手率[20260401]": ["0.544"],
                        "总市值[20260401]": [1875197434433.5],
                        "a股市值(不含限售股)[20260401]": ["1726960900000.000"],
                    }
                }]
            },
            "预测净利润平均值": _smart_table(股票代码=["300750.SZ"], 股票简称=["宁德时代"]),
        }
    )
    service = IFindService(client=client)

    pack = service.get_financial_pack("300750")

    assert pack.valuation is not None
    assert pack.valuation.volume_ratio == 0.864
    assert pack.valuation.turnover_rate == 0.544
    assert pack.valuation.total_market_value == 1875197434433.5
    assert pack.valuation.circulating_market_value == 1726960900000.0


def test_service_gets_stock_name_via_lightweight_query_and_reuses_cache():
    client = FakeIFindClient(
        responses={
            "股票简称": {
                "tables": [{
                    "table": {
                        "股票代码": ["600519.SH"],
                        "股票简称": ["贵州茅台"],
                    }
                }]
            }
        }
    )
    service = IFindService(client=client)

    first = service.get_stock_name("600519")
    second = service.get_stock_name("600519")

    assert first == "贵州茅台"
    assert second == "贵州茅台"
    assert client.calls == [("600519 股票简称", "stock")]


def test_service_reports_daily_and_realtime_capabilities_from_client():
    client = FakeIFindClient(supported_capabilities={"daily_data": True, "realtime_quote": True})
    service = IFindService(client=client)

    assert service.supports_daily_data() is True
    assert service.supports_realtime_quote() is True
    assert service.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31") == {
        "stock_code": "600519",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "rows": [],
    }
    assert service.get_realtime_quote("600519") == {"stock_code": "600519", "price": 123.45}


def test_service_treats_not_implemented_market_methods_as_unavailable():
    client = FakeIFindClient()
    service = IFindService(client=client)

    assert service.supports_daily_data() is False
    assert service.supports_realtime_quote() is False
    assert service.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31") is None
    assert service.get_realtime_quote("600519") is None
