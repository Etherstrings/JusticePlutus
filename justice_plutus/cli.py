"""CLI entrypoint for JusticePlutus instant stock analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .runtime import (
    build_run_meta,
    ensure_summary_markdown,
    normalize_stock_codes,
    resolve_run_output_dir,
    write_json_file,
)
from src.time_utils import cn_now


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(description="自选股即时推送流水线")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="执行自选股分析流水线")
    run_parser.add_argument("--stocks", type=str, help="临时覆盖股票列表，逗号分隔")
    run_parser.add_argument("--dry-run", action="store_true", help="只抓取数据，不做 AI 分析")
    run_parser.add_argument("--no-notify", action="store_true", help="只生成本地报告，不推送通知")
    run_parser.add_argument("--output-dir", type=str, help="自定义输出目录")
    run_parser.add_argument("--workers", type=int, default=1, help="并发数，默认 1")
    return parser


def _resolve_stock_codes(args, config) -> list[str]:
    if args.stocks:
        return normalize_stock_codes(args.stocks.split(","))
    config.refresh_stock_list()
    return normalize_stock_codes(config.stock_list)


def run_command(args) -> int:
    """Execute the stock pipeline once."""
    from src.config import get_config
    from src.core.pipeline import StockAnalysisPipeline
    from src.logging_config import setup_logging

    project_root = Path(__file__).resolve().parent.parent
    config = get_config()
    stock_codes = _resolve_stock_codes(args, config)
    if not stock_codes:
        raise SystemExit("未提供股票列表，请设置 STOCK_LIST 或通过 --stocks 传入。")

    output_dir = resolve_run_output_dir(project_root, args.output_dir)
    started_at = cn_now()

    config.max_workers = args.workers or 1
    config.single_stock_notify = True
    config.market_review_enabled = False
    config.trading_day_check_enabled = False
    config.backtest_enabled = False
    config.report_output_dir = str(output_dir)

    setup_logging(log_prefix="justice_plutus", debug=False, log_dir=config.log_dir)

    pipeline = StockAnalysisPipeline(
        config=config,
        max_workers=config.max_workers,
        query_source="cli",
    )
    results = pipeline.run(
        stock_codes=stock_codes,
        dry_run=args.dry_run,
        send_notification=not args.no_notify,
    )

    result_payloads = [result.to_dict() for result in results]
    summary_json = {
        "generated_at": cn_now().isoformat(),
        "stocks": result_payloads,
    }
    write_json_file(output_dir / "summary.json", summary_json)
    ensure_summary_markdown(output_dir / "summary.md", result_payloads, stock_codes, args.dry_run)

    success_codes = [item["code"] for item in result_payloads]
    success_lookup = set(success_codes)
    failed_codes = [code for code in stock_codes if code not in success_lookup]
    run_meta = build_run_meta(
        stock_codes=stock_codes,
        success_codes=success_codes,
        failed_codes=failed_codes,
        output_dir=output_dir,
        dry_run=args.dry_run,
        notify_enabled=not args.no_notify,
        workers=config.max_workers,
        started_at=started_at,
        finished_at=cn_now(),
    )
    write_json_file(output_dir / "run_meta.json", run_meta)
    return 0 if (args.dry_run or len(success_codes) > 0) else 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI main entry."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_command(args)
    parser.error(f"未知命令: {args.command}")
    return 2
