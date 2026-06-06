import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MessageResponse, FileResponse } from '@/types/api'
import * as messageApi from '@/api/message'
import * as fileApi from '@/api/file'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<MessageResponse[]>([])
  const files = ref<FileResponse[]>([])
  const sending = ref(false)
  const error = ref<string | null>(null)

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

  // 发送消息并等待 Agent 回复
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
    messages.value = []
    files.value = []
    error.value = null
    sending.value = false
  }

  return {
    messages, files, sending, error,
    sortedMessages,
    loadChat, sendMessage, uploadFile, removeFile, clearChat,
  }
})
