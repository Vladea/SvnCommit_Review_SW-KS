# SVN AI Review V2.0 — 智能代码体检助手

面向 Windows 内网环境的 SVN 代码自动审查工具。自动扫描 SVN 仓库提交记录、提取变更差异，结合**规则引擎 + AI 大模型 + 可定制 Skill** 三层审查体系分析代码质量，生成日报并通过 Teams/Email 推送。

---

## 核心功能

| 功能 | 说明 |
|------|------|
| **自动扫描** | 定时或手动按 SVN 真实 commit 日期拉取提交记录 |
| **三层审查** | 规则引擎（毫秒）→ AI 通用审查（秒级）→ 可定制 Skill 审查（提示词驱动） |
| **并发处理** | 3 线程并行扫描，SVN diff/LLM 审查并行，DB 写入锁保护 |
| **智能跳过** | 超大提交（>50 文件）自动预检跳过，避免超时 |
| **强制重扫** | 一键清除旧记录重新审查，覆盖已扫 commit |
| **进度可视** | 实时进度条 + 项目/Revision/文件追踪，切页面不中断 |
| **日报推送** | Markdown 报告自动生成，Teams Webhook + Email 双渠道推送 |
| **Web 管理** | 项目白名单、LLM 提供商热插拔、审查规则开关、定时任务配置 |
| **安全认证** | 可选 API Key 中间件保护所有接口 |
| **支持本地模型** | 无外网环境可用 Ollama 本地模型，零 API 费用 |

---

## 快速开始

### 生产环境

```
双击 StartTool.bat
```

首次运行自动创建虚拟环境、安装依赖。浏览器打开 `http://127.0.0.1:8000`。

### 开发环境

```
双击 dev.bat
```

后端 `uvicorn --reload :8000` + 前端 `Next.js HMR :3000`，API 自动代理。

### 构建 Release

```
双击 构建发布.bat
```

编译前端 → 生成 `SVN_AI_Review_V2.0.zip`，部署后仅需 Python。

---

## 前置条件

| 依赖 | 必需 | 说明 |
|------|------|------|
| Python 3.12+ | ✅ | 运行环境 |
| SVN CLI (`svn`) | ✅ | 需在 PATH 中 |
| Node.js 18+ | 仅构建 | `构建发布.bat` 需要 |

---

## 配置指南

### 1. 项目配置

启动后自动从 `config.example.yaml` 生成 `config.yaml`。Web UI 操作：

- **项目白名单** → 添加 SVN 仓库（支持 `file://` / `svn://` / `http://` / `https://`）
- **全局设置** → 配置扫描参数、审查规则、通知渠道

### 2. AI 审查（可选）

**全局设置 → LLM 提供商**，支持：

| 提供商 | 费用 | 配置 |
|--------|------|------|
| DeepSeek Chat | 免费 500 万 token/日 | 注册获取 Key，填 `.env` 的 `DEEPSEEK_API_KEY` |
| Ollama 本地 | 免费 | `ollama pull qwen2.5-coder:7b` |
| OpenAI GPT-4o | 付费 | 填 `.env` 的 `OPENAI_API_KEY` |
| 任意 OpenAI 兼容 API | — | 自定义 api_base + model |
| 本地模型（无 GPU） | 免费 | Ollama + 16GB 内存即可 |

### 3. Skill 审查规则

在 `config.yaml` 的 `skills:` 段定义 Skill（提示词 + 作用文件类型 + 风险等级）。系统内置：

- **代码格式对齐** (P4)：缩进、大括号、行尾空格
- **指针安全检查** (P2)：NULL 解引用、AllocatePool 返回值检查

可在 YAML 中直接添加新 Skill，重启即生效，无需改代码。

### 4. 通知（可选）

- **Teams**：频道 Incoming Webhook → 填 `.env` 的 `TEAMS_WEBHOOK_URL`
- **Email**：SMTP 配置 → 填 `.env` 对应字段

### 5. 定时扫描

**定时任务** → 支持多时段，每时段可独立开关通知。

---

## 使用流程

### 按日期扫描

**SVN 日期扫描** → 选日期范围 → 点击开始扫描：

1. 查询 SVN 获取 commit 列表
2. 超过 5 个 commit 时提示预览，可选择预览前 5 个或全部扫描
3. `--summarize` 快速预检文件数 → 超过上限的 commit 自动跳过
4. 并发处理：`svn diff` + 规则引擎 + LLM + Skill 审查
5. 生成报告 + 推送通知

勾选 **强制重扫** 可清除旧记录重新审查已扫过的 commit。

### 查看结果

- **审查报告**：卡片式列表，显示日期范围、仓库/提交/文件/作者统计、问题汇总
- **问题列表**：全局问题总览，区分引擎类型（rule/llm/skill）
- **提交人统计**：按作者汇总代码量与问题密度
- **仪表盘**：全局概览

---

## 审查体系

### 规则引擎（毫秒级）

| 规则 | 等级 | 检测内容 |
|------|------|---------|
| 合并冲突标记 | P1 | `<<<<<<<` / `>>>>>>>` / `=======` |
| TODO/FIXME | P4 | 未处理待办标记 |
| 调试输出 | P3 | `printf` / 调试打印 |
| memcpy 边界 | P3 | 缺少 sizeof 等长度保护 |

### AI 通用审查

使用配置的 LLM 提供商进行通用代码语义审查，返回结构化 JSON 结果。

### Skill 审查（提示词驱动）

用户可自定义 Skill（YAML 配置），按文件类型匹配。每个 Skill = 一段提示词 + 作用范围 + 风险等级，修改后重启即生效。

---

## 项目结构

```
├── app/                         # Python 后端 (37 py 文件)
│   ├── main.py                  # FastAPI 入口 + 认证中间件 + CORS
│   ├── config.py                # 配置管理（mtime 缓存 + 原子写）
│   ├── database.py              # SQLite WAL 模式 + busy_timeout
│   ├── models/                  # ORM 模型 (5) + 索引 + 外键
│   ├── schemas/                 # Pydantic 校验 (5)
│   ├── routes/                  # API 路由 (8) + scan 进度
│   ├── services/                # 核心业务
│   │   ├── svn_client.py        # SVN 操作（summarize 预检 + 重试）
│   │   ├── scanner.py           # 并发扫描编排（ThreadPoolExecutor）
│   │   ├── scan_progress.py     # 扫描进度追踪 + 取消机制
│   │   ├── review/              # 三层审查引擎
│   │   │   ├── rule_engine.py   # 正则规则
│   │   │   ├── llm.py           # AI 审查（重试 + Session 复用）
│   │   │   └── skill_engine.py  # Skill 审查（提示词驱动）
│   │   ├── report_builder.py    # Markdown 报告生成
│   │   └── notifier.py          # Teams + Email 推送
│   ├── scheduler.py             # APScheduler 多时段定时
│   └── static/                  # 前端构建产物（gitignore）
├── frontend/                    # Next.js 14 TypeScript
│   └── src/
│       ├── app/                 # 8 页面（App Router）
│       ├── components/ui/       # 组件库（Button/Card/Badge/DatePicker/Sidebar）
│       └── lib/                 # API 客户端 + 状态管理 + 类型定义
├── config.example.yaml          # 配置模板
├── .env.example                 # 环境变量模板
├── dev.bat / StartTool.bat / 构建发布.bat
└── AI_OPTIMIZATION_GUIDE.yaml   # 50 项优化清单（34 已完成）
```

---

## 常见问题

**Q: SVN 连接失败？**
检查 `svn` 命令在 PATH 中，`file://` 路径存在。

**Q: AI 审查不工作？**
确认 LLM 提供商已启用，`.env` 中 API Key 正确。点「测试」验证。

**Q: 扫描大仓库超时？**
`max_files_per_commit: 50` 控制单次提交文件上限，可调大；`--summarize` 预检机制秒级跳过超限提交。

**Q: 数据库被锁？**
SQLite WAL 模式 + busy_timeout=5s + 写锁串行，正常不会。若出现，关掉多余的 dev.bat 窗口。

**Q: 如何备份？**
备份 `data/svn_ai_review.db`、`config.yaml`、`.env` 三个文件。

**Q: 配置到新电脑？**
`git clone` → `dev.bat` 首次启动自动生成 `config.yaml` → 配置项目 + LLM + `.env`。历史数据不随 git 同步。
