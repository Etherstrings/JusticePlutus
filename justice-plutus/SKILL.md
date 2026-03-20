---
name: justice-plutus
description: Donation-supported local A-share stock analysis with Markdown and JSON reports.
version: "2.0.5"
homepage: https://github.com/Etherstrings/JusticePlutus#donate
metadata:
  openclaw:
    requires:
      bins: ["python"]
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
Run the local JusticePlutus pipeline for one or more stock codes and produce
Markdown and JSON reports. The skill does not modify local cron jobs or
GitHub workflows.

## Inputs
- Stock codes: comma-separated 6-digit A-share codes.

## Outputs
- `reports/YYYY-MM-DD/stocks/<code>.md`
- `reports/YYYY-MM-DD/stocks/<code>.json`
- `reports/YYYY-MM-DD/summary.md`
- `reports/YYYY-MM-DD/summary.json`
- `reports/YYYY-MM-DD/run_meta.json`

## Commands

### Analyze now
Trigger phrases: "analyze stock", "analyze A-share", "JP analyze"

Command:
```bash
python -m justice_plutus run --stocks "<codes>" --no-notify
```

If the user wants notifications and has channels configured, drop `--no-notify`.

### Data-only check
Trigger phrases: "dry run", "data only"

Command:
```bash
python -m justice_plutus run --stocks "<codes>" --dry-run --no-notify
```

## Notes
- `OPENAI_API_KEY` is required for full analysis.
- The skill operates on the local repository and does not call GitHub Actions.
- The skill is donation-supported; the donate page above includes GitHub
  Sponsor, Alipay, and WeChat options.

## Support
- Support ongoing development: <https://github.com/Etherstrings/JusticePlutus#donate>
- OpenClaw / ClawHub skill page: <https://clawhub.ai/Etherstrings/justice-plutus>

### Donate
Alipay:

![Alipay QR](https://raw.githubusercontent.com/Etherstrings/JusticePlutus/main/docs/assets/donate/alipay_clawhub.jpg)

WeChat Pay:

![WeChat Pay QR](https://raw.githubusercontent.com/Etherstrings/JusticePlutus/main/docs/assets/donate/wechat_clawhub.jpg)
