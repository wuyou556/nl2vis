import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SessionResponse } from '@/types/api'
import * as sessionApi from '@/api/session'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<SessionResponse[]>([])
  const currentId = ref<number | null>(null)
  const loading = ref(false)

  // 当前选中的会话对象
  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentId.value) ?? null
  )

  // 未关闭的会话
  const activeSessions = computed(() =>
    sessions.value.filter(s => s.status !== 'closed')
  )

  const closedSessions = computed(() =>
    sessions.value.filter(s => s.status === 'closed')
  )

  async function fetchSessions() {
    loading.value = true
    try {
      sessions.value = await sessionApi.getSessions()
    } finally {
      loading.value = false
    }
  }

  // 新建会话并自动切到它
  async function createSession() {
    const newSession = await sessionApi.createSession()
    sessions.value.unshift(newSession)
    currentId.value = newSession.id
    return newSession
  }

  function switchSession(id: number) {
    currentId.value = id
  }

  // 修改标题后同步更新本地列表
  async function updateTitle(id: number, title: string) {
    const updated = await sessionApi.updateSession(id, { title })
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) sessions.value[idx] = updated
  }

  // 删除会话（硬删除，从列表中移除）
  async function closeSession(id: number) {
    await sessionApi.closeSession(id)
    // 后端是硬删除，所以从前端列表中移除
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentId.value === id) currentId.value = null
  }

  return {
    sessions, currentId, loading,
    currentSession, activeSessions, closedSessions,
    fetchSessions, createSession, switchSession, updateTitle, closeSession,
  }
})
