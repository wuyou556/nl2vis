export interface SniffResult {
  textParts: string[]
  chartOptions: Record<string, unknown>[]
}

// 从 Agent 文本中提取 ECharts JSON
export function sniffECharts(text: string): SniffResult {
  const textParts: string[] = []
  const chartOptions: Record<string, unknown>[] = []

  // 优先匹配 ```echarts ... ``` 代码块
  const codeBlockRegex = /```echarts\s*\n([\s\S]*?)```/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = codeBlockRegex.exec(text)) !== null) {
    // 代码块之前的文本
    const before = text.slice(lastIndex, match.index).trim()
    if (before) textParts.push(before)

    // 尝试解析 JSON
    try {
      const json = JSON.parse(match[1].trim())
      chartOptions.push(json)
    } catch {
      // 解析失败，当作普通文本
      textParts.push(match[0])
    }

    lastIndex = match.index + match[0].length
  }

  // 剩余文本
  const remaining = text.slice(lastIndex).trim()
  if (remaining) textParts.push(remaining)

  // 如果没匹配到代码块，尝试找裸 JSON
  if (!chartOptions.length) {
    const jsonMatch = text.match(/\{[\s\S]*"series"[\s\S]*\}/)
    if (jsonMatch) {
      try {
        const json = JSON.parse(jsonMatch[0])
        chartOptions.push(json)
        // 从文本中移除 JSON 部分
        const cleaned = text.replace(jsonMatch[0], '').trim()
        return { textParts: cleaned ? [cleaned] : [], chartOptions }
      } catch {
        // 解析失败，返回纯文本
      }
    }
  }

  return { textParts, chartOptions }
}
