<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">我的测验</h1>
      <p class="page-sub">完成各课程在线测验</p>
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
    <div v-else-if="quizzes.length===0" class="empty">暂无测验</div>
    <div v-else class="quiz-list">
      <div v-for="qz in quizzes" :key="qz.id" class="quiz-card">
        <div class="quiz-left">
          <div class="quiz-icon">📝</div>
          <div>
            <div class="quiz-title">{{ qz.title }}</div>
            <div class="quiz-meta">
              <span class="meta-tag">{{ qz.question_count }} 道题</span>
              <span class="meta-tag" v-if="qz.time_limit">⏱ {{ qz.time_limit }} 分钟</span>
            </div>
          </div>
        </div>
        <div class="quiz-right">
          <span v-if="qz.attempted" class="badge done">已完成 {{ qz.my_score }} 分</span>
          <button v-else @click="startQuiz(qz)" class="start-btn">开始作答</button>
        </div>
      </div>
    </div>

    <!-- 作答弹窗 -->
    <el-dialog
      v-model="showQuiz"
      :title="currentQuiz?.title"
      width="680px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="quizDetail" class="quiz-body">
        <!-- 倒计时 -->
        <div v-if="timeLeft !== null" class="timer" :class="timeLeft < 60 ? 'urgent' : ''">
          ⏱ {{ formatTime(timeLeft) }}
        </div>

        <div class="progress-bar">
          <div class="progress-fill" :style="{width: `${(currentQ+1)/quizDetail.questions.length*100}%`}"></div>
        </div>
        <div class="q-counter">第 {{ currentQ+1 }} / {{ quizDetail.questions.length }} 题</div>

        <!-- 题目 -->
        <div class="question-block">
          <div class="q-text">{{ quizDetail.questions[currentQ].question }}</div>
          <div class="options">
            <div
              v-for="(opt, i) in quizDetail.questions[currentQ].options"
              :key="i"
              :class="['opt-item', answers[quizDetail.questions[currentQ].id] === i && 'selected']"
              @click="selectAnswer(quizDetail.questions[currentQ].id, i)"
            >
              <span class="opt-letter">{{ String.fromCharCode(65+i) }}</span>
              <span>{{ opt }}</span>
            </div>
          </div>
        </div>

        <!-- 导航 -->
        <div class="nav-row">
          <button @click="currentQ--" :disabled="currentQ===0" class="nav-btn">← 上一题</button>
          <div class="q-dots">
            <span
              v-for="(q, i) in quizDetail.questions" :key="q.id"
              :class="['dot', answers[q.id]!==undefined && 'answered', i===currentQ && 'current']"
              @click="currentQ=i"
            ></span>
          </div>
          <button v-if="currentQ < quizDetail.questions.length-1" @click="currentQ++" class="nav-btn">下一题 →</button>
          <button v-else @click="confirmSubmit" :disabled="submitting" class="submit-btn">
            {{ submitting ? '提交中...' : '提交答卷' }}
          </button>
        </div>
      </div>
      <div v-else class="empty">加载题目中...</div>
    </el-dialog>

    <!-- 结果弹窗 -->
    <el-dialog v-model="showResult" title="测验结果" width="400px" :close-on-click-modal="false">
      <div class="result-body">
        <div class="result-score" :class="scoreClass(result?.score)">{{ result?.score }}</div>
        <div class="result-label">{{ scoreLabel(result?.score) }}</div>
        <div class="result-detail">
          ✅ 答对 {{ result?.correct }} / {{ result?.total }} 题
        </div>
        <button @click="showResult=false; loadQuizzes()" class="done-btn">完成</button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const courses = ref<any[]>([])
const quizzes = ref<any[]>([])
const selectedCourse = ref<number|''>('')
const loading = ref(false)
const showQuiz = ref(false)
const showResult = ref(false)
const currentQuiz = ref<any>(null)
const quizDetail = ref<any>(null)
const answers = ref<Record<number, number>>({})  // {question_id: selected_index}
const currentQ = ref(0)
const submitting = ref(false)
const result = ref<any>(null)
const timeLeft = ref<number|null>(null)
let timer: ReturnType<typeof setInterval> | null = null

const formatTime = (s: number) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`
const scoreClass = (s?: number) => !s ? '' : s>=90?'excellent':s>=75?'good':s>=60?'pass':'fail'
const scoreLabel = (s?: number) => !s ? '' : s>=90?'优秀':s>=75?'良好':s>=60?'及格':'需要加油'

async function loadQuizzes() {
  loading.value = true
  try {
    let url = '/api/v1/quiz/'
    if (selectedCourse.value) url += `?course_id=${selectedCourse.value}`
    const r = await axios.get(url)
    // 后端已返回 attempted 和 my_score 字段（针对 student 角色）
    quizzes.value = r.data
  } finally { loading.value = false }
}

async function startQuiz(qz: any) {
  currentQuiz.value = qz
  answers.value = {}
  currentQ.value = 0
  showQuiz.value = true
  quizDetail.value = null
  try {
    const r = await axios.get(`/api/v1/quiz/${qz.id}`)
    quizDetail.value = r.data
    // 启动计时器
    if (qz.time_limit) {
      timeLeft.value = qz.time_limit * 60
      timer = setInterval(() => {
        if (timeLeft.value !== null && timeLeft.value > 0) {
          timeLeft.value -= 1
        } else {
          clearTimer()
          confirmSubmit()
        }
      }, 1000)
    }
  } catch(e: any) {
    alert(e.response?.data?.detail || '加载失败')
    showQuiz.value = false
  }
}

function selectAnswer(questionId: number, optionIndex: number) {
  answers.value[questionId] = optionIndex
}

async function confirmSubmit() {
  const unanswered = quizDetail.value.questions.filter((q: any) => answers.value[q.id] === undefined).length
  if (unanswered > 0) {
    if (!confirm(`还有 ${unanswered} 道题未作答，确认提交？`)) return
  }
  submitting.value = true
  clearTimer()
  try {
    // 转换答案格式：{question_id_str: selected_index}
    const payload: Record<string, number> = {}
    for (const [qId, ans] of Object.entries(answers.value)) {
      payload[String(qId)] = ans
    }
    const r = await axios.post(`/api/v1/quiz/${currentQuiz.value.id}/submit`, { answers: payload })
    result.value = r.data
    showQuiz.value = false
    showResult.value = true
  } catch(e: any) {
    alert(e.response?.data?.detail || '提交失败')
  } finally { submitting.value = false }
}

function clearTimer() {
  if (timer) { clearInterval(timer); timer = null }
  timeLeft.value = null
}

onUnmounted(clearTimer)

onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my')
  courses.value = c.data
  await loadQuizzes()
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.filter-bar { margin-bottom: 20px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.empty { color: var(--text-secondary); text-align: center; padding: 60px; font-size: 15px; }
/* 测验列表 */
.quiz-list { display: flex; flex-direction: column; gap: 12px; }
.quiz-card { display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 16px; padding: 20px 24px; transition: border-color 0.2s; }
.quiz-card:hover { border-color: rgba(99,102,241,0.3); }
.quiz-left { display: flex; align-items: center; gap: 16px; }
.quiz-icon { font-size: 28px; }
.quiz-title { font-size: 16px; font-weight: 700; color: var(--text-main); margin-bottom: 6px; }
.quiz-meta { display: flex; gap: 10px; }
.meta-tag { font-size: 12px; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 2px 10px; border-radius: 8px; }
.badge.done { font-size: 13px; font-weight: 700; color: #34d399; background: rgba(52,211,153,0.1); padding: 6px 16px; border-radius: 20px; }
.start-btn { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border: none; border-radius: 12px; padding: 9px 22px; cursor: pointer; font-weight: 700; font-size: 14px; transition: all 0.2s; }
.start-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,0.4); }
/* 作答弹窗 */
.quiz-body { display: flex; flex-direction: column; gap: 16px; }
.timer { text-align: right; font-size: 18px; font-weight: 700; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.timer.urgent { color: #f87171; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
.progress-bar { height: 4px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #7c3aed); border-radius: 4px; transition: width 0.3s; }
.q-counter { font-size: 12px; color: var(--text-secondary); text-align: center; }
.question-block { background: rgba(255,255,255,0.02); border: 1px solid rgba(99,102,241,0.1); border-radius: 14px; padding: 20px; }
.q-text { font-size: 16px; font-weight: 600; color: var(--text-main); line-height: 1.7; margin-bottom: 16px; }
.options { display: flex; flex-direction: column; gap: 10px; }
.opt-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; cursor: pointer; transition: all 0.18s; }
.opt-item:hover { background: rgba(99,102,241,0.08); border-color: rgba(99,102,241,0.3); }
.opt-item.selected { background: rgba(99,102,241,0.15); border-color: #6366f1; }
.opt-letter { font-size: 13px; font-weight: 700; color: #818cf8; background: rgba(99,102,241,0.12); width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.opt-item.selected .opt-letter { background: #6366f1; color: white; }
.opt-item span:last-child { font-size: 14px; color: var(--text-secondary); }
.opt-item.selected span:last-child { color: #c7d2fe; }
/* 导航 */
.nav-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.nav-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); border-radius: 10px; padding: 8px 16px; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.nav-btn:hover:not(:disabled) { background: rgba(255,255,255,0.1); color: var(--text-main); }
.nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.q-dots { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: rgba(255,255,255,0.1); cursor: pointer; transition: all 0.15s; flex-shrink: 0; }
.dot.answered { background: rgba(99,102,241,0.5); }
.dot.current { background: #6366f1; transform: scale(1.3); }
.submit-btn { background: linear-gradient(135deg, #059669, #10b981); border: none; color: white; border-radius: 10px; padding: 9px 20px; cursor: pointer; font-weight: 700; font-size: 14px; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
/* 结果 */
.result-body { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 20px 0; }
.result-score { font-size: 72px; font-weight: 900; line-height: 1; }
.result-score.excellent { color: #34d399; }
.result-score.good { color: #818cf8; }
.result-score.pass { color: #fbbf24; }
.result-score.fail { color: #f87171; }
.result-label { font-size: 18px; font-weight: 700; color: var(--text-secondary); }
.result-detail { font-size: 14px; color: var(--text-secondary); }
.done-btn { margin-top: 8px; background: linear-gradient(135deg, #6366f1, #7c3aed); border: none; color: white; border-radius: 12px; padding: 10px 32px; cursor: pointer; font-weight: 700; font-size: 15px; }
</style>
