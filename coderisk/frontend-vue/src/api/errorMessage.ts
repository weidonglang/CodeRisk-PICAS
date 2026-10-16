export function requestErrorMessage(error: {
  code?: string
  response?: { status?: number; data?: { message?: unknown } }
}): string {
  if (error.code === 'ECONNABORTED') return '请求超时，请稍后重试'
  if (!error.response) return '后端连接失败，请检查服务状态'
  if (error.response.status && error.response.status >= 500) return '后端服务暂不可用，请稍后重试'
  return typeof error.response.data?.message === 'string' && error.response.data.message.trim()
    ? error.response.data.message : '请求失败'
}
