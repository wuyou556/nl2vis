<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '@/store/session'
import { useChatStore } from '@/store/chat'
import ChatBubble from '@/components/ChatBubble.vue'
import ChatInput from '@/components/ChatInput.vue'
import FileUploader from '@/components/FileUploader.vue'
import { Edit } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const chatStore = useChatStore()

const messagesRef = ref<HTMLElement | null>(null)
const editingTitle = ref(false)
const titleInput = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

// 当前会话 id（从路由参数取）
const sessionId = ref<number | null>(null)

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 加载会话数据
async function loadSession(id: number) {
  sessionId.value = id
  sessionStore.switchSession(id)
  await chatStore.loadChat(id)
  scrollToBottom()
}

// 路由变化时加载对应会话
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      loadSession(Number(newId))
    } else {
      sessionId.value = null
      chatStore.clearChat()
    }
  },
  { immediate: true }
)

// 新消息自动滚动
watch(
  () => chatStore.messages.length,
  () => scrollToBottom()
)

// 发送消息
async function handleSend(content: string) {
  if (!sessionId.value) return
  await chatStore.sendMessage(sessionId.value, content)
  scrollToBottom()
}

// 上传文件
async function handleUpload(file: File) {
  if (!sessionId.value) return
  await chatStore.uploadFile(sessionId.value, file)
}

// 删除文件
async function handleRemoveFile(fileId: number) {
  if (!sessionId.value) return
  await chatStore.removeFile(sessionId.value, fileId)
}

// 编辑标题
function startEditTitle() {
  titleInput.value = sessionStore.currentSession?.title || ''
  editingTitle.value = true
}

async function saveTitle() {
  if (sessionId.value && titleInput.value.trim()) {
    await sessionStore.updateTitle(sessionId.value, titleInput.value.trim())
  }
  editingTitle.value = false
}

// 关闭会话
async function handleClose() {
  if (!sessionId.value) return
  await sessionStore.closeSession(sessionId.value)
  router.push('/')
}

// 触发文件选择（由 ChatInput 的 📎 按钮调用）
function triggerFileSelect() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.csv,.xlsx,.xls,.json'
  input.onchange = (e: Event) => {
    const target = e.target as HTMLInputElement
    if (target.files?.[0]) handleUpload(target.files[0])
  }
  input.click()
}
</script>

<template>
  <!-- 无会话选中时的空状态 -->
  <div v-if="!sessionId" class="empty-state">
    <p>👋 选择一个会话，或创建新会话开始</p>
  </div>

  <!-- 有会话时的聊天界面 -->
  <div v-else class="chat-view">
    <!-- 标题栏 -->
    <div class="chat-header">
      <div v-if="editingTitle" class="title-edit">
        <el-input
          v-model="titleInput"
          size="small"
          @keyup.enter="saveTitle"
          @blur="saveTitle"
          autofocus
        />
      </div>
      <div v-else class="title-display" @click="startEditTitle">
        {{ sessionStore.currentSession?.title || '新会话' }}
        <el-icon><Edit /></el-icon>
      </div>
      <el-button text size="small" type="danger" @click="handleClose">
        关闭会话
      </el-button>
    </div>

    <!-- 文件列表 -->
    <div v-if="chatStore.files.length" class="file-bar">
      <el-tag
        v-for="file in chatStore.files"
        :key="file.id"
        closable
        @close="handleRemoveFile(file.id)"
        size="small"
      >
        📄 {{ file.filename }}
      </el-tag>
    </div>

    <!-- 消息列表 -->
    <div ref="messagesRef" class="messages">
      <ChatBubble
        v-for="msg in chatStore.sortedMessages"
        :key="msg.id"
        :message="msg"
      />

      <!-- 加载中提示 -->
      <div v-if="chatStore.sending" class="typing">
        <span class="dot" /><span class="dot" /><span class="dot" />
      </div>

      <!-- 空消息提示 -->
      <el-empty
        v-if="!chatStore.sortedMessages.length && !chatStore.sending"
        description="发送消息开始对话"
      />
    </div>

    <!-- 输入区 -->
    <ChatInput
      :disabled="chatStore.sending"
      @send="handleSend"
      @upload="triggerFileSelect"
    />

    <!-- 文件上传（处理拖拽） -->
    <FileUploader
      :disabled="chatStore.sending"
      @upload="handleUpload"
    />
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
  font-size: 16px;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  min-height: 48px;
}

.title-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  color: #303133;
}

.title-display:hover {
  color: #409eff;
}

.title-edit {
  width: 240px;
}

.file-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* 打字动画 */
.typing {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
