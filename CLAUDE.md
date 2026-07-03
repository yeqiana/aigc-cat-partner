# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

通用剧情连载系统 V2.0 — AIGC 剧情向图文连载的文本流水线。核心设计：**先生成可审查/可修复的结构化文本制品，再进入图片生成**。

```text
最小入参 → story_plan → frame_plan → copy_plan → prompt_plan → qa_result → retake_prompt → prompt_task.md
```

纯 Python 标准库，无三方依赖。

## Commands

```bash
# 单任务生成
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json

# 命令行参数覆盖（可部分覆盖 JSON 中的字段）
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json --image-count 4 --scene "雨中车站"

# 批量生成
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json

# 修改流水线后的验证
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
```

## Pipeline Architecture

### 入口点

`tools/generate_prompt.py` 的 `main()`：
1. 解析 `--input JSON` + 可选 `--key value` 命令行覆盖
2. 校验必填字段（`scene`、`image_count`、`continuous_story`、`story_template`）
3. 填充默认值（10+ 个字段从 schema defaults 或硬编码兜底）
4. 调用 `build_prompt_bundle(data)` 进入流水线

### 流水线六阶段（函数级调用链）

```
build_prompt_bundle(data)
├── frame_plan(data)              → list[dict]   # 分帧规划
├── build_prompt(data, frame)     → str          # 逐帧生成 Prompt
├── build_pipeline_artifacts(data, frames, prompts)
│   ├── build_story_plan(data)       → dict       # ❶ 故事规划
│   ├── build_frame_plan(data,frames)→ list[dict] # ❷ 分帧规划
│   ├── build_copy_plan(data,frames) → list[dict] # ❸ 文案规划
│   ├── build_prompt_plan(data,frames,prompts) → list[dict] # ❹ 提示词规划
│   ├── build_qa_result(data,frames) → list[dict] # ❺ QA 验收
│   └── build_retake_prompt(data,frames) → list[dict] # ❻ 返工提示
└── write_task(data, bundle, prompts) → 写入 prompt_task.md + 6 个 JSON
```

### 两种生成模式

| 模式 | `continuous_story` | 行为 |
|---|---|---|
| **连续故事** | `"是"` | 帧来自 `story_templates.json` 循环，帧间有承接关系，角色/道具/情绪逐帧推进 |
| **同主题变体** | `"否"` | 帧为独立变体（角度轮转），不强制作剧情承接，适合同主题散图 |

### 帧循环规则（连续模式）

当 `image_count > len(template.frames)` 时，帧按 `frames[i % len(frames)]` 循环，`story_phase` 依次编号（第1幕、第2幕…）。每帧自动推算 `prev_phase`（上一帧阶段）和 `next_hint`（下一帧提示）。

### 锚帧引用规则（核心）

| 帧位置 | `generation_type` | `required_references` |
|---|---|---|
| Frame 1 | `anchor` | 身份参考图 + 风格参考图 + 场景母版图 |
| Frame 2 | `continuation` | 身份参考图 + 风格参考图 + **第 1 张锚点图** + 场景母版图 |
| Frame 3+ | `continuation` | 身份参考图 + 风格参考图 + 第 1 张锚点图 + **上一张成图** + 场景母版图 |
| 非连续 | `variant` | 身份参考图 + 风格参考图 + 场景母版图 |

引用优先级：身份/角色设定 > 风格/世界观设定 > 第 1 张锚点图 > 上一张成图 > 当前 Prompt。

### QA → Retake 反馈环

```
qa_result.json       ← 每帧状态（待检查/通过/不通过）+ 失败项 + 原因
retake_prompt.json   ← 自动生成的返工 Prompt + 必须保留的参考图清单
```

- QA 不通过时保留参考图重新生成，不重新设计角色/服装/背景
- 内置 8 个通用验收项：角色一致、风格一致、世界观一致、造型道具连续、动作清楚、情绪推进、文字安全、平台适配

## Config Hierarchy

| 配置文件 | 作用 | 解析时机 |
|---|---|---|
| `series_input_schema.json` | 定义必填字段 + 默认值 + 字段描述 | `validate_input()` + `normalize_defaults()` |
| `story_templates.json` | 按模板名存储帧序列 + 情绪曲线 | `choose_story_template()` → `template_frames()` |
| `character_spec.json` | 角色视觉基因模板（写新项目时参考） | 仅人工填写，不被运行时直接读取 |
| `world_spec.json` | 世界/风格模板（含 `visual_gene_template` 兜底） | `build_prompt()` 中作为 `visual_gene`/`worldview`/`style` 的兜底值 |
| `scenes.json` | 场景配置数据 | 仅人工填写 |
| `reference_manifest.json` | 跨会话身份/风格引用清单 | 仅人工填写 |
| `negative_prompt_common.txt` | 通用负向提示词 | `negative_prompt()` → 合并 common + project + 行内 |
| `negative_prompt_project.txt` | 项目特定负向提示词 | `negative_prompt()` → 同上 |
| `negative_prompt.txt` | 负向提示词汇总 | 人工参考 |

**默认值解析顺序**（优先级从高到低）：
1. `--key value` 命令行参数
2. JSON 输入文件中的值
3. `series_input_schema.json` 中 `defaults` 块的字段
4. `normalize_defaults()` 中的硬编码兜底

## Key Input Fields

必填（4 个）：`scene`、`image_count`、`continuous_story`、`story_template`

高频使用字段：

| 字段 | 说明 | 默认值 |
|---|---|---|
| `story_outline` | 完整故事线（不是塞进 extra） | `""` |
| `visual_gene_summary` | 角色视觉特征 | `world_spec.json` 兜底 |
| `worldview_summary` | 世界观边界 | `world_spec.json` 兜底 |
| `style_prompt` | 目标画风 | `world_spec.json` 兜底 |
| `emotional_progression` | 情绪推进逻辑 | `""` |
| `extra` | 补充约束/禁忌项 | `""` |
| `mood_curve` | 自定义情绪曲线 | `story_templates.json` 中模板自带 |
| `project_negative_prompt` | 行内项目负向提示词 | `""` |
| `bubble_mode` | `无/单角色气泡/多角色气泡/旁白标题` | `多角色气泡` |
| `text_render_mode` | `生成空白气泡 + 后期叠字图层`（默认） | 固定推荐 |
| `interaction_mode` | `不互动/看向观众/提问互动/评论引导/点赞关注/选择投票` | `评论引导` |
| `outfit_style_lock` | `不锁定/弱锁定/强锁定` | 连续故事默认强锁定 |
| `in_image_storyboard` | 是否开启图内分镜 | `关闭` |

## Story Templates

内置两个模板（`config/story_templates.json`）：

| 模板名 | 情绪曲线 | 适用场景 |
|---|---|---|
| `通用悬念连载` | 平静→疑惑→试探→紧张→反转→余味 | 悬疑/推理/惊悚 |
| `日常反转连载` | 轻松→好奇→误会→尴尬→反转→松弛 | 日常/轻喜剧/反转 |

新增模板：在 `story_templates.json` 中添加新 key，结构同现有模板（`description` + `mood_curve` + `frames[]`）。或者在输入中使用 `custom_frames` 数组完全覆盖模板帧。

## Batch System

`tools/generate_batch_plan.py` 很简单（仅 33 行）：
- 读取 `batch_plan.sample.json` 中的 `tasks[]` 数组
- 每个 task 写入临时 JSON 文件
- 调用 `subprocess.run` 执行 `generate_prompt.py`
- 无并行，按顺序逐个生成

```json
// batch_plan.sample.json 结构
{
  "tasks": [
    { "scene": "...", "image_count": 6, ... },
    { "scene": "...", "image_count": 4, ... }
  ]
}
```

## Output Structure

```
outputs/batch_plans/
├── {timestamp}_{scene}_{ratio}_{count}张_V2_pipeline/
│   ├── prompt_task.md        # 完整生成任务文档
│   ├── input.json            # 标准化入参
│   ├── story_plan.json       # ❶ 故事规划
│   ├── frame_plan.json       # ❷ 分帧规划
│   ├── copy_plan.json        # ❸ 文案规划
│   ├── prompt_plan.json      # ❹ 提示词规划
│   ├── qa_result.json        # ❺ QA 验收
│   └── retake_prompt.json    # ❻ 返工提示
```

## Core Rules

- **保持六阶段输出稳定**：`story_plan / frame_plan / copy_plan / prompt_plan / qa_result / retake_prompt` 的 schema 不能随意更改
- **禁止并行生成**：连续故事必须逐帧生成，不能一次性把所有 prompt 发送给图片模型
- **文字策略**：默认空白气泡 + 后期叠字，避免图片模型生成中文乱码
- **负向提示词分离**：`common` + `project` 分开维护，不改公用文件
- **IP 隔离**：通用层不携带旧 IP 内容（人猫搭档、外卖故事等）
- **不删历史资产**：旧项目文件保留为历史参考，除非用户明确要求迁移或删除
- **不引入新依赖**：只用 Python 标准库
- **小步可逆修改**：改动 `generate_prompt.py` 后务必用两个 sample 做 P0 验证
