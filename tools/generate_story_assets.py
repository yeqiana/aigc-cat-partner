#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate project-specific character prompts and chapter test inputs.

Examples:
  python tools/generate_story_assets.py character --character all
  python tools/generate_story_assets.py chapter --chapter 1 --run-pipeline
  python tools/generate_story_assets.py batch --start 1 --end 10 --run-pipeline
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = ROOT / "outputs" / "batch_plans"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_filename(text: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    for ch in bad:
        text = text.replace(ch, "_")
    return text.strip()[:80] or "item"


def load_character_spec() -> dict[str, Any]:
    return load_json(CONFIG_DIR / "character_spec.json")


def load_reference_manifest() -> dict[str, Any]:
    return load_json(CONFIG_DIR / "reference_manifest.json")


def load_chapter_plan() -> dict[str, Any]:
    return load_json(CONFIG_DIR / "chapter_scene_plan.json")


def character_reference_lines(character: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    refs = manifest.get("identity_references", {})
    lines = []
    for ref_id in character.get("reference_ids", []):
        ref = refs.get(ref_id)
        if ref:
            lines.append(f"- {ref_id}: {ref.get('path')}；用途：{ref.get('usage')}")
    return lines


def build_character_prompt(character_id: str, character: dict[str, Any], spec: dict[str, Any], manifest: dict[str, Any]) -> str:
    style_lock = spec.get("global_style_lock", {})
    forbidden = character.get("forbidden", [])
    reference_lines = character_reference_lines(character, manifest)
    if not reference_lines:
        reference_lines = ["- 暂无独立身份图；使用文字设定 + 统一画风参考。"]

    return f"""# 单角色身份参考 Prompt：{character.get('display_name', character_id)}

## 使用顺序
1. 上传或引用本角色的身份参考图。
2. 上传统一画风参考图。
3. 再发送本 Prompt。
4. 生成后只验收角色身份，不急着做章节场景。

## 参考图
{chr(10).join(reference_lines)}

## 角色锁定
- 角色ID：{character_id}
- 名称：{character.get('display_name', '')}
- 身份：{character.get('identity', character.get('role', ''))}
- 年龄线：{character.get('age_stage', '')}
- 脸部/体态：{character.get('face_or_shape', character.get('appearance', ''))}
- 发型/头部：{character.get('hair_or_head_features', '')}
- 服装/标志物：{character.get('outfit_or_marker', character.get('marker', ''))}
- 表情：{character.get('expression', character.get('state', ''))}
- 姿态：{character.get('body_or_posture', '')}
- 气质：{character.get('temperament', '')}

## 画风锁定
{style_lock.get('style_prompt', '')}

## 生成目标
生成一张 9:16 单角色身份参考图。角色全身或半身清晰可见，背景保持简洁、低干扰，不要加入复杂剧情动作。重点验证年龄感、脸部气质、服装轮廓和角色标志物。

## 禁止项
{chr(10).join(f'- {item}' for item in forbidden)}
{chr(10).join(f'- {item}' for item in style_lock.get('render_rules', []))}
""".strip()


def build_visual_gene_summary(character_ids: list[str], spec: dict[str, Any]) -> str:
    characters = spec.get("characters", {})
    parts = []
    for character_id in character_ids:
        character = characters.get(character_id)
        if not character:
            continue
        name = character.get("display_name", character_id)
        identity = character.get("identity", character.get("role", ""))
        face = character.get("face_or_shape", character.get("appearance", ""))
        marker = character.get("outfit_or_marker", character.get("marker", ""))
        forbidden = "；".join(character.get("forbidden", [])[:3])
        parts.append(f"{name}：{identity}；视觉：{face}；标志：{marker}；禁止：{forbidden}")
    return "\n".join(parts)


def build_identity_references(character_ids: list[str], spec: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    characters = spec.get("characters", {})
    refs = manifest.get("identity_references", {})
    result = []
    for character_id in character_ids:
        character = characters.get(character_id, {})
        for ref_id in character.get("reference_ids", []):
            ref = refs.get(ref_id)
            if ref:
                result.append(f"{character.get('display_name', character_id)}身份参考：{ref.get('path')}")
    style_ref = manifest.get("locked_master_policy", {}).get("style_master_reference")
    if style_ref:
        result.append(f"统一画风参考：{style_ref}")
    return result


def scene_reference_for_chapter(chapter: dict[str, Any], manifest: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    scene_refs = manifest.get("scene_master_references", {})
    chapter_no = chapter_number_from_source(chapter.get("source_file", ""))
    ref_id = None
    if chapter_no and 1 <= chapter_no <= 3:
        ref_id = "rural_funeral_winter"
    elif chapter_no and 4 <= chapter_no <= 6:
        ref_id = "city_home_winter_spring"
    elif chapter_no and 7 <= chapter_no <= 10:
        ref_id = "blind_school_childhood"
    return ref_id, scene_refs.get(ref_id or "", {})


def build_scene_references(chapter: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    ref_id, ref = scene_reference_for_chapter(chapter, manifest)
    if ref_id and ref.get("path"):
        return [f"场景母版参考：{ref.get('path')}；用途：{ref.get('usage')}"]
    return ["场景母版参考：暂无独立图片；使用章节场景设定文字。"]


def build_worldview_summary(chapter: dict[str, Any], manifest: dict[str, Any]) -> str:
    ref_id, ref = scene_reference_for_chapter(chapter, manifest)
    if ref_id and ref:
        scene_lock = f"{ref_id}: {ref.get('usage')}；母版：{ref.get('path', '暂无图片')}"
    else:
        scene_lock = "按章节场景设定执行，优先使用00_设定文档中的环境氛围。"
    return f"""章节时间：{chapter.get('period', '')}
主场景：{chapter.get('scene', '')}
场景锁定：{scene_lock}
生活质感：2000年代中国北方生活环境，真实室内外空间，重视温度、触觉、声音、气味等可视化线索。
安全边界：儿童角色不做成人化表达；暴力和伤害只做克制暗示，重点表现保护、陪伴和情绪变化。""".strip()


def chapter_number_from_source(source_file: str) -> int | None:
    match = re.search(r"第(\d+)章", source_file or "")
    return int(match.group(1)) if match else None


def short_text(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    return text[:max_chars]


def enriched_frames(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    frames = []
    for frame in chapter.get("custom_frames", []):
        item = dict(frame)
        item.setdefault("title", short_text(item.get("action", item.get("phase", "章节分镜")), 14))
        item.setdefault("narration", short_text(item.get("state", item.get("action", "")), 18))
        frames.append(item)
    return frames


def chapter_input(chapter_no: int, image_count: int | None = None) -> dict[str, Any]:
    spec = load_character_spec()
    manifest = load_reference_manifest()
    plan = load_chapter_plan()
    chapter = plan.get("chapters", {}).get(str(chapter_no))
    if not chapter:
        raise SystemExit(f"未配置章节：第{chapter_no}章")

    data = dict(plan.get("defaults", {}))
    if image_count:
        data["image_count"] = image_count

    character_ids = list(chapter.get("characters", []))
    frames = enriched_frames(chapter)
    data.update(
        {
            "project_name": plan.get("project_name", "陈年烈狗"),
            "preset_name": "陈年烈狗·前10章测试",
            "story_id": f"chen_nian_lie_gou_chapter_{chapter_no:03d}",
            "source_file": chapter.get("source_file", ""),
            "story_title": f"第{chapter_no}章｜{chapter.get('story_title', '')}",
            "story_outline": chapter.get("story_outline", ""),
            "emotional_progression": chapter.get("emotional_progression", ""),
            "scene": chapter.get("scene", ""),
            "action": frames[0].get("action", "") if frames else "",
            "style_prompt": spec.get("global_style_lock", {}).get("style_prompt", ""),
            "visual_gene_summary": build_visual_gene_summary(character_ids, spec),
            "worldview_summary": build_worldview_summary(chapter, manifest),
            "key_props": chapter.get("key_props", []),
            "subject_state": frames[0].get("state", "") if frames else "",
            "mood_curve": chapter.get("mood_curve", []),
            "custom_frames": frames,
            "identity_references": build_identity_references(character_ids, spec, manifest),
            "scene_references": build_scene_references(chapter, manifest),
            "character_lines": [
                {"name": "旁白", "text": "这一幕开始了"},
                {"name": "陶淮南", "text": "你在哪儿"},
                {"name": "迟苦", "text": "别怕"}
            ],
            "extra": (
                f"原文来源：{chapter.get('source_file')}。本任务是章节视觉改编分镜，只使用摘要情节和设定，不逐字搬运原文。"
                " 每张图只推进一个明确动作，优先保证人物年龄线、盲人动作逻辑、场景年代感和连续性。"
            ),
            "project_negative_prompt": plan.get("common_negative_prompt", ""),
        }
    )
    return data


def write_character_prompts(character_id: str) -> list[Path]:
    spec = load_character_spec()
    manifest = load_reference_manifest()
    characters = spec.get("characters", {})
    ids = sorted(characters) if character_id == "all" else [character_id]
    written = []
    for cid in ids:
        character = characters.get(cid)
        if not character:
            raise SystemExit(f"未找到角色：{cid}")
        prompt = build_character_prompt(cid, character, spec, manifest)
        out = PROMPTS_DIR / "character" / f"{safe_filename(cid)}.md"
        write_text(out, prompt + "\n")
        written.append(out)
    return written


def write_chapter_input(chapter_no: int, image_count: int | None = None) -> Path:
    data = chapter_input(chapter_no, image_count=image_count)
    out = PROMPTS_DIR / "chapter" / f"chapter_{chapter_no:03d}.input.json"
    write_json(out, data)
    return out


def run_generate_prompt(input_path: Path) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "generate_prompt.py"), "--input", str(input_path)],
        cwd=ROOT,
        check=True,
    )


def write_batch(start: int, end: int, image_count: int | None = None, run_pipeline: bool = False) -> list[Path]:
    written = []
    tasks = []
    for chapter_no in range(start, end + 1):
        path = write_chapter_input(chapter_no, image_count=image_count)
        written.append(path)
        tasks.append(chapter_input(chapter_no, image_count=image_count))
        if run_pipeline:
            run_generate_prompt(path)
    batch_path = PROMPTS_DIR / "batch" / f"chapters_{start:03d}_{end:03d}.batch_plan.json"
    write_json(batch_path, {"batch_name": f"陈年烈狗第{start}章到第{end}章测试任务", "tasks": tasks})
    written.append(batch_path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="陈年烈狗角色与章节测试 Prompt 生成工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_character = sub.add_parser("character", help="生成单角色身份参考 prompt")
    p_character.add_argument("--character", default="all", help="角色ID，或 all")

    p_chapter = sub.add_parser("chapter", help="生成单章章节场景 prompt 输入")
    p_chapter.add_argument("--chapter", type=int, required=True, help="章节号")
    p_chapter.add_argument("--image-count", type=int, default=None, help="覆盖每章生成张数")
    p_chapter.add_argument("--run-pipeline", action="store_true", help="同时调用 generate_prompt.py 生成 V2 产物")

    p_batch = sub.add_parser("batch", help="批量生成章节测试输入")
    p_batch.add_argument("--start", type=int, required=True, help="起始章节")
    p_batch.add_argument("--end", type=int, required=True, help="结束章节")
    p_batch.add_argument("--image-count", type=int, default=None, help="覆盖每章生成张数")
    p_batch.add_argument("--run-pipeline", action="store_true", help="同时逐章调用 generate_prompt.py 生成 V2 产物")

    args = parser.parse_args()

    if args.command == "character":
        paths = write_character_prompts(args.character)
    elif args.command == "chapter":
        path = write_chapter_input(args.chapter, image_count=args.image_count)
        paths = [path]
        if args.run_pipeline:
            run_generate_prompt(path)
    else:
        if args.end < args.start:
            raise SystemExit("--end 不能小于 --start")
        paths = write_batch(args.start, args.end, image_count=args.image_count, run_pipeline=args.run_pipeline)

    print("已生成：")
    for path in paths:
        print(path)
    if args.command in {"chapter", "batch"} and getattr(args, "run_pipeline", False):
        print(f"V2 产物目录：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
