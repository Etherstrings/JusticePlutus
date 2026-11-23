# Tonghuashun iFinD Skill Routing Design

## Goal

Upgrade the installed `tonghuashun-ifind` skill so OpenClaw agents can answer common stock and index questions without manually choosing endpoints or building raw payloads.

## Problem

The current skill exposes `api-call` plus a few thin wrappers, but it has no deterministic layer that maps user intent to the right iFinD endpoint and payload. That leaves the agent to guess:

- which endpoint to use
- how to normalize stock or index codes
- how to pick indicators
- when to fall back to documentation

That is why common questions like "查一下某股票价格" or "看一下大盘" can fail even though iFinD itself supports them.

## Approved Scope

First rollout covers four high-frequency query classes:

1. Stock realtime quote
2. Stock historical quote
3. Market or index snapshot
4. Basic fundamental and valuation pack

Anything outside those classes should not guess. The skill should guide the agent to the local references and, if no suitable route exists, explicitly say the skill does not currently cover that iFinD capability.

## Architecture

Keep the existing low-level primitives:

- `auth-login`
- `auth-set-tokens`
- `api-call`

Add a deterministic routing layer on top of them:

- `smart-query`
- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`

The routing layer is responsible for:

- detecting intent from common user phrasing
- resolving stock or index entities into normalized iFinD codes
- building the correct endpoint and payload templates
- returning structured fallback guidance instead of guessing unsupported routes

## Routing Rules

### 1. Realtime quote

Use `real_time_quotation` for:

- 最新价
- 现价
- 股价
- 行情
- quote / price

Default target is one stock or one explicitly named index.

### 2. Historical quote

Use `cmd_history_quotation` for:

- 历史走势
- K线
- 近一周 / 近一个月 / 近三个月 / 近半年 / 近一年
- from/to date ranges

If the user provides no date range, default to the last 30 calendar days ending today.

### 3. Market snapshot

Use `real_time_quotation` with an index-oriented default bundle for:

- 大盘
- 指数
- 盘面
- market snapshot

Default bundle:

- 上证指数 `000001.SH`
- 深证成指 `399001.SZ`
- 创业板指 `399006.SZ`
- 沪深300 `000300.SH`

If the user names a specific supported index, query only that index.

### 4. Fundamental basic

Use `smart_stock_picking` with three fixed query templates:

- financial statement metrics
- valuation metrics
- forecast metrics

This route returns a combined result package rather than forcing the agent to assemble three separate calls manually.

## Entity Resolution

Resolution order:

1. Direct normalized code
2. Known index alias map
3. Stock name lookup through `smart_stock_picking`

Normalization must support:

- `600519`
- `600519.SH`
- `SH600519`
- `sz000001`

Known market aliases should include the common mainland broad-market indices listed above.

## Failure Behavior

When `smart-query` cannot classify or resolve a request with confidence:

1. return a structured error indicating manual API lookup is required
2. include a doc hint pointing the agent to local references
3. instruct the agent to use `api-call` only after reading those references
4. if no suitable API can be found, tell the user the current skill does not cover that iFinD capability

The key rule is no fabricated endpoint guesses.

## Files

Working copy lives in:

- `.tmp/tonghuashun-ifind-skill`

Expected changes:

- modify `SKILL.md`
- modify `agents/openai.yaml`
- modify `references/usage.md`
- add `references/routing.md`
- modify `scripts/ifind_cli.py`
- add `scripts/runtime/tonghuashun_ifind_skill/routing.py`
- add tests in this repo for the working copy

## Test Strategy

Write tests first for:

1. realtime route from a plain-language stock query
2. history route with a relative time window
3. market snapshot route for `大盘`
4. fundamental route building the fixed smart-pick templates
5. unsupported query returning doc-guided fallback

The implementation is complete when those routes are deterministic and the updated skill can be synced back into `~/.openclaw/workspace/skills/tonghuashun-ifind`.
