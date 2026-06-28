<template>
  <div class="page">
    <header class="hero-panel">
      <div>
        <div class="hero-kicker">学生控制中枢</div>
        <h1>{{ displayName }}的学习驾驶舱</h1>
        <p>{{ today }} · 聚合作业、报告、测验、出勤和 AI 助学记录</p>
      </div>
      <div class="hero-actions">
        <router-link to="/student/course-progress" class="hero-btn primary">查看课程学情</router-link>
        <router-link to="/student/chat" class="hero-btn">进入 AI 助学</router-link>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card blue">
        <span>课表课程</span>
        <strong>{{ learning?.courses_count ?? courses.length }}</strong>
        <small>当前学习范围</small>
      </div>
      <div class="stat-card amber">
        <span>待处理任务</span>
        <strong>{{ alertCount }}</strong>
        <small>作业/报告/测验</small>
      </div>
      <div class="stat-card green">
        <span>出勤率</span>
        <strong>{{ percentText(learning?.attendance_rate) }}</strong>
        <small>{{ learning?.attended_sessions || 0 }}/{{ learning?.attendance_sessions || 0 }} 次</small>
      </div>
      <div class="stat-card red">
        <span>过程均分</span>
        <strong>{{ scoreText(learning?.average_score) }}</strong>
        <small>{{ statusText(learning?.status_level || 'good') }}</small>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="priority-panel">
        <div class="section-head">
          <div>
            <h2>今日优先事项</h2>
            <p>按截止和风险程度排序，直接处理最影响学情的事项。</p>
          </div>
          <span>{{ todoItems.length }} 项</span>
        </div>
        <div v-if="todoItems.length === 0" class="empty">暂无紧急待办，当前学习节奏稳定。</div>
        <router-link v-for="item in todoItems" :key="`${item.type}-${item.id}`" :to="item.to" class="todo-item" :class="item.level">
          <div class="todo-type">{{ item.typeLabel }}</div>
          <div class="todo-main">
            <strong>{{ item.title }}</strong>
            <span>{{ item.detail }}</span>
          </div>
          <em>{{ item.action }}</em>
        </router-link>
      </section>

      <section v-if="learning" class="process-panel" :class="learning.status_level">
        <div class="section-head">
          <div>
            <h2>学习全过程评价</h2>
            <p>作业、测验、出勤、AI 助学与课堂专注综合判断。</p>
          </div>
          <span class="status-pill">{{ statusText(learning.status_level) }}</span>
        </div>
        <div class="progress-list">
          <div class="progress-row">
            <div><span>作业完成</span><strong>{{ percentText(learning.assignment_completion_rate) }}</strong></div>
            <i><b :style="rateStyle(learning.assignment_completion_rate)"></b></i>
          </div>
          <div class="progress-row">
            <div><span>测验完成</span><strong>{{ percentText(learning.quiz_completion_rate) }}</strong></div>
            <i><b :style="rateStyle(learning.quiz_completion_rate)"></b></i>
          </div>
          <div class="progress-row">
            <div><span>课堂专注</span><strong>{{ percentText(learning.posture?.attentive_rate) }}</strong></div>
            <i><b :style="rateStyle(learning.posture?.attentive_rate)"></b></i>
          </div>
        </div>
        <div class="ai-chip">
          <span>AI 助学提问</span>
          <strong>{{ learning.ai_questions }}</strong>
          <router-link to="/student/chat">继续问答</router-link>
        </div>
      </section>
    </div>

    <div class="lower-grid">
      <section class="card">
        <div class="card-title"><el-icon><Collection /></el-icon> 我的课程</div>
        <div v-if="courses.length === 0" class="empty">
          请先 <router-link to="/student/timetable">导入课表</router-link>
        </div>
        <div v-for="c in courses.slice(0, 8)" :key="c.id" class="course-item">
          <div class="course-avatar">{{ c.name.charAt(0) }}</div>
          <div>
            <div class="course-name">{{ c.name }}</div>
            <div class="course-teacher">{{ c.teacher_name }} · {{ c.course_code }}</div>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-title"><el-icon><Bell /></el-icon> 最新公告</div>
        <div v-if="announcements.length === 0" class="empty">暂无公告</div>
        <div v-for="a in announcements.slice(0,4)" :key="a.id" class="ann-item">
          <span class="ann-priority" :class="`p${a.priority}`">{{ ['普通','重要','紧急'][a.priority] }}</span>
          <div>
            <div class="ann-title">{{ cleanTitle(a.title) }}</div>
            <div class="ann-time">{{ formatDate(a.created_at) }}</div>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-title"><el-icon><DataLine /></el-icon> 学习入口</div>
        <div class="quick-entry-grid">
          <router-link to="/student/course-progress" class="quick-entry">课程学情</router-link>
          <router-link to="/student/assignments" class="quick-entry">作业/实验/报告</router-link>
          <router-link to="/student/quiz" class="quick-entry">课堂测验</router-link>
          <router-link to="/student/chat" class="quick-entry">AI 助学</router-link>
        </div>
        <div class="pending-mini">
          <strong>待提交作业/报告</strong>
          <span>{{ pendingAssignments.length }} 项</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const courses = ref<any[]>([])
const assignments = ref<any[]>([])
const announcements = ref<any[]>([])
const grades = ref<any[]>([])
const learning = ref<any | null>(null)

const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
const displayName = computed(() => auth.user?.full_name || auth.user?.username || '同学')
const pendingAssignments = computed(() => assignments.value.filter(a => !a.submitted))
const alertCount = computed(() => (learning.value?.pending_assignments || pendingAssignments.value.length) + (learning.value?.missing_quizzes || 0))
const todoItems = computed(() => {
  const items: any[] = []
  for (const item of learning.value?.pending_items || []) {
    items.push({
      type: 'assignment',
      typeLabel: item.type === 'report' ? '报告' : '作业',
      id: item.id,
      title: cleanTitle(item.title),
      detail: item.course_name || '待提交作业/报告',
      action: '去提交',
      level: 'warning',
      to: '/student/assignments',
    })
  }
  for (const item of learning.value?.missing_quiz_items || []) {
    items.push({
      type: 'quiz',
      typeLabel: '测验',
      id: item.id,
      title: cleanTitle(item.title),
      detail: item.course_name || '待完成测验',
      action: '去作答',
      level: 'info',
      to: '/student/quiz',
    })
  }
  return items.slice(0, 5)
})
const avgScore = computed(() => {
  const scores = grades.value.map(g => g.score).filter(s => s != null)
  return scores.length ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : '--'
})

const cleanTitle = (value?: string) => (value || '')
  .replace(/^【课程过程】/, '')
  .replace(/^完成作业：/, '')
  .replace(/^完成测验：/, '')
  .trim()
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : ''
const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const scoreText = (v?: number | null) => v == null ? avgScore.value : Math.round(v)
const statusText = (level: string) => level === 'danger' ? '重点关注' : level === 'warning' ? '需要改进' : '状态良好'
const rateStyle = (value?: number | null) => ({ width: `${Math.max(0, Math.min(100, Math.round(value || 0)))}%` })

onMounted(async () => {
  try {
    const [c, a, ann, g, learn] = await Promise.all([
      axios.get('/api/v1/courses/my'),
      axios.get('/api/v1/assignments/'),
      axios.get('/api/v1/announcements/'),
      axios.get('/api/v1/grades/'),
      axios.get('/api/v1/learning/my-summary'),
    ])
    courses.value = c.data
    assignments.value = a.data
    announcements.value = ann.data
    grades.value = g.data
    learning.value = learn.data
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.page { padding: 28px; font-family: 'Inter', sans-serif; color: #0f2f64; }
.hero-panel {
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  background: linear-gradient(135deg, #075da8, #2d89d9);
  color: #ffffff; border-radius: 10px; padding: 24px 28px; margin-bottom: 16px;
  box-shadow: 0 16px 36px rgba(11,99,182,0.18);
}
.hero-kicker { font-size: 13px; font-weight: 800; opacity: .86; margin-bottom: 8px; }
.hero-panel h1 { margin: 0; font-size: 28px; font-weight: 900; letter-spacing: 0; }
.hero-panel p { margin: 8px 0 0; color: rgba(255,255,255,.82); font-size: 14px; }
.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.hero-btn { border: 1px solid rgba(255,255,255,.45); color: #ffffff; text-decoration: none; border-radius: 8px; padding: 10px 14px; font-size: 13px; font-weight: 800; background: rgba(255,255,255,.12); }
.hero-btn.primary { background: #ffffff; color: #075da8; border-color: #ffffff; }
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 16px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.stat-card span, .stat-card small { display: block; color: #5b6f92; font-size: 12px; }
.stat-card strong { display: block; color: #0f2f64; font-size: 30px; line-height: 1; margin: 9px 0 7px; }
.stat-card.blue { border-top: 3px solid #0b63b6; }
.stat-card.amber { border-top: 3px solid #d8890b; }
.stat-card.green { border-top: 3px solid #14a46f; }
.stat-card.red { border-top: 3px solid #cf3434; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(340px, .65fr); gap: 16px; margin-bottom: 16px; }
.priority-panel, .process-panel, .card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.section-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }
.section-head h2 { color: #0f2f64; font-size: 18px; margin: 0; }
.section-head p { color: #5b6f92; font-size: 12px; margin: 5px 0 0; line-height: 1.5; }
.section-head > span { color: #0b63b6; background: #eaf3ff; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.todo-item { display: grid; grid-template-columns: 54px minmax(0, 1fr) 58px; align-items: center; gap: 12px; text-decoration: none; padding: 12px 0; border-top: 1px solid #edf3fb; }
.todo-type { color: #0b63b6; background: #eaf3ff; border-radius: 8px; text-align: center; padding: 5px 0; font-size: 12px; font-weight: 900; }
.todo-main strong { display: block; color: #0f2f64; font-size: 14px; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.todo-main span { display: block; color: #5b6f92; font-size: 12px; margin-top: 4px; }
.todo-item em { color: #0b63b6; font-size: 12px; font-style: normal; font-weight: 800; text-align: right; }
.todo-item.warning .todo-type { color: #9a5a00; background: #fff2d9; }
.todo-item.warning em { color: #d8890b; }
.status-pill { background: #eaf3ff; color: #0b63b6; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 900; }
.process-panel.warning .status-pill { background: #fff2d9; color: #9a5a00; }
.process-panel.danger .status-pill { background: #fff0ef; color: #cf3434; }
.progress-list { display: flex; flex-direction: column; gap: 14px; }
.progress-row > div { display: flex; justify-content: space-between; color: #5b6f92; font-size: 12px; margin-bottom: 7px; }
.progress-row strong { color: #0f2f64; }
.progress-row i { display: block; height: 9px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.progress-row b { display: block; height: 100%; background: linear-gradient(90deg, #0b63b6, #54a4ee); border-radius: inherit; }
.ai-chip { margin-top: 16px; background: #f6faff; border: 1px solid #d9e7f7; border-radius: 8px; padding: 12px; display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; }
.ai-chip span { color: #5b6f92; font-size: 12px; }
.ai-chip strong { color: #0f2f64; font-size: 20px; }
.ai-chip a { color: #0b63b6; text-decoration: none; font-size: 12px; font-weight: 800; }
.lower-grid { display: grid; grid-template-columns: 1.1fr 1fr .9fr; gap: 16px; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 900; color: #0f2f64; margin-bottom: 14px; }
.card-title .el-icon { color: #0b63b6; }
.quick-entry-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.quick-entry { display: flex; align-items: center; justify-content: center; min-height: 48px; border-radius: 8px; background: #eaf3ff; border: 1px solid #c8ddf4; color: #0b63b6; text-decoration: none; font-size: 14px; font-weight: 900; }
.quick-entry:hover { background: #dceeff; }
.pending-mini { margin-top: 14px; border-top: 1px solid #edf3fb; padding-top: 12px; display: flex; justify-content: space-between; color: #5b6f92; font-size: 13px; }
.pending-mini strong { color: #0f2f64; }
.empty { text-align: center; color: #5b6f92; padding: 20px; font-size: 14px; border: 1px dashed #c8ddf4; border-radius: 8px; background: #f8fbff; }
.empty a { color: #0b63b6; }
.ann-item, .course-item { display: flex; gap: 10px; align-items: flex-start; padding: 10px 0; border-top: 1px solid #edf3fb; }
.ann-item:first-of-type, .course-item:first-of-type { border-top: none; }
.ann-priority { font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; white-space: nowrap; margin-top: 1px; }
.ann-priority.p0 { background: #eaf3ff; color: #0b63b6; }
.ann-priority.p1 { background: #fff2d9; color: #9a5a00; }
.ann-priority.p2 { background: #fff0ef; color: #cf3434; }
.ann-title { font-size: 14px; color: #0f2f64; font-weight: 700; line-height: 1.45; }
.ann-time { font-size: 12px; color: #5b6f92; margin-top: 2px; }
.course-avatar { width: 34px; height: 34px; border-radius: 8px; background: #0b63b6; display: flex; align-items: center; justify-content: center; color: white; font-weight: 900; font-size: 14px; flex-shrink: 0; }
.course-name { font-size: 14px; color: #0f2f64; font-weight: 800; }
.course-teacher { font-size: 12px; color: #5b6f92; margin-top: 2px; }
@media (max-width: 1180px) {
  .stats-grid, .lower-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .page { padding: 18px; }
  .hero-panel { flex-direction: column; align-items: flex-start; }
  .stats-grid, .lower-grid { grid-template-columns: 1fr; }
  .todo-item { grid-template-columns: 48px minmax(0, 1fr); }
  .todo-item em { grid-column: 2; text-align: left; }
}
</style>
