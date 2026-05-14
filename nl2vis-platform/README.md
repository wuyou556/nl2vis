# nl2vis


自然语言转可视化（Natural Language to Visualization）智能分析平台。

## 功能概述

- **对话式分析**：通过自然语言描述需求，自动生成数据可视化图表
- **多数据源支持**：支持 CSV / Excel 文件上传
- **Agent 智能体**：基于 ReAct 模式的 Agent，自主完成数据分析流程
- **代码沙箱执行**：安全隔离的 Python 代码执行环境
- **报告生成**：自动生成分析报告并导出
- **实时流式响应**：基于 SSE / WebSocket 的流式 Agent 步骤展示

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + ECharts + Pinia |
| 后端 | FastAPI + SQLAlchemy + Celery |
| Agent | LangChain / 自研 ReAct Agent |
| 沙箱 | Flask + Docker 隔离执行 |
| 数据库 | PostgreSQL (可替换) |
| 部署 | Docker Compose |

## 项目结构

```
nl2vis-platform/
├── frontend/                # Vue 3 前端工程
├── backend/                 # FastAPI 后端工程
│   ├── app/
│   │   ├── agent/           # Agent 核心（工具、提示词、记忆）
│   │   ├── services/        # 业务逻辑层
│   │   └── api/v1/          # REST API 路由
│   └── tests/
├── sandbox/                 # 代码执行沙箱服务
└── docker-compose.yml       # 一键部署
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 1. 环境配置

```bash
cp .env.example .env
# 编辑 .env 填入 API Key 等配置
```

### 2. Docker Compose 启动（推荐）

```bash
docker-compose up -d
```

### 3. 本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

**沙箱：**

```bash
cd sandbox
pip install -r requirements.txt
python executor_api.py
```

## License

MIT