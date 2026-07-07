# Prompt Policy

本项目的 Prompt 不是单条提示词，而是项目级约束层。后续所有章节、母版图、返工图都必须通过本规范生成或校验。

## 分层结构

### 1. 人物锁定层

作用：固定角色年龄、体型、五官、发型、服装、行为逻辑和禁止漂移项。人物锁定高于剧情动作。

字段：
- `character_id`
- `age_stage`
- `must`
- `visual_rules`
- `behavior_rules`
- `forbidden`
- `reference_ids`

示例：

```text
陶淮南必须是8岁盲人小孩；大而清亮但不聚焦的黑眼睛；不能准确看向人物、碗、冰溜子或门口；根据声音转头；用手摸索炕沿、碗、冰溜子确认位置。
```

### 2. 场景锁定层

作用：固定空间、年代、季节、道具和感官气氛。场景锁定高于画风和本帧剧情。

字段：
- `scene_id`
- `time`
- `space`
- `season_weather`
- `props`
- `sensory_details`
- `forbidden`
- `reference_ids`

示例：

```text
农村老屋：北方寒冬，火炕、漏风窗、窗框冰溜子、饭碗、纸灰味、柴火味，2000年代中国北方农村生活质感。
```

### 3. 画风锁定层

作用：固定系列视觉语言，避免同一章节在写实、Q版、赛博、偶像剧之间漂移。

字段：
- `style_name`
- `style_prompt`
- `lighting`
- `color`
- `render_rules`
- `forbidden`

示例：

```text
温柔现实向日系绘本插画，干净线稿，低饱和电影感光影，中国北方生活场景，人物表情克制。
```

### 4. 分镜结构层

作用：约束每张图为 9:16 竖屏，默认 2-3 个漫画分镜格，保证叙事不是单幅海报。

字段：
- `ratio`
- `platform`
- `panel_count`
- `layout`
- `required_shots`
- `continuity_rules`

示例：

```text
9:16 抖音竖屏，2-3格漫画分镜，主画面 + 特写小窗；必须包含空间建立、动作推进、手部/道具/反应特写。
```

### 5. 本帧剧情层

作用：只描述当前帧要推进的事件，不覆盖人物、场景和画风锁定。

字段：
- `chapter`
- `frame_index`
- `scene`
- `action`
- `focus`
- `previous_action`
- `next_action`
- `visual_evidence`

示例：

```text
迟苦把长长的冰溜子放到炕沿附近，陶淮南听见声响后偏头，伸手摸索确认位置。
```

### 6. 文字策略层

作用：避免中文乱码和误生成姓名标签。默认只生成空白气泡、空白旁白框和安全留白，文字由后期叠加。

字段：
- `allow_text_in_image`
- `bubble_mode`
- `narration_mode`
- `dialogue_name_mode`
- `forbidden_text`
- `post_text_list`

示例：

```text
画面中只保留空白对白气泡和空白矩形旁白框；台词、旁白、章节名、人物姓名只进入后期叠字清单，不直接入图。
```

### 7. 负面约束层

作用：集中列出会导致漂移、误解或不可验收的禁止项。

字段：
- `global_negative`
- `character_negative`
- `scene_negative`
- `text_negative`
- `composition_negative`

示例：

```text
不要姓名标签，不要第几章/第几帧/顶部标题栏，不要陶淮南正常对视，不要儿童成人化，不要短发陶晓东，不要中文乱码。
```

### 8. 内容安全改写层

作用：降低 Prompt 被平台内容政策拦截的概率。涉及儿童、冲突、受伤、酒后闯入、洗澡换衣、排泄照护、身体帮扶等内容时，必须先把原文改写成克制、生活化、保护导向的视觉表达。

字段：
- `risk_topics`
- `safe_rewrite_rules`
- `child_safety_rules`
- `violence_rewrite_rules`
- `forbidden_sensitive_detail`

示例：

```text
把“追打、喷血、光身、抽筋”改写为“危险临近、保护者阻止、旧伤痕、被旧毯或毛巾包住、虚弱发抖”。画面重点表现保护、安置和情绪变化，不表现血腥、裸露、虐打过程或施暴特写。
把“未成年人排泄照护、接尿、衣裤/下身、近距离身体照料”改写为“照护后的铝盆被放回锅台旁、门帘外低声交流、炕边摸索确认方向、尴尬但克制的关系变化”。不表现过程本身。
```

详细规则见 `docs/CONTENT_SAFETY_PROMPT_GUIDE.md`。

### 9. 验收层

作用：把 Prompt 输出转成可检查清单，指导出图后验收和返工。

字段：
- `must_pass`
- `character_checks`
- `scene_checks`
- `text_checks`
- `storyboard_checks`
- `retake_rules`

示例：

```text
陶淮南是否明显是盲人小孩；眼睛是否不聚焦；是否通过声音和触觉行动；是否没有人物姓名标签；是否为9:16且有2-3格分镜。
```

## 生成要求

所有章节 Prompt 必须：

1. 先输出“最高优先级：人物锁定”；
2. 再输出“画风锁定”；
3. 再输出“场景锁定”；
4. 再输出“本帧剧情”；
5. 再输出“分镜要求”；
6. 再输出“文字策略”；
7. 再输出“内容安全改写层”；
8. 最后输出“禁止项 / Negative Prompt”和“验收清单”。

禁止把配置字段里的 `story_title`、`phase`、`title`、`dialogue.name` 直接转成画面文字。除非输入显式开启 `allow_text_in_image=true`，否则中文台词和旁白必须只进入后期叠字清单。
