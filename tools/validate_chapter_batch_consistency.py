#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate chapter batch inputs before running full-book image generation.

This is a read-only gate for the first 10 chapter test batch. It does not call
the prompt generator and does not change public CLI contracts.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHAPTER_DIR = ROOT / "prompts" / "chapter"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "validation"

GENERATOR_FILES = [
    ROOT / "tools" / "generate_prompt.py",
    ROOT / "tools" / "prompt_builder.py",
    ROOT / "tools" / "generate_batch_plan.py",
]

REQUIRED_TOP_LEVEL_FIELDS = [
    "story_id",
    "story_title",
    "scene",
    "image_count",
    "continuous_story",
    "story_template",
    "visual_gene_summary",
    "worldview_summary",
    "style_prompt",
    "custom_frames",
    "project_negative_prompt",
]

REQUIRED_FRAME_FIELDS = [
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def effective_visual_evidence(frame: dict[str, Any]) -> list[str]:
    evidence = frame.get("visual_evidence")
    result = [str(x).strip() for x in evidence if str(x).strip()] if isinstance(evidence, list) else []
    for key in ["scene_detail", "action_momentum_detail", "focus", "panel_composition"]:
        value = str(frame.get(key) or "").strip()
        if value and value not in result:
            result.append(value)
        if len(result) >= 4:
            break
    return result[:4]


def issue(severity: str, area: str, message: str, detail: str = "") -> dict[str, str]:
    return {
        "severity": severity,
        "area": area,
        "message": message,
        "detail": detail,
    }


def chapter_number_from_task(task: dict[str, Any], fallback: int | None = None) -> int | None:
    candidates = [task.get("story_id"), task.get("source_file"), task.get("story_title")]
    for value in candidates:
        match = re.search(r"chapter_(\d{3})", str(value or ""))
        if match:
            return int(match.group(1))
        match = re.search(r"第(\d+)章", str(value or ""))
        if match:
            return int(match.group(1))
    return fallback


def frame_score(frames: Any) -> int:
    if not isinstance(frames, list):
        return 0
    keys = REQUIRED_FRAME_FIELDS
    return sum(1 for frame in frames if isinstance(frame, dict) for key in keys if not is_blank(frame.get(key)))


def hydrate_from_chapter_input(task: dict[str, Any], chapter: int) -> dict[str, Any]:
    chapter_path = DEFAULT_CHAPTER_DIR / f"chapter_{chapter:03d}.input.json"
    if not chapter_path.exists():
        return task
    chapter_data = load_json(chapter_path)
    merged = dict(chapter_data)
    for key, value in task.items():
        if not is_blank(value):
            merged[key] = value
    if frame_score(chapter_data.get("custom_frames")) > frame_score(task.get("custom_frames")):
        merged["custom_frames"] = chapter_data.get("custom_frames")
        merged["image_count"] = chapter_data.get("image_count", merged.get("image_count"))
    return merged


def chapter_inputs_from_dir(chapter_dir: Path, start: int, end: int) -> list[tuple[int, Path, dict[str, Any]]]:
    result = []
    for chapter in range(start, end + 1):
        path = chapter_dir / f"chapter_{chapter:03d}.input.json"
        if path.exists():
            result.append((chapter, path, load_json(path)))
        else:
            result.append((chapter, path, {}))
    return result


def chapter_inputs_from_batch(batch_path: Path) -> list[tuple[int, Path, dict[str, Any]]]:
    plan = load_json(batch_path)
    result = []
    for idx, task in enumerate(plan.get("tasks", []), 1):
        chapter = chapter_number_from_task(task, idx) or idx
        result.append((chapter, batch_path, hydrate_from_chapter_input(task, chapter)))
    return result


def source_mentions(name: str) -> list[str]:
    hits = []
    for path in GENERATOR_FILES:
        if path.exists() and name in path.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def runtime_analysis() -> list[dict[str, str]]:
    issues = []
    if not source_mentions("character_lock_chen_nian_lie_gou"):
        issues.append(issue("FAIL", "runtime", "生成入口未读取 character_lock 配置"))
    if not source_mentions("scene_lock_chen_nian_lie_gou"):
        issues.append(issue("FAIL", "runtime", "生成入口未读取 scene_lock 配置"))
    if not source_mentions("text_strategy"):
        issues.append(issue("FAIL", "runtime", "生成入口未读取 text_strategy 配置"))
    if not source_mentions("reference_manifest"):
        issues.append(
            issue(
                "FAIL",
                "runtime",
                "reference_manifest 当前不会被生成入口直接读取",
                "如章节输入没有 identity_references/scene_references，清单里的参考图不会自动进入 prompt_plan。",
            )
        )
    if not source_mentions("character_spec"):
        issues.append(
            issue(
                "FAIL",
                "runtime",
                "character_spec 当前不会被生成入口直接读取",
                "角色形象锁定主要来自 character_lock 与章节 visual_gene_summary，不来自 character_spec。",
            )
        )
    return issues


def validate_manifest_links() -> list[dict[str, str]]:
    issues = []
    character_lock_path = ROOT / "config" / "character_lock_chen_nian_lie_gou.json"
    manifest_path = ROOT / "config" / "reference_manifest.json"
    if not character_lock_path.exists() or not manifest_path.exists():
        return [issue("FAIL", "references", "缺少 character_lock 或 reference_manifest 配置文件")]

    character_lock = load_json(character_lock_path)
    manifest = load_json(manifest_path)
    manifest_ids = set((manifest.get("identity_references") or {}).keys())
    for char_id, char in (character_lock.get("characters") or {}).items():
        for ref_id in char.get("reference_ids") or []:
            if ref_id not in manifest_ids:
                issues.append(
                    issue(
                        "FAIL",
                        "references",
                        f"角色 {char_id} 的 reference_id 不在 reference_manifest 中",
                        ref_id,
                    )
                )

    for section in ["identity_references", "scene_master_references"]:
        for ref_id, ref in (manifest.get(section) or {}).items():
            raw_path = ref.get("path")
            if raw_path and not (ROOT / raw_path).exists():
                issues.append(
                    issue(
                        "WARN",
                        "references",
                        f"{section}.{ref_id} 的图片路径当前无法在仓库中解析",
                        raw_path,
                    )
                )
    return issues


def validate_chapter(
    chapter: int,
    path: Path,
    task: dict[str, Any],
    global_runtime_issues: list[dict[str, str]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not task:
        return [issue("FAIL", "input", "章节输入文件不存在", str(path))]

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if is_blank(task.get(field)):
            issues.append(issue("FAIL", "input", f"缺少顶层字段：{field}"))

    story_id = str(task.get("story_id") or "")
    expected_story_id = f"chapter_{chapter:03d}"
    if expected_story_id not in story_id:
        issues.append(issue("WARN", "input", "story_id 与章节编号不一致", f"expected contains {expected_story_id}, got {story_id}"))

    frames = task.get("custom_frames")
    image_count = task.get("image_count")
    if isinstance(frames, list):
        if isinstance(image_count, int) and image_count != len(frames):
            issues.append(issue("FAIL", "storyboard", "image_count 与 custom_frames 数量不一致", f"image_count={image_count}, frames={len(frames)}"))
        for idx, frame in enumerate(frames, 1):
            if not isinstance(frame, dict):
                issues.append(issue("FAIL", "storyboard", f"第 {idx} 帧不是对象"))
                continue
            missing = [field for field in REQUIRED_FRAME_FIELDS if is_blank(frame.get(field))]
            if missing:
                issues.append(issue("FAIL", "storyboard", f"第 {idx} 帧分镜输入缺项", ", ".join(missing)))
            raw_evidence = frame.get("visual_evidence")
            raw_count = len([x for x in raw_evidence if str(x).strip()]) if isinstance(raw_evidence, list) else 0
            if len(effective_visual_evidence(frame)) < 3:
                issues.append(issue("FAIL", "storyboard", f"第 {idx} 帧有效视觉证据少于 3 项"))
            elif raw_count < 3:
                issues.append(
                    issue(
                        "WARN",
                        "storyboard",
                        f"第 {idx} 帧 visual_evidence 原始项少于 3 项，运行时会用分镜细节兜底",
                    )
                )
    else:
        issues.append(issue("FAIL", "storyboard", "custom_frames 不是数组，无法做逐帧验收"))

    if is_blank(task.get("identity_references")):
        issues.append(
            issue(
                "FAIL",
                "references",
                "章节输入未显式提供 identity_references",
                "现有 required_references_for_frame 只读章节输入字段，不会自动展开 reference_manifest。",
            )
        )
    if is_blank(task.get("scene_references")):
        issues.append(
            issue(
                "FAIL",
                "references",
                "章节输入未显式提供 scene_references",
                "现有 required_references_for_frame 只读章节输入字段，不会自动展开 reference_manifest。",
            )
        )

    if is_blank(task.get("character_ids")):
        issues.append(
            issue(
                "WARN",
                "character_lock",
                "未显式提供 character_ids，生成器会默认注入三名主角色锁定",
                "默认包含 tao_huainan_child、chi_ku_child、tao_xiaodong_young；如某章不出场，可能造成提示词噪声。",
            )
        )

    if any(item["message"].startswith("character_spec 当前不会") for item in global_runtime_issues):
        issues.append(issue("FAIL", "character_lock", "character_spec 引用不会在本章运行时生效"))
    if any(item["message"].startswith("reference_manifest 当前不会") for item in global_runtime_issues):
        issues.append(issue("FAIL", "references", "reference_manifest 引用不会在本章运行时自动生效"))

    text_render_mode = str(task.get("text_render_mode") or "")
    allow_text = task.get("allow_text_in_image") is True
    if not allow_text and ("直接" in text_render_mode or "鐩存帴" in text_render_mode):
        issues.append(
            issue(
                "WARN",
                "text_strategy",
                "章节输入残留直接入图文字配置，但 allow_text_in_image 未开启",
                "generate_prompt.apply_policy_defaults 会用 text_strategy 默认值覆盖为后期叠字。",
            )
        )

    return issues


def summarize(chapter_results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"chapters": len(chapter_results), "FAIL": 0, "WARN": 0, "PASS": 0}
    for item in chapter_results:
        severities = [issue["severity"] for issue in item["issues"]]
        summary["FAIL"] += severities.count("FAIL")
        summary["WARN"] += severities.count("WARN")
        if not severities:
            summary["PASS"] += 1
    return summary


def render_markdown(global_issues: list[dict[str, str]], chapter_results: list[dict[str, Any]]) -> str:
    summary = summarize(chapter_results)
    lines = [
        "# 前10章批量生成一致性验收报告",
        "",
        f"- 章节数：{summary['chapters']}",
        f"- FAIL：{summary['FAIL']}",
        f"- WARN：{summary['WARN']}",
        f"- 无失败章节：{summary['PASS']}",
        "",
        "## 全局入口判断",
    ]
    if global_issues:
        for item in global_issues:
            detail = f"；{item['detail']}" if item.get("detail") else ""
            lines.append(f"- [{item['severity']}] {item['area']}：{item['message']}{detail}")
    else:
        lines.append("- [PASS] 生成入口关键配置读取关系未发现明显问题。")

    lines.extend(["", "## 按章节失败报告"])
    for result in chapter_results:
        issues = result["issues"]
        status = "FAIL" if any(item["severity"] == "FAIL" for item in issues) else ("WARN" if issues else "PASS")
        lines.append("")
        lines.append(f"### 第 {result['chapter']:03d} 章｜{status}")
        lines.append(f"- 输入：`{result['path']}`")
        if not issues:
            lines.append("- 未发现结构性失败。")
            continue
        for item in issues:
            detail = f"；{item['detail']}" if item.get("detail") else ""
            lines.append(f"- [{item['severity']}] {item['area']}：{item['message']}{detail}")
    lines.append("")
    lines.append("## 结论")
    if summary["FAIL"]:
        lines.append("当前不建议直接扩展到全书 126 章；应先处理 FAIL 项，再复跑本验收器。")
    else:
        lines.append("当前结构性验收未发现 FAIL，可进入小规模真实出图抽检。")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate chapter batch consistency before full-book generation.")
    parser.add_argument("--batch", help="Batch plan JSON. If omitted, checks prompts/chapter/chapter_001-010.input.json.")
    parser.add_argument("--chapter-dir", default=str(DEFAULT_CHAPTER_DIR), help="Chapter input directory.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=10)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.is_absolute():
            batch_path = ROOT / batch_path
        chapter_inputs = chapter_inputs_from_batch(batch_path)
    else:
        chapter_dir = Path(args.chapter_dir)
        if not chapter_dir.is_absolute():
            chapter_dir = ROOT / chapter_dir
        chapter_inputs = chapter_inputs_from_dir(chapter_dir, args.start, args.end)

    runtime_issues = runtime_analysis()
    global_issues = runtime_issues + validate_manifest_links()
    chapter_results = []
    for chapter, path, task in chapter_inputs:
        rel_path = str(path.relative_to(ROOT)) if path.exists() or path.is_absolute() else str(path)
        chapter_results.append(
            {
                "chapter": chapter,
                "path": rel_path,
                "issues": validate_chapter(chapter, path, task, runtime_issues),
            }
        )

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    markdown_path = out_dir / f"chapter_001_010_consistency_{stamp}.md"
    json_path = out_dir / f"chapter_001_010_consistency_{stamp}.json"

    payload = {
        "summary": summarize(chapter_results),
        "global_issues": global_issues,
        "chapters": chapter_results,
    }
    markdown_path.write_text(render_markdown(global_issues, chapter_results), encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = payload["summary"]
    print(f"Report: {markdown_path}")
    print(f"JSON: {json_path}")
    print(f"Chapters={summary['chapters']} FAIL={summary['FAIL']} WARN={summary['WARN']} PASS={summary['PASS']}")
    raise SystemExit(1 if summary["FAIL"] else 0)


if __name__ == "__main__":
    main()
