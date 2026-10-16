import { readonly, ref } from 'vue'
import { getSystemHealth, type SystemHealth } from '../api/systemApi'

const health = ref<SystemHealth | null>(null)
const checking = ref(false)
const healthError = ref('')
let request: Promise<void> | undefined

function refreshHealth(): Promise<void> {
  if (request) return request
  checking.value = true
  request = getSystemHealth().then(response => {
    if (!response.success || response.data.service !== 'coderisk-backend') throw new Error('服务响应不匹配')
    health.value = response.data
    healthError.value = ''
  }).catch(error => {
    health.value = null
    healthError.value = error instanceof Error ? error.message : '后端连接失败'
  }).finally(() => { checking.value = false; request = undefined })
  return request
}

export function useSystemStatus() {
  return { health: readonly(health), checking: readonly(checking), healthError: readonly(healthError), refreshHealth }
}
