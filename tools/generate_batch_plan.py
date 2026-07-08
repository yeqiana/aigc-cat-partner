#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 Prompt 任务
用法：python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def chapter_number(task: dict) -> int | None:
    for key in ["story_id", "source_file", "story_title"]:
        match = re.search(r"chapter_(\d{3})", str(task.get(key) or ""))
        if match:
            return int(match.group(1))
        match = re.search(r"第(\d+)章", str(task.get(key) or ""))
        if match:
            return int(match.group(1))
    return None


def frame_score(frames) -> int:
    if not isinstance(frames, list):
        return 0
    keys = [
        "scene",
        "action",
        "state",
        "visual_evidence",
        "camera",
        "shot_type",
        "focus",
        "scene_detail",
        "action_momentum_detail",
        "continuity_link",
        "character_path",
        "panel_composition",
    ]
    return sum(1 for frame in frames if isinstance(frame, dict) for key in keys if not is_blank(frame.get(key)))


def hydrate_from_chapter_input(task: dict) -> dict:
    chapter = chapter_number(task)
    if not chapter:
        return task
    chapter_path = ROOT / "prompts" / "chapter" / f"chapter_{chapter:03d}.input.json"
    if not chapter_path.exists():
        return task
    chapter_data = json.loads(chapter_path.read_text(encoding="utf-8"))
    merged = dict(chapter_data)
    for key, value in task.items():
        if not is_blank(value):
            merged[key] = value
    if frame_score(chapter_data.get("custom_frames")) > frame_score(task.get("custom_frames")):
        merged["custom_frames"] = chapter_data.get("custom_frames")
        merged["image_count"] = chapter_data.get("image_count", merged.get("image_count"))
    return merged


def main():
    parser = argparse.ArgumentParser(description="批量生成 Prompt 任务")
    parser.add_argument("--input", required=True, help="批量计划 JSON")
    parser.add_argument("--project-profile", default=None, help="项目层 profile；不传则只使用通用层配置")
    parser.add_argument("--policy", default=None)
    parser.add_argument("--character-lock", default=None)
    parser.add_argument("--scene-lock", default=None)
    parser.add_argument("--text-strategy", default=None)
    parser.add_argument("--character-spec", default=None)
    parser.add_argument("--reference-manifest", default=None)
    parser.add_argument("--negative-prompt-common", default=None)
    parser.add_argument("--negative-prompt-project", default=None)
    args = parser.parse_args()
    plan_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    tasks = plan.get("tasks", [])
    if not tasks:
        print("没有 tasks")
        return
    tmp_dir = ROOT / "outputs" / "batch_plans" / "_tmp_batch_inputs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for idx, task in enumerate(tasks, 1):
        task = hydrate_from_chapter_input(task)
        p = tmp_dir / f"task_{idx:02d}.json"
        p.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        command = [sys.executable, str(ROOT / "tools" / "generate_prompt.py"), "--input", str(p)]
        optional_args = {
            "--project-profile": args.project_profile,
            "--policy": args.policy,
            "--character-lock": args.character_lock,
            "--scene-lock": args.scene_lock,
            "--text-strategy": args.text_strategy,
            "--character-spec": args.character_spec,
            "--reference-manifest": args.reference_manifest,
            "--negative-prompt-common": args.negative_prompt_common,
            "--negative-prompt-project": args.negative_prompt_project,
        }
        for flag, value in optional_args.items():
            if value:
                command.extend([flag, value])
        subprocess.run(command, check=True)
    print(f"批量生成完成，共 {len(tasks)} 个任务。")

if __name__ == "__main__":
    main()
