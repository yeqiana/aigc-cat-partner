# 通用剧情连载系统 V2.0

这是一个用于 AIGC 剧情向图文连载的通用项目包。

当前版本的重点不是绑定某个具体 IP，而是沉淀一套可复用的文本流水线：

```text
最小入参
-> story_plan.json
-> frame_plan.json
-> copy_plan.json
-> prompt_plan.json
-> qa_result.json
-> retake_prompt.json
-> prompt_task.md
```

## 核心原则

1. 保留连载生产方法，不保留旧 IP 内容。
2. 第 1 张先生成锚点图，第 2 张引用锚点图，第 3-N 张引用锚点图和上一张成图。
3. 每张图都有动作、视觉证据、文案、Prompt、验收项和返工 Prompt。
4. 默认使用"空白气泡 + 后期叠字图层"，避免图片模型直接生成中文乱码。
5. Negative Prompt 拆分为通用负面词和项目专属负面词。

## 最快使用方式

```bash
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json
```

输出目录：

```text
outputs/batch_plans/{timestamp}_{scene}_{ratio}_{count}张_V2_pipeline/
```

先检查结构化产物，再进入真实图片生成。

## 批量生成

```bash
python tools/generate_batch_plan.py --input examples/batch_plan.sample.json
```

批量工具会逐个调用 `tools/generate_prompt.py`，生成多组任务目录。

## 目录结构

```
├── tools/                    # 核心生成工具 + 辅助工具
│   ├── generate_prompt.py
│   ├── generate_batch_plan.py
│   ├── extract_chapter_info.py   # 可选：从原文抽取信息
│   └── validate_config.py        # 可选：验证配置完整性
│
├── config/                   # 配置定义
│   ├── series_input_schema.json
│   ├── minimal_input_schema.json
│   ├── story_templates.json
│   ├── character_spec.json
│   ├── world_spec.json
│   ├── scenes.json
│   ├── reference_manifest.json
│   ├── negative_prompt_common.txt
│   ├── negative_prompt_project.txt
│   └── negative_prompt.txt
│
├── examples/                 # 输入样例
│   ├── generic_suspense_series.sample.json
│   ├── character_image.sample.json
│   ├── chapter_scene.sample.json
│   └── batch_plan.sample.json
│
├── prompts/                  # 生成出来的提示词（按用途分类）
│   ├── character/
│   ├── scene/
│   ├── chapter/
│   └── batch/
│
├── outputs/                  # 最终产物
│   ├── images/
│   ├── markdown/
│   ├── batch_plans/
│   └── logs/
│
├── references/               # 参考图与母版图
│   ├── style/
│   ├── character_master/
│   ├── scene_style/
│   └── composition/
│
├── 入口/
│   └── START_HERE.md
│
└── 00_设定文档/
    ├── 通用剧情连载系统_沉淀复用实施方案.md
    ├── 人物设定_陈年烈狗.md
    ├── 人物出场表_逐章分析.md
    ├── 场景设定_陈年烈狗.md
    └── 原文/ (1~126章)
```

## 重点文件

| 文件 | 说明 |
|---|---|
| `tools/generate_prompt.py` | 通用剧情连载 Prompt 生成器 |
| `tools/generate_batch_plan.py` | 批量任务生成工具 |
| `tools/validate_config.py` | JSON 配置完整性校验 |
| `tools/extract_chapter_info.py` | 正文结构化信息抽取 |
| `config/series_input_schema.json` | 通用连载入参 Schema |
| `config/story_templates.json` | 通用剧情模板 |
| `config/negative_prompt_common.txt` | 通用负面词 |
| `config/negative_prompt_project.txt` | 项目专属负面词占位 |
| `config/character_spec.json` | 新角色视觉基因模板 |
| `config/world_spec.json` | 新世界观设定模板 |
| `入口/START_HERE.md` | 新项目使用入口 |
| `examples/generic_suspense_series.sample.json` | 通用悬念连载样例 |

## 新项目必须先填写

- `project_name`
- `story_template`
- `story_outline`
- `visual_gene_summary`
- `worldview_summary`
- `style_prompt`
- `key_props`
- `project_negative_prompt`

## 关键提醒

连续故事稳定的关键不是"生成多个 prompt"，而是：

```text
第1张先出锚点
第2张用第1张锚点继续生成
第3张及以后用第1张锚点 + 上一张成图继续生成
```

不要一次性并行生成所有图片，否则会退化成同主题散图。
