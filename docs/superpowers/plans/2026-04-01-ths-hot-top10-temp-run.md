# THS Hot Top10 Temp Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a temporary local runner that fetches TongHuaShun's current A-share hot top 10 list and feeds those stock codes into the existing `justice_plutus run` pipeline for a one-off analysis.

**Architecture:** Keep the formal CLI unchanged. Add one small Python module that loads local overlay env values, pulls hot stocks from TongHuaShun via `pywencai`, normalizes the returned 6-digit codes, and then calls the existing CLI run command with those codes. Cover the behavior with focused unit tests around code extraction and runner argument wiring.

**Tech Stack:** Python, pytest, pandas, pywencai, python-dotenv

---

### Task 1: Add failing tests for THS hot stock extraction and runner wiring

**Files:**
- Create: `tests/test_ths_hot_runner.py`
- Test: `tests/test_ths_hot_runner.py`

- [ ] **Step 1: Write the failing test**

```python
def test_extract_hot_stock_codes_prefers_a_share_6_digit_codes():
    ...

def test_build_run_args_passes_hot_codes_into_existing_run_command():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ths_hot_runner.py -q`
Expected: FAIL because `justice_plutus.ths_hot_runner` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def extract_hot_stock_codes(...):
    ...

def build_run_args(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ths_hot_runner.py -q`
Expected: PASS

### Task 2: Add a temporary runnable entrypoint and verify one-off execution path

**Files:**
- Create: `justice_plutus/ths_hot_runner.py`
- Modify: `justice_plutus/ths_hot_runner.py`
- Test: `tests/test_ths_hot_runner.py`

- [ ] **Step 1: Write the failing test**

```python
def test_main_fetches_hot_codes_and_invokes_run_command(monkeypatch):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ths_hot_runner.py -q`
Expected: FAIL because `main()` is incomplete.

- [ ] **Step 3: Write minimal implementation**

```python
def main(argv=None):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ths_hot_runner.py -q`
Expected: PASS

- [ ] **Step 5: Verify the real one-off flow**

Run: `./.venv/bin/python -m justice_plutus.ths_hot_runner --limit 10`
Expected: the runner fetches today's THS hot top 10 list, injects the codes into the existing pipeline, and writes reports under `reports/YYYY-MM-DD/`.
