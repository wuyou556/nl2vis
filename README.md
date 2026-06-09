# nl2vis   Natural Language to Visualization（自然语言到可视化）

# ChatChart

<div align="center">

**聊着天就把数据分析完了**

🤖 基于 LLM Agent 的自然语言数据可视化平台  
Vue 3 · FastAPI · LangChain · ECharts · Docker

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vue.js)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)

</div>

---

## 📖 项目简介

ChatChart 是一个**自然语言驱动的自动化数据分析与可视化平台**。用户只需上传数据文件，用日常语言描述分析需求，系统即可自动完成数据探查、代码生成、图表渲染，并支持多轮迭代修改。

与传统 BI 工具不同，ChatChart 的核心是一个 **ReAct Agent**，它能够自主规划分析步骤、调用代码执行工具、在出错时自我反思并修复，最终将思考过程完全透明地展示给用户。

### 🎯 核心能力

- **对话式分析**：用自然语言提问，自动生成统计图表
- **自我纠错**：代码执行出错时，Agent 自动读取错误并修复重试
- **多轮迭代**：上下文保持，持续修改图表样式和数据范围
- **流式交互**：Agent 思考过程实时可见，不是黑箱等待
- **报告导出**：一键将分析结果组装为 Markdown/PDF 报告
- **安全沙箱**：AI 生成的代码在隔离 Docker 容器中执行

---

## 🖼️ 效果演示

### 主分析界面
> 左侧对话面板 + 右侧可视化面板，Agent 思考步骤可展开查看

### Agent 工作流示例
用户输入: "按地区统计销售额，画柱状图"
↓
💭 Thought: 需要按地区分组求和，降序排列，绘制柱状图
🛠️ Action: 调用 python_executor，生成 pandas + matplotlib 代码
👀 Observation: 图表已生成，华东区销售额最高
✅ Answer: 渲染 ECharts 柱状图 + 文字结论

text

### 自我纠错示例
🛠️ Action: 代码执行
👀 Observation: ❌ KeyError: '月份'
💡 Reflection: 数据中没有"月份"列，需要从"日期"列提取
🛠️ Action (retry): 修正代码，pd.to_datetime + dt.month
👀 Observation: ✅ 执行成功，折线图已生成

text

---

## 🏗️ 技术架构
┌─────────────────────────────────────────────────────┐
│ Frontend (Vue 3) │
│ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│ │ 对话面板 │ │ 图表面板 │ │ Agent 步骤可视化 │ │
│ └─────┬────┘ └─────┬────┘ └────────┬─────────┘ │
│ │ │ │ │
│ └─────────────┼───────────────┘ │
│ │ WebSocket / SSE │
└──────────────────────┼──────────────────────────────┘
│
┌──────────────────────┼──────────────────────────────┐
│ Backend (FastAPI) │
│ ┌───────────────────┴───────────────────┐ │
│ │ Agent Executor (LangChain) │ │
│ │ ┌─────────┐ ┌────────┐ ┌─────────┐ │ │
│ │ │ 规划模块 │ │ 工具集 │ │ 记忆模块 │ │ │
│ │ └─────────┘ └───┬────┘ └─────────┘ │ │
│ │ │ │ │
│ │ ┌───────────────┴───────────────┐ │ │
│ │ │ 代码执行 │ 数据探查 │ 图表生成 │ │ │
│ │ └───────┬───────┘ │ │ │
│ └──────────┼──────────────────┘ │ │
│ │ │ │
└─────────────┼───────────────────────┘ │
│ │
┌─────────────┴──────────────────────────────────┴──────┐
│ Sandbox (Docker 隔离容器) │
│ pandas · matplotlib · numpy │
│ 无网络 · 非 root · 资源限制 │
└────────────────────────────────────────────────────────┘

text

---

## 📁 项目结构
chatChart/
├── frontend/ # Vue 3 前端
│ ├── src/
│ │ ├── api/ # 后端接口封装
│ │ ├── components/ # 核心组件
│ │ │ ├── AgentSteps.vue # Agent 思考步骤面板
│ │ │ ├── ChartContainer.vue # ECharts 图表容器
│ │ │ ├── CodeViewer.vue # 代码高亮展示
│ │ │ ├── DataPreview.vue # 数据预览表格
│ │ │ ├── ChatMessage.vue # 对话气泡
│ │ │ └── ReportModal.vue # 报告导出弹窗
│ │ ├── hooks/ # 组合式函数
│ │ │ ├── useAnalysis.ts # 分析会话逻辑
│ │ │ ├── useChart.ts # 图表状态管理
│ │ │ └── useFileUpload.ts
│ │ ├── store/ # Pinia 状态管理
│ │ ├── views/ # 页面视图
│ │ │ ├── AnalysisView.vue # 主分析页
│ │ │ ├── HistoryView.vue # 历史会话
│ │ │ └── ReportView.vue # 报告预览
│ │ └── utils/ # 工具函数
│ └── vite.config.ts
│
├── backend/ # FastAPI 后端
│ ├── app/
│ │ ├── api/v1/ # REST API 路由
│ │ ├── agent/ # Agent 核心 ⭐
│ │ │ ├── agent_executor.py # ReAct 主控循环
│ │ │ ├── tools/ # 自定义工具集
│ │ │ ├── prompts/ # Prompt 模板
│ │ │ ├── memory/ # 对话记忆
│ │ │ └── reflection.py # 错误反思逻辑
│ │ ├── models/ # 数据库模型
│ │ ├── schemas/ # Pydantic 模型
│ │ ├── services/ # 业务服务层
│ │ └── tasks/ # Celery 异步任务
│ └── requirements.txt
│
├── sandbox/ # 代码执行沙箱
│ ├── executor_api.py # 执行服务
│ └── Dockerfile # 安全限制配置
│
├── docker-compose.yml # 一键启动
├── .env.example # 环境变量模板
└── README.md

text

---

## 🚀 快速开始

### 前置要求

- **Node.js** >= 18.x
- **Python** >= 3.10
- **Docker** & **Docker Compose**
- **OpenAI API Key**（或兼容的本地模型）

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/ChatChart.git
cd ChatChart
2. 配置环境变量
bash
cp .env.example .env
编辑 .env 文件，填入必要配置：

env
# LLM 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
# 或使用本地模型
# OPENAI_API_BASE=http://localhost:8000/v1

# 数据库
POSTGRES_USER=chatchart
POSTGRES_PASSWORD=chatchart123
POSTGRES_DB=chatchart

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-change-this
3. 启动基础设施
bash
docker-compose up -d
这会启动 PostgreSQL、Redis 和代码执行沙箱。

4. 启动后端
bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
API 文档自动生成，访问 http://localhost:8000/docs 查看 Swagger UI。

5. 启动前端
bash
cd frontend
npm install
npm run dev
访问 http://localhost:5173 即可使用。

🔧 核心配置说明
LLM 模型切换
支持任何 OpenAI 兼容接口的模型：

模型	配置方式
GPT-4o	OPENAI_API_KEY=sk-xxx
DeepSeek	OPENAI_API_BASE=https://api.deepseek.com/v1
本地 Qwen	OPENAI_API_BASE=http://localhost:8000/v1（Ollama/vLLM）
沙箱安全配置
sandbox/Dockerfile 关键安全设置：

dockerfile
FROM python:3.11-slim
RUN useradd -m -s /bin/bash sandbox
USER sandbox
# 容器编排时会添加：
# --network=none   # 禁止网络
# --memory=512m    # 内存限制
# --read-only      # 只读文件系统
📊 使用示例
基础分析
text
👤 用户：上传 sales.csv
👤 用户：按月份统计销售额，画折线图
🤖 ChatChart：生成月度销售趋势图 + 自动标注峰值
多轮迭代
text
👤 用户：只看华东地区
🤖 ChatChart：过滤数据，更新图表
👤 用户：改成柱状图，配色用蓝色系
🤖 ChatChart：切换图表类型，修改配色方案
错误自修复
text
👤 用户：画各地区利润环比增长率
🤖 ChatChart：[代码执行报错，自动读取错误]
🤖 ChatChart：[修正列名引用，重新执行]
🤖 ChatChart：✅ 已生成图表
🎓 毕业设计答辩要点
问题	回答方向
为什么不用现成的 BI 工具？	强调自然语言交互降低门槛，Agent 自主规划分析路径
Agent 体现在哪里？	ReAct 范式：规划→工具调用→观察→反思，不是简单的 API 套壳
如何保证代码执行安全？	Docker 沙箱隔离，无网络、非 root、资源限制
创新点是什么？	可观测的 Agent 工作流、自我纠错能力、上下文继承的多轮迭代
前端难点是什么？	流式通信（SSE/WS）、Agent 步骤可视化、复杂状态管理
📝 License
本项目采用 MIT License。

🙏 致谢
LangChain - Agent 框架

ECharts - 可视化图表库

FastAPI - 高性能 API 框架

Vue.js - 渐进式前端框架

<div align="center">
⭐ 如果这个项目对你有帮助，欢迎 Star！

</div> ```
