<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">我的课程学情</h1>
        <p class="page-sub">
          {{ data?.student?.full_name || auth.user?.full_name || auth.user?.username }} · 按当前课表汇总作业、报告、测验、资料、考勤和课程问答
        </p>
      </div>
      <button class="refresh-btn" @click="load" :disabled="loading" title="刷新数据">
        <el-icon><Refresh /></el-icon>
        <span>{{ loading ? '刷新中' : '刷新数据' }}</span>
      </button>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div class="metric-grid">
      <div class="metric-card cyan">
        <span>课表课程</span>
        <strong>{{ totals.courses || 0 }}</strong>
        <small>仅统计当前课表正式课程</small>
      </div>
      <div class="metric-card indigo">
        <span>作业完成</span>
        <strong>{{ doneText(totals.assignments_done, nonReportTotal) }}</strong>
        <small>课程报告 {{ doneText(totals.reports_done, totals.reports) }}</small>
      </div>
      <div class="metric-card amber">
        <span>测验完成</span>
        <strong>{{ doneText(totals.quizzes_done, totals.quizzes) }}</strong>
        <small>{{ totals.quiz_questions || 0 }} 道课程题目</small>
      </div>
      <div class="metric-card green">
        <span>课程资料</span>
        <strong>{{ totals.resources || 0 }}</strong>
        <small>来自课程资料库匹配</small>
      </div>
      <div class="metric-card blue">
        <span>课程问答</span>
        <strong>{{ totals.qa_records || 0 }}</strong>
        <small>平均响应 {{ responseTimeText }}</small>
      </div>
      <div class="metric-card rose">
        <span>综合成绩</span>
        <strong>{{ valueText(totals.average_score) }}</strong>
        <small>出勤 {{ percentText(totals.attendance_rate) }}</small>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>课程总体情况</h2>
          <p>按每门课程独立统计，避免不同课程之间互相混入。</p>
        </div>
        <span>{{ totals.attended_sessions || 0 }} / {{ totals.attendance_sessions || 0 }} 次出勤</span>
      </div>
      <div class="summary-grid">
        <div class="summary-item">
          <span>作业与报告完成率</span>
          <strong>{{ percentText(totals.assignment_completion_rate) }}</strong>
        </div>
        <div class="summary-item">
          <span>测验完成率</span>
          <strong>{{ percentText(totals.quiz_completion_rate) }}</strong>
        </div>
        <div class="summary-item">
          <span>出勤率</span>
          <strong>{{ percentText(totals.attendance_rate) }}</strong>
        </div>
        <div class="summary-item">
          <span>课程平均分</span>
          <strong>{{ valueText(totals.average_score) }}</strong>
        </div>
      </div>
    </section>

    <section class="course-grid">
      <article v-for="course in data?.courses || []" :key="course.id" class="course-card">
        <div class="course-head">
          <div>
            <h2>{{ course.name }}</h2>
            <p>{{ course.course_code }} · {{ course.teacher_name || '未绑定教师' }}</p>
          </div>
          <span :class="['status-pill', statusClass(course.status_label)]">{{ course.status_label }}</span>
        </div>

        <div class="course-numbers">
          <div>
            <span>作业</span>
            <strong>{{ doneText(course.assignments_done, course.assignments_total - course.reports_total) }}</strong>
          </div>
          <div>
            <span>报告</span>
            <strong>{{ doneText(course.reports_done, course.reports_total) }}</strong>
          </div>
          <div>
            <span>测验</span>
            <strong>{{ doneText(course.quizzes_done, course.quizzes_total) }}</strong>
          </div>
          <div>
            <span>成绩</span>
            <strong>{{ valueText(course.average_score) }}</strong>
          </div>
        </div>

        <div class="timeline-panel">
          <div class="timeline-head">
            <div>
              <strong>逐课次学习记录</strong>
              <span>共 {{ timelineSlots(course).length }} 次课，格子编号对应实际上课顺序</span>
            </div>
            <div class="timeline-legend">
              <span><i class="state-done"></i>已完成/出勤</span>
              <span><i class="state-missing"></i>未完成/缺勤</span>
              <span><i class="state-late"></i>迟到</span>
              <span><i class="state-none"></i>未安排</span>
              <span><i class="state-upcoming"></i>未开始</span>
            </div>
          </div>

          <div class="timeline-scroll">
            <div class="timeline-line ruler">
              <span class="track-label">课次</span>
              <div class="slot-grid" :style="timelineGridStyle(course)">
                <span v-for="slot in timelineSlots(course)" :key="`index-${slot.index}`" class="slot-index">
                  {{ slot.index }}
                </span>
              </div>
              <span class="track-count">{{ timelineSlots(course).length }} 次</span>
            </div>

            <div v-for="track in timelineTracks" :key="track.key" class="timeline-line">
              <span class="track-label">{{ track.label }}</span>
              <div class="slot-grid" :style="timelineGridStyle(course)">
                <button
                  v-for="slot in timelineSlots(course)"
                  :key="`${track.key}-${slot.index}`"
                  type="button"
                  :class="['slot-cell', `state-${slot[track.key]?.state || 'none'}`]"
                  :title="timelineTitle(slot, track)"
                >
                  {{ timelineMark(slot[track.key]?.state) }}
                </button>
              </div>
              <span class="track-count">{{ trackCountText(course, track.key) }}</span>
            </div>
          </div>
        </div>

        <div class="course-meta">
          <span>资料 {{ course.resources_count }}</span>
          <span>题目 {{ course.question_count }}</span>
          <span>问答 {{ course.qa_records }}</span>
        </div>
        <div class="schedule">{{ scheduleText(course.schedule) }}</div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const data = ref<any | null>(null)

const totals = computed(() => data.value?.totals || {})
const nonReportTotal = computed(() => Math.max(0, (totals.value.assignments || 0) - (totals.value.reports || 0)))
const responseTimeText = computed(() => {
  const ms = totals.value.avg_response_ms
  return ms == null ? '--' : `${(ms / 1000).toFixed(1)}s`
})

const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}`
const doneText = (done?: number | null, total?: number | null) => `${done || 0}/${total || 0}`
const timelineTracks = [
  { key: 'homework', label: '作业' },
  { key: 'report', label: '报告' },
  { key: 'quiz', label: '测验' },
  { key: 'attendance', label: '出勤' },
]

function timelineGridStyle(course: any) {
  const count = Math.max(1, timelineSlots(course).length || 1)
  return {
    gridTemplateColumns: `repeat(${count}, 22px)`,
    minWidth: `${count * 26}px`,
  }
}

function timelineSlots(course: any) {
  const existing = Array.isArray(course?.learning_timeline) ? course.learning_timeline : []
  if (existing.length) return existing
  const count = Math.max(
    0,
    Number(course?.session_count || course?.planned_sessions || course?.attendance_sessions || 0),
  )
  return Array.from({ length: count }, (_, i) => ({
    index: i + 1,
    homework: { state: 'none', label: '本次未安排' },
    report: { state: 'none', label: '本次未安排' },
    quiz: { state: 'none', label: '本次未安排' },
    attendance: { state: 'unrecorded', label: '未记录' },
  }))
}

function timelineMark(state?: string) {
  if (state === 'done' || state === 'present') return '✓'
  if (state === 'late') return '迟'
  return ''
}

function trackCountText(course: any, key: string) {
  if (key === 'homework') return doneText(course.assignments_done, Math.max(0, (course.assignments_total || 0) - (course.reports_total || 0)))
  if (key === 'report') return doneText(course.reports_done, course.reports_total)
  if (key === 'quiz') return doneText(course.quizzes_done, course.quizzes_total)
  return doneText(course.attended_sessions, course.attendance_sessions)
}

function timelineTitle(slot: any, track: any) {
  const dayChars = '一二三四五六日'
  const info = slot?.[track.key] || { state: 'none' }
  const parts = [
    `第${slot.index}次课`,
    slot.week ? `第${slot.week}周` : '',
    slot.day_of_week ? `星期${dayChars[slot.day_of_week - 1] || slot.day_of_week}` : '',
    slot.start_session ? `${slot.start_session}-${slot.end_session}节` : '',
    slot.location || '',
    `${track.label}：${info.label || (info.state === 'none' ? '本次未安排' : '未记录')}`,
    info.title || '',
    info.score != null ? `得分 ${Math.round(info.score)}` : '',
  ]
  return parts.filter(Boolean).join(' · ')
}

function statusClass(label: string) {
  if (label === '优秀') return 'good'
  if (label === '需关注') return 'warn'
  return 'stable'
}

function scheduleText(rows: any[]) {
  if (!rows?.length) return '暂无课表时间'
  const dayChars = '一二三四五六日'
  return rows.slice(0, 2).map((row) => {
    const day = row.day_of_week ? `星期${dayChars[row.day_of_week - 1] || row.day_of_week}` : '未排课'
    const session = row.start_session ? `${row.start_session}-${row.end_session}节` : '节次未定'
    return `${day} ${session} ${row.weeks || ''} ${row.location || ''}`.trim()
  }).join('；')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const r = await axios.get('/api/v1/learning/student-progress')
    data.value = r.data
  } catch (e: any) {
    try {
      const username = auth.user?.username || '2300840126'
      const fallback = await axios.get('/api/v1/acceptance/student-subjects', { params: { username } })
      data.value = fallback.data
      error.value = '当前后端未加载正式课程学情接口，已临时使用验收数据。请重启后端完成升级。'
    } catch (fallbackError: any) {
      error.value = fallbackError.response?.data?.detail || e.response?.data?.detail || '课程学情加载失败，请先确认已生成课程数据'
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.page-title { color: #0f2f64; font-size: 26px; font-weight: 900; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.5; }
.refresh-btn { display: inline-flex; align-items: center; gap: 8px; background: #0b63b6; border: 1px solid #0b63b6; color: #ffffff; border-radius: 8px; padding: 9px 14px; font-weight: 800; cursor: pointer; }
.refresh-btn:disabled { opacity: 0.6; cursor: wait; }
.error-box { border: 1px solid #ffd5cf; background: #fff4f2; color: #cf3434; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; }
.metric-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.metric-card { border: 1px solid #d9e7f7; border-radius: 8px; padding: 15px; background: #ffffff; min-height: 96px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.metric-card span, .metric-card small { color: #5b6f92; font-size: 12px; }
.metric-card strong { color: #0f2f64; font-size: 29px; line-height: 1; margin-top: 8px; }
.metric-card.cyan, .metric-card.blue { border-top: 3px solid #0b63b6; }
.metric-card.indigo { border-top: 3px solid #3478d8; }
.metric-card.amber { border-top: 3px solid #d8890b; }
.metric-card.green { border-top: 3px solid #14a46f; }
.metric-card.rose { border-top: 3px solid #cf3434; }
.panel, .course-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 8px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.panel { padding: 18px; margin-bottom: 16px; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 16px; margin: 0; }
.panel-head p, .panel-head span { color: #5b6f92; font-size: 12px; margin: 4px 0 0; line-height: 1.5; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.summary-item { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 13px; }
.summary-item span { color: #5b6f92; font-size: 12px; }
.summary-item strong { display: block; color: #0f2f64; font-size: 24px; margin-top: 6px; }
.course-grid { display: grid; grid-template-columns: 1fr; gap: 14px; }
.course-card { padding: 18px; min-width: 0; }
.course-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.course-head h2 { color: #0f2f64; font-size: 16px; margin: 0; line-height: 1.35; }
.course-head p { color: #5b6f92; font-size: 12px; margin: 6px 0 0; }
.status-pill { border-radius: 8px; padding: 5px 8px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.status-pill.good { color: #0b7d56; background: #e8f7f0; }
.status-pill.stable { color: #0b63b6; background: #eaf3ff; }
.status-pill.warn { color: #9a5a00; background: #fff2d9; }
.course-numbers { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.course-numbers div { background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 9px; }
.course-numbers span { color: #5b6f92; font-size: 11px; }
.course-numbers strong { display: block; color: #0f2f64; font-size: 16px; margin-top: 4px; }
.timeline-panel { margin-top: 16px; border-top: 1px solid #edf3fb; padding-top: 14px; }
.timeline-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 12px; }
.timeline-head strong { display: block; color: #0f2f64; font-size: 13px; }
.timeline-head > div > span { display: block; color: #5b6f92; font-size: 11px; margin-top: 4px; }
.timeline-legend { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px 12px; }
.timeline-legend span { display: inline-flex !important; align-items: center; gap: 5px; margin: 0 !important; white-space: nowrap; color: #5b6f92; }
.timeline-legend i { width: 10px; height: 10px; border-radius: 2px; border: 1px solid transparent; }
.timeline-legend i.state-done { background: #14a46f; border-color: #14a46f; }
.timeline-legend i.state-missing { background: #ffffff; border-color: #cf3434; box-shadow: inset 0 0 0 2px #ffffff; }
.timeline-legend i.state-late { background: #d8890b; border-color: #d8890b; }
.timeline-legend i.state-none { background: #edf3fb; border-color: #d9e7f7; }
.timeline-legend i.state-upcoming { background: #dce6f2; border-color: #c8d5e5; }
.timeline-scroll { overflow-x: auto; padding: 2px 0 8px; }
.timeline-scroll::-webkit-scrollbar { height: 6px; }
.timeline-scroll::-webkit-scrollbar-thumb { background: rgba(11,99,182,0.26); border-radius: 3px; }
.timeline-line { display: grid; grid-template-columns: 62px max-content 58px; align-items: center; gap: 10px; width: max-content; min-width: 100%; margin-bottom: 7px; }
.timeline-line.ruler { margin-bottom: 8px; }
.track-label, .track-count { color: #5b6f92; font-size: 11px; font-weight: 800; white-space: nowrap; }
.track-count { text-align: right; }
.slot-grid { display: grid; gap: 4px; width: max-content; }
.slot-index { display: flex; align-items: center; justify-content: center; width: 22px; color: #7c8da8; font-size: 9px; line-height: 18px; }
.slot-cell { width: 22px; height: 22px; padding: 0; border-radius: 4px; border: 1px solid #d9e7f7; background: #edf3fb; color: #7c8da8; font-size: 10px; font-weight: 900; cursor: help; }
.slot-cell.state-done, .slot-cell.state-present { color: #ffffff; background: #14a46f; border-color: #14a46f; }
.slot-cell.state-missing, .slot-cell.state-absent {
  color: transparent;
  background: #ffffff;
  border-color: #cf3434;
  box-shadow: inset 0 0 0 2px #ffffff;
}
.slot-cell.state-late { color: #ffffff; background: #d8890b; border-color: #d8890b; font-size: 9px; }
.slot-cell.state-upcoming { background: #dce6f2; border-color: #c8d5e5; color: #7c8da8; }
.slot-cell.state-unrecorded { color: #0b63b6; background: #eaf3ff; border-color: #c8ddf4; }
.slot-cell:hover { transform: translateY(-1px); filter: brightness(1.04); }
.course-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.course-meta span { color: #5b6f92; background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 7px; padding: 4px 7px; font-size: 12px; }
.schedule { color: #5b6f92; font-size: 12px; line-height: 1.45; margin-top: 10px; min-height: 34px; }
@media (max-width: 1280px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .page { padding: 18px; }
  .page-header { flex-direction: column; }
  .metric-grid, .summary-grid, .course-grid { grid-template-columns: 1fr; }
  .timeline-head { flex-direction: column; }
  .timeline-legend { justify-content: flex-start; }
}
</style>
