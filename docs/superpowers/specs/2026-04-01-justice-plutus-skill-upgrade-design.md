# JusticePlutus ClawHub Skill Upgrade Design

## Goal

Upgrade the published `justice-plutus` OpenClaw / ClawHub skill so its
packaged capability description and entry script reflect the current local
JusticePlutus product state.

The upgraded skill should continue to represent a **local-run** workflow, while
accurately exposing:

- Feishu notification support
- optional iFinD financial-analysis enhancement
- existing search enhancement
- existing chip-distribution enhancement
- current report outputs and non-intrusive degradation behavior

## Scope

This work only updates the packaged skill artifact under `justice-plutus/`.

In scope:

- `justice-plutus/SKILL.md`
- `justice-plutus/references/overview.md`
- `justice-plutus/scripts/run_analysis.sh`

Out of scope:

- core analysis pipeline logic under `src/`
- GitHub Actions workflow behavior
- new notification channels
- new data-source integrations
- ClawHub backend / publishing infrastructure

## Product Positioning

The skill remains a **local executor** for the repository’s existing pipeline.

It should not present itself as:

- a hosted SaaS service
- a GitHub Actions trigger wrapper
- a separate financial-report product

Instead, it should present itself as the OpenClaw-facing entry point for
running JusticePlutus on the local machine with optional enhancement modules.

## User-Facing Outcome

After the upgrade, a ClawHub / OpenClaw user who installs this skill should be
able to understand all major current capabilities from the packaged material
without reading the full repository README.

Specifically, the skill should make these points clear:

1. Base capability:
   - run local A-share analysis for one or more stock codes
   - produce Markdown and JSON reports

2. Optional enhancement capability:
   - search enhancement through configured providers
   - chip-distribution enhancement through configured providers
   - iFinD-based fundamental / valuation / forecast enhancement

3. Notification capability:
   - local run can optionally send notifications when channels are configured
   - Feishu should be named explicitly as a supported notification path

4. Reliability / degradation behavior:
   - missing optional enhancement keys should not block the main run
   - iFinD remains enhancement-only and non-intrusive

## Design Decisions

### 1. Keep the skill local-first

The skill will continue to run `python -m justice_plutus run` locally and will
not be reframed around remote workflow dispatch.

Reason:

- matches the repository’s current skill packaging
- matches the user-approved direction
- avoids turning one skill into two different operational models

### 2. Expand `SKILL.md` from minimal launcher text into a capability contract

`SKILL.md` should become the primary public contract for:

- what the skill does
- what is required to use it
- what is optional
- how to invoke enhanced runs

It should explicitly call out:

- Feishu notification support
- optional iFinD enhancement
- optional search / chip enhancement
- outputs and behavior when optional modules are unavailable

### 3. Turn `overview.md` into a concise operational overview

`overview.md` should stop being a thin summary and instead explain:

- the runtime flow
- the role of optional enhancements
- the report outputs
- the notification behavior
- the non-intrusive enhancement principle

This file should read like an operator-facing overview rather than internal dev
notes.

### 4. Upgrade `run_analysis.sh` to expose key runtime toggles

The script should remain simple, but it should no longer hide the newly shipped
capabilities.

Planned CLI surface:

- `run_analysis.sh <codes>`
- `run_analysis.sh <codes> --notify`
- `run_analysis.sh <codes> --ifind`
- `run_analysis.sh <codes> --dry-run`
- combinations of the above flags

Planned behavior:

- `--notify` removes `--no-notify`
- `--ifind` sets:
  - `ENABLE_IFIND=true`
  - `ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true`
- `--dry-run` passes `--dry-run`
- the script must not mutate `.env` or local files

### 5. Keep enhancement dependencies optional in presentation

The skill metadata should continue to treat the core LLM path as the primary
runtime requirement, while user-facing docs distinguish:

- core requirement:
  - Python
  - AI model key path already expected by JusticePlutus
- optional enhancement configuration:
  - Feishu webhook
  - iFinD refresh token
  - search provider keys
  - chip provider credentials

The purpose is to avoid misleading users into thinking every optional provider
is mandatory.

## File-Level Plan

### `justice-plutus/SKILL.md`

Update:

- version
- description
- purpose
- inputs / outputs
- command examples
- notes / support sections

Add:

- explicit Feishu support
- explicit iFinD enhancement description
- explicit search and chip enhancement description
- examples for normal run, notify run, dry run, and iFinD-enhanced run

### `justice-plutus/references/overview.md`

Rewrite into:

- short product summary
- input / output summary
- pipeline flow summary
- optional enhancement summary
- notification summary
- degradation summary

### `justice-plutus/scripts/run_analysis.sh`

Upgrade to:

- parse multiple flags safely
- preserve current default behavior
- inject temporary environment flags for iFinD enhancement
- support `--notify` and `--dry-run`
- print helpful usage guidance on invalid input

## Error Handling Expectations

The upgraded script and docs should preserve the current non-intrusive story:

- missing optional keys should not be presented as fatal unless they are needed
  for the requested mode
- enabling iFinD from the wrapper should still rely on the pipeline’s existing
  graceful fallback behavior
- notification remains optional

## Testing / Verification Expectations

Verification for this task should focus on package correctness:

1. Read the updated `SKILL.md` and confirm it matches current repository
   abilities.
2. Read `overview.md` and confirm it is user-facing rather than internal.
3. Run the shell script usage path and one or more non-destructive invocations
   to confirm flag parsing is correct.
4. Confirm the skill package remains publishable as a normal ClawHub skill
   folder.

## Success Criteria

This design is successful when:

- the skill package truthfully reflects current JusticePlutus capabilities
- Feishu and iFinD are visible in the packaged skill docs
- the entry script exposes the corresponding runtime options
- the skill still reads as a clean local-run OpenClaw skill, not a mixed-mode
  remote tool
