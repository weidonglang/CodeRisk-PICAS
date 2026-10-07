import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/questions', component: () => import('../views/QuestionListView.vue') },
  { path: '/questions/create', component: () => import('../views/QuestionCreateView.vue') },
  { path: '/questions/:questionId/submissions', component: () => import('../views/SubmissionUploadView.vue') },
  { path: '/tasks', component: () => import('../views/TaskListView.vue') },
  { path: '/tasks/:taskId/results', component: () => import('../views/TaskResultView.vue') },
  { path: '/results/:resultId', component: () => import('../views/ResultDetailView.vue') },
  { path: '/experiments', component: () => import('../views/ExperimentView.vue') },
  { path: '/settings', component: () => import('../views/SettingsView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
