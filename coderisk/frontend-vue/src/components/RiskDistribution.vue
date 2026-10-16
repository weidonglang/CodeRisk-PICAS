<script setup lang="ts">
import { computed } from 'vue'
import { riskDistribution } from '../utils/resultCharts'
import type { TaskResultSummary } from '../api/taskApi'
const props = defineProps<{ summary: TaskResultSummary | null }>()
const distribution = computed(() => riskDistribution(props.summary ? { ...props.summary } : null))
</script>

<template>
  <figure class="risk-distribution" aria-label="全任务风险等级分布">
    <div v-if="distribution.available && distribution.total" class="distribution-bar" role="img" :aria-label="distribution.segments.map(item => `${item.label} ${item.count} 对`).join('，')">
      <span v-for="item in distribution.segments" :key="item.level" :style="{ width: item.share + '%', background: item.color }" :title="`${item.label}：${item.count} 对`" />
    </div>
    <p v-else class="distribution-empty">{{ distribution.available ? '尚无已生成结果' : '分布暂不可用' }}</p>
    <figcaption class="distribution-legend">
      <div v-for="item in distribution.segments" :key="item.level"><i :style="{ background: item.color }" /><span>{{ item.label }}</span><strong>{{ item.count ?? '-' }}</strong><small>{{ item.count !== null && distribution.total ? (item.share).toFixed(1) + '%' : '-' }}</small></div>
    </figcaption>
  </figure>
</template>

<style scoped>
.risk-distribution { margin: 0; }
.distribution-bar { display: flex; height: 14px; background: #edf0f4; overflow: hidden; border-radius: 3px; margin: 24px 0; }
.distribution-bar > span { flex: 0 0 auto; }
.distribution-empty { color: var(--muted); padding: 4px 0; }
.distribution-legend { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 28px; }
.distribution-legend > div { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto auto; align-items: center; gap: 8px; font-size: 12px; }
.distribution-legend i { width: 6px; height: 6px; border-radius: 50%; }
.distribution-legend strong { font-variant-numeric: tabular-nums; }
.distribution-legend small { width: 43px; text-align: right; color: var(--muted); font-size: 11px; }
@media (max-width: 400px) { .distribution-legend { column-gap: 14px; } .distribution-legend > div { gap: 5px; } .distribution-legend small { display: none; } }
</style>
