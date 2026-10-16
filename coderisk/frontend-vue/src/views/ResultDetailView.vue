<script setup lang="ts">
import { ArrowLeft, Refresh, DocumentCopy, Search, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RiskBadge from '../components/RiskBadge.vue'
import ScoreTrack from '../components/ScoreTrack.vue'
import { percent, margin as signedPercent, includesQuery } from '../utils/presentation'
import { scorePosition, scoreDifference, adjustmentBar } from '../utils/resultCharts'

import {
  getResult,
  getResultDiffView,
  getResultEvidence,
  getResultMetrics,
  createTaskReport,
  type DiffView,
  type EvidenceItem,
  type ResultRow,
  type SimilarityMetric,
} from '../api/taskApi'

interface EvidenceFragment {
  tokens?: string[]
  submissionAStartLine?: number
  submissionAEndLine?: number
  submissionBStartLine?: number
  submissionBEndLine?: number
}

interface IdentifierMapping {
  mappingType?: string
  kind?: string
  canonicalName?: string
  scopePath?: string
  submissionAName?: string
  submissionBName?: string
  confidence?: number
}

const route = useRoute()
const router = useRouter()
const resultId = computed(() => Number(route.params.resultId))
const loading = ref(false)
const error = ref('')
const result = ref<ResultRow | null>(null)
const isHtmlResult = computed(() => result.value?.formulaVersion === 'HTML_STRUCTURE_FIXED_V1')
const evidence = ref<EvidenceItem[]>([])
const selectedEvidence = ref<EvidenceItem | null>(null)
const activeTab = ref('evidence')
const evidenceFilter = ref('ALL')
const mappingQuery = ref('')
const wrapCode = ref(false)
const codeLayout = ref('side')
const reportLoading = ref(false)
const filteredEvidence = computed(() => evidence.value.filter(item => evidenceFilter.value === 'ALL' || item.evidenceType === evidenceFilter.value))
const evidenceTypes = computed(() => [...new Set(evidence.value.map(item => item.evidenceType))])
const mappingRows = computed(() => evidence.value.flatMap(item => mappingsOf(item)))
const filteredMappings = computed(() => mappingRows.value.filter(item => includesQuery(mappingQuery.value, item.submissionAName, item.submissionBName, item.canonicalName, item.scopePath, item.kind, item.mappingType)))
let requestVersion = 0
const reviewAssessment = computed(() => evidence.value.find(item => item.metadata.category === 'REVIEW_ASSESSMENT')?.metadata)
const compatibilityContext = computed(() => evidence.value.find(item => item.metadata.category === 'LANGUAGE_COMPATIBILITY')?.metadata)
const templateContext = computed(() => evidence.value.find(item => item.metadata.category === 'SHARED_TEMPLATE_CONTEXT')?.metadata)
function contextSide(context: Record<string, unknown> | undefined, side: string): Record<string, unknown> {
  const value = context?.[`submission${side}`]
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}
function contextPercent(value: unknown) {
  return typeof value === 'number' ? percent(value) : '无可比较代码'
}
function compatibilityLimitations(side: string) {
  const context = contextSide(compatibilityContext.value, side)
  const labels: Record<string, string> = {
    STRUCTURE_UNAVAILABLE: '结构无法解析', NORMALIZATION_UNAVAILABLE: '作用域规范化不可用',
    DECLARED_PYTHON2_NOT_VALIDATED_BY_PYTHON3_PARSER: 'Python 3 解析器不能验证声明的 Python 2 版本',
    PYTHON_DIVISION_REQUIRES_VERSION_SEMANTICS_REVIEW: '旧版 Python 除法语义需要复核',
    DECLARED_VERSION_NEWER_THAN_PARSER_RUNTIME: '声明版本高于当前 Python 解析器版本',
    CPP_SYNTAX_HINT_IN_C_SUBMISSION: 'C 提交中发现 C++ 语法线索',
  }
  return Array.isArray(context.limitations) ? context.limitations.map(value => labels[String(value)] ?? String(value)).join('；') : ''
}
function templateRanges(side: string) {
  const ranges = contextSide(templateContext.value, side).fragments
  return Array.isArray(ranges) ? ranges.map((item: { startLine?: number; endLine?: number }) => `${item.startLine}-${item.endLine}`).join('、') || '无精确匹配' : '无精确匹配'
}
const metrics = ref<SimilarityMetric[]>([])
const diffView = ref<DiffView | null>(null)
const experimentalMetrics = computed(() => metrics.value.filter((item) => item.name.startsWith('CROSSLANG_')))
const irEvidence = computed(() => evidence.value.find((item) => item.evidenceType === 'CROSSLANG_IR_MATCH'))
const controlSummaryEvidence = computed(() => evidence.value.find((item) =>
  item.metadata.summaryKind === 'LIGHTWEIGHT_CONTROL_FLOW_SUMMARY',
))
const dataFlowSummaryEvidence = computed(() => evidence.value.find((item) =>
  item.metadata.summaryKind === 'LIGHTWEIGHT_DATA_FLOW_SUMMARY',
))

const dimensions = computed(() => [
  { label: 'Raw Token', value: result.value?.tokenSimilarity, color: '#558bc9' },
  { label: isHtmlResult.value ? 'HTML 标签树' : 'Basic AST', value: result.value?.astSimilarity, color: '#9a83b7' },
  { label: 'Canonical Token', value: result.value?.canonicalTokenSimilarity, color: '#359a86' },
  { label: 'Identifier Mapping', value: result.value?.identifierMappingSimilarity, color: '#c39a55' },
])
const canonicalDifference = computed(() => scoreDifference(result.value?.tokenSimilarity, result.value?.canonicalTokenSimilarity))
const alertType = computed(() => {
  if (result.value?.riskLevel === 'HIGH') return 'error'
  if (result.value?.riskLevel === 'ELEVATED') return 'warning'
  return 'info'
})

const thresholdAdjustments = computed(() => {
  const adjustment = result.value?.thresholdAdjustment
  return [
    { label: '题目难度', value: adjustment?.difficultyAdjustment },
    { label: '解法空间', value: adjustment?.solutionSpaceAdjustment },
    { label: '模板风险', value: adjustment?.templateRiskAdjustment },
    { label: '自然相似', value: adjustment?.naturalSimilarityAdjustment },
    { label: '历史分布', value: adjustment?.historicalDistributionAdjustment },
  ]
})
const adjustmentScale = computed(() => Math.max(.01, ...thresholdAdjustments.value.map(item => typeof item.value === 'number' && Number.isFinite(item.value) ? Math.abs(item.value) : 0)))

function fragmentsOf(item: EvidenceItem): EvidenceFragment[] {
  const value = item.metadata.fragments
  return Array.isArray(value) ? (value as EvidenceFragment[]) : []
}

function mappingsOf(item: EvidenceItem): IdentifierMapping[] {
  const value = item.metadata.mappings
  return Array.isArray(value) ? (value as IdentifierMapping[]) : []
}

function irSequence(key: 'irSequenceA' | 'irSequenceB') {
  const value = irEvidence.value?.metadata[key]
  return Array.isArray(value) ? value.join(' → ') : '-'
}

function irCoverage(key: 'coverageA' | 'coverageB') {
  const value = irEvidence.value?.metadata[key]
  return typeof value === 'number' ? value : null
}

function metricLabel(name: string) {
  const labels: Record<string, string> = {
    CROSSLANG_IR_SIMILARITY: 'Normalized IR',
    CROSSLANG_CONTROL_SUMMARY_SIMILARITY: '轻量控制摘要',
    CROSSLANG_DATA_FLOW_SUMMARY_SIMILARITY: '轻量数据摘要',
  }
  return labels[name] ?? name
}

function summaryItems(item: EvidenceItem | undefined, key: string) {
  const value = item?.metadata[key]
  if (!value || typeof value !== 'object' || Array.isArray(value)) return []
  return Object.entries(value as Record<string, unknown>).map(([label, content]) => ({
    label,
    value: Array.isArray(content) ? content.join(' → ') || '-' : String(content),
  }))
}

function collectHighlightedLines(side: 'A' | 'B') {
  const lines = new Set<number>()
  for (const item of selectedEvidence.value ? [selectedEvidence.value] : evidence.value) {
    for (const fragment of fragmentsOf(item)) {
      const start = side === 'A' ? fragment.submissionAStartLine : fragment.submissionBStartLine
      const end = side === 'A' ? fragment.submissionAEndLine : fragment.submissionBEndLine
      if (!start || !end) continue
      for (let line = start; line <= end; line += 1) {
        lines.add(line)
      }
    }
  }
  return lines
}

const highlightedA = computed(() => collectHighlightedLines('A'))
const highlightedB = computed(() => collectHighlightedLines('B'))

const selectedHighlights = computed(() => (diffView.value?.highlights ?? []).filter(item => !selectedEvidence.value || item.evidenceId === selectedEvidence.value.id))
const diffHighlightedA = computed(() => new Set(selectedHighlights.value.flatMap(item => rangeLines(item.aRange.startLine, item.aRange.endLine))))
const diffHighlightedB = computed(() => new Set(selectedHighlights.value.flatMap(item => rangeLines(item.bRange.startLine, item.bRange.endLine))))

async function selectEvidence(item: EvidenceItem) {
  selectedEvidence.value = item
  await nextTick()
  for (const pane of document.querySelectorAll('.code-block')) {
    const highlight = pane.querySelector<HTMLElement>('.highlighted')
    if (highlight) pane.scrollTop = Math.max(0, highlight.offsetTop - 24)
  }
  document.getElementById('source-comparison')?.scrollIntoView({ block: 'start' })
}

async function exportReport() {
  if (!result.value || reportLoading.value) return
  const requestedId = resultId.value
  reportLoading.value = true
  try {
    const response = await createTaskReport(result.value.taskId, { format: 'HTML', includeLowRiskPairs: true, includeCodeSnippets: true, includeThresholdExplanation: true })
    if (requestedId !== resultId.value) return
    const link = document.createElement('a')
    link.href = response.data.downloadUrl
    link.download = response.data.fileName
    link.click()
    ElMessage.success('任务报告已生成')
  } catch (err) { if (requestedId === resultId.value) ElMessage.error(err instanceof Error ? err.message : '报告生成失败') }
  finally { reportLoading.value = false }
}

async function copyCode(side: 'A' | 'B') {
  try {
    const code = side === 'A' ? diffView.value?.codeA.code : diffView.value?.codeB.code
    if (code == null) return
    await navigator.clipboard.writeText(code)
    ElMessage.success('代码已复制')
  } catch { ElMessage.error('复制失败，请检查浏览器剪贴板权限') }
}

function evidenceLabel(type: string) {
  return ({ TOKEN_MATCH: 'Token 片段', AST_STRUCTURE: 'AST 结构', AST_STRUCTURE_MATCH: 'AST 结构', IDENTIFIER_MAPPING: '标识符映射',
    CANONICAL_TOKEN_MATCH: '规范化片段', REVIEW_NOTE: '复核说明', PARSER_WARNING: '解析降级',
    CROSSLANG_IR_MATCH: 'IR · 实验性' } as Record<string, string>)[type] ?? type
}

function codeLines(code: string | undefined) {
  return (code ?? '').split(/\r?\n/).map((text, index) => ({ no: index + 1, text }))
}

function hasLine(set: Set<number>, line: number) {
  return set.has(line)
}

function rangeLines(start: number, end: number) {
  if (!start || !end) return []
  const lines = []
  for (let line = start; line <= end; line += 1) {
    lines.push(line)
  }
  return lines
}

async function load() {
  const version = ++requestVersion
  const requestedId = resultId.value
  loading.value = true
  error.value = ''
  try {
    const [resultResponse, evidenceResponse, metricResponse, codePairResponse] = await Promise.all([
      getResult(requestedId),
      getResultEvidence(requestedId),
      getResultMetrics(requestedId),
      getResultDiffView(requestedId),
    ])
    if (version !== requestVersion) return
    result.value = resultResponse.data
    evidence.value = evidenceResponse.data
    metrics.value = metricResponse.data
    diffView.value = codePairResponse.data
  } catch (err) {
    if (version === requestVersion) error.value = err instanceof Error ? err.message : '加载结果详情失败'
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

onMounted(load)
onUnmounted(() => { requestVersion++ })
watch(resultId, () => { result.value = null; evidence.value = []; metrics.value = []; diffView.value = null; selectedEvidence.value = null; activeTab.value = 'evidence'; evidenceFilter.value = 'ALL'; mappingQuery.value = ''; void load() })
</script>


<template>
  <section>
    <div class="page-header">
      <div><div class="eyebrow">EVIDENCE REVIEW · #{{ resultId }}</div><h1>结果证据</h1><p>{{ result?.submissionAFileName ?? '-' }} <span class="pair-separator">/</span> {{ result?.submissionBFileName ?? '-' }}</p></div>
      <div class="header-actions"><el-button :icon="ArrowLeft" @click="result ? router.push('/tasks/' + result.taskId + '/results') : router.push('/tasks')">任务结果</el-button><el-tooltip content="导出此任务的全部结果与证据"><el-button :icon="Download" :loading="reportLoading" :disabled="!result" @click="exportReport">任务报告</el-button></el-tooltip><el-tooltip content="刷新证据"><el-button :icon="Refresh" :loading="loading" @click="load" aria-label="刷新证据" /></el-tooltip></div>
    </div>
    <el-alert v-if="error" class="section-gap" type="error" :title="error" :closable="false" show-icon />
    <el-skeleton v-if="loading && !result" :rows="8" class="section-gap" />
    <template v-if="result">
      <el-alert v-if="result.isMock" class="section-gap" type="warning" title="mock 数据 · 仅用于联调展示" :closable="false" show-icon />
      <el-alert v-if="reviewAssessment && reviewAssessment.status !== 'SIMILARITY_SIGNALS_ONLY'" class="section-gap" type="warning"
        :title="reviewAssessment.status === 'INSUFFICIENT_DISTINGUISHING_EVIDENCE' ? '可区分依据不足' : '需要结合背景复核'"
        :description="String(reviewAssessment.message ?? '')" :closable="false" show-icon />
      <div class="metric-grid section-gap evidence-overview">
        <div class="metric-tile"><span>综合相似分</span><strong>{{ percent(result.weightedSimilarityScore) }}</strong><small>{{ result.formulaVersion }}</small></div>
        <div class="metric-tile"><span>{{ isHtmlResult ? '固定阈值 · 待验证' : '题目动态阈值' }}</span><strong>{{ percent(result.dynamicThreshold) }}</strong><small>{{ result.exceedThreshold ? '已超过当前阈值' : '未超过当前阈值' }}</small></div>
        <div class="metric-tile"><span>风险边际</span><strong :class="result.exceedThreshold ? 'risk-positive' : 'risk-negative'">{{ signedPercent(result.riskMargin) }}</strong><small>综合分与阈值之差</small></div>
        <div class="metric-tile"><span>相似风险</span><div class="risk-summary"><RiskBadge :level="result.riskLevel" /></div><small>人工复核线索，非关系判定</small></div>
      </div>
      <section class="score-analysis section-gap">
        <div class="score-analysis-primary"><div class="section-heading"><h2>分数与阈值</h2><span>同一 0–100% 刻度</span></div><ScoreTrack :score="result.weightedSimilarityScore" :threshold="result.dynamicThreshold" /><p>风险边际 <strong :class="result.exceedThreshold ? 'risk-positive' : 'risk-negative'">{{ signedPercent(result.riskMargin) }}</strong><span> · 分数不是关系概率</span></p></div>
        <div class="dimensions" aria-label="多维相似指标">
        <div v-for="dimension in dimensions" :key="dimension.label" class="dimension-item">
          <div><span>{{ dimension.label }}</span><strong>{{ percent(dimension.value) }}</strong></div>
          <div class="dimension-track" :class="{ unavailable: scorePosition(dimension.value) === null }" role="img" :aria-label="dimension.label + ' ' + percent(dimension.value)"><span v-if="scorePosition(dimension.value) !== null" :style="{ width: scorePosition(dimension.value) + '%', background: dimension.color }" /></div>
        </div>
        <p class="normalization-delta">Canonical − Raw <strong>{{ signedPercent(canonicalDifference) }}</strong><span>规范化前后差值，非额外风险加分</span></p>
        </div>
      </section>
      <p class="result-reason">{{ result.reasonSummary }} <span>仅提供相似风险与人工复核线索。</span></p>
      <el-tabs v-model="activeTab" class="evidence-tabs">
        <el-tab-pane label="证据与源码" name="evidence">
          <section class="panel">
            <div class="section-heading"><h2>证据列表</h2><span>{{ evidence.length }} 条</span></div>
            <div class="table-toolbar evidence-toolbar"><el-select v-model="evidenceFilter" aria-label="证据类型筛选"><el-option value="ALL" label="全部证据类型" /><el-option v-for="type in evidenceTypes" :key="type" :value="type" :label="evidenceLabel(type)" /></el-select><span class="text-muted">{{ filteredEvidence.length }} / {{ evidence.length }} 条</span></div>
            <el-table :data="filteredEvidence" empty-text="暂无证据" @row-click="selectEvidence" highlight-current-row row-key="id" class="evidence-table">
              <el-table-column label="证据类型" min-width="145"><template #default="{ row }"><el-tag :type="row.evidenceType === 'PARSER_WARNING' ? 'warning' : 'info'" effect="plain">{{ evidenceLabel(row.evidenceType) }}</el-tag></template></el-table-column>
              <el-table-column label="分数" width="85"><template #default="{ row }">{{ ['REVIEW_NOTE', 'PARSER_WARNING'].includes(row.evidenceType) ? '-' : percent(row.similarityScore) }}</template></el-table-column>
              <el-table-column prop="description" label="证据说明" min-width="280" />
              <el-table-column label="原文行号" min-width="190"><template #default="{ row }"><div v-for="(fragment, index) in fragmentsOf(row)" :key="index" class="fragment-row">A {{ fragment.submissionAStartLine }}–{{ fragment.submissionAEndLine }} / B {{ fragment.submissionBStartLine }}–{{ fragment.submissionBEndLine }}</div></template></el-table-column>
              <el-table-column label="定位" width="70"><template #default="{ row }"><el-tooltip content="定位到此证据的源码"><el-button :icon="Search" text @click.stop="selectEvidence(row)" :aria-label="'定位证据 ' + row.id" /></el-tooltip></template></el-table-column>
            </el-table>
            <div class="evidence-mobile">
              <button v-for="item in filteredEvidence" :key="item.id" class="mobile-evidence-item" :class="{ chosen: selectedEvidence?.id === item.id }" @click="selectEvidence(item)">
                <span class="mobile-evidence-title"><el-tag :type="item.evidenceType === 'PARSER_WARNING' ? 'warning' : 'info'" effect="plain">{{ evidenceLabel(item.evidenceType) }}</el-tag><strong>{{ ['REVIEW_NOTE', 'PARSER_WARNING'].includes(item.evidenceType) ? '-' : percent(item.similarityScore) }}</strong></span>
                <span class="mobile-evidence-description">{{ item.description }}</span>
                <span v-for="(fragment, index) in fragmentsOf(item)" :key="index" class="fragment-row">A {{ fragment.submissionAStartLine }}–{{ fragment.submissionAEndLine }} / B {{ fragment.submissionBStartLine }}–{{ fragment.submissionBEndLine }}</span>
              </button>
              <el-empty v-if="!filteredEvidence.length" :image-size="50" description="暂无证据" />
            </div>
          </section>
          <div id="source-comparison" class="section-heading source-heading"><h2>源码对照</h2><el-button v-if="selectedEvidence" link type="primary" @click="selectedEvidence = null">全部高亮</el-button><span v-else>原文证据范围</span></div>
          <div class="source-toolbar"><el-segmented v-model="codeLayout" :options="[{ label: '并排', value: 'side' }, { label: '上下', value: 'stack' }]" aria-label="源码排列方式" /><el-checkbox v-model="wrapCode">自动换行</el-checkbox><span>{{ diffView?.codeA.language ?? '-' }} / {{ diffView?.codeB.language ?? '-' }}</span></div>
          <div v-if="selectedEvidence" class="selected-evidence">{{ evidenceLabel(selectedEvidence.evidenceType) }} · {{ selectedEvidence.description }}</div>
          <section class="code-compare" :class="{ stacked: codeLayout === 'stack', wrapped: wrapCode }">
            <div class="code-pane">
              <div class="code-title"><span><small>A</small>{{ diffView?.codeA.fileName ?? '代码 A' }}</span><el-tooltip content="复制代码 A"><el-button :icon="DocumentCopy" text :disabled="!diffView" @click="copyCode('A')" aria-label="复制代码 A" /></el-tooltip></div>
              <pre class="code-block"><div v-for="line in codeLines(diffView?.codeA.code)" :key="line.no" :class="['code-line', { highlighted: hasLine(diffHighlightedA.size ? diffHighlightedA : highlightedA, line.no) }]"><span class="line-no">{{ line.no }}</span><code>{{ line.text || ' ' }}</code></div></pre>
            </div>
            <div class="code-pane">
              <div class="code-title"><span><small>B</small>{{ diffView?.codeB.fileName ?? '代码 B' }}</span><el-tooltip content="复制代码 B"><el-button :icon="DocumentCopy" text :disabled="!diffView" @click="copyCode('B')" aria-label="复制代码 B" /></el-tooltip></div>
              <pre class="code-block"><div v-for="line in codeLines(diffView?.codeB.code)" :key="line.no" :class="['code-line', { highlighted: hasLine(diffHighlightedB.size ? diffHighlightedB : highlightedB, line.no) }]"><span class="line-no">{{ line.no }}</span><code>{{ line.text || ' ' }}</code></div></pre>
            </div>
          </section>
        </el-tab-pane>
        <el-tab-pane :label="isHtmlResult ? '范围与阈值' : '题目与阈值'" name="profile">
          <section class="profile-layout">
            <div class="panel">
              <h2>{{ isHtmlResult ? 'HTML 检测范围' : '题目画像' }}</h2>
              <p v-if="isHtmlResult" class="profile-meta">标签结构、属性、文本和资源引用；HTML 固定阈值尚待真实标注数据验证。</p>
              <div v-else class="profile-score-grid"><div><span>难度</span><strong>{{ percent(result.problemProfile?.difficultyScore) }}</strong></div><div><span>解法空间</span><strong>{{ percent(result.problemProfile?.solutionSpaceScore) }}</strong></div><div><span>模板风险</span><strong>{{ percent(result.problemProfile?.templateRiskScore) }}</strong></div><div><span>自然相似风险</span><strong>{{ percent(result.problemProfile?.naturalSimilarityRisk) }}</strong></div></div>
              <p class="profile-meta">{{ result.problemProfile?.featureVersion ?? '-' }} · 置信度 {{ percent(result.problemProfile?.confidence) }}</p>
              <p class="profile-meta">{{ result.formulaVersion }} · {{ result.algorithmVersion }}</p>
              <p class="profile-meta">风险展示分 {{ percent(result.calibratedRiskScore) }}（风险边际的展示映射，非经验概率校准）</p>
            </div>
            <div class="panel">
              <h2>{{ isHtmlResult ? '固定阈值说明' : '动态阈值分解' }}</h2>
              <div class="threshold-line"><span>基础阈值</span><strong>{{ percent(result.thresholdAdjustment?.baseThreshold) }}</strong></div>
              <div v-for="item in (isHtmlResult ? [] : thresholdAdjustments)" :key="item.label" class="threshold-line adjustment-row"><span>{{ item.label }}</span><div class="adjustment-track" aria-hidden="true"><i v-if="adjustmentBar(item.value, adjustmentScale)" :class="{ negative: (item.value ?? 0) < 0 }" :style="{ left: adjustmentBar(item.value, adjustmentScale)!.left + '%', width: adjustmentBar(item.value, adjustmentScale)!.width + '%' }" /></div><strong>{{ signedPercent(item.value) }}</strong></div>
              <div class="threshold-line threshold-final"><span>最终阈值</span><strong>{{ percent(result.thresholdAdjustment?.finalThreshold) }}</strong></div>
              <p class="threshold-explanation">{{ result.thresholdAdjustment?.explanation }}</p>
            </div>
          </section>
        </el-tab-pane>
        <el-tab-pane label="标识符映射" name="mapping">
          <section class="panel"><div class="section-heading"><h2>作用域标识符映射</h2><span>{{ mappingRows.length }} 项</span></div>
            <div class="table-toolbar"><el-input v-model="mappingQuery" :prefix-icon="Search" placeholder="搜索名称或作用域" aria-label="搜索标识符映射" clearable /><span class="text-muted">{{ filteredMappings.length }} / {{ mappingRows.length }} 项</span></div>
            <el-table :data="filteredMappings" empty-text="暂无匹配的标识符映射">
              <el-table-column prop="submissionAName" label="代码 A" min-width="130" /><el-table-column prop="submissionBName" label="代码 B" min-width="130" />
              <el-table-column prop="canonicalName" label="规范化名称" min-width="160" /><el-table-column prop="scopePath" label="作用域" min-width="160" />
              <el-table-column label="类型" min-width="120"><template #default="{ row }">{{ row.mappingType ?? row.kind }}</template></el-table-column>
            </el-table>
          </section>
        </el-tab-pane>
        <el-tab-pane label="背景复核" name="context">
          <section v-if="compatibilityContext || templateContext" class="panel">
            <h2>版本与自然相似背景</h2>
            <p class="profile-meta">声明版本未经编译器验证；解析失败或低相似分不等于独立创作。以下背景不改变生产分数。</p>
            <div class="context-sides">
              <div v-for="side in ['A', 'B']" :key="side"><h3>代码 {{ side }}</h3><p>声明版本：{{ contextSide(compatibilityContext, side).declaredVersion ?? '未知' }}</p><p>非模板 Token：{{ contextSide(templateContext, side).effectiveTokenCount ?? '-' }}</p><p>{{ contextSide(compatibilityContext, side).syntaxParsed === true ? '结构已解析，版本未验证' : '结构未解析' }}</p><p v-if="compatibilityLimitations(side)" class="risk-positive">{{ compatibilityLimitations(side) }}</p></div>
            </div>
            <template v-if="templateContext?.registered === true">
              <p class="profile-meta">共同模板来源：{{ templateContext.sourceReference }}（登记信息，未独立核验）</p>
              <p class="profile-meta">精确覆盖：A {{ contextPercent(contextSide(templateContext, 'A').templateCoverage) }} · B {{ contextPercent(contextSide(templateContext, 'B').templateCoverage) }}</p>
              <p class="profile-meta">模板原文行号：A {{ templateRanges('A') }} · B {{ templateRanges('B') }}（最多20处）</p>
              <p class="profile-meta">非模板 Token 集合相似度：{{ contextPercent(templateContext.nonTemplateTokenSetSimilarity) }}（诊断指标，非生产综合分）</p>
            </template>
            <p class="profile-meta">“依据不足”规则未经过真实标注数据校准，不确认独立创作或排除派生关系。</p>
          </section>
          <el-empty v-else description="暂无背景复核信息" />
        </el-tab-pane>
        <el-tab-pane v-if="experimentalMetrics.length || irEvidence || controlSummaryEvidence || dataFlowSummaryEvidence" label="实验性指标" name="experimental">
          <el-alert type="warning" title="实验性能力 · 生产权重 0" description="有限 Java/Python normalized IR 与轻量摘要，不进入 PICAS_STANDARD；不是完整 CFG/DFG 或语义等价判断。" :closable="false" show-icon />
          <div class="metric-grid section-gap"><div v-for="metric in experimentalMetrics" :key="metric.name" class="metric-tile"><span>{{ metricLabel(metric.name) }}</span><strong>{{ percent(metric.value) }}</strong><small>实验性 · 不进入生产评分</small></div></div>
          <section v-if="irEvidence" class="panel section-gap"><h2>Normalized IR 对照</h2><div class="ir-grid"><div><span>A · 覆盖率 {{ percent(irCoverage('coverageA')) }}</span><code>{{ irSequence('irSequenceA') }}</code></div><div><span>B · 覆盖率 {{ percent(irCoverage('coverageB')) }}</span><code>{{ irSequence('irSequenceB') }}</code></div></div></section>
          <section v-if="controlSummaryEvidence || dataFlowSummaryEvidence" class="panel section-gap"><h2>轻量控制 / 数据摘要</h2><div class="summary-comparison"><template v-for="side in ['A', 'B']" :key="side"><div><h3>控制摘要 {{ side }}</h3><dl><div v-for="entry in summaryItems(controlSummaryEvidence, 'controlSummary' + side)" :key="entry.label"><dt>{{ entry.label }}</dt><dd>{{ entry.value }}</dd></div></dl></div><div><h3>数据摘要 {{ side }}</h3><dl><div v-for="entry in summaryItems(dataFlowSummaryEvidence, 'dataFlowSummary' + side)" :key="entry.label"><dt>{{ entry.label }}</dt><dd>{{ entry.value }}</dd></div></dl></div></template></div></section>
        </el-tab-pane>
      </el-tabs>
    </template>
  </section>
</template>

<style scoped>
.section-gap {
  margin-top: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.fragment-row {
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 12px;
}

.risk-positive {
  color: #b42318;
}

.risk-negative {
  color: #39705f;
}

.experimental-tile {
  border-color: #b7a4df;
}

.ir-panel {
  border-left: 4px solid #7c5ab8;
}

.ir-panel h2 {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ir-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.ir-grid span {
  color: #63726e;
  display: block;
  font-size: 13px;
  margin-bottom: 8px;
}

.ir-grid code {
  display: block;
  overflow-wrap: anywhere;
  line-height: 1.7;
}

.summary-comparison {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px 28px;
}

.summary-comparison h3 {
  font-size: 14px;
  margin: 0 0 8px;
}

.summary-comparison dl {
  margin: 0;
}

.summary-comparison dl div {
  border-bottom: 1px solid #e8efec;
  display: grid;
  grid-template-columns: minmax(130px, 0.55fr) minmax(0, 1fr);
  gap: 12px;
  padding: 7px 0;
}

.summary-comparison dt {
  color: #63726e;
}

.summary-comparison dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.profile-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.profile-score-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 18px;
}

.profile-score-grid div,
.threshold-line {
  border-bottom: 1px solid #e8efec;
  padding: 8px 0;
}

.profile-score-grid span,
.threshold-line span,
.profile-meta,
.threshold-explanation {
  color: #63726e;
  font-size: 13px;
}

.profile-score-grid strong {
  display: block;
  font-size: 20px;
  margin-top: 4px;
}

.profile-meta,
.threshold-explanation {
  line-height: 1.6;
  margin: 14px 0 0;
}

.threshold-line {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.threshold-final {
  border-bottom-color: #9dbbb1;
  font-size: 16px;
  padding-top: 12px;
}

.code-compare {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.code-pane {
  border: 1px solid #dce5e1;
  border-radius: 8px;
  background: #ffffff;
  min-width: 0;
  overflow: hidden;
}

.code-title {
  border-bottom: 1px solid #dce5e1;
  padding: 12px 14px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.code-block {
  margin: 0;
  padding: 10px 0;
  overflow: auto;
  max-height: 580px;
  background: #fbfdfc;
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 13px;
  line-height: 1.55;
}

.code-line {
  display: grid;
  grid-template-columns: 54px minmax(max-content, 1fr);
  min-width: max-content;
  padding-right: 14px;
}

.code-line.highlighted {
  background: #fff3cf;
}

.line-no {
  color: #7b8a86;
  padding: 0 12px;
  text-align: right;
  user-select: none;
}

.code-line code {
  white-space: pre;
}

@media (max-width: 980px) {
  .profile-layout,
  .ir-grid,
  .summary-comparison,
  .code-compare {
    grid-template-columns: 1fr;
  }
}

.evidence-overview .metric-tile > strong { font-size: 27px; }
.risk-summary { display: flex; align-items: center; height: 38px; margin-top: 10px; }
.risk-summary :deep(.el-tag) { height: 28px; padding: 0 12px; font-size: 12px; }
.pair-separator { margin: 0 7px; color: #bac2cd; }
.score-analysis { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); background: white; }
.score-analysis-primary { padding: 24px; border-right: 1px solid var(--line); }
.score-analysis-primary h2 { font-size: 14px; }
.score-analysis-primary p { font-size: 12px; margin: 20px 0 0; color: #7c8795; }
.score-analysis-primary strong { margin-left: 6px; }
.dimensions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; padding: 24px; }
.dimension-item > div:first-child { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; margin-bottom: 11px; color: #748091; }
.dimension-item strong { color: #5b6573; font-size: 12px; font-weight: 600; }
.dimension-track { height: 6px; border-radius: 2px; background: #edf0f4; overflow: hidden; }
.dimension-track > span { display: block; height: 100%; }
.dimension-track.unavailable { background: repeating-linear-gradient(90deg, #eef0f3 0 6px, white 6px 10px); }
.normalization-delta { grid-column: 1 / -1; margin: 0; color: #748091; font-size: 12px; line-height: 1.8; }
.normalization-delta strong { margin-left: 8px; color: #167d71; font-variant-numeric: tabular-nums; }
.normalization-delta span { display: block; color: #8993a0; font-size: 11px; }
.source-toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 20px; margin-bottom: 16px; }
.source-toolbar > span { color: #7c8795; font-size: 11px; margin-left: auto; }
.source-heading { scroll-margin-top: 22px; }
.code-compare.stacked { grid-template-columns: 1fr; }
.code-compare.wrapped .code-line { grid-template-columns: 48px minmax(0, 1fr); min-width: 0; }
.code-compare.wrapped code { white-space: pre-wrap; overflow-wrap: anywhere; }
.code-block { position: relative; }
.evidence-toolbar .el-select { width: 210px; max-width: 100%; }
.adjustment-row { display: grid; grid-template-columns: 72px minmax(30px, 1fr) 70px; gap: 12px; align-items: center; }
.adjustment-row strong { text-align: right; font-size: 12px; }
.adjustment-track { height: 15px; position: relative; background: #f7f9fb; }
.adjustment-track::before { content: ''; position: absolute; top: 0; bottom: 0; left: 50%; border-left: 1px solid #ccd4de; }
.adjustment-track i { height: 7px; top: 4px; background: #76b5a8; position: absolute; }
.adjustment-track i.negative { background: #b09ac7; }
.result-reason { margin: 18px 0 26px; font-size: 11px; color: #67717f; line-height: 1.8; }
.result-reason > span { color: #96a0ab; }
.evidence-table :deep(.el-table__row) { cursor: pointer; }
.evidence-mobile { display: none; }
.mobile-evidence-item { width: 100%; display: flex; flex-direction: column; align-items: stretch; gap: 10px; padding: 14px; border: 1px solid var(--line); border-radius: 4px; background: white; text-align: left; color: var(--ink); cursor: pointer; min-width: 0; }
.mobile-evidence-item + .mobile-evidence-item { margin-top: 10px; }
.mobile-evidence-item.chosen { border-color: #87bbac; background: #f4faf7; }
.mobile-evidence-title { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.mobile-evidence-title strong { font-size: 12px; font-weight: 550; }
.mobile-evidence-description { font-size: 12px; line-height: 1.8; overflow-wrap: anywhere; color: #687586; }
.source-heading { margin-top: 26px; }
.source-heading h2 { font-size: 14px; }
.selected-evidence { font-size: 11px; color: #8b7549; margin-bottom: 14px; line-height: 1.7; }
.code-title { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; min-height: 49px; padding: 8px 12px; background: #f9fafc; }
.code-title > span { min-width: 0; overflow-wrap: anywhere; }
.code-title small { display: inline-grid; place-items: center; width: 21px; height: 21px; color: #79879a; background: #eaf0f7; margin-right: 9px; border-radius: 3px; }
.code-pane { border-radius: 4px; border-color: #e1e6ed; }
.code-block { background: #fff; font-size: 12px; }
.code-line.highlighted { background: #fff5d9; box-shadow: inset 3px 0 #dcbf72; }
.context-sides { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px; margin: 24px 0; }
.context-sides h3 { font-size: 13px; }
.context-sides p { font-size: 12px; line-height: 1.7; color: #6d7887; }
@media (max-width: 1050px) { .score-analysis { grid-template-columns: 1fr; } .score-analysis-primary { border-right: 0; border-bottom: 1px solid var(--line); } }
@media (max-width: 680px) { .evidence-table { display: none; } .evidence-mobile { display: block; } }
@media (max-width: 560px) { .context-sides { grid-template-columns: 1fr; gap: 10px; } .evidence-overview .metric-tile > strong { font-size: 22px; } .dimensions { gap: 20px 16px; padding: 18px 14px; } .dimension-item > div { flex-wrap: wrap; } }

</style>
