<script setup lang="ts">
import { Download, Refresh } from '@element-plus/icons-vue'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { EChartsOption, EChartsType } from 'echarts'

const props = withDefaults(defineProps<{ option: EChartsOption; title: string; description: string; fileName: string; height?: number }>(), { height: 320 })
const emit = defineEmits<{ selectResult: [id: number] }>()
const surface = ref<HTMLDivElement>()
const error = ref(false)
const ready = ref(false)
let chart: EChartsType | undefined
let observer: ResizeObserver | undefined
let disposed = false
let mounting = false

function render() {
  chart?.setOption({ ...props.option, animation: false, textStyle: { fontFamily: 'Microsoft YaHei, sans-serif', fontSize: 11 },
    aria: { enabled: true, label: { description: props.description } },
  }, { notMerge: true })
}

async function initialize() {
  if (disposed || mounting || chart || !surface.value?.clientWidth || !surface.value?.clientHeight) return
  mounting = true
  error.value = false
  try {
    const { init } = await import('../charts/echartsRuntime')
    if (disposed || !surface.value) return
    chart = init(surface.value, undefined, { renderer: 'svg' })
    chart.on('click', (event: unknown) => {
      const data = (event as { data?: { resultId?: unknown } }).data
      if (typeof data?.resultId === 'number' && Number.isSafeInteger(data.resultId) && data.resultId > 0) emit('selectResult', data.resultId)
    })
    render()
    ready.value = true
  } catch {
    chart?.dispose(); chart = undefined
    error.value = true; ready.value = false
  } finally { mounting = false }
}

function download() {
  if (!chart) return
  try {
    const link = document.createElement('a')
    link.href = chart.getDataURL({ type: 'svg', backgroundColor: '#ffffff' })
    link.download = props.fileName + '.svg'
    link.click()
  } catch { ElMessage.error('图表导出失败，可使用下方数值明细') }
}

function reloadPage() { window.location.reload() }

onMounted(() => {
  observer = new ResizeObserver(() => {
    if (disposed) return
    if (chart && surface.value?.clientWidth && surface.value?.clientHeight) chart.resize()
    else if (!error.value) void initialize()
  })
  if (surface.value) observer.observe(surface.value)
  void initialize()
})
watch(() => props.option, () => { if (chart) render() }, { deep: true })
onUnmounted(() => { disposed = true; observer?.disconnect(); chart?.dispose(); chart = undefined })
</script>

<template>
  <figure class="stat-chart" :data-chart="fileName" :data-ready="ready && !error">
    <div class="chart-heading"><h3>{{ title }}</h3><el-tooltip :content="'下载' + title + ' SVG'"><el-button :icon="Download" text :disabled="!ready || error" @click="download" :aria-label="'下载' + title + ' SVG'" /></el-tooltip></div>
    <div class="chart-container" :style="{ height: height + 'px' }">
      <div ref="surface" class="chart-surface" role="img" :aria-label="description" />
      <div v-if="error" class="chart-fallback"><span>图表暂不可用，数值明细仍可查看</span><el-tooltip content="刷新页面重试图表"><el-button :icon="Refresh" text @click="reloadPage" aria-label="刷新页面重试图表" /></el-tooltip></div>
      <div v-else-if="!ready" class="chart-fallback"><span>图表加载中</span></div>
    </div>
  </figure>
</template>

<style scoped>
.stat-chart { margin: 0; min-width: 0; }
.chart-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.chart-heading h3 { font-size: 13px; margin: 0; font-weight: 600; }
.chart-container { position: relative; width: 100%; min-width: 0; overflow: hidden; }
.chart-surface { height: 100%; width: 100%; }
.chart-fallback { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 10px; color: var(--muted); background: #fff; font-size: 12px; }
</style>
