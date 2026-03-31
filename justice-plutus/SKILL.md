---
name: justice-plutus
description: Local A-share analysis with Markdown/JSON reports, optional Feishu notifications, and optional iFinD enhancement.
version: "2.1.0"
homepage: https://github.com/Etherstrings/JusticePlutus#donate
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      env: ["OPENAI_API_KEY"]
    primaryEnv: OPENAI_API_KEY
---

# JusticePlutus Local A-share Analysis

## Payment / Donation Notice
This skill is free to install on ClawHub, but it is donation-supported.

If JusticePlutus helps you save time, please support ongoing use and
maintenance here:

- Donate / Sponsor: <https://github.com/Etherstrings/JusticePlutus#donate>
- ClawHub page: <https://clawhub.ai/Etherstrings/justice-plutus>

## Purpose
Run the local JusticePlutus pipeline for one or more A-share stock codes and
produce structured Markdown and JSON reports.

This skill stays local-first:

- it runs the local repository on the current machine
- it does not convert the workflow into a hosted service
- it does not replace your existing cron or GitHub Actions setup

## Inputs
- Stock codes: comma-separated 6-digit A-share codes
- Optional runtime mode:
  - local report only
  - local report + notifications
  - dry-run data fetch
  - local report + iFinD enhancement

## Outputs
- `reports/YYYY-MM-DD/stocks/<code>.md`
- `reports/YYYY-MM-DD/stocks/<code>.json`
- `reports/YYYY-MM-DD/summary.md`
- `reports/YYYY-MM-DD/summary.json`
- `reports/YYYY-MM-DD/run_meta.json`

## Current Capabilities

Base capabilities:

- daily + realtime market data analysis
- chip-distribution aware decision dashboard
- structured Markdown / JSON report generation
- local single-run execution for one or more stock codes

Optional enhancements when configured:

- search enhancement through Bocha / Tavily / SerpAPI
- chip enhancement through Wencai / HSCloud and fallback sources
- iFinD financial enhancement for fundamentals, valuation, and consensus forecast
- notifications to configured channels, including Feishu and Telegram

## Commands

### Analyze now
Trigger phrases: "analyze stock", "analyze A-share", "JP analyze"

Command:
```bash
sh justice-plutus/scripts/run_analysis.sh "<codes>"
```

This keeps the run local and writes reports without sending notifications.

### Analyze and notify
Trigger phrases: "analyze and notify", "run with notifications"

Command:
```bash
sh justice-plutus/scripts/run_analysis.sh "<codes>" --notify
```

If Feishu, Telegram, or other supported channels are configured in the local
environment, notifications will be sent.

### Data-only check
Trigger phrases: "dry run", "data only"

Command:
```bash
sh justice-plutus/scripts/run_analysis.sh "<codes>" --dry-run
```

### Analyze with iFinD enhancement
Trigger phrases: "run with ifind", "fundamental enhancement", "financial enhancement"

Command:
```bash
sh justice-plutus/scripts/run_analysis.sh "<codes>" --ifind
```

This enables:

- `ENABLE_IFIND=true`
- `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`

for the current run only.

### Analyze with notifications and iFinD

Command:
```bash
sh justice-plutus/scripts/run_analysis.sh "<codes>" --ifind --notify
```

## Notes

Core runtime requirement:

- a working local JusticePlutus repository
- Python runtime
- at least one usable LLM key path such as:
  - `OPENAI_API_KEY`
  - `AIHUBMIX_KEY`
  - `GEMINI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DEEPSEEK_API_KEY`

Optional enhancement configuration:

- search enhancement:
  - `BOCHA_API_KEYS`
  - `TAVILY_API_KEYS`
  - `SERPAPI_API_KEYS`
- chip enhancement:
  - `WENCAI_COOKIE`
  - `HSCLOUD_AUTH_TOKEN` or `HSCLOUD_APP_KEY` + `HSCLOUD_APP_SECRET`
- iFinD enhancement:
  - `IFIND_REFRESH_TOKEN`
  - optional run flags `--ifind`
- Feishu notifications:
  - `FEISHU_WEBHOOK_URL`

Behavior guarantees:

- this skill operates on the local repository and does not call GitHub Actions
- iFinD is enhancement-only and does not replace the main analysis chain
- missing optional enhancement keys should not block the core local run
- notifications are optional and only fire when channels are configured and
  `--notify` is used
- the skill is donation-supported; the donate page includes GitHub Sponsor,
  Alipay, and WeChat options

## Support
- Support ongoing development: <https://github.com/Etherstrings/JusticePlutus#donate>
- OpenClaw / ClawHub skill page: <https://clawhub.ai/Etherstrings/justice-plutus>

### Donate
Alipay:

![Alipay QR](https://raw.githubusercontent.com/Etherstrings/JusticePlutus/main/docs/assets/donate/alipay_clawhub.jpg)

WeChat Pay:

![WeChat Pay QR](https://raw.githubusercontent.com/Etherstrings/JusticePlutus/main/docs/assets/donate/wechat_clawhub.jpg)
