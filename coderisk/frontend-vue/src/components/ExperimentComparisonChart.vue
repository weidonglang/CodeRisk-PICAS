<script setup lang="ts">
import { computed, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import type { ExperimentSummary } from '../api/experimentApi'
import StatChart from './StatChart.vue'
import { isScore } from '../utils/analysisStatistics'

const props = defineProps<{ summary: ExperimentSummary }>()
const group = ref<'E1_fixedVsDynamic' | 'E3_fusion' | 'E4_ablation'>('E1_fixedVsDynamic')
const metric = ref<'f1' | 'recall' | 'precision' | 'falsePositiveRate' | 'naturalSimilarityFpr'>('f1')
const labels = { f1: 'F1', recall: 'Recall', precision: 'Precision', falsePositiveRate: 'FPR', naturalSimilarityFpr: 'NaturalSimilar FPR' }
const rows = computed(() => props.summary[group.value] ?? [])
const valid = computed(() => rows.value.filter(row => isScore(row[metric.value])))
const option = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis', renderMode: 'richText', confine: true },
  grid: { left: 48, right: 20, top: 24, bottom: 88 },
  xAxis: { type: 'category', data: rows.value.map(row => `${row.method}\nn=${Number.isSafeInteger(row.sampleCount) && row.sampleCount >= 0 ? row.sampleCount : '-'}`), axisLabel: { fontSize: 10, interval: 0, width: 100, overflow: 'truncate', rotate: rows.value.length > 4 ? 20 : 0 } },
  yAxis: { type: 'value', min: 0, max: 100, name: '%', splitLine: { lineStyle: { color: '#edf0f4' } } },
  series: [{ type: 'bar', name: labels[metric.value], barMaxWidth: 46, data: rows.value.map((row, index) => ({ value: isScore(row[metric.value]) ? row[metric.value]! * 100 : '-', itemStyle: { color: ['#558bc9', '#359a86', '#9a83b7', '#c39a55'][index % 4] } })) }],
}))
</script>

<template>
  <section class="panel section-gap experiment-comparison">
    <div class="section-heading"><h2>实验方法对比</h2><span>同一次运行 · {{ summary.run.runId }}</span></div>
    <div class="comparison-controls"><el-segmented v-model="group" :options="[{ label: '固定 / 动态', value: 'E1_fixedVsDynamic' }, { label: '融合', value: 'E3_fusion' }, { label: '消融', value: 'E4_ablation' }]" aria-label="实验对比组" /><el-select v-model="metric" aria-label="实验对比指标"><el-option v-for="(label, key) in labels" :key="key" :value="key" :label="label" /></el-select></div>
    <StatChart v-if="valid.length" :option="option" :title="labels[metric] + ' · 方法对比'" file-name="experiment-method-comparison" :description="`${summary.run.datasetVersion}，${summary.run.runId}，${labels[metric]}；${valid.length}/${rows.length}方法有有效值，各方法n见横轴与原表。缺失不按0绘制。`" />
    <el-empty v-else description="当前指标不可计算，未绘制方法对比" :image-size="50" />
    <p class="comparison-note">{{ summary.run.datasetVersion }} · 有效方法 {{ valid.length }}/{{ rows.length }}。Precision / Recall / F1 越高与 FPR 越低含义不同；分母、支持范围和标签资格须结合原表及运行记录，图表不认证正式 benchmark。</p>
  </section>
</template>

<style scoped>
.comparison-controls { display: flex; gap: 18px; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 20px; }
.comparison-controls .el-select { width: 190px; }
.comparison-note { font-size: 11px; color: #7c8795; line-height: 1.8; margin: 0; }
</style>
