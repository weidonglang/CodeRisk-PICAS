<script setup lang="ts">
import { Refresh, Search, ArrowRight } from '@element-plus/icons-vue'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { listRecentTasks, type TaskSummary } from '../api/taskApi'
import TaskStatusBadge from '../components/TaskStatusBadge.vue'
import { dateTime, includesQuery, progress } from '../utils/presentation'

const loading = ref(false)
const error = ref('')
const tasks = ref<TaskSummary[]>([])
const query = ref('')
const state = ref('全部')
const options = ['全部', '运行中', '已完成', '需处理']
const visible = computed(() => tasks.value.filter(task =>
  includesQuery(query.value, task.taskName, task.id) &&
  (state.value === '全部' || (state.value === '运行中' && ['RUNNING', 'QUEUED'].includes(task.status)) ||
   (state.value === '已完成' && task.status === 'FINISHED') || (state.value === '需处理' && ['PENDING', 'FAILED', 'PARTIAL'].includes(task.status))),
))
let timer: ReturnType<typeof setTimeout> | undefined
let disposed = false
async function loadTasks() {
  if (loading.value || disposed) return
  clearTimeout(timer)
  loading.value = true
  error.value = ''
  try {
    const response = await listRecentTasks()
    if (!disposed) tasks.value = response.data
  } catch (err) {
    if (!disposed) error.value = err instanceof Error ? err.message : '无法加载任务'
  } finally {
    loading.value = false
    if (!disposed && tasks.value.some(task => ['RUNNING', 'QUEUED'].includes(task.status))) timer = setTimeout(loadTasks, 2000)
  }
}
onMounted(loadTasks)
onUnmounted(() => { disposed = true; clearTimeout(timer) })
</script>

<template>
  <section>
    <div class="page-header"><div><div class="eyebrow">DETECTION TASKS</div><h1>检测任务</h1><p>最近 {{ tasks.length }} 项任务</p></div><router-link to="/questions"><el-button type="primary">选择题目</el-button></router-link></div>
    <el-alert v-if="error" class="task-alert" type="error" :title="error" :closable="false" show-icon />
    <section class="panel">
      <div class="table-toolbar"><el-segmented v-model="state" :options="options" aria-label="任务状态筛选" /><div class="search-tools"><el-input v-model="query" :prefix-icon="Search" placeholder="搜索最近任务" aria-label="搜索最近任务" clearable /><el-tooltip content="刷新任务"><el-button :icon="Refresh" :loading="loading" @click="loadTasks" aria-label="刷新任务" /></el-tooltip></div></div>
      <el-table v-loading="loading && !tasks.length" :data="visible" empty-text="没有符合条件的任务" row-key="id">
        <el-table-column label="检测任务" min-width="220"><template #default="{ row }"><router-link :to="'/tasks/' + row.id + '/results'" class="text-link">{{ row.taskName }}</router-link><div class="row-sub">#{{ row.id }}</div></template></el-table-column>
        <el-table-column label="模式" min-width="150"><template #default="{ row }"><el-tag :type="row.taskMode === 'PICAS_CROSSLANG' ? 'warning' : 'info'" effect="plain">{{ row.taskMode === 'PICAS_STANDARD' ? 'PICAS 标准' : row.taskMode === 'PICAS_CROSSLANG' ? '跨语言 · 实验性' : row.taskMode }}</el-tag></template></el-table-column>
        <el-table-column label="状态" width="115"><template #default="{ row }"><TaskStatusBadge :status="row.status" /></template></el-table-column>
        <el-table-column label="成功代码对" min-width="160"><template #default="{ row }"><div class="progress-meta"><span>{{ row.finishedPairs }} / {{ row.totalPairs }}</span><span class="text-muted">{{ progress(row.finishedPairs, row.totalPairs) }}%</span></div><el-progress :percentage="progress(row.finishedPairs, row.totalPairs)" :show-text="false" :stroke-width="3" /></template></el-table-column>
        <el-table-column label="失败 / 未完成" width="115"><template #default="{ row }"><span :class="row.failedPairs ? 'has-failure' : 'text-muted'">{{ row.failedPairs }}</span></template></el-table-column>
        <el-table-column label="创建时间" min-width="115"><template #default="{ row }"><span class="data-mono text-muted">{{ dateTime(row.createdAt) }}</span></template></el-table-column>
        <el-table-column label="结果" width="95" fixed="right"><template #default="{ row }"><router-link :to="'/tasks/' + row.id + '/results'"><el-button link type="primary" :icon="ArrowRight">查看</el-button></router-link></template></el-table-column>
      </el-table>
      <div class="table-footer"><span>显示 {{ visible.length }} / {{ tasks.length }} 项最近任务</span><span v-if="tasks.some(task => ['RUNNING', 'QUEUED'].includes(task.status))" class="live-note">运行中 · 自动更新</span></div>
    </section>
  </section>
</template>

<style scoped>
.task-alert { margin-bottom: 18px; }
.search-tools { display: flex; gap: 10px; align-items: center; min-width: 0; }
.row-sub { color: #98a1ac; font-size: 10px; margin-top: 5px; }
.progress-meta { display: flex; justify-content: space-between; gap: 10px; font-size: 11px; margin-bottom: 8px; font-variant-numeric: tabular-nums; }
.has-failure { color: #bf6b3b; font-weight: 650; }
.live-note { color: #3e9781; }
@media (max-width: 680px) { .search-tools { width: 100%; } .search-tools .el-input { flex: 1; } }
</style>
