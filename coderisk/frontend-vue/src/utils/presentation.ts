export function percent(value: number | null | undefined, digits = 0): string {
  if (value == null || !Number.isFinite(value) || value < 0 || value > 1) return '-'
  return `${(value * 100).toFixed(digits)}%`
}

export function margin(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '-'
  const points = value * 100
  return `${points >= 0 ? '+' : ''}${points.toFixed(1)} pp`
}

export function dateTime(value: string | null | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return '-'
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(date)
}

export function progress(done: number, total: number): number {
  return total > 0 && Number.isFinite(done) && Number.isFinite(total)
    ? Math.min(100, Math.max(0, Math.round(done / total * 100))) : 0
}

export function includesQuery(query: string, ...values: unknown[]): boolean {
  const normalized = query.trim().toLocaleLowerCase()
  return !normalized || values.some(value => String(value ?? '').toLocaleLowerCase().includes(normalized))
}

const risks = {
  LOW: { label: '低风险', tone: 'success' },
  MEDIUM: { label: '中风险', tone: 'info' },
  ELEVATED: { label: '较高风险', tone: 'warning' },
  HIGH: { label: '高风险', tone: 'danger' },
} as const

const states = {
  PENDING: { label: '待启动', tone: 'info' },
  QUEUED: { label: '排队中', tone: 'warning' },
  RUNNING: { label: '分析中', tone: 'primary' },
  PARTIAL: { label: '部分完成', tone: 'warning' },
  FINISHED: { label: '已完成', tone: 'success' },
  FAILED: { label: '失败', tone: 'danger' },
  CANCELLED: { label: '已取消', tone: 'info' },
} as const

export function riskMeta(level: string) {
  return risks[level as keyof typeof risks] ?? { label: '未知', tone: 'info' as const }
}

export function taskMeta(status: string) {
  return states[status as keyof typeof states] ?? { label: '未知', tone: 'info' as const }
}
