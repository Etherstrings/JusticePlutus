# Tonghuashun iFinD Routing Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `tonghuashun-ifind` skill directly usable for common stock and index questions by adding deterministic routing and a documented fallback path.

**Architecture:** Keep the existing auth and raw `api-call` primitives, then add a routing layer plus explicit common-query commands. The routing layer resolves entities, selects stable endpoint templates, and returns doc-guided fallback errors instead of guessing unsupported APIs.

**Tech Stack:** Python 3, pytest, OpenClaw skill folder layout, existing iFinD HTTP wrapper

---

### Task 1: Add routing tests for the working copy

**Files:**
- Create: `tests/test_tonghuashun_ifind_skill.py`
- Test: `tests/test_tonghuashun_ifind_skill.py`

- [ ] **Step 1: Write the failing tests**

Cover:

- stock realtime route
- stock history route with relative date parsing
- market snapshot route for `大盘`
- fundamental route template generation
- unsupported-query fallback guidance

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tonghuashun_ifind_skill.py -q`
Expected: FAIL because routing module and CLI commands do not exist yet

### Task 2: Implement routing and command execution

**Files:**
- Modify: `.tmp/tonghuashun-ifind-skill/scripts/ifind_cli.py`
- Create: `.tmp/tonghuashun-ifind-skill/scripts/runtime/tonghuashun_ifind_skill/routing.py`

- [ ] **Step 1: Add the routing module**

Implement:

- intent detection
- symbol normalization
- common index alias map
- relative date parsing
- route-plan building

- [ ] **Step 2: Extend the CLI**

Add commands:

- `smart-query`
- `quote-realtime`
- `quote-history`
- `market-snapshot`
- `fundamental-basic`

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_tonghuashun_ifind_skill.py -q`
Expected: PASS

### Task 3: Update skill instructions and fallback docs

**Files:**
- Modify: `.tmp/tonghuashun-ifind-skill/SKILL.md`
- Modify: `.tmp/tonghuashun-ifind-skill/agents/openai.yaml`
- Modify: `.tmp/tonghuashun-ifind-skill/references/usage.md`
- Create: `.tmp/tonghuashun-ifind-skill/references/routing.md`

- [ ] **Step 1: Update the skill contract**

Make `smart-query` the primary entry for common user requests. Keep `api-call` as the advanced fallback after reading local routing docs.

- [ ] **Step 2: Add reference examples**

Include examples for the four common routes plus the manual-lookup fallback procedure.

- [ ] **Step 3: Run tests again**

Run: `pytest tests/test_tonghuashun_ifind_skill.py -q`
Expected: PASS

### Task 4: Verify and sync back to the installed skill

**Files:**
- Modify: `~/.openclaw/workspace/skills/tonghuashun-ifind/*` via sync from the working copy

- [ ] **Step 1: Smoke-test the CLI on the working copy**

Run:

- `python3 .tmp/tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query --query "看一下大盘"`
- `python3 .tmp/tonghuashun-ifind-skill/scripts/ifind_cli.py smart-query --query "看下贵州茅台近一个月走势"`

Expected: deterministic route selection; auth may still fail without tokens, but the selected route and payload should be correct

- [ ] **Step 2: Sync the working copy back to the installed skill**

Copy the updated files from `.tmp/tonghuashun-ifind-skill` into `~/.openclaw/workspace/skills/tonghuashun-ifind`

- [ ] **Step 3: Re-run the same smoke checks against the installed skill**

Expected: same command behavior from the installed location
