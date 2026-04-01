# Append Image After Text Notify Design

Date: 2026-04-02
Branch: `main`

## Summary

This change adds one user-facing master switch for notification enhancement:

- keep the current text notification behavior
- when the new switch is on, send the original text first
- then append one PNG image version of the same report

The requirement applies to both single-stock notifications and aggregate summary notifications. The image is an enhancement, not a replacement. Any image-generation or image-delivery failure must not block the original text push.

## Product Goals

- Add one simple switch for "text first, then image".
- Preserve all existing text notifications.
- Apply the same behavior to:
  - single-stock immediate pushes
  - aggregate summary pushes
  - batch-overview pushes in single-stock mode
- Reuse the existing Markdown-to-image pipeline and keep PNG as the only initial output format.
- Ensure image failures degrade silently to text-only behavior.

## Non-Goals

- Do not replace text notifications with image notifications.
- Do not add JPG or multi-format output in this iteration.
- Do not require users to maintain a per-channel image allowlist for the new behavior.
- Do not expand image delivery to channels that currently lack image-send support.
- Do not change the existing report content structure.

## Confirmed Decisions

- One new master switch is required.
- The switch should affect both single-stock and summary notifications.
- Text must always be sent before image.
- PNG is the only required image format for now.
- Image sending must not affect text-send success.
- Channels without existing image-send support should keep their current text-only behavior.

## User-Facing Behavior

### New Config Switch

Add a new config flag:

- `APPEND_IMAGE_AFTER_TEXT_NOTIFY=false`

Config mapping:

- `false`:
  - keep the current system behavior unchanged
- `true`:
  - send text using the existing notification path
  - after text is sent, attempt to send a PNG image version of the same content

### Scope

When `APPEND_IMAGE_AFTER_TEXT_NOTIFY=true`, the following notification paths should append a PNG after text:

- single-stock immediate notification from `process_single_stock`
- aggregate summary notification from `_send_notifications`
- single-stock mode batch-overview notification

### Success Semantics

- Text success remains the primary success condition.
- Image success is recorded as an enhancement result.
- If text succeeds and image fails, the overall notification is still considered successful.

## Compatibility Rules

The project already has an older image-delivery feature controlled by `MARKDOWN_TO_IMAGE_CHANNELS`. That feature currently converts Markdown to image and, for selected channels, may send image instead of text.

To avoid mixed semantics, the new switch should take precedence:

- when `APPEND_IMAGE_AFTER_TEXT_NOTIFY=false`:
  - preserve the existing `MARKDOWN_TO_IMAGE_CHANNELS` behavior as-is
- when `APPEND_IMAGE_AFTER_TEXT_NOTIFY=true`:
  - the new "text first, then append image" behavior becomes the active rule
  - the system must not replace text with image for those notifications

This preserves backward compatibility for existing users while making the new switch deterministic for the requested behavior.

## Architecture

### 1. Config Layer

Update `src/config.py` to add:

- `append_image_after_text_notify: bool = False`

Load it from environment:

- `APPEND_IMAGE_AFTER_TEXT_NOTIFY`

No new image-format config is required in this iteration.

The implementation should continue reusing:

- `MARKDOWN_TO_IMAGE_MAX_CHARS`
- `MD2IMG_ENGINE`

### 2. Image Rendering Layer

Keep `src/md2img.py` as the single Markdown-to-image conversion utility.

Requirements:

- keep the current function contract returning PNG bytes or `None`
- do not add JPG support in this change
- continue respecting the existing length guard via `max_chars`

### 3. Notification Layer

Update `src/notification.py` to support a new send mode:

- normal text send remains the first action
- if the new switch is enabled, the service attempts an additional image send after text

Recommended structure:

- add one internal helper responsible for:
  - deciding whether append-image mode is active
  - generating PNG bytes once for a given content block
  - sending that image only to channels that already support image delivery
  - logging skip/failure/success clearly

This helper should be reusable from both:

- `NotificationService.send(...)`
- aggregate-report sending paths that bypass `NotificationService.send(...)`

## Runtime Flow

### A. Single-Stock Immediate Notification

Current path:

- `src/core/pipeline.py::process_single_stock`
- generate single-stock report
- call `self.notifier.send(report_content, ...)`

Target behavior:

1. send text using the existing `NotificationService.send(...)` path
2. if append-image mode is enabled:
   - generate PNG from the same `report_content`
   - attempt image sends on supported channels
3. keep text-send result as the primary success result

### B. Aggregate Summary Notification

Current path:

- `src/core/pipeline.py::_send_notifications`

This path contains custom channel handling and does not rely exclusively on `NotificationService.send(...)`, so append-image behavior must also be integrated here.

Target behavior:

1. preserve existing summary-text behavior, including channel-specific special handling
2. once text sending is done, append PNG where supported
3. preserve current special cases:
   - WeChat dashboard formatting
   - email stock-group routing
   - single-stock mode batch-overview push

### C. Batch Overview in Single-Stock Mode

Current path:

- `src/core/pipeline.py::run`
- when `single_stock_notify` is enabled, send `generate_summary_overview(results)`

Target behavior:

- use the same "text first, then image" rule
- no separate config or behavior fork

## Channel Support Policy

In this iteration, append-image should only target channels that already have working image-send capabilities in the codebase:

- WeChat
- Telegram
- Email
- Custom Webhook where the destination is a Discord webhook

All other channels should keep text-only behavior:

- Feishu
- PushPlus
- ServerChan3
- Pushover
- AstrBot
- Discord bot channel paths without image support
- any context-based message channel

The helper should log that these channels remain text-only rather than treating that as an error.

## Error Handling

### Image Generation Failure

If Markdown-to-image conversion returns `None`, skip image sending and keep text already sent.

Common failure cases:

- required local dependency is missing
- content length exceeds `MARKDOWN_TO_IMAGE_MAX_CHARS`
- renderer timeout or conversion error

### Channel Delivery Failure

If image delivery fails for a supported channel:

- log the failure
- do not retry beyond current channel-specific behavior unless already implemented
- do not mark the overall notification as failed if text already succeeded

### WeChat Size Limit

If the generated PNG exceeds the WeChat image size limit:

- keep the text send result
- skip the image send for WeChat
- log a warning

### Unsupported Channels

If a channel has no image-send implementation:

- send text only
- log a debug/info message if needed
- do not treat it as failure

## Logging Expectations

Logs should make the two-stage behavior easy to diagnose:

- text notification succeeded, starting append-image step
- image rendering skipped or failed, keeping text-only result
- channel does not support image append, leaving text-only behavior
- image append succeeded

This is especially important because the enhancement should be observable without making operators think text delivery failed.

## Testing Strategy

Implementation should follow test-first behavior checks.

### 1. Config Tests

Add coverage for:

- default `append_image_after_text_notify == False`
- `APPEND_IMAGE_AFTER_TEXT_NOTIFY=true` loads correctly

### 2. Notification Service Tests

Add coverage for:

- switch off:
  - existing behavior remains unchanged
- switch on:
  - text send happens first
  - image append is attempted afterward
- image render failure:
  - text send success is preserved
- unsupported channel:
  - text still sends
  - no hard failure is raised

### 3. Pipeline Tests

Add coverage for:

- single-stock immediate path uses append-image mode
- aggregate summary path uses append-image mode
- single-stock mode batch-overview path uses append-image mode

### 4. Regression Tests

Protect the previous feature contract:

- when the new switch is off, old `MARKDOWN_TO_IMAGE_CHANNELS` behavior still works as before

## Implementation Notes

The safest rollout is to minimize surface area:

- reuse existing image senders
- centralize append-image orchestration
- avoid changing report generation
- avoid adding a new format abstraction yet

The main complexity is not image rendering itself. It is preserving the current notification branching while introducing a second delivery phase that does not change text semantics.

## Acceptance Criteria

The change is complete when all of the following are true:

- there is one new config switch for append-image behavior
- with the switch off, current notification behavior is unchanged
- with the switch on, text still sends first
- with the switch on, PNG append is attempted for single-stock notifications
- with the switch on, PNG append is attempted for aggregate summary notifications
- image failures do not block or downgrade text delivery
- automated tests cover the new behavior and the compatibility boundary
