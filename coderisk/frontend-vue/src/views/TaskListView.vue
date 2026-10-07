<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listRecentTasks, type TaskSummary } from '../api/taskApi'

const loading = ref(false)
const error = ref('')
const tasks = ref<TaskSummary[]>([])

async function loadTasks() {
  loading.value = true
  error.value = ''
  try {
    const response = await listRecentTasks()
    tasks.value = response.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '无法加载任务'
  } finally {
    loading.value = false
  }
}

onMounted(loadTasks)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>任务</h1>
        <p>检测任务会从创建、排队、运行到完成持续更新状态。</p>
      </div>
    </div>
    <el-alert v-if="error" class="task-alert" type="error" :title="error" :closable="false" />
    <section class="panel">
      <h2>最近任务</h2>
      <el-table v-loading="loading" :data="tasks" empty-text="暂无任务">
        <el-table-column prop="taskName" label="任务" min-width="180" />
        <el-table-column label="模式" min-width="190">
          <template #default="{ row }">
            <el-tag :type="row.taskMode === 'PICAS_CROSSLANG' ? 'warning' : 'info'" effect="plain">
              {{ row.taskMode }}{{ row.taskMode === 'PICAS_CROSSLANG' ? ' · 实验性' : '' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="进度" width="120">
          <template #default="{ row }">{{ row.finishedPairs }} / {{ row.totalPairs }}</template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="190" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <router-link :to="`/tasks/${row.id}/results`">
              <el-button link type="primary">结果</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<style scoped>
.task-alert {
  margin-bottom: 16px;
}
</style>
