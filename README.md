# 龙湖签到管理系统

一个基于 Flask 的自动签到管理平台，支持多用户管理、定时任务调度和钉钉通知。

## 功能特性

- 🔐 **安全登录**：管理员认证 + Cloudflare Turnstile 防护
- 👥 **多用户管理**：支持添加多个龙湖账号进行自动签到
- ⏰ **定时任务**：自定义每日签到时间，自动执行
- 📱 **钉钉通知**：签到失败时自动发送钉钉消息提醒
- 🎨 **现代界面**：响应式设计，支持移动端访问
- 🐳 **容器化部署**：支持 Docker 和 Docker Compose

## 快速开始

### 方式一：Docker 运行

```bash
docker run -d \
  -p 5900:5900 \
  --name longfor-signin \
  ghcr.io/your-username/autolongfor:latest
```

### 方式二：Docker Compose

1. 下载 `docker-compose.yml`
2. 配置环境变量（可选）：
   ```bash
   export TURNSTILE_SITE_KEY=your_site_key
   export TURNSTILE_SECRET_KEY=your_secret_key
   ```
3. 启动服务：
   ```bash
   docker-compose up -d
   ```

### 方式三：本地开发

```bash
# 克隆仓库
git clone https://github.com/your-username/autolongfor.git
cd autolongfor

# 安装依赖
uv sync  # 或 pip install -r requirements.txt

# 启动应用
python app.py
```

## 访问和配置

1. 打开浏览器访问：`http://localhost:5900`
2. 使用默认账号登录：`admin` / `admin`
3. 在"系统设置"中修改管理员密码
4. 在"用户管理"中添加龙湖账号信息

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `TURNSTILE_SITE_KEY` | Cloudflare Turnstile 站点密钥 | 否 |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile 私钥 | 否 |

## 龙湖账号配置

需要获取以下信息（通过抓包获得）：
- `token`: 用户认证令牌
- `x-lf-usertoken`: 用户令牌
- `cookie`: 会话Cookie
- `x-lf-dxrisk-token`: 风控令牌
- `x-lf-channel`: 渠道标识（默认：L0）
- `x-lf-bu-code`: 业务代码（默认：L00602）
- `x-lf-dxrisk-source`: 风控来源（默认：2）

## 钉钉通知配置

1. 在钉钉群中添加"自定义机器人"
2. 复制 Webhook URL
3. 配置加签密钥（可选但推荐）
4. 在系统设置中填入配置信息

## 技术栈

- **后端**: Flask + SQLAlchemy + APScheduler
- **前端**: Bootstrap 5 + JavaScript
- **数据库**: SQLite
- **部署**: Docker + GitHub Actions

## 开发

```bash
# 删除数据库重新开始
rm longfor.db

# 启动开发服务器
python app.py

# 访问 http://localhost:5900
```

## License

MIT License