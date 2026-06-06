import request from "@/api/request"
import type {MessageCreate,MessageResponse} from "@/types/api"

// 获取消息列表
export function getMessages(id: number): Promise<MessageResponse[]> {
    return request.get(`/sessions/${id}/messages`)
}

// 发送消息
export function sendMessage(id: number, data: MessageCreate): Promise<MessageResponse> {
    return request.post(`/sessions/${id}/messages`,data)
}
