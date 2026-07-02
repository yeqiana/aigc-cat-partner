#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 Prompt 任务
用法：python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="批量生成 Prompt 任务")
    parser.add_argument("--input", required=True, help="批量计划 JSON")
    args = parser.parse_args()
    plan_path = (ROOT / args.input) if not Path(args.input).is_absolute() else Path(args.input)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    tasks = plan.get("tasks", [])
    if not tasks:
        print("没有 tasks")
        return
    tmp_dir = ROOT / "06_最终可用图" / "生成任务" / "_tmp_batch_inputs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for idx, task in enumerate(tasks, 1):
        p = tmp_dir / f"task_{idx:02d}.json"
        p.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "tools" / "generate_prompt.py"), "--input", str(p)], check=True)
    print(f"批量生成完成，共 {len(tasks)} 个任务。")

if __name__ == "__main__":
    main()
