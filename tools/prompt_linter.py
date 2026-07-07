#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Linter V3。

检查生成 Prompt 是否违反项目级规范。文本检查不能替代出图验收，但能拦截高风险指令。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NEGATION_WORDS = ["不要", "不得", "禁止", "不生成", "不直接", "不出现", "不入图", "仅配置", "Negative", "negative", "禁止项", "不是"]


def is_negative_context(line: str) -> bool:
    return any(word in line for word in NEGATION_WORDS)


def active_lines(text: str) -> list[tuple[int, str]]:
    return [(idx, line.strip()) for idx, line in enumerate(text.splitlines(), 1) if line.strip()]


def non_instruction_lines(text: str) -> set[int]:
    result: set[int] = set()
    section = ""
    for idx, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("后期叠字清单"):
            section = "post_text"
        elif line.startswith("禁止项") or "Negative Prompt" in line:
            section = "negative"
        elif line.startswith("验收清单"):
            section = "qa"
        elif re.match(r"^[^\s#-].+$", line) and line not in ["Negative Prompt"]:
            if line in ["最高优先级：人物锁定", "画风锁定", "场景锁定", "本帧剧情", "分镜要求", "文字策略"]:
                section = ""
        if section in {"post_text", "negative"}:
            result.add(idx)
    return result


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def lint_text(text: str) -> list[dict[str, str | int]]:
    issues: list[dict[str, str | int]] = []
    lines = active_lines(text)
    non_instruction = non_instruction_lines(text)

    label_patterns = [
        "人物姓名小标签",
        "姓名小标签",
        "首次出场/形象变化时标注",
        "每帧标注",
        "人物介绍浮标",
        "角色名：台词"
    ]
    for line_no, line in lines:
        if line_no in non_instruction:
            continue
        if has_any(line, label_patterns) and not is_negative_context(line) and "不标注" not in line:
            issues.append({"level": "error", "line": line_no, "code": "NO_NAME_LABELS", "message": "疑似要求生成姓名标签或首次出场标注。"})

    if "陶淮南" in text:
        blind_markers = ["盲人", "不聚焦", "视线不能准确", "根据声音转头", "听声音", "摸索", "确认位置"]
        if not has_any(text, blind_markers):
            issues.append({"level": "error", "line": 1, "code": "MISSING_BLIND_MARKERS", "message": "出现陶淮南但缺少盲人视觉/行为表现。"})
        normal_look = re.compile(r"陶淮南.*(看向|盯着|凝视|对视).*(人物|物体|碗|冰溜子|门口|镜头|观众)")
        for line_no, line in lines:
            if line_no in non_instruction:
                continue
            if normal_look.search(line) and not is_negative_context(line):
                issues.append({"level": "error", "line": line_no, "code": "BLIND_LOOKS_NORMAL", "message": "疑似让陶淮南正常看向人物或物体。"})

    xiaodong_bad = ["短发", "寸头", "黑帮", "霸总", "韩式男主", "油头"]
    for line_no, line in lines:
        if line_no in non_instruction:
            continue
        if "陶晓东" in line and has_any(line, xiaodong_bad) and not is_negative_context(line):
            issues.append({"level": "error", "line": line_no, "code": "TAO_XIAODONG_DRIFT", "message": "疑似让陶晓东发型或气质漂移。"})

    direct_text_markers = ["直接在图中生成文字", "顶部标题", "标题栏", "姓名小标签", "角色名："]
    for line_no, line in lines:
        if line_no in non_instruction:
            continue
        if has_any(line, direct_text_markers) and not is_negative_context(line) and "allow_text_in_image=true" not in line:
            issues.append({"level": "error", "line": line_no, "code": "DIRECT_TEXT_RISK", "message": "疑似要求直接生成中文文字、标题或姓名。"})

    forbidden_text = ["第几帧", "第几章", "第1幕", "当前帧", "章节标题", "顶部标题栏"]
    for line_no, line in lines:
        if line_no in non_instruction:
            continue
        if has_any(line, forbidden_text) and not is_negative_context(line):
            issues.append({"level": "error", "line": line_no, "code": "FORBIDDEN_IN_IMAGE_TEXT", "message": "疑似要求生成禁用标题/帧序文字。"})

    required_layout = ["9:16", "2-3", "主画面 + 特写小窗"]
    for marker in required_layout:
        if marker not in text:
            issues.append({"level": "error", "line": 1, "code": "MISSING_STORYBOARD_RULE", "message": f"缺少分镜/画幅要求：{marker}"})
    if not has_any(text, ["空间建立", "动作推进"]) or not has_any(text, ["特写", "手部", "道具"]):
        issues.append({"level": "error", "line": 1, "code": "MISSING_PANEL_SHOTS", "message": "缺少空间建立、动作推进、手部/道具/反应特写要求。"})

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 Prompt 是否违反项目规范")
    parser.add_argument("--input", required=True, help="Prompt Markdown/TXT 文件")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args()

    input_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
    text = input_path.read_text(encoding="utf-8")
    issues = lint_text(text)

    if args.json:
        import json
        print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False, indent=2))
    else:
        if not issues:
            print("PASS: 未发现项目规范违规。")
        else:
            print("FAIL: 发现项目规范风险：")
            for item in issues:
                print(f"- [{item['level']}] {item['code']} line {item['line']}: {item['message']}")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
