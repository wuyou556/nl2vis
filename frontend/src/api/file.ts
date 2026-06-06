import request from './request'
import type { FileResponse } from '@/types/api'

// 上传文件 — POST /sessions/{id}/files
// 文件上传必须用 FormData 包装，不能直接发 JSON
// Axios 检测到 FormData 会自动设置 Content-Type: multipart/form-data
export function uploadFile(sessionId: number, file: File): Promise<FileResponse> {
  const fd = new FormData()
  fd.append('file', file)   // 'file' 是字段名，和后端 UploadFile 参数名一致
  return request.post(`/sessions/${sessionId}/files`, fd)
}

// 获取文件列表 — GET /sessions/{id}/files
export function getFiles(sessionId: number): Promise<FileResponse[]> {
  return request.get(`/sessions/${sessionId}/files`)
}

// 删除文件 — DELETE /sessions/{id}/files/{fid}
// 两层 id：会话 id + 文件 id
export function deleteFile(sessionId: number, fileId: number): Promise<void> {
  return request.delete(`/sessions/${sessionId}/files/${fileId}`)
}
