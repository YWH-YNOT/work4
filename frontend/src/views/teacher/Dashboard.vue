<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">教师控制台</h1>
        <p class="page-sub">{{ today }}，汇总当前授课课程的教学运行状态。</p>
      </div>
      <router-link to="/teacher/grades" class="analysis-link">
        <el-icon><DataAnalysis /></el-icon>
        查看 AI 学情分析
      </router-link>
    </div>

    <div class="stats-grid">
      <div class="stat-card blue">
        <div class="stat-icon"><el-icon><Collection /></el-icon></div>
        <div class="stat-num">{{ stats.courses }}</div>
        <div class="stat-label">我的课程</div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon"><el-icon><Document /></el-icon></div>
        <div class="stat-num">{{ stats.assignments }}</div>
        <div class="stat-label">已发布任务</div>
      </div>
      <div class="stat-card amber">
        <div class="stat-icon"><el-icon><Warning /></el-icon></div>
        <div class="stat-num">{{ learning?.totals?.risk_students || 0 }}</div>
        <div class="stat-label">需关注学生</div>
      </div>
      <div class="stat-card rose">
        <div class="stat-icon"><el-icon><ChatDotRound /></el-icon></div>
        <div class="stat-num">{{ learning?.totals?.ai_questions || stats.logs }}</div>
        <div class="stat-label">AI 助学提问</div>
      </div>
    </div>

    <div class="quick-links">
      <router-link to="/teacher/courses" class="quick-card"><el-icon><Collection /></el-icon><span>授课课程</span></router-link>
      <router-link to="/teacher/course-progress" class="quick-card"><el-icon><DataBoard /></el-icon><span>课程学情</span></router-link>
      <router-link to="/teacher/grades" class="quick-card"><el-icon><DataAnalysis /></el-icon><span>学情分析</span></router-link>
      <router-link to="/teacher/knowledge" class="quick-card"><el-icon><Share /></el-icon><span>知识图谱</span></router-link>
      <router-link to="/teacher/assignments" class="quick-card"><el-icon><Document /></el-icon><span>作业/实验/报告</span></router-link>
      <router-link to="/teacher/quiz" class="quick-card"><el-icon><Memo /></el-icon><span>课堂测验</span></router-link>
      <router-link to="/teacher/gradebook" class="quick-card"><el-icon><TrophyBase /></el-icon><span>成绩管理</span></router-link>
    </div>

    <div class="command-layout" v-if="learning">
      <section class="panel command-panel">
        <div class="panel-head">
          <div>
            <h2>今日教学指挥</h2>
            <p>按风险程度和过程指标自动生成教师优先处理事项。</p>
          </div>
        </div>
        <div class="command-list">
          <router-link
            v-for="item in commandItems"
            :key="item.title"
            :to="item.to"
            class="command-item"
            :class="item.level"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.detail }}</p>
            </div>
            <span>{{ item.tag }}</span>
          </router-link>
        </div>
      </section>

      <section class="panel radar-panel">
        <div class="panel-head">
          <div>
            <h2>过程达成雷达</h2>
            <p>作业、测验、考勤、AI 助学四类关键指标的综合态势。</p>
          </div>
        </div>
        <div class="dashboard-radar">
          <svg viewBox="0 0 260 230" role="img" aria-label="教学过程达成雷达图">
            <polygon
              v-for="grid in radarGrid"
              :key="grid.level"
              :points="grid.points"
              class="radar-grid"
            />
            <line
              v-for="axis in radarAxes"
              :key="axis.label"
              x1="130"
              y1="112"
              :x2="axis.x"
              :y2="axis.y"
              class="radar-axis"
            />
            <polygon :points="radarPolygon" class="radar-area" />
            <circle
              v-for="point in radarPointObjects"
              :key="`${point.x}-${point.y}`"
              :cx="point.x"
              :cy="point.y"
              r="3"
              class="radar-dot"
            />
            <text
              v-for="axis in radarAxes"
              :key="`text-${axis.label}`"
              :x="axis.labelX"
              :y="axis.labelY"
              text-anchor="middle"
              class="radar-label"
            >
              {{ axis.label }}
            </text>
          </svg>
          <div class="radar-values">
            <span v-for="item in overviewBars" :key="item.label">
              <i :style="{ background: item.color }"></i>{{ item.label }} {{ item.text }}
            </span>
          </div>
        </div>
      </section>

      <section class="panel ai-panel">
        <div class="panel-head">
          <div>
            <h2>AI 助学线索</h2>
            <p>抽取近期学生问题，便于回流到课堂讲解和知识图谱。</p>
          </div>
          <router-link to="/teacher/logs" class="text-link">查看日志</router-link>
        </div>
        <div class="question-list">
          <div v-if="recentQuestions.length === 0" class="empty-risk">暂无近期 AI 助学问题。</div>
          <div v-for="item in recentQuestions" :key="item.id" class="question-item">
            <strong>{{ item.student_name || item.user || '学生' }} · {{ item.course || '未绑定课程' }}</strong>
            <p>{{ shortText(item.content) }}</p>
          </div>
        </div>
      </section>
    </div>

    <div class="overview-layout" v-if="learning">
      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>教学全过程概览</h2>
            <p>只展示总体态势，学生级明细请进入“课程学情”和“学情分析”。</p>
          </div>
          <span>{{ learning.totals.students }} 名学生</span>
        </div>
        <div class="bar-list">
          <div v-for="item in overviewBars" :key="item.label" class="bar-row">
            <div class="bar-label">
              <span>{{ item.label }}</span>
              <strong>{{ item.text }}</strong>
            </div>
            <div class="bar-track"><i :style="{ width: item.width, background: item.color }"></i></div>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>风险分布</h2>
            <p>按当前预警学生列表估算教学干预优先级。</p>
          </div>
        </div>
        <div class="risk-summary">
          <div class="risk-card danger"><span>重点关注</span><strong>{{ riskCounts.danger }}</strong></div>
          <div class="risk-card warning"><span>需要跟进</span><strong>{{ riskCounts.warning }}</strong></div>
          <div class="risk-card stable"><span>整体稳定</span><strong>{{ stableStudents }}</strong></div>
        </div>
        <div class="ai-summary">
          <strong>AI 摘要</strong>
          <p>{{ aiSummary }}</p>
        </div>
      </section>
    </div>

    <section v-if="learning" class="panel">
      <div class="panel-head">
        <div>
          <h2>近期需关注</h2>
          <p>这里保留少量提醒，完整热力图和能力画像在“学情分析”。</p>
        </div>
        <router-link to="/teacher/grades" class="text-link">查看完整分析</router-link>
      </div>
      <div class="risk-list">
        <div v-if="learning.risk_students.length === 0" class="empty-risk">当前没有明显过程预警。</div>
        <div v-for="student in learning.risk_students.slice(0, 5)" :key="`${student.student_id}-${student.course_id}`" class="risk-item" :class="student.status_level">
          <div>
            <div class="risk-name">{{ student.student_name }} · {{ student.course_name }}</div>
            <div class="risk-detail">{{ student.first_recommendation }}</div>
          </div>
          <div class="risk-stats">
            <span>作业 {{ student.pending_assignments }}</span>
            <span>测验 {{ student.missing_quizzes }}</span>
            <span>成绩 {{ valueText(student.average_score) }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
const stats = ref({ courses: 0, assignments: 0, logs: 0 })
const learning = ref<any | null>(null)
const recentQuestions = ref<any[]>([])

const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : Math.round(v)
const clamp = (v?: number | null) => Math.max(0, Math.min(100, Number(v || 0)))
const arrayLen = (data: unknown) => Array.isArray(data) ? data.length : 0
const shortText = (text?: string) => {
  const value = (text || '').replace(/\s+/g, ' ').trim()
  return value.length > 56 ? `${value.slice(0, 56)}...` : value
}

const overviewBars = computed(() => {
  const totals = learning.value?.totals || {}
  const aiBase = Math.max(1, (totals.students || 1) * 5)
  const aiRate = clamp((totals.ai_questions || 0) / aiBase * 100)
  return [
    { label: '作业报告完成', text: percentText(totals.assignment_completion_rate), width: `${clamp(totals.assignment_completion_rate)}%`, color: '#0b63b6' },
    { label: '测验完成', text: percentText(totals.quiz_completion_rate), width: `${clamp(totals.quiz_completion_rate)}%`, color: '#3478d8' },
    { label: '考勤到课', text: percentText(totals.attendance_rate), width: `${clamp(totals.attendance_rate)}%`, color: '#14a46f' },
    { label: 'AI 助学活跃', text: `${Math.round(aiRate)}%`, width: `${aiRate}%`, color: '#d8890b' },
  ]
})

const riskCounts = computed(() => {
  const rows = learning.value?.risk_students || []
  return {
    danger: rows.filter((item: any) => item.status_level === 'danger').length,
    warning: rows.filter((item: any) => item.status_level === 'warning').length,
  }
})

const stableStudents = computed(() => Math.max(0, (learning.value?.totals?.students || 0) - (learning.value?.totals?.risk_students || 0)))

const aiSummary = computed(() => {
  const totals = learning.value?.totals || {}
  if ((totals.risk_students || 0) === 0) return '当前课程整体稳定，可重点跟踪高阶问题、项目报告和知识图谱资源使用情况。'
  if (riskCounts.value.danger > 0) return '系统识别到重点关注学生，建议优先核查未交任务、低出勤和连续低分记录。'
  return '多数预警属于阶段性跟进，建议在下一次课堂或作业反馈中完成定向提醒。'
})

const commandItems = computed(() => {
  const totals = learning.value?.totals || {}
  const items = []
  if ((totals.risk_students || 0) > 0) {
    const first = learning.value?.risk_students?.[0]
    items.push({
      title: `跟进 ${totals.risk_students} 名需关注学生`,
      detail: first
        ? `先处理 ${first.student_name} 的过程预警：${first.first_recommendation || '补齐作业、测验和课堂投入记录'}。`
        : '优先处理低完成率、低出勤和连续低分学生，进入学情分析查看热力图。',
      tag: '预警',
      level: 'danger',
      to: '/teacher/grades',
    })
  }
  if ((totals.assignment_completion_rate || 0) < 92) {
    items.push({
      title: '补齐实验与课程报告闭环',
      detail: '重点核查滤波器幅频特性程序、VXIbus 仲裁分析和课程报告选题，补齐文件提交、评语和成绩。',
      tag: percentText(totals.assignment_completion_rate),
      level: 'warning',
      to: '/teacher/assignments',
    })
  }
  if ((totals.quiz_completion_rate || 0) < 92) {
    items.push({
      title: '复核课堂测验薄弱点',
      detail: '提醒未完成测验学生，并重点讲评 GPIB/SCPI/VISA、VXI 地址译码和 DTB 仲裁相关错题。',
      tag: percentText(totals.quiz_completion_rate),
      level: 'warning',
      to: '/teacher/quiz',
    })
  }
  items.push({
    title: '沉淀 AI 助学高频问题',
    detail: '把 VISA 资源管理、SCPI 指令、滤波器频点设计和课程报告追溯问题回流到知识图谱和下次课堂。',
    tag: `${totals.ai_questions || 0} 问`,
    level: 'info',
    to: '/teacher/logs',
  })
  return items.slice(0, 4)
})

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  const rad = Math.PI / 180 * angle
  return { x: cx + Math.cos(rad) * radius, y: cy + Math.sin(rad) * radius }
}

const radarMetrics = computed(() => overviewBars.value.map((item) => ({
  label: item.label.replace('完成', '').replace('到课', '').replace('活跃', ''),
  value: clamp(Number.parseFloat(item.width)),
})))

const radarAngles = computed(() => radarMetrics.value.map((_item, index) => -90 + index * 360 / Math.max(1, radarMetrics.value.length)))

const radarPointObjects = computed(() => radarMetrics.value.map((item, index) => (
  polarPoint(130, 112, 74 * item.value / 100, radarAngles.value[index] ?? -90)
)))

const radarPolygon = computed(() => radarPointObjects.value.map(point => `${point.x},${point.y}`).join(' '))

const radarGrid = computed(() => [35, 60, 85, 100].map(level => ({
  level,
  points: radarAngles.value.map((angle) => {
    const point = polarPoint(130, 112, 74 * level / 100, angle)
    return `${point.x},${point.y}`
  }).join(' '),
})))

const radarAxes = computed(() => radarMetrics.value.map((metric, index) => {
  const angle = radarAngles.value[index] ?? -90
  const end = polarPoint(130, 112, 80, angle)
  const label = polarPoint(130, 112, 99, angle)
  return {
    label: metric.label,
    x: end.x,
    y: end.y,
    labelX: label.x,
    labelY: label.y + 4,
  }
}))

onMounted(async () => {
  const [courses, assignments, logStats, learn, logs] = await Promise.allSettled([
    axios.get('/api/v1/courses/my'),
    axios.get('/api/v1/assignments/'),
    axios.get('/api/v1/logs/stats?limit=1'),
    axios.get('/api/v1/learning/teacher-summary'),
    axios.get('/api/v1/logs/?page_size=6'),
  ])
  if (courses.status === 'fulfilled') stats.value.courses = arrayLen(courses.value.data)
  if (assignments.status === 'fulfilled') {
    const allowedCourseIds = new Set((courses.status === 'fulfilled' ? courses.value.data || [] : []).map((course: any) => course.id))
    stats.value.assignments = (assignments.value.data || []).filter((item: any) => !allowedCourseIds.size || allowedCourseIds.has(item.course_id)).length
  }
  if (logStats.status === 'fulfilled') stats.value.logs = logStats.value.data?.summary?.total_questions || 0
  if (learn.status === 'fulfilled') learning.value = learn.value.data
  if (logs.status === 'fulfilled') {
    recentQuestions.value = (logs.value.data?.items || []).filter((item: any) => item.role === 'user').slice(0, 4)
  }
})
</script>

<style scoped>
.page { padding: 32px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 22px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { font-size: 13px; color: #5b6f92; margin: 6px 0 0; }
.analysis-link, .text-link { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #0b63b6; font-weight: 800; }
.analysis-link { background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; padding: 9px 14px; white-space: nowrap; }
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; }
.stat-card { border-radius: 10px; padding: 18px; border: 1px solid #d9e7f7; background: #ffffff; box-shadow: 0 10px 24px rgba(15,47,100,.06); display: flex; flex-direction: column; gap: 8px; }
.stat-card.blue { border-top: 3px solid #0b63b6; }
.stat-card.green { border-top: 3px solid #14a46f; }
.stat-card.amber { border-top: 3px solid #d8890b; }
.stat-card.rose { border-top: 3px solid #cf3434; }
.stat-icon { font-size: 20px; color: #0b63b6; }
.stat-num { font-size: 32px; font-weight: 900; color: #0f2f64; line-height: 1; }
.stat-label { font-size: 13px; color: #5b6f92; }
.quick-links { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }
.quick-card { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 56px; padding: 12px; border-radius: 9px; border: 1px solid #c8ddf4; background: #f8fbff; color: #0b63b6; text-decoration: none; font-size: 14px; font-weight: 800; transition: all .18s; }
.quick-card:hover { background: #eaf3ff; transform: translateY(-1px); }
.command-layout { display: grid; grid-template-columns: minmax(360px, 1fr) minmax(320px, .86fr) minmax(340px, .92fr); gap: 16px; margin-bottom: 16px; }
.overview-layout { display: grid; grid-template-columns: 1.2fr .8fr; gap: 16px; margin-bottom: 16px; }
.panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.panel-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 17px; margin: 0; }
.panel-head p, .panel-head span { color: #5b6f92; font-size: 12px; margin: 5px 0 0; line-height: 1.55; }
.command-list, .question-list { display: grid; gap: 9px; }
.command-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 1px solid #d9e7f7; border-radius: 9px; padding: 11px 12px; text-decoration: none; background: #f8fbff; }
.command-item strong { display: block; color: #0f2f64; font-size: 13px; }
.command-item p { color: #5b6f92; font-size: 12px; line-height: 1.5; margin: 4px 0 0; }
.command-item > span { flex-shrink: 0; border-radius: 7px; padding: 5px 8px; color: #0b63b6; background: #eaf3ff; font-size: 12px; font-weight: 900; }
.command-item.danger { border-color: #ffd5cf; background: #fff4f2; }
.command-item.danger > span { color: #cf3434; background: #ffe6e2; }
.command-item.warning { border-color: #fde4a8; background: #fff8e6; }
.command-item.warning > span { color: #9a5a00; background: #fff0c9; }
.dashboard-radar { display: grid; grid-template-columns: minmax(180px, .85fr) minmax(150px, 1fr); align-items: center; gap: 10px; }
.dashboard-radar svg { width: 100%; height: 220px; display: block; }
.radar-grid { fill: none; stroke: #d9e7f7; stroke-width: 1; }
.radar-axis { stroke: #e1ecf8; stroke-width: 1; }
.radar-area { fill: rgba(11,99,182,.16); stroke: #0b63b6; stroke-width: 2; }
.radar-dot { fill: #0b63b6; }
.radar-label { fill: #0f2f64; font-size: 10px; font-weight: 900; }
.radar-values { display: grid; gap: 8px; }
.radar-values span { display: inline-flex; align-items: center; gap: 6px; color: #5b6f92; font-size: 12px; font-weight: 800; }
.radar-values i { width: 8px; height: 8px; border-radius: 2px; }
.question-item { border: 1px solid #e1ecf8; background: #f8fbff; border-radius: 9px; padding: 10px 11px; }
.question-item strong { display: block; color: #0f2f64; font-size: 12px; margin-bottom: 5px; }
.question-item p { color: #5b6f92; font-size: 12px; line-height: 1.55; margin: 0; }
.bar-list { display: grid; gap: 13px; }
.bar-label { display: flex; justify-content: space-between; color: #5b6f92; font-size: 13px; margin-bottom: 6px; }
.bar-label strong { color: #0f2f64; }
.bar-track { height: 11px; border-radius: 999px; background: #edf3fb; overflow: hidden; }
.bar-track i { display: block; height: 100%; border-radius: inherit; }
.risk-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.risk-card { border-radius: 9px; padding: 13px; border: 1px solid; background: #f8fbff; }
.risk-card span { display: block; font-size: 12px; color: #5b6f92; margin-bottom: 6px; }
.risk-card strong { color: #0f2f64; font-size: 26px; }
.risk-card.danger { border-color: #ffd5cf; background: #fff4f2; }
.risk-card.warning { border-color: #fde4a8; background: #fff8e6; }
.risk-card.stable { border-color: #b6e6ce; background: #e8f7f0; }
.ai-summary { margin-top: 12px; border: 1px solid #c8ddf4; background: #f8fbff; border-radius: 9px; padding: 12px; }
.ai-summary strong { color: #0b63b6; font-size: 13px; }
.ai-summary p { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 6px 0 0; }
.risk-list { display: flex; flex-direction: column; gap: 10px; }
.empty-risk { color: #5b6f92; border: 1px dashed #c8ddf4; background: #f8fbff; border-radius: 10px; padding: 18px; text-align: center; font-size: 13px; }
.risk-item { display: flex; justify-content: space-between; gap: 16px; align-items: center; background: #fff8e6; border: 1px solid #fde4a8; border-radius: 10px; padding: 12px 14px; }
.risk-item.danger { background: #fff4f2; border-color: #ffd5cf; }
.risk-name { color: #0f2f64; font-size: 14px; font-weight: 800; margin-bottom: 4px; }
.risk-detail { color: #5b6f92; font-size: 12px; }
.risk-stats { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.risk-stats span { color: #5b6f92; background: #ffffff; border: 1px solid #e3edf8; border-radius: 7px; padding: 4px 8px; font-size: 12px; white-space: nowrap; }
@media (max-width: 1180px) {
  .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .quick-links { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .command-layout { grid-template-columns: 1fr; }
  .overview-layout { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .page { padding: 20px; }
  .page-header, .risk-item { flex-direction: column; align-items: flex-start; }
  .stats-grid, .quick-links, .risk-summary { grid-template-columns: 1fr; }
  .dashboard-radar { grid-template-columns: 1fr; }
}
</style>
