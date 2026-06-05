<script setup lang="ts">
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  window.location.href = '/login'
}
</script>

<template>
  <div class="chat-page">
    <header class="chat-header">
      <span class="logo">📊 ChatChart</span>
      <div class="user-info">
        <span v-if="auth.user">{{ auth.user.username }}</span>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </header>
    <main class="chat-main">
      <p class="placeholder">👋 欢迎使用 ChatChart，Phase 2 将实现聊天功能</p>
    </main>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.logo {
  font-size: 18px;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
}

.placeholder {
  font-size: 18px;
  color: #909399;
}
</style>
