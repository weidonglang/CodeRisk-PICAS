<script setup lang="ts">
import { riskMeta } from '../utils/presentation'
defineProps<{ level: string }>()
</script>

<template>
  <el-tag :type="riskMeta(level).tone" effect="light" class="risk-badge">{{ riskMeta(level).label }}</el-tag>
</template>
