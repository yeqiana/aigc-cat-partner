#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人猫搭档 Prompt 生成入口 V1.7

V1.7 重点：
1. 在原 Prompt 包基础上输出 story/frame/copy/prompt/qa/retake 六类结构化产物。
2. 明确第 1 张锚点图、第 2 张续图、第 3-N 张续图的引用规则。
3. 支持用 qa_failures 手动标记失败，并生成可执行返工 Prompt。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "06_最终可用图" / "生成任务"

BUBBLE_MODES = ["无", "人物气泡", "猫咪气泡", "双气泡", "旁白标题"]
TEXT_MODES = ["无文字", "直接生成文字", "空白气泡后期加字"]
TEXT_RENDER_MODES = [
    "仅生成文案清单",
    "生成空白气泡 + 文案清单",
    "生成空白气泡 + 后期叠字图层",
    "直接在图中生成文字",
]
TEXT_POSITIONS = ["自动", "顶部标题区", "人物旁边", "猫咪旁边", "底部字幕区"]
COPYWRITING_MODES = ["手动填写", "自动根据情节生成"]
INTERACTION_MODES = ["不互动", "看向观众", "提问互动", "评论引导", "点赞关注", "选择投票"]
CONTINUOUS_STORY_VALUES = ["否", "是"]
STORY_TEMPLATES = ["自动判断", "外卖跑单故事", "居家治愈故事"]
STORY_COHERENCE_VALUES = ["普通", "强"]
OUTFIT_STYLE_LOCKS = ["不锁定", "弱锁定", "强锁定"]
OUTFIT_REFERENCES = ["文字描述", "人物参考图", "第一张锚点图", "当前故事模板默认服装", "第一张锚点图 + 人物参考图"]
IN_IMAGE_STORYBOARD_VALUES = ["关闭", "开启"]
STORYBOARD_VIEWS = ["第一人称", "第三人称", "第一人称 + 第三人称"]
STORYBOARD_LAYOUTS = ["上下分镜", "左右分镜", "主画面 + 小视角窗口"]
V17_REQUIRED_INPUT_FIELDS = ["image_count", "continuous_story", "story_template"]
QA_FAILURE_TYPES = ["剧情动作", "人物一致性", "猫咪一致性", "服装道具连续性", "气泡可用性", "文案完整性", "镜头构图", "平台适配"]


BASE_COPY = {
    "送外卖正面": {"title": "第1单出发", "narration": "人猫搭档开工", "human": "准备出发", "cat": "我坐稳啦"},
    "取外卖侧面": {"title": "取餐完成", "narration": "第一单到手", "human": "马上送到", "cat": "袋子好香"},
    "骑车45度": {"title": "路上赶单", "narration": "风里继续跑", "human": "稳一点", "cat": "我看路"},
    "楼下抬头": {"title": "先确认楼层", "narration": "到楼下了", "human": "就是这栋", "cat": "往上看"},
    "爬楼疲惫": {"title": "还剩几层", "narration": "最后一段路", "human": "快到了", "cat": "累鼠啦"},
    "送达门口": {"title": "这一单送达", "narration": "准时完成", "human": "已送到", "cat": "终于到了"},
    "收工回家": {"title": "今日收工", "narration": "回家放松", "human": "辛苦啦", "cat": "加餐吗"},
    "沙发绿植正面": {"title": "今日搭子营业", "narration": "在家也认真", "human": "坐好啦", "cat": "我很乖"},
    "沙发绿植45度": {"title": "抱住小搭子", "narration": "贴贴一下", "human": "别乱动", "cat": "知道啦"},
}

INTERACTION_COPY = {
    "不互动": {},
    "看向观众": {"title": "今天跟我们跑一单", "human": "跟上哦", "cat": "看我表现"},
    "提问互动": {"title": "你会点哪一单", "human": "这单送哪儿", "cat": "你选吧"},
    "评论引导": {"title": "评论区说说你最爱吃啥", "human": "我去取", "cat": "我来送"},
    "点赞关注": {"title": "关注人猫送达", "human": "准时送到", "cat": "点个赞嘛"},
    "选择投票": {"title": "接着跑还是先休息", "human": "听你的", "cat": "我想休息"},
}

DELIVERY_STORY = [
    {"scene": "送外卖正面", "angle": "正面中景", "action": "女生在街边整理外卖箱，准备出发，猫稳稳坐在前篮里", "extra": "第1幕：故事开场。还没出发，状态轻松，电动车和外卖箱完整干净。", "state": "开始跑单，精神比较足，外卖箱整齐，手上暂时没有餐袋。"},
    {"scene": "取外卖侧面", "angle": "侧面中景", "action": "女生在取餐窗口接过外卖袋，猫从车篮里好奇地看着袋子", "extra": "第2幕：取餐。道具推进：现在已经拿到第一单外卖袋。", "state": "承接上一张，已经出发并成功到店，手里出现外卖袋。"},
    {"scene": "骑车45度", "angle": "前方45度中景", "action": "女生骑车或扶车前进，外卖袋和外卖箱一起出现在车上，猫迎着风看前方", "extra": "第3幕：路上。状态推进：头发和衣角有风，画面更有动感。", "state": "承接上一张，已经离开店铺，正在去送餐的路上。外卖袋不能消失。"},
    {"scene": "楼下抬头", "angle": "仰拍中景", "action": "女生在楼下停好车，提着外卖袋抬头看楼，猫在前篮或背包里探头", "extra": "第4幕：到楼下确认楼层。", "state": "承接上一张，已经到达收餐地址楼下。电动车停在附近，女生手里仍提着外卖袋。"},
    {"scene": "爬楼疲惫", "angle": "背面45度 / 回头视角", "action": "女生提着外卖袋往楼上走，背着外卖箱，猫在宠物背包或旁边探头", "extra": "第5幕：爬楼。情绪推进：开始有点累。", "state": "承接上一张，正在上楼送餐，已经明显更累，但还没送达。"},
    {"scene": "送达门口", "angle": "侧前方中景", "action": "女生在住户门口送达外卖，猫在旁边探头看着，动作自然", "extra": "第6幕：送达。剧情推进：这一单完成。", "state": "承接上一张，已经到达门口，外卖袋准备递出或刚刚放下。"},
    {"scene": "爬楼疲惫", "angle": "正面低角度", "action": "女生在楼梯平台或过道短暂休息，猫坐在旁边一起发呆", "extra": "第7幕：送完后一小会儿休息。", "state": "承接上一张，外卖袋已经送出，不要再出现完整待送外卖袋。"},
    {"scene": "收工回家", "angle": "正面半身", "action": "女生和猫回到沙发上休息，女生轻轻搂着猫，氛围放松", "extra": "第8幕：收工。像一天结束后的结尾图。", "state": "承接上一张，回家收工，情绪从疲惫过渡到放松。"},
]

HOME_STORY = [
    {"scene": "沙发绿植正面", "angle": "正面半身", "action": "女生和猫坐在沙发上看镜头", "extra": "第1幕：开场合照。", "state": "故事开场，室内温馨。"},
    {"scene": "沙发绿植45度", "angle": "45度半身", "action": "女生侧身抱猫，猫靠在怀里", "extra": "第2幕：抱猫互动。", "state": "承接上一张，更亲密。"},
    {"scene": "沙发绿植正面", "angle": "正面近景", "action": "重点展示互印头像 T 恤", "extra": "第3幕：展示衣服图案。", "state": "承接上一张，重点切到衣服。"},
    {"scene": "沙发绿植45度", "angle": "45度近景", "action": "猫咪抢镜，女生轻轻扶着", "extra": "第4幕：猫咪抢镜。", "state": "承接上一张，猫成为视觉重点。"},
    {"scene": "收工回家", "angle": "正面半身", "action": "女生和猫一起放松休息", "extra": "第5幕：结尾纪念照。", "state": "结尾收束，氛围平静。"},
]

VISUAL_EVIDENCE_BY_SCENE = {
    "送外卖正面": ["手机订单页", "浅色电动车", "黑色网格前车篮", "浅色后外卖箱"],
    "取外卖侧面": ["取餐窗口", "外卖袋", "店门招牌", "前车篮里的猫"],
    "骑车45度": ["行驶中的电动车", "外卖箱", "路面动感", "前篮里的猫"],
    "楼下抬头": ["楼栋入口", "门牌或楼号", "停好的电动车", "手里的外卖袋"],
    "爬楼疲惫": ["楼梯扶手", "外卖袋", "背上的外卖箱", "宠物背包或猫背带"],
    "送达门口": ["住户门口", "外卖袋", "门牌区域", "猫探头看门口"],
    "收工回家": ["沙发", "放松姿态", "猫靠在身边", "室内暖光"],
    "沙发绿植正面": ["沙发", "绿植背景", "女生正面坐姿", "猫在怀里或身边"],
    "沙发绿植45度": ["沙发", "绿植背景", "侧身抱猫", "衣服图案或猫咪表情"],
}

MOOD_CURVES = {
    "外卖跑单故事": ["紧张", "小心", "专注", "进入状态", "有点慌", "放松", "短暂休息", "收工"],
    "居家治愈故事": ["放松", "亲密", "展示", "调皮", "安静", "治愈"],
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_v17_input(raw_data: dict, source_name: str = "输入 JSON") -> list[str]:
    missing = [field for field in V17_REQUIRED_INPUT_FIELDS if field not in raw_data or raw_data.get(field) in [None, ""]]
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


def safe_filename(text: str) -> str:
    bad = '<>:"/\\|?*\n\r\t'
    for ch in bad:
        text = text.replace(ch, "_")
    return text.strip()[:80] or "task"


def short_text(text: str, max_chars: int = 14) -> str:
    return (text or "").strip()[:max_chars]


def to_bool_text(value) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    value = str(value or "否").strip()
    return "是" if value in ["是", "true", "True", "1", "yes", "YES"] else "否"


def clamp_count(value) -> int:
    try:
        n = int(value)
    except Exception:
        n = 1
    return max(1, min(12, n))


def clothing_description(clothing: str) -> str:
    presets = {
        "白T互印头像": "人和猫都穿简约白色 T 恤。女生的白色 T 恤胸口印着猫的脸，图案占胸口大面积，保留猫的头部和脖子。猫的白色 T 恤胸口印着女生的脸，图案只保留女生头部，不要脖子。",
        "居家休闲服": "女生穿奶油白或浅咖色居家休闲上衣，柔软自然，有真实布料褶皱。猫穿协调的浅色小衣服，保持可爱但不过度拟人。",
        "外卖职业服": "女生穿白色 T 恤加简约外卖马甲，颜色以奶油白、浅咖、黑色边线为主。猫穿迷你外卖马甲，与女生形成搭档感。可以有简单爪印标志，但不要复杂乱码文字。",
    }
    return presets.get(clothing, clothing or presets["居家休闲服"])


def choose_story_template(data: dict) -> str:
    tpl = data.get("story_template") or "自动判断"
    if tpl != "自动判断":
        return tpl
    scene = data.get("scene") or "送外卖正面"
    if scene in ["送外卖正面", "取外卖侧面", "骑车45度", "楼下抬头", "爬楼疲惫", "送达门口"]:
        return "外卖跑单故事"
    return "居家治愈故事"


def frame_plan(data: dict) -> list[dict]:
    data = normalize_defaults(data)
    count = clamp_count(data.get("image_count", 1))
    continuous = to_bool_text(data.get("continuous_story", "否"))
    scene_name = data.get("scene") or "沙发绿植正面"
    if count <= 1:
        return [{"index": 1, "total": 1, "scene": scene_name, "story_phase": "单张图", "state": "单张图无需剧情推进。"}]
    if continuous == "是":
        tpl = choose_story_template(data)
        base = DELIVERY_STORY if tpl == "外卖跑单故事" else HOME_STORY
        frames = []
        for i in range(count):
            src = dict(base[i % len(base)])
            src["index"] = i + 1
            src["total"] = count
            src["story_template"] = tpl
            src["story_phase"] = src.get("extra", "").split("：")[0] if "：" in src.get("extra", "") else f"第{i + 1}幕"
            src["prev_phase"] = "无，故事开场" if i == 0 else frames[i - 1]["story_phase"]
            src["next_hint"] = base[(i + 1) % len(base)].get("extra", "下一幕继续").split("：")[0] if i + 1 < count else "故事收束"
            frames.append(src)
        return frames
    angles = ["正面中景", "前方45度中景", "侧面中景", "近景半身", "背面45度 / 回头视角", "低角度中景"]
    return [
        {
            "index": i + 1,
            "total": count,
            "scene": scene_name,
            "angle": angles[i % len(angles)],
            "action": data.get("action") or "保持同主题小变化",
            "extra": f"第{i + 1}张同主题变体，只换角度和细节，不要求故事推进。",
            "story_phase": "同主题变体",
            "state": "保持同主题。",
        }
        for i in range(count)
    ]


def copy_for_frame(data: dict, frame: dict) -> dict:
    manual = {
        "title": short_text(data.get("title_text"), 16),
        "narration": short_text(data.get("narration_text"), 16),
        "human": short_text(data.get("human_text"), 14),
        "cat": short_text(data.get("cat_text"), 14),
    }
    if data.get("copywriting_mode") == "手动填写" and any(manual.values()):
        base = dict(BASE_COPY.get(frame.get("scene"), BASE_COPY["沙发绿植正面"]))
        base.update({k: v for k, v in manual.items() if v})
        return base

    base = dict(BASE_COPY.get(frame.get("scene"), BASE_COPY["沙发绿植正面"]))
    interaction_mode = data.get("interaction_mode") or "不互动"
    is_interaction_frame = frame.get("total", 1) <= 1 or frame.get("index") == frame.get("total")
    if interaction_mode != "不互动" and is_interaction_frame:
        base.update({k: v for k, v in INTERACTION_COPY.get(interaction_mode, {}).items() if v})
    if frame.get("total", 1) > 1:
        base["narration"] = short_text(f"{frame.get('story_phase', '这一幕')}继续", 16)
    return {k: short_text(v, 16 if k in ["title", "narration"] else 14) for k, v in base.items()}


def build_story_plan(data: dict) -> dict:
    tpl = choose_story_template(data)
    count = clamp_count(data.get("image_count", 1))
    mood_curve = list(data.get("mood_curve") or MOOD_CURVES.get(tpl, ["日常", "推进", "收束"]))
    if len(mood_curve) < count:
        mood_curve.extend([mood_curve[-1]] * (count - len(mood_curve)))
    return {
        "story_id": data.get("story_id") or f"{'delivery' if tpl == '外卖跑单故事' else 'home'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "story_title": data.get("story_title") or ("第一天送外卖" if tpl == "外卖跑单故事" else "居家治愈日常"),
        "platform": data.get("platform") or "抖音竖屏",
        "ratio": data.get("ratio") or "9:16",
        "image_count": count,
        "continuous_story": to_bool_text(data.get("continuous_story", "否")) == "是",
        "story_template": tpl,
        "story_outline": data.get("story_outline") or "",
        "mood_curve": mood_curve[:count],
        "anchor_frame_index": 1,
        "text_render_mode": data.get("text_render_mode") or "生成空白气泡 + 后期叠字图层",
    }


def visual_evidence_for_frame(frame: dict) -> list[str]:
    scene_name = frame.get("scene") or "沙发绿植正面"
    evidence = list(VISUAL_EVIDENCE_BY_SCENE.get(scene_name, []))
    if len(evidence) < 2:
        evidence.extend(["人物动作清楚", "猫咪位置清楚"])
    return evidence[:4]


def cat_state_for_frame(frame: dict) -> str:
    scene_name = frame.get("scene") or ""
    if scene_name in ["送外卖正面", "骑车45度"]:
        return "坐在电动车前篮里，保持同一只白色银渐层猫"
    if scene_name in ["楼下抬头", "爬楼疲惫", "送达门口"]:
        return "在前篮、宠物背包或人物旁边探头，状态承接上一张"
    return "待在女生怀里或身边，表情自然稳定"


def build_frame_plan(data: dict, frames: list[dict]) -> list[dict]:
    story = build_story_plan(data)
    result = []
    for frame in frames:
        idx = frame.get("index", 1)
        role = "anchor" if idx == story["anchor_frame_index"] else ("continuation" if story["continuous_story"] else "variant")
        if idx == 1:
            continuity = "首张锚点图，无上一张"
        elif story["continuous_story"]:
            continuity = f"承接第 {idx - 1} 张成图，保持人物、猫、服装和关键道具连续"
        else:
            continuity = "非连续同主题变体，不强制引用上一张成图"
        result.append(
            {
                "frame_index": idx,
                "main_action": frame.get("action") or data.get("action") or "保持同主题小变化",
                "continuity_from_previous": continuity,
                "visual_evidence": visual_evidence_for_frame(frame),
                "character_emotion": story["mood_curve"][idx - 1] if idx - 1 < len(story["mood_curve"]) else data.get("mood", "自然"),
                "cat_state": cat_state_for_frame(frame),
                "camera": frame.get("angle") or data.get("angle") or "第三人称正面中景",
                "in_image_storyboard": data.get("in_image_storyboard") == "开启",
                "role": role,
                "source_scene": frame.get("scene"),
            }
        )
    return result


def build_copy_plan(data: dict, frames: list[dict]) -> list[dict]:
    interaction = data.get("interaction_mode") or "不互动"
    result = []
    for frame in frames:
        copy = copy_for_frame(data, frame)
        comment_prompt = "" if interaction == "不互动" else f"{copy['title']}，你会怎么选？"
        result.append(
            {
                "frame_index": frame.get("index", 1),
                "title": copy["title"],
                "girl_bubble": copy["human"],
                "cat_bubble": copy["cat"],
                "narration": copy.get("narration", copy["title"]),
                "comment_prompt": comment_prompt,
                "text_position": {
                    "title": "顶部标题区",
                    "girl_bubble": "人物附近安全区",
                    "cat_bubble": "猫咪附近安全区",
                    "comment_prompt": "底部字幕区",
                },
            }
        )
    return result


def required_references_for_frame(data: dict, frame: dict) -> list[str]:
    idx = frame.get("index", 1)
    continuous = to_bool_text(data.get("continuous_story", "否")) == "是"
    base = ["原始人物身份参考图", "原始猫咪身份参考图"]
    if not continuous:
        return base + ["当前场景母版图"]
    if idx == 1:
        return base + ["当前场景母版图"]
    if idx == 2:
        return base + ["第1张锚点图"]
    return base + ["第1张锚点图", f"第{idx - 1}张成图"]


def generation_type_for_frame(data: dict, frame: dict) -> str:
    if frame.get("index", 1) == 1:
        return "anchor"
    if to_bool_text(data.get("continuous_story", "否")) == "是":
        return "continuation"
    return "variant"


def build_prompt_plan(data: dict, frames: list[dict], prompts: list[tuple[dict, str]]) -> list[dict]:
    negative = (CONFIG_DIR / "negative_prompt.txt").read_text(encoding="utf-8").strip()
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
                "negative_prompt": f"{negative}\n不要换衣服，不要换车，不要换猫，不要生成拼图，不要九宫格，不要直接生成中文乱码文字。",
            }
        )
    return result


def retake_prompt_for_frame(frame_plan_item: dict, failed_items: list[str] | None = None, reason: str = "") -> str:
    failed_text = "、".join(failed_items or ["连续性", "视觉证据"]) or "连续性"
    evidence = "、".join(frame_plan_item.get("visual_evidence", []))
    scene_name = frame_plan_item.get("source_scene") or ""
    delivery_scenes = {"送外卖正面", "取外卖侧面", "骑车45度", "楼下抬头", "爬楼疲惫", "送达门口"}
    if scene_name in delivery_scenes:
        stable_items = [
            "同一个年轻女生",
            "同一只白色银渐层猫",
            "同一套米色外卖马甲、白 T、深色裤子",
            "同一辆浅色电动车",
            "同一黑色网格前车篮",
            "同一浅色后外卖箱",
            "同一米色猫背带",
        ]
    else:
        stable_items = [
            "同一个年轻女生",
            "同一只白色银渐层猫",
            "同一套居家服装、眼镜、发型和整体气质",
            "同一个沙发绿植居家环境",
            "同一套空白气泡和后期叠字策略",
        ]
    stable_block = "\n".join(f"- {item}" for item in stable_items)
    return f"""请基于第 1 张锚点图和上一张成图重新生成第 {frame_plan_item['frame_index']} 张。

本次返工重点：修复 {failed_text}。
失败原因：{reason or '当前图未通过人工验收'}。

必须保持：
{stable_block}

本张只表达一个动作：
{frame_plan_item['main_action']}

画面必须出现这些视觉证据：
{evidence}

镜头改为：
{frame_plan_item['camera']}

保留空白气泡，后期叠字，不要直接生成中文。
不要拼图，不要九宫格，不要漫画框。""".strip()


def build_qa_results(data: dict, frame_plan_items: list[dict]) -> list[dict]:
    failures = {int(x.get("frame_index")): x for x in data.get("qa_failures", []) if str(x.get("frame_index", "")).isdigit()}
    result = []
    for item in frame_plan_items:
        idx = item["frame_index"]
        failure = failures.get(idx)
        if failure:
            failed_items = failure.get("failed_items") or ["人工标记失败"]
            reason = failure.get("reason") or "人工标记当前图未通过"
            result.append(
                {
                    "frame_index": idx,
                    "passed": False,
                    "status": "failed_manual_review",
                    "failed_items": failed_items,
                    "reason": reason,
                    "retake_prompt": retake_prompt_for_frame(item, failed_items, reason),
                }
            )
            continue
        result.append(
            {
                "frame_index": idx,
                "passed": None,
                "status": "pending_image_review",
                "failed_items": [],
                "reason": "待真实图片生成后按验收标准人工检查",
                "retake_prompt": "",
                "check_items": QA_FAILURE_TYPES,
            }
        )
    return result


def build_retake_prompts(frame_plan_items: list[dict], qa_results: list[dict]) -> list[dict]:
    retakes = []
    qa_by_index = {x["frame_index"]: x for x in qa_results}
    for item in frame_plan_items:
        qa = qa_by_index[item["frame_index"]]
        retakes.append(
            {
                "frame_index": item["frame_index"],
                "trigger_items": qa.get("failed_items") or QA_FAILURE_TYPES,
                "retake_prompt": qa.get("retake_prompt") or retake_prompt_for_frame(item),
            }
        )
    return retakes


def build_pipeline_artifacts(data: dict, frames: list[dict], prompts: list[tuple[dict, str]]) -> dict:
    story = build_story_plan(data)
    frame_items = build_frame_plan(data, frames)
    copy_items = build_copy_plan(data, frames)
    prompt_items = build_prompt_plan(data, frames, prompts)
    qa_items = build_qa_results(data, frame_items)
    retake_items = build_retake_prompts(frame_items, qa_items)
    return {
        "input": data,
        "story_plan": story,
        "frame_plan": frame_items,
        "copy_plan": copy_items,
        "prompt_plan": prompt_items,
        "qa_result": qa_items,
        "retake_prompt": retake_items,
    }


def copywriting_block(data: dict, frame: dict) -> str:
    copy = copy_for_frame(data, frame)
    return "\n".join(
        [
            f"标题：{copy['title']}",
            f"旁白：{copy.get('narration', copy['title'])}",
            f"女生台词：{copy['human']}",
            f"猫咪台词：{copy['cat']}",
        ]
    )


def text_layer_block(data: dict, frame: dict) -> str:
    mode = data.get("text_render_mode") or "生成空白气泡 + 后期叠字图层"
    position = data.get("text_position") or "自动"
    copy = copy_for_frame(data, frame)
    if mode == "仅生成文案清单":
        return "只输出文案清单，不要求画面里出现气泡或文字。"
    if mode == "直接在图中生成文字":
        return f"可以直接在图中生成短中文：标题『{copy['title']}』，女生『{copy['human']}』，猫咪『{copy['cat']}』。文字必须清晰可读，不乱码。位置：{position}。"
    if mode == "生成空白气泡 + 文案清单":
        return f"画面生成干净空白气泡或空白标题贴纸，不直接生成文字；同时交付文案清单。后期文字位置：{position}。"
    return (
        "画面生成干净空白气泡，并预留后期叠字区域；交付叠字图层规格："
        f"标题置于顶部安全区『{copy['title']}』；女生台词放人物附近『{copy['human']}』；"
        f"猫咪台词放猫附近『{copy['cat']}』。文字不要遮挡人脸、猫脸、眼镜和关键动作。"
    )


def audience_interaction_description(interaction_mode: str) -> str:
    mapping = {
        "不互动": "不做观众互动，保持自然生活感。",
        "看向观众": "需要建立视线互动：女生和猫至少一个明确看向镜头。",
        "提问互动": "需要有轻微提问感：标题或气泡适合抛出问题。",
        "评论引导": "需要评论互动感：标题或气泡引导观众在评论区回复。",
        "点赞关注": "需要轻微点赞关注引导，但不要过度营销。",
        "选择投票": "需要投票互动感：给出 A/B 选择。",
    }
    return mapping.get(interaction_mode, mapping["不互动"])


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


def outfit_lock_description(data: dict) -> str:
    lock = data.get("outfit_style_lock") or "不锁定"
    ref = data.get("outfit_reference") or "文字描述"
    if lock == "不锁定":
        return f"服装风格不强制锁定，但仍需符合当前剧情。参考来源：{ref}。"
    if lock == "弱锁定":
        return f"服装弱锁定：保持同一风格和颜色体系，可有轻微细节变化。参考来源：{ref}。"
    return (
        f"服装强锁定：同一套衣服、颜色、配饰、鞋包、眼镜、外卖箱尽量一致。参考来源：{ref}。"
        "如果剧情没有明确换装理由，禁止随机更换服装类型。"
    )


def storyboard_description(data: dict, angle: str) -> str:
    enabled = data.get("in_image_storyboard") or "关闭"
    if enabled != "开启":
        return "当前图内分镜：关闭。必须保持单张完整大图，不要分镜框、不要视角窗口、不要多宫格。"
    view = data.get("storyboard_view") or "第一人称 + 第三人称"
    layout = data.get("storyboard_layout") or "主画面 + 小视角窗口"
    return (
        f"当前图内分镜：开启。允许 2-3 个分镜，视角：{view}，布局：{layout}。"
        f"主线镜头角度仍以 {angle} 为核心。不要生成九宫格，不要无关拼贴，分镜必须服务当前剧情。"
    )


def composition_description(data: dict, angle: str, idx: int, total: int) -> str:
    ratio = data.get("ratio") or "4:3"
    if ratio == "9:16" or data.get("platform") == "抖音竖屏":
        return (
            f"9:16，单张大图，抖音竖屏比例。当前是第 {idx}/{total} 张。"
            "主体居中偏上，人和猫完整清晰可见。顶部预留标题安全区，底部预留字幕/按钮安全区。"
            f"镜头角度：{angle}。\n{storyboard_description(data, angle)}"
        )
    return f"4:3，中景/半身为主，镜头角度：{angle}。\n{storyboard_description(data, angle)}"


def reference_block(scene_name: str) -> str:
    manifest = load_json(CONFIG_DIR / "reference_manifest.json")
    required = "\n".join([f"- {x}" for x in manifest.get("required_each_new_session", [])])
    optional = manifest.get("optional_master_references", {}).get(scene_name, "按本次场景选择对应母版图")
    return f"""【跨会话身份锁定｜新会话必须执行】
每次新开会话或切换工具时，必须先上传身份参考图，再发送本 Prompt。

必传身份参考图：
{required}

本场景建议额外上传母版参考图：
- {optional}
"""


def continuity_block(data: dict, frame: dict) -> str:
    total = frame.get("total", 1)
    idx = frame.get("index", 1)
    if total <= 1 or to_bool_text(data.get("continuous_story", "否")) != "是":
        return "本次不是连续故事图，可以单独生成。"
    coherence = data.get("story_coherence") or "强"
    if idx == 1:
        return f"这是连续故事的第 1 张锚点图。先单独生成这一张，用它锁定故事开场、服装、道具、电动车、外卖箱和整体气质。连续性强度：{coherence}。"
    return f"这是连续故事的第 {idx}/{total} 张。必须承接上一张，不要当成独立散图重新设计。生成本张时，除身份参考图外，还应继续上传：第 1 张锚点图 + 上一张成图 + 本场景母版图。服装、道具、电动车、外卖箱、光线时段、情绪状态都要延续。连续性强度：{coherence}。"


def build_prompt(data: dict, frame: dict) -> str:
    spec = load_json(CONFIG_DIR / "character_spec.json")
    scenes = load_json(CONFIG_DIR / "scenes.json")
    negative = (CONFIG_DIR / "negative_prompt.txt").read_text(encoding="utf-8").strip()
    scene_name = frame.get("scene") or data.get("scene") or "沙发绿植正面"
    scene = scenes.get(scene_name, scenes["沙发绿植正面"])
    angle = frame.get("angle") or data.get("angle") or scene.get("angle") or "正面半身"
    action = frame.get("action") or data.get("action") or scene.get("action_description")
    clothing = data.get("clothing") if data.get("clothing") not in [None, "", "自动使用场景预设"] else scene.get("clothing_suggestion") or "居家休闲服"
    mood = data.get("mood") or "日常轻松"
    story_outline = data.get("story_outline") or ""
    extra = frame.get("extra") or data.get("extra") or ""
    human = spec["human_visual_gene"]
    cat = spec["cat_visual_gene"]
    style = spec["style"]
    idx, total = frame.get("index", 1), frame.get("total", 1)

    return f"""基于《人猫搭档 AIGC 统一出图规范 V1.7》，保持同一个女生、同一只白色银渐层猫、同一套真实拍立得生活摄影风格，只改变本次场景、动作、角度和剧情推进，不改变核心视觉基因。

{reference_block(scene_name)}

【连续故事生成说明】
{continuity_block(data, frame)}

【身份锁定】
使用参考图锁定同一个年轻女生和同一只白色银渐层猫。
女生固定视觉基因：{human['age']}，{human['face']}，{human['hair']}，{human['glasses']}，{human['body']}。
猫固定视觉基因：{cat['breed']}，{cat['face']}，{cat['fur']}，{cat['expression']}。

【故事主线】
故事模板：{frame.get('story_template', choose_story_template(data))}
故事情节：{story_outline if story_outline else '未单独填写，按故事模板和本幕推进'}
当前镜头：第 {idx}/{total} 张
上一幕：{frame.get('prev_phase', '无')}
本幕：{frame.get('story_phase', '当前镜头')}
下一幕提示：{frame.get('next_hint', '无')}
剧情状态：{frame.get('state', '无')}

【本次生成目标】
场景名称：{scene_name}
场景描述：{scene.get('scene_description')}
动作：{action}
氛围：{mood}
补充剧情：{extra if extra else '无'}

【服装与道具锁定】
{clothing_description(clothing)}
{outfit_lock_description(data)}

【观众互动】
{audience_interaction_description(data.get('interaction_mode') or '不互动')}

【每张图文案清单】
{copywriting_block(data, frame)}

【气泡与文字落地】
{bubble_text_description(data, frame)}

【镜头构图】
{composition_description(data, angle, idx, total)}

【画质风格】
{style['quality']}。照片真实感生活感强，衣服、街道、楼道、沙发、猫毛、光影都要自然。

【连续性硬约束】
如果本任务是连续故事：
1. 不要把这一张当成全新摆拍海报。
2. 必须像同一天、同一段故事里的下一个镜头。
3. 保持服装、眼镜、猫的毛色和体型、电动车、外卖箱连续一致。
4. 道具状态要推进，不要回退；已拿到的餐袋不能凭空消失，已送达的餐袋不要再次出现为待送状态。
5. 情绪要推进：轻松 → 专注 → 忙碌/疲惫 → 放松收工。

【禁止项】
{human['forbidden']}。{cat['forbidden']}。不要换脸，不要换猫品种，不要卡通化，不要过度美颜，不要肢体错误，不要文字乱码。不要把连续故事做成彼此毫无关系的散图。

negative prompt:
{negative}
""".strip()


def publish_order(data: dict, prompts: list[tuple[dict, str]]) -> str:
    lines = ["| 顺序 | 类型 | 场景 | 发布作用 | 标题 |", "|---:|---|---|---|---|"]
    total = len(prompts)
    for frame, _ in prompts:
        idx = frame["index"]
        kind = "封面图" if idx == 1 else "结尾图" if idx == total else "过程图"
        role = "吸引点击，建立人猫身份" if idx == 1 else "收束故事，适合引导评论/关注" if idx == total else "推进剧情，保持连续翻页"
        title = copy_for_frame(data, frame)["title"]
        lines.append(f"| {idx} | {kind} | {frame.get('scene')} | {role} | {title} |")
    return "\n".join(lines)


def acceptance_table(prompts: list[tuple[dict, str]]) -> str:
    rows = ["| 顺序 | 必验项 | 失败返工提示 |", "|---:|---|---|"]
    for frame, _ in prompts:
        idx = frame["index"]
        rows.append(
            f"| {idx} | 人猫身份一致；服装道具连续；文案清单完整；不是拼图；主体不被气泡文字遮挡 | "
            f"第 {idx} 张不通过时：请保留身份参考图、首张锚点图和上一张成图，重新生成本张；强化“承接上一张、服装道具不变、不要散图”。 |"
        )
    return "\n".join(rows)


def repair_prompts(data: dict) -> str:
    return f"""【通用失败返工 Prompt】
上一版图片不符合要求。请基于同一身份参考图重新生成，保持同一个女生、同一只白色银渐层猫，不要换脸、不要换猫、不要换服装风格。输出仍为 {data.get('ratio')} {data.get('platform')} 单张大图。

【上一张不够连贯时的修复 Prompt】
请把当前图当作上一张的后续镜头，而不是新海报。继续使用首张锚点图 + 上一张成图作为参考，延续服装、道具、电动车/外卖箱状态、光线和情绪。只推进当前动作，不随机换背景或换造型。
"""


def platform_caption(data: dict, prompts: list[tuple[dict, str]]) -> str:
    first_copy = copy_for_frame(data, prompts[0][0])
    last_copy = copy_for_frame(data, prompts[-1][0])
    return f"""抖音文案：{first_copy['title']}。今天和猫搭子一起完成这组小故事，最后一张有点治愈。你更想看我们下一单去哪？
小红书文案：人猫搭档连续图文记录｜{first_copy['title']}到{last_copy['title']}，每一张都按顺序接着上一张拍。评论区告诉我下一组想看什么场景。"""


def build_prompt_bundle(data: dict):
    frames = frame_plan(data)
    prompts = [(frame, build_prompt(data, frame)) for frame in frames]
    if len(prompts) == 1:
        return prompts[0][1], prompts
    guide = f"""# 人猫搭档连续故事生成任务 V1.7

本任务共 {len(prompts)} 张图。

## 关键生成顺序（非常重要）
1. 第 1 张：先单独生成故事锚点。
2. 第 2 张：上传身份参考图 + 第 1 张锚点图 + 本张母版图，再生成第 2 张。
3. 第 3 张及以后：上传身份参考图 + 第 1 张锚点图 + 上一张成图 + 本张母版图，再生成当前张。
4. 不要一次性并行把所有 prompt 一起生成，否则会退化成散图。

## 抖音图文发布顺序清单
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
    scene = safe_filename(data.get("scene") or "人猫搭档")
    ratio = safe_filename(data.get("ratio") or "4:3").replace(":", "x")
    suffix = f"{clamp_count(data.get('image_count', 1))}张" if clamp_count(data.get("image_count", 1)) > 1 else "单张"
    task_dir = OUTPUT_DIR / f"{ts}_{scene}_{ratio}_{suffix}_V1_7_pipeline"
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
            "- [ ] 每张图都有标题、旁白、女生台词、猫咪台词",
            "- [ ] 文字落地模式符合预期，气泡或叠字不遮挡主体",
            "- [ ] 服装、道具、电动车、外卖箱前后连续一致",
            "- [ ] 当前图内分镜只在明确开启时出现",
            "- [ ] 每张图都是独立大图，不是拼图或多宫格",
            "- [ ] 每张图已写入 qa_result，失败项已生成 retake_prompt",
        ]
    )
    task_body = bundle_text if len(prompts) > 1 else f"```text\n{bundle_text}\n```"
    content = f"""# 人猫搭档生成任务 V1.7

## 最小入参

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

## V1.7 结构化产物

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


def normalize_defaults(data: dict) -> dict:
    data = dict(data)
    data.setdefault("preset_name", "")
    data.setdefault("story_outline", "")
    data.setdefault("scene", "送外卖正面")
    data.setdefault("output_mode", "单张大图")
    data.setdefault("ratio", "4:3")
    data.setdefault("platform", "抖音竖屏" if data.get("ratio") == "9:16" else "通用")
    data.setdefault("identity_lock", "强锁定")
    data.setdefault("bubble_mode", "无")
    data.setdefault("text_mode", "无文字")
    data.setdefault("text_render_mode", "生成空白气泡 + 后期叠字图层")
    data.setdefault("text_position", "自动")
    data.setdefault("copywriting_mode", "手动填写")
    data.setdefault("interaction_mode", "不互动")
    data.setdefault("story_template", "自动判断")
    data.setdefault("story_coherence", "强")
    data.setdefault("outfit_style_lock", "强锁定" if to_bool_text(data.get("continuous_story", "否")) == "是" else "弱锁定")
    data.setdefault("outfit_reference", "第一张锚点图 + 人物参考图" if to_bool_text(data.get("continuous_story", "否")) == "是" else "文字描述")
    data.setdefault("in_image_storyboard", "关闭")
    data.setdefault("storyboard_view", "第三人称")
    data.setdefault("storyboard_layout", "主画面 + 小视角窗口")
    data["image_count"] = clamp_count(data.get("image_count", 1))
    data["continuous_story"] = to_bool_text(data.get("continuous_story", "否"))
    if data.get("ratio") == "9:16":
        data["platform"] = "抖音竖屏"
    if data["image_count"] > 1 and data.get("output_mode") == "多镜头拼图":
        data["output_mode"] = "单张大图"
    if data.get("in_image_storyboard") != "开启":
        data["in_image_storyboard"] = "关闭"
    return data


def main():
    parser = argparse.ArgumentParser(description="人猫搭档 Prompt 生成器 V1.7")
    parser.add_argument("--input", type=str)
    parser.add_argument("--scene", type=str)
    parser.add_argument("--angle", type=str)
    parser.add_argument("--action", type=str)
    parser.add_argument("--clothing", type=str)
    parser.add_argument("--mood", type=str)
    parser.add_argument("--story-outline", dest="story_outline", type=str)
    parser.add_argument("--extra", type=str)
    parser.add_argument("--output-mode", dest="output_mode", type=str, choices=["单张大图", "多镜头拼图"])
    parser.add_argument("--ratio", type=str, choices=["4:3", "9:16"])
    parser.add_argument("--platform", type=str, choices=["通用", "抖音竖屏"])
    parser.add_argument("--image-count", dest="image_count", type=int)
    parser.add_argument("--continuous-story", dest="continuous_story", type=str, choices=CONTINUOUS_STORY_VALUES)
    parser.add_argument("--identity-lock", dest="identity_lock", type=str, choices=["强锁定", "普通锁定"])
    parser.add_argument("--bubble-mode", dest="bubble_mode", type=str, choices=BUBBLE_MODES)
    parser.add_argument("--text-mode", dest="text_mode", type=str, choices=TEXT_MODES)
    parser.add_argument("--text-render-mode", dest="text_render_mode", type=str, choices=TEXT_RENDER_MODES)
    parser.add_argument("--text-position", dest="text_position", type=str, choices=TEXT_POSITIONS)
    parser.add_argument("--copywriting-mode", dest="copywriting_mode", type=str, choices=COPYWRITING_MODES)
    parser.add_argument("--interaction-mode", dest="interaction_mode", type=str, choices=INTERACTION_MODES)
    parser.add_argument("--story-template", dest="story_template", type=str, choices=STORY_TEMPLATES)
    parser.add_argument("--story-coherence", dest="story_coherence", type=str, choices=STORY_COHERENCE_VALUES)
    parser.add_argument("--outfit-style-lock", dest="outfit_style_lock", type=str, choices=OUTFIT_STYLE_LOCKS)
    parser.add_argument("--outfit-reference", dest="outfit_reference", type=str, choices=OUTFIT_REFERENCES)
    parser.add_argument("--in-image-storyboard", dest="in_image_storyboard", type=str, choices=IN_IMAGE_STORYBOARD_VALUES)
    parser.add_argument("--storyboard-view", dest="storyboard_view", type=str, choices=STORYBOARD_VIEWS)
    parser.add_argument("--storyboard-layout", dest="storyboard_layout", type=str, choices=STORYBOARD_LAYOUTS)
    parser.add_argument("--title-text", dest="title_text", type=str)
    parser.add_argument("--narration-text", dest="narration_text", type=str)
    parser.add_argument("--human-text", dest="human_text", type=str)
    parser.add_argument("--cat-text", dest="cat_text", type=str)
    args = parser.parse_args()

    data = {}
    loaded_from_input = False
    if args.input:
        input_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
        data = load_json(input_path)
        loaded_from_input = True

    keys = [
        "scene",
        "angle",
        "action",
        "clothing",
        "mood",
        "story_outline",
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
        "story_template",
        "story_coherence",
        "outfit_style_lock",
        "outfit_reference",
        "in_image_storyboard",
        "storyboard_view",
        "storyboard_layout",
        "title_text",
        "narration_text",
        "human_text",
        "cat_text",
    ]
    for key in keys:
        val = getattr(args, key)
        if val not in [None, ""]:
            data[key] = val

    if loaded_from_input:
        errors = validate_v17_input(data, args.input)
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
