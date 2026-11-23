from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from justice_plutus.ths_hot_runner import build_run_args, extract_hot_stock_codes, main


def test_extract_hot_stock_codes_normalizes_dedupes_and_limits():
    df = pd.DataFrame(
        [
            {"股票代码": "002639.SZ", "股票简称": "雪人集团"},
            {"股票代码": "600666.SH", "股票简称": "奥瑞德"},
            {"股票代码": "600666.SH", "股票简称": "奥瑞德"},
            {"股票代码": "abc", "股票简称": "bad"},
            {"股票代码": "300750", "股票简称": "宁德时代"},
        ]
    )

    assert extract_hot_stock_codes(df, limit=3) == ["002639", "600666", "300750"]


def test_build_run_args_passes_hot_codes_into_existing_run_command():
    args = build_run_args(
        ["002639", "600666"],
        dry_run=True,
        notify=True,
        output_dir="/tmp/reports-hot",
        workers=3,
    )

    assert args.stocks == "002639,600666"
    assert args.dry_run is True
    assert args.no_notify is False
    assert args.output_dir == "/tmp/reports-hot"
    assert args.workers == 3


def test_main_fetches_hot_codes_and_invokes_run_command(monkeypatch, tmp_path: Path):
    calls: dict[str, object] = {}

    monkeypatch.delenv("ENABLE_IFIND", raising=False)
    monkeypatch.delenv("ENABLE_IFIND_ANALYSIS_ENHANCEMENT", raising=False)

    def fake_load_overlay_env(project_root: Path) -> None:
        calls["project_root"] = project_root

    def fake_fetch(limit: int) -> list[str]:
        calls["limit"] = limit
        return ["002639", "600666"]

    def fake_run_command(args) -> int:
        calls["args"] = args
        return 23

    monkeypatch.setattr("justice_plutus.ths_hot_runner.load_overlay_env", fake_load_overlay_env)
    monkeypatch.setattr("justice_plutus.ths_hot_runner.fetch_ths_hot_stock_codes", fake_fetch)
    monkeypatch.setattr("justice_plutus.ths_hot_runner.run_command", fake_run_command)

    exit_code = main(
        [
            "--limit",
            "2",
            "--output-dir",
            str(tmp_path),
            "--workers",
            "2",
            "--ifind",
        ]
    )

    assert exit_code == 23
    assert calls["limit"] == 2
    assert calls["project_root"] == Path(__file__).resolve().parent.parent
    args = calls["args"]
    assert args.stocks == "002639,600666"
    assert args.output_dir == str(tmp_path)
    assert args.workers == 2
    assert os.environ["ENABLE_IFIND"] == "true"
    assert os.environ["ENABLE_IFIND_ANALYSIS_ENHANCEMENT"] == "true"
