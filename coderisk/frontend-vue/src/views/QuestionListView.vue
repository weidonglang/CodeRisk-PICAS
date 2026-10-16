<script setup lang="ts">
import { Plus, Search, Refresh, Upload } from '@element-plus/icons-vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { listQuestions, type Question } from '../api/questionApi'
import { dateTime, includesQuery } from '../utils/presentation'

const loading = ref(false)
const error = ref('')
const questions = ref<Question[]>([])
const total = ref<number | null>(null)
const currentPage = ref(1)
const query = ref('')
let requestVersion = 0
const filtered = computed(() => questions.value.filter(item => includesQuery(query.value, item.title, item.id)))
async function loadQuestions() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  try {
    const response = await listQuestions(currentPage.value, 20)
    if (version !== requestVersion) return
    questions.value = response.data.items
    total.value = response.data.total
  } catch (err) {
    if (version === requestVersion) error.value = err instanceof Error ? err.message : '无法加载题目'
  } finally { if (version === requestVersion) loading.value = false }
}
watch(currentPage, () => { query.value = ''; void loadQuestions() })
onMounted(loadQuestions)
onUnmounted(() => { requestVersion++ })
</script>

<template>
  <section>
    <div class="page-header">
      <div><div class="eyebrow">QUESTION LIBRARY</div><h1>题目管理</h1><p>题目库 · {{ total ?? '-' }} 个题目</p></div>
      <router-link to="/questions/create"><el-button type="primary" :icon="Plus">新建题目</el-button></router-link>
    </div>
    <el-alert v-if="error" class="list-alert" type="error" :title="error" :closable="false" show-icon />
    <section class="panel">
      <div class="table-toolbar">
        <el-input v-model="query" :prefix-icon="Search" placeholder="本页搜索题目名称或 ID" aria-label="本页搜索题目" clearable />
        <el-tooltip content="刷新题目"><el-button :icon="Refresh" :loading="loading" @click="loadQuestions" aria-label="刷新题目" /></el-tooltip>
      </div>
      <el-table v-loading="loading" :data="filtered" :empty-text="query ? '本页没有匹配的题目' : '暂无题目'" row-key="id">
        <el-table-column label="题目" min-width="230"><template #default="{ row }"><router-link :to="'/questions/' + row.id + '/submissions'" class="text-link">{{ row.title }}</router-link><div class="question-id">#{{ row.id }}</div></template></el-table-column>
        <el-table-column prop="inputFormat" label="输入格式" min-width="180" show-overflow-tooltip />
        <el-table-column prop="outputFormat" label="输出格式" min-width="160" show-overflow-tooltip />
        <el-table-column label="共同模板" width="110"><template #default="{ row }"><el-tag v-if="row.starterCode" type="info">已登记</el-tag><span v-else class="text-muted">未登记</span></template></el-table-column>
        <el-table-column label="创建时间" min-width="120"><template #default="{ row }"><span class="data-mono text-muted">{{ dateTime(row.createdAt) }}</span></template></el-table-column>
        <el-table-column label="操作" width="120" fixed="right"><template #default="{ row }"><router-link :to="'/questions/' + row.id + '/submissions'"><el-button link type="primary" :icon="Upload">代码提交</el-button></router-link></template></el-table-column>
      </el-table>
      <div class="table-footer"><span>本页 {{ filtered.length }} 个 / 全部 {{ total ?? '-' }} 个</span><el-pagination v-model:current-page="currentPage" :page-size="20" :total="total ?? 0" layout="prev, pager, next" /></div>
    </section>
  </section>
</template>

<style scoped>
.list-alert { margin-bottom: 18px; }
.question-id { font-size: 10px; color: #98a1ac; margin-top: 5px; }
</style>
