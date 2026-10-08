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
  starterLanguage: 'java',
  starterCode: '',
  starterSource: '',
})

async function submit() {
  if (!form.title.trim()) {
    error.value = '题目标题不能为空'
    return
  }
  if (form.starterCode.trim() && !form.starterSource.trim()) {
    error.value = '登记共同模板时请填写来源依据'
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
      starterLanguage: form.starterLanguage,
      starterCode: form.starterCode,
      starterSource: form.starterSource,
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
        <p>题面与输入输出用于题目画像；共同模板用于解释自然相似。</p>
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
        <h2>共同模板（可选）</h2>
        <p>登记教师公开的框架或必需片段及来源，不要填完整参考答案。只标记精确匹配范围，原始相似分数仍保留。</p>
        <el-form-item label="模板语言">
          <el-select v-model="form.starterLanguage">
            <el-option v-for="language in ['java', 'python', 'c', 'html']" :key="language" :label="language" :value="language" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板来源依据">
          <el-input v-model="form.starterSource" :maxlength="2000" placeholder="课程公开框架地址、讲义版本或发布记录" />
        </el-form-item>
        <el-form-item label="共同模板源码">
          <el-input v-model="form.starterCode" type="textarea" :rows="6" :maxlength="20000" />
        </el-form-item>
        <p>有学生实现空位时，单独一行使用注释：Python 为 # CODERISK_STUDENT_CODE；Java/C 为 /* CODERISK_STUDENT_CODE */；HTML 为 &lt;!-- CODERISK_STUDENT_CODE --&gt;。短于 8 个 Token 的片段会忽略。</p>
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
