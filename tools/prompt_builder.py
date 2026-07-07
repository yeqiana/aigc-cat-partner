#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目级 Prompt Builder V3。

读取 prompt policy、人物锁定、场景锁定、文字策略和 v3 模板，输出可复制的合规 Prompt。
仅使用 Python 标准库。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
TEMPLATE_DIR = ROOT / "prompts" / "templates"


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def as_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def render_template(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def active_frame(data: dict[str, Any], frame_index: int) -> dict[str, Any]:
    frames = data.get("custom_frames")
    if isinstance(frames, list) and frames:
        index = max(1, min(frame_index, len(frames))) - 1
        frame = dict(frames[index])
        frame.setdefault("index", index + 1)
        return frame
    return {
        "index": frame_index,
        "scene": data.get("scene", ""),
        "action": data.get("action", ""),
        "focus": data.get("focus") or data.get("subject_state", ""),
        "previous_action": data.get("previous_action", ""),
        "next_action": data.get("next_action", ""),
        "visual_evidence": data.get("visual_evidence", []),
        "dialogue": data.get("character_lines", []),
        "narration": data.get("narration_text", ""),
        "title": data.get("title_text") or data.get("story_title", ""),
    }


def character_lock_text(character_lock: dict[str, Any], data: dict[str, Any]) -> str:
    characters = character_lock.get("characters", {})
    active_ids = data.get("character_ids")
    if not active_ids:
        active_ids = ["tao_huainan_child", "chi_ku_child", "tao_xiaodong_young"]
    lines = []
    lines.extend(character_lock.get("global_rules", []))
    for char_id in active_ids:
        char = characters.get(char_id)
        if not char:
            continue
        lines.append(f"{char.get('display_name', char_id)}｜{char.get('stage', '')}：{char.get('must', '')}")
        lines.extend(char.get("visual_rules", []))
        lines.extend(char.get("behavior_rules", []))
        lines.append("禁止：" + "；".join(char.get("forbidden", [])))
    return bullets(lines)


def style_lock_text(data: dict[str, Any], character_lock: dict[str, Any]) -> str:
    global_style = character_lock.get("global_style_lock", {})
    style_prompt = data.get("style_prompt") or global_style.get("style_prompt") or "温柔现实向日系绘本插画，低饱和电影感光影，真实中国北方生活场景。"
    render_rules = global_style.get("render_rules", [])
    return bullets([style_prompt, *render_rules])


def choose_scene(scene_lock: dict[str, Any], data: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    scene_name = frame.get("scene") or data.get("scene") or ""
    scenes = scene_lock.get("scenes", {})
    for scene in scenes.values():
        if scene.get("display_name") and scene.get("display_name") in scene_name:
            return scene
    for scene_id, scene in scenes.items():
        if scene_id in scene_name:
            return scene
    return next(iter(scenes.values()), {})


def scene_lock_text(scene_lock: dict[str, Any], data: dict[str, Any], frame: dict[str, Any]) -> str:
    scene = choose_scene(scene_lock, data, frame)
    lines = []
    lines.extend(scene_lock.get("global_rules", []))
    if scene:
        lines.append(f"{scene.get('display_name', '当前场景')}：{scene.get('space', '')}")
        lines.append(f"时间/天气：{scene.get('time', '')}；{scene.get('season_weather', '')}")
        lines.append("关键道具：" + "、".join(scene.get("props", [])))
        lines.append("感官细节：" + "、".join(scene.get("sensory_details", [])))
        lines.append("禁止：" + "；".join(scene.get("forbidden", [])))
    return bullets(lines)


def storyboard_rules_text(policy: dict[str, Any]) -> str:
    storyboard = policy.get("storyboard", {})
    lines = [
        f"{storyboard.get('ratio', '9:16')} {storyboard.get('platform', '抖音竖屏')}",
        f"{storyboard.get('panel_count', '2-3')} 个漫画分镜格，布局：{storyboard.get('layout', '主画面 + 特写小窗')}",
    ]
    lines.extend(storyboard.get("required_shots", []))
    lines.extend("禁止：" + item for item in storyboard.get("forbidden", []))
    return bullets(lines)


def text_strategy_text(text_strategy: dict[str, Any], data: dict[str, Any]) -> str:
    allow_text = data.get("allow_text_in_image") is True or str(data.get("allow_text_in_image")).lower() == "true"
    default = text_strategy.get("default", {})
    lines = list(text_strategy.get("rules", []))
    if allow_text:
        lines.insert(0, "本次显式开启 allow_text_in_image=true：只允许短文字直接入图，仍禁止姓名标签和章节/帧序号。")
    else:
        lines.insert(0, f"默认文字模式：{default.get('text_render_mode', '生成空白气泡 + 后期叠字图层')}")
    lines.append(f"人物姓名标注：{default.get('character_label_mode', '不标注')}")
    lines.append(f"对白姓名模式：{default.get('dialogue_name_mode', '气泡内不显示姓名')}")
    return bullets(lines)


def post_text_list(frame: dict[str, Any]) -> str:
    lines = []
    title = frame.get("title")
    narration = frame.get("narration")
    if title:
        lines.append(f"标题/配置名：{title}")
    if narration:
        lines.append(f"旁白：{narration}")
    for item in frame.get("dialogue") or frame.get("character_lines") or []:
        if isinstance(item, dict):
            name = str(item.get("name", "角色")).strip()
            text = str(item.get("text", "")).strip()
            if not text or set(text) == {"?"} or set(name) == {"?"}:
                continue
            lines.append(f"{name}：{text}")
    return bullets(lines) if lines else "- 无；画面只保留空白气泡或留白。"


def negative_prompt_text(policy: dict[str, Any], character_lock: dict[str, Any], scene_lock: dict[str, Any], text_strategy: dict[str, Any], data: dict[str, Any], frame: dict[str, Any]) -> str:
    items = []
    items.extend(policy.get("negative_prompt", []))
    for char in character_lock.get("characters", {}).values():
        items.extend(char.get("forbidden", []))
    scene = choose_scene(scene_lock, data, frame)
    items.extend(scene.get("forbidden", []))
    items.extend(text_strategy.get("forbidden_text", []))
    items.extend(as_lines(data.get("project_negative_prompt")))
    common = load_text(CONFIG_DIR / "negative_prompt_common.txt").strip()
    project = load_text(CONFIG_DIR / "negative_prompt_project.txt").strip()
    if common:
        items.append(common)
    if project:
        items.append(project)
    seen = set()
    result = []
    for item in items:
        item = str(item).strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return bullets(result)


def qa_checklist_text(policy: dict[str, Any]) -> str:
    return bullets(policy.get("acceptance", []))


def build_prompt(
    data: dict[str, Any],
    policy_path: Path,
    character_lock_path: Path,
    scene_lock_path: Path,
    text_strategy_path: Path,
    template_path: Path,
    frame_index: int,
) -> str:
    policy = load_json(policy_path, {})
    character_lock = load_json(character_lock_path, {})
    scene_lock = load_json(scene_lock_path, {})
    text_strategy = load_json(text_strategy_path, {})
    template = load_text(template_path)
    frame = active_frame(data, frame_index)
    values = {
        "character_lock": character_lock_text(character_lock, data),
        "style_lock": style_lock_text(data, character_lock),
        "scene_lock": scene_lock_text(scene_lock, data, frame),
        "project_name": str(data.get("project_name") or policy.get("project") or "陈年烈狗"),
        "story_title": str(data.get("story_title") or frame.get("title") or "未命名章节"),
        "frame_index": str(frame.get("index") or frame_index),
        "scene": str(frame.get("scene") or data.get("scene") or ""),
        "action": str(frame.get("action") or data.get("action") or ""),
        "focus": str(frame.get("focus") or frame.get("subject_focus") or data.get("subject_state") or ""),
        "previous_action": str(frame.get("previous_action") or ""),
        "next_action": str(frame.get("next_action") or ""),
        "visual_evidence": "、".join(as_lines(frame.get("visual_evidence"))) or "人物、动作、道具、场景都清晰可验收",
        "storyboard_rules": storyboard_rules_text(policy),
        "text_strategy": text_strategy_text(text_strategy, data),
        "post_text_list": post_text_list(frame),
        "negative_prompt": negative_prompt_text(policy, character_lock, scene_lock, text_strategy, data, frame),
        "qa_checklist": qa_checklist_text(policy),
    }
    return render_template(template, values).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="项目级 Prompt Builder V3")
    parser.add_argument("--input", required=True, help="章节或帧输入 JSON")
    parser.add_argument("--output", help="输出 Markdown 路径")
    parser.add_argument("--frame-index", type=int, default=1)
    parser.add_argument("--policy", default="config/prompt_policy.json")
    parser.add_argument("--character-lock", default="config/character_lock_chen_nian_lie_gou.json")
    parser.add_argument("--scene-lock", default="config/scene_lock_chen_nian_lie_gou.json")
    parser.add_argument("--text-strategy", default="config/text_strategy.json")
    parser.add_argument("--template", default="prompts/templates/frame_prompt_v3.template.md")
    args = parser.parse_args()

    input_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
    data = load_json(input_path, {})
    prompt = build_prompt(
        data,
        (ROOT / args.policy) if not Path(args.policy).is_absolute() else Path(args.policy),
        (ROOT / args.character_lock) if not Path(args.character_lock).is_absolute() else Path(args.character_lock),
        (ROOT / args.scene_lock) if not Path(args.scene_lock).is_absolute() else Path(args.scene_lock),
        (ROOT / args.text_strategy) if not Path(args.text_strategy).is_absolute() else Path(args.text_strategy),
        (ROOT / args.template) if not Path(args.template).is_absolute() else Path(args.template),
        args.frame_index,
    )
    if args.output:
        output_path = (ROOT / args.output) if not Path(args.output).is_absolute() else Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(prompt + "\n", encoding="utf-8")
        print(f"已生成 Prompt：{output_path}")
    else:
        print(prompt)


if __name__ == "__main__":
    main()
