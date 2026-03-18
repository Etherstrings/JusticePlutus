from src.analyzer import AnalysisResult
from src.formatters import (
    chunk_content_by_max_bytes,
    chunk_content_by_max_words,
    markdown_to_plain_text,
    slice_at_max_bytes,
)
from src.notification import NotificationService


def test_slice_at_max_bytes_preserves_utf8():
    first, second = slice_at_max_bytes("贵州茅台ABC", 7)
    assert first
    assert first.encode("utf-8")
    assert second
    assert first + second == "贵州茅台ABC"


def test_chunk_content_by_max_bytes_splits_large_content():
    content = "## 标题\n\n" + ("内容段落\n" * 200)
    chunks = chunk_content_by_max_bytes(content, 300, add_page_marker=True)
    assert len(chunks) > 1
    assert any("📄" in chunk for chunk in chunks)


def test_chunk_content_by_max_words_splits_large_content():
    content = "### 小节\n" + ("测试内容 " * 300)
    chunks = chunk_content_by_max_words(content, 120)
    assert len(chunks) > 1


def test_markdown_to_plain_text_removes_markup():
    text = markdown_to_plain_text("# 标题\n\n**加粗**\n\n- 项目")
    assert "标题" in text
    assert "加粗" in text
    assert "项目" in text


def test_generate_single_stock_report_is_detail_only():
    notifier = NotificationService()
    result = AnalysisResult(
        code="600519",
        name="贵州茅台",
        sentiment_score=65,
        trend_prediction="看多",
        operation_advice="观望",
        decision_type="hold",
        analysis_summary="当前处于高位震荡，等待更清晰的回踩买点。",
        dashboard={
            "core_conclusion": {
                "one_sentence": "等待回踩确认后再考虑介入。",
            },
            "intelligence": {
                "sentiment_summary": "市场情绪偏中性，等待催化。",
                "earnings_outlook": "短期业绩预期稳定，没有明显下修迹象。",
                "risk_alerts": ["短线波动较大，追高风险偏高。"],
                "positive_catalysts": ["消费白马配置需求仍在。"],
                "latest_news": "暂无重大利空，板块关注度维持稳定。",
            },
        },
    )

    content = notifier.generate_single_stock_report(result)
    assert "Jarvis Daily Investment Advice" not in content
    assert "共分析1只股票" not in content
    assert "📊 分析结果摘要" not in content
    assert "⚪ 贵州茅台 (600519)" in content
    assert "📰 重要信息速览" in content
    assert "🚨 风险警报" in content
    assert "✨ 利好催化" in content
    assert "📢 最新动态" in content
    assert "CST" in content


def test_generate_summary_overview_only_contains_batch_header():
    notifier = NotificationService()
    results = [
        AnalysisResult(
            code="600036",
            name="招商银行",
            sentiment_score=88,
            trend_prediction="强烈看多",
            operation_advice="买入",
            decision_type="buy",
        ),
        AnalysisResult(
            code="600519",
            name="贵州茅台",
            sentiment_score=45,
            trend_prediction="看空",
            operation_advice="观望",
            decision_type="hold",
        ),
    ]

    content = notifier.generate_summary_overview(results)
    assert "Jarvis Daily Investment Advice" in content
    assert "🎯" in content
    assert "📊 分析结果摘要" in content
    assert "招商银行(600036): 买入 | 评分 88 | 强烈看多" in content
    assert "贵州茅台(600519): 观望 | 评分 45 | 看空" in content


def test_generate_single_stock_report_includes_dashboard_sections():
    notifier = NotificationService()
    result = AnalysisResult(
        code="600722",
        name="金牛化工",
        sentiment_score=72,
        trend_prediction="看多",
        operation_advice="买入",
        decision_type="buy",
        analysis_summary="趋势回踩后仍保持强势，等待量能确认。",
        market_snapshot={
            "close": 10.21,
            "prev_close": 9.88,
            "open": 10.02,
            "high": 10.35,
            "low": 9.96,
            "pct_chg": "3.34%",
            "change_amount": 0.33,
            "amplitude": "3.95%",
            "volume": "1250.4 万股",
            "amount": "12.8 亿元",
            "price": 10.21,
            "volume_ratio": 1.58,
            "turnover_rate": "4.23%",
            "source": "tencent",
        },
        dashboard={
            "core_conclusion": {
                "one_sentence": "趋势未破坏，缩量回踩可分批介入。",
                "time_sensitivity": "不急",
                "position_advice": {
                    "no_position": "等待回踩后分批建仓。",
                    "has_position": "继续持有并设置跟踪止损。",
                },
            },
            "intelligence": {
                "sentiment_summary": "情绪偏乐观，但短线波动会放大。",
                "earnings_outlook": "行业景气上行，盈利预期存在上修空间。",
                "risk_alerts": ["估值偏高，若放量滞涨需防回撤。"],
                "positive_catalysts": ["产品涨价预期继续发酵。"],
                "latest_news": "公司公告经营正常，未披露重大利空。",
            },
            "data_perspective": {
                "trend_status": {
                    "ma_alignment": "MA5 > MA10 > MA20",
                    "is_bullish": True,
                    "trend_score": 78,
                },
                "price_position": {
                    "current_price": 10.21,
                    "ma5": 10.05,
                    "ma10": 9.92,
                    "ma20": 9.70,
                    "bias_ma5": 1.59,
                    "bias_status": "安全",
                    "support_level": 9.92,
                    "resistance_level": 10.35,
                },
                "volume_analysis": {
                    "volume_ratio": 1.58,
                    "volume_status": "放量",
                    "turnover_rate": 4.23,
                    "volume_meaning": "温和放量，买盘意愿增强。",
                },
                "chip_structure": {
                    "profit_ratio": "62%",
                    "avg_cost": "9.85",
                    "concentration": "18%",
                    "chip_health": "一般",
                },
            },
            "battle_plan": {
                "sniper_points": {
                    "ideal_buy": "10.00元",
                    "secondary_buy": "10.12元",
                    "stop_loss": "9.78元",
                    "take_profit": "10.60元",
                },
                "position_strategy": {
                    "suggested_position": "3成",
                    "entry_plan": "回踩分两笔建仓。",
                    "risk_control": "跌破止损位减仓。",
                },
                "action_checklist": ["✅ 均线多头排列", "✅ 量能有效放大"],
            },
        },
    )

    content = notifier.generate_single_stock_report(result)
    assert "### 📈 当日行情" in content
    assert "📰 重要信息速览" in content
    assert "📌 核心结论" in content
    assert "📊 数据透视" in content
    assert "🎯 作战计划" in content
    assert "✅ 检查清单" in content
