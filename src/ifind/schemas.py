from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FinancialStatementPack:
    stock_code: str
    stock_name: str = ""
    report_period: Optional[str] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    deduct_non_net_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    asset_liability_ratio: Optional[float] = None
    operating_cashflow: Optional[float] = None
    inventory: Optional[float] = None


@dataclass
class ValuationPack:
    stock_code: str
    stock_name: str = ""
    as_of_date: Optional[str] = None
    volume_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    total_market_value: Optional[float] = None
    circulating_market_value: Optional[float] = None


@dataclass
class ForecastMetric:
    period_end: str
    net_profit: Optional[float] = None
    revenue: Optional[float] = None


@dataclass
class ForecastPack:
    stock_code: str
    stock_name: str = ""
    periods: List[ForecastMetric] = field(default_factory=list)
    expected_growth_rate: Optional[float] = None


@dataclass
class FinancialQualitySummary:
    profit_quality: str = "unknown"
    cashflow_health: str = "unknown"
    leverage_risk: str = "unknown"
    growth_visibility: str = "unknown"
    notes: List[str] = field(default_factory=list)


@dataclass
class IFindFinancialPack:
    stock_code: str
    stock_name: str = ""
    financials: Optional[FinancialStatementPack] = None
    valuation: Optional[ValuationPack] = None
    forecast: Optional[ForecastPack] = None
    quality_summary: Optional[FinancialQualitySummary] = None
    partial_failures: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        if self.financials:
            context["ifind_financials"] = asdict(self.financials)
        if self.valuation:
            context["ifind_valuation"] = asdict(self.valuation)
        if self.forecast:
            context["ifind_forecast"] = asdict(self.forecast)
        if self.quality_summary:
            context["ifind_quality_summary"] = asdict(self.quality_summary)
        if self.partial_failures:
            context["ifind_partial_failures"] = list(self.partial_failures)
        return context
