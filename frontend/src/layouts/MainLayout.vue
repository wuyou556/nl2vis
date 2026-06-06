<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/store/session'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const sessionStore = useSessionStore()
const auth = useAuthStore()

onMounted(() => {
  sessionStore.fetchSessions()
})

// 新建会话
async function handleCreate() {
  const session = await sessionStore.createSession()
  router.push(`/session/${session.id}`)
}

// 切换会话
function handleSwitch(id: number) {
  sessionStore.switchSession(id)
  router.push(`/session/${id}`)
}

// 退出登录
function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <!-- 左侧栏 -->
    <aside class="sidebar">
      <!-- 顶部：Logo + 新建按钮 -->
      <div class="sidebar-header">
        <h2 class="logo"><img src="/logo.png" alt="logo" class="logo-img" /> ChatChart</h2>
        <el-button type="primary" size="small" @click="handleCreate">
          + 新会话
        </el-button>
      </div>

      <!-- 中部：会话列表 -->
      <div class="session-list">
        <div
          v-for="session in sessionStore.sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === sessionStore.currentId }"
          @click="handleSwitch(session.id)"
        >
          <span class="session-title">
            {{ session.title || '新会话' }}
          </span>
          <el-tag v-if="session.status === 'closed'" size="small" type="info">
            已关闭
          </el-tag>
        </div>

        <el-empty v-if="!sessionStore.sessions.length" description="暂无会话" />
      </div>

      <!-- 底部：用户信息 -->
      <div class="user-area">
        <div class="user-info">
          <el-avatar :size="32">{{ auth.user?.username?.[0] }}</el-avatar>
          <span class="username">{{ auth.user?.username }}</span>
        </div>
        <el-button text size="small" @click="handleLogout">退出</el-button>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.logo {
  font-size: 18px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.logo-img {
  width: 24px;
  height: 24px;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: #e8eaed;
}

.session-item.active {
  background: #d0e0ff;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.user-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-size: 14px;
  color: #303133;
}

.main {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
</style>
