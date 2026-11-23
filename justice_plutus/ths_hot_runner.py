"""Temporary runner for TongHuaShun hot-stock driven analysis."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

from dotenv import dotenv_values

from .cli import run_command

DEFAULT_QUERY = "今日A股热门股票前10"
_CODE_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")
_CODE_COLUMNS = ("code", "股票代码", "证券代码", "股票code", "股票代码code")


def load_overlay_env(project_root: Path) -> None:
    """Load `.env` and `.env.local` like the local overlay helper script."""
    merged: dict[str, str] = {}
    for name in (".env", ".env.local"):
        path = project_root / name
        if not path.exists():
            continue
        for key, value in dotenv_values(path).items():
            if value is not None:
                merged[key] = value

    for key, value in merged.items():
        os.environ[key] = value


def _normalize_a_share_code(raw: Any) -> str | None:
    text = str(raw or "").strip().upper()
    if not text:
        return None
    match = _CODE_PATTERN.search(text)
    if not match:
        return None
    return match.group(1)


def extract_hot_stock_codes(payload: Any, limit: int = 10) -> list[str]:
    """Extract normalized 6-digit A-share codes from a pywencai result table."""
    if payload is None:
        raise ValueError("TongHuaShun hot stock payload is empty")

    rows = payload.to_dict(orient="records") if hasattr(payload, "to_dict") else payload
    if not rows:
        raise ValueError("TongHuaShun hot stock payload has no rows")

    codes: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_code = None
        for column in _CODE_COLUMNS:
            value = row.get(column)
            if value:
                raw_code = value
                break
        code = _normalize_a_share_code(raw_code)
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
        if len(codes) >= limit:
            return codes

    if not codes:
        raise ValueError("No valid A-share codes found in TongHuaShun hot stock payload")
    return codes


def fetch_ths_hot_stock_codes(limit: int = 10, query: str = DEFAULT_QUERY) -> list[str]:
    """Fetch TongHuaShun hot top stocks through pywencai."""
    import pywencai

    from src.config import get_config

    config = get_config()
    cookie = (config.wencai_cookie or "").strip()
    user_agent = (config.wencai_user_agent or "").strip()
    if not cookie:
        raise RuntimeError("WENCAI_COOKIE is required to fetch TongHuaShun hot stocks")

    kwargs = {
        "query": query,
        "query_type": "stock",
        "loop": False,
        "cookie": cookie,
    }
    if user_agent:
        kwargs["user_agent"] = user_agent

    payload = pywencai.get(**kwargs)
    return extract_hot_stock_codes(payload, limit=limit)


def build_run_args(
    stock_codes: Sequence[str],
    *,
    dry_run: bool,
    notify: bool,
    output_dir: str | None,
    workers: int,
):
    """Build the existing CLI argument shape for `run_command` reuse."""
    return SimpleNamespace(
        stocks=",".join(stock_codes),
        dry_run=dry_run,
        no_notify=not notify,
        output_dir=output_dir,
        workers=workers,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="临时执行同花顺今日热门A股前N分析")
    parser.add_argument("--limit", type=int, default=10, help="拉取热门股票数量，默认 10")
    parser.add_argument("--dry-run", action="store_true", help="只抓数据，不做 AI 分析")
    parser.add_argument("--notify", action="store_true", help="分析完成后发送通知")
    parser.add_argument("--ifind", action="store_true", help="本次运行启用 iFinD 财务增强")
    parser.add_argument("--output-dir", type=str, help="自定义输出目录")
    parser.add_argument("--workers", type=int, default=1, help="并发数，默认 1")
    return parser


def _enable_ifind_env() -> None:
    os.environ["ENABLE_IFIND"] = "true"
    os.environ["ENABLE_IFIND_ANALYSIS_ENHANCEMENT"] = "true"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent.parent
    load_overlay_env(project_root)
    if args.ifind:
        _enable_ifind_env()

    stock_codes = fetch_ths_hot_stock_codes(limit=args.limit)
    run_args = build_run_args(
        stock_codes,
        dry_run=args.dry_run,
        notify=args.notify,
        output_dir=args.output_dir,
        workers=args.workers,
    )
    return run_command(run_args)


if __name__ == "__main__":
    raise SystemExit(main())
