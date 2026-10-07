<script setup lang="ts">
import { Download, Refresh, View } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { createTaskReport, getTask, getTaskResults, getTaskResultSummary, type DetectionTask, type ResultRow, type TaskResultSummary } from '../api/taskApi'

const route = useRoute()
const taskId = computed(() => Number(route.params.taskId))
const loading = ref(false)
const error = ref('')
const summary = ref<TaskResultSummary | null>(null)
const task = ref<DetectionTask | null>(null)
const results = ref<ResultRow[]>([])
const reportLoading = ref(false)
const reportMessage = ref('')

function percent(value: number) {
  return `${Math.round(value * 100)}%`
}

function margin(value: number) {
  const points = value * 100
  return `${points >= 0 ? '+' : ''}${points.toFixed(1)} pp`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [taskResponse, summaryResponse, resultsResponse] = await Promise.all([
      getTask(taskId.value),
      getTaskResultSummary(taskId.value),
      getTaskResults(taskId.value),
    ])
    task.value = taskResponse.data
    summary.value = summaryResponse.data
    results.value = resultsResponse.data.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载结果失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

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
        <p>综合展示原始、结构与规范化相似信号，并按题目画像动态校准复核阈值。</p>
      </div>
      <div class="header-actions">
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
