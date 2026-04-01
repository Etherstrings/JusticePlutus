# Append Image After Text Notify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one notification master switch that preserves existing text pushes and, when enabled, appends a PNG image after text for both single-stock and aggregate summary notifications.

**Architecture:** Keep report generation unchanged and reuse the existing Markdown-to-image utility in `src/md2img.py`. Add one new config flag in `src/config.py`, centralize append-image orchestration in `src/notification.py`, and integrate the aggregate-summary path in `src/core/pipeline.py` so single-stock, summary, and batch-overview pushes all follow the same "text first, then image" rule while preserving backward compatibility with `MARKDOWN_TO_IMAGE_CHANNELS` when the new switch is off.

**Tech Stack:** Python 3.11, pytest, existing notification senders, existing Markdown-to-image support

---

## File Map

- `/Users/boyuewu/Projects/JusticePlutus/src/config.py`
  - Add `append_image_after_text_notify` config field and env parsing.
- `/Users/boyuewu/Projects/JusticePlutus/src/notification.py`
  - Add append-image mode detection and shared helper(s) for image append after text.
- `/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py`
  - Preserve current summary text delivery logic, then append channel-appropriate PNGs when the new switch is on.
- `/Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py`
  - Cover default and enabled parsing for the new config flag.
- `/Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py`
  - New focused tests for direct notification send behavior and summary-path append behavior.
- `/Users/boyuewu/Projects/JusticePlutus/.env.example`
  - Document the new env flag near existing notification/image config.
- `/Users/boyuewu/Projects/JusticePlutus/README.md`
  - Add a short operator-facing explanation of the new flag and its interaction with text notifications.

### Task 1: Add the master switch and document it

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/config.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/.env.example`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/README.md`
- Test: `/Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py`

- [ ] **Step 1: Write the failing config tests**

```python
def test_append_image_after_text_notify_defaults_to_disabled(monkeypatch):
    cfg = _load_config(monkeypatch)
    assert cfg.append_image_after_text_notify is False


def test_append_image_after_text_notify_can_be_enabled(monkeypatch):
    cfg = _load_config(
        monkeypatch,
        APPEND_IMAGE_AFTER_TEXT_NOTIFY="true",
    )
    assert cfg.append_image_after_text_notify is True
```

Implementation note:
- Extend `_load_config()` cleanup in the same test file so `APPEND_IMAGE_AFTER_TEXT_NOTIFY` is cleared between tests.

- [ ] **Step 2: Run the config tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py -k "append_image_after_text_notify" -v
```

Expected: FAIL with missing `append_image_after_text_notify` on `Config`.

- [ ] **Step 3: Implement the config flag parsing and docs**

```python
@dataclass
class Config:
    append_image_after_text_notify: bool = False


append_image_after_text_notify=(
    os.getenv("APPEND_IMAGE_AFTER_TEXT_NOTIFY", "false").lower() == "true"
)
```

Documentation requirements:
- Add one commented example to `.env.example`.
- Add one short README note clarifying:
  - default behavior is unchanged
  - enabling the new flag sends text first and then PNG
  - this applies to both single-stock and summary notifications

- [ ] **Step 4: Run the config tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py -k "append_image_after_text_notify" -v
```

Expected: PASS for both new tests.

- [ ] **Step 5: Commit the config/docs slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/config.py /Users/boyuewu/Projects/JusticePlutus/.env.example /Users/boyuewu/Projects/JusticePlutus/README.md /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py
git commit -m "feat: add append-image notify config"
```

### Task 2: Add append-image behavior to direct notification sending

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/notification.py`
- Create: `/Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py`

- [ ] **Step 1: Write the failing notification-service tests**

```python
def test_send_appends_png_after_text_when_switch_enabled(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=True,
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = lambda image_bytes: events.append(("image", image_bytes)) or True
    monkeypatch.setattr("src.md2img.markdown_to_image", lambda content, max_chars=15000: b"png")

    assert notifier.send("hello") is True
    assert events == [("text", "hello"), ("image", b"png")]


def test_send_keeps_text_success_when_image_render_fails(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=True,
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = lambda image_bytes: events.append(("image", image_bytes)) or True
    monkeypatch.setattr("src.md2img.markdown_to_image", lambda content, max_chars=15000: None)

    assert notifier.send("hello") is True
    assert events == [("text", "hello")]


def test_send_preserves_legacy_replace_with_image_mode_when_append_switch_off(monkeypatch):
    notifier = build_test_notifier(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=False,
        markdown_to_image_channels={"telegram"},
    )
    events = []
    notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    notifier._send_telegram_photo = lambda image_bytes: events.append(("image", image_bytes)) or True
    monkeypatch.setattr("src.md2img.markdown_to_image", lambda content, max_chars=15000: b"png")

    assert notifier.send("hello") is True
    assert events == [("image", b"png")]
```

Test helper requirements:
- Build a `NotificationService` instance via `__new__` to avoid full config wiring.
- Stub `send_to_context`, `_available_channels`, `_markdown_to_image_channels`, `_markdown_to_image_max_chars`, `_append_image_after_text_notify`, and any sender method each test touches.

- [ ] **Step 2: Run the new notification tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py -v
```

Expected: FAIL because `NotificationService.send(...)` does not currently support append-image mode.

- [ ] **Step 3: Implement append-image orchestration in `src/notification.py`**

```python
class NotificationService(...):
    def __init__(...):
        self._append_image_after_text_notify = getattr(
            config,
            "append_image_after_text_notify",
            False,
        )

    def _append_image_mode_enabled(self) -> bool:
        return bool(self._append_image_after_text_notify)

    def _render_png_for_append(self, content: str) -> Optional[bytes]:
        if not self._append_image_mode_enabled():
            return None
        return markdown_to_image(content, max_chars=self._markdown_to_image_max_chars)

    def _append_image_after_text(
        self,
        content: str,
        channels: list[NotificationChannel],
        email_receivers: Optional[list[str]] = None,
    ) -> None:
        ...
```

Implementation requirements:
- Keep the existing replacement behavior fully intact when the new switch is off.
- When the new switch is on:
  - always send text first using the current per-channel logic
  - then try to send PNG only to supported channels
- Supported direct-send channels in this task:
  - WeChat
  - Telegram
  - Email
  - Custom Webhook via `_send_custom_webhook_image(image_bytes, fallback_content="")`
- Do not pass fallback text into `_send_custom_webhook_image(...)` during append mode, because text was already sent.
- Do not treat unsupported channels as failure.

- [ ] **Step 4: Run the new notification tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py -v
```

Expected: PASS for append-image ordering, render-failure fallback, and legacy compatibility behavior.

- [ ] **Step 5: Commit the direct notification slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/notification.py /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py
git commit -m "feat: append png after direct text notifications"
```

### Task 3: Add append-image behavior to aggregate summary delivery

**Files:**
- Modify: `/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py`
- Modify: `/Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py`

- [ ] **Step 1: Write the failing aggregate-summary tests**

```python
def test_send_notifications_appends_image_after_summary_text(monkeypatch):
    pipeline = build_test_pipeline(
        channels=[NotificationChannel.TELEGRAM],
        append_image_after_text_notify=True,
    )
    events = []
    pipeline.notifier.send_to_context = lambda content: False
    pipeline.notifier.send_to_telegram = lambda content: events.append(("text", content)) or True
    pipeline.notifier._send_telegram_photo = lambda image_bytes: events.append(("image", image_bytes)) or True
    monkeypatch.setattr("src.md2img.markdown_to_image", lambda content, max_chars=15000: b"png")

    pipeline._send_notifications([build_result()], ReportType.SIMPLE)

    assert events[0][0] == "text"
    assert events[1] == ("image", b"png")


def test_send_notifications_keeps_wechat_text_when_png_is_oversized(monkeypatch):
    pipeline = build_test_pipeline(
        channels=[NotificationChannel.WECHAT],
        append_image_after_text_notify=True,
    )
    events = []
    pipeline.notifier.generate_wechat_dashboard = lambda results: "wechat-content"
    pipeline.notifier.send_to_wechat = lambda content: events.append(("text", content)) or True
    pipeline.notifier._send_wechat_image = lambda image_bytes: events.append(("image", image_bytes)) or True
    monkeypatch.setattr("src.md2img.markdown_to_image", lambda content, max_chars=15000: b"x" * (2 * 1024 * 1024 + 1))

    pipeline._send_notifications([build_result()], ReportType.SIMPLE)

    assert events == [("text", "wechat-content")]
```

Test helper requirements:
- `build_test_pipeline(...)` should construct `StockAnalysisPipeline.__new__(...)` and attach a fake notifier with:
  - `save_report_to_file`
  - `is_available`
  - `get_available_channels`
  - `send_to_context`
  - channel methods touched by the test
  - `_markdown_to_image_max_chars`
  - `_append_image_after_text_notify`
- `build_result()` should return a minimal `AnalysisResult` that can pass through report generation.

- [ ] **Step 2: Run the aggregate-summary tests to verify they fail**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py -k "send_notifications" -v
```

Expected: FAIL because `_send_notifications(...)` currently uses image delivery only as a replacement path, not as a second phase.

- [ ] **Step 3: Implement summary-path append-image behavior in `src/core/pipeline.py`**

```python
def _send_notifications(...):
    ...
    if self.notifier._append_image_after_text_notify:
        # keep all existing text sends
        # then append image per channel/content variant
        ...
```

Implementation requirements:
- Preserve existing text-path branching exactly:
  - WeChat still uses dashboard content
  - grouped email recipients still get grouped reports
  - batch-overview push still uses summary-overview text
- After text sending, append images using the same content each channel received:
  - `dashboard_content` for WeChat
  - `report` for Telegram / Custom / default email path
  - `grp_report` for grouped email routes
- Reuse `NotificationService._should_use_image_for_channel(...)` for channel-specific limits like WeChat size.
- Keep the old replacement behavior only for the legacy mode when the new switch is off.

- [ ] **Step 4: Run the aggregate-summary tests again**

Run:

```bash
python3 -m pytest /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py -k "send_notifications" -v
```

Expected: PASS for summary append ordering and WeChat oversize fallback.

- [ ] **Step 5: Commit the aggregate summary slice**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py
git commit -m "feat: append png after summary notifications"
```

### Task 4: Run full regression checks for the feature boundary

**Files:**
- Verify: `/Users/boyuewu/Projects/JusticePlutus/src/config.py`
- Verify: `/Users/boyuewu/Projects/JusticePlutus/src/notification.py`
- Verify: `/Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py`
- Verify: `/Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py`
- Verify: `/Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py`
- Verify: `/Users/boyuewu/Projects/JusticePlutus/tests/test_formatters_and_notification.py`

- [ ] **Step 1: Run the focused feature test set**

Run:

```bash
python3 -m pytest \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py \
  /Users/boyuewu/Projects/JusticePlutus/tests/test_formatters_and_notification.py -v
```

Expected:
- all append-image and existing notification-formatting tests PASS

- [ ] **Step 2: Review the final diff for the intended scope**

Run:

```bash
git diff -- /Users/boyuewu/Projects/JusticePlutus/src/config.py /Users/boyuewu/Projects/JusticePlutus/src/notification.py /Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py /Users/boyuewu/Projects/JusticePlutus/.env.example /Users/boyuewu/Projects/JusticePlutus/README.md
```

Expected:
- only the new append-image feature, docs, and tests are changed

- [ ] **Step 3: Summarize runtime usage**

Prepare a concise operator summary covering:
- the new env flag name
- default off behavior
- text-first, image-second behavior when enabled
- supported image-append channels in this iteration

- [ ] **Step 4: Commit the final verification state**

```bash
git add /Users/boyuewu/Projects/JusticePlutus/src/config.py /Users/boyuewu/Projects/JusticePlutus/src/notification.py /Users/boyuewu/Projects/JusticePlutus/src/core/pipeline.py /Users/boyuewu/Projects/JusticePlutus/tests/test_config_llm_and_stock_overrides.py /Users/boyuewu/Projects/JusticePlutus/tests/test_notification_append_image.py /Users/boyuewu/Projects/JusticePlutus/.env.example /Users/boyuewu/Projects/JusticePlutus/README.md
git commit -m "feat: append png after text notifications"
```
