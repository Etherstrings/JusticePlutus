# TongHuaShun Pro Data Routing Design

Date: 2026-04-01
Branch: `main`

## Summary

This change evolves JusticePlutus from "optional iFinD fundamentals enhancement" into a broader "TongHuaShun-first when possible" data-routing model.

The user-facing requirement is simple:

1. Keep a single master switch.
2. When that switch is on, use TongHuaShun / iFinD professional data wherever the current account and implemented interfaces allow.
3. When TongHuaShun cannot serve a capability, automatically fall back to the current public-source chain.

The design must preserve the current pipeline's stability. TongHuaShun should become the preferred professional source for structured market and fundamental data, but not a hard dependency for the full product.

## Product Goals

- Add one master switch that represents "TongHuaShun professional mode".
- Make structured data paths TongHuaShun-first when enabled.
- Preserve existing behavior when the switch is off.
- Preserve automatic degradation when TongHuaShun is unavailable, lacks entitlement, or returns partial data.
- Expand enhancement coverage beyond prompt-only fundamentals into routing-level capability selection.

## Non-Goals

- Do not force an all-or-nothing migration to TongHuaShun.
- Do not remove current public data sources.
- Do not replace open web search/news providers with TongHuaShun by default.
- Do not assume every TongHuaShun account has the same entitlements.
- Do not block the main analysis/report flow on any TongHuaShun failure path.

## Confirmed Decisions

- A single user-facing master switch is required.
- "Can switch, then switch" is the correct routing rule.
- The existing iFinD enhancement flags should remain backward compatible, but the new master switch becomes the main entry point.
- TongHuaShun is most valuable for structured professional data:
  - fundamentals
  - valuation
  - earnings forecasts
  - announcements / report events
  - standardized market data when account rights permit
- Open-web search remains a separate category and should stay mixed-source for coverage and completeness.

## Why TongHuaShun Professional Data Is Better Here

For this product, TongHuaShun is stronger than the current public-source mix in the places where the data is:

- structured rather than narrative
- entitlement-backed rather than scraped
- normalized across securities and reporting periods
- useful for financial reasoning, announcement interpretation, and professional market context

That makes TongHuaShun a better default for:

- financial statements
- valuation fields
- consensus forecasts
- report / announcement metadata
- daily and realtime quote data if dedicated interfaces are available to the account

TongHuaShun is not automatically better for:

- broad web/news discovery
- long-tail public commentary
- non-structured internet search coverage

So the product should become:

- TongHuaShun-first for professional structured data
- mixed-provider for open search/news intelligence

## User-Facing Behavior

### New Master Switch

Add a new config flag:

- `ENABLE_THS_PRO_DATA=false`
  - Master switch for TongHuaShun professional mode.

Compatibility behavior:

- `ENABLE_IFIND=true` should still work.
- Internally, the system should treat `ENABLE_THS_PRO_DATA` as the new preferred control plane.
- Existing flags such as `ENABLE_IFIND_ANALYSIS_ENHANCEMENT` remain valid for fine-grained compatibility, but the user should only need the master switch for the main experience.

### Runtime Rule

When `ENABLE_THS_PRO_DATA=false`:

- the current project behaves exactly as it does today

When `ENABLE_THS_PRO_DATA=true`:

- TongHuaShun-backed capabilities are attempted first
- unsupported or failing TongHuaShun capabilities fall back automatically
- the analysis still completes with the existing public-source pipeline when needed

### Capability Policy

When TongHuaShun professional mode is on:

- fundamentals / valuation / forecast:
  - always prefer TongHuaShun
- announcements / report events:
  - use TongHuaShun if a supported interface is implemented and available
- daily bars:
  - use TongHuaShun first only if the daily-data interface is implemented and available
- realtime quotes:
  - use TongHuaShun first only if the realtime interface is implemented and available
- chip distribution:
  - keep the current TongHuaShun-ecosystem-friendly path, with Wencai / HSCloud preserved
- search/news:
  - preserve current web-search providers as the default completeness layer

## Architecture

### 1. TongHuaShun Capability Layer

Expand the current `src/ifind/` package from a single-query financial enhancement client into a reusable TongHuaShun capability layer.

Expected responsibilities:

- auth/token management
- low-level HTTP client methods
- capability-specific request helpers
- response normalization / mappers
- entitlement or availability detection

The `ifind` package should own TongHuaShun-specific details so the rest of the app only sees normalized domain outputs.

### 2. Data Routing Layer

Introduce a TongHuaShun-aware routing policy at the data-provider level.

Recommended shape:

- add one new fetcher or adapter for TongHuaShun-backed market data
- keep it separate from the current prompt-enhancement service
- let `DataFetcherManager` decide whether TongHuaShun should be tried first for each capability

This keeps a clean separation:

- `src/ifind/`: TongHuaShun transport, auth, capability API, normalization
- `data_provider/`: market-data routing and fetcher failover
- `src/core/pipeline.py`: orchestration and context assembly
- `src/analyzer.py`: prompt/report consumption

### 3. Capability Probe Model

The master switch should not imply that every TongHuaShun path is callable.

The runtime should support a capability probe or lazy detection model:

- `supports_financial_pack`
- `supports_daily_data`
- `supports_realtime_quote`
- `supports_report_events`

These can be implemented either by:

- explicit config plus known endpoint availability
- first-call lazy detection with cached result

The important behavior is:

- if a capability is available, route to TongHuaShun first
- if not, immediately use the current fallback chain

## Routing Design

### A. Financial / Valuation / Forecast Enhancement

This is the highest-confidence TongHuaShun path and should always be enabled when:

- TongHuaShun professional mode is on
- auth is available

Current `smart_stock_picking` support already covers:

- financial statements
- valuation
- earnings forecasts
- derived financial-quality summary

This path remains the first rollout priority and should no longer be treated as an isolated side enhancement. It becomes part of the normal professional-data mode.

### B. Daily Bar Routing

Current chain:

- `Efinance -> Akshare -> Tushare -> Pytdx -> Baostock -> Yfinance`

Target behavior in TongHuaShun professional mode:

- `TongHuaShunDaily -> existing chain`

Requirements:

- normalize TongHuaShun historical quote payloads into the existing standard OHLCV schema
- preserve indicator calculation and downstream analyzer assumptions
- keep full error logging and fallback continuity

If the TongHuaShun daily interface is not implemented or not entitled, the manager should skip it without changing user-visible behavior.

### C. Realtime Quote Routing

Current chain:

- driven by `REALTIME_SOURCE_PRIORITY`

Target behavior in TongHuaShun professional mode:

- `TongHuaShunRealtime -> configured existing realtime priority`

Requirements:

- normalize into the current unified realtime quote object
- preserve field supplementation from secondary sources when TongHuaShun is missing non-critical fields
- continue respecting existing switches such as `ENABLE_REALTIME_QUOTE`

If TongHuaShun realtime is unavailable, the current realtime priority system should continue unchanged.

### D. Chip Distribution Routing

Current chain already leans into the TongHuaShun ecosystem:

- `HSCloud -> Wencai -> Akshare -> Tushare -> Efinance`

Decision:

- keep this chain
- do not destabilize it just to force a naming-level TongHuaShun rewrite
- only enhance it if a clearer TongHuaShun professional chip interface is later confirmed and implemented

### E. Announcement / Report Event Enhancement

This is a good fit for TongHuaShun professional data and should be designed as an optional enhancement path.

Intended use:

- earnings announcements
- report publication dates
- major financial-event headlines
- announcement metadata or source links

This should enhance:

- `news_summary`
- `earnings_outlook`
- `risk_warning`
- event-driven explanation quality

This path is important, but it should remain optional if the dedicated interface is not yet implemented.

### F. Search / News Intelligence

Decision:

- keep `Bocha / Tavily / SerpAPI / other web search` as the main open-search layer

Reason:

- this category is not equivalent to professional structured data
- broader coverage is more important than source uniformity
- replacing it with TongHuaShun would likely reduce completeness before it increases quality

## Configuration Model

### User-Facing Flags

Recommended flags:

- `ENABLE_THS_PRO_DATA=false`
- `IFIND_REFRESH_TOKEN=...`

Compatibility flags to keep:

- `ENABLE_IFIND`
- `ENABLE_IFIND_ANALYSIS_ENHANCEMENT`

Recommended internal resolution rules:

1. If `ENABLE_THS_PRO_DATA=true`, TongHuaShun professional mode is on.
2. Else if `ENABLE_IFIND=true`, legacy TongHuaShun enhancement mode is on.
3. `ENABLE_IFIND_ANALYSIS_ENHANCEMENT` still controls prompt-injection compatibility, but in TongHuaShun professional mode the defaults should be upgraded so financial enhancement is on unless explicitly disabled.

This gives the user one clear switch without breaking existing setups.

## Failure Handling and Degradation

TongHuaShun professional mode must never break the existing workflow.

Rules:

- auth failure:
  - log warning
  - downgrade all TongHuaShun capabilities for that run
- capability not implemented:
  - skip immediately
  - continue existing source chain
- entitlement failure:
  - treat as capability unavailable
  - continue existing source chain
- partial data:
  - keep available TongHuaShun fields
  - supplement from legacy sources where the current pipeline already supports supplementation
- repeated failures in one run:
  - cache the failure state briefly to avoid repeated expensive retries

## Logging Requirements

Minimum logs should make these states obvious:

- TongHuaShun professional mode on/off
- legacy iFinD compatibility mode on/off
- auth success/failure
- per-capability route decision
- per-capability TongHuaShun success/fallback
- entitlement or unsupported-endpoint skips
- prompt/report enhancement injection success

The logs should answer:

- Was TongHuaShun mode enabled?
- Which capabilities actually switched?
- Which capabilities fell back?
- Why did fallback happen?

## File-Level Design Direction

Expected implementation touch points:

- `src/config.py`
  - add the new master switch and compatibility resolution
- `src/ifind/client.py`
  - expand beyond `smart_stock_picking` as needed
- `src/ifind/service.py`
  - expose capability-aware business methods
- `data_provider/base.py`
  - insert TongHuaShun-aware routing rules
- `data_provider/`
  - add a TongHuaShun-backed fetcher/adapter if needed
- `src/core/pipeline.py`
  - upgrade context injection from optional side enhancement to professional-mode behavior
- `src/analyzer.py`
  - consume new announcement/report enhancement fields when available
- `.env.example` and docs
  - document the new master switch and fallback model

## Testing and Verification Direction

At minimum, implementation should verify:

1. With TongHuaShun professional mode off, current behavior is unchanged.
2. With TongHuaShun professional mode on, existing financial enhancement still injects correctly.
3. Daily routing prefers TongHuaShun when the capability is available.
4. Realtime routing prefers TongHuaShun when the capability is available.
5. Unsupported TongHuaShun capabilities fall back without aborting the run.
6. Search/news behavior remains available even when TongHuaShun is disabled or partial.
7. Existing reports still generate successfully under all fallback combinations.

## Rollout Recommendation

Implement in this order:

1. Add the master switch and compatibility resolution.
2. Promote current financial enhancement into TongHuaShun professional mode.
3. Add capability-aware daily and realtime routing hooks.
4. Add announcement/report-event enhancement if the dedicated interface is confirmed.
5. Update docs and verification coverage.

This rollout order matches the user's requirement:

- one switch
- switch on means "use TongHuaShun where possible"
- anything that cannot switch continues to work through fallback

## Review Note

This design is intentionally conservative about all-or-nothing replacement.

The chosen model is not "replace everything with TongHuaShun immediately."
It is:

- professional structured data: TongHuaShun first
- open-search intelligence: mixed providers
- every path: graceful fallback

That is the most practical way to make the system stronger without making it brittle.
