# CLAUDE.md

This file provides guidance when working with this repository.

## Project Overview

This repository is now a **通用剧情连载系统 V2.0** for AIGC story-image series generation.

The core goal is to generate inspectable, repairable text artifacts before image generation:

```text
minimal input
  -> story_plan.json
  -> frame_plan.json
  -> copy_plan.json
  -> prompt_plan.json
  -> qa_result.json
  -> retake_prompt.json
  -> prompt_task.md
```

The system preserves generic production capabilities and should not reintroduce old project-specific IP content into the new generic layer.

## Commands

```bash
# Generate a generic suspense series task
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json

# Batch-generate multiple prompt tasks
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
```

This project uses Python standard library only. There is no package install step.

## Current Architecture

| Path | Purpose |
|---|---|
| `tools/generate_prompt.py` | Generic story-series prompt pipeline generator. |
| `tools/generate_batch_plan.py` | Batch runner that calls `generate_prompt.py` per task. |
| `config/series_input_schema.json` | Generic input schema. |
| `config/story_templates.json` | Generic story templates and frame beats. |
| `config/negative_prompt_common.txt` | Common negative prompt. |
| `config/negative_prompt_project.txt` | Project-specific negative prompt placeholder. |
| `config/character_spec.json` | Generic character visual-gene template. |
| `config/world_spec.json` | Generic world/style template. |
| `config/reference_manifest.json` | Generic cross-session identity/style reference manifest. |
| `examples/generic_suspense_series.sample.json` | Primary sample input. |
| `入口/START_HERE.md` | Human-facing quick start. |

## Core Rules

- Keep `story_plan / frame_plan / copy_plan / prompt_plan / qa_result / retake_prompt` outputs stable.
- Keep the anchor-frame sequence:
  - Frame 1: anchor.
  - Frame 2: identity/style references + frame 1 anchor.
  - Frame 3+: identity/style references + frame 1 anchor + previous generated frame.
- Do not parallel-generate all frames for a continuous story.
- Keep text rendering default as blank bubble / reserved safe area plus post-production text.
- Keep common and project-specific negative prompts separated.
- Treat old IP-specific files and assets as historical references unless the user explicitly asks to migrate or delete them.

## Implementation Notes

- Prefer small, reversible edits.
- Do not add new dependencies.
- Do not delete generated images or historical assets unless explicitly requested.
- When changing `tools/generate_prompt.py`, validate at least:

```bash
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
```
