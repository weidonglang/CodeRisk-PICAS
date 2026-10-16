<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ArrowLeft, Check } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { createQuestion } from '../api/questionApi'

const router = useRouter()
const saving = ref(false)
const error = ref('')
const expanded = ref<string[]>([])
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
  if (saving.value) return
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
        <div class="eyebrow">NEW QUESTION</div><h1>新建题目</h1>
        <p>题目管理 / 基础资料</p>
      </div>
      <el-button :icon="ArrowLeft" @click="router.push('/questions')">返回题目库</el-button>
    </div>
    <el-alert v-if="error" class="form-alert" type="error" :title="error" :closable="false" />
    <section class="panel">
      <h2>题目信息</h2>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="题目标题" required>
          <el-input v-model="form.title" placeholder="例如：数组求和" :maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="5" :maxlength="20000" />
        </el-form-item>
        <div class="io-fields"><el-form-item label="输入格式">
          <el-input v-model="form.inputFormat" type="textarea" :rows="3" :maxlength="8000" />
        </el-form-item>
        <el-form-item label="输出格式">
          <el-input v-model="form.outputFormat" type="textarea" :rows="3" :maxlength="8000" />
        </el-form-item>
        </div>
        <el-form-item label="约束条件">
          <el-input v-model="form.constraintsText" type="textarea" :rows="3" :maxlength="8000" />
        </el-form-item>
        <el-collapse v-model="expanded" class="template-collapse"><el-collapse-item title="共同模板 · 可选登记" name="template">
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
        </el-collapse-item></el-collapse>
        <div class="form-actions"><el-button :icon="Check" type="primary" :loading="saving" @click="submit">保存题目</el-button><el-button @click="router.push('/questions')">取消</el-button></div>
      </el-form>
    </section>
  </section>
</template>

<style scoped>
.form-alert {
  margin-bottom: 16px;
}
.template-collapse { margin: 12px 0 24px; border: 0; }
.template-collapse :deep(.el-collapse-item__header) { color: var(--ink); font-weight: 550; }
.template-collapse p { color: var(--muted); font-size: 11px; line-height: 1.8; }
.form-actions { display: flex; gap: 8px; padding-top: 8px; }
.form-actions .el-button + .el-button { margin-left: 0; }
.panel { max-width: 1050px; }
.io-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
@media (max-width: 680px) { .io-fields { grid-template-columns: 1fr; gap: 0; } }
</style>
