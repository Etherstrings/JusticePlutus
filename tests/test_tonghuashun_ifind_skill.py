from __future__ import annotations

from datetime import date
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1] / ".tmp" / "tonghuashun-ifind-skill"
RUNTIME_DIR = SKILL_ROOT / "scripts" / "runtime"

if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))


from tonghuashun_ifind_skill.routing import ResolvedEntity
from tonghuashun_ifind_skill.routing import build_route_plan


def test_realtime_route_uses_real_time_quotation_for_stock_price_query():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(raw="贵州茅台", symbol="600519.SH", name="贵州茅台", entity_type="stock")

    plan = build_route_plan(
        "看看贵州茅台现在股价",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "quote_realtime"
    assert plan.endpoint == "/real_time_quotation"
    assert plan.payload["codes"] == "600519.SH"


def test_history_route_parses_relative_one_month_window():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(raw="宁德时代", symbol="300750.SZ", name="宁德时代", entity_type="stock")

    plan = build_route_plan(
        "看下宁德时代近一个月走势",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "quote_history"
    assert plan.endpoint == "/cmd_history_quotation"
    assert plan.payload["codes"] == "300750.SZ"
    assert plan.payload["startdate"] == "2026-03-17"
    assert plan.payload["enddate"] == "2026-04-16"


def test_market_snapshot_defaults_to_major_indices_for_market_query():
    plan = build_route_plan(
        "看一下大盘",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "market_snapshot"
    assert plan.endpoint == "/real_time_quotation"
    assert plan.payload["codes"] == "000001.SH,399001.SZ,399006.SZ,000300.SH"


def test_fundamental_route_builds_three_smart_pick_queries():
    def lookup(_: str) -> ResolvedEntity:
        return ResolvedEntity(raw="宁德时代", symbol="300750.SZ", name="宁德时代", entity_type="stock")

    plan = build_route_plan(
        "看看宁德时代基本面",
        entity_lookup=lookup,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "fundamental_basic"
    assert plan.endpoint == "/smart_stock_picking"
    assert plan.payload["searchstrings"] == [
        "300750.SZ 营业总收入 归属于母公司所有者的净利润 扣除非经常性损益后的净利润 销售毛利率 销售净利率 净资产收益率roe 资产负债率 经营活动产生的现金流量净额 存货",
        "300750.SZ 量比 换手率 市盈率 市净率 总市值 流通市值",
        "300750.SZ 预测净利润平均值 预测主营业务收入平均值 2026 2027",
    ]


def test_unsupported_query_returns_manual_lookup_fallback():
    plan = build_route_plan(
        "帮我找贵州茅台公告PDF下载链接并按日期排序",
        entity_lookup=lambda _: None,
        today=date(2026, 4, 16),
    )

    assert plan.intent == "manual_lookup"
    assert plan.endpoint is None
    assert "references/routing.md" in (plan.note or "")
