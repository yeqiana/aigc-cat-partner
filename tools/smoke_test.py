#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 smoke test for the AIGC story pipeline.

Checks:
1. Python tools compile.
2. JSON config files are valid.
3. The sample input can generate the full V2 artifact set.
"""
from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
OUTPUT_DIR = ROOT / "outputs" / "batch_plans"

REQUIRED_ARTIFACTS = [
    "input.json",
    "story_plan.json",
    "frame_plan.json",
    "copy_plan.json",
    "prompt_plan.json",
    "qa_result.json",
    "retake_prompt.json",
    "prompt_task.md",
]


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def compile_tools() -> None:
    for path in sorted(TOOLS_DIR.glob("*.py")):
        py_compile.compile(str(path), doraise=True)


def run_quiet(command: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        print(result.stdout)
        fail(f"command failed: {' '.join(command)}")


def validate_config() -> None:
    run_quiet([sys.executable, str(TOOLS_DIR / "validate_config.py")])


def newest_task_dir(before: set[Path]) -> Path:
    after = {p for p in OUTPUT_DIR.glob("*_V2_pipeline") if p.is_dir()}
    created = sorted(after - before, key=lambda p: p.stat().st_mtime, reverse=True)
    if not created:
        fail("generate_prompt.py did not create a V2 pipeline output directory")
    return created[0]


def run_sample_generation() -> Path:
    sample_path = ROOT / "examples" / "generic_suspense_series.sample.json"
    if not sample_path.exists():
        fail(f"missing sample input: {sample_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before = {p for p in OUTPUT_DIR.glob("*_V2_pipeline") if p.is_dir()}

    with tempfile.TemporaryDirectory(prefix="aigc_smoke_") as tmp:
        tmp_input = Path(tmp) / "smoke_input.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        data["story_id"] = "smoke_test"
        data["story_title"] = "Smoke Test"
        data["image_count"] = 3
        tmp_input.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        run_quiet([sys.executable, str(TOOLS_DIR / "generate_prompt.py"), "--input", str(tmp_input)])

    return newest_task_dir(before)


def assert_artifacts(task_dir: Path) -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (task_dir / name).exists()]
    if missing:
        fail(f"missing output artifacts in {task_dir}: {', '.join(missing)}")

    story_plan = json.loads((task_dir / "story_plan.json").read_text(encoding="utf-8"))
    prompt_plan = json.loads((task_dir / "prompt_plan.json").read_text(encoding="utf-8"))
    qa_result = json.loads((task_dir / "qa_result.json").read_text(encoding="utf-8"))

    if story_plan.get("image_count") != 3:
        fail("story_plan.image_count should be 3 in smoke test output")
    if len(prompt_plan) != 3:
        fail("prompt_plan should contain 3 frames")
    if len(qa_result) != 3:
        fail("qa_result should contain 3 frames")
    if prompt_plan[0].get("generation_type") != "anchor":
        fail("first prompt frame should be an anchor")
    if prompt_plan[1].get("generation_type") != "continuation":
        fail("second prompt frame should be a continuation")


def main() -> None:
    generated_dir: Path | None = None
    try:
        compile_tools()
        validate_config()
        generated_dir = run_sample_generation()
        assert_artifacts(generated_dir)
    finally:
        if generated_dir and generated_dir.exists():
            shutil.rmtree(generated_dir)

    print("[OK] smoke test passed")


if __name__ == "__main__":
    main()
