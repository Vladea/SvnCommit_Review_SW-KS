# SVN AI Review V2.0

面向 Windows 内网环境的 SVN 代码自动审查工具。定时扫描 SVN 仓库提交记录，提取变更差异，结合规则引擎与 AI 大模型审查代码，生成每日报告并通过 Teams/Email 推送。

---

## 快速开始

### 生产环境（推荐）

```
双击 StartTool.bat
```

首次运行会自动创建 `.venv` 并安装依赖。浏览器打开 `http://127.0.0.1:8000`。

### 开发环境

```
双击 dev.bat
```

同时启动后端（uvicorn reload `:8000`）和前端（Next.js HMR `:3000`），API 自动代理。

### 构建 Release

```
双击 构建发布.bat
```

编译前端 → 复制到 `app/static/`。之后只需 `StartTool.bat`，无需 Node.js。

---

## 前置条件

| 依赖 | 说明 |
|------|------|
| Python 3.12+ | 必需 |
| SVN CLI (`svn`) | 必需，需在 PATH 中 |
| Node.js 18+ | 仅开发和构建时需要 |

---

## 初始配置

### 1. SVN 认证

编辑 `.env`（首次启动自动从 `.env.example` 复制）：

```env
SVN_USERNAME=your_username
SVN_PASSWORD=your_password
```

内网 SVN 服务器必须填写，否则无法拉取 log/diff。

### 2. 添加 SVN 项目

打开 `http://127.0.0.1:8000` → **项目白名单** → 填写项目名和完整 SVN URL：

```
file:///F:/SVN%20Store/trunk
svn://192.168.1.100/repo/branch
```

### 3. 配置 AI 审查（可选）

打开 **全局设置** → **LLM 提供商**，选择一个提供商启用并填写 API Key：

| 提供商 | 费用 | 配置 |
|--------|------|------|
| DeepSeek Chat | 免费 | 注册 [platform.deepseek.com](https://platform.deepseek.com) 获取 API Key |
| Ollama 本地 | 免费 | 安装 Ollama → `ollama pull qwen2.5-coder:7b` |
| OpenAI GPT-4o | 付费 | 在 [platform.openai.com](https://platform.openai.com) 获取 API Key |

然后在 `.env` 中填写对应 Key：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
```

### 4. 配置通知（可选）

**全局设置 → 通知配置**：

- **Teams**：在 Teams 频道中创建 Incoming Webhook，将 URL 填到 `.env` 的 `TEAMS_WEBHOOK_URL`
- **Email**：填写 SMTP 服务器信息

### 5. 配置定时扫描

**定时任务** → 设置时间和通知渠道。支持多个时段。

---

## 审查规则

| 规则 | 等级 | 说明 |
|------|------|------|
| 合并冲突标记 | P1 | `<<<<<<<` / `>>>>>>>` / `=======` |
| TODO/FIXME | P4 | 未处理的待办标记 |
| 调试输出 | P3 | `printf` / `System.out.println` |
| memcpy 边界 | P3 | 缺少 `sizeof` 等长度保护 |

可在 **全局设置 → 审查规则** 中单独开关每条规则。

---

## 手动扫描

**SVN 日期扫描** → 选择日期范围 → 开始扫描。

扫描流程：`svn log` → 按真实 commit 日期过滤 → `svn diff` → 规则审查 → AI 审查 → 生成报告 → 推送通知。

---

## 项目结构

```
├── app/                    # Python 后端
│   ├── main.py             # 入口
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库
│   ├── models/             # ORM 模型 (5)
│   ├── schemas/            # Pydantic 模型
│   ├── services/           # 业务逻辑
│   │   ├── svn_client.py   # SVN 操作 + 重试
│   │   ├── scanner.py      # 扫描编排
│   │   ├── review/         # 审查引擎
│   │   ├── report_builder.py
│   │   └── notifier.py     # Teams + Email
│   ├── routes/             # API (8 模块)
│   ├── scheduler.py        # APScheduler
│   └── static/             # 前端构建产物
├── frontend/               # Next.js 源码
│   └── src/                # 8 个页面 + 组件
├── config.yaml             # 运行配置
├── .env.example            # 环境变量模板
├── dev.bat                 # 开发启动
├── 构建发布.bat             # 打包
├── StartTool.bat           # 生产启动
└── 工程设计书.md
```

---

## 常见问题

**Q: 浏览器显示旧页面？**  
按 `Ctrl+F5` 强制刷新。

**Q: SVN 连接失败？**  
检查 `.env` 中 `SVN_USERNAME` / `SVN_PASSWORD`，确认 SVN URL 可访问。

**Q: AI 审查不工作？**  
检查 LLM 提供商是否启用并设为默认，确认 `.env` 中 API Key 正确填写。点击「测试」按钮验证连接。

**Q: 日志在哪里？**  
`logs/app.log`，每天自动轮转，保留 30 天。

**Q: 如何备份？**  
备份 `data/svn_ai_review.db` 和 `config.yaml`、`.env` 即可。
