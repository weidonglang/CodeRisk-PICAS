<script setup lang="ts">
import { Refresh, CircleCheck, Warning } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { getLanguages, getTaskModes, type LanguageDescriptor, type TaskModeDescriptor } from '../api/systemApi'
import { useSystemStatus } from '../composables/useSystemStatus'
import SupportLevelTag from '../components/SupportLevelTag.vue'
import { dateTime } from '../utils/presentation'

const { health, checking, healthError, refreshHealth } = useSystemStatus()
const languages = ref<LanguageDescriptor[]>([])
const modes = ref<TaskModeDescriptor[]>([])
const error = ref('')
const loading = ref(false)
const origin = window.location.origin
async function load() {
  if (loading.value) return
  loading.value = true
  const [l, m] = await Promise.allSettled([getLanguages(), getTaskModes(), refreshHealth()])
  const failed = []
  if (l.status === 'fulfilled') languages.value = l.value.data; else failed.push('语言支持')
  if (m.status === 'fulfilled') modes.value = m.value.data; else failed.push('检测模式')
  error.value = failed.length ? failed.join('、') + '加载失败' : ''
  loading.value = false
}
onMounted(load)
</script>

<template>
  <section>
    <div class="page-header"><div><div class="eyebrow">RUNTIME</div><h1>运行状态</h1><p>服务连接与当前配置</p></div><el-button :icon="Refresh" :loading="loading || checking" @click="load">重新检查</el-button></div>
    <el-alert v-if="error || healthError" class="section-gap" type="error" :title="error || healthError" :closable="false" show-icon />
    <section class="panel section-gap">
      <div class="section-heading"><h2>服务连接</h2><span>{{ dateTime(health?.checkedAt) }}</span></div>
      <div class="service-row"><CircleCheck class="service-icon up" /><div><strong>前端工作区</strong><code>{{ origin }}</code></div><el-tag type="success">已加载</el-tag></div>
      <div class="service-row"><component :is="health?.status === 'UP' ? CircleCheck : Warning" class="service-icon" :class="{ up: health?.status === 'UP' }" /><div><strong>Spring Boot 后端</strong><code>{{ health?.service ?? '连接未确认' }} · {{ health?.appVersion ?? '-' }}</code></div><el-tag :type="health?.status === 'UP' ? 'success' : 'danger'">{{ health?.status === 'UP' ? '已连接' : '未连接' }}</el-tag></div>
      <div class="service-row"><span class="service-icon configured">P</span><div><strong>Python 分析服务</strong><code>{{ health?.analysisBaseUrl ?? '-' }}</code></div><el-tag type="info">配置地址 · 非探活</el-tag></div>
      <div class="config-foot">数据库类型与分析服务实时健康状态未由当前接口暴露。</div>
    </section>
    <section class="panel section-gap"><div class="section-heading"><h2>语言支持</h2><span>{{ languages.length }} 项配置</span></div>
      <el-table :data="languages" empty-text="语言配置未加载"><el-table-column prop="displayName" label="语言" min-width="180" /><el-table-column label="支持范围" min-width="150"><template #default="{ row }"><SupportLevelTag :level="row.supportLevel" /></template></el-table-column><el-table-column label="默认启用" width="120"><template #default="{ row }">{{ row.defaultEnabled ? '是' : '否' }}</template></el-table-column></el-table>
    </section>
    <section class="panel section-gap"><div class="section-heading"><h2>检测模式</h2><span>只读配置</span></div>
      <el-table :data="modes" empty-text="模式配置未加载"><el-table-column prop="name" label="模式" min-width="220" /><el-table-column prop="code" label="标识" min-width="210" /><el-table-column prop="version" label="版本" min-width="130" /><el-table-column label="状态" width="110"><template #default="{ row }"><el-tag :type="row.stable ? 'success' : 'warning'">{{ row.stable ? '稳定范围' : '实验性' }}</el-tag></template></el-table-column></el-table>
    </section>
  </section>
</template>

<style scoped>
.service-row { display: flex; gap: 14px; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--line); }
.service-icon { width: 22px; height: 22px; flex: 0 0 22px; color: #b18c64; }
.service-icon.up { color: #34937c; }
.service-row > div { flex: 1; min-width: 0; }
.service-row strong { font-size: 12px; font-weight: 550; display: block; }
.service-row code { display: block; font-size: 11px; color: var(--muted); margin-top: 8px; overflow-wrap: anywhere; }
.configured { display: grid; place-items: center; background: #f1f4f9; font-size: 12px; border-radius: 4px; color: #8796aa; }
.config-foot { color: var(--muted); font-size: 11px; margin-top: 18px; line-height: 1.7; }
@media (max-width: 480px) { .service-row { flex-wrap: wrap; } .service-row > .el-tag { margin-left: 36px; } }
</style>
