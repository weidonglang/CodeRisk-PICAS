<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { getDashboardSummary, type DashboardSummary } from '../api/dashboardApi'
import { getLanguages, getSystemHealth, type LanguageDescriptor, type SystemHealth } from '../api/systemApi'
import HealthBadge from '../components/HealthBadge.vue'
import SupportLevelTag from '../components/SupportLevelTag.vue'

const loading = ref(false)
const error = ref('')
const summary = ref<DashboardSummary | null>(null)
const health = ref<SystemHealth | null>(null)
const languages = ref<LanguageDescriptor[]>([])

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    const [summaryResponse, healthResponse, languageResponse] = await Promise.all([
      getDashboardSummary(),
      getSystemHealth(),
      getLanguages(),
    ])
    summary.value = summaryResponse.data
    health.value = healthResponse.data
    languages.value = languageResponse.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '无法连接后端服务'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>检测工作台</h1>
        <p>题目、任务、风险结果与实验入口集中在这里。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadDashboard">刷新</el-button>
    </div>

    <el-alert v-if="error" class="mb" type="error" :title="error" :closable="false" />

    <div class="metric-grid mb">
      <div class="metric-tile">
        <span>题目</span>
        <strong>{{ summary?.questionCount ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>提交</span>
        <strong>{{ summary?.submissionCount ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>任务</span>
        <strong>{{ summary?.taskCount ?? 0 }}</strong>
      </div>
      <div class="metric-tile">
        <span>高风险结果</span>
        <strong>{{ summary?.highRiskResultCount ?? 0 }}</strong>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="panel">
        <h2>服务状态</h2>
        <dl class="kv">
          <div>
            <dt>后端</dt>
            <dd><HealthBadge :status="health?.status ?? 'UNKNOWN'" /></dd>
          </div>
          <div>
            <dt>版本阶段</dt>
            <dd>{{ summary?.versionStage ?? 'V2 delivery + V3 minimal experiment' }}</dd>
          </div>
          <div>
            <dt>分析服务地址</dt>
            <dd>{{ health?.analysisBaseUrl ?? '-' }}</dd>
          </div>
          <div>
            <dt>数据说明</dt>
            <dd>{{ summary?.dataNotice ?? 'JDBC persistence and multi-dimensional analysis enabled' }}</dd>
          </div>
        </dl>
      </section>

      <section class="panel">
        <h2>语言支持</h2>
        <el-table :data="languages" height="228" empty-text="暂无数据">
          <el-table-column prop="displayName" label="语言" min-width="110" />
          <el-table-column label="支持级别" min-width="140">
            <template #default="{ row }">
              <SupportLevelTag :level="row.supportLevel" />
            </template>
          </el-table-column>
          <el-table-column label="默认启用" width="110">
            <template #default="{ row }">
              {{ row.defaultEnabled ? '是' : '否' }}
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </section>
</template>

<style scoped>
.mb {
  margin-bottom: 16px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 16px;
}

.kv {
  display: grid;
  gap: 14px;
  margin: 0;
}

.kv div {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 12px;
}

.kv dt {
  color: #63726e;
}

.kv dd {
  margin: 0;
  min-width: 0;
  overflow-wrap: anywhere;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
