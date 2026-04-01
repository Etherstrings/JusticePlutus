# TongHuaShun Pro Data Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one TongHuaShun professional-data master switch that promotes the existing iFinD fundamentals enhancement into the default THS path, adds capability-aware daily/realtime routing hooks, and preserves automatic fallback to the current public-source chain.

**Architecture:** Keep TongHuaShun-specific auth, capability detection, and normalization inside `src/ifind/`, then route through `data_provider` only when the capability is available. `src/config.py` becomes the compatibility control plane, `src/core/pipeline.py` promotes THS enhancement into normal runtime behavior, and `DataFetcherManager` prefers a new THS-backed fetcher for daily/realtime only when the service says those capabilities are usable.

**Tech Stack:** Python 3.11, requests, pandas, pytest, existing `src/ifind/` service layer, existing `data_provider` strategy/failover manager

---

### Task 1: Add the TongHuaShun master switch and compatibility helpers

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/config.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/.env.example`
- Test: `/Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py`

- [ ] **Step 1: Write the failing config tests**

```python
def test_ths_pro_data_master_switch_enables_professional_mode(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        ENABLE_THS_PRO_DATA="true",
        IFIND_REFRESH_TOKEN="refresh-token-demo",
    )

    assert cfg.enable_ths_pro_data is True
    assert cfg.is_ths_pro_data_enabled() is True
    assert cfg.is_ifind_financial_enhancement_enabled() is True


def test_legacy_ifind_flags_still_enable_legacy_mode(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        ENABLE_IFIND="true",
        ENABLE_IFIND_ANALYSIS_ENHANCEMENT="false",
    )

    assert cfg.enable_ths_pro_data is False
    assert cfg.is_ths_pro_data_enabled() is True
    assert cfg.is_ifind_financial_enhancement_enabled() is False
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py -k "ths_pro_data or ifind_flags" -v
```

Expected: FAIL with missing `enable_ths_pro_data` / missing compatibility helper methods.

- [ ] **Step 3: Implement the master switch parsing and helper methods**

```python
@dataclass
class Config:
    enable_ths_pro_data: bool = False

    def is_ths_pro_data_enabled(self) -> bool:
        return self.enable_ths_pro_data or self.enable_ifind

    def is_ifind_financial_enhancement_enabled(self) -> bool:
        if self.enable_ths_pro_data:
            return self.enable_ifind_analysis_enhancement
        return self.enable_ifind and self.enable_ifind_analysis_enhancement

    @classmethod
    def _resolve_ifind_analysis_enhancement(cls) -> bool:
        explicit = os.getenv("ENABLE_IFIND_ANALYSIS_ENHANCEMENT")
        if explicit is not None:
            return explicit.lower() == "true"
        return os.getenv("ENABLE_THS_PRO_DATA", "false").lower() == "true"
```

Implementation notes:

- Parse `ENABLE_THS_PRO_DATA` in `_load_from_env()`.
- Use `_resolve_ifind_analysis_enhancement()` instead of the current hard-coded `false` default so THS professional mode turns on financial enhancement unless explicitly disabled.
- Extend `_load_config()` in the test file so `ENABLE_THS_PRO_DATA` is cleared between tests.
- Add commented env docs to `.env.example` near the existing iFinD block.

- [ ] **Step 4: Run the config tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py -k "ths_pro_data or ifind_flags" -v
```

Expected: PASS for the new THS-mode tests and the legacy iFinD tests.

- [ ] **Step 5: Commit the config compatibility slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/config.py /Users/boyuewu/Projects/JusticePlutus/.env.example /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py
git commit -m "feat: add TongHuaShun professional mode config"
```

### Task 2: Promote iFinD financial enhancement into TongHuaShun professional mode

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py`
- Test: `/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py`

- [ ] **Step 1: Write the failing pipeline tests for THS mode**

```python
def test_pipeline_injects_ifind_context_when_ths_pro_mode_enabled():
    pipeline = StockAnalysisPipeline.__new__(StockAnalysisPipeline)
    pipeline.config = DummyConfig(
        enable_ths_pro_data=True,
        enable_ifind=False,
        enable_ifind_analysis_enhancement=True,
    )
    pipeline.ifind_service = FakeIFindService(_build_pack())

    enhanced = pipeline._attach_ifind_context(
        {"code": "600519", "stock_name": "贵州茅台"},
        code="600519",
        stock_name="贵州茅台",
    )

    assert enhanced["ifind_financials"]["report_period"] == "2025-12-31"
    assert pipeline.ifind_service.calls == [("600519", "贵州茅台")]
```

- [ ] **Step 2: Run the pipeline integration tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py -v
```

Expected: FAIL because the pipeline only checks legacy `enable_ifind` flags today.

- [ ] **Step 3: Implement THS-mode-aware service initialization and context injection**

```python
def _ths_pro_data_enabled(self) -> bool:
    helper = getattr(self.config, "is_ths_pro_data_enabled", None)
    if callable(helper):
        return helper()
    return getattr(self.config, "enable_ifind", False)


def _ifind_financial_enhancement_enabled(self) -> bool:
    helper = getattr(self.config, "is_ifind_financial_enhancement_enabled", None)
    if callable(helper):
        return helper()
    return getattr(self.config, "enable_ifind", False) and getattr(
        self.config,
        "enable_ifind_analysis_enhancement",
        False,
    )
```

Implementation notes:

- Use `_ths_pro_data_enabled()` inside `_build_ifind_service()` so THS mode can initialize the service even when `ENABLE_IFIND=false`.
- Use `_ifind_financial_enhancement_enabled()` inside `_attach_ifind_context()`.
- Update startup logs so they clearly distinguish:
  - THS professional mode enabled
  - THS professional mode disabled
  - service unavailable because refresh token is missing
- Keep the current graceful-skip behavior intact.

- [ ] **Step 4: Run the pipeline integration tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py -v
```

Expected: PASS for both the legacy flag behavior and the new THS master-switch behavior.

- [ ] **Step 5: Commit the pipeline slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py
git commit -m "feat: promote iFinD enhancement into THS mode"
```

### Task 3: Add capability-aware TongHuaShun service methods for routing decisions

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/ifind/client.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/ifind/service.py`
- Optional Modify: `/Users/boyuewu/Projects/JusticePlutus/src/ifind/schemas.py`
- Test: `/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py`

- [ ] **Step 1: Write the failing service tests for capability-aware routing**

```python
def test_service_reports_daily_and_realtime_capabilities_from_client():
    client = FakeIFindClient()
    client.supported_capabilities = {"daily_data": True, "realtime_quote": True}
    service = IFindService(client=client)

    assert service.supports_daily_data() is True
    assert service.supports_realtime_quote() is True


def test_service_treats_not_implemented_market_methods_as_unavailable():
    client = FakeIFindClient()
    service = IFindService(client=client)

    assert service.supports_daily_data() is False
    assert service.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31") is None
```

- [ ] **Step 2: Run the service tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py -v
```

Expected: FAIL because `IFindService` has no daily/realtime capability API today.

- [ ] **Step 3: Implement capability helpers and market-data service methods**

```python
class IFindClient:
    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> dict:
        raise NotImplementedError("TongHuaShun daily data endpoint not configured")

    def get_realtime_quote(self, stock_code: str) -> dict:
        raise NotImplementedError("TongHuaShun realtime endpoint not configured")


class IFindService:
    def supports_daily_data(self) -> bool:
        return self._supports("daily_data", "get_daily_data")

    def supports_realtime_quote(self) -> bool:
        return self._supports("realtime_quote", "get_realtime_quote")

    def get_daily_data(self, stock_code: str, start_date: str, end_date: str):
        if not self.supports_daily_data():
            return None
        return self.client.get_daily_data(stock_code, start_date, end_date)

    def get_realtime_quote(self, stock_code: str):
        if not self.supports_realtime_quote():
            return None
        return self.client.get_realtime_quote(stock_code)
```

Implementation notes:

- Keep the existing financial-pack logic unchanged except for using the same service object.
- `_supports()` should cache negative results per run so unsupported capabilities do not retry every stock.
- If the real TongHuaShun market-data endpoints are known during implementation, wire them here.
- If they are still unverified, leave the client methods as explicit `NotImplementedError` stubs so routing safely falls back instead of guessing an HTTP contract.

- [ ] **Step 4: Run the service tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py -v
```

Expected: PASS for partial financial-pack behavior, cache behavior, and the new capability methods.

- [ ] **Step 5: Commit the service capability slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/ifind/client.py /Users/boyuewu/Projects/JusticePlutus/src/ifind/service.py /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py
git commit -m "feat: add capability-aware TongHuaShun service methods"
```

### Task 4: Add a TongHuaShun-backed fetcher and route daily/realtime through it when available

**Files:**
- Create: `/Users/boyuewu/Projects/JusticePlutus/data_provider/ifind_fetcher.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/data_provider/base.py`
- Test: `/Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_data_provider_routing.py`

- [ ] **Step 1: Write the failing data-provider routing tests**

```python
def test_daily_data_prefers_ifind_fetcher_when_ths_mode_enabled(monkeypatch):
    ifind = DummyIFindFetcher(daily_df=_sample_daily_df())
    fallback = DummyFallbackFetcher(name="EfinanceFetcher")
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(enable_ths_pro_data=True, enable_realtime_quote=True, realtime_source_priority="tencent"),
    )

    df, source = manager.get_daily_data("600519", start_date="2026-03-01", end_date="2026-03-31")

    assert source == "IFindFetcher"
    assert not df.empty


def test_realtime_quote_falls_back_when_ifind_fetcher_unavailable(monkeypatch):
    ifind = DummyIFindFetcher(realtime_error=DataSourceUnavailableError("not entitled"))
    fallback = DummyRealtimeFetcher(name="AkshareFetcher", source="tencent")
    manager = DataFetcherManager(fetchers=[fallback], ifind_fetcher=ifind)

    monkeypatch.setattr(
        "src.config.get_config",
        lambda: SimpleNamespace(enable_ths_pro_data=True, enable_realtime_quote=True, realtime_source_priority="tencent"),
    )

    quote = manager.get_realtime_quote("600519")
    assert quote.source.value == "tencent"
```

- [ ] **Step 2: Run the routing tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_data_provider_routing.py -v
```

Expected: FAIL because there is no `IFindFetcher` and `DataFetcherManager` cannot accept or prioritize it.

- [ ] **Step 3: Implement the fetcher and manager routing hooks**

```python
class IFindFetcher(BaseFetcher):
    name = "IFindFetcher"
    priority = -1

    def __init__(self, service: IFindService):
        self.service = service

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        payload = self.service.get_daily_data(stock_code, start_date, end_date)
        if payload is None:
            raise DataSourceUnavailableError("TongHuaShun daily data unavailable")
        return payload

    def get_realtime_quote(self, stock_code: str):
        quote = self.service.get_realtime_quote(stock_code)
        if quote is None:
            raise DataSourceUnavailableError("TongHuaShun realtime quote unavailable")
        return quote
```

Implementation notes:

- Extend `DataFetcherManager.__init__()` to accept `ifind_fetcher: Optional[BaseFetcher] = None`.
- Insert the THS fetcher ahead of the existing sorted fetcher list only when it is provided.
- Add helpers in `DataFetcherManager` for:
  - `_ths_mode_enabled(config)`
  - `_get_ifind_fetcher()`
  - `_can_use_ifind_daily()`
  - `_can_use_ifind_realtime()`
- Daily path:
  - try `IFindFetcher` first only when THS mode and daily capability are both true
  - on `DataSourceUnavailableError` or empty data, continue the current daily chain unchanged
- Realtime path:
  - try `IFindFetcher` first only when THS mode and realtime capability are both true
  - if it returns a partial quote, keep the existing supplementary-field merge logic against the configured realtime providers

- [ ] **Step 4: Run the routing tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_data_provider_routing.py -v
```

Expected: PASS for:

- THS daily-first routing when capability exists
- fallback to the legacy chain when THS market data is unavailable
- THS realtime-first routing while preserving the existing supplement logic

- [ ] **Step 5: Commit the routing slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/data_provider/ifind_fetcher.py /Users/boyuewu/Projects/JusticePlutus/data_provider/base.py /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_data_provider_routing.py
git commit -m "feat: prefer TongHuaShun market data when available"
```

### Task 5: Wire the shared THS service through the pipeline and update runtime docs

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/README.md`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/docs/FUNCTION_ARCHITECTURE.md`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/docs/IFIND_ENHANCEMENT_GUIDE.md`
- Optional Modify: `/Users/boyuewu/Projects/JusticePlutus/.env.example`

- [ ] **Step 1: Write the failing integration expectation as a doc-safe smoke checklist**

```text
Expectation:
- THS mode off -> current runtime logs stay functionally unchanged.
- THS mode on with refresh token -> pipeline logs show THS professional mode enabled.
- THS mode on without daily/realtime entitlement -> runtime logs show fallback, not abort.
```

- [ ] **Step 2: Update pipeline construction to share the THS service with the fetcher manager**

```python
self.ifind_service = self._build_ifind_service()
self.fetcher_manager = DataFetcherManager(
    ifind_fetcher=IFindFetcher(self.ifind_service) if self.ifind_service else None,
)
```

Implementation notes:

- Build `self.ifind_service` before `DataFetcherManager`.
- Do not create a second independent THS auth/service instance inside `data_provider`.
- Keep manager creation resilient when THS mode is off or the service is unavailable.

- [ ] **Step 3: Update the docs to describe the new control model**

Doc changes to make:

- `README.md`
  - document `ENABLE_THS_PRO_DATA`
  - explain "TongHuaShun-first for professional structured data, fallback to current chain"
- `docs/FUNCTION_ARCHITECTURE.md`
  - update daily/realtime routing tables to mention the conditional THS-first branch
- `docs/IFIND_ENHANCEMENT_GUIDE.md`
  - reframe iFinD from enhancement-only into the financial core of THS professional mode
  - explicitly state that open search/news remains mixed-source

- [ ] **Step 4: Run targeted regression tests and a no-notify smoke command**

Run:

```bash
python3 -m pytest \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_pipeline_integration.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_service.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_analyzer_prompt.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_ifind_data_provider_routing.py -v
```

Then run:

```bash
./scripts/run_with_overlay_env.sh --stocks 600519 --no-notify
```

Expected:

- pytest: PASS
- smoke run: completes without aborting
- if THS market-data capability is absent, logs show graceful fallback
- if THS market-data capability is present, logs show THS-first routing

- [ ] **Step 5: Commit the shared-runtime and docs slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py /Users/boyuewu/Projects/JusticePlutus/README.md /Users/boyuewu/Projects/JusticePlutus/docs/FUNCTION_ARCHITECTURE.md /Users/boyuewu/Projects/JusticePlutus/docs/IFIND_ENHANCEMENT_GUIDE.md
git commit -m "docs: describe TongHuaShun professional data mode"
```

## Notes for the Implementer

- Do not remove the existing public data source chain. Every new THS route must degrade cleanly.
- Do not guess the exact TongHuaShun HTTP contract for daily/realtime endpoints in `data_provider`. Keep that uncertainty isolated inside `src/ifind/client.py`.
- If the real THS daily/realtime endpoint contract is unavailable during implementation, ship the routing skeleton with explicit `NotImplementedError` capability stubs and keep fallback behavior green.
- Announcement/report-event enhancement is intentionally deferred from this plan unless the dedicated endpoint contract is verified during implementation. Do not wedge speculative HTTP calls into the analyzer path.
- The untracked `/Users/boyuewu/Projects/JusticePlutus/scripts/` workspace content is unrelated; do not revert or overwrite it.
