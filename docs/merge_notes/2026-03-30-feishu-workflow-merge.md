# 2026-03-30 Feishu Workflow Merge

## Source

- merged from: `origin/codex/feishu-webhook-gh-test`
- merge commit: `a72d608`

## What Changed

This merge brings the Feishu webhook workflow environment support into the main line.

Primary change:

- add `FEISHU_WEBHOOK_URL` passthrough into `.github/workflows/justice_plutus_analysis.yml`

## Why It Matters

This allows GitHub Actions runs to read the Feishu webhook configuration from the workflow environment, so Feishu can participate as a notification channel in automated runs.

## Scope

This merge is intentionally narrow.

- no major runtime logic changes
- no analysis-pipeline changes
- no report-schema changes

The main value is CI / workflow-side notification wiring.

## Notes

During merge, older branch documentation conflicted with newer `main` documentation.

Resolution policy:

- keep the newer `main` README and quickstart docs
- preserve the Feishu workflow environment injection
