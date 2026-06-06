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

  // 关闭会话后本地标记状态
  async function closeSession(id: number) {
    await sessionApi.closeSession(id)
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      sessions.value[idx].status = 'closed'
      sessions.value[idx].ended_at = new Date().toISOString()
    }
    if (currentId.value === id) currentId.value = null
  }

  return {
    sessions, currentId, loading,
    currentSession, activeSessions, closedSessions,
    fetchSessions, createSession, switchSession, updateTitle, closeSession,
  }
})
