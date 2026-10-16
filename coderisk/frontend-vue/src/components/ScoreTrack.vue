<script setup lang="ts">
import { computed } from 'vue'
import { scorePosition } from '../utils/resultCharts'
import { percent } from '../utils/presentation'

const props = withDefaults(defineProps<{ score?: number | null; threshold?: number | null; label?: string; compact?: boolean }>(), { label: '综合分与阈值', compact: false })
const position = computed(() => scorePosition(props.score))
const thresholdPosition = computed(() => scorePosition(props.threshold))
const description = computed(() => `${props.label}：综合分 ${percent(props.score, 1)}，阈值 ${percent(props.threshold, 1)}`)
</script>

<template>
  <figure class="score-track" :class="{ compact }" role="img" :aria-label="description">
    <div v-if="!compact" class="track-values"><span><i class="legend-dot" />综合分 <strong>{{ percent(score, 1) }}</strong></span><span><i class="legend-marker" />阈值 <strong>{{ percent(threshold, 1) }}</strong></span></div>
    <div class="track-plot" aria-hidden="true">
      <div class="track-grid" />
      <div v-if="position !== null" class="track-fill" :style="{ width: position + '%' }" />
      <span v-if="position !== null" class="track-point" :style="{ left: position + '%' }" />
      <span v-if="thresholdPosition !== null" class="track-threshold" :style="{ left: thresholdPosition + '%' }" />
    </div>
    <div v-if="!compact" class="track-axis" aria-hidden="true"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
    <figcaption v-if="position === null || thresholdPosition === null" class="track-missing">{{ position === null ? '综合分未提供' : '' }}{{ position === null && thresholdPosition === null ? ' · ' : '' }}{{ thresholdPosition === null ? '阈值未提供' : '' }}</figcaption>
  </figure>
</template>

<style scoped>
.score-track { margin: 0; min-width: 0; }
.track-values { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; font-size: 12px; color: #657083; margin-bottom: 17px; }
.track-values strong { font-variant-numeric: tabular-nums; margin-left: 6px; color: var(--ink); }
.legend-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #168578; margin-right: 6px; }
.legend-marker { display: inline-block; height: 11px; border-left: 2px dashed #a8752b; margin-right: 6px; vertical-align: middle; }
.track-plot { position: relative; height: 28px; margin: 0 5px; }
.track-grid { position: absolute; inset: 8px 0; background: #edf0f4; border-radius: 2px; }
.track-fill { position: absolute; top: 8px; height: 12px; background: #b2ded6; border-radius: 2px; }
.track-point { position: absolute; top: 8px; width: 12px; height: 12px; border-radius: 50%; background: #087f74; border: 2px solid white; box-shadow: 0 0 0 1px #087f74; transform: translateX(-50%); }
.track-threshold { position: absolute; top: 1px; height: 26px; border-left: 2px dashed #946922; transform: translateX(-1px); }
.track-axis { display: flex; justify-content: space-between; margin-top: 4px; color: #85909d; font-size: 11px; }
.track-missing { font-size: 11px; color: #7c8795; margin-top: 6px; }
.compact .track-plot { height: 22px; }
.compact .track-grid, .compact .track-fill, .compact .track-point { top: 6px; height: 9px; }
.compact .track-point { width: 9px; }
.compact .track-threshold { height: 21px; top: 0; }
</style>
