<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createQuestion } from '../api/questionApi'

const router = useRouter()
const saving = ref(false)
const error = ref('')
const form = reactive({
  title: '',
  description: '',
  inputFormat: '',
  outputFormat: '',
  constraintsText: '',
})

async function submit() {
  if (!form.title.trim()) {
    error.value = '题目标题不能为空'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await createQuestion({
      title: form.title,
      description: form.description,
      inputFormat: form.inputFormat,
      outputFormat: form.outputFormat,
      constraintsText: form.constraintsText,
    })
    await router.push('/questions')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>新增题目</h1>
        <p>题面、输入输出和参考答案会用于后续题目画像。</p>
      </div>
    </div>
    <el-alert v-if="error" class="form-alert" type="error" :title="error" :closable="false" />
    <section class="panel">
      <h2>题目信息</h2>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="题目标题">
          <el-input v-model="form.title" placeholder="例如：Array Sum" />
        </el-form-item>
        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="输入格式">
          <el-input v-model="form.inputFormat" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="输出格式">
          <el-input v-model="form.outputFormat" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="约束条件">
          <el-input v-model="form.constraintsText" type="textarea" :rows="3" />
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="submit">保存题目</el-button>
      </el-form>
    </section>
  </section>
</template>

<style scoped>
.form-alert {
  margin-bottom: 16px;
}
</style>
