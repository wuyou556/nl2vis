# Services 服务层架构设计

> NL2VIS 的业务逻辑层 —— 连接路由层和 Agent 层，编排业务流程

---

## 1. 为什么需要 Service 层？

### 当前问题

```
路由层 (sessions.py)  ──直接操作──►  数据库 (models)
```

路由层直接操作数据库，对于简单 CRUD 没问题。但 Agent 引入后，`send_message` 需要：

```
① 验证会话存在
② 保存用户消息
③ 查询文件列表
④ 加载历史消息
⑤ 组装 AgentExecutor
⑥ 调用 Agent（ReAct 循环）
⑦ 保存 Agent 回复
⑧ 返回结果
```

8 个步骤全部堆在路由函数里 → **路由变胖，职责不清，难以测试**。

### 引入 Service 层后

```
路由层 (sessions.py)
    │  只负责：接收请求、参数校验、调用 Service、返回响应
    ▼
服务层 (services/)          ◄── 新增
    │  只负责：业务编排、调用 Agent、事务管理
    ▼
Agent 层 (agent/core.py)
    │  只负责：ReAct 循环
    ▼
数据库层 (models/)
```

每层只做自己该做的事。路由是"服务员"，Service 是"厨师"，Agent 是"灶台"。

---

## 2. 目录结构

```
services/
├── __init__.py               # 导出 SessionService
├── README.md                 # 本文档
├── session_service.py        # 会话业务逻辑（核心）
├── file_service.py           # 文件业务逻辑（未来）
└── user_service.py           # 用户业务逻辑（未来）
```

当前只实现 `session_service.py`，其余按需扩展。

---

## 3. 核心服务：SessionService

### 3.1 职责边界

```
SessionService 负责：
  ✅ 编排"发消息"的完整业务流程
  ✅ 组装 AgentExecutor（工厂角色）
  ✅ 同步 Agent 调用 → 异步桥接
  ✅ 保存 Agent 回复到数据库
  ✅ 错误兜底（Agent 挂了也不丢消息）

SessionService 不负责：
  ❌ HTTP 请求解析（路由的事）
  ❌ ReAct 循环逻辑（Agent 的事）
  ❌ 用户认证鉴权（路由 + Depends 的事）
```

### 3.2 核心方法：`process_message()`

```
process_message(session_id, user_content, db) → Message

输入：
  session_id: int          # 会话 ID
  user_content: str        # 用户说的话
  db: AsyncSession         # 数据库会话

输出：
  Message 对象              # Agent 的回复消息（已持久化）

流程：
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ① 查询文件列表                                          │
│     select(File).where(session_id=...)                   │
│     → [File("sales.csv"), File("user.json")]             │
│                                                         │
│  ② 查询历史消息                                          │
│     select(Message).where(session_id=...).order_by(...)  │
│     → [Message(user), Message(agent), ...]               │
│                                                         │
│  ③ 组装 AgentExecutor                                    │
│     settings = get_agent_config()                        │
│     llm = create_llm_client(settings)                    │
│     tools = get_tools()                                  │
│     memory = ConversationMemory()                        │
│     executor = AgentExecutor(llm, tools, memory, ...)    │
│                                                         │
│  ④ 异步桥接：asyncio.to_thread()                         │
│     result = await asyncio.to_thread(                    │
│         executor.run,                                    │
│         user_content, session_id, files, history         │
│     )                                                    │
│     → AgentResult(output="销售数据呈现...")               │
│                                                         │
│  ⑤ 保存 Agent 回复                                       │
│     msg = Message(session_id=..., sender="agent",        │
│                   content=result.output)                 │
│     db.add(msg) → await db.flush() → await db.refresh() │
│                                                         │
│  ⑥ 返回 Message 对象                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 错误处理策略

```
AgentExecutor.run() 可能出现的异常：

┌──────────────────────────────────────────────────────────┐
│ 异常类型              │ 处理方式                           │
├──────────────────────────────────────────────────────────┤
│ LLM API 调用失败       │ catch → 存一条 system 消息          │
│ (key 无效、网络不通)    │   "抱歉，AI 服务暂时不可用..."       │
├──────────────────────────────────────────────────────────┤
│ 超过最大迭代次数        │ Agent 内部已处理                     │
│                        │   返回兜底文本，不抛异常              │
├──────────────────────────────────────────────────────────┤
│ 工具执行异常            │ Agent 内部已处理                     │
│                        │   Graceful degradation             │
├──────────────────────────────────────────────────────────┤
│ 未知异常               │ Service 层兜底 catch                 │
│                        │   存 system 消息 + 记录日志           │
└──────────────────────────────────────────────────────────┘

核心原则：无论 Agent 发生什么错误，都要：
  1. 存一条消息告知用户（不能静默失败）
  2. 记录日志（方便排查）
  3. 不抛 500（前端能正常渲染错误消息）
```

---

## 4. 接入路由层

### 4.1 改造前：`send_message` 当前代码

```python
# 只做两件事：验证会话 → 存用户消息 → 返回
@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id, data, db):
    session = (await db.execute(...)).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")

    message = Message(session_id=session_id, sender="user", content=data.content)
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message
```

### 4.2 改造后：引入 Service

```python
@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id, data, db):
    # ① 验证会话
    session = (await db.execute(...)).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")

    # ② 存用户消息
    user_msg = Message(session_id=session_id, sender="user", content=data.content)
    db.add(user_msg)
    await db.flush()

    # ③ 调 Agent（委托给 Service）
    service = SessionService()
    agent_msg = await service.process_message(session_id, data.content, db)

    return agent_msg
```

路由从 8 步缩到 3 步，Agent 相关的复杂逻辑全部封装在 Service 里。

---

## 5. 同步/异步桥接

### 5.1 为什么需要

```
FastAPI 是 async 框架             AgentExecutor.run() 是同步方法
基于 asyncio 事件循环               OpenAI SDK 同步调用
                                  
  事件循环                         线程池
     │                               │
     ├─ 请求1                        ├─ run() #1
     ├─ 请求2                        ├─ run() #2
     ├─ 请求3                        └─ run() #3
     └─ ...
```

如果在 async 函数里直接调用同步的 `executor.run()`，整个事件循环被卡住，**所有请求串行排队**。

### 5.2 解决方案

```python
import asyncio

# ❌ 错误：阻塞事件循环
result = executor.run(user_message, session_id, files, history)

# ✅ 正确：扔到线程池
result = await asyncio.to_thread(
    executor.run, user_message, session_id, files, history
)
```

`asyncio.to_thread()` 在后台线程运行同步代码，主线程不阻塞，其他请求照常处理。

---

## 6. 数据流全链路（含 Service 层）

```
前端 POST /sessions/1/messages
  body: {"content": "分析销售数据"}
    │
    ▼
┌─ 路由层 (sessions.py) ─────────────────────────────────────┐
│  send_message()                                             │
│    ├─ ① 查 Session 存在否                                   │
│    ├─ ② 存 Message(sender="user")                           │
│    └─ ③ service.process_message() ──────────────┐           │
└──────────────────────────────────────────────────┼──────────┘
                                                   │
    ┌──────────────────────────────────────────────┘
    ▼
┌─ 服务层 (session_service.py) ──────────────────────────────┐
│  process_message()                                          │
│    ├─ ① 查 files                                            │
│    ├─ ② 查 history                                          │
│    ├─ ③ 组装 AgentExecutor                                  │
│    ├─ ④ await to_thread(executor.run) ──────────┐           │
│    └─ ⑤ 存 Message(sender="agent")               │           │
└──────────────────────────────────────────────────┼──────────┘
                                                   │
    ┌──────────────────────────────────────────────┘
    ▼
┌─ Agent 层 (core.py) ───────────────────────────────────────┐
│  executor.run()                                             │
│    └─ ReAct 循环: Think → Act → Observe → ...              │
│         ├─ data_preview → 了解数据结构                       │
│         ├─ execute_code → 运行 Python 代码                   │
│         └─ Final Answer → "销售数据呈现上升趋势..."           │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 依赖关系

```
services/
  │
  ├─ 依赖 agent/  （AgentExecutor, get_agent_config, create_llm_client,
  │                 ConversationMemory, get_tools）
  │
  ├─ 依赖 models/ （Message, File, Session）
  │
  └─ 被依赖 api/v1/sessions.py （路由层调用 Service）
```

### 导入清单

```python
# session_service.py 需要导入的：

# 数据库
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.file import File

# Agent
from app.agent import (
    AgentExecutor,
    get_agent_config,
    create_llm_client,
    ConversationMemory,
    get_tools,
)

# 标准库
import asyncio
import logging
```

---

## 8. 未来扩展

```
Phase 1（当前）: SessionService.process_message()
               - 发消息 + 调 Agent + 存回复

Phase 2: FileService
               - 文件上传、删除、格式校验
               - 文件大小限制、类型白名单

Phase 3: 流式输出（SSE）
               - Service 层支持 async generator
               - 边跑 Agent 边推送给前端

Phase 4: 异步任务（Celery）
               - 耗时分析任务交给 Celery worker
               - Service 只创建任务 + 返回 task_id
               - 前端轮询或 WebSocket 获取进度
```

---

## 9. 设计原则回顾

| 原则 | 体现 |
|------|------|
| **单一职责** | 路由只做 HTTP 事，Service 只做业务编排，Agent 只做推理 |
| **依赖倒置** | 路由依赖 Service 抽象，不直接碰 Agent 或 LLM |
| **开闭原则** | 新增文件处理逻辑 → 加 FileService，不改 SessionService |
| **错误隔离** | Agent 挂了不影响路由，Service 兜底存 system 消息 |
| **可测试性** | Service 可以 mock AgentExecutor，不依赖真实 LLM |
