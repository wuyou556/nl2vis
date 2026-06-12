import { defineStore } from 'pinia'
import { ref, computed, nextTick } from 'vue'
import type { MessageResponse, FileResponse, SSEEvent } from '@/types/api'
import * as messageApi from '@/api/message'
import * as fileApi from '@/api/file'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<MessageResponse[]>([])
  const files = ref<FileResponse[]>([])
  const sending = ref(false)
  const error = ref<string | null>(null)
  const currentAbortController = ref<AbortController | null>(null)

  // 流式输出状态
  const streamingContent = ref('')
  const streamingToolCalls = ref<Array<{ tool: string; input: any; result?: string; success?: boolean }>>([])

  // 按时间排序的消息列表
  const sortedMessages = computed(() =>
    [...messages.value].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
  )

  // 加载某个会话的消息和文件
  async function loadChat(sessionId: number) {
    const [msgList, fileList] = await Promise.all([
      messageApi.getMessages(sessionId),
      fileApi.getFiles(sessionId),
    ])
    messages.value = msgList
    files.value = fileList
    error.value = null
  }

  // 发送消息并等待 Agent 回复（非流式，备用）
  async function sendMessage(sessionId: number, content: string) {
    // 先把用户消息加到列表（乐观更新）
    const tempUserMsg: MessageResponse = {
      id: Date.now(),
      session_id: sessionId,
      sender: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value.push(tempUserMsg)

    sending.value = true
    error.value = null

    try {
      const agentMsg = await messageApi.sendMessage(sessionId, { content })
      messages.value.push(agentMsg)
    } catch (e: any) {
      error.value = e?.message ?? '发送失败'
      messages.value.pop()
    } finally {
      sending.value = false
    }
  }

  // 发送消息（流式输出）
  function sendMessageStream(sessionId: number, content: string) {
    // 先把用户消息加到列表（乐观更新）
    const tempUserMsg: MessageResponse = {
      id: Date.now(),
      session_id: sessionId,
      sender: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value.push(tempUserMsg)

    sending.value = true
    error.value = null
    streamingContent.value = ''
    streamingToolCalls.value = []

    // 创建临时的 agent 消息（用于实时显示流式内容）
    const tempAgentMsg: MessageResponse = {
      id: Date.now() + 1,
      session_id: sessionId,
      sender: 'agent',
      content: '',
      created_at: new Date().toISOString(),
    }
    messages.value.push(tempAgentMsg)

    // 记录临时消息的索引，用于后续更新
    const agentMsgIndex = messages.value.length - 1

    const controller = messageApi.sendMessageStream(
      sessionId,
      { content },
      (event: SSEEvent) => {
        switch (event.type) {
          case 'token':
            streamingContent.value += event.content || ''
            // 更新临时消息的内容（使用索引访问，确保响应式更新）
            messages.value[agentMsgIndex] = {
              ...messages.value[agentMsgIndex],
              content: streamingContent.value
            }
            break

          case 'tool_call':
            streamingToolCalls.value.push({
              tool: event.tool || '',
              input: event.input,
            })
            break

          case 'tool_result':
            const lastTool = streamingToolCalls.value[streamingToolCalls.value.length - 1]
            if (lastTool) {
              lastTool.result = event.result
              lastTool.success = event.success
            }
            break

          case 'final':
            // 流式完成，更新最终内容
            messages.value[agentMsgIndex] = {
              ...messages.value[agentMsgIndex],
              content: event.output || streamingContent.value
            }
            sending.value = false
            break

          case 'error':
            error.value = event.message || '流式输出错误'
            sending.value = false
            break
        }
      },
      (err) => {
        error.value = err.message
        sending.value = false
      }
    )

    currentAbortController.value = controller
  }

  // 取消当前流式请求
  function cancelStream() {
    currentAbortController.value?.abort()
    currentAbortController.value = null
    sending.value = false
  }

  async function uploadFile(sessionId: number, file: File) {
    const result = await fileApi.uploadFile(sessionId, file)
    files.value.push(result)
    return result
  }

  async function removeFile(sessionId: number, fileId: number) {
    await fileApi.deleteFile(sessionId, fileId)
    files.value = files.value.filter(f => f.id !== fileId)
  }

  // 切换会话时清空，避免看到上一个会话的数据
  function clearChat() {
    cancelStream()
    messages.value = []
    files.value = []
    error.value = null
    sending.value = false
    streamingContent.value = ''
    streamingToolCalls.value = []
  }

  return {
    messages, files, sending, error,
    streamingContent, streamingToolCalls,
    sortedMessages,
    loadChat, sendMessage, sendMessageStream, cancelStream,
    uploadFile, removeFile, clearChat,
  }
})
