# Agent 核心架构设计

> NL2VIS 的智能引擎 —— 基于 ReAct 模式的多工具数据分析 Agent

---

## 1. 总体架构

```
                        ┌─────────────────────────────────────────┐
                        │            API 路由层 (已完成)            │
                        │  POST /sessions/{id}/messages            │
                        └──────────────┬──────────────────────────┘
                                       │ 用户消息
                                       ▼
                        ┌─────────────────────────────────────────┐
                        │          AgentExecutor (主循环)           │
                        │                                         │
                        │   ┌───────┐    ┌──────┐    ┌─────────┐ │
                        │   │ Think │───▶│ Act  │───▶│ Observe │ │
                        │   └───▲───┘    └──────┘    └────┬────┘ │
                        │       │                         │       │
                        │       └─────────────────────────┘       │
                        │              ReAct 循环                  │
                        └──────┬──────────────────────────────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              ┌──────────┐ ┌────────┐ ┌──────────┐
              │  Tools   │ │ Memory │ │ Prompts  │
              │  工具箱   │ │  记忆   │ │  提示词   │
              └──────────┘ └────────┘ └──────────┘
```

---

## 2. 目录结构

```
agent/
├── __init__.py              # 对外暴露 AgentExecutor
│
├── core.py                  # AgentExecutor 主循环
│                             #   - 驱动 Think → Act → Observe
│                             #   - 控制最大迭代次数
│                             #   - 解析 LLM 输出，决定下一步动作
│
├── config.py                # Agent 配置
│                             #   - LLM 客户端初始化
│                             #   - 模型选择、温度等参数
│                             #   - 最大迭代次数、超时设置
│
├── schemas.py               # Agent 内部数据结构
│                             #   - AgentAction (工具调用)
│                             #   - AgentObservation (工具结果)
│                             #   - AgentResult (最终输出)
│                             #   - AgentStep (单步记录)
│
├── tools/                   # ── 工具箱 ──
│   ├── __init__.py          #   工具注册表，统一导出
│   ├── base.py              #   BaseTool 抽象基类
│   ├── code_executor.py     #   代码执行工具（调用沙箱）
│   ├── file_reader.py       #   文件读取工具（读 CSV/Excel）
│   └── data_preview.py      #   数据预览工具（head/dtypes/shape）
│
├── prompts.py               #   系统提示词模板（单文件，够用）
│
└── memory.py                 #   对话历史管理 + 上下文裁剪（单文件）
```

---

## 3. 核心流程：一次完整的对话

以用户说 **"帮我分析这个销售数据的趋势"** 为例：

### 3.1 入口：路由层调用 Agent

```
用户在 sessions.py 发送消息
        │
        ▼
sessions.py 路由:
  1. 保存用户消息到 Message 表 (sender="user")
  2. 查询该会话关联的文件列表
  3. 加载该会话的历史消息
  4. 调用 agent.run(user_message, session_id, files, history)
  5. 保存 Agent 回复到 Message 表 (sender="agent")
  6. 返回结果给前端
```

### 3.2 Agent 主循环：ReAct 过程

```
AgentExecutor.run() 被调用
│
│  ┌─ 准备阶段 ──────────────────────────────────────────────────┐
│  │  1. 从 memory 加载对话历史                                    │
│  │  2. 从 tools 获取可用工具描述                                  │
│  │  3. 组装系统提示词 + 历史 + 用户消息 → 完整 prompt              │
│  └──────────────────────────────────────────────────────────────┘
│
│  ┌─ ReAct 循环 (最多 max_iterations 次) ───────────────────────┐
│  │                                                              │
│  │  第 1 轮：                                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Think (思考)                                          │   │
│  │  │                                                       │   │
│  │  │ LLM 收到：                                            │   │
│  │  │   - 系统提示词（你是一个数据分析 Agent...）              │   │
│  │  │   - 可用工具列表（execute_code, read_file, preview）   │   │
│  │  │   - 历史对话                                          │   │
│  │  │   - 用户消息："帮我分析销售数据的趋势"                   │   │
│  │  │                                                       │   │
│  │  │ LLM 输出：                                            │   │
│  │  │   Thought: 我需要先看看数据长什么样                     │   │
│  │  │   Action: data_preview                                │   │
│  │  │   Action Input: {"file_path": "uploads/1/xxx.csv"}    │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Act (行动)                                            │   │
│  │  │                                                       │   │
│  │  │ AgentExecutor 解析出：                                 │   │
│  │  │   工具名 = data_preview                               │   │
│  │  │   参数 = {file_path: "uploads/1/xxx.csv"}             │   │
│  │  │                                                       │   │
│  │  │ 调用 data_preview.run(file_path=...)                  │   │
│  │  │ 工具内部：用 pandas 读取 CSV，返回前5行+列类型+形状     │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Observe (观察)                                        │   │
│  │  │                                                       │   │
│  │  │ 工具返回：                                             │   │
│  │  │   "数据共 1000 行 × 4 列                               │   │
│  │  │    列: date(日期), product(产品), sales(销售额),        │   │
│  │  │        region(地区)                                    │   │
│  │  │    前5行: ..."                                         │   │
│  │  │                                                       │   │
│  │  │ → 将观察结果追加到消息历史                               │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼ 继续循环                          │
│  │                                                              │
│  │  第 2 轮：                                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Think:                                                │   │
│  │  │   Thought: 数据结构清楚了，我来写代码生成趋势图          │   │
│  │  │   Action: execute_code                                │   │
│  │  │   Action Input: {                                     │   │
│  │  │     "code": "import pandas as pd\n..."                │   │
│  │  │   }                                                   │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Act:                                                  │   │
│  │  │   调用 code_executor.run(code="...")                  │   │
│  │  │   → POST http://sandbox:5001/execute                  │   │
│  │  │   → 沙箱执行代码，返回 stdout/stderr                   │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Observe:                                              │   │
│  │  │   stdout: "图表已保存到 output/chart_data.json"        │   │
│  │  │   exit_code: 0                                        │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                          │                                   │
│  │                          ▼ 继续循环                          │
│  │                                                              │
│  │  第 3 轮：                                                   │
│  │  ┌──────────────────────────────────────────────────────┐   │
│  │  │ Think:                                                │   │
│  │  │   Thought: 代码执行成功，图表数据已生成                  │   │
│  │  │   Final Answer: 我已经分析了销售数据趋势...             │   │
│  │  │   (没有 Action，说明 LLM 认为任务完成)                  │   │
│  │  └──────────────────────────────────────────────────────┘   │
│  │                                                              │
│  └──────────────────── 循环结束 ────────────────────────────────┘
│
│  ┌─ 收尾阶段 ──────────────────────────────────────────────────┐
│  │  1. 提取 Final Answer 作为回复文本                            │
│  │  2. 收集所有 AgentStep（思考+行动+观察的完整记录）             │
│  │  3. 返回 AgentResult                                         │
│  └──────────────────────────────────────────────────────────────┘
```

---

## 4. 各模块详细设计

### 4.1 `core.py` — AgentExecutor 主循环

**职责：** 驱动整个 ReAct 循环的核心引擎。

```
AgentExecutor
│
├── __init__(llm, tools, memory, max_iterations=10)
│     存储 LLM 客户端、工具列表、记忆管理器、最大迭代次数
│
├── run(user_message, session_id, files, history) → AgentResult
│     主入口方法：
│     ① 组装消息列表（system prompt + history + user message）
│     ② 进入 ReAct 循环
│     ③ 每轮调用 LLM，解析输出
│     ④ 如果输出包含 Action → 调用工具 → 将结果作为 Observation 追加
│     ⑤ 如果输出包含 Final Answer → 结束循环
│     ⑥ 如果超过 max_iterations → 强制结束
│     ⑦ 返回 AgentResult
│
├── _parse_llm_output(text) → AgentAction | AgentFinish
│     解析 LLM 的文本输出：
│     - 包含 "Action:" → 返回 AgentAction（工具名 + 参数）
│     - 包含 "Final Answer:" → 返回 AgentFinish（最终回复）
│     - 都不包含 → 抛出异常，要求 LLM 重新生成
│
└── _call_tool(tool_name, tool_input) → str
      根据工具名找到对应工具实例，调用其 run() 方法
      捕获异常，返回错误信息而不是崩溃
```

### 4.2 `config.py` — 配置管理

**职责：** 集中管理 Agent 的所有配置项。

```
AgentConfig
│
├── LLM 配置
│   ├── model_name: str          # 模型名称（如 "deepseek-chat"）
│   ├── api_key: str             # 从环境变量读取
│   ├── base_url: str            # API 地址（兼容 OpenAI 格式）
│   ├── temperature: float       # 温度参数，控制创造性
│   └── max_tokens: int          # 单次最大输出长度
│
├── Agent 行为配置
│   ├── max_iterations: int = 10 # 最大 ReAct 循环次数（防止死循环）
│   ├── verbose: bool = True     # 是否打印每步日志
│   └── handle_errors: bool = True # 工具出错时是否重试
│
└── 外部服务地址
    └── sandbox_url: str         # 沙箱地址 http://localhost:5001
```

所有配置项从 `.env` 读取，提供合理默认值。

### 4.3 `schemas.py` — 内部数据结构

**职责：** 定义 Agent 运行过程中的数据类型。

```
AgentAction          # LLM 决定调用工具
  ├── tool: str              # 工具名称，如 "execute_code"
  ├── tool_input: dict       # 工具参数，如 {"code": "print(1+1)"}
  └── log: str               # LLM 的思考过程文本

AgentObservation     # 工具执行后的结果
  ├── tool: str              # 工具名称
  ├── result: str            # 执行结果文本
  └── success: bool          # 是否执行成功

AgentStep            # 一个完整的 ReAct 步骤
  ├── action: AgentAction
  └── observation: AgentObservation

AgentResult          # Agent 最终返回给路由层的结果
  ├── output: str            # 最终回复文本
  ├── steps: list[AgentStep] # 所有中间步骤记录
  ├── token_usage: dict      # Token 消耗统计
  └── iterations: int        # 实际循环次数
```

### 4.4 `tools/` — 工具箱

#### `tools/base.py` — 工具抽象基类

所有工具都继承自这个基类，保证接口统一：

```
BaseTool (抽象类)
│
├── name: str                # 工具名称，如 "execute_code"
├── description: str         # 工具描述（会放入系统提示词，告诉 LLM 这个工具能做什么）
│
├── run(**kwargs) → str      # 抽象方法：执行工具，返回结果字符串
└── get_schema() → dict      # 返回参数的 JSON Schema（告诉 LLM 这个工具需要什么参数）
```

#### `tools/code_executor.py` — 代码执行工具

```
CodeExecutorTool(BaseTool)
│
├── name = "execute_code"
├── description = "执行 Python 代码，用于数据处理、分析和生成图表数据"
│
├── run(code: str) → str
│     ① 调用沙箱 API：POST http://sandbox:5001/execute
│     ② 发送 {"code": code, "timeout": 30}
│     ③ 返回沙箱的 stdout（成功）或 stderr（失败）
│     ④ 如果沙箱不可达，返回错误提示
│
└── 使用场景：
    - 用 pandas 处理数据
    - 生成 ECharts 所需的 JSON 数据
    - 执行统计分析
```

#### `tools/file_reader.py` — 文件读取工具

```
FileReaderTool(BaseTool)
│
├── name = "read_file"
├── description = "读取用户上传的文件内容，支持 CSV、Excel、JSON 格式"
│
├── run(file_path: str) → str
│     ① 根据文件扩展名选择读取方式
│     ② CSV → pandas.read_csv → 返回前 N 行文本
│     ③ Excel → pandas.read_excel → 返回前 N 行文本
│     ④ JSON → json.load → 返回格式化文本
│     ⑤ 返回文件基本信息（行数、列数、列名）
│
└── 使用场景：
    - Agent 需要查看用户上传的数据内容
```

#### `tools/data_preview.py` — 数据预览工具

```
DataPreviewTool(BaseTool)
│
├── name = "data_preview"
├── description = "快速预览数据文件的结构信息，包括列名、数据类型、基本统计"
│
├── run(file_path: str) → str
│     ① 读取文件
│     ② 返回：shape（行列数）、dtypes（每列类型）、head（前5行）、describe（统计摘要）
│     ③ 比 file_reader 更结构化，侧重数据概况
│
└── 使用场景：
    - Agent 第一步通常先预览数据，了解数据结构
```

#### 工具注册表 `tools/__init__.py`

```
# 集中管理所有工具
TOOL_REGISTRY = {
    "execute_code": CodeExecutorTool(),
    "read_file":    FileReaderTool(),
    "data_preview": DataPreviewTool(),
}

def get_tools() → list[BaseTool]
def get_tool(name: str) → BaseTool
def get_tools_description() → str   # 生成工具描述文本，嵌入系统提示词
```

### 4.5 `prompts/system_prompt.py` — 系统提示词

**职责：** 定义 Agent 的角色、行为规则、输出格式。

```
SYSTEM_PROMPT 模板（大意）：

"""
你是一个专业的数据分析助手（ChatChart Agent）。

## 你的能力
- 分析用户上传的数据文件（CSV/Excel/JSON）
- 使用 Python 代码进行数据处理和统计分析
- 生成 ECharts 图表数据（JSON 格式）

## 可用工具
{tools_description}

## 工作流程
1. 先预览数据，了解数据结构
2. 根据用户需求，编写 Python 代码处理数据
3. 生成图表所需的 JSON 数据
4. 用自然语言向用户解释分析结果

## 输出格式
你必须严格按照以下格式输出：

Thought: （你的思考过程）
Action: （工具名称）
Action Input: （工具参数，JSON 格式）

或者当你认为任务完成时：

Thought: （总结思考）
Final Answer: （给用户的最终回复）

## 规则
- 每次只调用一个工具
- 操作数据前先预览数据结构
- 代码中用 print() 输出关键结果
- 图表数据输出为 JSON，前端会用 ECharts 渲染
- 如果代码执行出错，分析错误原因并修复后重试
- 最终回复要简洁、有洞察，用中文
"""
```

### 4.6 `memory/conversation.py` — 记忆管理

**职责：** 管理对话历史，确保不超出 LLM 的上下文窗口。

```
ConversationMemory
│
├── __init__(max_tokens=4000)
│
├── load_history(messages: list[Message]) → list[dict]
│     ① 将数据库 Message 记录转为 OpenAI 消息格式
│     ② sender="user" → {"role": "user", "content": ...}
│     ③ sender="agent" → {"role": "assistant", "content": ...}
│     ④ sender="system" → {"role": "system", "content": ...}
│
├── truncate(messages: list[dict]) → list[dict]
│     上下文裁剪策略：
│     ① 估算消息总 token 数
│     ② 如果超过 max_tokens，从最早的消息开始丢弃
│     ③ 始终保留最近 N 条消息（滑动窗口）
│     ④ （进阶）对早期对话做摘要压缩
│
└── build_messages(system_prompt, history, user_message, agent_steps) → list[dict]
      组装完整的 LLM 输入：
      [system_prompt] + [truncated history] + [agent_steps] + [user_message]
```

---

## 5. 数据流全链路

```
┌─────────────┐     ┌──────────┐     ┌───────────────────┐     ┌──────────┐
│   前端      │────▶│  路由层   │────▶│    Agent 核心      │────▶│   LLM    │
│  (Vue 3)   │     │ sessions │     │  AgentExecutor    │     │  (API)   │
└─────────────┘     └──────────┘     └────────┬──────────┘     └──────────┘
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                              ┌──────────┐ ┌──────┐ ┌───────┐
                              │ 沙箱执行  │ │ 文件 │ │ 数据  │
                              │ (Docker) │ │ 读取 │ │ 预览  │
                              └──────────┘ └──────┘ └───────┘

具体流程:

1. 前端 POST /sessions/5/messages
   body: {"content": "分析销售额趋势"}

2. sessions.py 路由:
   a. 保存用户消息 → Message(sender="user")
   b. 查询会话关联的文件 → [File(csv)]
   c. 加载历史消息 → [Message, Message, ...]

3. 调用 AgentExecutor.run():
   a. memory.build_messages() 组装上下文
   b. ReAct 循环开始：
      - 调用 LLM → 解析输出
      - 如果是 Action → 调用工具 → 追加观察结果
      - 如果是 Final Answer → 结束
   c. 返回 AgentResult

4. sessions.py 路由:
   a. 保存 Agent 回复 → Message(sender="agent")
   b. 返回 MessageResponse 给前端
```

---

## 6. 错误处理策略

```
错误类型                    处理方式
─────────────────────────────────────────────────
LLM 输出格式不符合规范  →  追加提示消息，要求重新输出
工具调用失败（代码报错）→  将错误信息作为 Observation 反馈给 LLM，让它自行修复
沙箱不可达             →  返回错误消息给用户，不重试
超过 max_iterations    →  强制结束，返回已有的部分结果 + 超时提示
LLM API 超时/限流      →  重试 1 次，仍失败则返回错误
文件不存在             →  工具返回 "文件不存在" 提示，让 LLM 换路径
```

---

## 7. 未来扩展点

```
当前版本先实现核心功能，以下功能后续迭代加入：

Phase 1（当前）: 基础 ReAct 循环 + 3 个工具 + 简单记忆
Phase 2: 流式输出（SSE），前端实时显示 Agent 思考过程
Phase 3: 图表渲染工具，Agent 直接输出 ECharts option JSON
Phase 4: 记忆增强，长期对话摘要压缩
Phase 5: 多 Agent 协作（数据分析 Agent + 代码审查 Agent）
Phase 6: 工具扩展（SQL 查询、网页搜索、图表美化）
```

---

## 8. 关键依赖

```
# 需要安装到 backend/requirements.txt 的新依赖:

httpx          # 异步 HTTP 客户端，用于调用沙箱 API
openai         # LLM API 客户端（兼容 DeepSeek 等 OpenAI 格式的 API）
tiktoken       # Token 计数，用于记忆管理的上下文裁剪
pandas         # 数据读取和预览（工具内部使用）
openpyxl       # Excel 文件读取支持
```

---

## 9. 开发顺序建议

按以下顺序逐个文件实现，每完成一个都可以测试：

```
Step 1  schemas.py          ← 定义数据结构（最简单，其他模块依赖它）
Step 2  config.py           ← 配置管理 + LLM 客户端初始化
Step 3  tools/base.py       ← 工具基类
Step 4  tools/file_reader.py    ← 第一个工具（可以单独测试）
Step 5  tools/data_preview.py   ← 第二个工具
Step 6  tools/code_executor.py  ← 第三个工具（需要沙箱运行）
Step 7  tools/__init__.py   ← 工具注册表
Step 8  prompts/system_prompt.py ← 系统提示词
Step 9  memory/conversation.py  ← 记忆管理
Step 10 core.py             ← AgentExecutor 主循环（最后组装所有模块）
Step 11 __init__.py         ← 对外暴露
```
