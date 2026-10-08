<script setup lang="ts">
import { UploadFilled, VideoPlay } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getQuestion, type Question } from '../api/questionApi'
import { listSubmissions, uploadSubmission, type Submission } from '../api/submissionApi'
import { getTaskModes, type TaskModeDescriptor } from '../api/systemApi'
import { createTask, startTask, type TaskMode } from '../api/taskApi'
import SupportLevelTag from '../components/SupportLevelTag.vue'

const route = useRoute()
const router = useRouter()
const questionId = computed(() => Number(route.params.questionId))
const question = ref<Question | null>(null)
const submissions = ref<Submission[]>([])
const taskModes = ref<TaskModeDescriptor[]>([])
const selectedTaskMode = ref<TaskMode>('PICAS_STANDARD')
const studentId = ref('')
const languageVersion = ref('')
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const uploading = ref(false)
const starting = ref(false)
const error = ref('')

const crossLanguageReady = computed(() => {
  if (submissions.value.length !== 2) return false
  const languages = new Set(submissions.value.map((item) => item.language.toLowerCase()))
  return languages.has('java') && languages.has('python')
})
const mixedNewLanguages = computed(() => {
  const languages = new Set(submissions.value.map((item) => item.language.toLowerCase()))
  return languages.size > 1 && (languages.has('c') || languages.has('html'))
})
const selectableTaskModes = computed(() => taskModes.value.filter((mode) =>
  mode.code === 'PICAS_STANDARD' || mode.code === 'PICAS_CROSSLANG',
))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [questionResponse, submissionsResponse, taskModeResponse] = await Promise.all([
      getQuestion(questionId.value),
      listSubmissions(questionId.value),
      getTaskModes(),
    ])
    question.value = questionResponse.data
    submissions.value = submissionsResponse.data
    taskModes.value = taskModeResponse.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function submitUpload() {
  if (!selectedFile.value) {
    error.value = '请选择代码文件'
    return
  }
  uploading.value = true
  error.value = ''
  try {
    await uploadSubmission(questionId.value, studentId.value, selectedFile.value, languageVersion.value)
    studentId.value = ''
    languageVersion.value = ''
    selectedFile.value = null
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '上传失败'
  } finally {
    uploading.value = false
  }
}

async function createAndStartTask() {
  if (submissions.value.length < 2) {
    error.value = '至少需要两份提交才能创建检测任务'
    return
  }
  if (selectedTaskMode.value === 'PICAS_CROSSLANG' && !crossLanguageReady.value) {
    error.value = '实验性跨语言 IR 目前要求恰好一份 Java 与一份 Python 提交'
    return
  }
  starting.value = true
  error.value = ''
  try {
    const taskResponse = await createTask({
      questionId: questionId.value,
      taskName: `${question.value?.title ?? 'Question'} ${selectedTaskMode.value}`,
      submissionIds: submissions.value.map((item) => item.id),
      taskMode: selectedTaskMode.value,
    })
    const started = await startTask(taskResponse.data.id)
    await router.push(`/tasks/${started.data.id}/results`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '任务启动失败'
  } finally {
    starting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="page-header">
      <div>
        <h1>{{ question?.title ?? '代码上传' }}</h1>
        <p>支持 Java、Python、C 和 HTML。C、HTML 请分别建立同语言题目与任务。</p>
      </div>
      <el-button :icon="VideoPlay" :loading="starting" :disabled="submissions.length < 2 || mixedNewLanguages || (selectedTaskMode === 'PICAS_CROSSLANG' && !crossLanguageReady)" type="primary" @click="createAndStartTask">
        创建并启动
      </el-button>
    </div>

    <el-alert v-if="error" class="section-gap" type="error" :title="error" :closable="false" />
    <el-alert v-if="mixedNewLanguages" class="section-gap" type="warning" title="请将 C、HTML 与其他语言分开建立检测任务" :closable="false" />
    <el-alert class="section-gap" type="info" title="C 与 HTML 为实验性支持" description="C 支持语法结构和有限作用域规范化；HTML 比较标签、属性和文本，使用待验证的固定阈值，脚本与样式按原文比较。相似页面模板需要人工复核。" :closable="false" />

    <div class="upload-grid">
      <section class="panel">
        <h2>上传提交</h2>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="学生标识">
            <el-input v-model="studentId" placeholder="例如：20260001" />
          </el-form-item>
          <el-form-item label="代码文件">
            <div class="file-row">
              <input type="file" accept=".java,.py,.c,.cpp,.html,.htm" @change="onFileChange" />
              <span>{{ selectedFile?.name ?? '未选择文件' }}</span>
            </div>
          </el-form-item>
          <el-form-item label="语言版本（可选）">
            <el-input v-model="languageVersion" :maxlength="64" placeholder="例如 Python 2.7、Python 3.12、Java 17、C11；未知请留空" />
          </el-form-item>
          <p>版本为提交者声明；解析通过不代表编译器验证或跨版本语义一致。</p>
          <el-button :icon="UploadFilled" type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
        </el-form>
      </section>

      <section class="panel">
        <h2>检测配置</h2>
        <el-form label-position="top">
          <el-form-item label="检测模式">
            <el-select v-model="selectedTaskMode" class="mode-select">
              <el-option
                v-for="mode in selectableTaskModes"
                :key="mode.code"
                :value="mode.code"
                :label="`${mode.name} · ${mode.version}${mode.stable ? '' : ' · 实验性'}`"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <el-alert
          v-if="selectedTaskMode === 'PICAS_CROSSLANG'"
          type="warning"
          title="实验性 normalized IR 与轻量结构摘要"
          description="仅支持一份 Java 与一份 Python 的有限结构；IR、控制摘要和数据摘要权重均为 0，不进入标准生产评分，也不构建完整 CFG/DFG。"
          :closable="false"
          show-icon
        />
        <h2 class="question-heading">题目信息</h2>
        <dl class="kv">
          <div>
            <dt>题目 ID</dt>
            <dd>{{ questionId }}</dd>
          </div>
          <div>
            <dt>输入格式</dt>
            <dd>{{ question?.inputFormat || '-' }}</dd>
          </div>
          <div>
            <dt>输出格式</dt>
            <dd>{{ question?.outputFormat || '-' }}</dd>
          </div>
        </dl>
      </section>
    </div>

    <section class="panel section-gap">
      <h2>已上传提交</h2>
      <el-table v-loading="loading" :data="submissions" empty-text="暂无提交">
        <el-table-column prop="studentId" label="学生标识" min-width="130" />
        <el-table-column prop="fileName" label="文件名" min-width="170" />
        <el-table-column prop="language" label="语言" width="100" />
        <el-table-column label="声明版本" min-width="130">
          <template #default="{ row }">{{ row.languageVersion || '未知' }}</template>
        </el-table-column>
        <el-table-column label="支持级别" width="140">
          <template #default="{ row }">
            <SupportLevelTag :level="row.supportLevel" />
          </template>
        </el-table-column>
        <el-table-column prop="parserStatus" label="解析状态" width="140" />
        <el-table-column prop="rawCodePath" label="保存路径" min-width="260" show-overflow-tooltip />
      </el-table>
    </section>
  </section>
</template>

<style scoped>
.section-gap {
  margin-top: 16px;
}

.mode-select {
  width: 100%;
}

.question-heading {
  margin-top: 20px;
}

.upload-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 0.8fr);
  gap: 16px;
}

.file-row {
  display: grid;
  grid-template-columns: minmax(180px, max-content) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  width: 100%;
}

.file-row span {
  color: #63726e;
  overflow-wrap: anywhere;
}

.kv {
  display: grid;
  gap: 12px;
  margin: 0;
}

.kv div {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  gap: 12px;
}

.kv dt {
  color: #63726e;
}

.kv dd {
  margin: 0;
  overflow-wrap: anywhere;
}

@media (max-width: 860px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }
}
</style>
