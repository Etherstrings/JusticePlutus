# JusticePlutus Skill Overview

`justice-plutus` is the local OpenClaw / ClawHub entry point for running the
JusticePlutus A-share analysis pipeline on the current machine.

## What It Does

It runs a single local analysis job for one or more stock codes and produces:

- per-stock Markdown reports
- per-stock JSON reports
- summary Markdown
- summary JSON
- run metadata

## Inputs

Primary input:

- one or more 6-digit A-share stock codes, comma-separated

Optional runtime modes:

- report-only run
- report + notification run
- dry-run data fetch
- iFinD-enhanced run

## Runtime Flow

1. Load the requested stock list.
2. Fetch base market data, including daily and realtime fields.
3. Pull optional search enhancement when search keys are configured.
4. Pull optional chip-distribution enhancement when supported providers are configured.
5. Pull optional iFinD financial enhancement when enabled for the current run.
6. Run LLM-based structured analysis.
7. Write Markdown and JSON reports into the `reports/` folder.
8. Optionally send notifications if channels are configured and notification mode is enabled.

## Optional Enhancements

### Search enhancement

When configured, JusticePlutus can enrich analysis with news, sentiment,
industry, and earnings-related search results from providers such as:

- Bocha
- Tavily
- SerpAPI

### Chip enhancement

When configured, JusticePlutus can improve chip-distribution analysis using:

- Wencai
- HSCloud
- project fallbacks already built into the main pipeline

### iFinD enhancement

When enabled, iFinD adds structured financial context to the existing analysis,
including:

- financial statement summary
- valuation summary
- consensus forecast summary
- financial-quality cues for the LLM prompt

iFinD is enhancement-only. It does not replace the main local analysis flow.

## Notifications

When channels are configured and the run is started with notification mode, the
pipeline can send results through configured channels such as:

- Feishu webhook
- Telegram
- other supported project channels already configured locally

Feishu is especially useful when `FEISHU_WEBHOOK_URL` is set and the user wants
results pushed out directly after the local run.

## Non-Intrusive Behavior

This skill follows the same non-intrusive model as the repository:

- missing optional enhancement credentials should not block a normal run
- missing iFinD credentials should only skip iFinD enhancement
- notification channels do nothing unless configured and explicitly enabled
- the skill remains a local executor and does not change cron jobs or call GitHub Actions

## Outputs

Typical output paths:

- `reports/YYYY-MM-DD/stocks/<code>.md`
- `reports/YYYY-MM-DD/stocks/<code>.json`
- `reports/YYYY-MM-DD/summary.md`
- `reports/YYYY-MM-DD/summary.json`
- `reports/YYYY-MM-DD/run_meta.json`
