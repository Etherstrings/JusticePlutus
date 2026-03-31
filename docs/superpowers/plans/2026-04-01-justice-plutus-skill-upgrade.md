# JusticePlutus Skill Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the packaged OpenClaw / ClawHub `justice-plutus` skill so it truthfully reflects the current local JusticePlutus capabilities, including Feishu notifications and optional iFinD enhancement.

**Architecture:** Keep the skill as a local-run wrapper around `python -m justice_plutus run`, but expand the packaged contract in `SKILL.md` and `references/overview.md`, then upgrade `scripts/run_analysis.sh` to expose `--notify`, `--ifind`, and `--dry-run` as explicit runtime toggles. Preserve the project’s non-intrusive enhancement behavior by using temporary environment flags instead of mutating local `.env` files.

**Tech Stack:** Markdown, POSIX shell, existing JusticePlutus CLI

---

### Task 1: Rewrite The Public Skill Contract

**Files:**
- Modify: `justice-plutus/SKILL.md`

- [ ] **Step 1: Review the current skill contract against the latest repository capabilities**

Reference:
- `justice-plutus/SKILL.md`
- `README.md`
- `docs/IFIND_ENHANCEMENT_GUIDE.md`
- `docs/merge_notes/2026-03-30-feishu-workflow-merge.md`

Expected outcome:
- A clear list of outdated statements to replace:
  - minimal description
  - only `OPENAI_API_KEY` framing
  - no Feishu mention
  - no iFinD / search / chip enhancement framing

- [ ] **Step 2: Rewrite the frontmatter and headline description**

Update:
- `description`
- `version`
- keep the homepage unless a better user-facing link is needed

Expected content direction:
- local A-share analysis
- Markdown / JSON reports
- optional Feishu notifications
- optional iFinD fundamental enhancement

- [ ] **Step 3: Rewrite purpose, inputs, outputs, and command sections**

Add concrete user-facing command coverage for:
- base run
- notify run
- dry run
- iFinD-enhanced run

Keep examples in direct shell form.

- [ ] **Step 4: Rewrite notes and support sections**

Make the notes explicitly cover:
- core requirement vs optional enhancements
- search enhancement
- chip enhancement
- Feishu notifications
- iFinD as enhancement-only and non-intrusive

- [ ] **Step 5: Commit**

```bash
git add justice-plutus/SKILL.md
git commit -m "docs: refresh JusticePlutus skill contract"
```

### Task 2: Rewrite The Skill Overview Reference

**Files:**
- Modify: `justice-plutus/references/overview.md`

- [ ] **Step 1: Replace the current thin summary with an operator-facing overview**

Target sections:
- summary
- inputs
- outputs
- runtime flow
- optional enhancements
- notifications
- degradation behavior

- [ ] **Step 2: Make enhancement behavior explicit and user-facing**

The overview should explain:
- search enhancement is optional
- chip enhancement is optional
- iFinD is optional and does not replace the main flow
- notifications are optional when channels are configured

- [ ] **Step 3: Check wording for external/public clarity**

Remove:
- internal shorthand
- branch / merge language
- developer-only framing

- [ ] **Step 4: Commit**

```bash
git add justice-plutus/references/overview.md
git commit -m "docs: expand JusticePlutus skill overview"
```

### Task 3: Upgrade The Skill Runner Script

**Files:**
- Modify: `justice-plutus/scripts/run_analysis.sh`

- [ ] **Step 1: Define the supported CLI contract**

Supported forms:
- `run_analysis.sh <codes>`
- `run_analysis.sh <codes> --notify`
- `run_analysis.sh <codes> --ifind`
- `run_analysis.sh <codes> --dry-run`
- combined flags in any order after codes

- [ ] **Step 2: Implement minimal flag parsing**

Requirements:
- reject unknown flags with usage output
- default to `--no-notify`
- if `--notify` is present, omit `--no-notify`
- if `--dry-run` is present, pass it through
- if `--ifind` is present, export:
  - `ENABLE_IFIND=true`
  - `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`

- [ ] **Step 3: Preserve simple runtime requirements**

Keep:
- core AI-key guard for the current local skill path
- donation notice

Avoid:
- writing to local config files
- assuming every optional provider must exist

- [ ] **Step 4: Run shell-level verification**

Run:
- `sh justice-plutus/scripts/run_analysis.sh`
Expected:
- usage error / exit 2

Run:
- `OPENAI_API_KEY=dummy sh justice-plutus/scripts/run_analysis.sh 600519 --dry-run`
Expected:
- command reaches the project CLI invocation path

Run:
- `OPENAI_API_KEY=dummy sh justice-plutus/scripts/run_analysis.sh 600519 --ifind --dry-run`
Expected:
- command sets iFinD env flags and reaches the project CLI invocation path

- [ ] **Step 5: Commit**

```bash
git add justice-plutus/scripts/run_analysis.sh
git commit -m "feat: upgrade JusticePlutus skill runner flags"
```

### Task 4: Final Package Verification

**Files:**
- Verify: `justice-plutus/SKILL.md`
- Verify: `justice-plutus/references/overview.md`
- Verify: `justice-plutus/scripts/run_analysis.sh`

- [ ] **Step 1: Re-read the updated package as a public artifact**

Check:
- does it clearly mention Feishu?
- does it clearly mention iFinD?
- does it preserve local-run positioning?
- does it avoid internal-only language?

- [ ] **Step 2: Run final diff review**

Run:
- `git diff -- justice-plutus/SKILL.md justice-plutus/references/overview.md justice-plutus/scripts/run_analysis.sh`

Expected:
- only the intended skill-package changes

- [ ] **Step 3: Summarize publish-ready state**

Prepare a concise summary covering:
- what changed in the skill package
- what new run modes are exposed
- whether the package is ready for `clawhub publish` / `clawhub sync`

- [ ] **Step 4: Commit**

```bash
git add justice-plutus/SKILL.md justice-plutus/references/overview.md justice-plutus/scripts/run_analysis.sh
git commit -m "feat: upgrade JusticePlutus ClawHub skill package"
```
