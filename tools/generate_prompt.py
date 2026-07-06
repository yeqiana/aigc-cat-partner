#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用剧情连载 Prompt 生成入口 V2.0

核心目标：
1. 输出 story/frame/copy/prompt/qa/retake 六类结构化产物。
2. 保留第 1 张锚点图、第 2 张续图、第 3-N 张续图的引用规则。
3. 不绑定具体 IP；角色、世界观、画风和项目禁忌全部由输入或配置提供。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "outputs" / "batch_plans"

BUBBLE_MODES = ["无", "单角色气泡", "多角色气泡", "旁白标题"]
TEXT_MODES = ["无文字", "直接生成文字", "空白气泡后期加字"]
TEXT_RENDER_MODES = [
    "仅生成文案清单",
    "生成空白气泡 + 文案清单",
    "生成空白气泡 + 后期叠字图层",
    "直接在图中生成文字",
]
TEXT_POSITIONS = ["自动", "顶部标题区", "主体旁边", "底部字幕区"]
COPYWRITING_MODES = ["手动填写", "自动根据情节生成"]
INTERACTION_MODES = ["不互动", "看向观众", "提问互动", "评论引导", "点赞关注", "选择投票"]
CONTINUOUS_STORY_VALUES = ["否", "是"]
STORY_COHERENCE_VALUES = ["普通", "强"]
OUTFIT_STYLE_LOCKS = ["不锁定", "弱锁定", "强锁定"]
OUTFIT_REFERENCES = ["文字描述", "身份参考图", "第一张锚点图", "当前故事模板默认造型", "第一张锚点图 + 身份参考图"]
IN_IMAGE_STORYBOARD_VALUES = ["关闭", "开启"]
STORYBOARD_VIEWS = ["第一人称", "第三人称", "第一人称 + 第三人称"]
STORYBOARD_LAYOUTS = ["上下分镜", "左右分镜", "主画面 + 小视角窗口"]
QA_FAILURE_TYPES = ["剧情动作", "角色一致性", "世界观一致性", "造型道具连续性", "气泡可用性", "文案完整性", "镜头构图", "平台适配"]


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8").strip()


def safe_filename(text: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    for ch in bad:
        text = text.replace(ch, "_")
    return text.strip()[:80] or "task"


def short_text(text: str, max_chars: int = 16) -> str:
    return (text or "").strip()[:max_chars]


def clamp_count(value: Any) -> int:
    try:
        n = int(value)
    except Exception:
        n = 1
    return max(1, min(12, n))


def to_bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    value = str(value or "否").strip()
    return "是" if value in ["是", "true", "True", "1", "yes", "YES"] else "否"


def normalize_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    return [text] if text else []


def load_schema() -> dict:
    return load_json(CONFIG_DIR / "series_input_schema.json", default={}) or {}


def load_templates() -> dict:
    return load_json(CONFIG_DIR / "story_templates.json", default={}) or {}


def first_template_name(templates: dict) -> str:
    return next(iter(templates.keys()), "通用悬念连载")


def validate_input(raw_data: dict, source_name: str = "输入 JSON") -> list[str]:
    schema = load_schema()
    required = schema.get("required", ["scene", "image_count", "continuous_story", "story_template"])
    missing = [field for field in required if raw_data.get(field) in [None, ""]]
    errors = [f"{source_name} 缺少必填字段：{', '.join(missing)}"] if missing else []
    if "image_count" in raw_data:
        try:
            count = int(raw_data["image_count"])
            if count < 1 or count > 12:
                errors.append("image_count 必须在 1 到 12 之间")
        except Exception:
            errors.append("image_count 必须是整数")
    if raw_data.get("continuous_story") not in [None, "", "是", "否", True, False, "true", "false", "True", "False", "1", "0"]:
        errors.append("continuous_story 必须是 是/否 或布尔值")
    return errors


def normalize_defaults(data: dict) -> dict:
    schema = load_schema()
    defaults = schema.get("defaults", {})
    data = dict(data)
    for key, value in defaults.items():
        data.setdefault(key, value)
    data.setdefault("project_name", "通用剧情连载")
    data.setdefault("preset_name", "")
    data.setdefault("story_outline", "")
    data.setdefault("emotional_progression", "")
    data.setdefault("scene", "异常开场")
    data.setdefault("action", "")
    data.setdefault("angle", "")
    data.setdefault("style_prompt", "")
    data.setdefault("visual_gene_summary", "")
    data.setdefault("worldview_summary", "")
    data.setdefault("subject_state", "")
    data.setdefault("extra", "")
    data.setdefault("identity_lock", "强锁定")
    data.setdefault("bubble_mode", "多角色气泡")
    data.setdefault("text_mode", "空白气泡后期加字")
    data.setdefault("text_position", "自动")
    data.setdefault("copywriting_mode", "自动根据情节生成")
    data.setdefault("interaction_mode", "评论引导")
    data.setdefault("story_coherence", "强")
    data.setdefault("outfit_style_lock", "强锁定" if to_bool_text(data.get("continuous_story", "否")) == "是" else "弱锁定")
    data.setdefault("outfit_reference", "第一张锚点图 + 身份参考图" if to_bool_text(data.get("continuous_story", "否")) == "是" else "文字描述")
    data.setdefault("storyboard_view", "第三人称")
    data.setdefault("storyboard_layout", "主画面 + 小视角窗口")
    data["image_count"] = clamp_count(data.get("image_count", 1))
    data["continuous_story"] = to_bool_text(data.get("continuous_story", "否"))
    if data.get("ratio") == "9:16" and data.get("platform") == "通用":
        data["platform"] = "抖音竖屏"
    if data["image_count"] > 1 and data.get("output_mode") == "多镜头拼图":
        data["output_mode"] = "单张大图"
    if data.get("in_image_storyboard") != "开启":
        data["in_image_storyboard"] = "关闭"
    return data


def choose_story_template(data: dict) -> str:
    templates = load_templates()
    tpl = data.get("story_template") or first_template_name(templates)
    if tpl == "自动判断":
        return first_template_name(templates)
    if tpl in templates:
        return tpl
    return first_template_name(templates)


def template_frames(data: dict) -> list[dict]:
    custom_frames = data.get("custom_frames")
    if isinstance(custom_frames, list) and custom_frames:
        return [dict(frame) for frame in custom_frames]
    templates = load_templates()
    tpl = choose_story_template(data)
    frames = templates.get(tpl, {}).get("frames") or []
    if frames:
        return [dict(frame) for frame in frames]
    return [
        {
            "scene": data.get("scene") or "单张图",
            "phase": "第1幕",
            "action": data.get("action") or "按故事情节推进一个明确动作",
            "state": data.get("subject_state") or "单张图无需剧情推进。",
            "visual_evidence": ["主体清晰", "动作清楚", "环境符合世界观", "画面预留文字安全区"],
            "camera": data.get("angle") or "第三人称中景",
        }
    ]


def frame_plan(data: dict) -> list[dict]:
    data = normalize_defaults(data)
    count = clamp_count(data.get("image_count", 1))
    continuous = to_bool_text(data.get("continuous_story", "否"))
    base = template_frames(data)
    frames = []
    if count <= 1:
        src = dict(base[0])
        src.update({
            "index": 1,
            "total": 1,
            "scene": data.get("scene") or src.get("scene") or "单张图",
            "story_phase": "单张图",
            "state": data.get("subject_state") or src.get("state") or "单张图无需剧情推进。",
        })
        return [src]
    if continuous == "是":
        tpl = choose_story_template(data)
        for i in range(count):
            src = dict(base[i % len(base)])
            src["index"] = i + 1
            src["total"] = count
            src["story_template"] = tpl
            src["scene"] = src.get("scene") or data.get("scene") or f"第{i + 1}幕"
            src["story_phase"] = src.get("phase") or f"第{i + 1}幕"
            src["prev_phase"] = "无，故事开场" if i == 0 else frames[i - 1]["story_phase"]
            src["next_hint"] = (base[(i + 1) % len(base)].get("phase") or f"第{i + 2}幕") if i + 1 < count else "故事收束"
            src["state"] = src.get("state") or "承接上一张，推进当前动作。"
            frames.append(src)
        return frames
    angles = ["正面中景", "前方45度中景", "侧面中景", "近景半身", "背面45度", "低角度中景"]
    for i in range(count):
        frames.append(
            {
                "index": i + 1,
                "total": count,
                "scene": data.get("scene") or "同主题变体",
                "camera": angles[i % len(angles)],
                "action": data.get("action") or "保持同主题小变化",
                "story_phase": "同主题变体",
                "state": "保持同主题，不强制剧情推进。",
                "visual_evidence": ["主体清晰", "动作清楚", "风格一致", "安全留白"],
            }
        )
    return frames


def mood_curve_for(data: dict, count: int) -> list[str]:
    templates = load_templates()
    tpl = choose_story_template(data)
    mood_curve = list(data.get("mood_curve") or templates.get(tpl, {}).get("mood_curve") or ["平静", "推进", "收束"])
    if not mood_curve:
        mood_curve = ["平静"]
    if len(mood_curve) < count:
        mood_curve.extend([mood_curve[-1]] * (count - len(mood_curve)))
    return mood_curve[:count]


def build_story_plan(data: dict) -> dict:
    count = clamp_count(data.get("image_count", 1))
    tpl = choose_story_template(data)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "story_id": data.get("story_id") or f"series_{now}",
        "story_title": data.get("story_title") or "未命名剧情连载",
        "project_name": data.get("project_name") or "通用剧情连载",
        "platform": data.get("platform") or "抖音竖屏",
        "ratio": data.get("ratio") or "9:16",
        "image_count": count,
        "continuous_story": to_bool_text(data.get("continuous_story", "否")) == "是",
        "story_template": tpl,
        "story_outline": data.get("story_outline") or "",
        "emotional_progression": data.get("emotional_progression") or "",
        "mood_curve": mood_curve_for(data, count),
        "anchor_frame_index": 1,
        "text_render_mode": data.get("text_render_mode") or "生成空白气泡 + 后期叠字图层",
    }


def visual_evidence_for_frame(frame: dict) -> list[str]:
    evidence = frame.get("visual_evidence")
    if isinstance(evidence, list) and evidence:
        return [str(x) for x in evidence[:4]]
    return ["主体清晰", "动作清楚", "关键道具可识别", "画面预留文字安全区"]


def subject_state_for_frame(data: dict, frame: dict) -> str:
    return frame.get("state") or data.get("subject_state") or "主体状态承接上一张，身份、造型、关键道具和世界观保持一致。"


def build_frame_plan(data: dict, frames: list[dict]) -> list[dict]:
    story = build_story_plan(data)
    result = []
    for frame in frames:
        idx = frame.get("index", 1)
        role = "anchor" if idx == story["anchor_frame_index"] else ("continuation" if story["continuous_story"] else "variant")
        if idx == 1:
            continuity = "首张锚点图，无上一张"
        elif story["continuous_story"]:
            continuity = f"承接第 {idx - 1} 张成图，保持角色、造型、风格、世界观和关键道具连续"
        else:
            continuity = "非连续同主题变体，不强制引用上一张成图"
        result.append(
            {
                "frame_index": idx,
                "main_action": frame.get("action") or data.get("action") or "推进一个明确动作",
                "continuity_from_previous": continuity,
                "visual_evidence": visual_evidence_for_frame(frame),
                "character_emotion": story["mood_curve"][idx - 1] if idx - 1 < len(story["mood_curve"]) else "自然",
                "subject_state": subject_state_for_frame(data, frame),
                "camera": frame.get("camera") or frame.get("angle") or data.get("angle") or "第三人称中景",
                "in_image_storyboard": data.get("in_image_storyboard") == "开启",
                "role": role,
                "source_scene": frame.get("scene") or data.get("scene"),
            }
        )
    return result


def default_character_lines(data: dict, frame: dict) -> list[dict]:
    title = frame.get("story_phase") or f"第{frame.get('index', 1)}幕"
    frame_lines = frame.get("dialogue") or frame.get("character_lines")
    if frame_lines:
        lines = []
        for item in frame_lines:
            if isinstance(item, dict):
                lines.append({"name": short_text(item.get("name", "角色"), 8), "text": short_text(item.get("text", ""), 16)})
        if lines:
            return lines[:3]
    if data.get("character_lines"):
        lines = []
        for item in data.get("character_lines", []):
            if isinstance(item, dict):
                lines.append({"name": short_text(item.get("name", "角色"), 8), "text": short_text(item.get("text", ""), 16)})
        if lines:
            return lines[:3]
    return [
        {"name": "角色A", "text": short_text("先看看情况", 16)},
        {"name": "角色B", "text": short_text("事情不太对", 16)},
    ] if data.get("bubble_mode") == "多角色气泡" else [{"name": "主角", "text": short_text(title, 16)}]


def copy_for_frame(data: dict, frame: dict) -> dict:
    manual_title = short_text(data.get("title_text"), 16)
    manual_narration = short_text(data.get("narration_text"), 18)
    title = manual_title or short_text(frame.get("title") or frame.get("story_phase") or "剧情继续", 16)
    narration = manual_narration or short_text(frame.get("narration") or f"{title}继续推进", 18)
    return {
        "title": title,
        "narration": narration,
        "character_lines": default_character_lines(data, frame),
    }


def build_copy_plan(data: dict, frames: list[dict]) -> list[dict]:
    interaction = data.get("interaction_mode") or "不互动"
    result = []
    for frame in frames:
        copy = copy_for_frame(data, frame)
        comment_prompt = "" if interaction == "不互动" else interaction_prompt(interaction, copy["title"])
        result.append(
            {
                "frame_index": frame.get("index", 1),
                "title": copy["title"],
                "narration": copy["narration"],
                "character_lines": copy["character_lines"],
                "comment_prompt": comment_prompt,
                "text_position": {
                    "title": "顶部标题区",
                    "character_lines": "主体旁边安全区",
                    "comment_prompt": "底部字幕区",
                },
            }
        )
    return result


def interaction_prompt(interaction_mode: str, title: str) -> str:
    mapping = {
        "看向观众": f"{title}，你注意到了什么？",
        "提问互动": f"{title}，如果是你会怎么做？",
        "评论引导": f"{title}，评论区说说你的判断。",
        "点赞关注": f"{title}，想看后续可以关注下一集。",
        "选择投票": f"{title}，A/B 你选哪一个？",
    }
    return mapping.get(interaction_mode, "")


def required_references_for_frame(data: dict, frame: dict) -> list[str]:
    idx = frame.get("index", 1)
    continuous = to_bool_text(data.get("continuous_story", "否")) == "是"
    base = normalize_lines(data.get("identity_references")) or ["身份参考图 / 角色设定表", "风格参考图 / 世界观设定表"]
    scene_refs = normalize_lines(data.get("scene_references"))
    scene_ref = scene_refs[0] if scene_refs else "当前场景母版图 / 场景设定"
    if not continuous:
        return base + [scene_ref]
    if idx == 1:
        return base + [scene_ref]
    if idx == 2:
        return base + ["第1张锚点图", scene_ref]
    return base + ["第1张锚点图", f"第{idx - 1}张成图", scene_ref]


def generation_type_for_frame(data: dict, frame: dict) -> str:
    if frame.get("index", 1) == 1:
        return "anchor"
    if to_bool_text(data.get("continuous_story", "否")) == "是":
        return "continuation"
    return "variant"


def negative_prompt(data: dict) -> str:
    common = load_text(CONFIG_DIR / "negative_prompt_common.txt")
    project = load_text(CONFIG_DIR / "negative_prompt_project.txt")
    inline = data.get("project_negative_prompt") or ""
    return "\n".join([x for x in [common, project, inline] if x]).strip()


def build_prompt_plan(data: dict, frames: list[dict], prompts: list[tuple[dict, str]]) -> list[dict]:
    prompt_by_index = {frame.get("index", 1): prompt for frame, prompt in prompts}
    result = []
    for frame in frames:
        idx = frame.get("index", 1)
        result.append(
            {
                "frame_index": idx,
                "generation_type": generation_type_for_frame(data, frame),
                "required_references": required_references_for_frame(data, frame),
                "reference_rule": continuity_block(data, frame),
                "positive_prompt": prompt_by_index[idx],
                "negative_prompt": negative_prompt(data),
            }
        )
    return result


def build_qa_result(data: dict, frames: list[dict]) -> list[dict]:
    failures = data.get("qa_failures") or []
    failure_by_index = {item.get("frame_index"): item for item in failures if isinstance(item, dict)}
    result = []
    for frame in frames:
        idx = frame.get("index", 1)
        failure = failure_by_index.get(idx)
        result.append(
            {
                "frame_index": idx,
                "status": "不通过" if failure else "待检查",
                "required_checks": [
                    "角色一致",
                    "风格一致",
                    "世界观一致",
                    "造型道具连续",
                    "动作清楚",
                    "情绪推进",
                    "文字安全",
                    "平台适配",
                ],
                "failed_items": failure.get("failed_items", []) if failure else [],
                "reason": failure.get("reason", "") if failure else "",
                "next_action": "返工" if failure else "人工检查后决定入库、后期修或返工",
            }
        )
    return result


def retake_prompt_for_failure(data: dict, frame: dict, failure: dict | None) -> str:
    base = (
        "上一版图片不符合要求。请基于同一身份参考图、风格参考图和必要的锚点图重新生成本张。"
        "保持同一角色、同一世界观、同一画风、同一关键道具状态。"
        "只修复当前失败项，不随机重设计角色、服装、背景或镜头语言。"
    )
    if failure:
        failed = "、".join(failure.get("failed_items", []))
        reason = failure.get("reason", "")
        return f"{base}\n失败项：{failed}\n失败原因：{reason}"
    return base


def build_retake_prompt(data: dict, frames: list[dict]) -> list[dict]:
    failures = data.get("qa_failures") or []
    failure_by_index = {item.get("frame_index"): item for item in failures if isinstance(item, dict)}
    result = []
    for frame in frames:
        idx = frame.get("index", 1)
        failure = failure_by_index.get(idx)
        result.append(
            {
                "frame_index": idx,
                "trigger": failure.get("failed_items", []) if failure else QA_FAILURE_TYPES,
                "retake_prompt": retake_prompt_for_failure(data, frame, failure),
                "references_to_keep": required_references_for_frame(data, frame),
            }
        )
    return result


def build_pipeline_artifacts(data: dict, frames: list[dict], prompts: list[tuple[dict, str]]) -> dict:
    return {
        "input": data,
        "story_plan": build_story_plan(data),
        "frame_plan": build_frame_plan(data, frames),
        "copy_plan": build_copy_plan(data, frames),
        "prompt_plan": build_prompt_plan(data, frames, prompts),
        "qa_result": build_qa_result(data, frames),
        "retake_prompt": build_retake_prompt(data, frames),
    }


def reference_block(data: dict, frame: dict) -> str:
    required = "\n".join([f"- {x}" for x in required_references_for_frame(data, frame)])
    return f"""【跨会话身份与风格锁定】
每次新开会话或切换工具时，必须先上传或提供本项目的身份参考、风格参考、世界观设定，再发送本 Prompt。

本张必须使用的参考：
{required}

优先级：身份参考 / 角色设定 > 风格参考 / 世界观设定 > 第1张锚点图 > 上一张成图 > 当前 Prompt。
"""


def continuity_block(data: dict, frame: dict) -> str:
    total = frame.get("total", 1)
    idx = frame.get("index", 1)
    if total <= 1 or to_bool_text(data.get("continuous_story", "否")) != "是":
        return "本次不是连续故事图，可以单独生成。"
    coherence = data.get("story_coherence") or "强"
    if idx == 1:
        return f"这是连续故事的第 1 张锚点图。先单独生成这一张，用它锁定角色身份、画风、造型、关键道具和世界观气质。连续性强度：{coherence}。"
    return f"这是连续故事的第 {idx}/{total} 张。必须承接上一张，不要当成独立散图重新设计。生成本张时应继续上传第 1 张锚点图和上一张成图。连续性强度：{coherence}。"


def outfit_lock_description(data: dict) -> str:
    lock = data.get("outfit_style_lock") or "不锁定"
    ref = data.get("outfit_reference") or "文字描述"
    props = "、".join(normalize_lines(data.get("key_props"))) or "本项目关键道具"
    if lock == "不锁定":
        return f"造型风格不强制锁定，但仍需符合当前剧情和世界观。参考来源：{ref}。关键道具：{props}。"
    if lock == "弱锁定":
        return f"造型弱锁定：保持同一风格和颜色体系，可有轻微细节变化。参考来源：{ref}。关键道具：{props}。"
    return f"造型强锁定：同一套核心造型、颜色、配饰和关键道具尽量一致。参考来源：{ref}。没有明确换装理由时禁止随机更换造型。关键道具：{props}。"


def storyboard_description(data: dict, angle: str) -> str:
    enabled = data.get("in_image_storyboard") or "关闭"
    if enabled != "开启":
        return "当前图内分镜：关闭。必须保持单张完整大图，不要分镜框、不要视角窗口、不要多宫格。"
    view = data.get("storyboard_view") or "第一人称 + 第三人称"
    layout = data.get("storyboard_layout") or "主画面 + 小视角窗口"
    return f"当前图内分镜：开启。允许 2-3 个分镜，视角：{view}，布局：{layout}。主线镜头角度仍以 {angle} 为核心。"


def composition_description(data: dict, angle: str, idx: int, total: int) -> str:
    ratio = data.get("ratio") or "9:16"
    platform = data.get("platform") or "通用"
    if ratio == "9:16" or platform == "抖音竖屏":
        return (
            f"9:16，单张大图，适配{platform}。当前是第 {idx}/{total} 张。"
            "主体居中偏上，关键动作和道具完整清晰可见。顶部预留标题安全区，底部预留字幕/互动安全区。"
            f"镜头角度：{angle}。\n{storyboard_description(data, angle)}"
        )
    return f"{ratio}，单张大图，镜头角度：{angle}。\n{storyboard_description(data, angle)}"


def text_layer_block(data: dict, frame: dict) -> str:
    copy = copy_for_frame(data, frame)
    lines = [f"标题：{copy['title']}", f"旁白：{copy['narration']}"]
    for item in copy["character_lines"]:
        lines.append(f"{item['name']}：{item['text']}")
    if data.get("text_render_mode") == "直接在图中生成文字":
        return "允许短文字直接出现在画面中，但必须清晰、无乱码、无多余字符。\n" + "\n".join(lines)
    if data.get("text_mode") == "空白气泡后期加字":
        return "只生成干净空白气泡或留白区域，文字由后期叠加。文案清单如下：\n" + "\n".join(lines)
    return "仅输出文案清单，不要求画面中出现文字。\n" + "\n".join(lines)


def bubble_text_description(data: dict, frame: dict) -> str:
    bubble_mode = data.get("bubble_mode") or "无"
    text_mode = data.get("text_mode") or "无文字"
    if bubble_mode == "无" or text_mode == "无文字":
        return "不生成任何气泡、字幕、标题文字或贴纸文字；仍需在任务文件中输出文案清单，便于后期使用。"
    return "\n".join(
        [
            f"气泡模式：{bubble_mode}",
            f"文字模式：{text_mode}",
            f"文字落地模式：{data.get('text_render_mode')}",
            text_layer_block(data, frame),
        ]
    )


def audience_interaction_description(interaction_mode: str) -> str:
    mapping = {
        "不互动": "不需要观众互动，画面只服务剧情。",
        "看向观众": "允许角色看向镜头，像把观众拉入当前剧情。",
        "提问互动": "结尾或关键节点预留提问空间。",
        "评论引导": "最后一张或关键反转处适合引导评论。",
        "点赞关注": "结尾可保留轻量关注引导，但不要广告化。",
        "选择投票": "画面可形成 A/B 选择感，便于评论投票。",
    }
    return mapping.get(interaction_mode, mapping["不互动"])


def copywriting_block(data: dict, frame: dict) -> str:
    copy = copy_for_frame(data, frame)
    lines = [f"- 标题：{copy['title']}", f"- 旁白：{copy['narration']}"]
    for item in copy["character_lines"]:
        lines.append(f"- {item['name']}台词：{item['text']}")
    if data.get("interaction_mode") != "不互动":
        lines.append(f"- 互动引导：{interaction_prompt(data.get('interaction_mode'), copy['title'])}")
    return "\n".join(lines)


def build_prompt(data: dict, frame: dict) -> str:
    world = load_json(CONFIG_DIR / "world_spec.json", default={}) or {}
    scene_name = frame.get("scene") or data.get("scene") or "当前场景"
    angle = frame.get("camera") or frame.get("angle") or data.get("angle") or "第三人称中景"
    action = frame.get("action") or data.get("action") or "推进一个明确动作"
    story_outline = data.get("story_outline") or ""
    extra = data.get("extra") or ""
    visual_gene = data.get("visual_gene_summary") or world.get("visual_gene_template", {}).get("primary_subject", {}).get("fixed", "待填写：主角色固定视觉特征")
    worldview = data.get("worldview_summary") or world.get("visual_gene_template", {}).get("world", {}).get("fixed", "待填写：世界观、场景系统、道具系统、色彩体系")
    style_prompt = data.get("style_prompt") or world.get("style", {}).get("default", "请填写目标画风")
    idx, total = frame.get("index", 1), frame.get("total", 1)

    return f"""基于《通用剧情连载系统 V2.0》，生成同一项目、同一角色体系、同一世界观、同一画风下的连续剧情图。只改变本张的场景、动作、镜头和剧情推进，不随机改变核心视觉基因。

{reference_block(data, frame)}

【连续故事生成说明】
{continuity_block(data, frame)}

【项目与身份锁定】
项目名称：{data.get('project_name') or '通用剧情连载'}
视觉基因：{visual_gene}
世界观边界：{worldview}
目标画风：{style_prompt}

【故事主线】
故事模板：{frame.get('story_template', choose_story_template(data))}
故事情节：{story_outline if story_outline else '未单独填写，按故事模板和本幕推进'}
情绪推进：{data.get('emotional_progression') or '按 mood_curve 逐张推进'}
当前镜头：第 {idx}/{total} 张
上一幕：{frame.get('prev_phase', '无')}
本幕：{frame.get('story_phase', '当前镜头')}
下一幕提示：{frame.get('next_hint', '无')}
主体状态：{subject_state_for_frame(data, frame)}

【本次生成目标】
场景名称：{scene_name}
动作：{action}
视觉证据：{'、'.join(visual_evidence_for_frame(frame))}
补充约束：{extra if extra else '无'}

【造型与道具锁定】
{outfit_lock_description(data)}

【观众互动】
{audience_interaction_description(data.get('interaction_mode') or '不互动')}

【每张图文案清单】
{copywriting_block(data, frame)}

【气泡与文字落地】
{bubble_text_description(data, frame)}

【镜头构图】
{composition_description(data, angle, idx, total)}

【连续性硬约束】
如果本任务是连续故事：
1. 不要把这一张当成全新海报。
2. 必须像同一段故事里的下一个镜头。
3. 保持角色身份、造型、画风、世界观、关键道具连续一致。
4. 道具状态要推进，不要回退；已经发生的剧情状态不能凭空消失。
5. 情绪要按 mood_curve 推进，不能每张都停在同一种情绪。

【禁止项】
不要换角色身份，不要偏离世界观，不要随机换画风，不要肢体错误，不要文字乱码，不要把连续故事做成彼此无关的散图。

negative prompt:
{negative_prompt(data)}
""".strip()


def publish_order(data: dict, prompts: list[tuple[dict, str]]) -> str:
    lines = ["| 顺序 | 类型 | 场景 | 发布作用 | 标题 |", "|---:|---|---|---|---|"]
    total = len(prompts)
    for frame, _ in prompts:
        idx = frame["index"]
        kind = "封面图" if idx == 1 else "结尾图" if idx == total else "过程图"
        role = "吸引点击，建立角色与世界观" if idx == 1 else "收束故事，适合引导评论/关注" if idx == total else "推进剧情，保持连续翻页"
        title = copy_for_frame(data, frame)["title"]
        lines.append(f"| {idx} | {kind} | {frame.get('scene')} | {role} | {title} |")
    return "\n".join(lines)


def acceptance_table(prompts: list[tuple[dict, str]]) -> str:
    rows = ["| 顺序 | 必验项 | 失败返工提示 |", "|---:|---|---|"]
    for frame, _ in prompts:
        idx = frame["index"]
        rows.append(
            f"| {idx} | 角色一致；风格一致；世界观一致；造型道具连续；文案清单完整；不是拼图；主体不被气泡文字遮挡 | "
            f"第 {idx} 张不通过时：保留身份参考图、风格参考图、首张锚点图和上一张成图，重新生成本张；强化“承接上一张、造型道具不变、不要散图”。 |"
        )
    return "\n".join(rows)


def repair_prompts(data: dict) -> str:
    return f"""【通用失败返工 Prompt】
上一版图片不符合要求。请基于同一身份参考图、风格参考图和世界观设定重新生成，保持同一角色体系、同一画风、同一关键道具状态。输出仍为 {data.get('ratio')} {data.get('platform')} 单张大图。

【上一张不够连贯时的修复 Prompt】
请把当前图当作上一张的后续镜头，而不是新海报。继续使用首张锚点图 + 上一张成图作为参考，延续角色、造型、道具状态、光线和情绪。只推进当前动作，不随机换背景或换造型。
"""


def platform_caption(data: dict, prompts: list[tuple[dict, str]]) -> str:
    first_copy = copy_for_frame(data, prompts[0][0])
    last_copy = copy_for_frame(data, prompts[-1][0])
    return f"""抖音文案：{first_copy['title']}。这一组按顺序推进到「{last_copy['title']}」。你觉得下一张该怎么发展？
小红书文案：剧情连载图文记录｜从{first_copy['title']}到{last_copy['title']}，每一张都承接上一张。评论区告诉我下一集想看什么。"""


def build_prompt_bundle(data: dict):
    frames = frame_plan(data)
    prompts = [(frame, build_prompt(data, frame)) for frame in frames]
    if len(prompts) == 1:
        return prompts[0][1], prompts
    guide = f"""# 通用剧情连载生成任务 V2.0

本任务共 {len(prompts)} 张图。

## 关键生成顺序（非常重要）
1. 第 1 张：先单独生成故事锚点。
2. 第 2 张：上传身份参考图 + 风格参考图 + 第 1 张锚点图 + 本张母版图，再生成第 2 张。
3. 第 3 张及以后：上传身份参考图 + 风格参考图 + 第 1 张锚点图 + 上一张成图 + 本张母版图，再生成当前张。
4. 不要一次性并行把所有 prompt 一起生成，否则会退化成散图。

## 图文发布顺序清单
{publish_order(data, prompts)}

## 每张图验收表
{acceptance_table(prompts)}

## 返工提示词
{repair_prompts(data)}

## 平台发布文案
{platform_caption(data, prompts)}
"""
    parts = [guide]
    for frame, prompt in prompts:
        parts.append(
            f"""

---

## 第 {frame['index']}/{frame['total']} 张 Prompt

```text
{prompt}
```"""
        )
    return "\n".join(parts).strip(), prompts


def write_task(data: dict, bundle_text: str, prompts):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    scene = safe_filename(data.get("scene") or "通用剧情连载")
    ratio = safe_filename(data.get("ratio") or "9:16").replace(":", "x")
    suffix = f"{clamp_count(data.get('image_count', 1))}张" if clamp_count(data.get("image_count", 1)) > 1 else "单张"
    task_dir = OUTPUT_DIR / f"{ts}_{scene}_{ratio}_{suffix}_V2_pipeline"
    task_dir.mkdir(parents=True, exist_ok=True)
    out = task_dir / "prompt_task.md"
    frames = [frame for frame, _ in prompts]
    artifacts = build_pipeline_artifacts(data, frames, prompts)
    artifact_files = {
        "input.json": artifacts["input"],
        "story_plan.json": artifacts["story_plan"],
        "frame_plan.json": artifacts["frame_plan"],
        "copy_plan.json": artifacts["copy_plan"],
        "prompt_plan.json": artifacts["prompt_plan"],
        "qa_result.json": artifacts["qa_result"],
        "retake_prompt.json": artifacts["retake_prompt"],
    }
    for filename, payload in artifact_files.items():
        (task_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    checklist = "\n".join(
        [
            "- [ ] 第 1 张已先单独生成为锚点图",
            "- [ ] 第 2 张开始已带上“第 1 张锚点 + 上一张成图”继续生成",
            "- [ ] 已确认 story_plan / frame_plan / copy_plan / prompt_plan",
            "- [ ] 每张图都有标题、旁白、角色台词或文案清单",
            "- [ ] 文字落地模式符合预期，气泡或叠字不遮挡主体",
            "- [ ] 角色、造型、道具、世界观前后连续一致",
            "- [ ] 当前图内分镜只在明确开启时出现",
            "- [ ] 每张图都是独立大图，不是拼图或多宫格",
            "- [ ] 每张图已写入 qa_result，失败项已生成 retake_prompt",
        ]
    )
    task_body = bundle_text if len(prompts) > 1 else f"```text\n{bundle_text}\n```"
    content = f"""# 通用剧情连载生成任务 V2.0

## 最小入参

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

## V2.0 结构化产物

- `input.json`
- `story_plan.json`
- `frame_plan.json`
- `copy_plan.json`
- `prompt_plan.json`
- `qa_result.json`
- `retake_prompt.json`

## 生成任务

{task_body}

## 验收清单
{checklist}
"""
    out.write_text(content, encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description="通用剧情连载 Prompt 生成器 V2.0")
    parser.add_argument("--input", type=str)
    parser.add_argument("--project-name", dest="project_name", type=str)
    parser.add_argument("--preset-name", dest="preset_name", type=str)
    parser.add_argument("--story-id", dest="story_id", type=str)
    parser.add_argument("--story-title", dest="story_title", type=str)
    parser.add_argument("--story-template", dest="story_template", type=str)
    parser.add_argument("--story-outline", dest="story_outline", type=str)
    parser.add_argument("--emotional-progression", dest="emotional_progression", type=str)
    parser.add_argument("--scene", type=str)
    parser.add_argument("--angle", type=str)
    parser.add_argument("--action", type=str)
    parser.add_argument("--style-prompt", dest="style_prompt", type=str)
    parser.add_argument("--visual-gene-summary", dest="visual_gene_summary", type=str)
    parser.add_argument("--worldview-summary", dest="worldview_summary", type=str)
    parser.add_argument("--subject-state", dest="subject_state", type=str)
    parser.add_argument("--extra", type=str)
    parser.add_argument("--output-mode", dest="output_mode", type=str, choices=["单张大图", "多镜头拼图"])
    parser.add_argument("--ratio", type=str, choices=["4:3", "9:16"])
    parser.add_argument("--platform", type=str)
    parser.add_argument("--image-count", dest="image_count", type=int)
    parser.add_argument("--continuous-story", dest="continuous_story", type=str, choices=CONTINUOUS_STORY_VALUES)
    parser.add_argument("--identity-lock", dest="identity_lock", type=str, choices=["强锁定", "普通锁定"])
    parser.add_argument("--bubble-mode", dest="bubble_mode", type=str, choices=BUBBLE_MODES)
    parser.add_argument("--text-mode", dest="text_mode", type=str, choices=TEXT_MODES)
    parser.add_argument("--text-render-mode", dest="text_render_mode", type=str, choices=TEXT_RENDER_MODES)
    parser.add_argument("--text-position", dest="text_position", type=str, choices=TEXT_POSITIONS)
    parser.add_argument("--copywriting-mode", dest="copywriting_mode", type=str, choices=COPYWRITING_MODES)
    parser.add_argument("--interaction-mode", dest="interaction_mode", type=str, choices=INTERACTION_MODES)
    parser.add_argument("--story-coherence", dest="story_coherence", type=str, choices=STORY_COHERENCE_VALUES)
    parser.add_argument("--outfit-style-lock", dest="outfit_style_lock", type=str, choices=OUTFIT_STYLE_LOCKS)
    parser.add_argument("--outfit-reference", dest="outfit_reference", type=str, choices=OUTFIT_REFERENCES)
    parser.add_argument("--in-image-storyboard", dest="in_image_storyboard", type=str, choices=IN_IMAGE_STORYBOARD_VALUES)
    parser.add_argument("--storyboard-view", dest="storyboard_view", type=str, choices=STORYBOARD_VIEWS)
    parser.add_argument("--storyboard-layout", dest="storyboard_layout", type=str, choices=STORYBOARD_LAYOUTS)
    parser.add_argument("--title-text", dest="title_text", type=str)
    parser.add_argument("--narration-text", dest="narration_text", type=str)
    parser.add_argument("--project-negative-prompt", dest="project_negative_prompt", type=str)
    args = parser.parse_args()

    data = {}
    loaded_from_input = False
    if args.input:
        input_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
        data = load_json(input_path)
        loaded_from_input = True

    keys = [
        "project_name",
        "preset_name",
        "story_id",
        "story_title",
        "story_template",
        "story_outline",
        "emotional_progression",
        "scene",
        "angle",
        "action",
        "style_prompt",
        "visual_gene_summary",
        "worldview_summary",
        "subject_state",
        "extra",
        "output_mode",
        "ratio",
        "platform",
        "image_count",
        "continuous_story",
        "identity_lock",
        "bubble_mode",
        "text_mode",
        "text_render_mode",
        "text_position",
        "copywriting_mode",
        "interaction_mode",
        "story_coherence",
        "outfit_style_lock",
        "outfit_reference",
        "in_image_storyboard",
        "storyboard_view",
        "storyboard_layout",
        "title_text",
        "narration_text",
        "project_negative_prompt",
    ]
    for key in keys:
        val = getattr(args, key)
        if val not in [None, ""]:
            data[key] = val

    if loaded_from_input:
        errors = validate_input(data, args.input)
        if errors:
            raise SystemExit("入参校验失败：\n- " + "\n- ".join(errors))

    data = normalize_defaults(data)
    bundle, prompts = build_prompt_bundle(data)
    out = write_task(data, bundle, prompts)
    print("已生成 Prompt 任务：")
    print(out)
    print("\n--- Prompt 预览 ---\n")
    print(bundle)


if __name__ == "__main__":
    main()
