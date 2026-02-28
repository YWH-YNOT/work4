<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">成绩管理</h1>
      <button @click="openGradeDialog(null)" class="create-btn">＋ 录入成绩</button>
    </div>

    <!-- 课程筛选 -->
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadData" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <div class="tab-group">
        <button :class="['tab-btn', tab==='grades'&&'active']" @click="tab='grades'">课程成绩</button>
        <button :class="['tab-btn', tab==='submissions'&&'active']" @click="tab='submissions';loadSubmissions()">作业批改</button>
      </div>
    </div>

    <!-- 课程成绩列表 -->
    <div v-if="tab==='grades'">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="grades.length===0" class="empty">暂无成绩记录</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>学生ID</th><th>课程</th><th>成绩</th><th>等级</th><th>评语</th><th>录入时间</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in grades" :key="g.id">
            <td>{{ g.student_id }}</td>
            <td>{{ g.course_name }}</td>
            <td>
              <span class="score-badge" :class="scoreClass(g.score)">{{ g.score }}</span>
            </td>
            <td><span class="grade-level" :class="scoreClass(g.score)">{{ scoreLabel(g.score) }}</span></td>
            <td class="comment-cell">{{ g.comment || '—' }}</td>
            <td>{{ fmt(g.created_at) }}</td>
            <td>
              <button @click="openGradeDialog(g)" class="edit-btn">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 作业提交列表 -->
    <div v-if="tab==='submissions'">
      <div class="sub-filter">
        <select v-model="selectedAssignment" @change="loadSubmissions" class="sel">
          <option value="">请选择作业</option>
          <option v-for="a in assignments" :key="a.id" :value="a.id">{{ a.title }}</option>
        </select>
      </div>
      <div v-if="!selectedAssignment" class="empty">请先选择一个作业查看提交情况</div>
      <div v-else-if="submissions.length===0" class="empty">该作业暂无提交</div>
      <table v-else class="table">
        <thead>
          <tr><th>学生ID</th><th>提交内容</th><th>提交时间</th><th>评分</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in submissions" :key="s.id">
            <td>{{ s.student_id }}</td>
            <td class="content-cell">{{ s.content || '（未填写内容）' }}</td>
            <td>{{ fmt(s.submitted_at) }}</td>
            <td>
              <span v-if="s.score!=null" class="score-badge" :class="scoreClass(s.score)">{{ s.score }}</span>
              <span v-else class="pending-badge">待批</span>
            </td>
            <td>
              <button @click="openGradeSubmission(s)" class="edit-btn">批改</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 录入/编辑成绩对话框 -->
    <el-dialog v-model="gradeDialogVisible" :title="editingGrade?'编辑成绩':'录入成绩'" width="460px">
      <div class="dialog-form">
        <label>学生ID</label>
        <input v-model.number="gradeForm.student_id" type="number" class="inp" placeholder="学生用户 ID" :disabled="!!editingGrade"/>
        <label>课程</label>
        <select v-model="gradeForm.course_id" class="inp-sel" :disabled="!!editingGrade">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label>成绩（0-100）</label>
        <input v-model.number="gradeForm.score" type="number" min="0" max="100" class="inp" placeholder="0 - 100"/>
        <label>评语（可选）</label>
        <textarea v-model="gradeForm.comment" class="ta" rows="3" placeholder="对该成绩的说明或反馈..."></textarea>
        <div class="dialog-actions">
          <button @click="gradeDialogVisible=false" class="cancel-btn">取消</button>
          <button @click="saveGrade" :disabled="saving" class="confirm-btn">{{ saving?'保存中...':'确认保存' }}</button>
        </div>
      </div>
    </el-dialog>

    <!-- 作业批改对话框 -->
    <el-dialog v-model="subDialogVisible" title="批改作业" width="460px">
      <div class="dialog-form">
        <label>学生提交内容</label>
        <div class="sub-content-box">{{ gradingSubmission?.content || '（无内容）' }}</div>
        <label>评分（0-100）</label>
        <input v-model.number="subGradeForm.score" type="number" min="0" max="100" class="inp"/>
        <label>反馈（可选）</label>
        <textarea v-model="subGradeForm.feedback" class="ta" rows="3" placeholder="批改反馈..."></textarea>
        <div class="dialog-actions">
          <button @click="subDialogVisible=false" class="cancel-btn">取消</button>
          <button @click="gradeSubmission" :disabled="saving" class="confirm-btn">提交批改</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const courses = ref<any[]>([])
const grades = ref<any[]>([])
const assignments = ref<any[]>([])
const submissions = ref<any[]>([])
const selectedCourse = ref<number|''>('')
const selectedAssignment = ref<number|''>('')
const loading = ref(false)
const saving = ref(false)
const tab = ref<'grades'|'submissions'>('grades')

const gradeDialogVisible = ref(false)
const subDialogVisible = ref(false)
const editingGrade = ref<any>(null)
const gradingSubmission = ref<any>(null)
const gradeForm = ref({ student_id: 0, course_id: 0, score: 80, comment: '' })
const subGradeForm = ref({ score: 80, feedback: '' })

const fmt = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : '—'
const scoreClass = (s: number) => s >= 90 ? 'excellent' : s >= 75 ? 'good' : s >= 60 ? 'pass' : 'fail'
const scoreLabel = (s: number) => s >= 90 ? '优秀' : s >= 75 ? '良好' : s >= 60 ? '及格' : '不及格'

async function loadData() {
  loading.value = true
  try {
    let url = '/api/v1/grades/'
    if (selectedCourse.value) url += `?course_id=${selectedCourse.value}`
    const r = await axios.get(url)
    grades.value = r.data
  } finally { loading.value = false }
}

async function loadSubmissions() {
  if (!selectedAssignment.value) { submissions.value = []; return }
  const r = await axios.get(`/api/v1/assignments/${selectedAssignment.value}/submissions`)
  submissions.value = r.data
}

function openGradeDialog(g: any) {
  editingGrade.value = g
  if (g) {
    gradeForm.value = { student_id: g.student_id, course_id: g.course_id, score: g.score, comment: g.comment || '' }
  } else {
    gradeForm.value = { student_id: 0, course_id: courses.value[0]?.id || 0, score: 80, comment: '' }
  }
  gradeDialogVisible.value = true
}

function openGradeSubmission(s: any) {
  gradingSubmission.value = s
  subGradeForm.value = { score: s.score ?? 80, feedback: s.feedback || '' }
  subDialogVisible.value = true
}

async function saveGrade() {
  saving.value = true
  try {
    await axios.post('/api/v1/grades/', gradeForm.value)
    gradeDialogVisible.value = false
    ElMessage.success('成绩保存成功')
    await loadData()
  } catch(e: any) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

async function gradeSubmission() {
  if (!gradingSubmission.value) return
  saving.value = true
  try {
    await axios.patch(`/api/v1/assignments/submissions/${gradingSubmission.value.id}/grade`, subGradeForm.value)
    subDialogVisible.value = false
    ElMessage.success('批改完成')
    await loadSubmissions()
  } catch(e: any) { ElMessage.error(e.response?.data?.detail || '批改失败') }
  finally { saving.value = false }
}

onMounted(async () => {
  const [c, a] = await Promise.all([
    axios.get('/api/v1/courses/my'),
    axios.get('/api/v1/assignments/')
  ])
  courses.value = c.data
  assignments.value = a.data
  if (c.data.length) gradeForm.value.course_id = c.data[0].id
  await loadData()
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.create-btn { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; border-radius: 10px; padding: 9px 20px; cursor: pointer; font-weight: 600; font-size: 14px; }
.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }
.sub-filter { margin-bottom: 16px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.tab-group { display: flex; gap: 4px; background: rgba(255,255,255,0.04); border-radius: 10px; padding: 4px; margin-left: auto; }
.tab-btn { padding: 6px 18px; border-radius: 8px; border: none; background: transparent; color: var(--text-secondary); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.18s; }
.tab-btn.active { background: rgba(16,185,129,0.15); color: #34d399; }
.loading, .empty { color: var(--text-secondary); text-align: center; padding: 40px; font-size: 15px; }
.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; padding: 12px 14px; font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; border-bottom: 1px solid rgba(16,185,129,0.1); }
.table td { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 14px; color: var(--text-secondary); vertical-align: middle; }
.score-badge { font-size: 15px; font-weight: 700; padding: 4px 12px; border-radius: 8px; display: inline-block; }
.score-badge.excellent { background: rgba(52,211,153,0.15); color: #34d399; }
.score-badge.good { background: rgba(129,140,248,0.15); color: #818cf8; }
.score-badge.pass { background: rgba(251,191,36,0.15); color: #fbbf24; }
.score-badge.fail { background: rgba(248,113,113,0.15); color: #f87171; }
.grade-level { font-size: 12px; font-weight: 600; }
.grade-level.excellent { color: #34d399; }
.grade-level.good { color: #818cf8; }
.grade-level.pass { color: #fbbf24; }
.grade-level.fail { color: #f87171; }
.pending-badge { font-size: 12px; color: #f59e0b; background: rgba(245,158,11,0.1); padding: 3px 10px; border-radius: 8px; font-weight: 600; }
.comment-cell { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.content-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.edit-btn { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; padding: 5px 14px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.edit-btn:hover { background: rgba(99,102,241,0.25); }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp, .inp-sel { background: rgba(255,255,255,0.06); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; box-sizing: border-box; }
.inp:disabled, .inp-sel:disabled { opacity: 0.5; }
.ta { background: rgba(255,255,255,0.06); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; box-sizing: border-box; }
.sub-content-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; color: var(--text-secondary); font-size: 13px; line-height: 1.6; min-height: 60px; max-height: 160px; overflow-y: auto; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #059669, #10b981); border: none; color: white; cursor: pointer; font-weight: 600; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
