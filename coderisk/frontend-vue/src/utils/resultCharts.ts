// Presentation only: every score and risk classification still comes from the API.
export function scorePosition(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? value * 100 : null
}

export function scoreDifference(raw: unknown, canonical: unknown): number | null {
  return scorePosition(raw) !== null && scorePosition(canonical) !== null
    ? (canonical as number) - (raw as number) : null
}

export function riskDistribution(summary: Record<string, unknown> | null) {
  const definitions = [
    { key: 'lowCount', level: 'LOW', label: '低风险', color: '#359a86' },
    { key: 'mediumCount', level: 'MEDIUM', label: '中风险', color: '#558bc9' },
    { key: 'elevatedCount', level: 'ELEVATED', label: '较高风险', color: '#c99439' },
    { key: 'highCount', level: 'HIGH', label: '高风险', color: '#c55a58' },
  ]
  const total = summary?.totalResults
  const counts = definitions.map(item => summary?.[item.key])
  const validCount = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0
  const available = validCount(total) && counts.every(validCount) && counts.reduce((sum, value) => sum + value, 0) === total
  return {
    available,
    total: available ? total : null,
    segments: definitions.map((item, index) => ({ ...item,
      count: available ? counts[index] as number : null,
      share: available && total > 0 ? (counts[index] as number) / total * 100 : 0,
    })),
  }
}

export function adjustmentBar(value: unknown, scale: number) {
  if (typeof value !== 'number' || !Number.isFinite(value) || !(scale > 0) || !Number.isFinite(scale)) return null
  const width = Math.min(50, Math.abs(value) / scale * 50)
  return { left: value < 0 ? 50 - width : 50, width }
}
