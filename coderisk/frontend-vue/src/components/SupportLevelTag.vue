<script setup lang="ts">
import type { SupportLevel } from '../api/systemApi'

defineProps<{
  level: SupportLevel
}>()
</script>

<template>
  <span class="support-tag" :class="level.toLowerCase()">
    {{ level === 'STABLE' ? '稳定范围' : level === 'EXPERIMENTAL' ? '实验性' : '未启用' }}
  </span>
</template>

<style scoped>
.support-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 550;
  padding: 0 8px;
}

.stable {
  background: #edf7f1;
  color: #43836b;
}

.experimental {
  background: #faf4e8;
  color: #a18148;
}

.disabled {
  background: #e8eceb;
  color: #65716e;
}
</style>
