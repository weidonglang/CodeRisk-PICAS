<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import type { EChartsOption } from 'echarts'
import StatChart from './StatChart.vue'
import { analysisCsv, describeScores, dimensionHeatmap, dimensionSummaries, normalizationPairs, quantile, scoreHistogram, type AnalysisRow } from '../utils/analysisStatistics'
import { margin, percent } from '../utils/presentation'

const props = defineProps<{ rows: AnalysisRow[]; page: number; loaded: number; total: number }>()
const router = useRouter()
const route = useRoute()
function plotFromQuery() { return ['normalization', 'dimensions'].includes(String(route.query.plot)) ? String(route.query.plot) : 'distribution' }
const mode = ref(plotFromQuery())
watch(() => route.query.plot, () => { mode.value = plotFromQuery() })
watch(mode, value => {
  if (!/^\/tasks\/\d+\/results$/.test(route.path) || value === plotFromQuery()) return
  void router.replace({ query: { ...route.query, plot: value === 'distribution' ? undefined : value } })
})
const histogramMeasure = ref('count')
const bins = ref(10)
const description = computed(() => `第${props.page}页筛选后${props.rows.length}对；本页加载${props.loaded}对，任务总结果${props.total}对。` +
  (props.total > 0 && props.rows.length === props.total && props.loaded === props.total ? '当前覆盖全部已生成结果，仍不代表独立样本。' : '当前页不是随机抽样，不能外推全任务。'))
const scores = computed(() => describeScores(props.rows.map(row => row.weightedSimilarityScore)))
const histogram = computed(() => scoreHistogram(props.rows.map(row => row.weightedSimilarityScore), bins.value))
const pairs = computed(() => normalizationPairs(props.rows))
const summaries = computed(() => dimensionSummaries(props.rows))
const cells = computed(() => dimensionHeatmap(props.rows))
const boxes = computed(() => summaries.value.filter(row => row.n >= 4))
const medianDelta = computed(() => quantile(pairs.value.points.map(row => row.delta).sort((a, b) => a - b), .5))
const grid = { top: 26, bottom: 42, left: 46, right: 16, containLabel: false }
const axisColor = '#84909f'
const tooltip = { renderMode: 'richText' as const, confine: true, textStyle: { fontSize: 11 } }

const histogramOption = computed<EChartsOption>(() => ({
  tooltip: { ...tooltip, trigger: 'axis' }, grid,
  xAxis: { type: 'category', data: histogram.value.bins.map(bin => `${Math.round(bin.lower * 100)}–${Math.round(bin.upper * 100)}`), axisLabel: { color: axisColor, fontSize: 10, interval: bins.value === 10 ? 1 : 0 }, axisTick: { alignWithLabel: true } },
  yAxis: { type: 'value', name: histogramMeasure.value === 'share' ? '占比 %' : '代码对数', min: 0, max: histogramMeasure.value === 'share' ? 100 : undefined, minInterval: histogramMeasure.value === 'count' ? 1 : undefined, axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: '#edf0f4' } } },
  series: [{ type: 'bar', name: histogramMeasure.value === 'share' ? '有效分数占比 %' : '有效分数计数', barMaxWidth: 48, data: histogram.value.bins.map(bin => histogramMeasure.value === 'share' ? Number(((bin.share ?? 0) * 100).toFixed(2)) : bin.count), itemStyle: { color: '#4c98a8', borderRadius: [2, 2, 0, 0] } }],
}))

const riskGroups = [
  { key: 'LOW', label: '低风险', color: '#359a86' }, { key: 'MEDIUM', label: '中风险', color: '#558bc9' },
  { key: 'ELEVATED', label: '较高风险', color: '#c99439' }, { key: 'HIGH', label: '高风险', color: '#c55a58' },
  { key: 'UNKNOWN', label: '未知等级', color: '#88919e' },
]
const scatterOption = computed<EChartsOption>(() => ({
  tooltip: { ...tooltip, formatter: (event: unknown) => {
    const data = (event as { data?: { value?: number[]; resultId?: number } }).data
    return data?.value ? `#${data.resultId}\nRaw ${data.value[0]?.toFixed(1)}%\nCanonical ${data.value[1]?.toFixed(1)}%` : ''
  } },
  grid: { ...grid, left: 46, bottom: 56, top: 30, right: 24 },
  xAxis: { type: 'value', name: 'Raw Token %', min: 0, max: 100, interval: 25, nameLocation: 'middle', nameGap: 30, axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: '#edf0f4' } } },
  yAxis: { type: 'value', name: 'Canonical %', min: 0, max: 100, interval: 25, axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: '#edf0f4' } } },
  series: riskGroups.map((group, index) => ({
    type: 'scatter', name: group.label, symbolSize: 11, clip: false,
    itemStyle: { color: group.color, opacity: .85, borderColor: '#fff', borderWidth: 1 },
    data: pairs.value.points.filter(point => (riskGroups.some(item => item.key === point.riskLevel) ? point.riskLevel : 'UNKNOWN') === group.key).map(point => ({ value: [point.raw * 100, point.canonical * 100], resultId: point.id })),
    markLine: index === 0 ? { silent: true, symbol: ['none', 'none'], label: { show: false }, lineStyle: { color: '#9aa8b6', type: 'dashed', width: 1 }, data: [[{ coord: [0, 0] }, { coord: [100, 100] }]] } : undefined,
  })),
}))

const heatmapOption = computed<EChartsOption>(() => ({
  tooltip: { ...tooltip, formatter: (event: unknown) => {
    const data = (event as { data?: { resultId?: number; dimension?: string; value?: number[] } }).data
    return data?.value ? `#${data.resultId} · ${data.dimension}\n${data.value[2]?.toFixed(1)}%` : ''
  } },
  grid: { top: 10, bottom: 70, left: 66, right: 16 },
  xAxis: { type: 'category', data: summaries.value.map(item => item.key === 'tokenSimilarity' ? 'Raw' : item.label), axisLabel: { fontSize: 10, color: axisColor, interval: 0 }, splitArea: { show: false } },
  yAxis: { type: 'category', data: props.rows.map(row => '#' + row.id), inverse: true, axisLabel: { color: axisColor, fontSize: 10 }, axisTick: { show: false } },
  visualMap: { type: 'continuous', min: 0, max: 100, orient: 'horizontal', left: 'center', bottom: 2, itemWidth: 10, itemHeight: 110, text: ['100%', '0%'], textStyle: { fontSize: 10 }, calculable: false, inRange: { color: ['#d9e6f3', '#80b8c9', '#156c78'] } },
  series: [{ type: 'heatmap', data: cells.value.map(cell => ({ value: [cell.columnIndex, cell.rowIndex, cell.value * 100], resultId: cell.id, dimension: cell.label, label: { color: cell.value > .6 ? '#ffffff' : '#34495e' } })), label: { show: true, fontSize: 10, formatter: (event: unknown) => { const value = (event as { value: number[] }).value; return value[2]!.toFixed(0) } }, itemStyle: { borderWidth: 3, borderColor: '#ffffff' }, emphasis: { itemStyle: { borderColor: '#536a80', borderWidth: 2 } } }],
}))

const boxOption = computed<EChartsOption>(() => ({
  tooltip: { ...tooltip, trigger: 'item' }, grid: { ...grid, top: 20 },
  xAxis: { type: 'category', data: boxes.value.map(row => `${row.label}\nn=${row.n}`), axisLabel: { color: axisColor, fontSize: 10, interval: 0 } },
  yAxis: { type: 'value', min: 0, max: 100, name: '%', axisLabel: { color: axisColor }, splitLine: { lineStyle: { color: '#edf0f4' } } },
  series: [{ type: 'boxplot', data: boxes.value.map(row => ({ value: [row.min!, row.q1!, row.median!, row.q3!, row.max!].map(value => value * 100), itemStyle: { color: row.color + '35', borderColor: row.color } })) }],
}))

function downloadCsv() {
  const url = URL.createObjectURL(new Blob([analysisCsv(props.rows, 'CURRENT_PAGE_FILTERED_PAGE_' + props.page)], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url; link.download = `picas-page-${props.page}-analysis.csv`; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function openResult(id: number) { void router.push('/results/' + id) }
</script>

<template>
  <section class="statistical-analysis" aria-label="当前页描述性统计分析">
    <div class="analysis-toolbar"><el-segmented v-model="mode" :options="[{ label: '分数分布', value: 'distribution' }, { label: '规范化对照', value: 'normalization' }, { label: '多维结构', value: 'dimensions' }]" aria-label="统计分析类型" /><el-button :icon="Download" :disabled="!rows.length" @click="downloadCsv">导出本页 CSV</el-button></div>
    <p class="analysis-scope">{{ description }}</p>
    <el-empty v-if="!rows.length" description="当前页筛选后没有可分析的代码对" :image-size="50" />
    <template v-else>
      <div v-if="mode === 'distribution'" class="analysis-distribution">
        <div class="analysis-plot"><div class="plot-controls"><el-segmented v-model="histogramMeasure" :options="[{ label: '计数', value: 'count' }, { label: '占比', value: 'share' }]" aria-label="直方图纵轴" /><el-segmented v-model="bins" :options="[{ label: '5组', value: 5 }, { label: '10组', value: 10 }]" aria-label="直方图区间数" /></div>
          <StatChart v-if="scores.n" :option="histogramOption" title="综合分直方图" file-name="score-histogram" :description="description + `有效分数${scores.n}，缺失${scores.missing}。横轴是相似分区间，不是时间。`" />
          <el-empty v-else description="没有有效综合分，未绘制分布" :image-size="50" />
          <p class="analysis-note">有效 n={{ histogram.n }} · 缺失/无效 {{ histogram.missing }} · 区间左闭右开，最后一组包含100%；占比分母为有效综合分。</p>
        </div>
        <aside class="analysis-facts"><h3>样本描述</h3><dl><div><dt>有效代码对</dt><dd>{{ scores.n }} / {{ rows.length }}</dd></div><div><dt>中位数</dt><dd>{{ percent(scores.median, 1) }}</dd></div><div><dt>下四分位 Q1</dt><dd>{{ percent(scores.q1, 1) }}</dd></div><div><dt>上四分位 Q3</dt><dd>{{ percent(scores.q3, 1) }}</dd></div><div><dt>均值</dt><dd>{{ percent(scores.mean, 1) }}</dd></div><div><dt>范围</dt><dd>{{ percent(scores.min, 1) }} – {{ percent(scores.max, 1) }}</dd></div></dl><p>仅描述当前页，不计算置信区间、检验显著性或推断独立来源。代码对可能共享提交，并非独立样本。</p></aside>
      </div>
      <template v-else-if="mode === 'normalization'">
        <div class="analysis-distribution"><div class="analysis-plot"><StatChart v-if="pairs.n" :option="scatterOption" title="Raw / Canonical 散点图" file-name="normalization-scatter" :height="360" :description="description + `两指标共同有效${pairs.n}，缺失${pairs.missing}。虚线是y=x参考线，不是拟合线。`" @select-result="openResult" /><el-empty v-else description="没有共同有效的 Raw / Canonical，未绘制散点" :image-size="50" /><div class="scatter-legend"><span v-for="group in riskGroups" :key="group.key"><i :style="{ background: group.color }" />{{ group.label }}</span></div><p class="analysis-note">参考线 y=x；点的位置未经抖动，重合位置可能对应多对代码。颜色沿用后端风险等级，不由散点重判。</p></div>
        <aside class="analysis-facts"><h3>规范化前后</h3><dl><div><dt>共同有效</dt><dd>{{ pairs.n }} / {{ rows.length }}</dd></div><div><dt>Canonical 更高</dt><dd>{{ pairs.increased }}</dd></div><div><dt>基本相同</dt><dd>{{ pairs.unchanged }}</dd></div><div><dt>Canonical 更低</dt><dd>{{ pairs.decreased }}</dd></div><div><dt>差值中位数</dt><dd>{{ margin(medianDelta) }}</dd></div></dl><div v-if="pairs.n" class="change-ratio" role="img" :aria-label="`更高${pairs.increased}，相同${pairs.unchanged}，更低${pairs.decreased}`"><span :style="{ width: pairs.increased / pairs.n * 100 + '%', background: '#359a86' }" /><span :style="{ width: pairs.unchanged / pairs.n * 100 + '%', background: '#8299b3' }" /><span :style="{ width: pairs.decreased / pairs.n * 100 + '%', background: '#c99439' }" /></div><p>差值与比例不是识别成功率，也不是额外风险加分。当前页观察不能证明规范化有效或判断派生关系。</p></aside></div>
      </template>
      <template v-else>
        <div class="multi-dimensional"><div class="analysis-plot"><StatChart v-if="cells.length" :option="heatmapOption" title="逐对多维指标热力图" file-name="dimension-heatmap" :height="Math.max(220, rows.length * 28 + 100)" :description="description + `四个分量共${rows.length * 4}格，有效${cells.length}格；空白是缺失，不是0分。`" @select-result="openResult" /><el-empty v-else description="四维指标均不可用，未绘制热力图" :image-size="50" /><p class="analysis-note">空白=缺失，不是0；颜色表示相似分，不表示相关系数。每行是一个代码对，不是一个独立学生。</p></div><div class="analysis-plot"><StatChart v-if="boxes.length" :option="boxOption" title="分量箱线图" file-name="dimension-boxplot" :description="description + '每分量至少4个有效值才绘图；箱体Q1到Q3，须线取最小和最大值，不进行异常值检验。'" /><el-empty v-else description="各分量有效值不足4个，暂不绘制箱线图" :image-size="50" /><p class="analysis-note">Q1/中位数/Q3采用线性插值；须线为 min/max，不是1.5IQR异常判断，也不表示四分量独立。</p></div></div>
      </template>
      <details class="analysis-numbers"><summary>数值明细 · 分量统计与原始代码对</summary>
        <div class="analysis-table-wrap"><table><caption>当前页各分量独立有效分母</caption><thead><tr><th>分量</th><th>有效 n</th><th>缺失</th><th>最小</th><th>Q1</th><th>中位数</th><th>Q3</th><th>最大</th></tr></thead><tbody><tr v-for="item in summaries" :key="item.key"><th>{{ item.label }}</th><td>{{ item.n }}</td><td>{{ item.missing }}</td><td>{{ percent(item.min, 1) }}</td><td>{{ percent(item.q1, 1) }}</td><td>{{ percent(item.median, 1) }}</td><td>{{ percent(item.q3, 1) }}</td><td>{{ percent(item.max, 1) }}</td></tr></tbody></table></div>
        <div class="analysis-table-wrap"><table><caption>当前页筛选后的原始指标 · 缺失值显示为“-”</caption><thead><tr><th>代码对</th><th>Raw</th><th>{{ summaries[1]?.label ?? '结构' }}</th><th>Canonical</th><th>Mapping</th><th>综合分</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><th><router-link :to="'/results/' + row.id">#{{ row.id }}</router-link></th><td>{{ percent(row.tokenSimilarity, 1) }}</td><td>{{ percent(row.astSimilarity, 1) }}</td><td>{{ percent(row.canonicalTokenSimilarity, 1) }}</td><td>{{ percent(row.identifierMappingSimilarity, 1) }}</td><td>{{ percent(row.weightedSimilarityScore, 1) }}</td></tr></tbody></table></div>
      </details>
    </template>
  </section>
</template>

<style scoped>
.analysis-toolbar, .plot-controls { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.analysis-scope { font-size: 12px; line-height: 1.8; padding: 12px 0 16px; margin: 0; color: #788494; }
.analysis-distribution { display: grid; grid-template-columns: minmax(0, 2fr) minmax(190px, .8fr); gap: 32px; }
.analysis-plot { min-width: 0; }
.plot-controls { margin: 6px 0 18px; }
.analysis-facts { border-left: 1px solid var(--line); padding-left: 26px; }
.analysis-facts h3 { font-size: 13px; margin: 8px 0 18px; }
.analysis-facts dl { margin: 0; }
.analysis-facts dl > div { display: flex; justify-content: space-between; gap: 14px; border-bottom: 1px solid var(--line); padding: 12px 0; font-size: 12px; }
.analysis-facts dt { color: #788494; }
.analysis-facts dd { margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; }
.analysis-facts p, .analysis-note { font-size: 11px; line-height: 1.85; color: #7c8795; margin: 15px 0 0; }
.scatter-legend { display: flex; flex-wrap: wrap; gap: 16px; font-size: 11px; color: #6e7b8a; }
.scatter-legend i { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.change-ratio { display: flex; height: 10px; margin-top: 20px; background: #edf0f4; border-radius: 2px; overflow: hidden; }
.multi-dimensional { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 32px; align-items: start; }
.analysis-numbers { border-top: 1px solid var(--line); margin-top: 24px; padding-top: 18px; }
.analysis-numbers summary { cursor: pointer; font-size: 12px; color: #527185; }
.analysis-table-wrap { width: 100%; overflow-x: auto; margin-top: 20px; }
table { width: 100%; border-collapse: collapse; font-size: 11px; white-space: nowrap; }
caption { text-align: left; padding: 0 0 12px; color: #788494; }
td, th { text-align: right; padding: 10px 12px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums; }
th:first-child { text-align: left; }
thead th { font-weight: 500; color: #7c8795; background: #f8fafc; }
tbody th { font-weight: 500; }
@media (max-width: 1000px) { .analysis-distribution, .multi-dimensional { grid-template-columns: 1fr; } .analysis-facts { border-left: 0; border-top: 1px solid var(--line); padding: 18px 0 0; } .analysis-facts dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 28px; } }
@media (max-width: 480px) { .analysis-facts dl { grid-template-columns: 1fr; } .analysis-toolbar { gap: 14px; } }
</style>
