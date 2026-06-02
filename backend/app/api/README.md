# NL2VIS API 路由层设计

## 设计原则

- **资源嵌套** — 消息、文件作为会话的子资源，路径体现层级关系
- **认证先行** — 除注册/登录外，所有端点受 JWT 保护
- **嵌套扁平写** — 学习阶段一个文件管理所有会话相关端点，不拆子路由
- **接口预留** — 分析/Agent 端点提前留位，分页参数预留

---

## 目录结构

```
backend/app/api/v1/
├── router.py          # v1 总聚合器
├── auth.py            # 注册 + 登录（公开）
├── users.py           # 用户管理（受保护）
├── sessions.py        # 会话 + 嵌套消息 + 嵌套文件
└── analysis.py        # Agent 流式响应（预留）
```

---

## 全端点一览

```
/api/v1
│
├── /auth
│   ├── POST   /register         注册用户
│   ├── POST   /login            登录，返回 JWT token
│   └── GET    /me               获取当前登录用户信息
│
├── /users                                    ← 受保护
│   ├── GET    /                             用户列表（分页预留）
│   ├── GET    /{user_id}                    查单个
│   ├── PUT    /{user_id}                    更新
│   └── DELETE /{user_id}                    软删除
│
├── /sessions                                 ← 受保护（嵌套消息和文件）
│   ├── POST   /                             创建会话
│   ├── GET    /                             当前用户会话列表
│   │
│   └── /{session_id}
│       ├── GET    /                         会话详情
│       ├── PUT    /                         改标题
│       ├── DELETE /                         关闭会话
│       │
│       ├── /messages                        消息子资源
│       │   ├── GET    /                     消息历史（分页预留）
│       │   └── POST   /                     发送用户消息
│       │
│       └── /files                           文件子资源
│           ├── POST   /                     上传文件
│           ├── GET    /                     会话内文件列表
│           ├── GET    /{file_id}            文件元信息
│           └── DELETE /{file_id}            删除文件
│
└── /analysis                                 ← 受保护（预留）
    └── POST   /{session_id}/chat            发送消息 + 流式返回 Agent 分析结果
```

---

## 数据模型关系

```
User (1) ──────< (N) Session (1) ──────< (N) Message
                              (1) ──────< (N) File
```

- 文件从属于会话（`File.session_id`），而非直接属于用户
- 会话删除时，关联的文件（CASCADE）和消息（CASCADE）一并删除
- 文件上传到本地 `uploads/{session_id}/` 目录

---

## 认证方式

| 项目 | 说明 |
|------|------|
| 协议 | JWT（Bearer Token） |
| 公开端点 | `POST /auth/register`、`POST /auth/login` |
| 受保护端点 | 其余所有端点 |
| 当前用户获取 | `Depends(get_current_user)` — 从 token 解析 user_id，查库返回 User |

路由中没有 `TMP_USER_ID` 硬编码，全部通过依赖注入获取当前登录用户。

---

## 分页设计（预留）

列表端点预留分页参数，当前未实现：

```
GET /sessions/?page=1&page_size=20
GET /sessions/{id}/messages?page=1&page_size=50
```

---

## 文件上传设计

| 项 | 说明 |
|----|------|
| 请求格式 | `multipart/form-data`，字段名 `file` |
| 存储位置 | `backend/uploads/{session_id}/{uuid}.{ext}` |
| 数据库字段 | `storage_path` 存相对路径，不写死绝对路径 |
| 存储策略 | 本地目录（开发） → MinIO/S3（生产） |

---

## Agent 流式响应（预留）

```
POST /analysis/{session_id}/chat
Content-Type: text/event-stream
```

SSE 事件流格式（Agent 接入后实现）：

| event | data 内容 | 说明 |
|-------|-----------|------|
| `agent_thinking` | `{"step": "分析文件..."}` | 当前思考步骤 |
| `agent_code` | `{"code": "..."}` | 生成的 Python 代码 |
| `agent_chart` | `{"chart_option": {...}}` | ECharts 配置 |
| `done` | `{"message_id": 42}` | 完成信号 |

---

## 开发状态

| 端点 | 状态 | 文件 |
|------|------|------|
| `POST /auth/register` | ❌ 待实现 | `auth.py` |
| `POST /auth/login` | ❌ 待实现 | `auth.py` |
| `GET /auth/me` | ❌ 待实现 | `auth.py` |
| `GET /users/...` | ✅ 已有（密码哈希已实现） | `users.py` |
| `PUT /users/...` | ✅ 已有 | `users.py` |
| `DELETE /users/...` | ✅ 已有 | `users.py` |
| `POST /sessions/` | ✅ 已有 | `sessions.py` |
| `GET /sessions/` | ✅ 已有 | `sessions.py` |
| `GET /sessions/{id}/messages` | ✅ 已实现 | `sessions.py` |
| `POST /sessions/{id}/messages` | ✅ 已有 | `sessions.py` |
| `GET /sessions/{id}/files` | ❌ 待实现 | `sessions.py` |
| `POST /sessions/{id}/files` | ❌ 待实现 | `sessions.py` |
| `GET /sessions/{id}/files/{fid}` | ❌ 待实现 | `sessions.py` |
| `DELETE /sessions/{id}/files/{fid}` | ❌ 待实现 | `sessions.py` |
| `POST /analysis/{id}/chat` | ⏳ Agent 接入后实现 | `analysis.py` |

---

## 路由注册结构

```python
# router.py
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)        # /auth
v1_router.include_router(users_router)       # /users
v1_router.include_router(sessions_router)    # /sessions
# v1_router.include_router(analysis_router)  # 预留
```

嵌套路由采用**扁平式**写法：消息和文件端点全部放在 `sessions.py` 中，通过 `/{session_id}/messages` 和 `/{session_id}/files` 路径区分。
