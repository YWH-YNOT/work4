<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">课程学情</h1>
        <p class="page-sub">面向单门课程展示真实过程数据：作业、报告、测验、考勤、课堂表现和 AI 助学使用情况。</p>
      </div>
      <div class="header-actions">
        <select v-model.number="selectedCourseId" class="course-select" @change="load">
          <option v-for="course in courses" :key="course.id" :value="course.id">
            {{ course.name }} · {{ course.course_code }}
          </option>
        </select>
        <button class="refresh-btn" @click="load" :disabled="loading">
          <el-icon><Refresh /></el-icon>
          {{ loading ? '刷新中' : '刷新数据' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <section v-if="selectedCourse" class="course-band">
      <div>
        <h2>{{ selectedCourse.name }}</h2>
        <p>{{ selectedCourse.course_code }} · {{ selectedCourse.teacher_name || '未绑定教师' }} · {{ scheduleText(selectedCourse.schedule) }}</p>
      </div>
      <div class="course-tags">
        <span>作业 {{ selectedCourse.assignments_total }}</span>
        <span>报告 {{ selectedCourse.reports_total }}</span>
        <span>测验 {{ selectedCourse.quizzes_total }}</span>
        <span>资料 {{ selectedCourse.resources_count }}</span>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>课程总体情况</h2>
          <p>只统计当前选中课程，不合并其他课程数据。</p>
        </div>
        <span>{{ totals.students || 0 }} 名学生</span>
      </div>
      <div class="metric-grid">
        <div class="metric-card"><span>作业报告完成率</span><strong>{{ percentText(totals.assignment_completion_rate) }}</strong></div>
        <div class="metric-card"><span>测验完成率</span><strong>{{ percentText(totals.quiz_completion_rate) }}</strong></div>
        <div class="metric-card"><span>出勤率</span><strong>{{ percentText(totals.attendance_rate) }}</strong></div>
        <div class="metric-card"><span>平均成绩</span><strong>{{ valueText(totals.average_score) }}</strong></div>
        <div class="metric-card"><span>课程问答</span><strong>{{ totals.qa_records || 0 }}</strong></div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h2>学生具体情况</h2>
          <p>每名学生按五类评价指标展示完成进度，进一步细节可进入作业、测验、考勤等模块核查。</p>
        </div>
        <span>{{ filteredStudents.length }} / {{ students.length }} 名学生</span>
      </div>

      <div class="student-tools">
        <div class="status-tabs">
          <button
            v-for="tab in statusTabs"
            :key="tab.value"
            type="button"
            :class="{ active: statusFilter === tab.value }"
            @click="statusFilter = tab.value"
          >
            {{ tab.label }} <span>{{ tab.count }}</span>
          </button>
        </div>
        <input v-model.trim="studentKeyword" class="student-search" placeholder="按姓名或学号搜索" />
      </div>

      <div class="status-strip">
        <div class="status-stat warn">
          <span>需关注</span>
          <strong>{{ statusCounts.warn }}</strong>
        </div>
        <div class="status-stat stable">
          <span>稳定</span>
          <strong>{{ statusCounts.stable }}</strong>
        </div>
        <div class="status-stat good">
          <span>优秀</span>
          <strong>{{ statusCounts.good }}</strong>
        </div>
        <div class="status-stat ai">
          <span>AI 助学平均</span>
          <strong>{{ percentText(avgAiRate) }}</strong>
        </div>
      </div>

      <div v-if="students.length === 0" class="empty">当前课程暂无学生数据。</div>
      <div v-else-if="filteredStudents.length === 0" class="empty">当前筛选条件下暂无学生。</div>
      <div v-else class="student-list">
        <article v-for="student in filteredStudents" :key="student.id" class="student-card">
          <div class="student-head">
            <div class="student-cell">
              <div class="avatar">{{ initial(student.full_name || student.username) }}</div>
              <div>
                <strong>{{ student.full_name || student.username }}</strong>
                <p>{{ student.username }}</p>
              </div>
            </div>
            <div class="student-score">
              <span>综合成绩</span>
              <strong>{{ valueText(student.average_score) }}</strong>
              <em :class="['status-pill', statusClass(student.status_label)]">{{ student.status_label }}</em>
            </div>
          </div>

          <div class="progress-grid">
            <div
              v-for="item in studentProgressItems(student)"
              :key="item.label"
              class="progress-item"
              :class="item.level"
            >
              <div class="progress-label">
                <span>{{ item.label }}</span>
                <strong>{{ item.text }}</strong>
              </div>
              <div class="progress-track"><i :style="{ width: `${item.value}%`, background: item.color }"></i></div>
            </div>
          </div>

          <div class="timeline-panel">
            <div class="timeline-head">
              <div>
                <strong>逐课次学习记录</strong>
                <span>共 {{ timelineSlots(student).length }} 次课，格子编号对应实际上课顺序</span>
              </div>
              <div class="timeline-legend">
                <span><i class="state-done"></i>已完成/出勤</span>
                <span><i class="state-missing"></i>未完成/缺勤</span>
                <span><i class="state-late"></i>迟到</span>
                <span><i class="state-none"></i>未安排</span>
              </div>
            </div>

            <div class="timeline-scroll">
              <div class="timeline-line ruler">
                <span class="track-label">课次</span>
                <div class="slot-grid" :style="timelineGridStyle(student)">
                  <span v-for="slot in timelineSlots(student)" :key="`index-${student.id}-${slot.index}`" class="slot-index">
                    {{ slot.index }}
                  </span>
                </div>
                <span class="track-count">{{ timelineSlots(student).length }} 次</span>
              </div>

              <div v-for="track in timelineTracks" :key="track.key" class="timeline-line">
                <span class="track-label">{{ track.label }}</span>
                <div class="slot-grid" :style="timelineGridStyle(student)">
                  <button
                    v-for="slot in timelineSlots(student)"
                    :key="`${student.id}-${track.key}-${slot.index}`"
                    type="button"
                    :class="['slot-cell', `state-${slot[track.key]?.state || 'none'}`]"
                    :title="timelineTitle(slot, track)"
                  >
                    {{ timelineMark(slot[track.key]?.state) }}
                  </button>
                </div>
                <span class="track-count">{{ trackCountText(student, track.key) }}</span>
              </div>
            </div>
          </div>

          <div class="student-meta">
            <span>AI 助学 {{ percentText(studentAiRate(student)) }}</span>
            <span>提问 {{ student.qa_records || 0 }} 次</span>
            <span>课堂表现 {{ percentText(student.classroom_rate ?? student.posture_rate ?? student.attendance_rate) }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="panel detail-panel">
      <div class="panel-head">
        <div>
          <h2>作业报告完成率分布</h2>
          <p>用于快速定位具体数据异常，智能诊断请进入“学情分析”。</p>
        </div>
      </div>
      <div class="distribution">
        <div v-for="student in topStudents" :key="student.id" class="dist-row">
          <span>{{ student.full_name || student.username }}</span>
          <div class="bar"><i :style="{ width: percentWidth(student.assignment_completion_rate) }"></i></div>
          <b>{{ percentText(student.assignment_completion_rate) }}</b>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const loading = ref(false)
const error = ref('')
const payload = ref<any | null>(null)
const selectedCourseId = ref<number | null>(null)

const courses = computed(() => payload.value?.courses || [])
const selectedCourse = computed(() => payload.value?.selected_course || null)
const totals = computed(() => payload.value?.totals || {})
const students = computed(() => payload.value?.students || [])
const studentKeyword = ref('')
const statusFilter = ref<'all' | 'warn' | 'stable' | 'good'>('all')
const statusCounts = computed(() => ({
  warn: students.value.filter((item: any) => item.status_label === '需关注').length,
  stable: students.value.filter((item: any) => item.status_label === '稳定').length,
  good: students.value.filter((item: any) => item.status_label === '优秀').length,
}))
const statusTabs = computed(() => [
  { value: 'all' as const, label: '全部', count: students.value.length },
  { value: 'warn' as const, label: '需关注', count: statusCounts.value.warn },
  { value: 'stable' as const, label: '稳定', count: statusCounts.value.stable },
  { value: 'good' as const, label: '优秀', count: statusCounts.value.good },
])
const maxQaRecords = computed(() => Math.max(5, ...students.value.map((item: any) => Number(item.qa_records || 0))))
const filteredStudents = computed(() => {
  const keyword = studentKeyword.value.toLowerCase()
  const statusMap = { warn: '需关注', stable: '稳定', good: '优秀' } as Record<string, string>
  return [...students.value]
    .filter((student: any) => {
      if (statusFilter.value !== 'all' && student.status_label !== statusMap[statusFilter.value]) return false
      if (!keyword) return true
      return `${student.full_name || ''} ${student.username || ''}`.toLowerCase().includes(keyword)
    })
    .sort((a: any, b: any) => {
      const rank = { '需关注': 0, '稳定': 1, '优秀': 2 } as Record<string, number>
      return (rank[a.status_label] ?? 3) - (rank[b.status_label] ?? 3) || (a.average_score || 0) - (b.average_score || 0)
    })
})
const topStudents = computed(() => [...filteredStudents.value].slice(0, 14))
const avgAiRate = computed(() => {
  if (!students.value.length) return null
  return students.value.reduce((sum: number, item: any) => sum + studentAiRate(item), 0) / students.value.length
})

const clamp = (v?: number | null) => Math.max(0, Math.min(100, Number(v || 0)))
const percentText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}%`
const valueText = (v?: number | null) => v == null ? '--' : `${Math.round(v)}`
const doneText = (done?: number | null, total?: number | null) => `${done || 0}/${total || 0}`
const percentWidth = (v?: number | null) => `${clamp(v)}%`
const timelineTracks = [
  { key: 'homework', label: '作业' },
  { key: 'report', label: '报告' },
  { key: 'quiz', label: '测验' },
  { key: 'attendance', label: '出勤' },
]
const initial = (name: string) => name?.slice(0, 1) || '学'

function statusClass(label: string) {
  if (label === '优秀') return 'good'
  if (label === '需关注') return 'warn'
  return 'stable'
}

function studentAiRate(student: any) {
  return clamp((student.qa_records || 0) / maxQaRecords.value * 100)
}

function classroomRate(student: any) {
  const attendance = student.attendance_rate ?? 70
  return clamp(attendance * 0.72 + studentAiRate(student) * 0.28)
}

function progressLevel(value: number) {
  if (value >= 85) return 'good'
  if (value >= 70) return 'stable'
  return 'warn'
}

function studentProgressItems(student: any) {
  const assignment = clamp(student.assignment_completion_rate)
  const quiz = clamp(student.quiz_completion_rate)
  const attendance = clamp(student.attendance_rate)
  const classroom = classroomRate(student)
  const ai = studentAiRate(student)
  return [
    { label: '作业报告', text: percentText(student.assignment_completion_rate), value: assignment, color: '#0b63b6', level: progressLevel(assignment) },
    { label: '测验掌握', text: percentText(student.quiz_completion_rate), value: quiz, color: '#3478d8', level: progressLevel(quiz) },
    { label: '考勤稳定', text: percentText(student.attendance_rate), value: attendance, color: '#14a46f', level: progressLevel(attendance) },
    { label: '课堂表现', text: percentText(classroom), value: classroom, color: '#22a06b', level: progressLevel(classroom) },
    { label: 'AI 助学', text: percentText(ai), value: ai, color: '#d8890b', level: progressLevel(ai) },
  ]
}

function timelineGridStyle(student: any) {
  const count = Math.max(1, timelineSlots(student).length || 1)
  return {
    gridTemplateColumns: `repeat(${count}, 22px)`,
    minWidth: `${count * 26}px`,
  }
}

function timelineSlots(student: any) {
  const existing = Array.isArray(student?.learning_timeline) ? student.learning_timeline : []
  if (existing.length) return existing
  const count = Math.max(
    1,
    Number(student?.session_count || 0),
    Number(student?.planned_sessions || 0),
    Number(student?.attendance_sessions || 0),
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

function trackCountText(student: any, key: string) {
  if (key === 'homework') return doneText(student.assignments_done, Math.max(0, (student.assignments_total || 0) - (student.reports_total || 0)))
  if (key === 'report') return doneText(student.reports_done, student.reports_total)
  if (key === 'quiz') return doneText(student.quizzes_done, student.quizzes_total)
  return doneText(student.attended_sessions, student.attendance_sessions)
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
    const params: Record<string, number> = {}
    if (selectedCourseId.value) params.course_id = selectedCourseId.value
    const res = await axios.get('/api/v1/acceptance/course-students', { params })
    payload.value = res.data
    if (!selectedCourseId.value && res.data?.selected_course?.id) {
      selectedCourseId.value = res.data.selected_course.id
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '课程学情加载失败，请确认已生成课程过程数据'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 28px; color: #0f2f64; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.page-title { color: #0f2f64; font-size: 28px; font-weight: 900; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; margin: 6px 0 0; line-height: 1.6; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.course-select { min-width: 300px; max-width: 460px; background: #ffffff; border: 1px solid #c8ddf4; color: #0f2f64; border-radius: 8px; padding: 10px 12px; outline: none; }
.refresh-btn { display: inline-flex; align-items: center; gap: 8px; background: #0b63b6; border: 1px solid #0b63b6; color: #ffffff; border-radius: 8px; padding: 10px 14px; font-weight: 800; cursor: pointer; white-space: nowrap; }
.refresh-btn:disabled { opacity: .6; cursor: wait; }
.error-box { border: 1px solid #ffd5cf; background: #fff4f2; color: #cf3434; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; }
.course-band, .panel { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.course-band { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 17px 18px; margin-bottom: 16px; }
.course-band h2 { color: #0f2f64; font-size: 18px; margin: 0; }
.course-band p { color: #5b6f92; font-size: 12px; margin: 6px 0 0; line-height: 1.5; }
.course-tags { display: flex; flex-wrap: wrap; gap: 7px; justify-content: flex-end; }
.course-tags span { color: #0b7d56; background: #e8f7f0; border: 1px solid #b6e6ce; border-radius: 8px; padding: 6px 9px; font-size: 12px; font-weight: 800; }
.panel { padding: 18px; margin-bottom: 16px; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-head h2 { color: #0f2f64; font-size: 17px; margin: 0; }
.panel-head p, .panel-head span { color: #5b6f92; font-size: 12px; margin: 4px 0 0; line-height: 1.6; }
.metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.metric-card { border: 1px solid #e1ecf8; border-radius: 8px; padding: 14px; background: #f8fbff; }
.metric-card span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 8px; }
.metric-card strong { color: #0f2f64; font-size: 28px; line-height: 1; }
.student-tools { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
.status-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.status-tabs button { border: 1px solid #c8ddf4; background: #ffffff; color: #0b63b6; border-radius: 8px; padding: 7px 10px; font-size: 12px; font-weight: 900; cursor: pointer; }
.status-tabs button.active { color: #ffffff; background: #0b63b6; border-color: #0b63b6; }
.status-tabs span { margin-left: 5px; opacity: .78; }
.student-search { width: 220px; border: 1px solid #c8ddf4; background: #ffffff; color: #0f2f64; border-radius: 8px; padding: 8px 10px; outline: none; }
.status-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }
.status-stat { border: 1px solid #e1ecf8; background: #f8fbff; border-radius: 9px; padding: 11px 12px; }
.status-stat span { display: block; color: #5b6f92; font-size: 12px; margin-bottom: 5px; }
.status-stat strong { color: #0f2f64; font-size: 24px; line-height: 1; }
.status-stat.warn { border-color: #fde4a8; background: #fff8e6; }
.status-stat.stable { border-color: #c8ddf4; background: #eaf3ff; }
.status-stat.good { border-color: #b6e6ce; background: #e8f7f0; }
.status-stat.ai { border-color: #d9e7f7; background: #ffffff; }
.student-list { display: grid; gap: 12px; }
.student-card { background: #f8fbff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 14px; }
.student-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
.student-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.student-cell strong { color: #0f2f64; font-size: 15px; }
.student-cell p { color: #5b6f92; font-size: 12px; margin: 3px 0 0; }
.avatar { width: 38px; height: 38px; border-radius: 8px; background: #eaf3ff; border: 1px solid #c8ddf4; color: #0b63b6; display: flex; align-items: center; justify-content: center; font-weight: 900; flex-shrink: 0; }
.student-score { display: flex; align-items: center; gap: 9px; flex-shrink: 0; }
.student-score span { color: #5b6f92; font-size: 12px; }
.student-score strong { color: #0f2f64; font-size: 22px; }
.status-pill { display: inline-flex; justify-content: center; border-radius: 8px; padding: 5px 8px; font-size: 12px; font-weight: 800; font-style: normal; white-space: nowrap; }
.status-pill.good { color: #0b7d56; background: #e8f7f0; }
.status-pill.stable { color: #0b63b6; background: #eaf3ff; }
.status-pill.warn { color: #9a5a00; background: #fff2d9; }
.timeline-panel { border-top: 1px solid #edf3fb; padding-top: 12px; margin-top: 12px; }
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
.student-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
.student-meta span { color: #5b6f92; background: #ffffff; border: 1px solid #e1ecf8; border-radius: 7px; padding: 4px 7px; font-size: 12px; }
.progress-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.progress-item { background: #ffffff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 10px; }
.progress-item.warn { border-color: #ffd5cf; background: #fffafa; }
.progress-item.stable { border-color: #d9e7f7; }
.progress-item.good { border-color: #b6e6ce; background: #fbfffd; }
.progress-label { display: flex; justify-content: space-between; gap: 8px; color: #5b6f92; font-size: 12px; margin-bottom: 7px; }
.progress-label strong { color: #0f2f64; white-space: nowrap; }
.progress-track { height: 8px; border-radius: 999px; background: #edf3fb; overflow: hidden; }
.progress-track i { display: block; height: 100%; border-radius: inherit; }
.detail-panel { max-width: 1040px; }
.distribution { display: flex; flex-direction: column; gap: 9px; }
.dist-row { display: grid; grid-template-columns: 120px 1fr 48px; gap: 10px; align-items: center; }
.dist-row span, .dist-row b { color: #5b6f92; font-size: 12px; font-weight: 800; }
.bar { height: 8px; background: #edf3fb; border-radius: 999px; overflow: hidden; }
.bar i { display: block; height: 100%; background: linear-gradient(90deg, #0b63b6, #14a46f); border-radius: inherit; }
.empty { color: #5b6f92; text-align: center; padding: 32px 0; border: 1px dashed #c8ddf4; border-radius: 8px; background: #f8fbff; }
@media (max-width: 1280px) {
  .metric-grid, .progress-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .status-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .page { padding: 18px; }
  .page-header, .course-band, .header-actions, .student-head, .student-tools { flex-direction: column; align-items: flex-start; }
  .course-select { width: 100%; min-width: 0; }
  .student-search { width: 100%; box-sizing: border-box; }
  .metric-grid, .progress-grid, .status-strip { grid-template-columns: 1fr; }
}
</style>
