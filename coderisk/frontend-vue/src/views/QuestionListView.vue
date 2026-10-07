<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'

import { listQuestions, type Question } from '../api/questionApi'

const loading = ref(false)
const error = ref('')
const questions = ref<Question[]>([])
const total = ref(0)

async function loadQuestions() {
  loading.value = true
  error.value = ''
  try {
    const response = await listQuestions()
    questions.value = response.data.items
    total.value = response.data.total
  } catch (err) {
    error.value = err instanceof Error ? err.message : '无法加载题目'
  } finally {
    loading.value = false
  }
}

onMounted(loadQuestions)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>题目</h1>
        <p>题目画像会驱动动态阈值和自然相似风险校准。</p>
      </div>
      <router-link to="/questions/create">
        <el-button type="primary" :icon="Plus">新增</el-button>
      </router-link>
    </div>
    <el-alert v-if="error" class="list-alert" type="error" :title="error" :closable="false" />
    <section class="panel">
      <h2>题目列表</h2>
      <el-table v-loading="loading" :data="questions" empty-text="暂无题目">
        <el-table-column prop="title" label="题目" min-width="180" />
        <el-table-column prop="inputFormat" label="输入格式" min-width="180" show-overflow-tooltip />
        <el-table-column prop="outputFormat" label="输出格式" min-width="160" show-overflow-tooltip />
        <el-table-column prop="createdAt" label="创建时间" min-width="190" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <router-link :to="`/questions/${row.id}/submissions`">
              <el-button link type="primary">上传代码</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">共 {{ total }} 个题目</div>
    </section>
  </section>
</template>

<style scoped>
.list-alert {
  margin-bottom: 16px;
}

.table-footer {
  color: #63726e;
  font-size: 13px;
  margin-top: 12px;
}
</style>
