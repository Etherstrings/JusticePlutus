# 2026-03-30 iFinD Enhancement Merge

## Source

- merged from: `codex/ifind-analysis-enhancement`
- merge commit: current merge on `codex/merge-main-20260330`

## What Changed

This merge adds optional iFinD-based financial-data enhancement to the existing JusticePlutus analysis flow.

Main additions:

- new config flags:
  - `IFIND_REFRESH_TOKEN`
  - `ENABLE_IFIND`
  - `ENABLE_IFIND_ANALYSIS_ENHANCEMENT`
- new standalone iFinD service layer under `src/ifind/`
- optional pipeline injection of:
  - `ifind_financials`
  - `ifind_valuation`
  - `ifind_forecast`
  - `ifind_quality_summary`
- prompt enhancement section:
  - `基本面与估值增强`
- documentation for current enhancement behavior and future standalone report-product direction

## Why It Matters

The current project now has a cleaner way to consume structured financial-report, valuation, and earnings-expectation data without making iFinD a hard dependency.

This is useful for:

- improving report grounding
- improving financial-quality reasoning
- improving valuation commentary
- preserving a path to a future standalone financial-report product

## Non-Intrusive Behavior

This merge was designed to stay optional.

- if iFinD is disabled, the main flow behaves as before
- if the refresh token is missing, the enhancement is skipped
- if iFinD fails, the main analysis flow still completes

## Related Docs

- [iFinD 增强接入说明](../IFIND_ENHANCEMENT_GUIDE.md)
- [iFinD 财报项目记录](../IFIND_FINANCIAL_REPORT_PROJECT_RECORD.md)
