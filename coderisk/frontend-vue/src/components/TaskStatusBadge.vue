<script setup lang="ts">
import { taskMeta } from '../utils/presentation'
defineProps<{ status: string }>()
</script>

<template>
  <el-tag :type="taskMeta(status).tone" effect="light" :class="{ 'is-running': status === 'RUNNING' }">
    {{ taskMeta(status).label }}
  </el-tag>
</template>
