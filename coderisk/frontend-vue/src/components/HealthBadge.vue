<script setup lang="ts">
defineProps<{
  status: string
}>()
</script>

<template>
  <span class="health" :class="{ up: status === 'UP' }">
    {{ status }}
  </span>
</template>

<style scoped>
.health {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  border-radius: 999px;
  background: #f3e4e2;
  color: #a73f34;
  font-size: 13px;
  font-weight: 600;
  padding: 0 10px;
}

.health.up {
  background: #ddf3e7;
  color: #16724a;
}
</style>
