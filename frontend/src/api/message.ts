import request from "@/api/request"
import type {MessageCreate, MessageResponse, SSEEvent} from "@/types/api"

// 后端 API 基础地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// 获取消息列表
export function getMessages(id: number): Promise<MessageResponse[]> {
    return request.get(`/sessions/${id}/messages`)
}

// 发送消息（非流式）
export function sendMessage(id: number, data: MessageCreate): Promise<MessageResponse> {
    return request.post(`/sessions/${id}/messages`, data)
}

// 发送消息（流式输出）
export function sendMessageStream(
    sessionId: number,
    data: MessageCreate,
    onEvent: (event: SSEEvent) => void,
    onError?: (error: Error) => void
): AbortController {
    const controller = new AbortController()
    const signal = controller.signal

    fetch(`${API_BASE_URL}/sessions/${sessionId}/messages/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal,
    })
        .then(async (response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) {
                throw new Error('ReadableStream not supported')
            }

            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })

                // 解析 SSE 格式
                const lines = buffer.split('\n')
                buffer = lines.pop() || '' // 保留未完成的行

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const event: SSEEvent = JSON.parse(line.slice(6))
                            onEvent(event)
                        } catch (e) {
                            console.error('Failed to parse SSE event:', e)
                        }
                    }
                }
            }

            // 处理剩余 buffer
            if (buffer.startsWith('data: ')) {
                try {
                    const event: SSEEvent = JSON.parse(buffer.slice(6))
                    onEvent(event)
                } catch (e) {
                    console.error('Failed to parse SSE event:', e)
                }
            }
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                onError?.(err)
            }
        })

    return controller
}
