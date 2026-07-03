#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可选工具：从正文（00_设定文档/原文/）中抽取人物、场景、情绪信息。

用法：
  python tools/extract_chapter_info.py --chapter 第1章
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT / "00_设定文档" / "原文"


def extract_characters(text: str) -> list[str]:
    """简单人物抽取示例（可扩展为 LLM 调用）"""
    # 用「」或【】或：引出的名字
    names = set()
    for m in re.finditer(r'[「「【【]([^」」】】]{1,8})[」」】】]', text):
        names.add(m.group(1))
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description="从原文抽取结构化信息")
    parser.add_argument("--chapter", help="章节名，例如 第1章")
    args = parser.parse_args()

    if args.chapter:
        path = CHAPTERS_DIR / f"{args.chapter}.txt"
        if not path.exists():
            raise SystemExit(f"未找到：{path}")
        text = path.read_text(encoding="utf-8")
        chars = extract_characters(text)
        print(json.dumps({"chapter": args.chapter, "characters": chars}, ensure_ascii=False, indent=2))
    else:
        print(f"用法：python {__file__} --chapter 第1章")


if __name__ == "__main__":
    main()
