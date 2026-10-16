<script setup lang="ts">
import { Download, Refresh, View, Search, DataAnalysis, List } from '@element-plus/icons-vue'
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RiskBadge from '../components/RiskBadge.vue'
import TaskStatusBadge from '../components/TaskStatusBadge.vue'
import RiskDistribution from '../components/RiskDistribution.vue'
import ScoreTrack from '../components/ScoreTrack.vue'
import { percent, margin, includesQuery, dateTime } from '../utils/presentation'

const TaskStatisticalAnalysis = defineAsyncComponent(() => import('../components/TaskStatisticalAnalysis.vue'))

import { createTaskReport, getTask, getTaskFailures, getTaskResults, getTaskResultSummary, startTask, type DetectionTask, type ResultRow, type TaskResultSummary, type TaskPairFailure } from '../api/taskApi'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => Number(route.params.taskId))
const loading = ref(false)
const error = ref('')
const summary = ref<TaskResultSummary | null>(null)
const task = ref<DetectionTask | null>(null)
const results = ref<ResultRow[]>([])
const reportLoading = ref(false)
const reportMessage = ref('')
const failures = ref<TaskPairFailure[]>([])
const currentPage = ref(1)
const totalRows = ref(0)
const starting = ref(false)
const search = ref('')
const riskFilter = ref('全部')
function viewFromQuery() { return ['chart', 'analysis'].includes(String(route.query.view)) ? String(route.query.view) : 'table' }
const resultView = ref(viewFromQuery())
watch(() => route.query.view, () => { resultView.value = viewFromQuery() })
watch(resultView, value => {
  if (route.path !== `/tasks/${taskId.value}/results` || value === viewFromQuery()) return
  void router.replace({ query: { ...route.query, view: value === 'table' ? undefined : value, plot: value === 'analysis' ? route.query.plot : undefined } })
})
const visibleResults = computed(() => results.value.filter(row =>
  includesQuery(search.value, row.submissionAFileName, row.submissionBFileName) &&
  (riskFilter.value === '全部' || row.riskLevel === riskFilter.value),
))
const active = computed(() => ['RUNNING', 'QUEUED'].includes(task.value?.status ?? ''))
const retryable = computed(() => ['PENDING', 'PARTIAL', 'FAILED'].includes(task.value?.status ?? ''))
let timer: ReturnType<typeof setTimeout> | undefined
let disposed = false

async function load() {
  if (loading.value || disposed) return
  clearTimeout(timer)
  const requestedTask = taskId.value
  const requestedPage = currentPage.value
  loading.value = true
  error.value = ''
  try {
    // FINISHED is written after result commits. Read it before fetching results,
    // so a terminal status cannot stop polling with a stale final result snapshot.
    const taskResponse = await getTask(requestedTask)
    if (disposed || requestedTask !== taskId.value || requestedPage !== currentPage.value) return
    const [summaryResponse, resultsResponse, failuresResponse] = await Promise.all([
      getTaskResultSummary(requestedTask),
      getTaskResults(requestedTask, requestedPage),
      getTaskFailures(requestedTask),
    ])
    if (disposed || requestedTask !== taskId.value || requestedPage !== currentPage.value) return
    task.value = taskResponse.data
    summary.value = summaryResponse.data
    results.value = resultsResponse.data.items
    failures.value = failuresResponse.data
    totalRows.value = resultsResponse.data.total
  } catch (err) {
    if (!disposed && requestedTask === taskId.value) error.value = err instanceof Error ? err.message : '加载结果失败'
  } finally {
    loading.value = false
    if (!disposed && (requestedTask !== taskId.value || requestedPage !== currentPage.value)) timer = setTimeout(load, 0)
    else if (!disposed && active.value) timer = setTimeout(load, 2000)
  }
}

onMounted(load)
onUnmounted(() => { disposed = true; clearTimeout(timer) })
watch(currentPage, () => { search.value = ''; riskFilter.value = '全部'; void load() })
watch(taskId, () => { currentPage.value = 1; task.value = null; summary.value = null; results.value = []; failures.value = []; totalRows.value = 0; reportMessage.value = ''; void load() })

async function resume() {
  const requestedTask = taskId.value
  starting.value = true
  try {
    const response = await startTask(requestedTask)
    if (disposed || requestedTask !== taskId.value) return
    task.value = response.data
    await load()
  } catch (err) {
    if (!disposed && requestedTask === taskId.value) error.value = err instanceof Error ? err.message : '启动失败，请稍后重试'
  } finally { starting.value = false }
}

async function exportReport() {
  const requestedTask = taskId.value
  reportLoading.value = true
  reportMessage.value = ''
  try {
    const response = await createTaskReport(requestedTask, {
      format: 'HTML',
      includeLowRiskPairs: true,
      includeCodeSnippets: true,
      includeThresholdExplanation: true,
    })
    if (disposed || requestedTask !== taskId.value) return
    reportMessage.value = `报告已生成：${response.data.fileName}`
    const link = document.createElement('a')
    link.href = response.data.downloadUrl
    link.download = response.data.fileName
    link.click()
  } catch (err) {
    if (!disposed && requestedTask === taskId.value) error.value = err instanceof Error ? err.message : '报告生成失败'
  } finally {
    reportLoading.value = false
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <div class="eyebrow">TASK #{{ taskId }} · {{ task?.taskMode ?? 'PICAS' }}</div>
        <h1>检测结果</h1>
        <p>{{ task?.taskName ?? '正在读取任务' }}<span v-if="task"> · {{ dateTime(task.createdAt) }}</span></p>
      </div>
      <div class="header-actions">
        <el-button v-if="retryable" type="primary" :loading="starting" :disabled="loading" @click="resume">{{ task?.status === 'PENDING' ? '开始检测' : '重试未完成代码对' }}</el-button>
        <el-button :icon="Download" :loading="reportLoading" :disabled="!summary?.totalResults" @click="exportReport">导出报告</el-button>
        <el-tooltip content="刷新结果"><el-button :icon="Refresh" :loading="loading" @click="load" aria-label="刷新结果" /></el-tooltip>
      </div>
    </div>

    <el-alert v-if="summary?.containsMockData" class="section-gap" type="warning" title="当前结果包含 mock 数据，仅用于联调展示。" :closable="false" />
    <el-alert
      v-if="task?.taskMode === 'PICAS_CROSSLANG'"
      class="section-gap"
      type="warning"
      title="跨语言 IR 与轻量结构摘要均为实验性零权重指标"
      description="它们仅支持有限 Java/Python 结构，不构建完整 CFG/DFG，不进入 PICAS_STANDARD，也不表示语义等价。"
      :closable="false"
      show-icon
    />
    <el-alert v-if="error" class="section-gap" type="error" :title="error" :closable="false" />
    <el-alert v-if="reportMessage" class="section-gap" type="success" :title="reportMessage" :closable="false" />
    <section v-if="task" class="panel section-gap">
      <div class="section-heading"><h2>任务状态：{{ task.status }}</h2><TaskStatusBadge :status="task.status" /></div>
      <p>已成功 {{ task.finishedPairs }} / {{ task.totalPairs }} 对；{{ active ? '本轮失败' : '失败或未完成' }} {{ task.failedPairs }} 对。<span v-if="active">尚待处理 {{ Math.max(0, task.totalPairs - task.finishedPairs - task.failedPairs) }} 对。</span>进度表示成功覆盖率。</p>
      <el-progress :percentage="Math.round(task.progress * 100)" />
      <el-alert v-if="task.failureReason" :title="task.failureReason" type="warning" :closable="false" />
      <p v-if="active">任务已受理，可能正在等待空闲工作线程。可以离开页面后再查看结果。</p>
      <p v-if="task.status !== 'FINISHED'">当前报告仅包含已成功的代码对，不代表全部检测完成。</p>
    </section>
    <section v-if="failures.length" class="panel section-gap">
      <h2>失败与恢复记录</h2>
      <el-table :data="failures">
        <el-table-column prop="submissionAId" label="提交 A" width="100" />
        <el-table-column prop="submissionBId" label="提交 B" width="100" />
        <el-table-column prop="message" label="原因" min-width="240" show-overflow-tooltip />
        <el-table-column prop="attempts" label="失败次数" width="100" />
        <el-table-column label="恢复状态" width="120"><template #default="{ row }">{{ row.resolved ? '已恢复' : '待重试' }}</template></el-table-column>
      </el-table>
    </section>

    <div class="metric-grid section-gap result-counts">
      <div class="metric-tile">
        <span>结果数</span>
        <strong>{{ summary?.totalResults ?? '-' }}</strong>
      </div>
      <div class="metric-tile">
        <span>低风险</span>
        <strong>{{ summary?.lowCount ?? '-' }}</strong>
      </div>
      <div class="metric-tile"><span>中风险</span><strong>{{ summary?.mediumCount ?? '-' }}</strong></div>
      <div class="metric-tile">
        <span>较高风险</span>
        <strong>{{ summary?.elevatedCount ?? '-' }}</strong>
      </div>
      <div class="metric-tile">
        <span>高风险</span>
        <strong>{{ summary?.highCount ?? '-' }}</strong>
      </div>
    </div>

    <section class="panel section-gap distribution-section">
      <div class="distribution-summary"><div class="section-heading"><h2>风险分布</h2><span>全任务 · 已生成结果</span></div><RiskDistribution :summary="summary" /></div>
      <div class="review-boundary"><h3>人工复核建议</h3><p>优先结合较高风险与高风险代码对的证据、题目约束和共同模板复核；风险等级不表示来源关系成立。</p><p v-if="task && task.status !== 'FINISHED'">任务尚未全部完成，当前分布不包含失败或待处理代码对。</p><p v-else>低分或解析降级也不能证明独立创作。</p></div>
    </section>

    <section class="panel section-gap">
      <div class="section-heading"><h2>代码对结果</h2><span>第 {{ currentPage }} 页 · 共 {{ totalRows }} 对</span></div>
      <div class="table-toolbar">
        <el-input v-model="search" :prefix-icon="Search" placeholder="本页搜索文件名" aria-label="本页搜索文件名" clearable />
        <el-select v-model="riskFilter" aria-label="本页风险筛选" class="risk-filter"><el-option v-for="option in [{ value: '全部', label: '本页全部风险' }, { value: 'HIGH', label: '高风险' }, { value: 'ELEVATED', label: '较高风险' }, { value: 'MEDIUM', label: '中风险' }, { value: 'LOW', label: '低风险' }]" :key="option.value" :value="option.value" :label="option.label" /></el-select>
        <el-segmented v-model="resultView" :options="[{ value: 'table', label: '列表', icon: List }, { value: 'chart', label: '图表', icon: DataAnalysis }, { value: 'analysis', label: '分析', icon: DataAnalysis }]" aria-label="结果展示方式"><template #default="{ item }"><span class="view-option"><el-icon><component :is="item.icon" /></el-icon>{{ item.label }}</span></template></el-segmented>
      </div>
      <div v-if="resultView === 'chart'" class="pair-chart" aria-label="当前页代码对分数与阈值对比">
        <div class="chart-caption"><span>当前页筛选结果 · {{ visibleResults.length }} 对</span><span><i class="score-key" />综合分 <i class="threshold-key" />阈值</span></div>
        <div v-for="row in visibleResults" :key="row.id" class="pair-chart-row">
          <router-link :to="'/results/' + row.id" class="pair-chart-name"><span>{{ row.submissionAFileName }}</span><small>↔ {{ row.submissionBFileName }}</small></router-link>
          <div><ScoreTrack :score="row.weightedSimilarityScore" :threshold="row.dynamicThreshold" compact :label="row.submissionAFileName + ' / ' + row.submissionBFileName" /><div class="pair-chart-values"><span>综合 {{ percent(row.weightedSimilarityScore, 1) }}</span><span>阈值 {{ percent(row.dynamicThreshold, 1) }}</span><strong :class="row.exceedThreshold ? 'margin-positive' : 'margin-negative'">{{ margin(row.riskMargin) }}</strong></div></div>
          <RiskBadge :level="row.riskLevel" />
          <el-tooltip content="查看此代码对的证据"><el-button :icon="View" text @click="$router.push('/results/' + row.id)" :aria-label="'查看代码对 ' + row.id + ' 的证据'" /></el-tooltip>
        </div>
        <el-empty v-if="!visibleResults.length" :description="search || riskFilter !== '全部' ? '本页没有符合条件的代码对' : '暂无结果'" />
        <div v-if="visibleResults.length" class="pair-chart-axis" aria-hidden="true"><div><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div></div>
      </div>
      <TaskStatisticalAnalysis v-else-if="resultView === 'analysis'" :rows="visibleResults" :page="currentPage" :loaded="results.length" :total="totalRows" />
      <el-table v-else v-loading="loading && !results.length" :data="visibleResults" :empty-text="search || riskFilter !== '全部' ? '本页没有符合条件的代码对' : '暂无结果'" row-key="id" class="results-desktop">
        <el-table-column label="代码 A" min-width="160">
          <template #default="{ row }">{{ row.submissionAFileName }}</template>
        </el-table-column>
        <el-table-column label="代码 B" min-width="160">
          <template #default="{ row }">{{ row.submissionBFileName }}</template>
        </el-table-column>
        <el-table-column label="综合分" width="110">
          <template #default="{ row }">{{ percent(row.weightedSimilarityScore) }}</template>
        </el-table-column>
        <el-table-column label="Token" width="110">
          <template #default="{ row }">{{ percent(row.tokenSimilarity) }}</template>
        </el-table-column>
        <el-table-column label="AST" width="100">
          <template #default="{ row }">{{ percent(row.astSimilarity) }}</template>
        </el-table-column>
        <el-table-column label="Canonical" width="120">
          <template #default="{ row }">{{ percent(row.canonicalTokenSimilarity) }}</template>
        </el-table-column>
        <el-table-column label="动态阈值" width="120">
          <template #default="{ row }">{{ percent(row.dynamicThreshold) }}</template>
        </el-table-column>
        <el-table-column label="风险边际" width="120">
          <template #default="{ row }">
            <span :class="row.exceedThreshold ? 'margin-positive' : 'margin-negative'">{{ margin(row.riskMargin) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="120"><template #default="{ row }"><RiskBadge :level="row.riskLevel" /></template></el-table-column>
        <el-table-column label="数据类型" width="110">
          <template #default="{ row }"><span class="text-muted">{{ row.isMock ? 'mock' : '实际分析' }}</span></template>
        </el-table-column>
        <el-table-column label="证据" width="120" fixed="right">
          <template #default="{ row }">
            <el-button :icon="View" link type="primary" @click="$router.push(`/results/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="resultView === 'table'" class="results-mobile">
        <article v-for="row in visibleResults" :key="row.id" class="mobile-pair">
          <div class="section-heading"><router-link :to="'/results/' + row.id">{{ row.submissionAFileName }}<span class="mobile-pair-second">{{ row.submissionBFileName }}</span></router-link><RiskBadge :level="row.riskLevel" /></div>
          <ScoreTrack :score="row.weightedSimilarityScore" :threshold="row.dynamicThreshold" compact />
          <dl><div><dt>综合分</dt><dd>{{ percent(row.weightedSimilarityScore, 1) }}</dd></div><div><dt>阈值</dt><dd>{{ percent(row.dynamicThreshold, 1) }}</dd></div><div><dt>风险边际</dt><dd>{{ margin(row.riskMargin) }}</dd></div></dl>
          <div class="mobile-pair-footer"><span>{{ row.isMock ? 'mock · 联调' : '实际分析' }}</span><el-button :icon="View" link type="primary" @click="$router.push('/results/' + row.id)">查看证据</el-button></div>
        </article>
        <el-empty v-if="!visibleResults.length" :description="search || riskFilter !== '全部' ? '本页没有符合条件的代码对' : '暂无结果'" />
      </div>
      <div class="table-footer"><span>本页 {{ visibleResults.length }} / {{ results.length }} 对</span><el-pagination v-model:current-page="currentPage" :page-size="20" :total="totalRows" layout="prev, pager, next, total" /></div>
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

.margin-positive {
  color: #b42318;
  font-weight: 700;
}

.margin-negative {
  color: #39705f;
  font-weight: 650;
}
.result-counts { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.risk-filter { width: 180px; }
.distribution-section { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 42px; }
.distribution-summary { min-width: 0; }
.review-boundary { border-left: 1px solid var(--line); padding-left: 28px; }
.review-boundary h3 { font-size: 13px; margin: 0 0 12px; }
.review-boundary p { font-size: 12px; color: #748091; line-height: 1.85; margin: 8px 0 0; }
.view-option { display: flex; align-items: center; gap: 6px; }
.chart-caption { display: flex; justify-content: space-between; gap: 14px; font-size: 11px; color: #7c8795; margin-bottom: 12px; flex-wrap: wrap; }
.score-key { width: 7px; height: 7px; border-radius: 50%; background: #087f74; display: inline-block; margin-right: 4px; }
.threshold-key { height: 11px; border-left: 2px dashed #946922; display: inline-block; margin: 0 4px 0 12px; vertical-align: middle; }
.pair-chart-row { display: grid; grid-template-columns: minmax(120px, .7fr) minmax(0, 1.5fr) 75px 34px; gap: 20px; align-items: center; border-bottom: 1px solid var(--line); padding: 18px 0; }
.pair-chart-name { font-size: 12px; text-decoration: none; overflow-wrap: anywhere; line-height: 1.6; }
.pair-chart-name:hover { text-decoration: underline; }
.pair-chart-name small { display: block; color: #7c8795; font-size: 11px; }
.pair-chart-values { display: flex; justify-content: space-between; gap: 8px; color: #7c8795; font-size: 11px; margin-top: 7px; flex-wrap: wrap; }
.pair-chart-axis { display: grid; grid-template-columns: minmax(120px, .7fr) minmax(0, 1.5fr) 75px 34px; gap: 20px; margin-top: 14px; font-size: 11px; color: #8b95a2; }
.pair-chart-axis > div { grid-column: 2; display: flex; justify-content: space-between; padding: 0 5px; }
.results-mobile { display: none; }
.mobile-pair { border-bottom: 1px solid var(--line); padding: 18px 0; }
.mobile-pair .section-heading { align-items: flex-start; }
.mobile-pair a { min-width: 0; text-decoration: none; line-height: 1.8; overflow-wrap: anywhere; }
.mobile-pair-second { display: block; color: var(--muted); font-size: 12px; }
.mobile-pair dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 14px 0; }
.mobile-pair dt { font-size: 11px; color: var(--muted); }
.mobile-pair dd { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; margin: 7px 0 0; }
.mobile-pair-footer { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 11px; }
@media (max-width: 1000px) { .table-toolbar { flex-wrap: wrap; } .distribution-section { gap: 24px; } }
@media (max-width: 680px) { .distribution-section { grid-template-columns: 1fr; } .review-boundary { border-left: 0; border-top: 1px solid var(--line); padding: 18px 0 0; } .results-desktop { display: none; } .results-mobile { display: block; } .pair-chart-row { grid-template-columns: minmax(0, 1fr) 75px 34px; gap: 12px; } .pair-chart-name { grid-column: 1 / -1; } .pair-chart-axis { grid-template-columns: minmax(0, 1fr) 75px 34px; gap: 12px; } .pair-chart-axis > div { grid-column: 1; } }
@media (max-width: 680px) {
  .result-counts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .result-counts .metric-tile { border-right: 1px solid var(--line); }
  .result-counts .metric-tile:nth-child(odd) { border-right: 0; }
  .result-counts .metric-tile:first-child { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; }
  .result-counts .metric-tile:first-child > strong { margin: 0; }
}
</style>
