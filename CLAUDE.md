# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**人猫搭档 (Human-Cat Partner)** V1.7 — AIGC 图片生成项目，用于稳定生成"同一个女生 + 同一只白色银渐层猫"的连续故事图组。

核心定位：把连续故事图拆成可检查、可返工的文本流水线，再进入真实图片生成。

## Commands

```bash
# 生成 V1.7 完整文本流水线（推荐用法）
python tools/generate_prompt.py --input examples/v1_7_delivery_story_pipeline.sample.json

# 居家治愈故事 5 张
python tools/generate_prompt.py --input examples/v1_7_home_story_pipeline.sample.json

# 分镜和失败返工测试
python tools/generate_prompt.py --input examples/v1_5_storyboard.sample.json

# 缺字段校验测试
python tools/generate_prompt.py --input examples/minimal_input.sample.json

# 批量生成（按 batch_plan 逐个任务执行）
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json

# 支持所有字段通过 CLI 参数覆盖
python tools/generate_prompt.py --scene "送外卖正面" --ratio "9:16" --image-count 6 --continuous-story "是" --story-template "外卖跑单故事"
```

项目无测试框架、无构建系统、无包依赖（纯 Python 3 标准库 + 浏览器端 HTML/JS）。

## Pipeline Architecture (V1.7)

最小入参 JSON → 经 `tools/generate_prompt.py` 处理，在 `06_最终可用图/生成任务/` 下生成 pipeline 目录，包含：

```
最小入参 JSON
  -> story_plan.json      # 故事级：ID、标题、平台、比例、张数、情绪曲线、模板
  -> frame_plan.json      # 镜头级：每帧动作、连续性说明、视觉证据、情绪、猫状态、相机角度
  -> copy_plan.json       # 文案级：每帧标题、旁白、女生气泡、猫咪气泡、评论引导
  -> prompt_plan.json     # Prompt 级：正/负向 Prompt、参考图规则、引用策略
  -> qa_result.json       # 验收：每帧通过/失败/待检查，失败项及对应返工 Prompt
  -> retake_prompt.json   # 返工：每帧失败触发条件及修复 Prompt
  -> prompt_task.md       # 人类可读的完整任务书（含生成顺序指引、验收表、发布文案）
```

### 关键生成顺序规则

- 第 1 张 → **锚点图**（单独生成，锁定开场设定）
- 第 2 张 → 参考第 1 张锚点图继续生成
- 第 3+ 张 → 参考第 1 张锚点图 + 上一张成图
- 不要一次性并行生成所有图（否则退化成散图）

## Project Structure

```
├── tools/
│   ├── generate_prompt.py        # 核心脚本：943行，V1.7 文本流水线生成器
│   └── generate_batch_plan.py    # 批量执行工具：遍历 batch_plan 逐个调用 generate_prompt.py
├── config/
│   ├── character_spec.json       # 角色视觉基因（人物+猫的固定特征）
│   ├── scenes.json               # 9 个预设场景描述（动作、服装建议、角度）
│   ├── negative_prompt.txt       # 全局 negative prompt
│   ├── reference_manifest.json   # 跨会话身份锁定参考图清单
│   └── minimal_input_schema.json # V1.7 入参 Schema 定义（含所有字段说明）
├── examples/
│   ├── v1_7_delivery_story_pipeline.sample.json  # 外卖连续故事 6 张
│   ├── v1_7_home_story_pipeline.sample.json      # 居家治愈故事 5 张
│   ├── v1_5_storyboard.sample.json               # 分镜+qa_failures 测试
│   ├── minimal_input.sample.json                 # 缺字段校验测试
│   ├── batch_plan.sample.json                    # 批量生成计划
│   ├── douyin_story_sequence.sample.json         # V1.6 抖音故事序列
│   ├── douyin_story_continuous.sample.json       # V1.6 连续故事
│   ├── audience_interaction.sample.json          # V1.6 观众互动
│   ├── bubble_text.sample.json                   # V1.6 气泡文字
│   ├── no_text.sample.json                       # V1.6 无文字
│   └── v1_5_storyboard.sample.json               # V1.5 分镜
├── 入口/
│   ├── 入口_开始这里.html         # 浏览器端表单 UI（生成最小入参 JSON）
│   ├── START_HERE.md              # 快速上手指南
│   └── 新会话启动提示词.txt        # 新会话首次发送的 Prompt
├── 00_角色设定文档/               # 角色设计文档（视觉基因表、验收标准、Prompt 模板等）
├── 01_母版图/                     # 各场景母版图目录
├── 02_多角度/                     # 多角度资产目录
├── 03_动作/                       # 动作资产目录
├── 04_服装/                       # 服装资产目录
├── 05_场景/                       # 场景资产目录
├── 06_最终可用图/
│   └── 生成任务/                  # 脚本输出目录（含 pipeline 产物）
└── 99_跨会话身份锁定包/           # 必须上传的身份参考图
```

## Core JSON Input Schema

必填字段（V1.7）：`scene`、`image_count`（1-12）、`continuous_story`（是/否）、`story_template`（自动判断/外卖跑单故事/居家治愈故事）

关键可选字段：
- `story_outline` — 独立故事情节（V1.7 新拆出，不再塞进 extra）
- `preset_name` — 常用配置模板名称（仅记录，不参与生成）
- `mood_curve` — 自定义情绪曲线数组
- `qa_failures` — 手动标记已生成图片的失败项，自动生成 retake_prompt
- `text_render_mode` — 文字落地模式（推荐"生成空白气泡 + 后期叠字图层"）
- `in_image_storyboard` — 默认关闭，开启后允许当前图内 2-3 个分镜

## Input Entry Points

1. **最简**：打开 `入口/入口_开始这里.html` → 选择模板 → 填写故事情节 → 复制 JSON → 传给脚本
2. **直接**：编辑 example JSON → `python tools/generate_prompt.py --input examples/xxx.json`
3. **CLI**：所有字段支持 `--field value` 参数

## Cross-Session Identity Lock

每次新会话必须上传 3 张原始参考图：
- `R01_human_identity_ref.jpg` — 女生身份锚点
- `R02_cat_identity_ref_front.jpg` — 猫咪正面身份锚点
- `R03_cat_identity_ref_close.jpg` — 猫咪特写身份锚点

可选母版图用于稳定场景风格。参考优先级：原始人像 > 原始猫图 > 母版图 > Prompt 场景描述。

## Important Reminders

- 默认文字落地策略是"空白气泡 + 后期叠字图层"，避免图片模型直接生成中文乱码
- 连续故事关键：不要一次性并行生成所有 prompt，必须按顺序逐张生成
- 服装道具默认强锁定：同一套服装、电动车、外卖箱在连续故事中不得随机更换
- V1.7 将故事情节从 extra 拆出为独立的 `story_outline` 字段
- 常用模板在浏览器端 localStorage 中保存，不影响项目文件
