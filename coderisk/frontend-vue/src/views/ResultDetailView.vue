<script setup lang="ts">
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  getResult,
  getResultDiffView,
  getResultEvidence,
  getResultMetrics,
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

function percent(value: number | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`
}

function signedPercent(value: number | undefined) {
  const points = (value ?? 0) * 100
  return `${points >= 0 ? '+' : ''}${points.toFixed(1)} pp`
}

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
  ]
})

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
  return typeof value === 'number' ? value : 0
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
  for (const item of evidence.value) {
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

const diffHighlightedA = computed(() => new Set((diffView.value?.highlights ?? []).flatMap((item) => rangeLines(item.aRange.startLine, item.aRange.endLine))))
const diffHighlightedB = computed(() => new Set((diffView.value?.highlights ?? []).flatMap((item) => rangeLines(item.bRange.startLine, item.bRange.endLine))))

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
  loading.value = true
  error.value = ''
  try {
    const [resultResponse, evidenceResponse, metricResponse, codePairResponse] = await Promise.all([
      getResult(resultId.value),
      getResultEvidence(resultId.value),
      getResultMetrics(resultId.value),
      getResultDiffView(resultId.value),
    ])
    result.value = resultResponse.data
    evidence.value = evidenceResponse.data
    metrics.value = metricResponse.data
    diffView.value = codePairResponse.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载结果详情失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>结果证据</h1>
        <p>{{ result?.submissionAFileName ?? '-' }} / {{ result?.submissionBFileName ?? '-' }}</p>
      </div>
      <div class="header-actions">
        <el-button :icon="ArrowLeft" @click="router.back()">返回</el-button>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert v-if="error" class="section-gap" type="error" :title="error" :closable="false" />
    <el-alert v-if="result?.isMock" class="section-gap" type="warning" title="当前结果包含 mock 数据，仅用于联调展示。" :closable="false" />
    <el-alert
      v-if="experimentalMetrics.length"
      class="section-gap"
      type="warning"
      :title="`跨语言实验指标：${experimentalMetrics.length} 项`"
      description="Normalized IR 与轻量控制/数据流摘要权重均为 0，不进入 PICAS_STANDARD；系统不构建完整 CFG/DFG，也不表示语义等价。"
      :closable="false"
      show-icon
    />
    <el-alert
      v-if="result && !result.isMock"
      class="section-gap"
      :type="alertType"
      :title="result.reasonSummary"
      description="系统仅评估相似风险并提供人工复核线索，不直接作出纪律结论。"
      :closable="false"
      show-icon
    />

    <div class="metric-grid section-gap">
      <div class="metric-tile">
        <span>综合分</span>
        <strong>{{ percent(result?.weightedSimilarityScore) }}</strong>
      </div>
      <div class="metric-tile">
        <span>Token</span>
        <strong>{{ percent(result?.tokenSimilarity) }}</strong>
      </div>
      <div class="metric-tile">
        <span>{{ isHtmlResult ? 'HTML 标签树' : 'AST' }}</span>
        <strong>{{ percent(result?.astSimilarity) }}</strong>
      </div>
      <div class="metric-tile">
        <span>Canonical</span>
        <strong>{{ percent(result?.canonicalTokenSimilarity) }}</strong>
      </div>
      <div class="metric-tile">
        <span>{{ isHtmlResult ? '固定阈值（待验证）' : '动态阈值' }}</span>
        <strong>{{ percent(result?.dynamicThreshold) }}</strong>
      </div>
      <div class="metric-tile">
        <span>风险边际</span>
        <strong :class="result?.exceedThreshold ? 'risk-positive' : 'risk-negative'">{{ signedPercent(result?.riskMargin) }}</strong>
      </div>
      <div class="metric-tile">
        <span>校准风险分</span>
        <strong>{{ percent(result?.calibratedRiskScore) }}</strong>
      </div>
      <div class="metric-tile">
        <span>风险等级</span>
        <strong>{{ result?.riskLevel ?? '-' }}</strong>
      </div>
      <div v-for="metric in experimentalMetrics" :key="metric.name" class="metric-tile experimental-tile">
        <span>{{ metricLabel(metric.name) }} · 实验性</span>
        <strong>{{ percent(metric.value) }}</strong>
      </div>
    </div>

    <section class="profile-layout section-gap">
      <div class="panel">
        <h2>{{ isHtmlResult ? 'HTML 检测范围' : '题目画像' }}</h2>
        <p v-if="isHtmlResult" class="profile-meta">比较标签结构、属性、文本和资源引用；模板共性需要人工复核。HTML 暂无经过标注数据校准的题目复杂度模型。</p>
        <div v-else class="profile-score-grid">
          <div>
            <span>难度</span>
            <strong>{{ percent(result?.problemProfile?.difficultyScore) }}</strong>
          </div>
          <div>
            <span>解法空间</span>
            <strong>{{ percent(result?.problemProfile?.solutionSpaceScore) }}</strong>
          </div>
          <div>
            <span>模板风险</span>
            <strong>{{ percent(result?.problemProfile?.templateRiskScore) }}</strong>
          </div>
          <div>
            <span>自然相似风险</span>
            <strong>{{ percent(result?.problemProfile?.naturalSimilarityRisk) }}</strong>
          </div>
        </div>
        <p class="profile-meta">
          {{ result?.problemProfile?.featureVersion ?? '-' }} · 置信度 {{ percent(result?.problemProfile?.confidence) }}
        </p>
        <p class="profile-meta">
          {{ result?.formulaVersion ?? '-' }} · {{ result?.algorithmVersion ?? '-' }}
        </p>
      </div>
      <div class="panel">
        <h2>{{ isHtmlResult ? '固定阈值说明' : '动态阈值分解' }}</h2>
        <div class="threshold-line">
          <span>基础阈值</span>
          <strong>{{ percent(result?.thresholdAdjustment?.baseThreshold) }}</strong>
        </div>
        <div v-for="item in (isHtmlResult ? [] : thresholdAdjustments)" :key="item.label" class="threshold-line">
          <span>{{ item.label }}</span>
          <strong>{{ signedPercent(item.value) }}</strong>
        </div>
        <div class="threshold-line threshold-final">
          <span>最终阈值</span>
          <strong>{{ percent(result?.thresholdAdjustment?.finalThreshold) }}</strong>
        </div>
        <p class="threshold-explanation">{{ result?.thresholdAdjustment?.explanation }}</p>
      </div>
    </section>

    <section class="panel section-gap">
      <h2>证据片段</h2>
      <el-table v-loading="loading" :data="evidence" empty-text="暂无证据">
        <el-table-column prop="evidenceType" label="类型" width="150" />
        <el-table-column label="分数" width="100">
          <template #default="{ row }">{{ percent(row.similarityScore) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="260" />
        <el-table-column label="行号" min-width="260">
          <template #default="{ row }">
            <div v-for="(fragment, index) in fragmentsOf(row)" :key="index" class="fragment-row">
              A: {{ fragment.submissionAStartLine }}-{{ fragment.submissionAEndLine }}
              / B: {{ fragment.submissionBStartLine }}-{{ fragment.submissionBEndLine }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="变量映射" min-width="240">
          <template #default="{ row }">
            <div v-for="(mapping, index) in mappingsOf(row)" :key="index" class="fragment-row">
              {{ mapping.submissionAName }} → {{ mapping.submissionBName }}
              ({{ mapping.mappingType ?? mapping.kind }} / {{ mapping.canonicalName }})
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section v-if="irEvidence" class="panel section-gap ir-panel">
      <h2>Normalized IR 对照 <el-tag type="warning" effect="plain">实验性</el-tag></h2>
      <div class="ir-grid">
        <div>
          <span>代码 A · 覆盖率 {{ percent(irCoverage('coverageA')) }}</span>
          <code>{{ irSequence('irSequenceA') }}</code>
        </div>
        <div>
          <span>代码 B · 覆盖率 {{ percent(irCoverage('coverageB')) }}</span>
          <code>{{ irSequence('irSequenceB') }}</code>
        </div>
      </div>
    </section>

    <section v-if="controlSummaryEvidence || dataFlowSummaryEvidence" class="panel section-gap ir-panel">
      <h2>轻量结构摘要 <el-tag type="warning" effect="plain">实验性 · 非完整 CFG/DFG</el-tag></h2>
      <div class="summary-comparison">
        <div v-for="side in ['A', 'B']" :key="`control-${side}`">
          <h3>控制摘要 {{ side }}</h3>
          <dl>
            <div v-for="entry in summaryItems(controlSummaryEvidence, `controlSummary${side}`)" :key="entry.label">
              <dt>{{ entry.label }}</dt><dd>{{ entry.value }}</dd>
            </div>
          </dl>
        </div>
        <div v-for="side in ['A', 'B']" :key="`data-${side}`">
          <h3>数据摘要 {{ side }}</h3>
          <dl>
            <div v-for="entry in summaryItems(dataFlowSummaryEvidence, `dataFlowSummary${side}`)" :key="entry.label">
              <dt>{{ entry.label }}</dt><dd>{{ entry.value }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <section class="code-compare section-gap">
      <div class="code-pane">
        <div class="code-title">{{ diffView?.codeA.fileName ?? '代码 A' }}</div>
        <pre class="code-block"><div
          v-for="line in codeLines(diffView?.codeA.code)"
          :key="line.no"
          :class="['code-line', { highlighted: hasLine(diffHighlightedA.size ? diffHighlightedA : highlightedA, line.no) }]"
        ><span class="line-no">{{ line.no }}</span><code>{{ line.text || ' ' }}</code></div></pre>
      </div>
      <div class="code-pane">
        <div class="code-title">{{ diffView?.codeB.fileName ?? '代码 B' }}</div>
        <pre class="code-block"><div
          v-for="line in codeLines(diffView?.codeB.code)"
          :key="line.no"
          :class="['code-line', { highlighted: hasLine(diffHighlightedB.size ? diffHighlightedB : highlightedB, line.no) }]"
        ><span class="line-no">{{ line.no }}</span><code>{{ line.text || ' ' }}</code></div></pre>
      </div>
    </section>
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
</style>
