<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  option: Record<string, unknown>
  height?: string
}>()

const chartRef = ref<HTMLElement | null>(null)
let instance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  instance = echarts.init(chartRef.value)
  instance.setOption(props.option, { notMerge: true })
}

function handleResize() {
  instance?.resize()
}

// option 变化时更新图表
watch(
  () => props.option,
  (newOption) => {
    if (instance) {
      instance.setOption(newOption, { notMerge: true })
    }
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  instance?.dispose()
  instance = null
})
</script>

<template>
  <div
    ref="chartRef"
    class="echart-container"
    :style="{ height: height || '400px' }"
  />
</template>

<style scoped>
.echart-container {
  width: 100%;
}
</style>
