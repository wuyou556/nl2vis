<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [content: string]
  upload: []
}>()

defineProps<{
  disabled?: boolean
}>()

const content = ref('')

function handleSend() {
  const text = content.value.trim()
  if (!text) return
  emit('send', text)
  content.value = ''
}

// Enter 发送，Shift+Enter 换行
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <el-button text @click="emit('upload')" :disabled="disabled">
      📎
    </el-button>
    <el-input
      v-model="content"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 6 }"
      placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
      :disabled="disabled"
      @keydown="handleKeydown"
      resize="none"
    />
    <slot name="extra" />
    <el-button
      type="primary"
      @click="handleSend"
      :disabled="disabled || !content.trim()"
    >
      发送
    </el-button>
  </div>
</template>

<style scoped>
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
}
</style>
