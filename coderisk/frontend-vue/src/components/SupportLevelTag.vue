<script setup lang="ts">
import type { SupportLevel } from '../api/systemApi'

defineProps<{
  level: SupportLevel
}>()
</script>

<template>
  <span class="support-tag" :class="level.toLowerCase()">
    {{ level }}
  </span>
</template>

<style scoped>
.support-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  padding: 0 8px;
}

.stable {
  background: #dff2e5;
  color: #156f3a;
}

.experimental {
  background: #fff1d7;
  color: #9a5a00;
}

.disabled {
  background: #e8eceb;
  color: #65716e;
}
</style>
