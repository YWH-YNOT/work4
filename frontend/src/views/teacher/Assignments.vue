<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">作业/实验/报告</h1>
        <p class="page-sub">按真实教学流程管理任务：先保存草稿，发布后学生可提交文件，教师可下载、在线预览、填写评语和成绩。</p>
      </div>
      <button class="primary-btn" @click="openCreate">新建作业/实验/报告</button>
    </div>

    <div class="filter-bar">
      <select v-model="selectedCourse" class="select" @change="loadAssignments">
        <option value="">全部课程</option>
        <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
      </select>
      <select v-model="selectedType" class="select" @change="loadAssignments">
        <option value="">全部类型</option>
        <option value="homework">作业/实验</option>
        <option value="report">课程报告</option>
      </select>
      <select v-model="selectedStatus" class="select">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="published">已发布</option>
        <option value="closed">已截止</option>
      </select>
    </div>

    <div class="summary-strip">
      <div><span>任务总数</span><strong>{{ assignments.length }}</strong></div>
      <div><span>已发布任务</span><strong>{{ publishedTaskCount }}</strong></div>
      <div><span>草稿任务</span><strong>{{ draftTaskCount }}</strong></div>
      <div><span>提交总量</span><strong>{{ submissionTotal }}</strong></div>
      <div><span>已发布答案</span><strong>{{ publishedAnswerCount }}</strong></div>
    </div>

    <div class="workspace">
      <section class="list-panel">
        <div v-if="visibleAssignments.length === 0" class="empty">暂无符合条件的任务</div>
        <button
          v-for="item in visibleAssignments"
          :key="item.id"
          :class="['assignment-row', item.status, selectedAssignment?.id === item.id && 'active']"
          @click="selectAssignment(item)"
        >
          <div class="row-main">
            <span :class="['type-badge', item.type]">{{ item.type === 'report' ? '课程报告' : '作业/实验' }}</span>
            <strong>{{ cleanTitle(item.title) }}</strong>
            <span :class="['status-chip', item.status || 'published']">{{ item.status_label || statusLabel(item.status) }}</span>
          </div>
          <div class="row-sub">
            <span>{{ item.course_name || courseMap[item.course_id] || '未关联课程' }}</span>
            <span v-if="item.session_index">第 {{ item.session_index }} 次课</span>
            <span>{{ item.due_date ? `截止 ${fmtDate(item.due_date)}` : '未设置截止时间' }}</span>
            <span>{{ item.submissions_count ?? 0 }} 份提交</span>
          </div>
          <div class="row-footer">
            <span :class="['answer-state', item.standard_answer_published && 'on']">
              {{ item.standard_answer_published ? '参考答案已发布' : '参考答案未发布' }}
            </span>
            <span v-if="item.status === 'draft'" class="draft-tip">学生端暂不可见</span>
          </div>
        </button>
      </section>

      <section class="detail-panel">
        <div v-if="!selectedAssignment" class="empty detail-empty">选择左侧任务后查看提交与批阅情况</div>
        <template v-else>
          <div class="detail-head">
            <div>
              <div class="type-line">
                <span :class="['type-badge', selectedAssignment.type]">
                  {{ selectedAssignment.type === 'report' ? '课程报告' : '作业/实验' }}
                </span>
                <span :class="['status-chip', selectedAssignment.status || 'published']">
                  {{ selectedAssignment.status_label || statusLabel(selectedAssignment.status) }}
                </span>
                <span>{{ selectedAssignment.course_name || courseMap[selectedAssignment.course_id] }}</span>
              </div>
              <h2>{{ cleanTitle(selectedAssignment.title) }}</h2>
              <p>{{ selectedAssignment.description || '暂无任务说明。' }}</p>
              <div class="detail-meta">
                <span v-if="selectedAssignment.session_index">第 {{ selectedAssignment.session_index }} 次课</span>
                <span>{{ selectedAssignment.due_date ? `截止 ${fmtTime(selectedAssignment.due_date)}` : '未设置截止时间' }}</span>
                <span v-if="selectedAssignment.published_at">发布时间：{{ fmtTime(selectedAssignment.published_at) }}</span>
              </div>
            </div>
            <div class="detail-side">
              <div class="detail-count">
                <strong>{{ submissions.length }}</strong>
                <span>提交</span>
              </div>
              <div class="detail-actions">
                <button class="outline-btn" @click="openEdit(selectedAssignment)">编辑</button>
                <button v-if="selectedAssignment.status !== 'published'" class="publish-btn" @click="setAssignmentStatus(selectedAssignment, 'published')">发布</button>
                <button v-if="selectedAssignment.status === 'published'" class="outline-btn" @click="setAssignmentStatus(selectedAssignment, 'draft')">撤回</button>
                <button v-if="selectedAssignment.status !== 'closed'" class="outline-btn" @click="setAssignmentStatus(selectedAssignment, 'closed')">截止</button>
                <button class="delete-btn" @click="deleteAssignment(selectedAssignment)">删除</button>
              </div>
            </div>
          </div>

          <div class="answer-panel">
            <div class="answer-head">
              <div>
                <strong>参考答案 / 评分要点</strong>
                <span>{{ selectedAssignment.standard_answer_published ? '学生端可见' : '仅教师可见' }}</span>
              </div>
              <button class="outline-btn" @click="saveStandardAnswer(!selectedAssignment.standard_answer_published)">
                {{ selectedAssignment.standard_answer_published ? '取消发布' : '发布给学生' }}
              </button>
            </div>
            <textarea
              v-model="standardAnswerDraft"
              rows="4"
              class="textarea"
              placeholder="填写参考答案、评分要点或课程报告评价标准。"
            ></textarea>
            <button class="save-answer" @click="saveStandardAnswer(selectedAssignment.standard_answer_published)">保存评分要点</button>
          </div>

          <div class="submission-head">
            <h3>学生提交与批阅</h3>
            <span>{{ gradedCount }}/{{ submissions.length }} 已批阅</span>
          </div>

          <div v-if="loadingSubs" class="empty">加载提交记录...</div>
          <div v-else-if="submissions.length === 0" class="empty">暂无学生提交</div>
          <div v-else class="submission-list">
            <article v-for="submission in submissions" :key="submission.id" class="submission-card">
              <div class="sub-top">
                <div>
                  <strong>{{ submission.student_name || submission.student_username }}</strong>
                  <span>{{ submission.student_username }}</span>
                </div>
                <span :class="['grade-pill', submission.score == null ? 'pending' : 'done']">
                  {{ submission.score == null ? '未批阅' : `${Math.round(submission.score)} 分` }}
                </span>
              </div>

              <p class="sub-content">{{ submission.content || '学生未填写文字说明。' }}</p>

              <div v-if="submission.file_name" class="file-panel">
                <span>{{ submission.file_name }}</span>
                <div class="file-actions">
                  <button class="link-btn" @click="downloadSubmission(submission)">下载文件</button>
                  <button class="link-btn" @click="previewSubmission(submission)">在线预览</button>
                </div>
              </div>
              <div v-else class="file-panel muted">未上传文件，仅有文字说明。</div>

              <div class="grade-row">
                <input v-model.number="submission.editScore" type="number" min="0" max="100" class="score-input" placeholder="分数" />
                <input v-model="submission.editFeedback" class="feedback-input" placeholder="填写评语，例如：结构完整，实验数据分析需补充误差来源。" />
                <button class="grade-btn" @click="gradeSubmission(submission)">保存批阅</button>
              </div>
              <div class="sub-time">提交时间：{{ submission.submitted_at ? fmtTime(submission.submitted_at) : '--' }}</div>
            </article>
          </div>
        </template>
      </section>
    </div>

    <el-dialog v-model="showTaskDialog" :title="editingAssignment ? '编辑作业/实验/报告' : '新建作业/实验/报告'" width="640px">
      <div class="dialog-form">
        <label>所属课程</label>
        <select v-model.number="taskForm.course_id" class="input">
          <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
        </select>
        <label>任务类型</label>
        <select v-model="taskForm.type" class="input">
          <option value="homework">作业/实验</option>
          <option value="report">课程报告</option>
        </select>
        <label>发布状态</label>
        <select v-model="taskForm.status" class="input">
          <option value="draft">保存为草稿</option>
          <option value="published">发布给学生</option>
          <option value="closed">设为已截止</option>
        </select>
        <label>标题</label>
        <input v-model="taskForm.title" class="input" placeholder="例如：实验二 自动测试系统软件设计" />
        <label>关联课次</label>
        <input v-model.number="taskForm.session_index" class="input" type="number" min="1" placeholder="用于学生端逐课次学习进度展示" />
        <label>截止时间</label>
        <input v-model="taskForm.due_date" class="input" type="datetime-local" />
        <label>任务说明</label>
        <textarea v-model="taskForm.description" class="textarea" rows="3" placeholder="填写上传文件格式、报告结构、评分要求等。"></textarea>
        <label>参考答案 / 评分要点</label>
        <textarea v-model="taskForm.standard_answer" class="textarea" rows="4" placeholder="可先保存为教师可见，截止后再发布给学生。"></textarea>
        <label class="check-row"><input v-model="taskForm.standard_answer_published" type="checkbox" /> 立即发布参考答案</label>
        <div class="dialog-actions">
          <button class="cancel-btn" @click="showTaskDialog = false">取消</button>
          <button class="confirm-btn" :disabled="saving" @click="saveTask">{{ saving ? '保存中...' : taskSubmitText }}</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const courses = ref<any[]>([])
const assignments = ref<any[]>([])
const submissions = ref<any[]>([])
const selectedCourse = ref('')
const selectedType = ref('')
const selectedStatus = ref('')
const selectedAssignment = ref<any | null>(null)
const loadingSubs = ref(false)
const showTaskDialog = ref(false)
const editingAssignment = ref<any | null>(null)
const saving = ref(false)
const standardAnswerDraft = ref('')
const taskForm = ref(defaultTask())

const courseMap = computed(() => Object.fromEntries(courses.value.map(course => [course.id, course.name])))
const visibleAssignments = computed(() => {
  if (!selectedStatus.value) return assignments.value
  return assignments.value.filter(item => (item.status || 'published') === selectedStatus.value)
})
const gradedCount = computed(() => submissions.value.filter(item => item.score != null).length)
const submissionTotal = computed(() => assignments.value.reduce((sum, item) => sum + Number(item.submissions_count || 0), 0))
const publishedAnswerCount = computed(() => assignments.value.filter(item => item.standard_answer_published).length)
const publishedTaskCount = computed(() => assignments.value.filter(item => (item.status || 'published') === 'published').length)
const draftTaskCount = computed(() => assignments.value.filter(item => item.status === 'draft').length)
const taskSubmitText = computed(() => taskForm.value.status === 'published' ? '保存并发布' : '保存任务')

const cleanTitle = (value?: string) => (value || '').replace(/^【课程过程】/, '').trim()
const fmtDate = (value: string) => new Date(value).toLocaleDateString('zh-CN')
const fmtTime = (value: string) => new Date(value).toLocaleString('zh-CN')
const statusLabel = (value?: string) => ({ draft: '草稿', published: '已发布', closed: '已截止' }[value || 'published'] || '已发布')

function defaultTask() {
  return {
    course_id: 0,
    title: '',
    type: 'homework',
    status: 'draft',
    session_index: null as number | null,
    due_date: '',
    description: '',
    standard_answer: '',
    standard_answer_published: false,
  }
}

function toDatetimeLocal(value?: string | null) {
  if (!value) return ''
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

async function loadAssignments() {
  const params = new URLSearchParams()
  if (selectedCourse.value) params.set('course_id', selectedCourse.value)
  if (selectedType.value) params.set('type', selectedType.value)
  const query = params.toString()
  const response = await axios.get(`/api/v1/assignments/${query ? `?${query}` : ''}`)
  assignments.value = response.data
  if (selectedAssignment.value) {
    const fresh = assignments.value.find(item => item.id === selectedAssignment.value.id)
    if (fresh) {
      selectedAssignment.value = fresh
    } else {
      selectedAssignment.value = null
      submissions.value = []
    }
  }
}

async function selectAssignment(item: any) {
  selectedAssignment.value = item
  standardAnswerDraft.value = item.standard_answer || ''
  await loadSubmissions(item.id)
}

async function loadSubmissions(assignmentId: number) {
  loadingSubs.value = true
  try {
    const response = await axios.get(`/api/v1/assignments/${assignmentId}/submissions`)
    submissions.value = response.data.map((item: any) => ({
      ...item,
      editScore: item.score ?? null,
      editFeedback: item.feedback || '',
    }))
  } finally {
    loadingSubs.value = false
  }
}

function openCreate() {
  const task = defaultTask()
  task.course_id = Number(selectedCourse.value || courses.value[0]?.id || 0)
  task.type = selectedType.value || 'homework'
  taskForm.value = task
  editingAssignment.value = null
  showTaskDialog.value = true
}

function openEdit(item: any) {
  taskForm.value = {
    course_id: item.course_id,
    title: cleanTitle(item.title),
    type: item.type || 'homework',
    status: item.status || 'published',
    session_index: item.session_index ?? null,
    due_date: toDatetimeLocal(item.due_date),
    description: item.description || '',
    standard_answer: item.standard_answer || '',
    standard_answer_published: Boolean(item.standard_answer_published),
  }
  editingAssignment.value = item
  showTaskDialog.value = true
}

function buildTaskPayload() {
  const payload: any = { ...taskForm.value }
  payload.title = payload.title.trim()
  payload.due_date = payload.due_date ? new Date(payload.due_date).toISOString() : null
  if (!payload.session_index) payload.session_index = null
  return payload
}

async function saveTask() {
  if (!taskForm.value.course_id || !taskForm.value.title.trim()) {
    ElMessage.warning('请选择课程并填写标题。')
    return
  }
  saving.value = true
  try {
    const payload = buildTaskPayload()
    const response = editingAssignment.value
      ? await axios.patch(`/api/v1/assignments/${editingAssignment.value.id}`, payload)
      : await axios.post('/api/v1/assignments/', payload)
    ElMessage.success(payload.status === 'published' ? '任务已发布' : '任务已保存')
    showTaskDialog.value = false
    await loadAssignments()
    const fresh = assignments.value.find(item => item.id === response.data.id)
    if (fresh) await selectAssignment(fresh)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function replaceAssignment(updated: any) {
  const index = assignments.value.findIndex(item => item.id === updated.id)
  if (index >= 0) assignments.value[index] = updated
  if (selectedAssignment.value?.id === updated.id) selectedAssignment.value = updated
}

async function setAssignmentStatus(item: any, status: 'draft' | 'published' | 'closed') {
  const response = await axios.patch(`/api/v1/assignments/${item.id}/status`, { status })
  replaceAssignment(response.data)
  ElMessage.success(status === 'published' ? '任务已发布，学生端可见' : status === 'draft' ? '任务已撤回为草稿' : '任务已截止')
}

async function deleteAssignment(item: any) {
  if (!window.confirm(`确认删除「${cleanTitle(item.title)}」？学生提交与批阅记录也会删除。`)) return
  await axios.delete(`/api/v1/assignments/${item.id}`)
  ElMessage.success('任务已删除')
  selectedAssignment.value = null
  submissions.value = []
  await loadAssignments()
}

async function saveStandardAnswer(published: boolean) {
  if (!selectedAssignment.value) return
  const response = await axios.patch(`/api/v1/assignments/${selectedAssignment.value.id}/standard-answer`, {
    standard_answer: standardAnswerDraft.value,
    published,
  })
  replaceAssignment(response.data)
  ElMessage.success(published ? '参考答案已发布' : '评分要点已保存')
}

async function gradeSubmission(submission: any) {
  if (submission.editScore == null || Number.isNaN(Number(submission.editScore))) {
    ElMessage.warning('请填写分数。')
    return
  }
  await axios.patch(`/api/v1/assignments/submissions/${submission.id}/grade`, {
    score: Number(submission.editScore),
    feedback: submission.editFeedback,
  })
  ElMessage.success('批阅已保存')
  await loadSubmissions(selectedAssignment.value.id)
  await loadAssignments()
}

async function downloadSubmission(submission: any) {
  if (!submission.download_url) return
  const response = await axios.get(submission.download_url, { responseType: 'blob' })
  saveBlob(response.data, submission.file_name || 'submission')
}

async function previewSubmission(submission: any) {
  if (!submission.view_url) return
  const response = await axios.get(submission.view_url, { responseType: 'blob' })
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

onMounted(async () => {
  const response = await axios.get('/api/v1/courses/my')
  courses.value = response.data
  await loadAssignments()
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.6; }
.primary-btn, .confirm-btn, .grade-btn, .save-answer, .publish-btn { background: #0b63b6; color: white; border: none; border-radius: 8px; padding: 9px 16px; cursor: pointer; font-weight: 900; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.select, .input, .textarea, .score-input, .feedback-input { background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; outline: none; }
.select { padding: 9px 14px; min-width: 180px; }
.summary-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-strip div { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 13px; box-shadow: 0 8px 20px rgba(15,47,100,.05); }
.summary-strip span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.summary-strip strong { color: #0f2f64; font-size: 24px; }
.workspace { display: grid; grid-template-columns: minmax(360px, .85fr) minmax(560px, 1.15fr); gap: 18px; align-items: start; }
.list-panel, .detail-panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 14px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.assignment-row { width: 100%; text-align: left; background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 14px; margin-bottom: 10px; cursor: pointer; transition: all .18s; }
.assignment-row:hover, .assignment-row.active { border-color: #9ec8f1; background: #eaf3ff; }
.assignment-row.draft { background: #f7fafc; border-style: dashed; color: #6c7f9f; }
.assignment-row.closed { background: #fffdf7; border-color: #f0dca8; }
.row-main { display: flex; gap: 9px; align-items: center; color: #0f2f64; flex-wrap: wrap; }
.row-main strong { font-size: 15px; line-height: 1.4; }
.row-sub { display: flex; flex-wrap: wrap; gap: 8px 12px; color: #5b6f92; font-size: 12px; margin-top: 9px; }
.row-footer { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-top: 9px; flex-wrap: wrap; }
.type-badge, .status-chip { font-size: 12px; padding: 3px 8px; border-radius: 7px; font-weight: 900; white-space: nowrap; }
.type-badge.homework { background: #eaf3ff; color: #0b63b6; }
.type-badge.report { background: #fff2d9; color: #9a5a00; }
.status-chip.published { background: #e8f7f0; color: #0b7d56; }
.status-chip.draft { background: #edf3fa; color: #6c7f9f; }
.status-chip.closed { background: #fff2d9; color: #9a5a00; }
.answer-state { color: #7c8da8; font-size: 12px; }
.answer-state.on { color: #0b7d56; }
.draft-tip { color: #8a96a8; font-size: 12px; font-weight: 800; }
.detail-empty { min-height: 360px; display: flex; align-items: center; justify-content: center; }
.detail-head { display: flex; justify-content: space-between; gap: 18px; border-bottom: 1px solid #edf3fb; padding-bottom: 14px; margin-bottom: 14px; }
.type-line { display: flex; align-items: center; gap: 9px; color: #5b6f92; font-size: 12px; flex-wrap: wrap; }
.detail-head h2 { color: #0f2f64; font-size: 20px; margin: 8px 0 4px; line-height: 1.4; }
.detail-head p { color: #5b6f92; line-height: 1.6; margin: 0; white-space: pre-wrap; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 8px 12px; margin-top: 8px; color: #6c7f9f; font-size: 12px; }
.detail-side { display: grid; gap: 10px; justify-items: end; align-content: start; }
.detail-count { min-width: 78px; text-align: center; background: #eaf3ff; border: 1px solid #c8ddf4; border-radius: 9px; padding: 10px; color: #0b63b6; }
.detail-count strong { display: block; color: #0f2f64; font-size: 24px; }
.detail-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; max-width: 330px; }
.answer-panel { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 14px; margin-bottom: 16px; }
.answer-head, .submission-head, .sub-top, .grade-row, .file-panel { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.answer-head strong, .submission-head h3 { color: #0f2f64; font-size: 15px; margin: 0; }
.answer-head span, .submission-head span, .sub-top span, .sub-time { color: #5b6f92; font-size: 12px; }
.outline-btn, .link-btn { background: #ffffff; border: 1px solid #9ec8f1; color: #0b63b6; border-radius: 8px; padding: 7px 12px; cursor: pointer; font-weight: 900; }
.delete-btn { background: #fff4f2; border: 1px solid #ffd5cf; color: #cf3434; border-radius: 8px; padding: 7px 12px; cursor: pointer; font-weight: 900; }
.textarea { width: 100%; resize: vertical; margin-top: 8px; padding: 10px; line-height: 1.6; }
.save-answer { margin-top: 10px; padding: 8px 14px; }
.submission-list { display: flex; flex-direction: column; gap: 12px; }
.submission-card { background: #ffffff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 13px; }
.sub-top strong { color: #0f2f64; display: block; margin-bottom: 2px; }
.grade-pill { border-radius: 7px; padding: 4px 8px; font-size: 12px; font-weight: 900; }
.grade-pill.done { color: #0b7d56; background: #e8f7f0; }
.grade-pill.pending { color: #9a5a00; background: #fff2d9; }
.sub-content { color: #5b6f92; font-size: 13px; line-height: 1.65; background: #f8fbff; border-radius: 8px; padding: 10px; white-space: pre-wrap; }
.file-panel { margin-top: 10px; padding: 10px; border-radius: 8px; background: #f8fbff; border: 1px solid #e1ecf8; color: #0f2f64; flex-wrap: wrap; }
.file-panel.muted { color: #7c8da8; justify-content: flex-start; }
.file-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.score-input { width: 86px; padding: 9px; }
.feedback-input { flex: 1; padding: 9px; min-width: 220px; }
.grade-row { margin-top: 12px; flex-wrap: wrap; }
.grade-btn { padding: 9px 12px; }
.sub-time { margin-top: 8px; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 24px; text-align: center; background: #f8fbff; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: #5b6f92; font-weight: 800; }
.input { padding: 10px 12px; width: 100%; }
.check-row { display: inline-flex; align-items: center; gap: 8px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.cancel-btn { padding: 8px 18px; border-radius: 8px; background: #ffffff; border: 1px solid #c8ddf4; color: #5b6f92; cursor: pointer; font-weight: 800; }
.confirm-btn:disabled { opacity: .55; cursor: not-allowed; }
@media (max-width: 1180px) {
  .workspace { grid-template-columns: 1fr; }
  .summary-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .detail-head { flex-direction: column; }
  .detail-side { justify-items: stretch; }
  .detail-actions { justify-content: flex-start; max-width: none; }
}
</style>
