<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits<{
  upload: [file: File]
}>()

const props = defineProps<{
  disabled?: boolean
}>()

const isDragging = ref(false)
let dragCounter = 0

const ALLOWED_TYPES = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/json',
]
const ALLOWED_EXTS = ['.csv', '.xlsx', '.xls', '.json']
const MAX_SIZE = 50 * 1024 * 1024 // 50MB

function validate(file: File): boolean {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTS.includes(ext)) {
    ElMessage.warning('仅支持 CSV、Excel、JSON 文件')
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.warning('文件不能超过 50MB')
    return false
  }
  return true
}

// 点击上传：触发隐藏的 input
function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) {
    const file = input.files[0]
    if (validate(file)) emit('upload', file)
  }
  input.value = ''
}

// 拖拽上传：监听整个页面
function onDragEnter(e: DragEvent) {
  e.preventDefault()
  dragCounter++
  if (dragCounter === 1) isDragging.value = true
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
}

function onDragLeave(e: DragEvent) {
  e.preventDefault()
  dragCounter--
  if (dragCounter === 0) isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragCounter = 0
  isDragging.value = false
  if (props.disabled) return
  const file = e.dataTransfer?.files[0]
  if (file && validate(file)) emit('upload', file)
}

onMounted(() => {
  document.addEventListener('dragenter', onDragEnter)
  document.addEventListener('dragover', onDragOver)
  document.addEventListener('dragleave', onDragLeave)
  document.addEventListener('drop', onDrop)
})

onUnmounted(() => {
  document.removeEventListener('dragenter', onDragEnter)
  document.removeEventListener('dragover', onDragOver)
  document.removeEventListener('dragleave', onDragLeave)
  document.removeEventListener('drop', onDrop)
})
</script>

<template>
  <!-- 拖拽遮罩层 -->
  <Teleport to="body">
    <div v-if="isDragging" class="drop-overlay">
      <div class="drop-hint">📂 松开即可上传文件</div>
    </div>
  </Teleport>
</template>

<style scoped>
.drop-overlay {
  position: fixed;
  inset: 0;
  background: rgba(64, 158, 255, 0.15);
  border: 3px dashed #409eff;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-hint {
  font-size: 20px;
  color: #409eff;
  background: #fff;
  padding: 16px 32px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
