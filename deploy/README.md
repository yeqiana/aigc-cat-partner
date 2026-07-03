# nginx Docker 部署架构

目标端口：

- `29000`：项目导航页，跳转到其他项目主页。
- `29001`：Daily Event Draw，保留现有容器服务。
- `29002`：当前 AIGC Cat Partner 提示词生成静态页面。

## 线上实际架构

服务器当前使用 Docker 对外暴露项目端口：

```text
29000 -> nginx:stable-alpine 容器 80
29001 -> daily-event-draw 容器 4567
29002 -> aigc-cat-partner nginx 容器 80
```

`29001` 不由新 nginx 配置接管，避免影响现有 Daily Event Draw。

## 服务器目录

```text
/app/soft/nginx/html/index.html
/app/soft/aigc-cat-partner/html/index.html
```

## 发布静态文件

从本地上传：

```bash
scp deploy/navigation/index.html root@121.89.82.216:/app/soft/nginx/html/index.html
scp "入口/入口_开始这里.html" root@121.89.82.216:/app/soft/aigc-cat-partner/html/index.html
```

启动或重启 `29002`：

```bash
bash deploy/docker/run-aigc-cat-partner.sh
```

服务器上实际执行时，需要先把脚本传到服务器，或直接执行脚本里的 `docker run` 命令。

## 29001 迁移注意

如果后续明确要让 nginx 接管 `29001`，先确认 Daily Event Draw 是静态站点还是 Node 服务：

- 静态站点：停止原服务，把构建产物放到静态目录，再新增 `listen 29001` 静态 server。
- Node 服务：把 Node 服务迁移到内网端口，例如 `29101`，再由 nginx 的 `29001` 反向代理到 `127.0.0.1:29101`。

## 防火墙和安全组

需要放行：

- `29000/tcp`
- `29001/tcp`
- `29002/tcp`

服务器使用 `firewalld` 时：

```bash
firewall-cmd --permanent --add-port=29000/tcp
firewall-cmd --permanent --add-port=29001/tcp
firewall-cmd --permanent --add-port=29002/tcp
firewall-cmd --reload
```

## 验证

```bash
curl -I http://121.89.82.216:29000/
curl -I http://121.89.82.216:29001/
curl -I http://121.89.82.216:29002/
```

预期返回 `200`。
