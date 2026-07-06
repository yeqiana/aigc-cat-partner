#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an embedded chapter archive for storyboard_config.html."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DIR = ROOT / "prompts" / "chapter"
PLAN_FILE = ROOT / "config" / "chapter_scene_plan.json"
OUT_FILE = ROOT / "\u5165\u53e3" / "storyboard_chapter_archive.js"


def source_file_for(data: dict, path: Path, plan: dict) -> str:
    if data.get("source_file"):
        return str(data["source_file"])

    match = re.search(r"chapter_(\d+)\.input\.json$", path.name)
    if match:
        chapter = plan.get("chapters", {}).get(str(int(match.group(1))), {})
        if chapter.get("source_file"):
            return str(chapter["source_file"])

    extra = str(data.get("extra") or "")
    match = re.search(r"\u539f\u6587\u6765\u6e90[：:]([^\u3002.]+)", extra)
    return match.group(1).strip() if match else ""


def load_chapter_inputs() -> list[dict]:
    plan = json.loads(PLAN_FILE.read_text(encoding="utf-8")) if PLAN_FILE.exists() else {}
    chapters = []
    for path in sorted(CHAPTER_DIR.glob("chapter_*.input.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["source_file"] = source_file_for(data, path, plan)
        chapters.append(
            {
                "id": path.stem,
                "label": data.get("story_title") or path.stem,
                "source_file": data["source_file"],
                "input": data,
            }
        )
    return chapters


def main() -> None:
    chapters = load_chapter_inputs()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(chapters, ensure_ascii=False, indent=2)
    OUT_FILE.write_text(
        "window.STORYBOARD_CHAPTER_ARCHIVE = "
        + payload
        + ";\n",
        encoding="utf-8",
    )
    print(f"Generated chapter archive: {OUT_FILE}")
    print(f"Chapter count: {len(chapters)}")


if __name__ == "__main__":
    main()
