<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">课程与教务数据</h1>
        <p class="page-sub">由管理员统一维护课程、教师授课表和学生选课表，后续对接真实教务数据时可直接沿用 Excel 模板。</p>
      </div>
      <div class="header-actions">
        <button class="ghost-btn" @click="downloadMembershipTemplate">
          <el-icon><Download /></el-icon>
          选课/授课模板
        </button>
        <button class="ghost-btn" @click="downloadProcessTemplate">
          <el-icon><Download /></el-icon>
          教学过程模板
        </button>
        <button class="ghost-btn" @click="membershipInput?.click()">
          <el-icon><Upload /></el-icon>
          导入教务 Excel
        </button>
        <button class="primary-btn" @click="exportMemberships">
          <el-icon><Document /></el-icon>
          导出教务数据
        </button>
        <input ref="membershipInput" class="hidden-input" type="file" accept=".xlsx" @change="importMembershipExcel" />
      </div>
    </div>

    <section class="process-band">
      <div class="process-step">
        <span>1</span>
        <strong>下载模板</strong>
        <p>包含学生表、教师授课表、学生选课表、任务表、课堂测验题目表和成绩表。</p>
      </div>
      <div class="process-step">
        <span>2</span>
        <strong>填入真实数据</strong>
        <p>课程代码优先匹配，任务和成绩按课程、学号、标题形成关联。</p>
      </div>
      <div class="process-step">
        <span>3</span>
        <strong>分批导入平台</strong>
        <p>先导入选课授课，再导入任务、测验和成绩等过程数据。</p>
      </div>
    </section>

    <section v-if="importResult" class="result-panel">
      <div class="result-head">
        <strong>最近一次导入结果</strong>
        <span v-if="importResult.errors?.length">{{ importResult.errors.length }} 行需要检查</span>
      </div>
      <div class="result-grid">
        <div><span>新建教师</span><strong>{{ importResult.created_teachers || 0 }}</strong></div>
        <div><span>新建学生</span><strong>{{ importResult.created_students || 0 }}</strong></div>
        <div><span>新建课程</span><strong>{{ importResult.created_courses || 0 }}</strong></div>
        <div><span>授课关系</span><strong>{{ importResult.teaching_assignments || 0 }}</strong></div>
        <div><span>新增选课</span><strong>{{ importResult.enrollments || 0 }}</strong></div>
        <div><span>更新选课</span><strong>{{ importResult.updated_enrollments || 0 }}</strong></div>
      </div>
      <div v-if="importResult.errors?.length" class="error-list">
        <div v-for="err in importResult.errors.slice(0, 5)" :key="`${err.sheet}-${err.row}-${err.reason}`">
          {{ err.sheet }} 第 {{ err.row }} 行：{{ err.reason }}
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>课程清单</h2>
          <p>教师端只读取这里生成的授课课程，不再承担选课和授课数据导入。</p>
        </div>
        <button class="light-btn" @click="loadCourses" :disabled="loading">
          <el-icon><Refresh /></el-icon>
          {{ loading ? '刷新中' : '刷新' }}
        </button>
      </div>

      <div class="course-table">
        <div class="table-head">
          <span>课程</span>
          <span>课程代码</span>
          <span>主讲教师</span>
          <span>课程说明</span>
        </div>
        <div v-if="courses.length === 0" class="empty">暂无课程数据，请先导入教务 Excel。</div>
        <div v-for="course in courses" :key="course.id" class="table-row">
          <div class="course-cell">
            <div class="avatar">{{ initial(course.name) }}</div>
            <strong>{{ course.name }}</strong>
          </div>
          <span>{{ course.course_code || '未设置' }}</span>
          <span>{{ course.teacher?.full_name || course.teacher?.username || '未绑定' }}</span>
          <p>{{ course.description || '暂无课程简介' }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const courses = ref<any[]>([])
const loading = ref(false)
const membershipInput = ref<HTMLInputElement | null>(null)
const importResult = ref<any | null>(null)

function initial(name: string) {
  return (name || '课').slice(0, 1)
}

function saveBlob(data: BlobPart, filename: string) {
  const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function loadCourses() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/courses/')
    courses.value = res.data || []
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '课程清单加载失败')
  } finally {
    loading.value = false
  }
}

async function downloadMembershipTemplate() {
  try {
    const res = await axios.get('/api/v1/imports/course-memberships/template', { responseType: 'blob' })
    saveBlob(res.data, '选课授课导入模板.xlsx')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '模板下载失败')
  }
}

async function downloadProcessTemplate() {
  try {
    const res = await axios.get('/api/v1/imports/teaching-process/template', { responseType: 'blob' })
    saveBlob(res.data, '教学过程数据导入模板.xlsx')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '模板下载失败')
  }
}

async function importMembershipExcel(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await axios.post('/api/v1/imports/course-memberships', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = res.data
    const errors = res.data.errors?.length || 0
    ElMessage.success(errors ? `导入完成，${errors} 行需要检查` : '教务数据导入完成')
    await loadCourses()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || 'Excel 导入失败')
  } finally {
    input.value = ''
  }
}

async function exportMemberships() {
  try {
    const res = await axios.get('/api/v1/imports/course-memberships/export', { responseType: 'blob' })
    saveBlob(res.data, '教务选课授课数据.xlsx')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '教务数据导出失败')
  }
}

onMounted(loadCourses)
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; margin: 0; color: #0f2f64; }
.page-sub { margin: 6px 0 0; color: #5b6f92; font-size: 13px; line-height: 1.6; }
.header-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.hidden-input { display: none; }
.ghost-btn, .primary-btn, .light-btn { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px; padding: 9px 14px; font-weight: 800; cursor: pointer; }
.ghost-btn, .light-btn { background: #ffffff; color: #0b63b6; border: 1px solid #c8ddf4; }
.primary-btn { background: #0b63b6; color: #ffffff; border: 1px solid #0b63b6; }
.light-btn:disabled { opacity: .55; cursor: wait; }
.process-band { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.process-step { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.process-step span { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border-radius: 8px; background: #eaf3ff; color: #0b63b6; font-weight: 900; margin-bottom: 10px; }
.process-step strong { display: block; color: #0f2f64; font-size: 15px; }
.process-step p { color: #5b6f92; font-size: 12px; line-height: 1.6; margin: 6px 0 0; }
.panel, .result-panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); margin-bottom: 16px; }
.panel-head, .result-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 17px; margin: 0; }
.panel-head p { color: #5b6f92; font-size: 12px; line-height: 1.6; margin: 5px 0 0; }
.result-head strong { color: #0f2f64; }
.result-head span { color: #cf3434; background: #fff0ef; border: 1px solid #ffd5cf; border-radius: 7px; padding: 4px 8px; font-size: 12px; }
.result-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.result-grid div { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 11px; }
.result-grid span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.result-grid strong { color: #0f2f64; font-size: 22px; }
.error-list { margin-top: 12px; display: grid; gap: 6px; color: #9a5a00; font-size: 12px; }
.course-table { display: grid; gap: 8px; }
.table-head, .table-row { display: grid; grid-template-columns: minmax(220px, 1.4fr) 150px 160px minmax(260px, 2fr); gap: 12px; align-items: center; }
.table-head { color: #5b6f92; font-size: 12px; padding: 0 12px 4px; }
.table-row { background: #f8fbff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 12px; min-height: 64px; }
.course-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.avatar { width: 36px; height: 36px; border-radius: 8px; background: #eaf3ff; border: 1px solid #c8ddf4; color: #0b63b6; display: flex; align-items: center; justify-content: center; font-weight: 900; flex-shrink: 0; }
.course-cell strong { color: #0f2f64; font-size: 14px; }
.table-row span, .table-row p { color: #5b6f92; font-size: 13px; margin: 0; line-height: 1.5; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; background: #f8fbff; border-radius: 8px; padding: 28px; text-align: center; }
@media (max-width: 1180px) {
  .page-header { flex-direction: column; }
  .header-actions { justify-content: flex-start; }
  .process-band, .result-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .table-head { display: none; }
  .table-row { grid-template-columns: 1fr 1fr; }
  .table-row p { grid-column: 1 / -1; }
}
@media (max-width: 720px) {
  .process-band, .result-grid, .table-row { grid-template-columns: 1fr; }
}
</style>
