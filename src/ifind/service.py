import logging
from typing import Dict, Optional

from src.config import Config
from src.ifind.auth import IFindAuthProvider
from src.ifind.client import IFindClient
from src.ifind.mappers import map_financial_statement_pack, map_forecast_pack, map_valuation_pack
from src.ifind.schemas import (
    FinancialQualitySummary,
    IFindFinancialPack,
)


logger = logging.getLogger(__name__)


class IFindService:
    FINANCIAL_QUERY = (
        "{target} 营业总收入 归属于母公司所有者的净利润 扣除非经常性损益后的净利润 "
        "销售毛利率 销售净利率 净资产收益率roe 资产负债率 经营活动产生的现金流量净额 存货"
    )
    VALUATION_QUERY = "{target} 市盈率 市净率 总市值 流通市值"
    FORECAST_QUERY = "{target} 预测净利润平均值 预测主营业务收入平均值 2026 2027"

    def __init__(self, client: IFindClient):
        self.client = client
        self._financial_pack_cache: Dict[str, IFindFinancialPack] = {}

    @classmethod
    def from_config(cls, config: Config) -> "IFindService":
        auth_provider = IFindAuthProvider(
            refresh_token=config.ifind_refresh_token or "",
        )
        client = IFindClient(
            auth_provider=auth_provider,
        )
        return cls(client=client)

    def get_financial_pack(self, stock_code: str, stock_name: Optional[str] = None) -> IFindFinancialPack:
        if stock_code in self._financial_pack_cache:
            return self._financial_pack_cache[stock_code]

        pack = IFindFinancialPack(stock_code=stock_code, stock_name=stock_name or "")
        target = stock_name or stock_code

        for label, query, mapper in (
            ("financials", self.FINANCIAL_QUERY.format(target=target), map_financial_statement_pack),
            ("valuation", self.VALUATION_QUERY.format(target=target), map_valuation_pack),
            ("forecast", self.FORECAST_QUERY.format(target=target), map_forecast_pack),
        ):
            try:
                payload = self.client.smart_stock_picking(query)
                setattr(pack, label, mapper(stock_code, payload))
            except Exception as exc:
                pack.partial_failures.append(label)
                logger.warning("iFinD %s query failed for %s: %s", label, stock_code, exc)

        pack.stock_name = (
            pack.stock_name
            or (pack.financials.stock_name if pack.financials else "")
            or (pack.valuation.stock_name if pack.valuation else "")
            or (pack.forecast.stock_name if pack.forecast else "")
        )
        pack.quality_summary = derive_quality_summary(pack)
        self._financial_pack_cache[stock_code] = pack
        return pack


def derive_quality_summary(pack: IFindFinancialPack) -> FinancialQualitySummary:
    financials = pack.financials
    forecast = pack.forecast

    profit_quality = "unknown"
    if financials and financials.gross_margin is not None and financials.net_margin is not None and financials.roe is not None:
        if financials.gross_margin >= 40 and financials.net_margin >= 15 and financials.roe >= 15:
            profit_quality = "strong"
        elif financials.net_margin >= 8 or financials.roe >= 8:
            profit_quality = "stable"
        else:
            profit_quality = "weak"

    cashflow_health = "unknown"
    if financials and financials.operating_cashflow is not None and financials.net_profit not in (None, 0):
        if financials.operating_cashflow > 0 and financials.operating_cashflow >= 0.8 * financials.net_profit:
            cashflow_health = "healthy"
        elif financials.operating_cashflow > 0:
            cashflow_health = "moderate"
        else:
            cashflow_health = "weak"

    leverage_risk = "unknown"
    if financials and financials.asset_liability_ratio is not None:
        if financials.asset_liability_ratio <= 40:
            leverage_risk = "low"
        elif financials.asset_liability_ratio <= 60:
            leverage_risk = "medium"
        else:
            leverage_risk = "high"

    growth_visibility = "unknown"
    if forecast and forecast.expected_growth_rate is not None:
        if forecast.expected_growth_rate >= 20:
            growth_visibility = "high"
        elif forecast.expected_growth_rate >= 5:
            growth_visibility = "medium"
        else:
            growth_visibility = "low"

    notes = []
    if pack.partial_failures:
        notes.append(f"partial_failures={','.join(pack.partial_failures)}")

    return FinancialQualitySummary(
        profit_quality=profit_quality,
        cashflow_health=cashflow_health,
        leverage_risk=leverage_risk,
        growth_visibility=growth_visibility,
        notes=notes,
    )
