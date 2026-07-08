# AGENTS.md

## 项目目标

本仓库用于 AIGC 剧情向图文连载生成。所有 Prompt、模板、配置和工具改动，都必须服务于：

1. 人物形象连续稳定；
2. 场景风格连续稳定；
3. 分镜叙事清晰；
4. 中文文字后期可控；
5. 生成结果可验收、可返工；
6. 通用层和项目层清晰隔离，后续换 IP 只操作项目层。

## 通用层 / 项目层隔离规则

### 绝对规则

1. 不得删除、清空或迁移当前项目数据，除非用户明确要求。
2. 不得把具体 IP 的人物、场景、原文、参考图、母版图路径写入通用层默认配置。
3. 通用入口默认只读取 `config/common/`。
4. 具体项目必须通过 `projects/{project_id}/project_profile.json` 显式接入。
5. 后续换 IP 时，只新增或替换项目层 profile 指向的配置和资产，不修改通用层默认规则。

### 通用层范围

通用层只允许保存方法和空模板：

- `tools/generate_prompt.py`
- `tools/generate_batch_plan.py`
- `config/common/`
- `examples/generic_suspense_series.sample.json`
- 通用 README 和入口说明

通用层可以包含：

- 连载流水线；
- 锚点图机制；
- 批量生成能力；
- 情绪推进字段；
- 通用文字策略；
- 通用负面词；
- QA 验收框架；
- 返工 Prompt 结构；
- 角色 / 世界观设定表模板。

通用层禁止包含：

- 具体作品名；
- 具体角色名；
- 具体章节原文；
- 具体项目参考图路径；
- 具体项目场景资产路径；
- 项目专属 negative prompt。

### 项目层范围

项目层保存具体 IP 的全部数据。当前项目层入口为：

```text
projects/chen_nian_lie_gou/project_profile.json
```

该 profile 只建立读取关系，不搬迁、不删除原有项目数据。

当前《陈年烈狗》项目数据允许保留在原位置，包括但不限于：

- `00_设定文档/`
- `02_风格母版图/`
- `03_场景资产/`
- `config/prompt_policy.json`
- `config/character_lock_chen_nian_lie_gou.json`
- `config/scene_lock_chen_nian_lie_gou.json`
- `config/text_strategy.json`
- `config/character_spec.json`
- `config/reference_manifest.json`
- `config/negative_prompt_project.txt`
- `prompts/`
- `examples/chennianliegou_*.json`

使用项目层时必须显式传入：

```bash
python tools/generate_prompt.py --project-profile projects/chen_nian_lie_gou/project_profile.json --input examples/chennianliegou_ch3_pipeline_input.json
```

批量项目任务必须显式传入：

```bash
python tools/generate_batch_plan.py --project-profile projects/chen_nian_lie_gou/project_profile.json --input prompts/batch/chapters_001_010.batch_plan.json
```

## Prompt 生成总规范

所有章节 Prompt 必须由约束层生成或校验，不能只靠单次手写提示词修补。生成顺序固定为：

1. 人物锁定层；
2. 场景锁定层；
3. 画风锁定层；
4. 本帧剧情层；
5. 分镜结构层；
6. 文字策略层；
7. 负面约束层；
8. 验收层。

通用任务优先读取：

- `config/common/prompt_policy.json`
- `config/common/character_lock.json`
- `config/common/scene_lock.json`
- `config/common/text_strategy.json`
- `config/common/character_spec.json`
- `config/common/reference_manifest.json`
- `config/negative_prompt_common.txt`
- `config/common/negative_prompt_project.txt`

项目任务优先读取当前 profile 指向的项目配置。

## 最高优先级规则

人物锁定 > 场景锁定 > 画风锁定 > 本帧剧情 > 分镜结构 > 文字排版。

如果剧情动作与人物设定冲突，优先保留人物设定。
如果人物动作与角色行为逻辑冲突，优先保留角色行为逻辑。
如果文字入图与人物稳定冲突，优先使用空白气泡和后期叠字。

如果剧情原文包含儿童裸露、血腥伤口、击打瞬间、虐打过程、喷血、光身、抽筋、黑帮化、未成年人排泄照护、衣裤 / 下身细节、近距离身体照料等高风险表达，必须先按 `docs/CONTENT_SAFETY_PROMPT_GUIDE.md` 改写为克制、生活化、保护导向的视觉表达。

## 文字策略

默认不直接生成中文文字。
默认生成空白对白气泡和空白矩形旁白框，供后期叠字。

除非输入显式设置 `allow_text_in_image=true`，否则不得把台词、旁白、人物姓名、章节标题写进图中。

即使输入中包含 `story_title`、`phase`、`title`、`dialogue.name` 等字段，也只能作为配置、文案清单或后期叠字素材，不得指示模型把这些文字直接画进图中。

禁止图中出现：

- 人物姓名标签；
- 第几章；
- 第几帧；
- 第几幕；
- 当前帧；
- 章节标题；
- 人物介绍浮标；
- 角色名冒号台词。

## 分镜策略

默认 9:16 抖音竖屏。
默认 2-3 个漫画分镜格。
必须有清晰边界。

必须包含：

- 一个空间建立镜头；
- 一个动作推进镜头；
- 一个手部、道具或人物反应特写。

禁止生成单幅海报式大图。

## 返工规则

如果用户指出人物漂移，不要只修改当前 Prompt。必须判断是否应该更新：

- 当前项目 profile 指向的人物锁定配置；
- 当前项目 profile 指向的场景锁定配置；
- 当前项目 profile 指向的文字策略配置；
- 当前项目 profile 指向的 reference manifest；
- 通用层模板或 QA 规则。

如果用户纠正眼睛、服装、年龄、发型、场景年代、场景道具、中文乱码、姓名标签、分镜结构等问题，必须判断是否沉淀到配置或模板。

反复出现的问题必须进入项目级规范；只有跨 IP 都成立的方法问题，才进入通用层。

## 验收规则

涉及通用层 / 项目层隔离的改动，必须至少验收：

1. `python -m py_compile tools/generate_prompt.py tools/generate_batch_plan.py`
2. 通用入口生成成功；
3. 通用输出不包含具体项目词；
4. 项目 profile 入口生成成功；
5. 项目输出能正确读取项目层人物、场景和负面词；
6. 批量入口生成成功；
7. 验证输出目录清理干净。

通用层清洁度检查示例：

```bash
rg -n "陈年烈狗|陶淮南|迟苦|陶晓东|火炕|盲校|农村老屋" tools config/common
```

期望结果：无匹配。
