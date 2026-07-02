#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人猫搭档 Prompt 生成入口 V1.4

修复重点：
1. 连续情节不再只是“同角色换不同场景”，而是“前后承接的一段故事”。
2. 输出任务中明确要求按顺序生成，第 2 张开始使用“首张锚点 + 上一张成图”继续生成。
3. 支持故事模板：自动判断 / 外卖跑单故事 / 居家治愈故事。
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "06_最终可用图" / "生成任务"
BUBBLE_MODES = ["无", "人物气泡", "猫咪气泡", "双气泡", "旁白标题"]
TEXT_MODES = ["无文字", "直接生成文字", "空白气泡后期加字"]
TEXT_POSITIONS = ["自动", "顶部标题区", "人物旁边", "猫咪旁边", "底部字幕区"]
COPYWRITING_MODES = ["手动填写", "自动根据情节生成"]
INTERACTION_MODES = ["不互动", "看向观众", "提问互动", "评论引导", "点赞关注", "选择投票"]
CONTINUOUS_STORY_VALUES = ["否", "是"]
STORY_TEMPLATES = ["自动判断", "外卖跑单故事", "居家治愈故事"]
STORY_COHERENCE_VALUES = ["普通", "强"]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def safe_filename(text: str) -> str:
    bad = '<>:"/\|?*
	'
    for ch in bad:
        text = text.replace(ch, "_")
    return text.strip()[:80] or "task"

def short_text(text: str, max_chars: int = 12) -> str:
    return (text or "").strip()[:max_chars]

def to_bool_text(value) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    value = str(value or "否").strip()
    return "是" if value in ["是", "true", "True", "1", "yes", "YES"] else "否"

def clamp_count(value) -> int:
    try: n = int(value)
    except Exception: n = 1
    return max(1, min(12, n))


def clothing_description(clothing: str) -> str:
    presets = {
        "白T互印头像": "人和猫都穿简约白色 T 恤。女生的白色 T 恤胸口印着猫的脸，图案占胸口大面积，保留猫的头部和脖子。猫的白色 T 恤胸口印着女生的脸，图案只保留女生头部，不要脖子。",
        "居家休闲服": "女生穿奶油白或浅咖色居家休闲上衣，柔软自然，有真实布料褶皱。猫穿协调的浅色小衣服，保持可爱但不过度拟人。",
        "外卖职业服": "女生穿白色 T 恤加简约外卖马甲，颜色以奶油白、浅咖、黑色边线为主。猫穿迷你外卖马甲，与女生形成搭档感。可以有简单爪印标志，但不要复杂乱码文字。"
    }
    return presets.get(clothing, clothing or presets["居家休闲服"])

BASE_COPY = {
    "送外卖正面": {"title": "第1单出发", "human": "准备出发", "cat": "我坐稳啦"},
    "取外卖侧面": {"title": "取餐完成", "human": "马上送到", "cat": "袋子好香"},
    "骑车45度": {"title": "路上赶单", "human": "稳一点", "cat": "我看路"},
    "楼下抬头": {"title": "先确认楼层", "human": "就是这栋", "cat": "往上看"},
    "爬楼疲惫": {"title": "还剩几层", "human": "快到了", "cat": "累鼠啦"},
    "送达门口": {"title": "这一单送达", "human": "已送到", "cat": "终于到了"},
    "收工回家": {"title": "今日收工", "human": "辛苦啦", "cat": "加餐吗"},
    "沙发绿植正面": {"title": "今日搭子营业", "human": "坐好啦", "cat": "我很乖"},
    "沙发绿植45度": {"title": "抱住小搭子", "human": "别乱动", "cat": "知道啦"},
}
INTERACTION_COPY = {
    "不互动": {},
    "看向观众": {"title": "今天跟我们跑一单", "human": "跟上哦", "cat": "看我表现"},
    "提问互动": {"title": "你会点哪一单？", "human": "这单送哪儿", "cat": "你选吧"},
    "评论引导": {"title": "评论区说说你最爱吃啥", "human": "我去取", "cat": "我来送"},
    "点赞关注": {"title": "关注人猫送达", "human": "准时送到", "cat": "点个赞嘛"},
    "选择投票": {"title": "接着跑还是先休息？", "human": "听你的", "cat": "我想休息"}
}

DELIVERY_STORY = [
    {"scene":"送外卖正面","angle":"正面中景","action":"女生在街边整理外卖箱，准备出发，猫稳稳坐在前篮里","extra":"第1幕：故事开场。还没出发，状态轻松，电动车和外卖箱完整干净。","state":"开始跑单，精神比较足，外卖箱整齐，手上暂时没有餐袋。"},
    {"scene":"取外卖侧面","angle":"侧面中景","action":"女生在取餐窗口接过外卖袋，猫从车篮里好奇地看着袋子","extra":"第2幕：取餐。道具推进：现在已经拿到第一单外卖袋。","state":"承接上一张，已经出发并成功到店，手里出现外卖袋。"},
    {"scene":"骑车45度","angle":"前方45度中景","action":"女生骑车或扶车前进，外卖袋和外卖箱一起出现在车上，猫迎着风看前方","extra":"第3幕：路上。状态推进：头发和衣角有风，画面更有动感。","state":"承接上一张，已经离开店铺，正在去送餐的路上。外卖袋不能消失。"},
    {"scene":"楼下抬头","angle":"仰拍中景","action":"女生在楼下停好车，提着外卖袋抬头看楼，猫在前篮或背包里探头","extra":"第4幕：到楼下确认楼层。","state":"承接上一张，已经到达收餐地址楼下。电动车停在附近，女生手里仍提着外卖袋。"},
    {"scene":"爬楼疲惫","angle":"背面45度 / 回头视角","action":"女生提着外卖袋往楼上走，背着外卖箱，猫在宠物背包或旁边探头","extra":"第5幕：爬楼。情绪推进：开始有点累。","state":"承接上一张，正在上楼送餐，已经明显更累，但还没送达。"},
    {"scene":"送达门口","angle":"侧前方中景","action":"女生在住户门口送达外卖，猫在旁边探头看着，动作自然","extra":"第6幕：送达。剧情推进：这一单完成。","state":"承接上一张，已经到达门口，外卖袋准备递出或刚刚放下。"},
    {"scene":"爬楼疲惫","angle":"正面低角度","action":"女生在楼梯平台或过道短暂休息，猫坐在旁边一起发呆","extra":"第7幕：送完后一小会儿休息。","state":"承接上一张，外卖袋已经送出，不要再出现完整待送外卖袋。"},
    {"scene":"收工回家","angle":"正面半身","action":"女生和猫回到沙发上休息，女生轻轻搂着猫，氛围放松","extra":"第8幕：收工。像一天结束后的结尾图。","state":"承接上一张，回家收工，情绪从疲惫过渡到放松。"}
]
HOME_STORY = [
    {"scene":"沙发绿植正面","angle":"正面半身","action":"女生和猫坐在沙发上看镜头","extra":"第1幕：开场合照。","state":"故事开场，室内温馨。"},
    {"scene":"沙发绿植45度","angle":"45度半身","action":"女生侧身抱猫，猫靠在怀里","extra":"第2幕：抱猫互动。","state":"承接上一张，更亲密。"},
    {"scene":"沙发绿植正面","angle":"正面近景","action":"重点展示互印头像 T 恤","extra":"第3幕：展示衣服图案。","state":"承接上一张，重点切到衣服。"},
    {"scene":"沙发绿植45度","angle":"45度近景","action":"猫咪抢镜，女生轻轻扶着","extra":"第4幕：猫咪抢镜。","state":"承接上一张，猫成为视觉重点。"},
    {"scene":"收工回家","angle":"正面半身","action":"女生和猫一起放松休息","extra":"第5幕：结尾纪念照。","state":"结尾收束，氛围平静。"}
]

def auto_copy(scene_name: str, interaction_mode: str) -> dict:
    base = dict(BASE_COPY.get(scene_name, BASE_COPY["沙发绿植正面"]))
    if interaction_mode != "不互动":
        base.update({k: v for k, v in INTERACTION_COPY.get(interaction_mode, {}).items() if v})
    return {k: short_text(v, 14) for k, v in base.items()}


def audience_interaction_description(interaction_mode: str) -> str:
    mapping = {
        "不互动": "不做观众互动，保持自然生活感。",
        "看向观众": "需要建立视线互动：女生和猫至少一个明确看向镜头。",
        "提问互动": "需要有轻微提问感：标题或气泡适合抛出问题。",
        "评论引导": "需要评论互动感：标题或气泡引导观众在评论区回复。",
        "点赞关注": "需要轻微点赞关注引导，但不要过度营销。",
        "选择投票": "需要投票互动感：给出 A/B 选择。"
    }
    return mapping.get(interaction_mode, mapping["不互动"])


def bubble_text_description(data: dict, scene_name: str) -> str:
    bubble_mode = data.get("bubble_mode") or "无"
    text_mode = data.get("text_mode") or "无文字"
    position = data.get("text_position") or "自动"
    copy = auto_copy(scene_name, data.get("interaction_mode") or "不互动")
    if bubble_mode == "无" or text_mode == "无文字":
        return "不生成任何气泡、字幕、标题文字或贴纸文字。"
    if text_mode == "空白气泡后期加字":
        return f"生成 {bubble_mode}，但只保留空白气泡/空白标题贴纸，不直接生成文字。推荐后期加字：标题『{copy['title']}』，女生『{copy['human']}』，猫咪『{copy['cat']}』。位置：{position}。"
    details = [f"位置：{position}。", f"推荐标题：{copy['title']}。"]
    if bubble_mode in ["人物气泡", "双气泡"]: details.append(f"女生气泡：{copy['human']}。")
    if bubble_mode in ["猫咪气泡", "双气泡"]: details.append(f"猫咪气泡：{copy['cat']}。")
    if bubble_mode == "旁白标题": details.append(f"标题：{copy['title']}。")
    details.append("如果模型无法稳定出中文，请退回空白气泡后期加字。")
    return "允许生成短文字。" + "".join(details)


def reference_block(scene_name: str) -> str:
    manifest = load_json(CONFIG_DIR / "reference_manifest.json")
    required = "
".join([f"- {x}" for x in manifest.get("required_each_new_session", [])])
    optional = manifest.get("optional_master_references", {}).get(scene_name, "按本次场景选择对应母版图")
    return f"""【跨会话身份锁定｜新会话必须执行】
每次新开会话或切换工具时，必须先上传身份参考图，再发送本 Prompt。

必传身份参考图：
{required}

本场景建议额外上传母版参考图：
- {optional}
"""


def choose_story_template(data: dict) -> str:
    tpl = data.get("story_template") or "自动判断"
    if tpl != "自动判断":
        return tpl
    scene = data.get("scene") or "送外卖正面"
    if scene in ["送外卖正面","取外卖侧面","骑车45度","楼下抬头","爬楼疲惫","送达门口"]:
        return "外卖跑单故事"
    return "居家治愈故事"


def frame_plan(data: dict) -> list[dict]:
    data = normalize_defaults(data)
    count = clamp_count(data.get("image_count", 1))
    continuous = to_bool_text(data.get("continuous_story", "否"))
    scene_name = data.get("scene") or "沙发绿植正面"
    if count <= 1:
        return [{"index":1, "total":1, "scene":scene_name, "story_phase":"单张图", "state":"单张图无需剧情推进。"}]
    if continuous == "是":
        tpl = choose_story_template(data)
        base = DELIVERY_STORY if tpl == "外卖跑单故事" else HOME_STORY
        frames=[]
        for i in range(count):
            src = dict(base[i % len(base)])
            src["index"]=i+1; src["total"]=count
            src["story_template"]=tpl
            src["story_phase"]=src.get("extra","").split('：')[0] if '：' in src.get('extra','') else f"第{i+1}幕"
            src["prev_phase"] = "无，故事开场" if i==0 else frames[i-1]["story_phase"]
            src["next_hint"] = (base[(i+1) % len(base)].get("extra","下一幕继续").split('：')[0] if i+1 < count else "故事收束")
            frames.append(src)
        return frames
    # non-continuous variants
    angles=["正面中景","前方45度中景","侧面中景","近景半身","背面45度 / 回头视角","低角度中景"]
    return [{"index":i+1,"total":count,"scene":scene_name,"angle":angles[i%len(angles)],"action":data.get("action") or "保持同主题小变化","extra":f"第{i+1}张同主题变体，只换角度和细节，不要求故事推进。","story_phase":"同主题变体","state":"保持同主题。"} for i in range(count)]


def composition_description(data: dict, angle: str, idx: int, total: int) -> str:
    ratio = data.get("ratio") or "4:3"
    if ratio == "9:16" or data.get("platform") == "抖音竖屏":
        return f"9:16，单张大图，抖音竖屏比例。当前是第 {idx}/{total} 张。主体居中偏上，人和猫完整清晰可见。顶部预留标题安全区，底部预留字幕安全区。不要拼图、不要多宫格、不要分镜框。镜头角度：{angle}。"
    return f"4:3，中景/半身为主，镜头角度：{angle}。"


def continuity_block(data: dict, frame: dict) -> str:
    total = frame.get("total",1)
    idx = frame.get("index",1)
    if total <= 1 or to_bool_text(data.get("continuous_story","否")) != "是":
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
    extra = frame.get("extra") or data.get("extra") or ""
    human = spec["human_visual_gene"]
    cat = spec["cat_visual_gene"]
    style = spec["style"]
    idx, total = frame.get("index",1), frame.get("total",1)

    return f"""基于《人猫搭档 AIGC 统一出图规范 V1.4》，保持同一个女生、同一只白色银渐层猫、同一套真实拍立得生活摄影风格，只改变本次场景、动作、角度和剧情推进，不改变核心视觉基因。

{reference_block(scene_name)}

【连续故事生成说明】
{continuity_block(data, frame)}

【身份锁定】
使用参考图锁定同一个年轻女生和同一只白色银渐层猫。
女生固定视觉基因：{human['age']}，{human['face']}，{human['hair']}，{human['glasses']}，{human['body']}。
猫固定视觉基因：{cat['breed']}，{cat['face']}，{cat['fur']}，{cat['expression']}。

【故事主线】
故事模板：{frame.get('story_template', choose_story_template(data))}
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

【服装】
{clothing_description(clothing)}

【观众互动】
{audience_interaction_description(data.get('interaction_mode') or '不互动')}

【气泡与文字】
{bubble_text_description(data, scene_name)}

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


def build_prompt_bundle(data: dict):
    frames = frame_plan(data)
    prompts = [(f, build_prompt(data, f)) for f in frames]
    if len(prompts)==1:
        return prompts[0][1], prompts
    guide = f"""# 人猫搭档连续故事生成任务 V1.4

本任务共 {len(prompts)} 张图。

## 关键生成顺序（非常重要）
1. 第 1 张：先单独生成故事锚点。
2. 第 2 张：上传身份参考图 + 第 1 张锚点图 + 本张母版图，再生成第 2 张。
3. 第 3 张及以后：上传身份参考图 + 第 1 张锚点图 + 上一张成图 + 本张母版图，再生成当前张。
4. 不要一次性并行把所有 prompt 一起生成，否则会退化成散图。

## 目标
让多张竖屏大图成为前后承接的一个故事，而不是同一个角色在不同背景里的几张散图。
"""
    parts=[guide]
    for f,p in prompts:
        parts.append(f"

---

## 第 {f['index']}/{f['total']} 张 Prompt

```text
{p}
```")
    return "
".join(parts).strip(), prompts


def write_task(data: dict, bundle_text: str, prompts):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    scene = safe_filename(data.get("scene") or "人猫搭档")
    ratio = safe_filename(data.get("ratio") or "4:3").replace(":", "x")
    suffix = f"{clamp_count(data.get('image_count',1))}张" if clamp_count(data.get('image_count',1))>1 else "单张"
    out = OUTPUT_DIR / f"{ts}_{scene}_{ratio}_{suffix}_V1_4_Prompt.md"
    checklist = "
".join([
        "- [ ] 第 1 张已先单独生成为锚点图",
        "- [ ] 第 2 张开始已带上“第 1 张锚点 + 上一张成图”继续生成",
        "- [ ] 多张图之间能看出明确剧情推进，而不是同角色换背景",
        "- [ ] 服装、道具、电动车、外卖箱前后连续一致",
        "- [ ] 人脸一致：同一个女生",
        "- [ ] 猫脸一致：同一只白色银渐层猫",
        "- [ ] 每张图都是独立大图，不是拼图或多宫格",
    ])
    content=f"# 人猫搭档生成任务 V1.4

## 最小入参

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

## 生成任务

{bundle_text if len(prompts)>1 else '```text
'+bundle_text+'
```'}

## 验收清单
{checklist}
"
    out.write_text(content, encoding='utf-8')
    return out


def normalize_defaults(data: dict) -> dict:
    data=dict(data)
    data.setdefault("scene","送外卖正面")
    data.setdefault("output_mode","单张大图")
    data.setdefault("ratio","4:3")
    data.setdefault("platform","抖音竖屏" if data.get("ratio")=="9:16" else "通用")
    data.setdefault("identity_lock","强锁定")
    data.setdefault("bubble_mode","无")
    data.setdefault("text_mode","无文字")
    data.setdefault("text_position","自动")
    data.setdefault("copywriting_mode","手动填写")
    data.setdefault("interaction_mode","不互动")
    data.setdefault("story_template","自动判断")
    data.setdefault("story_coherence","强")
    data["image_count"]=clamp_count(data.get("image_count",1))
    data["continuous_story"]=to_bool_text(data.get("continuous_story","否"))
    if data.get("ratio")=="9:16": data["platform"]="抖音竖屏"
    if data["image_count"]>1 and data.get("output_mode") == "多镜头拼图": data["output_mode"] = "单张大图"
    return data


def main():
    p=argparse.ArgumentParser(description="人猫搭档 Prompt 生成器 V1.4")
    p.add_argument("--input", type=str)
    p.add_argument("--scene", type=str); p.add_argument("--angle", type=str); p.add_argument("--action", type=str)
    p.add_argument("--clothing", type=str); p.add_argument("--mood", type=str); p.add_argument("--extra", type=str)
    p.add_argument("--output-mode", dest="output_mode", type=str, choices=["单张大图","多镜头拼图"])
    p.add_argument("--ratio", type=str, choices=["4:3","9:16"]); p.add_argument("--platform", type=str, choices=["通用","抖音竖屏"])
    p.add_argument("--image-count", dest="image_count", type=int); p.add_argument("--continuous-story", dest="continuous_story", type=str, choices=CONTINUOUS_STORY_VALUES)
    p.add_argument("--identity-lock", dest="identity_lock", type=str, choices=["强锁定","普通锁定"])
    p.add_argument("--bubble-mode", dest="bubble_mode", type=str, choices=BUBBLE_MODES)
    p.add_argument("--text-mode", dest="text_mode", type=str, choices=TEXT_MODES)
    p.add_argument("--text-position", dest="text_position", type=str, choices=TEXT_POSITIONS)
    p.add_argument("--copywriting-mode", dest="copywriting_mode", type=str, choices=COPYWRITING_MODES)
    p.add_argument("--interaction-mode", dest="interaction_mode", type=str, choices=INTERACTION_MODES)
    p.add_argument("--story-template", dest="story_template", type=str, choices=STORY_TEMPLATES)
    p.add_argument("--story-coherence", dest="story_coherence", type=str, choices=STORY_COHERENCE_VALUES)
    args=p.parse_args()
    data={}
    if args.input:
        input_path=(ROOT/args.input) if not Path(args.input).is_absolute() else Path(args.input)
        data=load_json(input_path)
    for key in ["scene","angle","action","clothing","mood","extra","output_mode","ratio","platform","image_count","continuous_story","identity_lock","bubble_mode","text_mode","text_position","copywriting_mode","interaction_mode","story_template","story_coherence"]:
        val=getattr(args,key)
        if val not in [None,""]: data[key]=val
    data=normalize_defaults(data)
    bundle,prompts=build_prompt_bundle(data)
    out=write_task(data,bundle,prompts)
    print("已生成 Prompt 任务：")
    print(out)
    print("
--- Prompt 预览 ---
")
    print(bundle)

if __name__ == "__main__":
    main()
