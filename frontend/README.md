# Frontend Architecture — NL2VIS (ChatChart)

> 自然语言驱动的数据可视化平台前端架构设计文档。
> 本文档是**开发前**的蓝图，所有实现细节以本文档为准。

---

## 1. 技术栈

| 类别 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue 3 | 3.4+ | Composition API + `<script setup>` |
| 语言 | TypeScript | 5.x | 严格模式 |
| 构建工具 | Vite | 5.x | 开发体验 + HMR |
| 路由 | Vue Router | 4.x | 路由守卫做鉴权 |
| 状态管理 | Pinia | 2.x | 替代 Vuex，更轻量 |
| HTTP 客户端 | Axios | 1.x | 拦截器统一处理 token / 错误 |
| 图表 | ECharts | 5.x | Agent 输出 ECharts JSON → 前端渲染 |
| UI 组件库 | Element Plus | 2.x | 快速搭建后台风格界面 |
| CSS 方案 | SCSS | — | BEM 命名，与 Element Plus 主题变量对齐 |
| 代码规范 | ESLint + Prettier | — | 统一代码风格 |
| 图标 | @element-plus/icons-vue | — | 与 Element Plus 配套 |

---

## 2. 目录结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/                    # ── API 请求层 ──
│   │   ├── request.ts          #   Axios 实例 + 拦截器
│   │   ├── auth.ts             #   登录 / 注册 / 获取当前用户
│   │   ├── session.ts          #   会话 CRUD
│   │   ├── message.ts          #   消息列表 / 发送消息
│   │   └── file.ts             #   文件上传 / 列表 / 删除
│   │
│   ├── assets/                 # ── 静态资源 ──
│   │   ├── styles/
│   │   │   ├── variables.scss  #   SCSS 变量（主色、字号、间距）
│   │   │   ├── reset.scss      #   全局样式重置
│   │   │   └── global.scss     #   全局通用样式
│   │   └── images/             #   图片资源
│   │
│   ├── components/             # ── 通用组件 ──
│   │   ├── AppHeader.vue       #   顶部导航栏
│   │   ├── ChatBubble.vue      #   单条聊天气泡（区分 user/agent/system）
│   │   ├── ChatInput.vue       #   消息输入框 + 发送按钮
│   │   ├── FileUploader.vue    #   文件拖拽上传组件
│   │   ├── EChartRenderer.vue  #   ECharts 动态渲染器
│   │   ├── AgentSteps.vue      #   Agent 思考步骤折叠面板
│   │   └── MarkdownRenderer.vue#   Markdown 渲染（agent 回复含代码块/表格）
│   │
│   ├── composables/            # ── 组合式函数（Hooks） ──
│   │   ├── useAuth.ts          #   登录态管理 + token 刷新
│   │   ├── useChat.ts          #   发送消息 + 自动滚动 + 加载状态
│   │   └── useECharts.ts       #   ECharts 初始化 / 自适应 / 销毁
│   │
│   ├── layouts/                # ── 布局组件 ──
│   │   └── MainLayout.vue      #   左侧会话列表 + 右侧聊天主区域
│   │
│   ├── router/                 # ── 路由 ──
│   │   └── index.ts            #   路由表 + 导航守卫
│   │
│   ├── store/                  # ── Pinia Store ──
│   │   ├── auth.ts             #   用户认证状态
│   │   ├── session.ts          #   会话列表 + 当前会话
│   │   └── chat.ts             #   当前会话的消息 + 文件
│   │
│   ├── types/                  # ── TypeScript 类型定义 ──
│   │   ├── api.ts              #   后端响应类型（对齐 Pydantic Schema）
│   │   └── echarts.ts          #   ECharts option 类型
│   │
│   ├── utils/                  # ── 工具函数 ──
│   │   ├── storage.ts          #   localStorage 封装（token 存取）
│   │   └── echarts-sniffer.ts  #   从 agent 文本中提取 ECharts JSON
│   │
│   ├── views/                  # ── 页面组件 ──
│   │   ├── LoginView.vue       #   登录页
│   │   ├── RegisterView.vue    #   注册页
│   │   └── ChatView.vue        #   主聊天页（核心页面）
│   │
│   ├── App.vue                 #   根组件
│   └── main.ts                 #   入口：挂载 App + 注册插件
│
├── index.html                  #   Vite 入口 HTML
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tsconfig.node.json
```

> **目录设计原则**：`api/` 只管请求，`store/` 管状态，`composables/` 管可复用逻辑，`views/` 管页面，`components/` 管通用 UI。各层职责清晰，不交叉。

---

## 3. TypeScript 类型定义

前端类型必须与后端 Pydantic Schema 一一对应，确保类型安全。

### `types/api.ts`

```typescript
// ── 用户 ──
export interface UserResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string    // ISO 8601
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string       // "bearer"
  user: UserResponse
}

// ── 会话 ──
export interface SessionResponse {
  id: number
  user_id: number
  title: string | null
  started_at: string
  ended_at: string | null
  status: string           // "active" | "closed"
}

export interface SessionUpdate {
  title?: string
}

// ── 消息 ──
export interface MessageResponse {
  id: number
  session_id: number
  sender: 'user' | 'agent' | 'system'
  content: string
  created_at: string
}

export interface MessageCreate {
  content: string
}

// ── 文件 ──
export interface FileResponse {
  id: number
  session_id: number
  filename: string
  storage_path: string
  content_type: string | null
  size: number | null
  uploaded_at: string
}

// ── 通用 API 响应包装 ──
export interface ApiError {
  detail: string
}
```

> **原则**：每个类型字段名和结构与后端 Schema 完全一致，避免前后端字段映射的心智负担。

---

## 4. API 请求层

### 4.1 Axios 实例 (`api/request.ts`)

```
baseURL: 从环境变量 VITE_API_BASE_URL 读取，默认 http://localhost:8000/api/v1
timeout: 120000  (Agent 执行可能耗时较长)

请求拦截器：
  - 从 localStorage 读取 token
  - 添加 Authorization: Bearer <token>

响应拦截器：
  - 2xx → 直接返回 data
  - 401 → 清除 token，跳转登录页
  - 其他 → ElMessage.error 展示错误信息
```

### 4.2 API 模块划分

| 模块文件 | 函数 | HTTP | 端点 |
|----------|------|------|------|
| `auth.ts` | `register(data)` | POST | `/auth/register` |
| | `login(data)` | POST | `/auth/login` |
| | `getMe()` | GET | `/auth/me` |
| `session.ts` | `createSession()` | POST | `/sessions/` |
| | `getSessions()` | GET | `/sessions/` |
| | `getSession(id)` | GET | `/sessions/{id}` |
| | `updateSession(id, data)` | PUT | `/sessions/{id}` |
| | `closeSession(id)` | DELETE | `/sessions/{id}` |
| `message.ts` | `getMessages(sessionId)` | GET | `/sessions/{id}/messages` |
| | `sendMessage(sessionId, data)` | POST | `/sessions/{id}/messages` |
| `file.ts` | `uploadFile(sessionId, file)` | POST | `/sessions/{id}/files` |
| | `getFiles(sessionId)` | GET | `/sessions/{id}/files` |
| | `deleteFile(sessionId, fileId)` | DELETE | `/sessions/{id}/files/{fid}` |

> **文件上传特殊处理**：`uploadFile` 使用 `FormData`，Content-Type 让浏览器自动设为 `multipart/form-data`。

---

## 5. 状态管理 (Pinia)

### 5.1 `store/auth.ts` — 认证状态

```
state:
  token: string | null          // JWT token
  user:  UserResponse | null    // 当前用户信息

getters:
  isLoggedIn: boolean           // !!token

actions:
  login(username, password)     // 调 API → 存 token + user
  register(username, email, password)
  fetchMe()                     // 刷新当前用户信息
  logout()                      // 清除 token + user，跳转登录页
```

**持久化**：token 存 `localStorage`，页面刷新时从 localStorage 恢复。

### 5.2 `store/session.ts` — 会话状态

```
state:
  sessions: SessionResponse[]   // 会话列表
  currentId: number | null      // 当前活跃会话 ID
  loading: boolean

getters:
  currentSession                // 当前会话对象
  activeSessions                // status === "active" 的会话

actions:
  fetchSessions()               // 加载会话列表
  createSession()               // 新建会话 → 加入列表 → 设为当前
  updateTitle(id, title)        // 重命名会话
  closeSession(id)              // 关闭会话 → 从活跃列表移除
  switchSession(id)             // 切换当前会话 → 触发 chat store 加载
```

### 5.3 `store/chat.ts` — 聊天状态

```
state:
  messages: MessageResponse[]   // 当前会话消息列表
  files: FileResponse[]         // 当前会话文件列表
  sending: boolean              // 是否正在等待 Agent 回复
  error: string | null          // 最近一次错误

getters:
  sortedMessages                // 按 created_at 升序排列

actions:
  loadChat(sessionId)           // 加载消息 + 文件列表
  sendMessage(content)          // 发消息 → 追加 user 消息 → 等待 agent 回复 → 追加 agent 消息
  uploadFile(file)              // 上传文件 → 更新文件列表
  removeFile(fileId)            // 删除文件 → 更新文件列表
  clearChat()                   // 切换会话时清空
```

> **Store 交互关系**：`session.switchSession(id)` → `chat.loadChat(id)`。会话切换自动触发聊天数据加载。

---

## 6. 路由设计

### 6.1 路由表

| 路径 | 组件 | 布局 | 权限 |
|------|------|------|------|
| `/login` | LoginView | 无（独立页面） | 仅未登录 |
| `/register` | RegisterView | 无（独立页面） | 仅未登录 |
| `/` | ChatView | MainLayout | 需登录 |
| `/session/:id` | ChatView | MainLayout | 需登录 |

### 6.2 导航守卫

```
全局前置守卫 (beforeEach):
  - 若目标路由需要登录 且 无 token → 重定向 /login
  - 若目标路由是 login/register 且 有 token → 重定向 /
  - 若有 token 但 store 无 user → 调 fetchMe() 恢复用户信息
```

> **设计决策**：`/` 和 `/session/:id` 共用 ChatView 组件。区别在于 `/` 自动选中最近一个活跃会话，`/session/:id` 选中指定会话。URL 与会话绑定，方便用户分享或刷新页面保持状态。

---

## 7. 页面设计

### 7.1 LoginView / RegisterView

```
┌────────────────────────────────────────────┐
│                                            │
│            📊 ChatChart Logo               │
│         自然语言驱动的数据可视化              │
│                                            │
│    ┌──────────────────────────────┐        │
│    │  用户名                       │        │
│    └──────────────────────────────┘        │
│    ┌──────────────────────────────┐        │
│    │  邮箱        (仅注册)         │        │
│    └──────────────────────────────┘        │
│    ┌──────────────────────────────┐        │
│    │  密码                         │        │
│    └──────────────────────────────┘        │
│                                            │
│    ┌──────────────────────────────┐        │
│    │         登录 / 注册            │        │
│    └──────────────────────────────┘        │
│                                            │
│       还没有账号？去注册 / 已有账号？去登录    │
│                                            │
└────────────────────────────────────────────┘
```

- 居中卡片式布局，简洁
- 登录只需用户名 + 密码
- 注册需要用户名 + 邮箱 + 密码
- 表单校验：用户名 1-64 字符，密码 ≥6 字符，邮箱格式

### 7.2 ChatView（核心页面）

```
┌──────────────────────────────────────────────────────────────────┐
│  AppHeader: Logo + 用户名 + 退出                                  │
├──────────────┬───────────────────────────────────────────────────┤
│              │                                                   │
│  会话列表     │  会话标题栏  [编辑标题] [关闭会话]                    │
│              ├───────────────────────────────────────────────────┤
│  🔍 搜索     │                                                   │
│              │   ┌─────────────────────────────────────────┐     │
│  📁 销售分析  │   │  🤖 Agent: 数据共 1000 行，5 列...       │     │
│  📁 用户行为  │   │  [📊 ECharts 图表渲染区域]               │     │
│  📁 财务报表  │   │  [▶ 展开 Agent 思考过程]                  │     │
│              │   └─────────────────────────────────────────┘     │
│  ──────────  │                                                   │
│  已关闭       │   ┌─────────────────────────────────────────┐     │
│  📁 测试数据  │   │  👤 User: 帮我分析销售趋势               │     │
│              │   └─────────────────────────────────────────┘     │
│              │                                                   │
│              │   ┌─────────────────────────────────────────┐     │
│              │   │  ⚠️ System: 处理你的请求时出了点问题      │     │
│              │   └─────────────────────────────────────────┘     │
│              │                                                   │
│  [+ 新会话]   │                                                   │
│              ├───────────────────────────────────────────────────┤
│              │  📎 上传文件 │ 输入消息...              │ ➤ 发送  │
│              │              │ (Enter 发送, Shift+Enter 换行)     │
│              └───────────────────────────────────────────────────┘
└──────────────┴───────────────────────────────────────────────────┘
```

#### 布局细节

| 区域 | 宽度 | 说明 |
|------|------|------|
| 左侧栏 | 260px | 会话列表 + 新建按钮，可折叠 |
| 右侧主区域 | flex-1 | 标题栏 + 消息区 + 输入区 |
| 标题栏 | 高 56px | 会话标题（可点击编辑）+ 操作按钮 |
| 消息区 | flex-1, 可滚动 | 消息列表，自动滚动到底部 |
| 输入区 | 高自适应 | 文件上传 + 文本框 + 发送按钮 |

---

## 8. 核心组件设计

### 8.1 ChatBubble — 聊天气泡

**Props**:
```
message: MessageResponse    // 消息对象
```

**渲染逻辑**:
```
sender === "user"   → 右对齐蓝色气泡，纯文本
sender === "agent"  → 左对齐白色气泡，渲染 MarkdownRenderer + EChartRenderer
sender === "system" → 左对齐灰色气泡，显示 ⚠️ 图标 + 错误文本
```

**Agent 消息的特殊处理**：Agent 回复的 `content` 中可能同时包含自然语言文本和 ECharts JSON。组件需要：
1. 先用 `echarts-sniffer.ts` 检测并提取 ECharts JSON 块
2. 文本部分交给 `MarkdownRenderer` 渲染
3. ECharts JSON 部分交给 `EChartRenderer` 渲染

### 8.2 EChartRenderer — 图表渲染器

**Props**:
```
option: object       // ECharts option 对象
height?: string      // 图表高度，默认 "400px"
```

**核心逻辑**（由 `useECharts` composable 封装）:
```
1. 模板中创建一个 div 容器，ref 绑定
2. onMounted → echarts.init(container) 保存实例
3. watch(option) → instance.setOption(option, { notMerge: true })
4. ResizeObserver → instance.resize() 自适应容器
5. onUnmounted → instance.dispose() 销毁
```

### 8.3 AgentSteps — Agent 思考步骤

**Props**:
```
steps: AgentStep[]       // ReAct 中间步骤（未来 SSE 推送时使用）
```

> **当前限制**：后端目前只返回最终 `output`，不返回中间 `steps`。此组件先预留接口，等后端 SSE 改造后启用。渲染为 `<el-collapse>` 折叠面板，每步显示 Thought → Action → Observation。

### 8.4 FileUploader — 文件上传

**Props**:
```
sessionId: number
```

**功能**:
- 点击或拖拽上传
- 限制文件类型：`.csv`, `.xlsx`, `.xls`, `.json`
- 限制文件大小：50MB
- 上传进度条
- 上传成功后触发 `chat.uploadFile()` 刷新文件列表

### 8.5 MarkdownRenderer — Markdown 渲染

**Props**:
```
content: string      // Markdown 文本
```

**依赖**: `markdown-it` + `highlight.js`（代码块语法高亮）

**处理逻辑**:
- 普通文本 → markdown-it 渲染
- 代码块 → highlight.js 高亮
- 表格 → markdown-it 自带表格渲染
- **ECharts JSON 代码块** → 不渲染为代码，而是提取出来传给 `EChartRenderer`

### 8.6 ChatInput — 消息输入

**Props**: 无（内部调用 `chat store`）

**功能**:
- `el-input` textarea 类型，自动增高（max 6 行）
- Enter 发送，Shift+Enter 换行
- 发送时 `sending === true` 则禁用输入
- 左侧 📎 按钮触发 FileUploader

---

## 9. ECharts 集成策略

这是前端最关键的设计——Agent 的回复中如何嵌入图表。

### 9.1 数据流

```
Agent Final Answer 文本（含 ECharts JSON）
        │
        ▼
  echarts-sniffer.ts 检测 + 提取
        │
        ├──→ 纯文本部分 → MarkdownRenderer
        │
        └──→ ECharts JSON 部分 → JSON.parse() → EChartRenderer
                                    │
                                    ▼
                              echarts.setOption()
```

### 9.2 `utils/echarts-sniffer.ts` — ECharts JSON 提取器

Agent 回复中的 ECharts JSON 有两种可能的格式：

**格式 A — 代码块标记**（Agent 按提示词输出）:
````
以下是图表配置：
```echarts
{"xAxis": {"type": "category", "data": [...]}, ...}
```
````

**格式 B — 自然语言包裹**:
```
图表数据如下：
{"xAxis": {"type": "category", "data": [...]}, "series": [...]}
```

**提取策略**:
1. 优先匹配 ` ```echarts ... ``` ` 代码块（精确、可靠）
2. 兜底：尝试查找 `{` 开头、包含 `"series"` 键的 JSON 对象
3. 提取后 `JSON.parse()` 验证，失败则当作普通文本

**返回结构**:
```typescript
interface SniffResult {
  textParts: string[]       // 非图表文本片段
  chartOptions: object[]    // 提取出的 ECharts option 对象
}
```

### 9.3 图表自适应

- 图表容器宽度 100%，跟随消息气泡宽度
- 高度默认 400px，Agent 可在 option 中通过自定义字段指定
- `ResizeObserver` 监听容器变化，自动 `resize()`
- 窗口 `resize` 事件也触发重绘

---

## 10. 认证流程

```
┌──────────────┐     POST /auth/login      ┌──────────────┐
│  LoginView   │ ─────────────────────────→ │   Backend    │
│  输入账密     │ ←───────────────────────── │  返回 token  │
└──────┬───────┘     TokenResponse          └──────────────┘
       │
       │ 1. localStorage.setItem('token', access_token)
       │ 2. auth store 保存 token + user
       │ 3. router.push('/')
       │
       ▼
┌──────────────┐     GET /auth/me           ┌──────────────┐
│  ChatView    │ ─────────────────────────→ │   Backend    │
│  刷新页面     │ ←───────────────────────── │  返回 user   │
└──────────────┘     恢复登录态              └──────────────┘
```

**Token 管理策略**:
- 存储位置：`localStorage`（跨标签页共享）
- 请求携带：Axios 请求拦截器自动添加 `Authorization: Bearer <token>`
- 过期处理：响应拦截器捕获 401 → 清除 token → 跳转 `/login`
- 刷新页面：`router.beforeEach` 中检查 token 存在但 user 为空 → 调 `fetchMe()` 恢复

---

## 11. 核心数据流

### 11.1 发送消息（当前同步模式）

```
用户输入 "帮我分析销售趋势"
       │
       ▼
ChatInput → chatStore.sendMessage(content)
       │
       ├── 1. 追加 user 消息到 messages[]（乐观更新）
       ├── 2. sending = true，禁用输入
       │
       ├── 3. POST /sessions/{id}/messages { content }
       │       │
       │       │  (后端: 保存 user msg → Agent 处理 → 保存 agent msg)
       │       │  (耗时可能 10~30 秒)
       │       ▼
       │   返回 MessageResponse (sender="agent", content="...")
       │
       ├── 4. 追加 agent 消息到 messages[]
       ├── 5. sending = false
       └── 6. 自动滚动到底部
```

### 11.2 发送消息（未来 SSE 流式模式）

```
用户输入 "帮我分析销售趋势"
       │
       ▼
ChatInput → chatStore.sendMessage(content)
       │
       ├── 1. 追加 user 消息
       ├── 2. 创建空 agent 消息，追加到 messages[]
       │
       ├── 3. POST /sessions/{id}/messages/stream (SSE endpoint)
       │       │
       │       │  event: thought     → 更新 agent 消息显示 "正在思考..."
       │       │  event: action      → 显示 "调用 data_preview 工具"
       │       │  event: observation → 显示工具返回结果
       │       │  event: done        → 完整 content 回填
       │       ▼
       │   流式更新 agent 消息内容
       │
       ├── 4. 每次更新自动滚动到底部
       └── 5. sending = false
```

> **SSE 是 TIPS.md 中的高优先改进项。** 前端架构在 API 层预留 `message.ts` 中 `sendMessageStream()` 接口，当前用同步实现，后续只需切换调用函数。

---

## 12. 关键交互细节

### 12.1 会话切换

```
左侧栏点击会话
    → sessionStore.switchSession(id)
    → chatStore.loadChat(id)
        → 并行: getMessages(id) + getFiles(id)
        → 合并写入 state
    → router.push(`/session/${id}`)
    → 消息区自动滚到底部
```

### 12.2 新建会话

```
点击 [+ 新会话]
    → sessionStore.createSession()
        → POST /sessions/ → 获得新 session
        → 加入 sessions[] 列表
        → switchSession(newId)
    → 右侧显示空白聊天界面
    → 用户可以先上传文件再提问
```

### 12.3 文件上传

```
点击 📎 或拖拽文件
    → FileUploader 校验文件类型 + 大小
    → POST /sessions/{id}/files (multipart/form-data)
    → 成功后 chatStore.files 追加新文件
    → 输入区上方显示已上传文件标签
```

### 12.4 Agent 回复中的图表

```
Agent 返回内容: "销售趋势如下：\n```echarts\n{\"xAxis\":...}\n```\n从图表可以看出..."

渲染流程:
  ChatBubble (sender="agent")
    → echarts-sniffer.ts 提取
    → textParts: ["销售趋势如下：", "从图表可以看出..."]
    → chartOptions: [{ xAxis: {...}, ... }]
    → 渲染:
        <MarkdownRenderer content="销售趋势如下：" />
        <EChartRenderer :option="chartOptions[0]" />
        <MarkdownRenderer content="从图表可以看出..." />
```

---

## 13. 环境变量

在项目根目录创建 `.env` 文件：

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

开发模式 `.env.development`:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

生产模式 `.env.production`:
```
VITE_API_BASE_URL=/api/v1    # 通过 Nginx 反向代理到后端
```

> **安全注意**：只有 `VITE_` 前缀的变量会被 Vite 注入前端代码。绝不要在前端环境变量中存放密钥。

---

## 14. 开发阶段规划

### Phase 1: 项目骨架 + 认证 ✦ 优先

| 任务 | 说明 |
|------|------|
| Vite + Vue 3 + TS 初始化 | `npm create vite@latest` |
| 安装依赖 | Element Plus, Pinia, Vue Router, Axios, ECharts, SCSS |
| 配置路径别名 | `@/` → `src/` |
| `api/request.ts` | Axios 实例 + 拦截器 |
| `store/auth.ts` | 认证状态管理 |
| `router/index.ts` | 路由表 + 守卫 |
| LoginView + RegisterView | 登录注册页面 |
| `utils/storage.ts` | token 存取 |

**验收标准**：能注册、登录、刷新页面保持登录态、退出。

### Phase 2: 聊天核心

| 任务 | 说明 |
|------|------|
| `store/session.ts` | 会话列表管理 |
| `store/chat.ts` | 消息 + 文件状态 |
| MainLayout | 左右分栏布局 |
| ChatView | 主聊天页面骨架 |
| ChatBubble | 三种 sender 样式 |
| ChatInput | 输入框 + 发送 |
| FileUploader | 文件上传 |

**验收标准**：能创建会话、发消息、收到 Agent 回复、上传文件。

### Phase 3: 图表渲染

| 任务 | 说明 |
|------|------|
| `useECharts.ts` | ECharts 生命周期 composable |
| EChartRenderer | 图表渲染组件 |
| MarkdownRenderer | Markdown + 代码高亮 |
| `echarts-sniffer.ts` | ECharts JSON 提取 |
| ChatBubble 整合 | agent 消息文本 + 图表混合渲染 |

**验收标准**：Agent 返回 ECharts JSON 时能渲染出交互式图表。

### Phase 4: 体验打磨

| 任务 | 说明 |
|------|------|
| 会话标题编辑 | 点击编辑 → 调 updateSession |
| 关闭会话 | 调 closeSession → 移入已关闭列表 |
| 消息自动滚动 | 新消息 → smooth scroll to bottom |
| 加载状态 | Agent 思考时显示 loading 动画 |
| 响应式布局 | 移动端左侧栏可折叠 |
| 错误处理 | 网络断开、token 过期、上传失败 |

**验收标准**：整体交互流畅，异常情况有友好提示。

---

## 15. 未来扩展点

| 扩展 | 前端改动 |
|------|----------|
| **SSE 流式输出** | `api/message.ts` 新增 `sendMessageStream()` 使用 `EventSource`，ChatBubble 支持流式文本追加 |
| **Agent 思考过程展示** | AgentSteps 组件启用，后端推送 thought/action/observation 事件 |
| **图表类型推荐** | 在 EChartRenderer 上方加推荐标签栏 |
| **多 Agent 协作** | ChatBubble 区分不同 Agent 的消息，增加 Agent 头像/标签 |
| **导出报告** | 新增"导出"按钮，将聊天记录 + 图表截图打包为 PDF |
| **数据缓存 (Redis)** | 纯后端改动，前端无感知 |
| **深色模式** | 利用 Element Plus 的 dark mode + CSS 变量切换 |

---

## 16. 依赖清单

```json
{
  "dependencies": {
    "vue": "^3.4",
    "vue-router": "^4.3",
    "pinia": "^2.1",
    "axios": "^1.7",
    "element-plus": "^2.7",
    "@element-plus/icons-vue": "^2.3",
    "echarts": "^5.5",
    "markdown-it": "^14.0",
    "highlight.js": "^11.9"
  },
  "devDependencies": {
    "typescript": "^5.4",
    "vite": "^5.2",
    "@vitejs/plugin-vue": "^5.0",
    "sass": "^1.72",
    "eslint": "^8.57",
    "prettier": "^3.2",
    "@types/markdown-it": "^14.0"
  }
}
```

---

> **文档版本**: v1.0 | **最后更新**: 2026-06-05
