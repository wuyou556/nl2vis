import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import type { MessageResponse, SSEEvent, SessionState } from '@/types/api'
import * as messageApi from '@/api/message'
import * as fileApi from '@/api/file'


export const useChatStore = defineStore('chat', () => {
  // 当前会话 ID
  const currentSessionId = ref<number | null>(null)

  // 所有会话的状态映射（使用 reactive 确保深层响应式）
  const sessionStates = reactive<Map<number, SessionState>>(new Map())

  // 获取当前会话的状态（如果没有则创建）
  function getCurrentState(): SessionState {
    const id = currentSessionId.value
    if (!id) {
      // 返回一个临时的空状态（用于初始化前）
      return reactive({
        messages: [],
        files: [],
        sending: false,
        error: null,
        streamingContent: '',
        streamingToolCalls: [],
        abortController: null,
      })
    }

    if (!sessionStates.has(id)) {
      sessionStates.set(id, reactive({
        messages: [],
        files: [],
        sending: false,
        error: null,
        streamingContent: '',
        streamingToolCalls: [],
        abortController: null,
      }))
    }
    return sessionStates.get(id)!
  }

  // 便捷访问器（当前会话）
  const messages = computed({
    get: () => getCurrentState().messages,
    set: (val) => { getCurrentState().messages = val },
  })

  const files = computed({
    get: () => getCurrentState().files,
    set: (val) => { getCurrentState().files = val },
  })

  const sending = computed({
    get: () => getCurrentState().sending,
    set: (val) => { getCurrentState().sending = val },
  })

  const error = computed({
    get: () => getCurrentState().error,
    set: (val) => { getCurrentState().error = val },
  })

  const streamingContent = computed({
    get: () => getCurrentState().streamingContent,
    set: (val) => { getCurrentState().streamingContent = val },
  })

  const streamingToolCalls = computed({
    get: () => getCurrentState().streamingToolCalls,
    set: (val) => { getCurrentState().streamingToolCalls = val },
  })

  // 按时间排序的消息列表
  const sortedMessages = computed(() =>
    [...messages.value].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
  )

  // 加载某个会话的消息和文件
  async function loadChat(sessionId: number) {
    currentSessionId.value = sessionId
    const state = getCurrentState()

    // 如果已经在发送中，不重新加载（让流式请求继续）
    if (state.sending) return

    const [msgList, fileList] = await Promise.all([
      messageApi.getMessages(sessionId),
      fileApi.getFiles(sessionId),
    ])
    state.messages = msgList
    state.files = fileList
    state.error = null
  }

  // 发送消息并等待 Agent 回复（非流式，备用）
  async function sendMessage(sessionId: number, content: string) {
    const state = getCurrentState()

    // 先把用户消息加到列表（乐观更新）
    const tempUserMsg: MessageResponse = {
      id: Date.now(),
      session_id: sessionId,
      sender: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    state.messages.push(tempUserMsg)

    state.sending = true
    state.error = null

    try {
      const agentMsg = await messageApi.sendMessage(sessionId, { content })
      state.messages.push(agentMsg)
    } catch (e: any) {
      state.error = e?.message ?? '发送失败'
      state.messages.pop()
    } finally {
      state.sending = false
    }
  }

  // 发送消息（流式输出）
  function sendMessageStream(sessionId: number, content: string) {
    const state = getCurrentState()

    // 先把用户消息加到列表（乐观更新）
    const tempUserMsg: MessageResponse = {
      id: Date.now(),
      session_id: sessionId,
      sender: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    state.messages.push(tempUserMsg)

    state.sending = true
    state.error = null
    state.streamingContent = ''
    state.streamingToolCalls = []

    // 创建临时的 agent 消息（用于实时显示流式内容）
    const tempAgentMsg: MessageResponse = {
      id: Date.now() + 1,
      session_id: sessionId,
      sender: 'agent',
      content: '',
      created_at: new Date().toISOString(),
    }
    state.messages.push(tempAgentMsg)

    // 记录临时消息的索引，用于后续更新
    const agentMsgIndex = state.messages.length - 1

    const controller = messageApi.sendMessageStream(
      sessionId,
      { content },
      (event: SSEEvent) => {
        // 始终更新对应会话的状态（闭包捕获的 state）
        switch (event.type) {
          case 'token':
            state.streamingContent += event.content || ''
            // 更新临时消息的内容
            state.messages[agentMsgIndex] = {
              ...state.messages[agentMsgIndex],
              content: state.streamingContent
            }
            break

          case 'tool_call':
            state.streamingToolCalls.push({
              tool: event.tool || '',
              input: event.input,
            })
            break

          case 'tool_result':
            const lastTool = state.streamingToolCalls[state.streamingToolCalls.length - 1]
            if (lastTool) {
              lastTool.result = event.result
              lastTool.success = event.success
            }
            break

          case 'final':
            // 流式完成，更新最终内容
            state.messages[agentMsgIndex] = {
              ...state.messages[agentMsgIndex],
              content: event.output || state.streamingContent
            }
            state.sending = false
            state.abortController = null
            break

          case 'error':
            state.error = event.message || '流式输出错误'
            state.sending = false
            state.abortController = null
            break
        }
      },
      (err) => {
        state.error = err.message
        state.sending = false
        state.abortController = null
      }
    )

    state.abortController = controller
  }

  // 取消指定会话的流式请求
  function cancelStream(sessionId?: number) {
    const id = sessionId ?? currentSessionId.value
    if (!id) return

    const state = sessionStates.get(id)
    if (state) {
      state.abortController?.abort()
      state.abortController = null
      state.sending = false
    }
  }

  async function uploadFile(sessionId: number, file: File) {
    const state = getCurrentState()
    const result = await fileApi.uploadFile(sessionId, file)
    state.files.push(result)
    return result
  }

  async function removeFile(sessionId: number, fileId: number) {
    const state = getCurrentState()
    await fileApi.deleteFile(sessionId, fileId)
    state.files = state.files.filter(f => f.id !== fileId)
  }

  // 切换会话时清空，避免看到上一个会话的数据
  function clearChat() {
    // 取消所有会话的流式请求
    sessionStates.forEach((state) => {
      if (state.abortController) {
        state.abortController.abort()
        state.abortController = null
        state.sending = false
      }
    })
    sessionStates.clear()
    currentSessionId.value = null
  }

  return {
    currentSessionId,
    messages, files, sending, error,
    streamingContent, streamingToolCalls,
    sortedMessages,
    loadChat, sendMessage, sendMessageStream, cancelStream,
    uploadFile, removeFile, clearChat,
  }
})
