import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '工作台', nav: '/dashboard' } },
  { path: '/questions', component: () => import('../views/QuestionListView.vue'), meta: { title: '题目管理', nav: '/questions' } },
  { path: '/questions/create', component: () => import('../views/QuestionCreateView.vue'), meta: { title: '新建题目', nav: '/questions' } },
  { path: '/questions/:questionId/submissions', component: () => import('../views/SubmissionUploadView.vue'), meta: { title: '代码提交', nav: '/questions' } },
  { path: '/tasks', component: () => import('../views/TaskListView.vue'), meta: { title: '检测任务', nav: '/tasks' } },
  { path: '/tasks/:taskId/results', component: () => import('../views/TaskResultView.vue'), meta: { title: '检测结果', nav: '/tasks' } },
  { path: '/results/:resultId', component: () => import('../views/ResultDetailView.vue'), meta: { title: '结果证据', nav: '/tasks' } },
  { path: '/experiments', component: () => import('../views/ExperimentView.vue'), meta: { title: '研究实验', nav: '/experiments' } },
  { path: '/settings', component: () => import('../views/SettingsView.vue'), meta: { title: '运行状态', nav: '/settings' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return to.path === from.path ? false : { top: 0 }
  },
})

router.afterEach(to => { document.title = `${String(to.meta.title ?? '工作空间')} · CodeRisk / PICAS` })

export default router
