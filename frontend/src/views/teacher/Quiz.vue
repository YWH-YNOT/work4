<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">课堂测验</h1>
        <p class="page-sub">按课程创建课堂测验、维护题目、发布测验，并查看作答统计和未完成学生。</p>
      </div>
      <button @click="openCreateQuiz" class="primary-btn">新建课堂测验</button>
    </div>

    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadQuizzes" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <div class="summary-strip">
      <div><span>课堂测验总数</span><strong>{{ quizzes.length }}</strong></div>
      <div><span>已发布</span><strong>{{ publishedCount }}</strong></div>
      <div><span>题目总数</span><strong>{{ questionTotal }}</strong></div>
      <div><span>已截止</span><strong>{{ closedCount }}</strong></div>
    </div>

    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="quizzes.length===0" class="empty">暂无课堂测验，点击右上角新建</div>
    <div v-else class="quiz-list">
      <article v-for="qz in quizzes" :key="qz.id" :class="['quiz-card', qz.status]">
        <div class="quiz-head">
          <div>
            <div class="course-name">{{ qz.course_name || courseMap[qz.course_id] }}</div>
            <h2>{{ qz.title }}</h2>
          </div>
          <span :class="['status-pill', qz.status]">{{ qz.status_label }}</span>
        </div>
        <div class="quiz-meta">
          <span>{{ qz.question_count }} 道题</span>
          <span v-if="qz.session_index">第 {{ qz.session_index }} 次课</span>
          <span v-if="qz.time_limit">{{ qz.time_limit }} 分钟</span>
          <span v-if="qz.start_at">开始 {{ fmt(qz.start_at) }}</span>
          <span v-if="qz.end_at">截止 {{ fmt(qz.end_at) }}</span>
        </div>
        <div class="quiz-actions">
          <button @click="openEditQuiz(qz)" class="outline-btn">编辑</button>
          <button @click="openAddQuestion(qz)" class="outline-btn">添加题目</button>
          <button @click="openStats(qz)" class="outline-btn">管理/统计</button>
          <button v-if="qz.status !== 'published'" @click="setStatus(qz, 'published')" class="publish-btn">发布</button>
          <button v-if="qz.status === 'published'" @click="setStatus(qz, 'closed')" class="close-btn">截止</button>
          <button v-if="qz.status !== 'draft'" @click="setStatus(qz, 'draft')" class="ghost-btn">转为草稿</button>
          <button @click="deleteQuiz(qz)" class="delete-btn">删除</button>
        </div>
      </article>
    </div>

    <el-dialog v-model="showCreateQuiz" :title="editingQuiz ? '编辑课堂测验' : '新建课堂测验'" width="560px">
      <div class="dialog-form">
        <label>所属课程</label>
        <select v-model.number="quizForm.course_id" class="inp-sel">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label>课堂测验名称</label>
        <input v-model="quizForm.title" class="inp" placeholder="如：第 6 次课随堂测验" />
        <label>关联课次</label>
        <input v-model.number="quizForm.session_index" type="number" min="1" class="inp" placeholder="如：6，对应学生端第 6 次课测验格" />
        <label>状态</label>
        <select v-model="quizForm.status" class="inp-sel">
          <option value="draft">草稿</option>
          <option value="published">直接发布</option>
        </select>
        <label>时间限制（分钟，可选）</label>
        <input v-model.number="quizForm.time_limit" type="number" min="1" class="inp" placeholder="留空不限时" />
        <div class="time-grid">
          <div>
            <label>开始时间</label>
            <input v-model="quizForm.start_at" type="datetime-local" class="inp" />
          </div>
          <div>
            <label>截止时间</label>
            <input v-model="quizForm.end_at" type="datetime-local" class="inp" />
          </div>
        </div>
        <div class="dialog-actions">
          <button @click="showCreateQuiz=false" class="cancel-btn">取消</button>
          <button @click="saveQuiz" :disabled="saving" class="confirm-btn">{{ saving ? '保存中...' : quizSubmitText }}</button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showAddQ" :title="`${editingQuestion ? '编辑题目' : '添加题目'} - ${currentQuiz?.title}`" width="600px">
      <div class="dialog-form">
        <label>题目内容</label>
        <textarea v-model="qForm.question" class="ta" rows="3" placeholder="输入题目文字"></textarea>
        <label>选项（每行一个，至少 2 项）</label>
        <div class="options-list">
          <div v-for="(_, i) in qForm.options" :key="i" class="option-row">
            <span>{{ String.fromCharCode(65+i) }}.</span>
            <input v-model="qForm.options[i]" class="inp opt-inp" :placeholder="`选项 ${String.fromCharCode(65+i)}`" />
            <button v-if="qForm.options.length>2" @click="removeOption(i)" class="mini-delete">删除</button>
          </div>
          <button v-if="qForm.options.length<6" @click="addOption" class="ghost-btn wide">添加选项</button>
        </div>
        <label>正确答案</label>
        <select v-model.number="qForm.correct_option" class="inp-sel">
          <option v-for="(opt, i) in qForm.options" :key="i" :value="i">
            {{ String.fromCharCode(65+i) }}. {{ opt || '未填写' }}
          </option>
        </select>
        <div class="dialog-actions">
          <button @click="showAddQ=false" class="cancel-btn">取消</button>
          <button @click="saveQuestion" :disabled="saving" class="confirm-btn">保存题目</button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showStats" :title="`课堂测验统计 - ${statsQuiz?.title || ''}`" width="860px">
      <div v-if="stats" class="stats-panel">
        <div class="stat-row">
          <div class="stat-item"><strong>{{ stats.students_count || 0 }}</strong><span>课程学生</span></div>
          <div class="stat-item"><strong>{{ stats.attempts_count }}</strong><span>已作答</span></div>
          <div class="stat-item"><strong>{{ percentText(stats.completion_rate) }}</strong><span>完成率</span></div>
          <div class="stat-item"><strong>{{ valueText(stats.average_score) }}</strong><span>平均分</span></div>
          <div class="stat-item"><strong>{{ stats.weak_questions.length }}</strong><span>薄弱题</span></div>
        </div>

        <div class="manage-grid">
          <section>
            <h3>题目管理</h3>
            <div v-if="quizDetail?.questions?.length === 0" class="empty compact">暂无题目</div>
            <div v-for="(q, index) in quizDetail?.questions || []" :key="q.id" class="question-card">
              <div class="question-top">
                <strong>第 {{ Number(index) + 1 }} 题</strong>
                <div class="question-actions">
                  <button class="mini-edit" @click="openEditQuestion(q)">编辑</button>
                  <button class="mini-delete" @click="deleteQuestion(q.id)">删除</button>
                </div>
              </div>
              <p>{{ q.question }}</p>
              <div class="option-line" v-for="(opt, i) in q.options || []" :key="i" :class="{ correct: Number(i) === q.correct_option }">
                {{ String.fromCharCode(65 + Number(i)) }}. {{ opt }}
              </div>
            </div>
          </section>
          <section>
            <h3>未作答学生</h3>
            <div v-if="stats.missing_students.length === 0" class="empty compact">全部学生已完成</div>
            <div v-for="stu in stats.missing_students" :key="stu.student_id" class="student-row">
              <strong>{{ stu.student_name }}</strong>
              <span>{{ stu.student_username }}</span>
            </div>
          </section>
        </div>

        <section class="analysis-list">
          <h3>题目统计</h3>
          <div v-if="stats.questions.length === 0" class="empty compact">暂无题目统计</div>
          <article v-for="(q, index) in stats.questions" :key="q.id" class="analysis-card" :class="{ weak: q.weak }">
            <div class="analysis-head">
              <strong>第 {{ Number(index) + 1 }} 题 · {{ q.question }}</strong>
              <span>{{ q.correct_rate ?? '--' }}%</span>
            </div>
            <div class="answer-line">正确答案：{{ String.fromCharCode(65 + Number(q.correct_option)) }}. {{ q.correct_answer || '未设置' }}</div>
            <div class="option-bars">
              <div v-for="opt in q.options" :key="opt.index" class="option-stat">
                <span :class="{ correct: opt.is_correct }">{{ opt.label }}</span>
                <div class="bar"><i :class="{ correct: opt.is_correct }" :style="{ width: `${opt.rate}%` }"></i></div>
                <em>{{ opt.count }} 人 · {{ opt.rate }}%</em>
              </div>
            </div>
          </article>
        </section>
      </div>
      <div v-else class="empty">加载中...</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const courses = ref<any[]>([])
const quizzes = ref<any[]>([])
const selectedCourse = ref<number|''>('')
const loading = ref(false)
const saving = ref(false)
const showCreateQuiz = ref(false)
const showAddQ = ref(false)
const showStats = ref(false)
const currentQuiz = ref<any>(null)
const statsQuiz = ref<any>(null)
const stats = ref<any>(null)
const quizDetail = ref<any>(null)
const editingQuiz = ref<any>(null)
const editingQuestion = ref<any>(null)

const quizForm = ref({ course_id: 0, title: '', session_index: null as number|null, time_limit: null as number|null, start_at: '', end_at: '', status: 'draft' })
const qForm = ref({ question: '', options: ['', ''] as string[], correct_option: 0 })
const courseMap = computed(() => Object.fromEntries(courses.value.map((c: any) => [c.id, c.name])))
const publishedCount = computed(() => quizzes.value.filter((q: any) => q.status === 'published').length)
const closedCount = computed(() => quizzes.value.filter((q: any) => q.status === 'closed').length)
const questionTotal = computed(() => quizzes.value.reduce((sum: number, q: any) => sum + Number(q.question_count || 0), 0))
const quizSubmitText = computed(() => editingQuiz.value ? '保存修改' : '创建课堂测验')

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : Math.round(v)
const toDatetimeLocal = (value?: string | null) => {
  if (!value) return ''
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

function addOption() { if (qForm.value.options.length < 6) qForm.value.options.push('') }
function removeOption(i: number) {
  qForm.value.options.splice(i, 1)
  if (qForm.value.correct_option >= qForm.value.options.length) qForm.value.correct_option = 0
}

async function loadQuizzes() {
  loading.value = true
  try {
    let url = '/api/v1/quiz/'
    if (selectedCourse.value) url += `?course_id=${selectedCourse.value}`
    const r = await axios.get(url)
    quizzes.value = r.data
  } finally { loading.value = false }
}

function resetQuizForm() {
  quizForm.value = { course_id: courses.value[0]?.id || 0, title: '', session_index: null, time_limit: null, start_at: '', end_at: '', status: 'draft' }
}

function openCreateQuiz() {
  editingQuiz.value = null
  resetQuizForm()
  showCreateQuiz.value = true
}

function openEditQuiz(qz: any) {
  editingQuiz.value = qz
  quizForm.value = {
    course_id: qz.course_id,
    title: qz.title || '',
    session_index: qz.session_index ?? null,
    time_limit: qz.time_limit ?? null,
    start_at: toDatetimeLocal(qz.start_at),
    end_at: toDatetimeLocal(qz.end_at),
    status: qz.status || 'draft',
  }
  showCreateQuiz.value = true
}

async function saveQuiz() {
  if (!quizForm.value.course_id || !quizForm.value.title.trim()) {
    alert('请选择课程并填写课堂测验名称')
    return
  }
  saving.value = true
  try {
    const payload: any = {
      course_id: quizForm.value.course_id,
      title: quizForm.value.title.trim(),
      session_index: quizForm.value.session_index || null,
      time_limit: quizForm.value.time_limit || null,
      start_at: quizForm.value.start_at ? new Date(quizForm.value.start_at).toISOString() : null,
      end_at: quizForm.value.end_at ? new Date(quizForm.value.end_at).toISOString() : null,
      status: quizForm.value.status,
    }
    if (editingQuiz.value) {
      await axios.patch(`/api/v1/quiz/${editingQuiz.value.id}`, payload)
    } else {
      await axios.post('/api/v1/quiz/', payload)
    }
    showCreateQuiz.value = false
    editingQuiz.value = null
    resetQuizForm()
    await loadQuizzes()
  } finally { saving.value = false }
}

async function setStatus(qz: any, status: string) {
  await axios.patch(`/api/v1/quiz/${qz.id}/status`, { status })
  await loadQuizzes()
  if (statsQuiz.value?.id === qz.id) await openStats(qz)
}

async function deleteQuiz(qz: any) {
  if (!window.confirm(`确认删除测验「${qz.title}」？`)) return
  await axios.delete(`/api/v1/quiz/${qz.id}`)
  await loadQuizzes()
}

function openAddQuestion(qz: any) {
  currentQuiz.value = qz
  editingQuestion.value = null
  qForm.value = { question: '', options: ['', ''], correct_option: 0 }
  showAddQ.value = true
}

function openEditQuestion(question: any) {
  currentQuiz.value = statsQuiz.value
  editingQuestion.value = question
  qForm.value = {
    question: question.question || '',
    options: [...(question.options || ['', ''])],
    correct_option: Number(question.correct_option || 0),
  }
  while (qForm.value.options.length < 2) qForm.value.options.push('')
  showAddQ.value = true
}

async function saveQuestion() {
  const opts = qForm.value.options.filter(o => o.trim())
  if (opts.length < 2) { alert('至少填写 2 个选项'); return }
  if (!qForm.value.question.trim()) { alert('请填写题目内容'); return }
  saving.value = true
  try {
    const payload = {
      question: qForm.value.question,
      options: opts,
      correct_option: qForm.value.correct_option,
    }
    if (editingQuestion.value) {
      await axios.patch(`/api/v1/quiz/questions/${editingQuestion.value.id}`, payload)
    } else {
      await axios.post(`/api/v1/quiz/${currentQuiz.value.id}/questions`, payload)
    }
    showAddQ.value = false
    if (statsQuiz.value?.id) await openStats(statsQuiz.value)
    await loadQuizzes()
  } finally { saving.value = false }
}

async function openStats(qz: any) {
  statsQuiz.value = qz
  stats.value = null
  quizDetail.value = null
  showStats.value = true
  const [detail, analysis] = await Promise.all([
    axios.get(`/api/v1/quiz/${qz.id}`),
    axios.get(`/api/v1/quiz/${qz.id}/analysis`),
  ])
  quizDetail.value = detail.data
  stats.value = analysis.data
}

async function deleteQuestion(questionId: number) {
  if (!window.confirm('确认删除这道题？')) return
  await axios.delete(`/api/v1/quiz/questions/${questionId}`)
  await openStats(statsQuiz.value)
  await loadQuizzes()
}

onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my')
  courses.value = c.data
  if (c.data.length) quizForm.value.course_id = c.data[0].id
  await loadQuizzes()
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 12px; }
.summary-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-strip div { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 13px; box-shadow: 0 8px 20px rgba(15,47,100,.05); }
.summary-strip span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.summary-strip strong { color: #0f2f64; font-size: 24px; }
.sel, .inp, .inp-sel, .ta { background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; outline: none; padding: 10px 12px; }
.sel { min-width: 220px; }
.primary-btn, .confirm-btn, .publish-btn { background: #0b63b6; color: white; border: none; border-radius: 8px; padding: 9px 16px; cursor: pointer; font-weight: 800; }
.quiz-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.quiz-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.quiz-card.draft { background: #f7fafc; border-style: dashed; box-shadow: none; opacity: .78; }
.quiz-card.closed { background: #fffdf7; border-color: #f0dca8; }
.quiz-head { display: flex; justify-content: space-between; gap: 14px; align-items: flex-start; }
.course-name { color: #0b63b6; font-size: 12px; margin-bottom: 6px; font-weight: 800; }
.quiz-head h2 { color: #0f2f64; font-size: 18px; margin: 0; line-height: 1.4; }
.status-pill { border-radius: 8px; padding: 5px 8px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.status-pill.draft { color: #5b6f92; background: #edf3fb; }
.status-pill.published { color: #0b7d56; background: #e8f7f0; }
.status-pill.closed { color: #cf3434; background: #fff0ef; }
.quiz-meta { display: flex; flex-wrap: wrap; gap: 8px 12px; color: #5b6f92; font-size: 12px; margin: 12px 0; }
.quiz-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.outline-btn, .ghost-btn, .close-btn, .delete-btn, .cancel-btn, .mini-delete { border-radius: 8px; padding: 7px 11px; cursor: pointer; font-weight: 800; }
.outline-btn { background: #ffffff; border: 1px solid #9ec8f1; color: #0b63b6; }
.ghost-btn { background: #f8fbff; border: 1px solid #d9e7f7; color: #5b6f92; }
.close-btn { background: #fff2d9; border: 1px solid #f0c77c; color: #9a5a00; }
.delete-btn, .mini-delete { background: #fff4f2; border: 1px solid #ffd5cf; color: #cf3434; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 24px; text-align: center; background: #f8fbff; }
.empty.compact { padding: 14px; font-size: 13px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { color: #5b6f92; font-size: 13px; font-weight: 700; }
.time-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.ta { resize: vertical; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.cancel-btn { background: #ffffff; border: 1px solid #c8ddf4; color: #5b6f92; }
.option-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.option-row span { color: #5b6f92; min-width: 22px; }
.opt-inp { flex: 1; }
.wide { width: 100%; }
.stats-panel { display: flex; flex-direction: column; gap: 16px; }
.stat-row { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.stat-item { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 12px; }
.stat-item strong { display: block; color: #0f2f64; font-size: 24px; }
.stat-item span { color: #5b6f92; font-size: 12px; }
.manage-grid { display: grid; grid-template-columns: 1.35fr .65fr; gap: 14px; }
.manage-grid h3, .analysis-list h3 { color: #0f2f64; font-size: 15px; margin: 0 0 10px; }
.question-card, .analysis-card, .student-row { background: #ffffff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 12px; margin-bottom: 10px; }
.question-top, .analysis-head, .student-row, .option-stat { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
.question-actions { display: flex; align-items: center; gap: 8px; }
.mini-edit { background: #ffffff; border: 1px solid #9ec8f1; color: #0b63b6; border-radius: 8px; padding: 7px 11px; cursor: pointer; font-weight: 800; }
.question-card p, .answer-line { color: #5b6f92; line-height: 1.6; font-size: 13px; }
.option-line { color: #5b6f92; font-size: 12px; margin-top: 6px; }
.option-line.correct { color: #0b7d56; }
.student-row strong, .analysis-head strong { color: #0f2f64; }
.student-row span { color: #5b6f92; font-size: 12px; }
.analysis-card.weak { border-color: #ffd5cf; background: #fff4f2; }
.analysis-head span { color: #0b63b6; font-weight: 900; }
.option-stat { margin-top: 8px; }
.option-stat span { width: 22px; color: #5b6f92; font-weight: 800; }
.option-stat span.correct { color: #0b7d56; }
.bar { flex: 1; height: 7px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.bar i { display: block; height: 100%; background: #54a4ee; border-radius: inherit; }
.bar i.correct { background: #14a46f; }
.option-stat em { width: 86px; text-align: right; color: #5b6f92; font-size: 12px; font-style: normal; }
@media (max-width: 1180px) {
  .quiz-list, .manage-grid { grid-template-columns: 1fr; }
  .stat-row, .summary-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
