from src.ifind.service import IFindService


def _smart_table(**columns):
    return {"tables": [{"table": columns}]}


class FakeIFindClient:
    def __init__(self, responses=None, errors=None):
        self.responses = responses or {}
        self.errors = errors or {}
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
