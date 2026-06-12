// ── 用户 ──
export interface UserCreate {
  username: string
  email: string
  password: string
}

export interface UserUpdate {
  username?: string
  email?: string
  password?: string
  is_active?: boolean
}

export interface UserResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

// ── 会话 ──
export interface SessionCreate {}

export interface SessionUpdate {
  title?: string
}

export interface SessionResponse {
  id: number
  user_id: number
  title: string | null
  started_at: string
  ended_at: string | null
  status: string
}

// ── 消息 ──
export interface MessageCreate {
  content: string
}

export interface MessageResponse {
  id: number
  session_id: number
  sender: 'user' | 'agent' | 'system'
  content: string
  created_at: string
}

// ── 文件 ──
export interface FileCreate {
  filename: string
}

export interface FileResponse {
  id: number
  session_id: number
  filename: string
  storage_path: string
  content_type: string | null
  size: number | null
  uploaded_at: string
}

// ── 通用 ──
export interface ApiError {
  detail: string
}

// ── SSE 流式事件 ──
export interface SSEEvent {
  type: 'token' | 'tool_call' | 'tool_result' | 'retry' | 'final' | 'error'
  content?: string
  tool?: string
  input?: any
  result?: string
  success?: boolean
  output?: string
  message?: string
  iteration?: number
}
