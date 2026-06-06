import request from './request'
import type { SessionResponse, SessionUpdate } from '@/types/api'

// 创建会话 — POST /sessions/
// 返回新会话对象（自动生成标题，前端不需要传额外参数）
export function createSession(): Promise<SessionResponse> {
  return request.post('/sessions/')
}

// 获取会话列表 — GET /sessions/
// 返回当前用户的所有会话，按 id 降序排列（后端已排序）
export function getSessions(): Promise<SessionResponse[]> {
  return request.get('/sessions/')
}

// 获取单个会话 — GET /sessions/{id}
export function getSession(id: number): Promise<SessionResponse> {
  return request.get(`/sessions/${id}`)
}

// 更新会话（改标题）— PUT /sessions/{id}
// data 只传需要改的字段，如 { title: "新标题" }
export function updateSession(id: number, data: SessionUpdate): Promise<SessionResponse> {
  return request.put(`/sessions/${id}`, data)
}

// 关闭会话 — DELETE /sessions/{id}
// 后端返回 204 No Content，没有响应体，所以返回类型是 void
export function closeSession(id: number): Promise<void> {
  return request.delete(`/sessions/${id}`)
}
