<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">成绩管理</h1>
        <p class="page-sub">按课程导入、导出和核查过程成绩，AI 学情分析只读取这里形成的成绩数据。</p>
      </div>
      <div class="header-actions">
        <button class="ghost-btn" @click="downloadTemplate">
          <el-icon><Download /></el-icon>
          成绩模板
        </button>
        <button class="ghost-btn" @click="fileInput?.click()">
          <el-icon><Upload /></el-icon>
          导入成绩
        </button>
        <button class="primary-btn" @click="exportGrades">
          <el-icon><Document /></el-icon>
          导出成绩
        </button>
        <input ref="fileInput" class="hidden-input" type="file" accept=".xlsx" @change="importGrades" />
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="selectedCourse" class="select" @change="loadGrades">
        <option value="">全部课程</option>
        <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
      </select>
      <button class="light-btn" @click="loadGrades" :disabled="loading">
        <el-icon><Refresh /></el-icon>
        {{ loading ? '刷新中' : '刷新' }}
      </button>
    </div>

    <section class="summary-strip">
      <div><span>成绩记录</span><strong>{{ grades.length }}</strong></div>
      <div><span>已覆盖学生</span><strong>{{ coveredStudents }}</strong></div>
      <div><span>平均成绩</span><strong>{{ averageScore }}</strong></div>
      <div><span>低于 60 分</span><strong>{{ lowScoreCount }}</strong></div>
    </section>

    <section v-if="importResult" class="result-panel">
      <div class="result-head">
        <strong>最近一次导入结果</strong>
        <span>新增 {{ importResult.imported || 0 }} 条，更新 {{ importResult.updated || 0 }} 条</span>
      </div>
      <div v-if="importResult.errors?.length" class="error-list">
        <div v-for="err in importResult.errors.slice(0, 6)" :key="`${err.row}-${err.reason}`">
          第 {{ err.row }} 行：{{ err.reason }}
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>成绩明细</h2>
          <p>可按课程筛选后导出对应成绩表，作为中期检查或过程评价附件。</p>
        </div>
      </div>
      <div class="grade-table">
        <div class="table-head">
          <span>学生</span>
          <span>课程</span>
          <span>成绩</span>
          <span>评语</span>
          <span>写入时间</span>
        </div>
        <div v-if="loading" class="empty">加载中...</div>
        <div v-else-if="grades.length === 0" class="empty">暂无成绩数据，可先下载模板导入。</div>
        <div v-for="item in grades" :key="item.id" class="table-row">
          <div>
            <strong>{{ item.student_name || item.student_username }}</strong>
            <span>{{ item.student_username }}</span>
          </div>
          <span>{{ item.course_name }}</span>
          <strong :class="['score', scoreLevel(item.score)]">{{ Math.round(item.score) }}</strong>
          <p>{{ item.comment || '暂无评语' }}</p>
          <span>{{ item.created_at ? fmtTime(item.created_at) : '--' }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const courses = ref<any[]>([])
const grades = ref<any[]>([])
const selectedCourse = ref<number | ''>('')
const loading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const importResult = ref<any | null>(null)

const coveredStudents = computed(() => new Set(grades.value.map(item => item.student_id)).size)
const lowScoreCount = computed(() => grades.value.filter(item => Number(item.score) < 60).length)
const averageScore = computed(() => {
  if (!grades.value.length) return '--'
  return Math.round(grades.value.reduce((sum, item) => sum + Number(item.score || 0), 0) / grades.value.length)
})

function saveBlob(data: BlobPart, filename: string) {
  const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function params() {
  return selectedCourse.value ? { course_id: selectedCourse.value } : {}
}

function fmtTime(value: string) {
  return new Date(value).toLocaleString('zh-CN')
}

function scoreLevel(value: number) {
  if (value >= 85) return 'high'
  if (value >= 60) return 'mid'
  return 'low'
}

async function loadCourses() {
  const response = await axios.get('/api/v1/courses/my')
  courses.value = response.data || []
}

async function loadGrades() {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/grades/', { params: params() })
    grades.value = response.data || []
  } finally {
    loading.value = false
  }
}

async function downloadTemplate() {
  try {
    const response = await axios.get('/api/v1/grades/template', { params: params(), responseType: 'blob' })
    saveBlob(response.data, '成绩导入模板.xlsx')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '成绩模板下载失败')
  }
}

async function exportGrades() {
  try {
    const response = await axios.get('/api/v1/grades/export', { params: params(), responseType: 'blob' })
    const course = courses.value.find(item => item.id === Number(selectedCourse.value))
    saveBlob(response.data, `${course?.name || '课程'}-成绩表.xlsx`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '成绩导出失败')
  }
}

async function importGrades(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  if (selectedCourse.value) form.append('course_id', String(selectedCourse.value))
  try {
    const response = await axios.post('/api/v1/grades/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = response.data
    ElMessage.success(`成绩导入完成：新增 ${response.data.imported} 条，更新 ${response.data.updated} 条`)
    await loadGrades()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '成绩导入失败')
  } finally {
    input.value = ''
  }
}

onMounted(async () => {
  await loadCourses()
  await loadGrades()
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.6; }
.header-actions, .filter-bar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.filter-bar { margin-bottom: 14px; }
.hidden-input { display: none; }
.ghost-btn, .primary-btn, .light-btn { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px; padding: 9px 14px; font-weight: 900; cursor: pointer; }
.ghost-btn, .light-btn { background: #fff; color: #0b63b6; border: 1px solid #c8ddf4; }
.primary-btn { background: #0b63b6; color: #fff; border: 1px solid #0b63b6; }
.select { background: #fff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; padding: 9px 14px; min-width: 220px; outline: none; }
.summary-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-strip div, .panel, .result-panel { background: #fff; border: 1px solid #d9e7f7; border-radius: 10px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.summary-strip div { padding: 13px; }
.summary-strip span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.summary-strip strong { color: #0f2f64; font-size: 24px; }
.panel, .result-panel { padding: 18px; margin-bottom: 16px; }
.result-head, .panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }
.result-head strong, .panel-head h2 { color: #0f2f64; margin: 0; }
.result-head span { color: #0b7d56; background: #e8f7f0; border-radius: 8px; padding: 4px 8px; font-size: 12px; font-weight: 900; }
.panel-head p { color: #5b6f92; font-size: 12px; margin: 5px 0 0; }
.error-list { display: grid; gap: 6px; color: #9a5a00; font-size: 12px; }
.grade-table { display: grid; gap: 8px; overflow-x: auto; }
.table-head, .table-row { display: grid; grid-template-columns: 180px 220px 90px minmax(240px, 1fr) 170px; gap: 12px; align-items: center; min-width: 900px; }
.table-head { color: #5b6f92; font-size: 12px; padding: 0 12px 4px; }
.table-row { background: #f8fbff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 12px; }
.table-row strong { color: #0f2f64; }
.table-row span, .table-row p { color: #5b6f92; font-size: 13px; margin: 0; line-height: 1.5; }
.table-row div span { display: block; margin-top: 2px; font-size: 12px; }
.score { border-radius: 8px; padding: 7px 9px; text-align: center; }
.score.high { background: #e8f7f0; color: #0b7d56; }
.score.mid { background: #eaf3ff; color: #0b63b6; }
.score.low { background: #fff0ef; color: #cf3434; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 28px; text-align: center; background: #f8fbff; }
@media (max-width: 900px) {
  .page-header { flex-direction: column; }
  .summary-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .summary-strip { grid-template-columns: 1fr; }
}
</style>
