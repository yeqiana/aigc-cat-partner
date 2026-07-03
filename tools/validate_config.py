#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可选工具：检查 JSON 配置文件是否完整、可解析。

用法：
  python tools/validate_config.py
  python tools/validate_config.py config/story_templates.json
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"

REQUIRED_KEYS: dict[str, list[str]] = {
    "series_input_schema.json": ["required", "defaults", "fields"],
    "story_templates.json": [],
    "character_spec.json": [],
    "world_spec.json": [],
    "scenes.json": [],
    "reference_manifest.json": [],
}


def validate_json(path: Path) -> list[str]:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON 解析失败：{e}"]
    except Exception as e:
        return [f"读取失败：{e}"]

    required = REQUIRED_KEYS.get(path.name, [])
    for key in required:
        if key not in data:
            errors.append(f"缺少顶级键：{key}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="验证 JSON 配置文件")
    parser.add_argument("files", nargs="*", help="指定文件（默认检查 config/*.json）")
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(CONFIG_DIR.glob("*.json"))

    exit_code = 0
    for path in paths:
        errors = validate_json(path)
        if errors:
            print(f"❌ {path.name}")
            for e in errors:
                print(f"   - {e}")
            exit_code = 1
        else:
            print(f"✅ {path.name}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
