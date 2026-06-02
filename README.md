# 多Agent协作研究助手

> Multi-Agent Collaborative Research Assistant

基于 Python + FastAPI 后端的多 Agent 协作学术研究分析系统。5 个专业 Agent **并行执行**，通过 OpenAI 兼容 API 对学术内容进行深度分析，前端实时展示协作过程和分析结果。

## ✨ 功能特点

- **5 Agent 并行协作**：协调者、分析专员、评审专员、综合专员、研究顾问同时并发调用 LLM，大幅缩短分析耗时
- **3 种分析模式**：论文分析、文献综述、研究方案
- **实时可视化**：协作流程图、Agent 状态动画、逐段进度条、实时日志
- **Web 前端**：单文件 HTML，Tailwind CSS，暗色模式，Markdown 渲染
- **快速测试**：一键模拟完整流程，不消耗 token，快速验证前后端数据流
- **灵活部署**：支持 CLI 命令行和 Web 服务两种模式
- **兼容 OpenAI 接口**：支持任何兼容 OpenAI API 格式的服务（GPT-4o、DeepSeek、MiMo 等）

## 🏗️ 项目结构

```
research-assistant/
├── server.py                # FastAPI 后端服务（Web 模式入口）
├── main.py                  # CLI 命令行入口
├── pipeline.py              # Agent 协作管线（支持串行/并行两种模式）
├── agents/
│   ├── base.py              # Agent 基类
│   ├── coordinator.py       # 协调者：任务分解与调度
│   ├── analyzer.py          # 分析专员：内容分析与方法论
│   ├── reviewer.py          # 评审专员：创新性与局限性评审
│   ├── synthesizer.py       # 综合专员：整合与报告生成
│   └── advisor.py           # 研究顾问：建议与研究方向
├── utils/
│   └── api_client.py        # LLM API 客户端封装
├── static/
│   ├── index.html           # Web 前端页面
│   └── manifest.json        # PWA 配置
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
├── .gitignore
├── TEST_CASE.md             # 测试用例
└── README.md
```

## 🤖 Agent 协作流程

```
用户输入（论文/主题/研究问题）
  │
  ▼
  ┌──────────────────────────────────────────┐
  │         5 个 Agent 并行执行               │
  │                                          │
  │  ┌─────────────┐  ┌─────────────┐        │
  │  │ Coordinator  │  │  Analyzer   │        │
  │  │ · 判断类型   │  │ · 内容概述   │        │
  │  │ · 制定计划   │  │ · 方法论分析 │        │
  │  └─────────────┘  └─────────────┘        │
  │  ┌─────────────┐  ┌─────────────┐        │
  │  │  Reviewer    │  │ Synthesizer │        │
  │  │ · 创新性评估 │  │ · 整合结果   │        │
  │  │ · 局限性分析 │  │ · 综合报告   │        │
  │  └─────────────┘  └─────────────┘        │
  │  ┌─────────────┐                         │
  │  │   Advisor    │                         │
  │  │ · 研究方向   │                         │
  │  │ · 应用建议   │                         │
  │  └─────────────┘                         │
  └──────────────────────────────────────────┘
  │
  ▼
  分析结果（5 份报告）
```

并行模式下 5 个 Agent 同时启动，独立调用 LLM，无需等待前序结果，总耗时约 40-60 秒。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd research-assistant
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 复制示例文件
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置：

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

> 支持任何兼容 OpenAI API 格式的服务，只需修改 `OPENAI_API_BASE` 即可。

### 3. 运行

#### Web 服务模式（推荐）

```bash
python server.py
```

浏览器打开 **`http://127.0.0.1:8000`** 即可使用。

#### CLI 命令行模式

```bash
# 交互模式（循环输入）
python main.py

# 单次分析
python main.py "请分析 Transformer 架构的创新点"

# 测试 API 连接
python main.py --test
```

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/api/start-analysis` | POST | 启动分析任务（后台并行执行） |
| `/api/stop-analysis` | POST | 停止当前分析 |
| `/api/task-status` | GET | 获取任务状态和 Agent 运行状态 |
| `/api/agent-status` | GET | 获取 Agent 状态（task-status 别名） |
| `/api/logs` | GET | 获取实时日志（支持增量拉取 `?since_id=N`） |
| `/api/result/{type}` | GET | 获取指定类型的分析结果 |
| `/api/all-results` | GET | 获取所有 Agent 的分析结果 |
| `/api/test` | POST | 测试 API 连接 |
| `/api/test-pipeline` | POST | 快速测试（模拟流程，不消耗 token） |
| `/api/config` | GET | 获取当前配置状态 |

### 启动分析请求

```json
POST /api/start-analysis
{
    "content": "论文内容或研究主题...",
    "mode": "paper",
    "api_key": "sk-xxx",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4o"
}
```

参数说明：
- `content`：必填，要分析的内容
- `mode`：分析模式，`paper`（论文分析）/ `review`（文献综述）/ `proposal`（研究方案）
- `api_key` / `api_base` / `model`：可选，不填则使用 `.env` 中的配置

### 轮询结果

分析启动后，前端通过轮询获取进度：

```
GET /api/task-status          → { task_status, agent_states, elapsed }
GET /api/logs?since_id=0      → { logs: [{id, time, type, message}], last_id }
GET /api/all-results          → { results: { coordinator, analyzer, ... } }
```

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | API 密钥（必填） | - |
| `OPENAI_API_BASE` | API 端点 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 使用的模型 | `gpt-4o` |
| `SERVER_HOST` | 服务监听地址 | `127.0.0.1` |
| `SERVER_PORT` | 服务端口 | `8000` |

### 支持的模型

任何兼容 OpenAI Chat Completions API 的模型均可使用，例如：

- `gpt-4o` / `gpt-4o-mini` — OpenAI
- `deepseek-chat` — DeepSeek
- `mimo-v2-pro` — MiMo
- 其他兼容 OpenAI API 格式的服务

## 🧪 快速测试

页面上的 **⚡ 快速测试** 按钮可以一键模拟完整的 Agent 流水线：

- 不消耗任何 token
- 约 2 秒完成
- 验证前后端数据流：请求 → Agent 状态更新 → 结果存储 → 前端渲染
- 适合在修改代码后快速验证功能是否正常

## 📋 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Python + FastAPI + Uvicorn |
| AI 接口 | OpenAI SDK（兼容 API） |
| 前端 | 单文件 HTML + Tailwind CSS + Font Awesome |
| 渲染 | marked.js + highlight.js |
| 并发 | ThreadPoolExecutor（5 Agent 并行） |
| 架构 | 轮询式 REST API + 后台线程任务管理 |

## 📄 许可

MIT License
