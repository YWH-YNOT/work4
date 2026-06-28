<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">我的作业/实验/报告</h1>
        <p class="page-sub">在线查看任务要求，完成后上传作业、实验报告或课程报告文件。</p>
      </div>
    </div>

    <section class="summary-strip">
      <div><span>任务总数</span><strong>{{ assignments.length }}</strong></div>
      <div><span>待提交</span><strong>{{ pendingCount }}</strong></div>
      <div><span>已提交</span><strong>{{ submittedCount }}</strong></div>
      <div><span>已批阅</span><strong>{{ gradedCount }}</strong></div>
      <div><span>完成率</span><strong>{{ completionRate }}%</strong></div>
    </section>

    <section class="overview-panel">
      <div>
        <strong>任务完成情况</strong>
        <p>只显示教师已发布的作业、实验和课程报告，草稿任务不会出现在学生端。</p>
      </div>
      <div class="progress-track">
        <i :style="{ width: `${completionRate}%` }"></i>
      </div>
    </section>

    <div class="filter-bar">
      <button
        v-for="item in filters"
        :key="item.value"
        :class="['filter-btn', filter === item.value && 'active']"
        @click="filter = item.value"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="filteredItems.length === 0" class="empty">暂无任务</div>
    <div v-else class="task-list">
      <article v-for="item in filteredItems" :key="item.id" class="task-card">
        <div class="task-main">
          <div class="task-title-row">
            <span :class="['type-badge', item.type]">{{ item.type === 'report' ? '课程报告' : '作业/实验' }}</span>
            <h2>{{ cleanTitle(item.title) }}</h2>
          </div>
          <p class="task-desc">{{ item.description || '教师暂未填写详细说明。' }}</p>
          <div class="task-meta">
            <span>{{ item.course_name || '未关联课程' }}</span>
            <span v-if="item.session_index">第 {{ item.session_index }} 次课</span>
            <span :class="{ urgent: isUrgent(item.due_date) }">
              {{ item.due_date ? `截止 ${fmtDate(item.due_date)}` : '未设置截止时间' }}
            </span>
          </div>

          <div v-if="item.submitted" class="submission-box">
            <div class="submission-line">
              <strong>{{ item.score != null ? `已批阅 ${Math.round(item.score)} 分` : '已提交，待教师批阅' }}</strong>
              <span>{{ item.submitted_at ? fmtTime(item.submitted_at) : '' }}</span>
            </div>
            <div v-if="item.file_name" class="file-row">
              <span>{{ item.file_name }}</span>
              <button @click="downloadFile(item)" class="link-btn">下载</button>
              <button @click="previewFile(item)" class="link-btn">预览</button>
            </div>
            <p v-if="item.feedback" class="feedback">教师评语：{{ item.feedback }}</p>
          </div>

          <div v-if="item.standard_answer" class="answer-box">
            <strong>参考答案 / 评分要点</strong>
            <p>{{ item.standard_answer }}</p>
          </div>
        </div>

        <div class="task-actions">
          <button class="submit-btn" @click="openSubmit(item)">
            {{ item.submitted ? '重新提交' : '提交文件' }}
          </button>
        </div>
      </article>
    </div>

    <el-dialog v-model="dialogVisible" :title="submitTitle" width="620px">
      <div class="submit-form">
        <label>提交说明</label>
        <textarea
          v-model="submitContent"
          rows="4"
          class="textarea"
          placeholder="可填写设计说明、报告摘要、补充说明或实验环境说明。"
        ></textarea>

        <label>上传文件</label>
        <div class="upload-box" @click="fileInput?.click()" @dragover.prevent @drop.prevent="onDrop">
          <input ref="fileInput" type="file" hidden @change="onFileChange" />
          <strong>{{ selectedFile ? selectedFile.name : '点击或拖拽文件到此处' }}</strong>
          <span>支持 PDF、Word、PPT、Excel、图片、压缩包等，单个文件不超过 50MB。</span>
        </div>

        <div class="dialog-actions">
          <button class="cancel-btn" @click="dialogVisible = false">取消</button>
          <button class="confirm-btn" :disabled="submitting" @click="doSubmit">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const assignments = ref<any[]>([])
const loading = ref(true)
const filter = ref('all')
const dialogVisible = ref(false)
const submitting = ref(false)
const currentAssignment = ref<any | null>(null)
const submitContent = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const filters = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待提交' },
  { value: 'submitted', label: '已提交' },
  { value: 'graded', label: '已批阅' },
]

const filteredItems = computed(() => {
  if (filter.value === 'pending') return assignments.value.filter(item => !item.submitted)
  if (filter.value === 'submitted') return assignments.value.filter(item => item.submitted)
  if (filter.value === 'graded') return assignments.value.filter(item => item.score != null)
  return assignments.value
})
const pendingCount = computed(() => assignments.value.filter(item => !item.submitted).length)
const submittedCount = computed(() => assignments.value.filter(item => item.submitted).length)
const gradedCount = computed(() => assignments.value.filter(item => item.score != null).length)
const completionRate = computed(() => {
  if (!assignments.value.length) return 0
  return Math.round(submittedCount.value / assignments.value.length * 100)
})

const submitTitle = computed(() => currentAssignment.value ? `提交：${cleanTitle(currentAssignment.value.title)}` : '提交任务')

const cleanTitle = (value?: string) => (value || '').replace(/^【课程过程】/, '').trim()
const fmtDate = (value: string) => new Date(value).toLocaleDateString('zh-CN')
const fmtTime = (value: string) => new Date(value).toLocaleString('zh-CN')

function isUrgent(value?: string | null) {
  if (!value) return false
  const diff = new Date(value).getTime() - Date.now()
  return diff > 0 && diff <= 3 * 24 * 60 * 60 * 1000
}

function openSubmit(item: any) {
  currentAssignment.value = item
  submitContent.value = item.content || ''
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
  dialogVisible.value = true
}

function onFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) selectedFile.value = file
}

function onDrop(event: DragEvent) {
  const file = event.dataTransfer?.files?.[0]
  if (file) selectedFile.value = file
}

async function doSubmit() {
  if (!currentAssignment.value) return
  if (!selectedFile.value && !submitContent.value.trim()) {
    ElMessage.warning('请上传文件，或填写提交说明。')
    return
  }

  submitting.value = true
  try {
    if (selectedFile.value) {
      const form = new FormData()
      form.append('file', selectedFile.value)
      form.append('content', submitContent.value)
      await axios.post(`/api/v1/assignments/${currentAssignment.value.id}/submit-file`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    } else {
      await axios.post(`/api/v1/assignments/${currentAssignment.value.id}/submit`, {
        content: submitContent.value,
      })
    }
    ElMessage.success('提交成功')
    dialogVisible.value = false
    await load()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function downloadFile(item: any) {
  if (!item.download_url) return
  const response = await axios.get(item.download_url, { responseType: 'blob' })
  saveBlob(response.data, item.file_name || 'submission')
}

async function previewFile(item: any) {
  if (!item.view_url) return
  const response = await axios.get(item.view_url, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

function saveBlob(data: BlobPart, filename: string) {
  const url = URL.createObjectURL(new Blob([data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function load() {
  const response = await axios.get('/api/v1/assignments/')
  assignments.value = response.data
}

onMounted(async () => {
  try {
    await load()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; margin: 0; color: #0f2f64; }
.page-sub { margin: 6px 0 0; color: #5b6f92; font-size: 14px; }
.summary-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.summary-strip div { background: #fff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 13px; box-shadow: 0 8px 20px rgba(15,47,100,.05); }
.summary-strip span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.summary-strip strong { color: #0f2f64; font-size: 24px; }
.overview-panel { display: grid; grid-template-columns: minmax(260px, .8fr) minmax(320px, 1.2fr); gap: 16px; align-items: center; background: #fff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.05); }
.overview-panel strong { color: #0f2f64; font-size: 16px; }
.overview-panel p { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 6px 0 0; }
.progress-track { height: 12px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.progress-track i { display: block; height: 100%; background: linear-gradient(90deg, #0b63b6, #54a4ee); border-radius: inherit; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.filter-btn { border: 1px solid #c8ddf4; background: #fff; color: #5b6f92; border-radius: 8px; padding: 8px 14px; font-weight: 800; cursor: pointer; }
.filter-btn.active, .filter-btn:hover { background: #eaf3ff; border-color: #9ec8f1; color: #0b63b6; }
.task-list { display: grid; gap: 14px; }
.task-card { display: flex; justify-content: space-between; gap: 18px; background: #fff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.05); }
.task-main { flex: 1; min-width: 0; }
.task-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.task-title-row h2 { margin: 0; font-size: 18px; line-height: 1.4; color: #0f2f64; }
.type-badge { border-radius: 7px; padding: 4px 8px; font-size: 12px; font-weight: 900; white-space: nowrap; }
.type-badge.homework { background: #eaf3ff; color: #0b63b6; }
.type-badge.report { background: #fff2d9; color: #9a5a00; }
.task-desc { color: #5b6f92; line-height: 1.65; margin: 0 0 10px; white-space: pre-wrap; }
.task-meta { display: flex; flex-wrap: wrap; gap: 8px 12px; color: #5b6f92; font-size: 12px; }
.urgent { color: #d64545; font-weight: 900; }
.submission-box { margin-top: 12px; border: 1px solid #d9e7f7; background: #f8fbff; border-radius: 9px; padding: 12px; }
.submission-line, .file-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.submission-line strong { color: #0b7d56; }
.submission-line span { color: #7c8da8; font-size: 12px; }
.file-row { margin-top: 9px; color: #0f2f64; }
.link-btn { border: none; background: #eaf3ff; color: #0b63b6; border-radius: 7px; padding: 6px 10px; cursor: pointer; font-weight: 800; }
.feedback { color: #5b6f92; margin: 10px 0 0; line-height: 1.6; }
.answer-box { margin-top: 12px; border: 1px solid #c8eadb; background: #f2fbf7; border-radius: 9px; padding: 12px; }
.answer-box strong { color: #0b7d56; font-size: 13px; }
.answer-box p { color: #42624f; line-height: 1.65; margin: 8px 0 0; white-space: pre-wrap; }
.task-actions { display: flex; align-items: flex-start; }
.submit-btn, .confirm-btn { background: #0b63b6; color: #fff; border: none; border-radius: 8px; padding: 9px 16px; font-weight: 900; cursor: pointer; white-space: nowrap; }
.submit-form { display: grid; gap: 10px; }
.submit-form label { color: #5b6f92; font-weight: 800; font-size: 13px; }
.textarea { width: 100%; resize: vertical; border: 1px solid #c8ddf4; background: #fff; color: #0f2f64; border-radius: 8px; padding: 10px; line-height: 1.6; outline: none; }
.upload-box { border: 1px dashed #9ec8f1; background: #f8fbff; border-radius: 10px; padding: 20px; cursor: pointer; display: grid; gap: 6px; text-align: center; }
.upload-box strong { color: #0f2f64; }
.upload-box span { color: #5b6f92; font-size: 12px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.cancel-btn { background: #fff; border: 1px solid #c8ddf4; color: #5b6f92; border-radius: 8px; padding: 8px 16px; cursor: pointer; font-weight: 800; }
.confirm-btn:disabled { opacity: .55; cursor: not-allowed; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 10px; padding: 28px; text-align: center; background: #f8fbff; }
@media (max-width: 780px) {
  .summary-strip, .overview-panel { grid-template-columns: 1fr; }
  .task-card { flex-direction: column; }
  .task-actions { align-items: stretch; }
  .submit-btn { width: 100%; }
}
</style>
