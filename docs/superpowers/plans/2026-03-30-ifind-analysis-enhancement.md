# iFinD Analysis Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional iFinD data service and wire its normalized financial datasets into the existing JusticePlutus analysis pipeline without changing default behavior when the feature flags are off.

**Architecture:** Build a new `src/ifind/` package that owns token exchange, HTTP access, schema normalization, and a high-level financial-pack API. Keep the current orchestration in `src/core/pipeline.py`, where iFinD data is fetched only when `ENABLE_IFIND=true` and `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`, then injected into analyzer context for prompt/report enhancement. Degrade gracefully on auth or upstream failures so the main stock analysis still completes.

**Tech Stack:** Python 3, `requests`, `pytest`, existing `Config` singleton, existing pipeline/analyzer flow, local `.env.local` overlay via `scripts/run_with_overlay_env.sh`

---

## File Structure

### New Files

- `src/ifind/__init__.py`
  - Package exports for the iFinD service layer.
- `src/ifind/auth.py`
  - Refresh-token to access-token exchange, in-memory token cache, expiry handling.
- `src/ifind/client.py`
  - Thin HTTP client for iFinD API requests, retries, timeout, error normalization.
- `src/ifind/schemas.py`
  - Dataclasses / typed containers for financial, valuation, forecast, and quality summary packs.
- `src/ifind/mappers.py`
  - Raw payload to normalized schema mapping helpers.
- `src/ifind/service.py`
  - Public orchestration API: `get_financial_pack(stock_code)` with per-run cache and partial-failure handling.
- `tests/test_ifind_auth.py`
  - Unit tests for token refresh, cache reuse, and auth failure behavior.
- `tests/test_ifind_service.py`
  - Unit tests for pack assembly, mapper behavior, partial failures, and feature-facing outputs.
- `tests/test_ifind_pipeline_integration.py`
  - Integration-style tests for pipeline context injection and analyzer invocation.
- `tests/test_ifind_analyzer_prompt.py`
  - Prompt formatting / parser tests for the new `基本面与估值增强` section.

### Modified Files

- `src/config.py`
  - Add `IFIND_REFRESH_TOKEN`, `ENABLE_IFIND`, `ENABLE_IFIND_ANALYSIS_ENHANCEMENT` parsing and fields.
- `src/core/pipeline.py`
  - Lazily initialize iFinD service, fetch pack when flags are enabled, inject normalized data into context, add logging.
- `src/analyzer.py`
  - Add prompt section for iFinD-enhanced fundamentals, valuation, and forecasts; reflect iFinD as a data source when present.
- `tests/test_config_llm_and_stock_overrides.py`
  - Add config parsing tests for the new flags and refresh token.
- `README.md`
  - Document optional iFinD integration and env flags if there is already a configuration section for optional data sources.
- `.env.example`
  - Add commented example placeholders for the new iFinD variables without touching user-local secrets.

## Task 1: Add iFinD config flags and env parsing

**Files:**
- Modify: `src/config.py`
- Modify: `tests/test_config_llm_and_stock_overrides.py`
- Modify: `.env.example`

- [ ] **Step 1: Write the failing config tests**

```python
def test_ifind_flags_default_to_disabled(monkeypatch):
    cfg = _load_config(monkeypatch)
    assert cfg.enable_ifind is False
    assert cfg.enable_ifind_analysis_enhancement is False
    assert cfg.ifind_refresh_token is None


def test_ifind_flags_and_refresh_token_are_loaded(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        IFIND_REFRESH_TOKEN="refresh-token-demo",
        ENABLE_IFIND="true",
        ENABLE_IFIND_ANALYSIS_ENHANCEMENT="true",
    )
    assert cfg.ifind_refresh_token == "refresh-token-demo"
    assert cfg.enable_ifind is True
    assert cfg.enable_ifind_analysis_enhancement is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_llm_and_stock_overrides.py -k ifind -v`
Expected: FAIL because `Config` does not expose `ifind_refresh_token` or the new flags yet.

- [ ] **Step 3: Write the minimal implementation**

```python
@dataclass
class Config:
    ifind_refresh_token: Optional[str] = None
    enable_ifind: bool = False
    enable_ifind_analysis_enhancement: bool = False
```

```python
return cls(
    # ...
    ifind_refresh_token=os.getenv("IFIND_REFRESH_TOKEN"),
    enable_ifind=os.getenv("ENABLE_IFIND", "false").lower() == "true",
    enable_ifind_analysis_enhancement=(
        os.getenv("ENABLE_IFIND_ANALYSIS_ENHANCEMENT", "false").lower() == "true"
    ),
)
```

```dotenv
# Optional iFinD enhancement
IFIND_REFRESH_TOKEN=
ENABLE_IFIND=false
ENABLE_IFIND_ANALYSIS_ENHANCEMENT=false
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_llm_and_stock_overrides.py -k ifind -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config_llm_and_stock_overrides.py .env.example
git commit -m "feat: add ifind config flags"
```

## Task 2: Build the standalone iFinD auth and service layer

**Files:**
- Create: `src/ifind/__init__.py`
- Create: `src/ifind/auth.py`
- Create: `src/ifind/client.py`
- Create: `src/ifind/schemas.py`
- Create: `src/ifind/mappers.py`
- Create: `src/ifind/service.py`
- Test: `tests/test_ifind_auth.py`
- Test: `tests/test_ifind_service.py`

- [ ] **Step 1: Write the failing auth and service tests**

```python
def test_auth_provider_reuses_cached_access_token(monkeypatch):
    provider = IFindAuthProvider(refresh_token="rt-demo")
    monkeypatch.setattr(provider, "_exchange_token", lambda: ("access-1", 3600))
    assert provider.get_access_token() == "access-1"
    assert provider.get_access_token() == "access-1"


def test_service_returns_partial_pack_when_forecast_call_fails():
    client = FakeIFindClient(
        financials={"tables": [{"report_date": "2025-12-31", "revenue": 100}]},
        valuation={"tables": [{"pe_ttm": 18.5, "pb": 3.2}]},
        forecast_error=RuntimeError("forecast unavailable"),
    )
    service = IFindService(client=client)

    pack = service.get_financial_pack("600519")

    assert pack.financials is not None
    assert pack.valuation is not None
    assert pack.forecast is None
    assert "forecast" in pack.partial_failures
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ifind_auth.py tests/test_ifind_service.py -v`
Expected: FAIL because the `src/ifind/` package does not exist.

- [ ] **Step 3: Write the minimal implementation**

```python
@dataclass
class IFindFinancialPack:
    stock_code: str
    financials: Optional[FinancialStatementPack] = None
    valuation: Optional[ValuationPack] = None
    forecast: Optional[ForecastPack] = None
    quality_summary: Optional[FinancialQualitySummary] = None
    partial_failures: List[str] = field(default_factory=list)
```

```python
class IFindAuthProvider:
    TOKEN_URL = "https://quantapi.51ifind.com/api/v1/get_access_token"

    def get_access_token(self) -> str:
        if self._cached_token and time.time() < self._expires_at:
            return self._cached_token
        token, expires_in = self._exchange_token()
        self._cached_token = token
        self._expires_at = time.time() + max(expires_in - 60, 60)
        return token
```

```python
class IFindService:
    def get_financial_pack(self, stock_code: str) -> IFindFinancialPack:
        pack = IFindFinancialPack(stock_code=stock_code)
        for label, loader in (
            ("financials", self._load_financials),
            ("valuation", self._load_valuation),
            ("forecast", self._load_forecast),
        ):
            try:
                setattr(pack, label, loader(stock_code))
            except Exception:
                pack.partial_failures.append(label)
        pack.quality_summary = derive_quality_summary(pack)
        return pack
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ifind_auth.py tests/test_ifind_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ifind tests/test_ifind_auth.py tests/test_ifind_service.py
git commit -m "feat: add ifind service layer"
```

## Task 3: Integrate iFinD into pipeline orchestration with safe degradation

**Files:**
- Modify: `src/core/pipeline.py`
- Test: `tests/test_ifind_pipeline_integration.py`

- [ ] **Step 1: Write the failing pipeline tests**

```python
def test_pipeline_injects_ifind_context_when_flags_enabled(monkeypatch):
    cfg = make_config(enable_ifind=True, enable_ifind_analysis_enhancement=True)
    service = FakeIFindService.with_full_pack("600519")
    pipeline = build_pipeline(cfg, ifind_service=service)

    result = pipeline.analyze_stock("600519", ReportType.SIMPLE, query_id="q1")

    assert result is not None
    assert pipeline.analyzer.last_context["ifind_financials"]["report_period"] == "2025-12-31"
    assert pipeline.analyzer.last_context["ifind_quality_summary"]["profit_quality"] == "strong"


def test_pipeline_skips_ifind_when_feature_disabled(monkeypatch):
    cfg = make_config(enable_ifind=False, enable_ifind_analysis_enhancement=False)
    service = FakeIFindService.with_full_pack("600519")
    pipeline = build_pipeline(cfg, ifind_service=service)

    pipeline.analyze_stock("600519", ReportType.SIMPLE, query_id="q2")

    assert service.calls == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ifind_pipeline_integration.py -v`
Expected: FAIL because pipeline does not yet initialize or inject iFinD data.

- [ ] **Step 3: Write the minimal implementation**

```python
class StockAnalysisPipeline:
    def __init__(self, ...):
        # ...
        self.ifind_service = self._build_ifind_service()
```

```python
def _build_ifind_service(self):
    if not (self.config.enable_ifind and self.config.ifind_refresh_token):
        logger.info("iFinD disabled or refresh token missing")
        return None
    return IFindService.from_config(self.config)
```

```python
if self.config.enable_ifind and self.config.enable_ifind_analysis_enhancement and self.ifind_service:
    try:
        ifind_pack = self.ifind_service.get_financial_pack(code)
        enhanced_context.update(ifind_pack.to_prompt_context())
        logger.info("%s(%s) iFinD financial pack injected", stock_name, code)
    except Exception as exc:
        logger.warning("%s(%s) iFinD enhancement skipped: %s", stock_name, code, exc)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ifind_pipeline_integration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/pipeline.py tests/test_ifind_pipeline_integration.py
git commit -m "feat: wire ifind into analysis pipeline"
```

## Task 4: Add analyzer prompt/report enhancement for fundamentals and valuation

**Files:**
- Modify: `src/analyzer.py`
- Test: `tests/test_ifind_analyzer_prompt.py`

- [ ] **Step 1: Write the failing analyzer tests**

```python
def test_prompt_includes_ifind_section_when_pack_available():
    analyzer = GeminiAnalyzer()
    prompt = analyzer._format_prompt(
        {
            "code": "600519",
            "stock_name": "贵州茅台",
            "date": "2026-03-30",
            "today": {},
            "ifind_financials": {"report_period": "2025-12-31", "revenue": 1871.9, "roe": 34.1},
            "ifind_valuation": {"pe_ttm": 23.6, "pb": 8.1},
            "ifind_forecast": {"consensus_net_profit_growth": 14.2},
            "ifind_quality_summary": {"profit_quality": "strong", "cashflow_health": "healthy"},
        },
        "贵州茅台",
        news_context=None,
    )
    assert "## 基本面与估值增强" in prompt
    assert "ROE" in prompt
    assert "一致预期净利润增速" in prompt


def test_prompt_omits_ifind_section_when_no_ifind_data():
    analyzer = GeminiAnalyzer()
    prompt = analyzer._format_prompt({"code": "600519", "stock_name": "贵州茅台", "today": {}}, "贵州茅台")
    assert "## 基本面与估值增强" not in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ifind_analyzer_prompt.py -v`
Expected: FAIL because analyzer does not render any iFinD prompt block.

- [ ] **Step 3: Write the minimal implementation**

```python
if any(context.get(key) for key in (
    "ifind_financials",
    "ifind_valuation",
    "ifind_forecast",
    "ifind_quality_summary",
)):
    prompt += """
---

## 基本面与估值增强
"""
```

```python
financials = context.get("ifind_financials") or {}
valuation = context.get("ifind_valuation") or {}
forecast = context.get("ifind_forecast") or {}
quality = context.get("ifind_quality_summary") or {}
```

```python
if context.get("ifind_quality_summary"):
    prompt += f"- 盈利质量：{quality.get('profit_quality', 'N/A')}\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ifind_analyzer_prompt.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/analyzer.py tests/test_ifind_analyzer_prompt.py
git commit -m "feat: add ifind prompt enhancement"
```

## Task 5: Document usage and run focused verification

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-03-30-ifind-analysis-enhancement.md`

- [ ] **Step 1: Update docs with the new feature flags and local overlay usage**

```md
### Optional iFinD Enhancement

- Put `IFIND_REFRESH_TOKEN` in `.env.local`
- Enable `ENABLE_IFIND=true`
- Enable `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true` only when you want the current LLM analysis flow to consume iFinD data
- Recommended local runner: `scripts/run_with_overlay_env.sh`
```

- [ ] **Step 2: Run focused tests**

Run: `pytest tests/test_config_llm_and_stock_overrides.py -k ifind -v`
Expected: PASS

Run: `pytest tests/test_ifind_auth.py tests/test_ifind_service.py tests/test_ifind_pipeline_integration.py tests/test_ifind_analyzer_prompt.py -v`
Expected: PASS

- [ ] **Step 3: Run a lightweight end-to-end smoke command**

Run: `./scripts/run_with_overlay_env.sh --stocks 600519`
Expected: analysis completes; logs show either `iFinD financial pack injected` or a warning-level graceful skip without aborting the run

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/plans/2026-03-30-ifind-analysis-enhancement.md
git commit -m "docs: document ifind enhancement usage"
```

## Notes For Execution

- Keep iFinD fully optional. When flags are off, there should be no new network requests and no prompt changes.
- Do not edit user-local secret files beyond `.env.local`; the implementation should rely on the existing overlay launcher when local secrets are needed.
- Do not block the main analysis flow on any iFinD failure path.
- Prefer mapping to small, analyzer-friendly context dicts instead of leaking raw upstream field names into `src/analyzer.py`.
- If the official iFinD payload schema differs from the assumptions above, update only `src/ifind/mappers.py` and `src/ifind/schemas.py` rather than spreading field-name logic into pipeline/analyzer code.
