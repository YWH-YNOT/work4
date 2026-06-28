<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">我的课堂测验</h1>
      <p class="page-sub">完成教师发布的课堂测验</p>
    </div>

    <section class="summary-strip">
      <div><span>课堂测验</span><strong>{{ quizzes.length }}</strong></div>
      <div><span>待作答</span><strong>{{ pendingCount }}</strong></div>
      <div><span>已完成</span><strong>{{ completedCount }}</strong></div>
      <div><span>平均得分</span><strong>{{ averageScore }}</strong></div>
    </section>

    <section class="overview-panel">
      <div>
        <strong>测验完成情况</strong>
        <p>只显示教师已发布或已截止的课堂测验，草稿测验不会出现在学生端。</p>
      </div>
      <div class="progress-track">
        <i :style="{ width: `${completionRate}%` }"></i>
      </div>
    </section>

    <!-- 课程筛选 -->
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadQuizzes" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <!-- 测验列表 -->
    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="quizzes.length===0" class="empty">暂无课堂测验</div>
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
              :class="['opt-item', answers[quizDetail.questions[currentQ].id] === Number(i) && 'selected']"
              @click="selectAnswer(quizDetail.questions[currentQ].id, Number(i))"
            >
              <span class="opt-letter">{{ String.fromCharCode(65+Number(i)) }}</span>
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
              :class="['dot', answers[q.id]!==undefined && 'answered', Number(i)===currentQ && 'current']"
              @click="currentQ=Number(i)"
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
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
const completedCount = computed(() => quizzes.value.filter((item: any) => item.attempted).length)
const pendingCount = computed(() => quizzes.value.filter((item: any) => !item.attempted).length)
const completionRate = computed(() => quizzes.value.length ? Math.round(completedCount.value / quizzes.value.length * 100) : 0)
const averageScore = computed(() => {
  const scores = quizzes.value.filter((item: any) => item.my_score != null).map((item: any) => Number(item.my_score))
  if (!scores.length) return '--'
  return Math.round(scores.reduce((sum: number, score: number) => sum + score, 0) / scores.length)
})

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
.page { padding: 28px; color: #0f2f64; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { font-size: 14px; color: #5b6f92; margin-top: 6px; }
.summary-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.summary-strip div { background: #fff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 13px; box-shadow: 0 8px 20px rgba(15,47,100,.05); }
.summary-strip span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 6px; }
.summary-strip strong { color: #0f2f64; font-size: 24px; }
.overview-panel { display: grid; grid-template-columns: minmax(260px, .8fr) minmax(320px, 1.2fr); gap: 16px; align-items: center; background: #fff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.05); }
.overview-panel strong { color: #0f2f64; font-size: 16px; }
.overview-panel p { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 6px 0 0; }
.progress-track { height: 12px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.progress-track i { display: block; height: 100%; background: linear-gradient(90deg, #0b63b6, #54a4ee); border-radius: inherit; }
.filter-bar { margin-bottom: 20px; }
.sel { background: #fff; border: 1px solid #c8ddf4; border-radius: 8px; padding: 9px 14px; color: #0f2f64; font-size: 14px; outline: none; min-width: 220px; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 10px; padding: 28px; text-align: center; background: #f8fbff; }
/* 测验列表 */
.quiz-list { display: flex; flex-direction: column; gap: 12px; }
.quiz-card { display: flex; align-items: center; justify-content: space-between; background: #fff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px 20px; transition: border-color 0.2s; box-shadow: 0 10px 24px rgba(15,47,100,.05); }
.quiz-card:hover { border-color: #9ec8f1; }
.quiz-left { display: flex; align-items: center; gap: 16px; }
.quiz-icon { width: 42px; height: 42px; border-radius: 10px; background: #eaf3ff; color: #0b63b6; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.quiz-title { font-size: 16px; font-weight: 900; color: #0f2f64; margin-bottom: 6px; }
.quiz-meta { display: flex; gap: 10px; }
.meta-tag { font-size: 12px; color: #5b6f92; background: #f2f7fd; border: 1px solid #d9e7f7; padding: 3px 10px; border-radius: 8px; }
.badge.done { font-size: 13px; font-weight: 900; color: #0b7d56; background: #e8f7f0; padding: 6px 16px; border-radius: 20px; }
.start-btn { background: #0b63b6; color: white; border: none; border-radius: 8px; padding: 9px 18px; cursor: pointer; font-weight: 900; font-size: 14px; transition: all 0.2s; }
.start-btn:hover { background: #075da8; }
/* 作答弹窗 */
.quiz-body { display: flex; flex-direction: column; gap: 16px; }
.timer { text-align: right; font-size: 18px; font-weight: 700; color: #5b6f92; font-variant-numeric: tabular-nums; }
.timer.urgent { color: #f87171; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
.progress-bar { height: 5px; background: #edf3fb; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #0b63b6; border-radius: 4px; transition: width 0.3s; }
.q-counter { font-size: 12px; color: #5b6f92; text-align: center; }
.question-block { background: #f8fbff; border: 1px solid #d9e7f7; border-radius: 14px; padding: 20px; }
.q-text { font-size: 16px; font-weight: 800; color: #0f2f64; line-height: 1.7; margin-bottom: 16px; }
.options { display: flex; flex-direction: column; gap: 10px; }
.opt-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: #fff; border: 1px solid #d9e7f7; border-radius: 12px; cursor: pointer; transition: all 0.18s; }
.opt-item:hover { background: #eaf3ff; border-color: #9ec8f1; }
.opt-item.selected { background: #eaf3ff; border-color: #0b63b6; }
.opt-letter { font-size: 13px; font-weight: 900; color: #0b63b6; background: #eaf3ff; width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.opt-item.selected .opt-letter { background: #0b63b6; color: white; }
.opt-item span:last-child { font-size: 14px; color: #5b6f92; }
.opt-item.selected span:last-child { color: #0f2f64; }
/* 导航 */
.nav-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.nav-btn { background: #fff; border: 1px solid #c8ddf4; color: #5b6f92; border-radius: 10px; padding: 8px 16px; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.nav-btn:hover:not(:disabled) { background: #eaf3ff; color: #0b63b6; }
.nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.q-dots { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #d9e7f7; cursor: pointer; transition: all 0.15s; flex-shrink: 0; }
.dot.answered { background: #54a4ee; }
.dot.current { background: #0b63b6; transform: scale(1.3); }
.submit-btn { background: #0b7d56; border: none; color: white; border-radius: 10px; padding: 9px 20px; cursor: pointer; font-weight: 900; font-size: 14px; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
/* 结果 */
.result-body { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 20px 0; }
.result-score { font-size: 72px; font-weight: 900; line-height: 1; }
.result-score.excellent { color: #34d399; }
.result-score.good { color: #818cf8; }
.result-score.pass { color: #fbbf24; }
.result-score.fail { color: #f87171; }
.result-label { font-size: 18px; font-weight: 700; color: #5b6f92; }
.result-detail { font-size: 14px; color: #5b6f92; }
.done-btn { margin-top: 8px; background: #0b63b6; border: none; color: white; border-radius: 10px; padding: 10px 32px; cursor: pointer; font-weight: 900; font-size: 15px; }
@media (max-width: 820px) {
  .summary-strip, .overview-panel { grid-template-columns: 1fr; }
  .quiz-card { align-items: flex-start; flex-direction: column; gap: 14px; }
}
</style>
