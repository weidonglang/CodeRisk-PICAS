// Descriptive UI statistics only; never used for production scores or decisions.
export interface AnalysisRow {
  id: number
  submissionAFileName?: string
  submissionBFileName?: string
  tokenSimilarity?: number | null
  astSimilarity?: number | null
  canonicalTokenSimilarity?: number | null
  identifierMappingSimilarity?: number | null
  weightedSimilarityScore?: number | null
  dynamicThreshold?: number | null
  riskMargin?: number | null
  riskLevel?: string
  formulaVersion?: string
}

export const analysisDimensions = [
  { key: 'tokenSimilarity', label: 'Raw Token', color: '#558bc9' },
  { key: 'astSimilarity', label: 'AST', color: '#9a83b7' },
  { key: 'canonicalTokenSimilarity', label: 'Canonical', color: '#359a86' },
  { key: 'identifierMappingSimilarity', label: 'Mapping', color: '#c39a55' },
] as const

export function isScore(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
}

export function quantile(sorted: readonly number[], probability: number): number | null {
  if (!sorted.length || probability < 0 || probability > 1 || !Number.isFinite(probability)) return null
  const index = (sorted.length - 1) * probability
  const lower = Math.floor(index)
  return sorted[lower]! + (sorted[Math.ceil(index)]! - sorted[lower]!) * (index - lower)
}

export function describeScores(input: readonly unknown[]) {
  const values = input.filter(isScore).sort((a, b) => a - b)
  return {
    n: values.length, missing: input.length - values.length,
    min: values[0] ?? null, max: values.at(-1) ?? null,
    q1: quantile(values, .25), median: quantile(values, .5), q3: quantile(values, .75),
    mean: values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null,
  }
}

export function scoreHistogram(input: readonly unknown[], bins = 10) {
  if (!Number.isInteger(bins) || bins < 1 || bins > 50) throw new Error('Histogram bins must be an integer in [1, 50]')
  const values = input.filter(isScore)
  const counts = Array<number>(bins).fill(0)
  for (const value of values) counts[Math.min(bins - 1, Math.floor(value * bins))]!++
  return {
    n: values.length, missing: input.length - values.length,
    bins: counts.map((count, index) => ({
      lower: index / bins, upper: (index + 1) / bins, count,
      upperInclusive: index === bins - 1,
      share: values.length ? count / values.length : null,
    })),
  }
}

export function normalizationPairs(rows: readonly AnalysisRow[]) {
  const points = rows.filter(row => isScore(row.tokenSimilarity) && isScore(row.canonicalTokenSimilarity))
    .map(row => ({
      id: row.id, label: `#${row.id}`, fileA: row.submissionAFileName ?? '-', fileB: row.submissionBFileName ?? '-',
      raw: row.tokenSimilarity!, canonical: row.canonicalTokenSimilarity!,
      delta: row.canonicalTokenSimilarity! - row.tokenSimilarity!, riskLevel: row.riskLevel ?? 'UNKNOWN',
    }))
  return {
    points, n: points.length, missing: rows.length - points.length,
    increased: points.filter(point => point.delta > 1e-10).length,
    decreased: points.filter(point => point.delta < -1e-10).length,
    unchanged: points.filter(point => Math.abs(point.delta) <= 1e-10).length,
  }
}

export function dimensionSummaries(rows: readonly AnalysisRow[]) {
  return dimensionsFor(rows).map(dimension => ({ ...dimension,
    ...describeScores(rows.map(row => row[dimension.key])),
  }))
}

export function dimensionHeatmap(rows: readonly AnalysisRow[]) {
  const dimensions = dimensionsFor(rows)
  return rows.flatMap((row, rowIndex) => dimensions.flatMap((dimension, columnIndex) => {
    const value = row[dimension.key]
    return isScore(value) ? [{ id: row.id, rowIndex, columnIndex, value, label: dimension.label }] : []
  }))
}

function dimensionsFor(rows: readonly AnalysisRow[]) {
  const html = rows.length > 0 && rows.every(row => row.formulaVersion === 'HTML_STRUCTURE_FIXED_V1')
  return analysisDimensions.map(dimension => ({ ...dimension, label: html && dimension.key === 'astSimilarity' ? 'HTML 结构' : dimension.label }))
}

export function csvCell(value: unknown): string {
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''
  let text = value == null ? '' : String(value)
  // Source filenames are untrusted spreadsheet text, not formula expressions.
  if (/^\s*[=+\-@]|^[\t\r]/.test(text)) text = "'" + text
  return '"' + text.replaceAll('"', '""') + '"'
}

export function analysisCsv(rows: readonly AnalysisRow[], scope: string) {
  const header = ['scope', 'result_id', 'file_a', 'file_b', 'raw_token_0_1', 'ast_0_1', 'canonical_0_1', 'mapping_0_1', 'weighted_score_0_1', 'threshold_0_1', 'risk_margin', 'risk_level', 'formula_version']
  const lines = rows.map(row => [scope, row.id, row.submissionAFileName, row.submissionBFileName,
    ...analysisDimensions.map(dimension => isScore(row[dimension.key]) ? row[dimension.key] : null),
    isScore(row.weightedSimilarityScore) ? row.weightedSimilarityScore : null,
    isScore(row.dynamicThreshold) ? row.dynamicThreshold : null,
    typeof row.riskMargin === 'number' && Number.isFinite(row.riskMargin) ? row.riskMargin : null,
    row.riskLevel,
    row.formulaVersion,
  ].map(csvCell).join(','))
  return '\uFEFF' + [header.join(','), ...lines].join('\r\n') + '\r\n'
}
