# AIGC 人猫搭档 Project V1.5

这是一个用于稳定生成“同一个女生 + 同一只白色银渐层猫”的 AIGC 图片项目包。

## V1.5 修改重点

V1.5 继承 V1.4 的连续故事顺序生成机制，并补充三项能力：

1. `text_render_mode`：输出每张图的标题、旁白、女生台词、猫咪台词，并支持“空白气泡 + 后期叠字图层”。
2. `outfit_style_lock` / `outfit_reference`：锁定同一组图的服装风格、颜色、配饰和关键道具。
3. `in_image_storyboard`：当前图内分镜默认关闭，只有明确开启时才允许 2-3 个分镜或视角窗口。

任务文件会额外生成：

- 抖音图文发布顺序清单
- 每张图验收表
- 失败返工 Prompt
- 上一张不够连贯时的修复 Prompt
- 抖音 / 小红书平台发布文案

## 最快使用方式

1. 打开 `99_跨会话身份锁定包/新会话_必须上传清单.md`。
2. 新会话里先上传 3 张原始参考图。
3. 打开 `入口/入口_开始这里.html`。
4. 选择：`比例=9:16`、`生成张数>=3`、`连续情节=是`。
5. 推荐开启：`服装风格锁定=强锁定`、`文字落地模式=生成空白气泡 + 后期叠字图层`。
6. 按任务文件顺序一张张生成，不要一次并行生成全部图片。
7. 第 2 张开始，把“第 1 张锚点 + 上一张成图 + 本张母版图”继续作为参考图上传。

## 连续故事推荐命令

```bash
python tools/generate_prompt.py --scene 送外卖正面 --ratio 9:16 --platform 抖音竖屏 --image-count 6 --continuous-story 是 --story-template 外卖跑单故事 --story-coherence 强 --bubble-mode 双气泡 --text-mode 空白气泡后期加字 --text-render-mode "生成空白气泡 + 后期叠字图层" --copywriting-mode 自动根据情节生成 --interaction-mode 评论引导 --outfit-style-lock 强锁定 --outfit-reference "第一张锚点图 + 人物参考图" --in-image-storyboard 关闭
```

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
- `入口/入口_开始这里.html`
- `config/minimal_input_schema.json`
- `examples/douyin_story_continuous.sample.json`
- `examples/v1_5_storyboard.sample.json`
