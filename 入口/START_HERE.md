# 从这里开始｜通用剧情连载系统 V2.0

## 最简单用法

1. 先阅读 `00_设定文档/通用剧情连载系统_沉淀复用实施方案.md`。
2. 新项目先填写角色、世界观和画风，不要复用旧 IP 内容。
3. 复制并修改 `examples/generic_suspense_series.sample.json`。
4. 运行：

```bash
python tools/generate_prompt.py --input examples/generic_suspense_series.sample.json
```

默认命令只使用 `config/common/` 通用层配置，不会读取当前项目的具体人物和场景数据。

5. 打开输出目录 `outputs/batch_plans/*_V2_pipeline/`。
6. 先检查：
   - `story_plan.json`
   - `frame_plan.json`
   - `copy_plan.json`
   - `prompt_plan.json`
   - `qa_result.json`
   - `retake_prompt.json`
   - `prompt_task.md`
7. 人工确认后，再按 `prompt_task.md` 的顺序逐张生成图片。
8. 每张图生成后先验收；失败先返工，不进入下一张。

## 项目层入口

如果要使用当前《陈年烈狗》项目数据，显式传入项目 profile：

```bash
python tools/generate_prompt.py --project-profile projects/chen_nian_lie_gou/project_profile.json --input examples/chennianliegou_ch3_pipeline_input.json
```

换新 IP 时，只新增一个新的 `projects/{project_id}/project_profile.json`，让它指向新项目自己的配置和资产；通用层不用改，也不需要删除当前项目数据。

## 推荐默认组合

```text
模板：通用悬念连载
比例：9:16
平台：抖音竖屏
生成张数：6
连续情节：是
气泡模式：多角色气泡
文字模式：空白气泡后期加字
文字落地模式：生成空白气泡 + 后期叠字图层
文案生成：自动根据情节生成
观众互动：评论引导
造型风格锁定：强锁定
当前图内分镜：关闭
```

## 必填核心字段

| 字段 | 说明 |
|---|---|
| project_name | 新项目名称。 |
| story_template | 剧情模板，例如 `通用悬念连载`、`日常反转连载`。 |
| story_outline | 本次故事从哪里开始、如何推进、在哪里结束。 |
| scene | 当前主场景或开场场景。 |
| image_count | 本组图片张数，1-12。 |
| continuous_story | 是否连续剧情，推荐 `是`。 |
| visual_gene_summary | 新角色、新搭档、新身份的固定视觉基因。 |
| worldview_summary | 新世界观、场景系统、道具系统和禁忌边界。 |
| style_prompt | 目标画风。 |

## 故事情节和补充说明的区别

```text
故事情节：本次故事讲什么，按什么顺序发生。
补充说明：额外限制、禁忌项、返工要求。
```

不要把完整故事只写进 `extra`。完整故事应写入 `story_outline`，这样脚本才能拆出 story/frame/copy/prompt/qa/retake。

## 关键生成顺序

```text
第1张：先生成锚点图
第2张：身份参考 + 风格参考 + 第1张锚点图
第3-N张：身份参考 + 风格参考 + 第1张锚点图 + 上一张成图
```

不要一次性并行生成所有图片，否则会退化成同主题散图。
