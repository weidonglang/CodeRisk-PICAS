<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { getLatestExperiment, type ExperimentMetricRow, type LatestExperiment } from '../api/experimentApi'

const loading = ref(false)
const error = ref('')
const experiment = ref<LatestExperiment | null>(null)

function percent(value: number | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    experiment.value = (await getLatestExperiment()).data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '实验结果加载失败'
  } finally {
    loading.value = false
  }
}

function rows(key: 'E1_fixedVsDynamic' | 'E3_fusion' | 'E4_ablation'): ExperimentMetricRow[] {
  return experiment.value?.summary[key] ?? []
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>实验</h1>
        <p>展示脚本真实运行的最小基线、融合与消融结果，不代替大规模 benchmark。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert v-if="error" type="error" :title="error" :closable="false" />

    <div v-if="experiment" class="metric-grid section-gap">
      <div class="metric-tile">
        <span>实验样本</span>
        <strong>{{ experiment.summary.run.caseCount }}</strong>
      </div>
      <div class="metric-tile">
        <span>Raw token 均值</span>
        <strong>{{ percent(experiment.summary.E2_rawVsCanonical.meanRawTokenSimilarity) }}</strong>
      </div>
      <div class="metric-tile">
        <span>Canonical 均值</span>
        <strong>{{ percent(experiment.summary.E2_rawVsCanonical.meanCanonicalTokenSimilarity) }}</strong>
      </div>
      <div class="metric-tile">
        <span>失败 / 边界</span>
        <strong>{{ experiment.summary.E5_failureAnalysis.failureCount }} / {{ experiment.summary.E5_failureAnalysis.borderlineCount }}</strong>
      </div>
    </div>

    <el-alert
      v-if="experiment"
      class="section-gap"
      type="info"
      :closable="false"
      :title="`Problem-level 隔离：validation ${experiment.summary.run.validationCaseCount} 条 / test ${experiment.summary.run.testCaseCount} 条`"
      :description="`Validation 选择固定阈值 ${experiment.summary.validationCalibration.selectedFixedThreshold.toFixed(2)}；生产动态阈值公式未在 test 上调整。`"
    />

    <section v-if="experiment" class="panel section-gap">
      <h2>E1 固定阈值 vs 动态阈值</h2>
      <el-table :data="rows('E1_fixedVsDynamic')">
        <el-table-column prop="method" label="方法" min-width="150" />
        <el-table-column label="Precision" width="110"><template #default="{ row }">{{ percent(row.precision) }}</template></el-table-column>
        <el-table-column label="Recall" width="100"><template #default="{ row }">{{ percent(row.recall) }}</template></el-table-column>
        <el-table-column label="F1" width="90"><template #default="{ row }">{{ percent(row.f1) }}</template></el-table-column>
        <el-table-column label="Natural FPR" width="130"><template #default="{ row }">{{ percent(row.naturalSimilarityFpr) }}</template></el-table-column>
      </el-table>
    </section>

    <section v-if="experiment" class="panel section-gap">
      <h2>E3 多维融合 / E4 消融</h2>
      <div class="experiment-tables">
        <el-table :data="rows('E3_fusion')">
          <el-table-column prop="method" label="融合方法" min-width="150" />
          <el-table-column label="F1" width="90"><template #default="{ row }">{{ percent(row.f1) }}</template></el-table-column>
          <el-table-column label="FNR" width="90"><template #default="{ row }">{{ percent(row.falseNegativeRate) }}</template></el-table-column>
        </el-table>
        <el-table :data="rows('E4_ablation')">
          <el-table-column prop="method" label="消融方法" min-width="150" />
          <el-table-column label="F1" width="90"><template #default="{ row }">{{ percent(row.f1) }}</template></el-table-column>
          <el-table-column label="FNR" width="90"><template #default="{ row }">{{ percent(row.falseNegativeRate) }}</template></el-table-column>
        </el-table>
      </div>
      <p class="run-meta">
        {{ experiment.summary.run.formulaVersion }} · {{ experiment.summary.run.algorithmVersion }} ·
        {{ experiment.summary.run.datasetVersion }} · seed {{ experiment.summary.run.randomSeed }}
      </p>
    </section>
  </section>
</template>

<style scoped>
.section-gap {
  margin-top: 16px;
}

.experiment-tables {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.run-meta {
  color: #63726e;
  font-size: 13px;
  line-height: 1.6;
  margin: 16px 0 0;
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .experiment-tables {
    grid-template-columns: 1fr;
  }
}
</style>
