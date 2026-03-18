"""Lightweight runtime helpers for JusticePlutus."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from src.time_utils import cn_now


def normalize_stock_codes(raw_codes: Iterable[str]) -> list[str]:
    """Normalize, deduplicate, and preserve the original stock order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in raw_codes:
        code = (raw or "").strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        normalized.append(code)
    return normalized


def resolve_run_output_dir(project_root: Path, output_dir: str | None = None, now: datetime | None = None) -> Path:
    """Resolve the run output directory for this execution."""
    if output_dir:
        destination = Path(output_dir)
    else:
        current = now or cn_now()
        destination = project_root / "reports" / current.strftime("%Y-%m-%d")
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def write_json_file(path: Path, payload: dict) -> Path:
    """Write JSON with UTF-8 encoding and readable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def ensure_summary_markdown(path: Path, results: Sequence[dict], stock_codes: Sequence[str], dry_run: bool) -> Path:
    """Create a fallback summary markdown when the pipeline did not generate one."""
    if path.exists():
        return path

    lines = [
        "# 自选股分析摘要",
        "",
        f"- 股票数: {len(stock_codes)}",
        f"- 成功数: {len(results)}",
        f"- 模式: {'dry-run' if dry_run else 'run'}",
        "",
    ]
    if results:
        lines.append("## 完成情况")
        lines.append("")
        for item in results:
            lines.append(
                f"- {item.get('name', item.get('code', 'UNKNOWN'))}({item.get('code', 'UNKNOWN')}): "
                f"{item.get('operation_advice', 'N/A')} | 评分 {item.get('sentiment_score', 'N/A')}"
            )
    else:
        lines.extend(
            [
                "## 完成情况",
                "",
                "- 本次未生成分析结果。",
            ]
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_run_meta(
    stock_codes: Sequence[str],
    success_codes: Sequence[str],
    failed_codes: Sequence[str],
    output_dir: Path,
    dry_run: bool,
    notify_enabled: bool,
    workers: int,
    started_at: datetime,
    finished_at: datetime,
) -> dict:
    """Build a machine-readable run metadata payload."""
    return {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "stock_codes": list(stock_codes),
        "success_codes": list(success_codes),
        "failed_codes": list(failed_codes),
        "success_count": len(success_codes),
        "failure_count": len(failed_codes),
        "dry_run": dry_run,
        "notify_enabled": notify_enabled,
        "workers": workers,
        "output_dir": str(output_dir),
    }
