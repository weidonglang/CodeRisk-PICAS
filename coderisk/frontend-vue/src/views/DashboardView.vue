<script setup lang="ts">
import { ArrowRight, Plus, Refresh, Files, List, Upload, Warning } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { getDashboardSummary, type DashboardSummary } from '../api/dashboardApi'
import { listQuestions, type Question } from '../api/questionApi'
import { listRecentTasks, type TaskSummary } from '../api/taskApi'
import { getLanguages, type LanguageDescriptor } from '../api/systemApi'
import TaskStatusBadge from '../components/TaskStatusBadge.vue'
import SupportLevelTag from '../components/SupportLevelTag.vue'
import { useSystemStatus } from '../composables/useSystemStatus'
import { dateTime, progress } from '../utils/presentation'

const { health, refreshHealth } = useSystemStatus()
const loading = ref(false)
const error = ref('')
const summary = ref<DashboardSummary | null>(null)
const tasks = ref<TaskSummary[]>([])
const questions = ref<Question[]>([])
const languages = ref<LanguageDescriptor[]>([])
const activeCount = computed(() => tasks.value.filter(task => ['QUEUED', 'RUNNING'].includes(task.status)).length)
const today = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }).format(new Date())
async function loadDashboard() {
  if (loading.value) return
  loading.value = true
  const responses = await Promise.allSettled([getDashboardSummary(), listRecentTasks(), listQuestions(1, 4), getLanguages(), refreshHealth()])
  const failures: string[] = []
  const [s, t, q, l] = responses
  if (s.status === 'fulfilled') summary.value = s.value.data; else failures.push('概览')
  if (t.status === 'fulfilled') tasks.value = t.value.data; else failures.push('最近任务')
  if (q.status === 'fulfilled') questions.value = q.value.data.items; else failures.push('题目')
  if (l.status === 'fulfilled') languages.value = l.value.data; else failures.push('语言')
  error.value = failures.length ? failures.join('、') + '加载失败' : ''
  loading.value = false
}
onMounted(loadDashboard)
</script>

<template>
  <section>
    <div class="page-header">
      <div><div class="eyebrow">OVERVIEW</div><h1>检测工作台</h1><p>{{ today }}</p></div>
      <div class="header-actions">
        <el-tooltip content="刷新工作台"><el-button :icon="Refresh" :loading="loading" aria-label="刷新工作台" @click="loadDashboard" /></el-tooltip>
        <router-link to="/questions"><el-button :icon="Upload">提交代码</el-button></router-link>
      </div>
    </div>
    <el-alert v-if="error" class="mb" type="error" :title="error" :closable="false" show-icon />
    <div class="metric-grid mb" v-loading="loading && !summary">
      <div class="metric-tile"><span>题目总数 <Files class="stat-icon blue" /></span><strong>{{ summary?.questionCount ?? '-' }}</strong><small>题目库</small></div>
      <div class="metric-tile"><span>代码提交 <Upload class="stat-icon teal" /></span><strong>{{ summary?.submissionCount ?? '-' }}</strong><small>已接收源码</small></div>
      <div class="metric-tile"><span>检测任务 <List class="stat-icon violet" /></span><strong>{{ summary?.taskCount ?? '-' }}</strong><small>{{ activeCount }} 项最近任务运行中</small></div>
      <div class="metric-tile"><span>高风险代码对 <Warning class="stat-icon amber" /></span><strong>{{ summary?.highRiskResultCount ?? '-' }}</strong><small>待结合证据人工复核</small></div>
    </div>
    <div class="dashboard-grid">
      <div class="work-column">
        <section class="panel">
          <div class="section-heading"><h2>最近检测任务 <span v-if="activeCount" class="live-label">{{ activeCount }} 项运行中</span></h2><router-link to="/tasks" class="section-link">全部任务 <ArrowRight /></router-link></div>
          <el-table v-if="tasks.length || loading" :data="tasks.slice(0, 6)" v-loading="loading" empty-text="暂无任务">
            <el-table-column label="任务" min-width="195"><template #default="{ row }"><router-link :to="'/tasks/' + row.id + '/results'" class="text-link">{{ row.taskName }}</router-link><div class="row-sub">#{{ row.id }} · {{ row.taskMode === 'PICAS_CROSSLANG' ? '跨语言 · 实验性' : row.taskMode }}</div></template></el-table-column>
            <el-table-column label="状态" width="100"><template #default="{ row }"><TaskStatusBadge :status="row.status" /></template></el-table-column>
            <el-table-column label="成功代码对" min-width="130"><template #default="{ row }"><div class="progress-meta">{{ row.finishedPairs }} <span>/ {{ row.totalPairs }}</span></div><el-progress :percentage="progress(row.finishedPairs, row.totalPairs)" :stroke-width="3" :show-text="false" /></template></el-table-column>
            <el-table-column label="创建时间" min-width="110"><template #default="{ row }"><span class="data-mono text-muted">{{ dateTime(row.createdAt) }}</span></template></el-table-column>
          </el-table>
          <el-empty v-else :image-size="76" description="暂无检测任务"><router-link to="/questions"><el-button type="primary" :icon="Plus">选择题目</el-button></router-link></el-empty>
        </section>
        <section class="panel section-gap">
          <div class="section-heading"><h2>最近题目</h2><router-link to="/questions" class="section-link">题目库 <ArrowRight /></router-link></div>
          <div v-if="questions.length" class="question-rows">
            <router-link v-for="question in questions" :key="question.id" :to="'/questions/' + question.id + '/submissions'" class="question-row">
              <span class="question-icon"><Files /></span><span class="question-info"><strong>{{ question.title }}</strong><small>#{{ question.id }} · {{ dateTime(question.createdAt) }}</small></span><span class="question-action">代码提交 <ArrowRight /></span>
            </router-link>
          </div>
          <el-empty v-else :image-size="64" description="题目库为空"><router-link to="/questions/create"><el-button :icon="Plus">新建题目</el-button></router-link></el-empty>
        </section>
      </div>
      <aside class="context-column">
        <section class="panel">
          <div class="section-heading"><h2>运行概况</h2><span class="service-pill" :class="{ up: health?.status === 'UP' }">{{ health?.status === 'UP' ? '已连接' : '未连接' }}</span></div>
          <dl class="runtime-list">
            <div><dt>后端版本</dt><dd>{{ health?.appVersion ?? '-' }}</dd></div>
            <div><dt>默认检测模式</dt><dd>PICAS Standard</dd></div>
            <div><dt>分析服务配置</dt><dd class="data-mono">{{ health?.analysisBaseUrl ?? '-' }}</dd></div>
            <div><dt>最近健康检查</dt><dd class="data-mono">{{ dateTime(health?.checkedAt) }}</dd></div>
          </dl>
          <router-link to="/settings" class="section-link status-link">运行状态 <ArrowRight /></router-link>
        </section>
        <section class="panel section-gap">
          <div class="section-heading"><h2>语言范围</h2><span>{{ languages.length }} 项</span></div>
          <div v-for="language in languages" :key="language.language" class="language-row"><span>{{ language.displayName }}</span><SupportLevelTag :level="language.supportLevel" /></div>
          <el-empty v-if="!languages.length" :image-size="44" description="语言数据未加载" />
        </section>
        <div class="review-note"><Warning /><div><strong>人工复核边界</strong><p>高相似分不证明派生关系，低分或解析失败也不证明独立创作。</p></div></div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.mb { margin-bottom: 24px; }
.stat-icon { width: 16px; height: 16px; float: right; }
.blue { color: #5085c8; } .teal { color: #149983; } .violet { color: #8e7bb0; } .amber { color: #cd9942; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1fr) 285px; gap: 24px; align-items: start; }
.work-column, .context-column { min-width: 0; }
.section-link { color: #8a95a2; font-size: 11px; display: inline-flex; align-items: center; gap: 6px; text-decoration: none; white-space: nowrap; }
.section-link:hover { color: var(--el-color-primary); }
.section-link svg { width: 11px; }
.live-label { color: #469480; font-size: 10px; font-weight: 400; margin-left: 8px; }
.row-sub { color: #98a1ac; font-size: 10px; margin-top: 4px; }
.progress-meta { font-size: 11px; font-variant-numeric: tabular-nums; margin-bottom: 7px; }
.progress-meta span { color: #a0a8b1; }
.question-row { padding: 15px 0; display: flex; gap: 12px; align-items: center; border-bottom: 1px solid #f0f2f6; text-decoration: none; color: var(--ink); }
.question-row:last-child { border: 0; padding-bottom: 0; }
.question-row:first-child { padding-top: 0; }
.question-icon { width: 32px; height: 34px; flex: 0 0 32px; background: #f1f5fa; color: #7d96b5; border-radius: 4px; display: grid; place-items: center; }
.question-icon svg { width: 16px; }
.question-info { min-width: 0; flex: 1; }
.question-info strong { font-size: 12px; font-weight: 550; display: block; overflow-wrap: anywhere; }
.question-info small { color: #98a1ac; font-size: 10px; margin-top: 5px; display: block; }
.question-action { color: #8d98a4; font-size: 10px; display: flex; gap: 6px; white-space: nowrap; }
.question-action svg { width: 11px; }
.runtime-list { margin: 0; }
.runtime-list div { margin-top: 18px; }
.runtime-list dt { color: #97a0ac; font-size: 10px; margin-bottom: 7px; }
.runtime-list dd { margin: 0; color: #596575; font-size: 11px; overflow-wrap: anywhere; }
.service-pill { color: #ae6767; background: #faf1f1; padding: 4px 7px; border-radius: 3px; font-size: 10px; }
.service-pill.up { color: #469480; background: #edf7f1; }
.status-link { margin-top: 22px; border-top: 1px solid var(--line); padding-top: 16px; width: 100%; justify-content: space-between; }
.language-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 0; border-bottom: 1px solid #f0f2f6; font-size: 11px; }
.language-row:last-child { border: 0; padding-bottom: 0; }
.review-note { display: flex; align-items: flex-start; gap: 9px; margin-top: 22px; padding: 0 6px; color: #8a94a1; }
.review-note > svg { flex: 0 0 14px; width: 14px; height: 14px; color: #bba276; }
.review-note strong { font-size: 11px; font-weight: 500; }
.review-note p { margin: 7px 0 0; font-size: 10px; line-height: 1.9; }
@media (max-width: 1180px) { .dashboard-grid { grid-template-columns: minmax(0, 1fr) 245px; gap: 18px; } }
@media (max-width: 1000px) { .dashboard-grid { grid-template-columns: 1fr; } .context-column { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; } .context-column .section-gap { margin-top: 0; } .review-note { grid-column: 1 / -1; } }
@media (max-width: 560px) { .context-column { display: block; } .context-column .section-gap { margin-top: 18px; } .question-action { font-size: 0; } }
</style>
