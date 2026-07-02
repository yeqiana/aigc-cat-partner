# AIGC 人猫搭档 Project V1.7

这是一个用于稳定生成“同一个女生 + 同一只白色银渐层猫”的 AIGC 图片项目包。

V1.7 的重点不是继续堆单张 Prompt 字段，而是把连续故事图拆成可检查、可返工的文本流水线：

```text
最小入参
-> story_plan
-> frame_plan[]
-> copy_plan[]
-> prompt_plan[]
-> qa_result[]
-> retake_prompt[]
```

## V1.7 修改重点

1. `tools/generate_prompt.py` 会同时输出 Markdown 任务和结构化 JSON 产物。
2. 第 1 张标记为锚点图，第 2 张引用第 1 张锚点图，第 3-N 张引用第 1 张锚点图和上一张成图。
3. 每张图都有分镜动作、视觉证据、文案、正向 Prompt、反向 Prompt、验收项和返工 Prompt。
4. 默认使用“空白气泡 + 后期叠字图层”，避免图片模型直接生成中文乱码。
5. 可在输入 JSON 中加入 `qa_failures`，手动标记失败项并生成对应返工 Prompt。

## 最快使用方式

1. 打开 `99_跨会话身份锁定包/新会话_必须上传清单.md`。
2. 新会话里先上传 3 张原始参考图。
3. 先生成 V1.7 文本流水线：

```bash
python tools/generate_prompt.py --input examples/v1_7_delivery_story_pipeline.sample.json
```

4. 打开输出目录 `06_最终可用图/生成任务/*_V1_7_pipeline/`。
5. 先检查 `story_plan.json`、`frame_plan.json`、`copy_plan.json`、`prompt_plan.json`。
6. 人工确认后，按 `prompt_task.md` 的顺序逐张生成图片。
7. 每张图生成后按 `qa_result.json` 和 `retake_prompt.json` 验收；失败先返工，不进入下一张。

## 输出产物

每次生成会创建一个 V1.7 pipeline 目录，包含：

- `input.json`
- `story_plan.json`
- `frame_plan.json`
- `copy_plan.json`
- `prompt_plan.json`
- `qa_result.json`
- `retake_prompt.json`
- `prompt_task.md`

## 示例命令

外卖连续故事 6 张：

```bash
python tools/generate_prompt.py --input examples/v1_7_delivery_story_pipeline.sample.json
```

居家治愈故事 5 张：

```bash
python tools/generate_prompt.py --input examples/v1_7_home_story_pipeline.sample.json
```

分镜和失败返工测试：

```bash
python tools/generate_prompt.py --input examples/v1_5_storyboard.sample.json
```

缺字段校验测试：

```bash
python tools/generate_prompt.py --input examples/minimal_input.sample.json
```

预期会提示缺少 V1.7 必填字段，例如 `story_template`。

## 关键提醒

连续故事稳定的关键不是“生成 6 个 prompt”，而是：

```text
第1张先出锚点
第2张用第1张锚点继续生成
第3张及以后用第1张锚点 + 上一张成图继续生成
```

默认不要开启当前图内分镜。只有某一张确实需要第一人称 / 第三人称组合时，再显式设置 `in_image_storyboard=开启`。

## 重点文件

- `tools/generate_prompt.py`
- `config/minimal_input_schema.json`
- `examples/v1_7_delivery_story_pipeline.sample.json`
- `examples/v1_7_home_story_pipeline.sample.json`
- `examples/v1_5_storyboard.sample.json`
- `入口/入口_开始这里.html`
