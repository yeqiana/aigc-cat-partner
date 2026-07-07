#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt QA V3。

根据角色、场景、分镜和文字策略输出人工验收清单。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def checklist(data: dict[str, Any], policy: dict[str, Any], character_lock: dict[str, Any], scene_lock: dict[str, Any], text_strategy: dict[str, Any]) -> dict[str, Any]:
    character_checks = []
    for char in character_lock.get("characters", {}).values():
        character_checks.append(f"{char.get('display_name')}：{char.get('must')}")
        character_checks.extend(char.get("visual_rules", [])[:3])
        character_checks.extend(char.get("behavior_rules", [])[:2])

    scene_checks = []
    scene_name = data.get("scene", "")
    for scene in scene_lock.get("scenes", {}).values():
        if scene.get("display_name") in scene_name or not scene_checks:
            scene_checks = [
                f"场景：{scene.get('display_name')}",
                f"空间：{scene.get('space')}",
                f"天气/季节：{scene.get('season_weather')}",
                "关键道具：" + "、".join(scene.get("props", [])),
                "感官细节：" + "、".join(scene.get("sensory_details", [])),
            ]
            if scene.get("display_name") in scene_name:
                break

    storyboard = policy.get("storyboard", {})
    storyboard_checks = [
        f"画幅必须为 {storyboard.get('ratio', '9:16')}",
        f"必须是 {storyboard.get('panel_count', '2-3')} 格漫画分镜",
        f"布局必须包含 {storyboard.get('layout', '主画面 + 特写小窗')}",
        *storyboard.get("required_shots", []),
    ]

    text_default = text_strategy.get("default", {})
    text_checks = [
        f"allow_text_in_image 默认必须为 {text_default.get('allow_text_in_image', False)}",
        f"文字模式：{text_default.get('text_render_mode')}",
        f"人物姓名标注：{text_default.get('character_label_mode')}",
        "不得出现人物姓名标签、章节标题、第几帧、顶部标题栏或中文乱码",
    ]

    return {
        "story_id": data.get("story_id", ""),
        "story_title": data.get("story_title", ""),
        "scene": data.get("scene", ""),
        "must_pass": policy.get("acceptance", []),
        "character_checks": character_checks,
        "scene_checks": scene_checks,
        "storyboard_checks": storyboard_checks,
        "text_checks": text_checks,
        "retake_rule": "如任一项失败，保留人物母版图、场景母版图、首帧锚点图和上一帧成图，只修复失败项；反复失败时更新 config 或 docs 规则。"
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Prompt QA 验收清单",
        "",
        f"- 故事：{result.get('story_title') or result.get('story_id')}",
        f"- 场景：{result.get('scene')}",
        "",
        "## 必须通过",
    ]
    for item in result["must_pass"]:
        lines.append(f"- [ ] {item}")
    for section, title in [
        ("character_checks", "人物检查"),
        ("scene_checks", "场景检查"),
        ("storyboard_checks", "分镜检查"),
        ("text_checks", "文字检查"),
    ]:
        lines.extend(["", f"## {title}"])
        for item in result[section]:
            lines.append(f"- [ ] {item}")
    lines.extend(["", "## 返工规则", f"- {result['retake_rule']}"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="输出 Prompt 验收清单")
    parser.add_argument("--input", required=True, help="章节或帧输入 JSON")
    parser.add_argument("--output", help="输出 Markdown 路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    input_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
    data = load_json(input_path, {})
    result = checklist(
        data,
        load_json(CONFIG_DIR / "prompt_policy.json", {}),
        load_json(CONFIG_DIR / "character_lock_chen_nian_lie_gou.json", {}),
        load_json(CONFIG_DIR / "scene_lock_chen_nian_lie_gou.json", {}),
        load_json(CONFIG_DIR / "text_strategy.json", {}),
    )
    output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else markdown_report(result)
    if args.output:
        output_path = (ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
        print(f"已生成 QA 清单：{output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
