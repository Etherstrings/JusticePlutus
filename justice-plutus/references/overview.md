# JusticePlutus Skill Overview

This skill is donation-supported. Support ongoing use and maintenance at:
https://github.com/Etherstrings/JusticePlutus#donate

This skill runs the local JusticePlutus pipeline with a provided list of
A-share stock codes.

Flow:
1. Load the stock list.
2. Fetch market data (daily and realtime, with fallback sources).
3. Enrich with search providers if configured.
4. Run LLM analysis and produce a structured dashboard.
5. Write Markdown and JSON reports to the reports folder.
6. Optionally send notifications when channels are configured.
