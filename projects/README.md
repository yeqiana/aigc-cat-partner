# 项目层说明

`projects/` 只放项目 profile 和项目级入口说明，不搬迁、不删除项目数据。

通用层默认只读取 `config/common/`，不读取任何具体 IP。

换 IP 时推荐新增：

```text
projects/{project_id}/project_profile.json
```

然后在 profile 里指向该项目自己的：

- prompt policy
- character lock
- scene lock
- text strategy
- character spec
- reference manifest
- project negative prompt

运行时显式传入：

```bash
python tools/generate_prompt.py --project-profile projects/{project_id}/project_profile.json --input examples/xxx.json
```

当前项目数据仍保留在原位置，`projects/chen_nian_lie_gou/project_profile.json` 只是建立读取关系。
