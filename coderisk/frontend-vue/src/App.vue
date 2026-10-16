<script setup lang="ts">
import { DataAnalysis, DataBoard, Files, HomeFilled, List, Setting, Plus, ArrowRight, Connection } from '@element-plus/icons-vue'
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStatus } from './composables/useSystemStatus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()
const { health, checking, healthError, refreshHealth } = useSystemStatus()
const navItems = [
  { path: '/dashboard', label: '工作台', icon: HomeFilled },
  { path: '/questions', label: '题目管理', icon: Files },
  { path: '/tasks', label: '检测任务', icon: List },
  { path: '/experiments', label: '研究实验', icon: DataAnalysis },
  { path: '/settings', label: '运行状态', icon: Setting },
]
const activePath = computed(() => String(route.meta.nav ?? route.path))
const section = computed(() => navItems.find(item => activePath.value.startsWith(item.path)))
let healthTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  void refreshHealth()
  healthTimer = setInterval(() => { if (!document.hidden) void refreshHealth() }, 30000)
})
onUnmounted(() => clearInterval(healthTimer))
</script>

<template>
  <el-config-provider :locale="zhCn">
    <div class="app-shell">
      <a class="skip-link" href="#main-content">跳到正文</a>
      <aside class="sidebar" aria-label="主导航">
        <router-link class="brand" to="/dashboard" aria-label="CodeRisk 工作台">
          <span class="brand-symbol"><DataBoard /></span>
          <span class="brand-name"><strong>CodeRisk<span class="brand-dot">.</span></strong><small>PICAS / 分析工作区</small></span>
        </router-link>
        <div class="nav-caption">工作空间</div>
        <nav>
          <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link"
            :class="{ active: activePath.startsWith(item.path) }" :aria-current="activePath.startsWith(item.path) ? 'page' : undefined">
            <component :is="item.icon" /><span>{{ item.label }}</span>
            <ArrowRight v-if="activePath.startsWith(item.path)" class="nav-arrow" />
          </router-link>
        </nav>
        <div class="sidebar-footer"><span class="workspace-mark">P</span><div><strong>PICAS Workspace</strong><span>相似风险 · 人工复核</span></div></div>
      </aside>
      <div class="main-column">
        <header class="topbar">
          <div class="breadcrumb"><span class="mobile-brand">CodeRisk</span><span class="desktop-label">工作空间</span><ArrowRight />
            <router-link v-if="section" :to="section.path">{{ section.label }}</router-link>
            <template v-if="route.meta.title && route.meta.title !== section?.label"><ArrowRight /><span>{{ route.meta.title }}</span></template>
          </div>
          <div class="topbar-actions">
            <el-tooltip :content="healthError || (health ? '后端 ' + health.appVersion + ' · ' + health.service : '检查后端连接')">
              <button class="connection-status" :class="{ online: health?.status === 'UP' }" :disabled="checking" @click="refreshHealth" aria-label="重新检查后端连接">
                <span class="status-dot" /><span>{{ checking ? '连接中' : health?.status === 'UP' ? '后端已连接' : '后端未连接' }}</span>
              </button>
            </el-tooltip>
            <router-link to="/questions/create" class="top-create"><el-button :icon="Plus" type="primary">新建题目</el-button></router-link>
          </div>
        </header>
        <main id="main-content" class="main-surface" tabindex="-1"><router-view /></main>
        <footer class="page-footer"><span class="project-credit">© 2026 魏语石 · CodeRisk / PICAS</span><span>相似信号不等于来源关系，风险结果仅供人工复核。</span><Connection /></footer>
      </div>
    </div>
  </el-config-provider>
</template>

<style scoped>
.app-shell { display: grid; grid-template-columns: 216px minmax(0, 1fr); min-height: 100vh; }
.sidebar { position: sticky; top: 0; height: 100vh; padding: 28px 16px 18px; background: #fff; border-right: 1px solid var(--line); display: flex; flex-direction: column; }
.brand { display: flex; gap: 10px; align-items: center; padding: 0 10px; text-decoration: none; color: var(--ink); }
.brand-symbol { display: grid; place-items: center; width: 34px; height: 38px; color: #087f74; }
.brand-symbol svg { width: 32px; height: 32px; }
.brand-name strong { display: block; font-size: 22px; font-weight: 750; }
.brand-dot { color: #087f74; }
.brand-name small { display: block; font-size: 10px; color: var(--muted); margin-top: 4px; }
.nav-caption { margin: 38px 12px 12px; color: #929aa5; font-size: 11px; }
nav { display: grid; gap: 6px; }
.nav-link { position: relative; display: flex; align-items: center; gap: 12px; min-height: 43px; padding: 0 13px; color: #647080; font-size: 13px; text-decoration: none; border-radius: 5px; }
.nav-link svg { width: 18px; height: 18px; flex: 0 0 auto; }
.nav-link:hover { background: #f5f7fa; color: var(--ink); }
.nav-link.active { background: #eaf6f2; color: #087568; font-weight: 650; }
.nav-link.active::before { content: ''; position: absolute; left: -16px; height: 22px; width: 3px; background: #087f74; }
.nav-link .nav-arrow { width: 12px; margin-left: auto; }
.sidebar-footer { margin-top: auto; border-top: 1px solid var(--line); padding: 20px 6px 0; display: flex; align-items: center; gap: 10px; }
.workspace-mark { background: #eff2f7; color: #53617a; border: 1px solid #e2e7ee; width: 30px; height: 32px; display: grid; place-items: center; border-radius: 4px; font-size: 13px; font-weight: 700; }
.sidebar-footer strong { display: block; font-size: 11px; color: #4f5968; }
.sidebar-footer div span { font-size: 10px; display: block; color: var(--muted); margin-top: 5px; }
.main-column { min-width: 0; display: flex; flex-direction: column; }
.topbar { height: 68px; flex: 0 0 auto; padding: 0 32px; display: flex; align-items: center; justify-content: space-between; gap: 16px; background: #fff; border-bottom: 1px solid var(--line); }
.breadcrumb { min-width: 0; display: flex; align-items: center; gap: 10px; color: #87909d; font-size: 12px; }
.breadcrumb a { color: #677180; text-decoration: none; }
.breadcrumb svg { width: 10px; flex: 0 0 10px; }
.breadcrumb > span:last-child { color: #344050; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mobile-brand { display: none; }
.topbar-actions { display: flex; align-items: center; gap: 22px; flex: 0 0 auto; }
.connection-status { display: flex; align-items: center; gap: 7px; border: 0; background: none; color: #8a5661; font-size: 11px; padding: 8px 0; cursor: pointer; }
.connection-status.online { color: #587069; }
.status-dot { width: 6px; height: 6px; flex: 0 0 6px; border-radius: 50%; background: #be6471; }
.online .status-dot { background: #159578; }
.main-surface { width: 100%; max-width: 1640px; margin: 0 auto; padding: 32px; flex: 1; outline: none; min-width: 0; }
.page-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 20px 32px; font-size: 10px; color: #929aa5; }
.page-footer svg { width: 14px; height: 14px; }
.skip-link { position: fixed; top: -80px; left: 12px; z-index: 3000; padding: 12px; background: white; }
.skip-link:focus { top: 12px; }
@media (max-width: 1100px) {
  .app-shell { grid-template-columns: 184px minmax(0, 1fr); }
  .topbar { padding: 0 22px; }
  .main-surface { padding: 24px 22px; }
  .brand { padding: 0 4px; }
  .brand-name strong { font-size: 20px; }
}
@media (max-width: 760px) {
  .app-shell { display: block; padding-bottom: calc(70px + env(safe-area-inset-bottom)); }
  .sidebar { position: fixed; inset: auto 0 0; height: auto; width: 100%; padding: 6px 6px calc(6px + env(safe-area-inset-bottom)); border: 0; border-top: 1px solid var(--line); z-index: 100; }
  .brand, .nav-caption, .sidebar-footer, .nav-arrow, .desktop-label, .top-create { display: none !important; }
  nav { grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 2px; }
  .nav-link { flex-direction: column; min-height: 52px; gap: 5px; justify-content: center; padding: 5px 0; font-size: 10px; }
  .nav-link.active::before { display: none; }
  .topbar { padding: 0 16px; height: 56px; }
  .mobile-brand { display: inline; font-weight: 700; color: var(--ink); }
  .breadcrumb { gap: 6px; font-size: 11px; }
  .topbar-actions { gap: 0; }
  .connection-status { font-size: 10px; }
  .main-surface { padding: 22px 16px; }
  .page-footer { padding: 12px 16px; align-items: flex-start; flex-wrap: wrap; gap: 9px; }
  .page-footer .project-credit { flex-basis: 100%; }
  .page-footer svg { display: none; }
}
</style>
