from datetime import datetime
from pathlib import Path

from justice_plutus.runtime import (
    build_run_meta,
    ensure_summary_markdown,
    normalize_stock_codes,
    resolve_run_output_dir,
    write_json_file,
)


def test_normalize_stock_codes_dedupes_and_preserves_order():
    codes = normalize_stock_codes(["600519", " 000001 ", "600519", "", "sz000001"])
    assert codes == ["600519", "000001", "SZ000001"]


def test_resolve_run_output_dir_uses_date_folder(tmp_path: Path):
    target = resolve_run_output_dir(tmp_path, now=datetime(2026, 3, 12, 8, 0, 0))
    assert target == tmp_path / "reports" / "2026-03-12"
    assert target.exists()


def test_write_json_and_summary_markdown(tmp_path: Path):
    summary_json = tmp_path / "summary.json"
    summary_md = tmp_path / "summary.md"
    write_json_file(summary_json, {"ok": True})
    ensure_summary_markdown(
        summary_md,
        [{"code": "600519", "name": "贵州茅台", "operation_advice": "买入", "sentiment_score": 88}],
        ["600519"],
        dry_run=False,
    )
    assert '"ok": true' in summary_json.read_text(encoding="utf-8")
    content = summary_md.read_text(encoding="utf-8")
    assert "600519" in content
    assert "买入" in content


def test_build_run_meta_counts_success_and_failures(tmp_path: Path):
    meta = build_run_meta(
        stock_codes=["600519", "000001"],
        success_codes=["600519"],
        failed_codes=["000001"],
        output_dir=tmp_path,
        dry_run=False,
        notify_enabled=True,
        workers=1,
        started_at=datetime(2026, 3, 12, 8, 0, 0),
        finished_at=datetime(2026, 3, 12, 8, 0, 5),
    )
    assert meta["success_count"] == 1
    assert meta["failure_count"] == 1
    assert meta["workers"] == 1
