# iFinD Analysis Enhancement Design

Date: 2026-03-30
Branch: `codex/ifind-analysis-enhancement`

## Summary

This change introduces TongHuaShun iFinD as a new, optional capability in JusticePlutus through two coordinated tracks:

1. A standalone `ifind` data service layer that extracts high-value financial datasets from iFinD.
2. An analysis enhancement path that injects those structured datasets into the existing LLM-driven stock analysis flow.

The first version is intentionally narrow. It focuses on hard-to-source financial data such as financial statements, valuation, earnings forecasts, and derived financial quality summaries. It does not replace the current daily/realtime/search pipeline and must remain fully optional behind explicit feature flags.

## Product Goals

- Add a reusable iFinD integration layer without coupling transport/auth details into the analyzer.
- Improve report quality with more structured and authoritative financial inputs.
- Preserve current behavior when iFinD is disabled.
- Create a foundation for future standalone iFinD-powered product modules.

## Confirmed Decisions

- Default behavior: iFinD is disabled unless explicitly enabled.
- Independent module shape: a standalone data service layer, not a dedicated report page in V1.
- Standalone module V1 focus: financial statements, earnings forecasts, valuation, and core financial indicators.
- Existing analysis V1 focus: enhance LLM input and final report content first.
- V1 does not yet add iFinD into the daily/realtime primary fetch chain.

## User-Facing Behavior

### New Feature Flags

- `ENABLE_IFIND=false`
  - Master switch for all iFinD capability.
- `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=false`
  - Enables injection of iFinD financial data into the current analysis/report pipeline.
  - Only effective when `ENABLE_IFIND=true`.

### Runtime Behavior

- When both flags are `false`, JusticePlutus behaves exactly as it does today.
- When `ENABLE_IFIND=true` but `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=false`, iFinD can be used only as an internal service module for future consumers.
- When both are `true`, the analysis pipeline requests a structured iFinD financial package for each stock and injects it into the LLM prompt/report generation path.

## Architecture

### Track 1: Standalone iFinD Data Service Layer

Create a new package:

- `src/ifind/auth.py`
  - Exchanges `IFIND_REFRESH_TOKEN` for `access_token`
  - Tracks expiry and refresh policy
- `src/ifind/client.py`
  - Encapsulates HTTP requests, headers, retries, timeouts, and error normalization
- `src/ifind/schemas.py`
  - Defines normalized domain models
- `src/ifind/mappers.py`
  - Maps raw iFinD payloads into project-friendly structures
- `src/ifind/service.py`
  - Public high-level business API for the rest of the app

The `ifind` package must be reusable from any future product module without requiring knowledge of token exchange or raw field names.

### Track 2: Existing Analysis Enhancement

The current pipeline continues to own orchestration:

- `src/core/pipeline.py`
  - Detects whether iFinD enhancement is enabled
  - Calls `ifind.service`
  - Injects normalized results into analysis context

- `src/analyzer.py`
  - Consumes the new context
  - Adds a new prompt section for fundamentals, valuation, and forecast data
  - Improves report sections that already exist, rather than creating a separate parallel report format

This keeps responsibilities clean:

- `ifind`: data acquisition and normalization
- `pipeline`: orchestration
- `analyzer`: prompt/report consumption

## V1 Data Scope

V1 defines four structured packages.

### 1. Financial Statement Pack

Purpose: capture hard-to-source financial statement indicators.

Candidate fields:

- revenue
- net_profit
- deduct_non_net_profit
- gross_margin
- net_margin
- roe
- asset_liability_ratio
- operating_cashflow
- receivables trend
- inventory trend
- reporting period metadata

Primary use:

- support `fundamental_analysis`
- support financial quality reasoning
- replace weak “news-derived” earnings assumptions

### 2. Valuation Pack

Candidate fields:

- pe
- pb
- ps
- total_market_value
- circulating_market_value
- valuation percentile or relative range if available

Primary use:

- support valuation reasoning in prompt
- strengthen `risk_warning`
- support more consistent PE/PB judgment

### 3. Forecast Pack

Candidate fields:

- consensus revenue forecast
- consensus net profit forecast
- multi-period forecast trend
- forecast revisions if available
- expected growth rate

Primary use:

- strengthen `earnings_outlook`
- improve support for “growth vs valuation” conclusions

### 4. Financial Quality Summary Pack

Derived labels computed from the packs above:

- `profit_quality`
- `cashflow_health`
- `leverage_risk`
- `growth_visibility`

Primary use:

- make prompt consumption simpler
- provide short, legible summary data for reports and notifications

## Integration Points

### Pipeline

Current flow stays intact for:

- daily bars
- realtime quote
- chip distribution
- search intelligence

New insertion point:

1. Fetch existing market/search context as usual
2. If iFinD enhancement is enabled, call `ifind.service.get_financial_pack(stock_code)`
3. Attach results into analysis context
4. Continue into analyzer

Suggested new context keys:

- `ifind_financials`
- `ifind_valuation`
- `ifind_forecast`
- `ifind_quality_summary`

### Analyzer / Prompt

Add a new section after current market/chip sections:

- `基本面与估值增强`

Include only available fields. No fabricated defaults.

This section should directly strengthen existing output fields rather than inventing a new report schema:

- `fundamental_analysis`
- `earnings_outlook`
- `risk_warning`
- `buy_reason`

## Failure Handling and Degradation

iFinD must never block the main analysis flow in V1.

### Rules

- Token refresh failure:
  - Log warning
  - Skip iFinD enhancement for that run or stock
- Partial iFinD API failure:
  - Return partial data if possible
  - Avoid failing the whole pack if one sub-call fails
- Missing fields:
  - Omit them from prompt/report
  - Do not substitute invented business values
- Consecutive failures:
  - Add short-lived cooldown / retry control to reduce repeated failures during one run

### Cache Strategy

V1 should include:

- in-memory `access_token` cache keyed by expiry time
- per-run `financial_pack` cache by stock code

V1 should not include durable cross-run persistence.

## Logging Requirements

Minimum log checkpoints:

- iFinD enabled / disabled
- token refresh success / failure
- financial pack success / partial / failure
- which sub-packs were available
- whether analyzer context injection occurred

These logs should make it easy to distinguish:

- config disabled
- token/auth issue
- upstream API issue
- mapper/schema issue

## Configuration Requirements

Add support for:

- `IFIND_REFRESH_TOKEN`
- `ENABLE_IFIND`
- `ENABLE_IFIND_ANALYSIS_ENHANCEMENT`

The existing `.env` must not be relied upon for local-only secrets. Overlay usage through `.env.local` remains valid.

## Branching and Workspace Safety

This design is associated with branch:

- `codex/ifind-analysis-enhancement`

The repository currently has unrelated local changes. Implementation must not revert or overwrite those changes. Future work should continue with explicit care around dirty worktree state.

## Out of Scope for V1

- Integrating iFinD into the primary daily-bar fetch priority chain
- Integrating iFinD into the realtime quote primary chain
- Replacing current search providers
- Announcement/event ingestion
- Industry/theme/concept comparison
- Standalone frontend page or dashboard
- Full financial report parsing
- Large-scale scoring/factor engine

These are expected follow-up phases after the financial data path is stable.

## Acceptance Criteria

1. With `ENABLE_IFIND=false`, current behavior remains unchanged.
2. With `ENABLE_IFIND=true` and analysis enhancement enabled:
   - token exchange succeeds from `IFIND_REFRESH_TOKEN`
   - at least one normalized financial pack is fetched successfully
3. Analyzer prompt contains a visible iFinD-based fundamentals section.
4. Final report quality improves in:
   - `fundamental_analysis`
   - `earnings_outlook`
   - `risk_warning`
5. If iFinD fails, the stock analysis still completes and produces a report.

## Implementation Direction

The intended next step is to write a dedicated implementation plan that covers:

- file creation and ownership
- config updates
- request client design
- data schemas and mappers
- pipeline injection
- analyzer prompt/report updates
- test coverage and verification

## Review Note

This spec was prepared from the approved brainstorming decisions in-session. A formal subagent spec-review loop was not run here because delegated subagents were not explicitly requested in this conversation.
