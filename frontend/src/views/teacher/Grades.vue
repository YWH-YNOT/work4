<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">AI 学情分析</h1>
        <p class="page-sub">基于课程过程数据生成热力图、能力画像和干预建议。具体提交、测验、考勤数据请到“课程学情”查看。</p>
      </div>
      <div class="header-actions">
        <router-link class="ghost-btn" to="/teacher/gradebook">成绩管理</router-link>
        <button class="refresh-btn" @click="loadData" :disabled="loading">刷新分析</button>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadData" class="sel">
        <option value="">全部课程</option>
        <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
      </select>
      <router-link class="data-link" to="/teacher/course-progress">查看课程具体数据</router-link>
    </div>

    <div v-if="loading" class="empty">分析生成中...</div>
    <template v-else-if="summary">
      <section class="diagnosis-band">
        <div>
          <span>AI 综合研判</span>
          <h2>{{ diagnosis.title }}</h2>
          <p>{{ diagnosis.detail }}</p>
        </div>
        <strong>{{ valueText(summary.totals.average_score) }}</strong>
      </section>

      <div class="metric-grid">
        <div class="metric-card"><span>课程数</span><strong>{{ summary.totals.courses }}</strong></div>
        <div class="metric-card"><span>学生数</span><strong>{{ summary.totals.students }}</strong></div>
        <div class="metric-card"><span>作业报告完成</span><strong>{{ percentText(summary.totals.assignment_completion_rate) }}</strong></div>
        <div class="metric-card"><span>测验完成</span><strong>{{ percentText(summary.totals.quiz_completion_rate) }}</strong></div>
        <div class="metric-card"><span>出勤率</span><strong>{{ percentText(summary.totals.attendance_rate) }}</strong></div>
        <div class="metric-card"><span>AI 助学活跃</span><strong>{{ percentText(teacherAiActivityRate) }}</strong></div>
        <div class="metric-card warn"><span>需关注学生</span><strong>{{ summary.totals.risk_students }}</strong></div>
      </div>

      <LearningAnalyticsCharts
        :metrics="abilityChartMetrics"
        :series="teacherRadarSeries"
        :segments="teacherDistributionSegments"
        radar-title="班级能力雷达"
        radar-subtitle="对比班级均值、课程目标和需关注群体"
        wheel-title="课程能力目标达成"
        wheel-subtitle="按任务、测验、考勤、课堂和 AI 五类指标映射"
        distribution-title="学习过程结构分布"
        distribution-subtitle="用于识别当前课程运行中占比和薄弱环节"
        distribution-center-title="过程"
        distribution-center-sub="结构"
      />

      <div class="analysis-layout">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>学生风险热力图</h2>
              <p>颜色越深表示越需要优先干预，按作业、测验、考勤、课堂表现、AI 助学五类指标归因。</p>
            </div>
          </div>
          <div v-if="heatRows.length === 0" class="empty">当前没有明显风险学生。</div>
          <div v-else class="heatmap">
            <div class="heat-head">
              <span>学生</span>
              <span v-for="metric in heatMetrics" :key="metric">{{ metric }}</span>
              <span>建议</span>
            </div>
            <div v-for="row in heatRows" :key="`${row.student_id}-${row.course_id}`" class="heat-row">
              <div class="heat-name">
                <strong>{{ row.student_name }}</strong>
                <em>{{ row.course_name }}</em>
              </div>
              <div v-for="cell in row.cells" :key="cell.label" class="heat-cell" :class="cell.level">
                {{ cell.text }}
              </div>
              <p>{{ row.first_recommendation }}</p>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>课程能力画像</h2>
              <p>参考智慧课程建设思路，将过程数据映射为能力维度。</p>
            </div>
          </div>
          <div class="ability-matrix">
            <div
              v-for="item in abilityMetrics"
              :key="item.label"
              class="ability-tile"
              :class="abilityLevel(item.value)"
            >
              <div class="tile-top">
                <span :style="{ background: item.color }">{{ item.short }}</span>
                <strong>{{ item.text }}</strong>
              </div>
              <h3>{{ item.label }}</h3>
              <div class="tile-meter"><i :style="{ width: item.width, background: item.color }"></i></div>
              <p>{{ abilityHint(item.value) }}</p>
            </div>
          </div>
          <div class="ability-summary">
            <div>
              <span>优势维度</span>
              <strong>{{ strongestAbility.short }} · {{ strongestAbility.text }}</strong>
            </div>
            <div>
              <span>优先补强</span>
              <strong>{{ weakestAbility.short }} · {{ weakestAbility.text }}</strong>
            </div>
          </div>
        </section>
      </div>

      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>AI 干预建议</h2>
            <p>面向教师给出下一步教学动作，具体学生名单可按热力图排序跟进。</p>
          </div>
        </div>
        <div class="suggestion-grid">
          <div v-for="item in aiInterventionSuggestions" :key="item.title" class="suggestion-card">
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import LearningAnalyticsCharts from '@/components/LearningAnalyticsCharts.vue'

const courses = ref<any[]>([])
const selectedCourse = ref<number | ''>('')
const summary = ref<any | null>(null)
const loading = ref(false)
const heatMetrics = ['作业', '测验', '考勤', '课堂', 'AI']

const clamp = (v?: number | null) => Math.max(0, Math.min(100, Number(v || 0)))
const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : Math.round(v)
const levelByScore = (value: number) => value >= 75 ? 'ok' : value >= 55 ? 'mid' : 'high'
const teacherAiActivityRate = computed(() => {
  const totals = summary.value?.totals || {}
  const aiBase = Math.max(1, (totals.students || 1) * 5)
  return clamp((totals.ai_questions || 0) / aiBase * 100)
})

const diagnosis = computed(() => {
  const totals = summary.value?.totals || {}
  const risk = totals.risk_students || 0
  if (risk === 0) {
    return { title: '整体学习状态稳定', detail: '作业、测验和出勤数据未出现集中异常，可继续强化项目化任务和高阶问题链。' }
  }
  if (risk >= Math.max(8, Math.round((totals.students || 0) * 0.2))) {
    return { title: '存在成组学习风险', detail: '建议优先检查任务难度、截止时间和课堂节奏，针对低完成率指标安排集中反馈。' }
  }
  return { title: '少量学生需要定向跟进', detail: '风险主要集中在个别学生，可结合热力图逐人查看缺交、未测、低出勤和 AI 助学使用情况。' }
})

const abilityMetrics = computed(() => {
  const totals = summary.value?.totals || {}
  const aiRate = teacherAiActivityRate.value
  const classroom = clamp(((totals.attendance_rate || 0) * 0.65) + (aiRate * 0.35))
  const assignment = clamp(totals.assignment_completion_rate)
  const quiz = clamp(totals.quiz_completion_rate)
  const attendance = clamp(totals.attendance_rate)
  return [
    { label: '自主学习与任务完成', short: '任务', text: `${Math.round(assignment)}%`, width: `${assignment}%`, value: assignment, color: '#0b63b6' },
    { label: '知识掌握与测验表现', short: '测验', text: `${Math.round(quiz)}%`, width: `${quiz}%`, value: quiz, color: '#3478d8' },
    { label: '学习投入与出勤稳定', short: '考勤', text: `${Math.round(attendance)}%`, width: `${attendance}%`, value: attendance, color: '#14a46f' },
    { label: '课堂表现与参与质量', short: '课堂', text: `${Math.round(classroom)}%`, width: `${classroom}%`, value: classroom, color: '#22a06b' },
    { label: 'AI 助学与问题意识', short: 'AI', text: `${Math.round(aiRate)}%`, width: `${aiRate}%`, value: aiRate, color: '#d8890b' },
  ]
})

const strongestAbility = computed(() => [...abilityMetrics.value].sort((a, b) => b.value - a.value)[0] || {
  short: '--',
  text: '--',
})

const weakestAbility = computed(() => [...abilityMetrics.value].sort((a, b) => a.value - b.value)[0] || {
  short: '--',
  text: '--',
})

function abilityLevel(value: number) {
  if (value >= 85) return 'good'
  if (value >= 70) return 'stable'
  return 'warn'
}

function abilityHint(value: number) {
  if (value >= 90) return '优势明显，可沉淀为示范案例'
  if (value >= 80) return '运行稳定，保持当前教学节奏'
  if (value >= 70) return '基本可控，建议增加过程提醒'
  return '需要重点跟进，安排定向干预'
}

function widthToValue(width: string) {
  const value = Number.parseFloat(String(width || '').replace('%', ''))
  return Number.isFinite(value) ? clamp(value) : 0
}

const abilityChartMetrics = computed(() => abilityMetrics.value.map(item => ({
  label: item.label,
  short: item.short,
  text: item.text,
  width: item.width,
  value: widthToValue(item.width),
  color: item.color,
})))

const teacherRadarSeries = computed(() => {
  const baseValues = abilityChartMetrics.value.map(item => item.value)
  const rows = summary.value?.risk_students || []
  const count = Math.max(1, rows.length)
  const riskValues = rows.length ? [
    clamp(100 - rows.reduce((sum: number, item: any) => sum + (item.pending_assignments || 0), 0) / count * 24),
    clamp(100 - rows.reduce((sum: number, item: any) => sum + (item.missing_quizzes || 0), 0) / count * 32),
    clamp(rows.reduce((sum: number, item: any) => sum + (item.attendance_rate ?? 70), 0) / count),
    clamp(rows.reduce((sum: number, item: any) => sum + Math.max(35, (item.attendance_rate ?? 70) - (item.status_level === 'danger' ? 20 : 8)), 0) / count),
    clamp(rows.reduce((sum: number, item: any) => sum + (item.ai_questions || 0), 0) / count / 5 * 100),
  ] : baseValues.map(value => clamp(value - 12))
  return [
    { name: '班级均值', color: '#0b63b6', values: baseValues },
    { name: '需关注群体', color: '#d8890b', values: riskValues },
    { name: '课程目标', color: '#14a46f', values: [90, 88, 92, 88, 82] },
  ]
})

const teacherDistributionSegments = computed(() => {
  const totals = summary.value?.totals || {}
  const riskRate = (totals.risk_students || 0) / Math.max(1, totals.students || 1) * 100
  return [
    { label: '任务完成', value: clamp(totals.assignment_completion_rate || 0), color: '#0b63b6' },
    { label: '测验掌握', value: clamp(totals.quiz_completion_rate || 0), color: '#3478d8' },
    { label: '出勤投入', value: clamp(totals.attendance_rate || 0), color: '#14a46f' },
    { label: 'AI 活跃', value: teacherAiActivityRate.value, color: '#d8890b' },
    { label: '重点关注压力', value: clamp(riskRate), color: '#df6ea5', reverse: true },
  ]
})

const heatRows = computed(() => {
  return (summary.value?.risk_students || []).map((student: any) => {
    const assignmentScore = student.pending_assignments > 0 ? Math.max(20, 100 - student.pending_assignments * 24) : 90
    const quizScore = student.missing_quizzes > 0 ? Math.max(25, 100 - student.missing_quizzes * 32) : 88
    const attendanceScore = student.attendance_rate == null ? 70 : student.attendance_rate
    const classroomScore = student.attendance_rate == null ? 70 : Math.max(35, student.attendance_rate - (student.status_level === 'danger' ? 20 : 8))
    const aiScore = clamp((student.ai_questions || 0) / 5 * 100)
    return {
      ...student,
      cells: [
        { label: '作业', text: student.pending_assignments, level: levelByScore(assignmentScore) },
        { label: '测验', text: student.missing_quizzes, level: levelByScore(quizScore) },
        { label: '考勤', text: percentText(student.attendance_rate), level: levelByScore(attendanceScore) },
        { label: '课堂', text: `${Math.round(classroomScore)}%`, level: levelByScore(classroomScore) },
        { label: 'AI', text: `${Math.round(aiScore)}%`, level: levelByScore(aiScore) },
      ],
    }
  })
})

const suggestions = computed(() => {
  const totals = summary.value?.totals || {}
  const rows = summary.value?.risk_students || []
  const primary = rows[0]
  return [
    {
      title: '优先跟进低完成率学生',
      detail: primary ? `先联系 ${primary.student_name}，核查“${primary.first_recommendation}”并确认补交时间。` : '当前无需集中补交提醒，可保持常规节奏。',
    },
    {
      title: '调整下一次课堂节奏',
      detail: (totals.quiz_completion_rate || 0) < 90 ? '测验完成率偏低，建议课前推送知识点清单并在课中安排 5 分钟即时测。' : '测验完成率较稳，可增加综合应用题和工程案例讨论。',
    },
    {
      title: '引导 AI 助学闭环',
      detail: (totals.ai_questions || 0) < (totals.students || 0) * 3 ? 'AI 助学提问偏少，建议把课后问题链作为作业说明的一部分。' : 'AI 助学活跃度较好，可将高频问题回流到知识图谱。',
    },
  ]
})

const aiInterventionSuggestions = computed(() => {
  const fallbackSuggestions = suggestions.value
  if (!summary.value) return fallbackSuggestions
  const totals = summary.value?.totals || {}
  const rows = summary.value?.risk_students || []
  const primary = rows[0]
  const weak = weakestAbility.value as any
  const weakKey = weak?.short || ''
  const courseName = selectedCourse.value
    ? courses.value.find((course: any) => course.id === selectedCourse.value)?.name || '当前课程'
    : '自动测试系统A'

  const weakAdviceMap: Record<string, string> = {
    '任务': '把“滤波器幅频特性自动测试程序”和“VXIbus 中断与 DTB 仲裁分析”拆成补交清单，要求学生补齐源文件、运行截图、原始数据和误差分析。',
    '测验': '下一次课前安排 8 分钟错题回收，重点讲清 GPIB/SCPI/VISA 程控指令、VXI 地址译码和 IACK 响应链路。',
    '考勤': '把缺勤和迟到学生单独拉出名单，要求其完成对应课次的知识点小测和实验步骤复盘，避免只补文件不补过程。',
    '课堂': '课堂巡查时优先关注低参与小组，围绕资源地址配置、仪器连线确认和异常恢复流程进行现场提问。',
    'AI': '将学生高频问题整理为知识图谱节点，例如 VISA 会话流程、SCPI 错误队列、滤波器频点设计和课程报告可追溯证据链。',
  }

  return [
    {
      title: primary ? `优先跟进 ${primary.student_name} 的过程短板` : '保持当前教学节奏',
      detail: primary
        ? `${courseName} 中该生仍存在 ${primary.pending_assignments || 0} 项作业/报告、${primary.missing_quizzes || 0} 次测验或课堂投入不足。建议先核对“${primary.first_recommendation || '补齐缺失任务并复盘薄弱知识点'}”，给出明确补交时间和复核方式。`
        : '当前未识别到集中风险学生，可继续保持作业、测验、考勤和课堂表现的过程跟踪。',
    },
    {
      title: `${weakKey || '能力'} 维度优先补强`,
      detail: weakAdviceMap[weakKey] || '结合热力图中红色和黄色指标，先处理完成率、测验掌握、出勤稳定性、课堂表现和 AI 助学中最低的一项。',
    },
    {
      title: '形成下一次课的闭环动作',
      detail: `建议把本次分析转化为 3 个课堂动作：课前推送 SCPI/VISA 与 VXI 地址译码速查表，课中用 1 道小测定位薄弱点，课后要求学生用 AI 助学追问并把关键回答写入实验或课程报告。当前作业报告完成 ${percentText(totals.assignment_completion_rate)}，测验完成 ${percentText(totals.quiz_completion_rate)}，出勤 ${percentText(totals.attendance_rate)}。`,
    },
  ]
})

async function loadData() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedCourse.value) params.course_id = selectedCourse.value
    const res = await axios.get('/api/v1/learning/teacher-summary', { params })
    summary.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await axios.get('/api/v1/courses/my')
  courses.value = (res.data || []).filter((course: any) => {
    const code = course.course_code || ''
    const name = course.name || ''
    return !code.startsWith('QA') && !code.startsWith('ACCEPT-') && !name.startsWith('系统验收')
  })
  await loadData()
})
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.6; }
.header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.hidden-input { display: none; }
.refresh-btn, .ghost-btn, .data-link { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px; padding: 9px 14px; font-weight: 800; cursor: pointer; text-decoration: none; }
.refresh-btn { background: #0b63b6; border: 1px solid #0b63b6; color: #ffffff; }
.ghost-btn, .data-link { background: #ffffff; border: 1px solid #c8ddf4; color: #0b63b6; }
.filter-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.sel { min-width: 240px; background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; outline: none; padding: 9px 12px; }
.diagnosis-band { display: flex; justify-content: space-between; gap: 18px; align-items: center; background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); margin-bottom: 16px; }
.diagnosis-band span { color: #0b63b6; font-size: 12px; font-weight: 900; }
.diagnosis-band h2 { color: #0f2f64; font-size: 20px; margin: 7px 0; }
.diagnosis-band p { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 0; }
.diagnosis-band > strong { color: #0f2f64; font-size: 42px; line-height: 1; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 16px; }
.metric-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 15px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.metric-card.warn { border-top: 3px solid #d8890b; }
.metric-card span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 8px; }
.metric-card strong { color: #0f2f64; font-size: 28px; line-height: 1; }
.analysis-layout { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(360px, .65fr); gap: 16px; margin-bottom: 16px; }
.panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.panel-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 17px; margin: 0; }
.panel-head p { color: #5b6f92; font-size: 12px; margin: 5px 0 0; line-height: 1.6; }
.heatmap { display: grid; gap: 8px; overflow-x: auto; }
.heat-head, .heat-row { display: grid; grid-template-columns: 170px repeat(5, minmax(64px, .5fr)) minmax(220px, 1.2fr); gap: 8px; align-items: stretch; min-width: 820px; }
.heat-head { color: #5b6f92; font-size: 12px; padding: 0 8px; }
.heat-row { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 8px; }
.heat-name strong { display: block; color: #0f2f64; font-size: 13px; }
.heat-name em { display: block; color: #5b6f92; font-size: 11px; font-style: normal; margin-top: 3px; }
.heat-cell { display: flex; align-items: center; justify-content: center; border-radius: 7px; font-weight: 900; font-size: 12px; }
.heat-cell.ok { background: #e8f7f0; color: #0b7d56; }
.heat-cell.mid { background: #fff8e6; color: #9a5a00; }
.heat-cell.high { background: #fff0ef; color: #cf3434; }
.heat-row p { color: #5b6f92; font-size: 12px; line-height: 1.5; margin: 0; }
.ability-matrix { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.ability-tile { min-height: 118px; border: 1px solid #e1ecf8; background: #f8fbff; border-radius: 9px; padding: 12px; display: flex; flex-direction: column; gap: 9px; }
.ability-tile.good { background: #f4fbf8; border-color: #cbead9; }
.ability-tile.stable { background: #fffaf0; border-color: #f1dfb7; }
.ability-tile.warn { background: #fff7f6; border-color: #f4ceca; }
.tile-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.tile-top span { width: 34px; height: 34px; border-radius: 9px; display: inline-flex; align-items: center; justify-content: center; color: #ffffff; font-size: 12px; font-weight: 900; flex: none; }
.tile-top strong { color: #0f2f64; font-size: 20px; line-height: 1; }
.ability-tile h3 { color: #0f2f64; font-size: 13px; line-height: 1.35; margin: 0; }
.tile-meter { height: 8px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.tile-meter i { display: block; height: 100%; border-radius: inherit; }
.ability-tile p { color: #5b6f92; font-size: 11px; line-height: 1.45; margin: 0; }
.ability-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.ability-summary div { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 11px 12px; }
.ability-summary span { display: block; color: #5b6f92; font-size: 11px; margin-bottom: 5px; }
.ability-summary strong { color: #0f2f64; font-size: 13px; }
.suggestion-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.suggestion-card { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 13px; }
.suggestion-card strong { color: #0f2f64; font-size: 14px; }
.suggestion-card p { color: #5b6f92; font-size: 12px; line-height: 1.6; margin: 7px 0 0; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 24px; text-align: center; background: #f8fbff; }
@media (max-width: 1280px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .analysis-layout { grid-template-columns: 1fr; }
}
@media (max-width: 820px) {
  .page { padding: 20px; }
  .page-header, .filter-bar, .diagnosis-band { flex-direction: column; align-items: flex-start; }
  .header-actions { justify-content: flex-start; }
  .metric-grid, .suggestion-grid, .ability-matrix, .ability-summary { grid-template-columns: 1fr; }
}
</style>
