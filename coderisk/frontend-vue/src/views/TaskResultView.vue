<script setup lang="ts">
import { Download, Refresh, View } from '@element-plus/icons-vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { createTaskReport, getTask, getTaskFailures, getTaskResults, getTaskResultSummary, startTask, type DetectionTask, type ResultRow, type TaskResultSummary, type TaskPairFailure } from '../api/taskApi'

const route = useRoute()
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
const active = computed(() => ['RUNNING', 'QUEUED'].includes(task.value?.status ?? ''))
const retryable = computed(() => ['PENDING', 'PARTIAL', 'FAILED'].includes(task.value?.status ?? ''))
let timer: ReturnType<typeof setTimeout> | undefined
let disposed = false

function percent(value: number) {
  return `${Math.round(value * 100)}%`
}

function margin(value: number) {
  const points = value * 100
  return `${points >= 0 ? '+' : ''}${points.toFixed(1)} pp`
}

async function load() {
  if (loading.value || disposed) return
  clearTimeout(timer)
  const requestedTask = taskId.value
  const requestedPage = currentPage.value
  loading.value = true
  error.value = ''
  try {
    const [taskResponse, summaryResponse, resultsResponse, failuresResponse] = await Promise.all([
      getTask(requestedTask),
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
watch(currentPage, load)
watch(taskId, () => { currentPage.value = 1; task.value = null; summary.value = null; results.value = []; failures.value = []; totalRows.value = 0; void load() })

async function resume() {
  starting.value = true
  try {
    const response = await startTask(taskId.value)
    task.value = response.data
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '启动失败，请稍后重试'
  } finally { starting.value = false }
}

async function exportReport() {
  reportLoading.value = true
  reportMessage.value = ''
  try {
    const response = await createTaskReport(taskId.value, {
      format: 'HTML',
      includeLowRiskPairs: true,
      includeCodeSnippets: true,
      includeThresholdExplanation: true,
    })
    reportMessage.value = `报告已生成：${response.data.fileName}`
    const link = document.createElement('a')
    link.href = response.data.downloadUrl
    link.download = response.data.fileName
    link.click()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '报告生成失败'
  } finally {
    reportLoading.value = false
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>检测结果</h1>
        <p>展示相似信号、复核阈值与证据。运行期间每两秒刷新，重试保留已成功结果。</p>
      </div>
      <div class="header-actions">
        <el-button v-if="retryable" type="primary" :loading="starting" :disabled="loading" @click="resume">{{ task?.status === 'PENDING' ? '开始检测' : '重试未完成代码对' }}</el-button>
        <el-button :icon="Download" :loading="reportLoading" @click="exportReport">导出报告</el-button>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
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
      <h2>任务状态：{{ task.status }}</h2>
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

    <div class="metric-grid section-gap">
      <div class="metric-tile">
        <span>结果数</span>
        <strong>{{ summary?.totalResults ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>低风险</span>
        <strong>{{ summary?.lowCount ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>较高风险</span>
        <strong>{{ summary?.elevatedCount ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>高风险</span>
        <strong>{{ summary?.highCount ?? 0 }}</strong>
      </div>
    </div>

    <section class="panel section-gap">
      <h2>代码对结果</h2>
      <el-table v-loading="loading" :data="results" empty-text="暂无结果">
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
        <el-table-column prop="riskLevel" label="风险等级" width="120" />
        <el-table-column label="数据类型" width="110">
          <template #default="{ row }">{{ row.isMock ? 'mock' : 'real' }}</template>
        </el-table-column>
        <el-table-column label="证据" width="120" fixed="right">
          <template #default="{ row }">
            <el-button :icon="View" link type="primary" @click="$router.push(`/results/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="currentPage" :page-size="20" :total="totalRows" layout="prev, pager, next, total" class="section-gap" />
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
</style>
