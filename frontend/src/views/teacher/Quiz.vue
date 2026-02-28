<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">测验管理</h1>
      <button @click="showCreateQuiz=true" class="create-btn">＋ 新建测验</button>
    </div>

    <!-- 课程筛选 -->
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadQuizzes" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <!-- 测验列表 -->
    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="quizzes.length===0" class="empty">暂无测验，点击右上角新建</div>
    <div v-else class="quiz-list">
      <div v-for="qz in quizzes" :key="qz.id" class="quiz-card">
        <div class="quiz-info">
          <div class="quiz-title">{{ qz.title }}</div>
          <div class="quiz-meta">
            <span class="meta-item">📋 {{ qz.question_count }} 道题</span>
            <span class="meta-item" v-if="qz.time_limit">⏱ {{ qz.time_limit }} 分钟</span>
            <span class="meta-item" v-if="qz.start_at">开始: {{ fmtDt(qz.start_at) }}</span>
            <span class="meta-item" v-if="qz.end_at">截止: {{ fmtDt(qz.end_at) }}</span>
          </div>
        </div>
        <div class="quiz-actions">
          <button @click="openAddQuestion(qz)" class="add-q-btn">＋ 添加题目</button>
          <button @click="loadStats(qz)" class="stats-btn">📊 统计</button>
        </div>
      </div>
    </div>

    <!-- 创建测验对话框 -->
    <el-dialog v-model="showCreateQuiz" title="新建测验" width="480px">
      <div class="dialog-form">
        <label>所属课程</label>
        <select v-model="quizForm.course_id" class="inp-sel">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label>测验名称</label>
        <input v-model="quizForm.title" class="inp" placeholder="如：第三章随堂测验"/>
        <label>时间限制（分钟，留空不限时）</label>
        <input v-model.number="quizForm.time_limit" type="number" min="1" class="inp" placeholder="可选"/>
        <div class="dialog-actions">
          <button @click="showCreateQuiz=false" class="cancel-btn">取消</button>
          <button @click="createQuiz" :disabled="saving" class="confirm-btn">{{ saving?'创建中...':'创建测验' }}</button>
        </div>
      </div>
    </el-dialog>

    <!-- 添加题目对话框 -->
    <el-dialog v-model="showAddQ" :title="`添加题目 — ${currentQuiz?.title}`" width="560px">
      <div class="dialog-form">
        <label>题目内容</label>
        <textarea v-model="qForm.question" class="ta" rows="3" placeholder="输入题目文字..."></textarea>
        <label>选项（每行一个，至少 2 项）</label>
        <div class="options-list">
          <div v-for="(opt, i) in qForm.options" :key="i" class="option-row">
            <span class="opt-label">{{ String.fromCharCode(65+i) }}.</span>
            <input v-model="qForm.options[i]" class="inp opt-inp" :placeholder="`选项 ${String.fromCharCode(65+i)}`"/>
            <button v-if="qForm.options.length>2" @click="removeOption(i)" class="del-opt-btn">✕</button>
          </div>
          <button v-if="qForm.options.length<6" @click="addOption" class="add-opt-btn">＋ 添加选项</button>
        </div>
        <label>正确答案</label>
        <select v-model.number="qForm.correct_option" class="inp-sel">
          <option v-for="(opt, i) in qForm.options" :key="i" :value="i">
            {{ String.fromCharCode(65+i) }}. {{ opt || '(未填)' }}
          </option>
        </select>
        <div class="dialog-actions">
          <button @click="showAddQ=false" class="cancel-btn">取消</button>
          <button @click="addQuestion" :disabled="saving" class="confirm-btn">添加题目</button>
        </div>
      </div>
    </el-dialog>

    <!-- 答题统计对话框 -->
    <el-dialog v-model="showStats" :title="`答题统计 — ${statsQuiz?.title}`" width="400px">
      <div v-if="stats" class="stats-panel">
        <div class="stat-row">
          <div class="stat-item">
            <div class="stat-val">{{ stats.count }}</div>
            <div class="stat-lab">参与人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-val" :class="scoreClass(stats.avg)">{{ stats.avg }}</div>
            <div class="stat-lab">平均分</div>
          </div>
          <div class="stat-item">
            <div class="stat-val excellent">{{ stats.max }}</div>
            <div class="stat-lab">最高分</div>
          </div>
        </div>
        <div v-if="stats.count===0" class="no-stats">暂无学生作答</div>
      </div>
      <div v-else class="empty">加载中...</div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

const quizForm = ref({ course_id: 0, title: '', time_limit: null as number|null })
const qForm = ref({ question: '', options: ['', ''] as string[], correct_option: 0 })

const fmtDt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
const scoreClass = (s: number) => s >= 90 ? 'excellent' : s >= 75 ? 'good' : s >= 60 ? 'pass' : 'fail'

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

async function createQuiz() {
  saving.value = true
  try {
    const payload: any = { course_id: quizForm.value.course_id, title: quizForm.value.title }
    if (quizForm.value.time_limit) payload.time_limit = quizForm.value.time_limit
    await axios.post('/api/v1/quiz/', payload)
    showCreateQuiz.value = false
    quizForm.value = { course_id: courses.value[0]?.id || 0, title: '', time_limit: null }
    await loadQuizzes()
  } catch(e: any) { alert(e.response?.data?.detail || '创建失败') }
  finally { saving.value = false }
}

function openAddQuestion(qz: any) {
  currentQuiz.value = qz
  qForm.value = { question: '', options: ['', ''], correct_option: 0 }
  showAddQ.value = true
}

async function addQuestion() {
  const opts = qForm.value.options.filter(o => o.trim())
  if (opts.length < 2) { alert('至少填写 2 个选项'); return }
  if (!qForm.value.question.trim()) { alert('请填写题目内容'); return }
  saving.value = true
  try {
    await axios.post(`/api/v1/quiz/${currentQuiz.value.id}/questions`, {
      question: qForm.value.question,
      options: opts,
      correct_option: qForm.value.correct_option
    })
    qForm.value = { question: '', options: ['', ''], correct_option: 0 }
    await loadQuizzes()
    alert(`✅ 题目已添加！该测验现有 ${quizzes.value.find(q=>q.id===currentQuiz.value.id)?.question_count} 道题`)
  } catch(e: any) { alert(e.response?.data?.detail || '添加失败') }
  finally { saving.value = false }
}

async function loadStats(qz: any) {
  statsQuiz.value = qz
  stats.value = null
  showStats.value = true
  try {
    const r = await axios.get(`/api/v1/quiz/${qz.id}/stats`)
    stats.value = r.data
  } catch {}
}

onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my')
  courses.value = c.data
  if (c.data.length) quizForm.value.course_id = c.data[0].id
  await loadQuizzes()
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.create-btn { background: linear-gradient(135deg, #7c3aed, #6366f1); color: white; border: none; border-radius: 10px; padding: 9px 20px; cursor: pointer; font-weight: 600; font-size: 14px; }
.filter-bar { margin-bottom: 20px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.empty { color: var(--text-secondary); text-align: center; padding: 40px; font-size: 15px; }
.quiz-list { display: flex; flex-direction: column; gap: 12px; }
.quiz-card { display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 14px; padding: 18px 22px; transition: border-color 0.2s; }
.quiz-card:hover { border-color: rgba(99,102,241,0.3); }
.quiz-title { font-size: 16px; font-weight: 600; color: var(--text-main); margin-bottom: 8px; }
.quiz-meta { display: flex; gap: 14px; flex-wrap: wrap; }
.meta-item { font-size: 13px; color: var(--text-secondary); }
.quiz-actions { display: flex; gap: 8px; flex-shrink: 0; }
.add-q-btn { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; padding: 7px 16px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.add-q-btn:hover { background: rgba(99,102,241,0.25); }
.stats-btn { background: rgba(16,185,129,0.1); color: #34d399; border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.stats-btn:hover { background: rgba(16,185,129,0.2); }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp, .inp-sel { background: rgba(255,255,255,0.06); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; box-sizing: border-box; }
.ta { background: rgba(255,255,255,0.06); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; box-sizing: border-box; }
.options-list { display: flex; flex-direction: column; gap: 8px; }
.option-row { display: flex; align-items: center; gap: 8px; }
.opt-label { font-size: 14px; font-weight: 700; color: #818cf8; min-width: 20px; }
.opt-inp { flex: 1; }
.del-opt-btn { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.2); border-radius: 6px; padding: 6px 10px; cursor: pointer; font-size: 12px; flex-shrink: 0; }
.add-opt-btn { align-self: flex-start; background: rgba(99,102,241,0.1); color: #818cf8; border: 1px dashed rgba(99,102,241,0.3); border-radius: 8px; padding: 7px 16px; cursor: pointer; font-size: 13px; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #7c3aed, #6366f1); border: none; color: white; cursor: pointer; font-weight: 600; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.stats-panel { padding: 10px 0; }
.stat-row { display: flex; gap: 16px; justify-content: center; }
.stat-item { flex: 1; text-align: center; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 20px 10px; }
.stat-val { font-size: 36px; font-weight: 900; color: var(--text-main); line-height: 1; margin-bottom: 8px; }
.stat-val.excellent { color: #34d399; }
.stat-val.good { color: #818cf8; }
.stat-val.pass { color: #fbbf24; }
.stat-val.fail { color: #f87171; }
.stat-lab { font-size: 12px; color: var(--text-secondary); }
.no-stats { text-align: center; color: var(--text-secondary); margin-top: 16px; font-size: 14px; }
</style>
