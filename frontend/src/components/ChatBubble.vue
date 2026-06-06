<script setup lang="ts">
import type { MessageResponse } from '@/types/api'

defineProps<{
  message: MessageResponse
}>()

// 格式化时间
function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="bubble-row" :class="message.sender">
    <!-- 头像 -->
    <div class="avatar" v-if="message.sender !== 'user'">
      <span v-if="message.sender === 'agent'">🤖</span>
      <span v-else>⚠️</span>
    </div>

    <!-- 气泡内容 -->
    <div class="bubble" :class="message.sender">
      <div class="content">{{ message.content }}</div>
      <div class="time">{{ formatTime(message.created_at) }}</div>
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
}

/* 用户消息：右对齐 */
.bubble-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.bubble .time {
  font-size: 12px;
  margin-top: 4px;
}

/* 用户气泡 */
.bubble.user {
  background: #409eff;
  color: #fff;
}

.bubble.user .time {
  color: rgba(255, 255, 255, 0.7);
  text-align: right;
}

/* Agent 气泡 */
.bubble.agent {
  background: #f4f4f5;
  color: #303133;
}

.bubble.agent .time {
  color: #909399;
}

/* 系统消息：居中提示 */
.bubble-row.system {
  justify-content: center;
}

.bubble.system {
  background: #fdf6ec;
  color: #e6a23c;
  font-size: 13px;
  max-width: 80%;
  text-align: center;
  border-radius: 20px;
}

.bubble.system .time {
  color: #e6a23c;
  opacity: 0.7;
  text-align: center;
}
</style>
