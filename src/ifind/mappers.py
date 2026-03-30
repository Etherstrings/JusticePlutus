import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.ifind.schemas import FinancialStatementPack, ForecastMetric, ForecastPack, ValuationPack


_DATE_SUFFIX_RE = re.compile(r"^(?P<label>.+?)\[(?P<date>\d{8})\]$")


def _extract_table(payload: Dict[str, Any]) -> Dict[str, Any]:
    tables = payload.get("tables") or []
    if not tables:
        return {}
    return tables[0].get("table") or {}


def _first_value(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError:
        return raw


def _parse_metric_columns(table: Dict[str, Any]) -> List[Tuple[str, Optional[str], Any]]:
    parsed: List[Tuple[str, Optional[str], Any]] = []
    for key, value in table.items():
        match = _DATE_SUFFIX_RE.match(key)
        if match:
            parsed.append((match.group("label"), _normalize_date(match.group("date")), _first_value(value)))
        else:
            parsed.append((key, None, _first_value(value)))
    return parsed


def _find_value(parsed_columns: List[Tuple[str, Optional[str], Any]], keyword: str) -> Tuple[Optional[Any], Optional[str]]:
    for label, metric_date, value in parsed_columns:
        if keyword in label:
            return value, metric_date
    return None, None


def map_financial_statement_pack(stock_code: str, payload: Dict[str, Any]) -> Optional[FinancialStatementPack]:
    table = _extract_table(payload)
    if not table:
        return None
    parsed = _parse_metric_columns(table)
    stock_name = _first_value(table.get("股票简称")) or ""

    revenue, period = _find_value(parsed, "营业总收入")
    net_profit, _ = _find_value(parsed, "归属于母公司所有者的净利润")
    deduct_non_net_profit, _ = _find_value(parsed, "扣除非经常性损益后的净利润")
    gross_margin, _ = _find_value(parsed, "销售毛利率")
    net_margin, _ = _find_value(parsed, "销售净利率")
    roe, _ = _find_value(parsed, "净资产收益率roe")
    asset_liability_ratio, _ = _find_value(parsed, "资产负债率")
    operating_cashflow, _ = _find_value(parsed, "经营活动产生的现金流量净额")
    inventory, _ = _find_value(parsed, "存货")

    return FinancialStatementPack(
        stock_code=stock_code,
        stock_name=stock_name,
        report_period=period,
        revenue=_to_float(revenue),
        net_profit=_to_float(net_profit),
        deduct_non_net_profit=_to_float(deduct_non_net_profit),
        gross_margin=_to_float(gross_margin),
        net_margin=_to_float(net_margin),
        roe=_to_float(roe),
        asset_liability_ratio=_to_float(asset_liability_ratio),
        operating_cashflow=_to_float(operating_cashflow),
        inventory=_to_float(inventory),
    )


def map_valuation_pack(stock_code: str, payload: Dict[str, Any]) -> Optional[ValuationPack]:
    table = _extract_table(payload)
    if not table:
        return None
    parsed = _parse_metric_columns(table)
    stock_name = _first_value(table.get("股票简称")) or ""

    pe_ttm, as_of_date = _find_value(parsed, "市盈率(pe)")
    pb, pb_date = _find_value(parsed, "市净率(pb)")
    total_mv, total_mv_date = _find_value(parsed, "总市值")
    circ_mv, circ_mv_date = _find_value(parsed, "流通市值")

    return ValuationPack(
        stock_code=stock_code,
        stock_name=stock_name,
        as_of_date=as_of_date or pb_date or total_mv_date or circ_mv_date,
        pe_ttm=_to_float(pe_ttm),
        pb=_to_float(pb),
        total_market_value=_to_float(total_mv),
        circulating_market_value=_to_float(circ_mv),
    )


def map_forecast_pack(stock_code: str, payload: Dict[str, Any]) -> Optional[ForecastPack]:
    table = _extract_table(payload)
    if not table:
        return None

    parsed = _parse_metric_columns(table)
    stock_name = _first_value(table.get("股票简称")) or ""
    by_period: Dict[str, ForecastMetric] = {}

    for label, metric_date, value in parsed:
        if not metric_date:
            continue
        metric = by_period.setdefault(metric_date, ForecastMetric(period_end=metric_date))
        if "预测净利润平均值" in label:
            metric.net_profit = _to_float(value)
        elif "预测主营业务收入平均值" in label or "营业收入" in label:
            metric.revenue = _to_float(value)

    periods = sorted(by_period.values(), key=lambda item: item.period_end)
    expected_growth_rate: Optional[float] = None
    net_profit_periods = [item for item in periods if item.net_profit is not None]
    if len(net_profit_periods) >= 2 and net_profit_periods[0].net_profit:
        base = net_profit_periods[0].net_profit or 0.0
        if base:
            expected_growth_rate = round(((net_profit_periods[1].net_profit or 0.0) - base) / base * 100, 2)

    return ForecastPack(
        stock_code=stock_code,
        stock_name=stock_name,
        periods=periods,
        expected_growth_rate=expected_growth_rate,
    )
