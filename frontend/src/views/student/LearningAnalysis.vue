<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">我的学情分析</h1>
        <p class="page-sub">{{ studentName }} · 基于作业、测验、考勤、课堂表现和 AI 助学记录生成个人学习画像。</p>
      </div>
      <button class="refresh-btn" @click="load" :disabled="loading">
        <el-icon><Refresh /></el-icon>
        {{ loading ? '刷新中' : '刷新分析' }}
      </button>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>
    <div v-if="loading && !summary" class="empty">分析生成中...</div>

    <template v-if="summary">
      <section class="diagnosis-band">
        <div>
          <span>AI 学习诊断</span>
          <h2>{{ diagnosis.title }}</h2>
          <p>{{ diagnosis.detail }}</p>
        </div>
        <strong>{{ valueText(summary.average_score) }}</strong>
      </section>

      <div class="metric-grid">
        <div class="metric-card"><span>课程数</span><strong>{{ summary.courses_count }}</strong></div>
        <div class="metric-card"><span>作业报告完成</span><strong>{{ percentText(summary.assignment_completion_rate) }}</strong></div>
        <div class="metric-card"><span>测验完成</span><strong>{{ percentText(summary.quiz_completion_rate) }}</strong></div>
        <div class="metric-card"><span>出勤率</span><strong>{{ percentText(summary.attendance_rate) }}</strong></div>
        <div class="metric-card"><span>AI 助学活跃</span><strong>{{ percentText(aiActivityRate) }}</strong></div>
      </div>

      <LearningAnalyticsCharts
        :metrics="abilityChartMetrics"
        :series="studentRadarSeries"
        :segments="studentDistributionSegments"
        radar-title="个人能力雷达"
        radar-subtitle="对比个人画像、课程均值和学习目标"
        wheel-title="能力目标达成"
        wheel-subtitle="把作业、测验、考勤、课堂表现和 AI 助学映射成能力目标"
        distribution-title="个人学习结构分布"
        distribution-subtitle="展示学习投入在不同过程指标上的占比"
        distribution-center-title="个人"
        distribution-center-sub="结构"
      />

      <div class="analysis-layout">
        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>能力画像</h2>
              <p>和教师端保持同一评价口径，便于师生围绕同一组指标沟通。</p>
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

        <section class="panel">
          <div class="panel-head">
            <div>
              <h2>课程热力图</h2>
              <p>用于识别每门课的薄弱环节，具体逐课次数据见“课程学情”。</p>
            </div>
          </div>
          <div v-if="courseRows.length === 0" class="empty">暂无课程学情数据。</div>
          <div v-else class="heatmap">
            <div class="heat-head">
              <span>课程</span>
              <span v-for="metric in heatMetrics" :key="metric">{{ metric }}</span>
            </div>
            <div v-for="row in courseRows" :key="row.id" class="heat-row">
              <div class="heat-name">
                <strong>{{ row.name }}</strong>
                <em>{{ row.teacher_name || '未绑定教师' }}</em>
              </div>
              <div v-for="cell in row.cells" :key="cell.label" class="heat-cell" :class="cell.level">{{ cell.text }}</div>
            </div>
          </div>
        </section>
      </div>

      <section class="panel">
        <div class="panel-head">
          <div>
            <h2>下一步建议</h2>
            <p>由系统根据当前完成情况自动生成，建议结合“课程学情”的逐课次记录执行。</p>
          </div>
          <router-link to="/student/course-progress" class="text-link">查看课程学情</router-link>
        </div>
        <div class="recommend-grid">
          <div v-for="item in recommendations" :key="item.title" class="recommend-card" :class="item.level">
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
import { useAuthStore } from '@/stores/auth'
import LearningAnalyticsCharts from '@/components/LearningAnalyticsCharts.vue'

const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const summary = ref<any | null>(null)
const progress = ref<any | null>(null)
const heatMetrics = ['作业', '测验', '考勤', '课堂', 'AI']

const studentName = computed(() => summary.value?.student_name || auth.user?.full_name || auth.user?.username || '学生')
const clamp = (v?: number | null) => Math.max(0, Math.min(100, Number(v || 0)))
const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : Math.round(v)
const levelByScore = (value: number) => value >= 75 ? 'ok' : value >= 55 ? 'mid' : 'high'
const aiActivityRate = computed(() => {
  const s = summary.value || {}
  return clamp((s.ai_questions || 0) / Math.max(5, (s.courses_count || 1) * 5) * 100)
})

const diagnosis = computed(() => {
  const s = summary.value || {}
  if (s.status_level === 'danger') {
    return { title: '学习状态需要重点调整', detail: '当前存在多项未完成任务、低分或低出勤风险，请优先补齐最近任务并联系任课教师。' }
  }
  if (s.status_level === 'warning') {
    return { title: '部分环节需要跟进', detail: '整体学习仍可恢复，建议从未完成作业、未完成测验和出勤记录中选择最紧急项处理。' }
  }
  return { title: '学习节奏整体稳定', detail: '当前任务、测验、考勤和 AI 助学记录较完整，可继续推进高阶问题和课程报告。' }
})

const abilityMetrics = computed(() => {
  const s = summary.value || {}
  const aiRate = aiActivityRate.value
  const classroom = s.posture?.attentive_rate ?? clamp(((s.attendance_rate || 0) * 0.7) + (aiRate * 0.3))
  const assignment = clamp(s.assignment_completion_rate)
  const quiz = clamp(s.quiz_completion_rate)
  const attendance = clamp(s.attendance_rate)
  const classroomValue = clamp(classroom)
  return [
    { label: '作业报告完成', short: '任务', text: `${Math.round(assignment)}%`, width: `${assignment}%`, value: assignment, color: '#0b63b6' },
    { label: '测验知识掌握', short: '测验', text: `${Math.round(quiz)}%`, width: `${quiz}%`, value: quiz, color: '#3478d8' },
    { label: '考勤稳定程度', short: '考勤', text: `${Math.round(attendance)}%`, width: `${attendance}%`, value: attendance, color: '#14a46f' },
    { label: '课堂表现质量', short: '课堂', text: `${Math.round(classroomValue)}%`, width: `${classroomValue}%`, value: classroomValue, color: '#22a06b' },
    { label: 'AI 助学活跃', short: 'AI', text: `${Math.round(aiRate)}%`, width: `${aiRate}%`, value: aiRate, color: '#d8890b' },
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
  if (value >= 90) return '优势明显，继续保持当前节奏'
  if (value >= 80) return '表现稳定，可挑战高阶任务'
  if (value >= 70) return '基本可控，建议按周补齐记录'
  return '需要重点补强，优先处理最近任务'
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
  value: item.value ?? widthToValue(item.width),
  color: item.color,
})))

const courseAverageValues = computed(() => {
  const rows = courseRows.value
  if (!rows.length) return abilityChartMetrics.value.map(item => item.value)
  return heatMetrics.map((_metric, index) => {
    const values = rows.map((row: any) => Number(row.cells[index]?.score ?? 0)).filter(Number.isFinite)
    if (!values.length) return abilityChartMetrics.value[index]?.value || 0
    return clamp(values.reduce((sum: number, value: number) => sum + value, 0) / values.length)
  })
})

const studentRadarSeries = computed(() => [
  { name: '个人画像', color: '#0b63b6', values: abilityChartMetrics.value.map(item => item.value) },
  { name: '课程均值', color: '#d8890b', values: courseAverageValues.value },
  { name: '目标线', color: '#14a46f', values: [90, 88, 92, 88, 80] },
])

const studentDistributionSegments = computed(() => {
  const s = summary.value || {}
  const aiRate = aiActivityRate.value
  return [
    { label: '作业报告', value: clamp(s.assignment_completion_rate || 0), color: '#0b63b6' },
    { label: '测验掌握', value: clamp(s.quiz_completion_rate || 0), color: '#3478d8' },
    { label: '考勤投入', value: clamp(s.attendance_rate || 0), color: '#14a46f' },
    { label: '课堂表现', value: clamp(s.posture?.attentive_rate ?? s.attendance_rate ?? 0), color: '#22a06b' },
    { label: 'AI 助学', value: aiRate, color: '#d8890b' },
  ]
})

const courseRows = computed(() => {
  return (progress.value?.courses || []).map((course: any) => {
    const aiMax = Math.max(5, ...(progress.value?.courses || []).map((item: any) => item.qa_records || 0))
    const classroom = course.classroom_rate ?? course.attendance_rate
    const aiRate = clamp((course.qa_records || 0) / aiMax * 100)
    const cells = [
      { label: '作业', text: percentText(course.assignment_completion_rate), score: course.assignment_completion_rate ?? 70 },
      { label: '测验', text: percentText(course.quiz_completion_rate), score: course.quiz_completion_rate ?? 70 },
      { label: '考勤', text: percentText(course.attendance_rate), score: course.attendance_rate ?? 70 },
      { label: '课堂', text: percentText(classroom), score: classroom ?? 70 },
      { label: 'AI', text: `${Math.round(aiRate)}%`, score: aiRate },
    ]
    return {
      ...course,
      cells: cells.map(cell => ({ ...cell, level: levelByScore(Number(cell.score || 0)) })),
    }
  })
})

const recommendations = computed(() => {
  const rows = summary.value?.recommendations || []
  if (rows.length) return rows.slice(0, 4)
  return [{ level: 'success', title: '保持当前节奏', detail: '当前学习过程数据较完整，请继续按周查看课程学情。' }]
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [summaryRes, progressRes] = await Promise.all([
      axios.get('/api/v1/learning/my-summary'),
      axios.get('/api/v1/learning/student-progress'),
    ])
    summary.value = summaryRes.data
    progress.value = progressRes.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || '学情分析加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 18px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.6; }
.refresh-btn, .text-link { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px; padding: 9px 14px; font-weight: 800; text-decoration: none; }
.refresh-btn { background: #0b63b6; color: #ffffff; border: 1px solid #0b63b6; cursor: pointer; white-space: nowrap; }
.refresh-btn:disabled { opacity: .6; cursor: wait; }
.text-link { background: #ffffff; border: 1px solid #c8ddf4; color: #0b63b6; }
.error-box { border: 1px solid #ffd5cf; background: #fff4f2; color: #cf3434; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; }
.diagnosis-band, .panel, .metric-card { background: #ffffff; border: 1px solid #d9e7f7; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.diagnosis-band { display: flex; justify-content: space-between; align-items: center; gap: 18px; border-radius: 10px; padding: 18px; margin-bottom: 16px; }
.diagnosis-band span { color: #0b63b6; font-size: 12px; font-weight: 900; }
.diagnosis-band h2 { color: #0f2f64; font-size: 20px; margin: 7px 0; }
.diagnosis-band p { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 0; }
.diagnosis-band > strong { color: #0f2f64; font-size: 42px; line-height: 1; }
.metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.metric-card { border-radius: 9px; padding: 15px; }
.metric-card span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 8px; }
.metric-card strong { color: #0f2f64; font-size: 28px; line-height: 1; }
.analysis-layout { display: grid; grid-template-columns: .8fr 1.2fr; gap: 16px; margin-bottom: 16px; }
.panel { border-radius: 10px; padding: 18px; }
.panel-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 17px; margin: 0; }
.panel-head p { color: #5b6f92; font-size: 12px; margin: 5px 0 0; line-height: 1.6; }
.ability-matrix { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }
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
.heatmap { display: grid; gap: 8px; overflow-x: auto; }
.heat-head, .heat-row { display: grid; grid-template-columns: 170px repeat(5, minmax(62px, .5fr)); gap: 8px; align-items: stretch; min-width: 560px; }
.heat-head { color: #5b6f92; font-size: 12px; padding: 0 8px; }
.heat-row { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 8px; }
.heat-name strong { display: block; color: #0f2f64; font-size: 13px; }
.heat-name em { display: block; color: #5b6f92; font-size: 11px; font-style: normal; margin-top: 3px; }
.heat-cell { display: flex; align-items: center; justify-content: center; border-radius: 7px; font-weight: 900; font-size: 12px; }
.heat-cell.ok { background: #e8f7f0; color: #0b7d56; }
.heat-cell.mid { background: #fff8e6; color: #9a5a00; }
.heat-cell.high { background: #fff0ef; color: #cf3434; }
.recommend-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.recommend-card { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 9px; padding: 13px; }
.recommend-card.warning { background: #fff8e6; border-color: #fde4a8; }
.recommend-card.danger { background: #fff4f2; border-color: #ffd5cf; }
.recommend-card strong { color: #0f2f64; font-size: 14px; }
.recommend-card p { color: #5b6f92; font-size: 12px; line-height: 1.6; margin: 7px 0 0; }
.empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 24px; text-align: center; background: #f8fbff; }
@media (max-width: 1280px) {
  .metric-grid, .recommend-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .analysis-layout { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .page { padding: 18px; }
  .page-header, .diagnosis-band, .panel-head { flex-direction: column; align-items: flex-start; }
  .metric-grid, .recommend-grid, .ability-summary { grid-template-columns: 1fr; }
}
</style>
