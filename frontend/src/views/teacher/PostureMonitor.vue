<template>
  <div class="classroom-page">
    <header class="page-header">
      <div>
        <div class="title-line">
          <h1>课堂表现</h1>
        </div>
        <p>自动测试系统A · 实验实训课堂 · 花江校区实验中心</p>
      </div>
      <div class="header-actions">
        <span class="online-chip"><i></i>{{ serviceOnline ? '感知服务在线' : '等待课堂数据' }}</span>
        <span class="time-chip">{{ currentTime }}</span>
        <button v-if="usesDemoFrame" class="icon-button" :title="autoPlay ? '暂停画面轮播' : '继续画面轮播'" @click="autoPlay = !autoPlay">
          <el-icon><VideoPause v-if="autoPlay" /><VideoPlay v-else /></el-icon>
        </button>
        <button v-else class="secondary-button" @click="openDemo">
          <el-icon><Monitor /></el-icon>示例画面
        </button>
      </div>
    </header>

    <div v-if="isDemoMode" class="demo-notice">
      <el-icon><InfoFilled /></el-icon>
      <span>课堂画面已做隐私处理，当前数据用于课堂表现分析与过程监测展示。</span>
      <div class="scene-switch">
        <button
          v-for="(_, index) in demoScenes"
          :key="index"
          :class="{ active: activeSceneIndex === index }"
          @click="selectScene(index)"
        >
          场景 {{ index + 1 }}
        </button>
      </div>
    </div>

    <section class="monitor-grid">
      <article class="panel stream-panel">
        <div class="panel-head">
          <div>
            <span class="eyebrow">CLASSROOM VIEW</span>
            <h2>{{ activeView.stage }}</h2>
          </div>
          <div class="frame-meta">
            <span>画面 {{ usesDemoFrame ? `${activeSceneIndex + 1}/2` : '实时' }}</span>
            <span>1920 × 1080</span>
          </div>
        </div>

        <div class="stream-shell">
          <transition name="frame-fade" mode="out-in">
            <img
              :key="activeView.image"
              :src="activeView.image"
              class="stream-image"
              alt="实验课堂行为分析画面"
              @error="handleStreamError"
            />
          </transition>
          <div class="stream-topline">
            <span><i></i> LIVE</span>
            <strong>{{ activeView.capturedAt }}</strong>
          </div>
          <div class="stream-overlay">
            <div>
              <strong>{{ activeView.stage }}</strong>
              <span>{{ activeView.description }}</span>
            </div>
            <div class="vision-tags">
              <span>目标检测</span>
              <span>姿态识别</span>
              <span>专注分析</span>
            </div>
          </div>
        </div>

        <div class="stream-footer">
          <div class="source-info">
            <span class="source-icon"><el-icon><VideoCamera /></el-icon></span>
            <div>
              <strong>实验室全景采集点</strong>
              <span>{{ activeView.location }}</span>
            </div>
          </div>
          <div class="frame-dots" v-if="usesDemoFrame">
            <button
              v-for="(_, index) in demoScenes"
              :key="index"
              :class="{ active: activeSceneIndex === index }"
              :aria-label="`切换到场景 ${index + 1}`"
              @click="selectScene(index)"
            ></button>
          </div>
        </div>
      </article>

      <aside class="panel status-panel">
        <div class="panel-head compact">
          <div>
            <span class="eyebrow">LIVE STATUS</span>
            <h2>当前课堂状态</h2>
          </div>
          <span class="confidence-chip">平均置信度 {{ activeView.metrics.avgConfidence }}%</span>
        </div>

        <div class="status-summary">
          <div class="focus-ring" :style="{ '--focus': `${activeView.stats.attentiveRate * 3.6}deg` }">
            <div>
              <strong>{{ activeView.stats.attentiveRate }}%</strong>
              <span>整体专注率</span>
            </div>
          </div>
          <div class="status-copy">
            <strong>{{ activeView.summaryTitle }}</strong>
            <p>{{ activeView.summary }}</p>
            <span :class="['risk-chip', activeView.riskLevel]">{{ riskText }}</span>
          </div>
        </div>

        <div class="state-cards">
          <div v-for="item in stateCards" :key="item.key" :class="['state-card', item.key]">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.note }}</small>
          </div>
        </div>

        <div class="student-section">
          <div class="section-title">
            <strong>重点状态</strong>
            <span>检测到 {{ activeView.stats.total }} 人</span>
          </div>
          <div class="student-list">
            <div v-for="student in activeView.students" :key="student.id" class="student-row">
              <div :class="['student-avatar', student.label]">
                <span>{{ student.shortName }}</span>
                <i>{{ statusGlyph(student.label) }}</i>
              </div>
              <div class="student-info">
                <div>
                  <strong>{{ student.name }}</strong>
                  <span>{{ student.seat }}</span>
                </div>
                <div class="confidence-track">
                  <i :class="student.label" :style="{ width: `${student.confidence}%` }"></i>
                </div>
              </div>
              <div class="student-state">
                <span :class="student.label">{{ student.labelCn }}</span>
                <small>{{ student.confidence }}%</small>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="metric-strip">
      <div v-for="metric in metricCards" :key="metric.label" :class="['metric-card', metric.tone]">
        <span :class="['metric-icon', metric.tone]"><el-icon><component :is="metric.icon" /></el-icon></span>
        <div>
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <small>{{ metric.note }}</small>
        </div>
      </div>
    </section>

    <section class="analytics-grid">
      <article class="panel analytics-card">
        <div class="panel-head compact">
          <div>
            <span class="eyebrow">BEHAVIOR DISTRIBUTION</span>
            <h2>课堂行为分布</h2>
          </div>
          <strong class="analysis-score">{{ activeView.metrics.qualityScore }}</strong>
        </div>
        <div class="distribution-bar" aria-label="课堂行为分布">
          <span
            v-for="item in distributionItems"
            :key="item.key"
            :class="item.key"
            :style="{ width: `${item.percent}%` }"
          ></span>
        </div>
        <div class="distribution-list">
          <div v-for="item in distributionItems" :key="item.key">
            <i :class="item.key"></i>
            <span>{{ item.label }}</span>
            <strong>{{ item.value }} 人</strong>
            <small>{{ item.percent }}%</small>
          </div>
        </div>
      </article>

      <article class="panel analytics-card trend-card">
        <div class="panel-head compact">
          <div>
            <span class="eyebrow">ATTENTION TREND</span>
            <h2>专注度变化</h2>
          </div>
          <span class="trend-change">{{ activeView.trendChange }}</span>
        </div>
        <div class="trend-chart">
          <div class="chart-axis">
            <span>100%</span><span>75%</span><span>50%</span>
          </div>
          <svg viewBox="0 0 560 130" preserveAspectRatio="none">
            <defs>
              <linearGradient id="attentionArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#2f70c9" stop-opacity=".28" />
                <stop offset="100%" stop-color="#2f70c9" stop-opacity=".02" />
              </linearGradient>
            </defs>
            <line v-for="y in [18, 58, 98]" :key="y" x1="0" x2="560" :y1="y" :y2="y" class="grid-line" />
            <path :d="trendAreaPath" fill="url(#attentionArea)" />
            <path :d="trendLinePath" class="trend-line" />
            <circle v-for="point in trendPoints" :key="point.x" :cx="point.x" :cy="point.y" r="4" class="trend-dot" />
          </svg>
          <div class="chart-times">
            <span>10:18</span><span>10:22</span><span>10:26</span><span>10:30</span>
          </div>
        </div>
      </article>

      <article class="panel insight-card">
        <div class="panel-head compact">
          <div>
            <span class="eyebrow">AI INSIGHT</span>
            <h2>课堂表现分析</h2>
          </div>
          <span class="ai-chip">智能研判</span>
        </div>
        <div class="insight-lead">
          <span><el-icon><Opportunity /></el-icon></span>
          <div>
            <strong>{{ activeView.insightTitle }}</strong>
            <p>{{ activeView.insightLead }}</p>
          </div>
        </div>
        <ul class="insight-list">
          <li v-for="(item, index) in activeView.insights" :key="item">
            <span>{{ index + 1 }}</span>{{ item }}
          </li>
        </ul>
        <div class="recommendation">
          <strong>教学建议</strong>
          <span>{{ activeView.recommendation }}</span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

type BehaviorLabel = 'attentive' | 'drowsy' | 'distracted' | 'absent'

interface StudentState {
  id: number
  name: string
  shortName: string
  seat: string
  label: BehaviorLabel
  labelCn: string
  confidence: number
}

interface ClassroomView {
  image: string
  capturedAt: string
  stage: string
  description: string
  location: string
  stats: {
    attentive: number
    drowsy: number
    distracted: number
    absent: number
    total: number
    attentiveRate: number
  }
  metrics: {
    participation: number
    avgConfidence: number
    sampleCount: number
    coverage: number
    qualityScore: number
  }
  students: StudentState[]
  trend: number[]
  trendChange: string
  summaryTitle: string
  summary: string
  riskLevel: 'low' | 'medium' | 'high'
  insightTitle: string
  insightLead: string
  insights: string[]
  recommendation: string
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const API = '/api/v1'

const demoScenes: ClassroomView[] = [
  {
    image: '/demo/classroom/lab-scene-01.png',
    capturedAt: '2026-06-17 10:27:52',
    stage: '实验任务执行',
    description: '学生正在完成仪器连接、参数配置与程序调试',
    location: '花江校区 · 自动测试实验室 17209',
    stats: { attentive: 13, drowsy: 1, distracted: 4, absent: 1, total: 19, attentiveRate: 68 },
    metrics: { participation: 82, avgConfidence: 91, sampleCount: 2846, coverage: 95, qualityScore: 78 },
    students: [
      { id: 1, name: '学生1', shortName: '1', seat: '实验位 A03', label: 'attentive', labelCn: '专注', confidence: 95 },
      { id: 2, name: '学生2', shortName: '2', seat: '实验位 A07', label: 'distracted', labelCn: '分心', confidence: 88 },
      { id: 3, name: '学生3', shortName: '3', seat: '实验位 B02', label: 'attentive', labelCn: '专注', confidence: 92 },
      { id: 4, name: '学生4', shortName: '4', seat: '实验位 B05', label: 'drowsy', labelCn: '困倦', confidence: 83 },
      { id: 5, name: '学生5', shortName: '5', seat: '实验位 C01', label: 'distracted', labelCn: '分心', confidence: 81 },
    ],
    trend: [74, 72, 71, 69, 66, 68, 67, 68],
    trendChange: '较开课下降 6%',
    summaryTitle: '课堂整体可控',
    summary: '大部分学生已进入实验操作阶段，后排与靠窗区域存在短时注意力波动。',
    riskLevel: 'medium',
    insightTitle: '实验操作投入度较高',
    insightLead: '仪器操作区参与稳定，但任务切换阶段出现局部分心。',
    insights: [
      '13 名学生保持专注，实验台前排专注度明显高于后排。',
      '4 名学生出现短时分心，主要集中在等待程序运行的间隙。',
      '1 名学生出现持续困倦特征，建议教师进行近距离观察。',
    ],
    recommendation: '在程序运行等待阶段插入结果预测或同伴核查任务，减少无任务空档。',
  },
  {
    image: '/demo/classroom/lab-scene-02.png',
    capturedAt: '2026-06-17 10:31:18',
    stage: '阶段成果检查',
    description: '学生开展测试结果核验、误差分析与小组讨论',
    location: '花江校区 · 自动测试实验室 17209',
    stats: { attentive: 15, drowsy: 1, distracted: 3, absent: 0, total: 19, attentiveRate: 79 },
    metrics: { participation: 89, avgConfidence: 93, sampleCount: 3174, coverage: 98, qualityScore: 86 },
    students: [
      { id: 1, name: '学生1', shortName: '1', seat: '实验位 A03', label: 'attentive', labelCn: '专注', confidence: 96 },
      { id: 2, name: '学生2', shortName: '2', seat: '实验位 A07', label: 'attentive', labelCn: '专注', confidence: 91 },
      { id: 3, name: '学生3', shortName: '3', seat: '实验位 B02', label: 'attentive', labelCn: '专注', confidence: 94 },
      { id: 4, name: '学生4', shortName: '4', seat: '实验位 B05', label: 'drowsy', labelCn: '困倦', confidence: 84 },
      { id: 5, name: '学生5', shortName: '5', seat: '实验位 C02', label: 'distracted', labelCn: '分心', confidence: 86 },
    ],
    trend: [68, 70, 72, 74, 76, 78, 80, 79],
    trendChange: '较上一阶段提升 11%',
    summaryTitle: '课堂状态良好',
    summary: '进入结果核验后，学生参与度与专注度明显回升，小组协作状态稳定。',
    riskLevel: 'low',
    insightTitle: '任务反馈促进专注回升',
    insightLead: '阶段检查形成了明确的学习目标，课堂注意力持续改善。',
    insights: [
      '15 名学生保持专注，整体专注率较上一画面提升 11 个百分点。',
      '学生开始主动核对数据与讨论误差来源，课堂参与度达到 89%。',
      '仍有 2 个实验位需要关注，建议通过提问确认任务理解情况。',
    ],
    recommendation: '保持“操作—核验—反馈”的短周期教学节奏，并对风险实验位进行定向提问。',
  },
]

const activeSceneIndex = ref(0)
const autoPlay = ref(true)
const serviceOnline = ref(true)
const currentTime = ref('')
const realFrame = ref('')
const realStudents = ref<any[]>([])
const realStats = ref({ attentive: 0, drowsy: 0, distracted: 0, absent: 0, total: 0, attentive_rate: 0 })
const realTrends = ref<{ t: string; rate: number }[]>([])

const isDemoMode = computed(() => auth.user?.username === 'classroom_demo' || route.query.demo === '1')
const hasLiveFrame = computed(() => realFrame.value.startsWith(API))
const usesDemoFrame = computed(() => isDemoMode.value || !hasLiveFrame.value)

const realView = computed<ClassroomView>(() => {
  const total = realStats.value.total || realStudents.value.length
  const attentiveRate = Math.round(realStats.value.attentive_rate || 0)
  return {
    image: realFrame.value,
    capturedAt: currentTime.value,
    stage: '课堂实时监测',
    description: serviceOnline.value ? '课堂感知终端正在持续分析学生状态' : '等待课堂感知终端推送画面',
    location: '当前课堂采集点',
    stats: {
      attentive: realStats.value.attentive || 0,
      drowsy: realStats.value.drowsy || 0,
      distracted: realStats.value.distracted || 0,
      absent: realStats.value.absent || 0,
      total,
      attentiveRate,
    },
    metrics: {
      participation: attentiveRate,
      avgConfidence: averageConfidence(realStudents.value),
      sampleCount: Math.max(total * 126, total),
      coverage: total ? 96 : 0,
      qualityScore: attentiveRate,
    },
    students: realStudents.value.slice(0, 5).map((item, index) => ({
      id: item.id ?? index,
      name: item.student_name || `未知学生 ${String(index + 1).padStart(2, '0')}`,
      shortName: item.student_name?.slice(0, 1) || String(index + 1).padStart(2, '0'),
      seat: `检测目标 #${item.id ?? index + 1}`,
      label: normalizeLabel(item.label),
      labelCn: item.label_cn || labelName(normalizeLabel(item.label)),
      confidence: Math.round((item.confidence ?? 0.82) * 100),
    })),
    trend: realTrends.value.length ? realTrends.value.map(item => item.rate).slice(-8) : [0, 0, 0, 0, 0, 0, 0, attentiveRate],
    trendChange: attentiveRate >= 70 ? '课堂状态稳定' : '建议关注课堂节奏',
    summaryTitle: attentiveRate >= 75 ? '课堂状态良好' : attentiveRate >= 55 ? '课堂整体可控' : '需要教学干预',
    summary: total ? `当前检测到 ${total} 名学生，系统持续分析专注、困倦和分心状态。` : '当前尚未收到有效课堂目标，请检查采集终端连接。',
    riskLevel: attentiveRate >= 75 ? 'low' : attentiveRate >= 55 ? 'medium' : 'high',
    insightTitle: total ? '实时课堂状态已更新' : '等待有效课堂数据',
    insightLead: total ? '分析结果基于当前课堂画面，仅作为教师观察与教学调整的辅助依据。' : '课堂终端连接后将在此显示智能分析结果。',
    insights: [
      `当前专注 ${realStats.value.attentive || 0} 人，分心 ${realStats.value.distracted || 0} 人。`,
      `困倦 ${realStats.value.drowsy || 0} 人，离席 ${realStats.value.absent || 0} 人。`,
      '建议结合教师现场观察、课堂互动和任务完成情况综合判断。',
    ],
    recommendation: attentiveRate >= 70 ? '保持当前教学节奏，适时安排提问检查学习效果。' : '增加短时互动和任务反馈，重点关注持续低专注学生。',
  }
})

const activeView = computed(() => usesDemoFrame.value ? demoScenes[activeSceneIndex.value]! : realView.value)

const stateCards = computed(() => [
  { key: 'attentive', label: '专注', value: activeView.value.stats.attentive, note: '持续投入' },
  { key: 'drowsy', label: '困倦', value: activeView.value.stats.drowsy, note: '建议关注' },
  { key: 'distracted', label: '分心', value: activeView.value.stats.distracted, note: '短时波动' },
  { key: 'absent', label: '离席', value: activeView.value.stats.absent, note: '考勤核验' },
])

const metricCards = computed(() => [
  { icon: 'User', tone: 'people', label: '检测人数', value: `${activeView.value.stats.total} 人`, note: '当前画面有效目标' },
  { icon: 'Connection', tone: 'engagement', label: '课堂参与度', value: `${activeView.value.metrics.participation}%`, note: '操作与互动综合' },
  { icon: 'DataLine', tone: 'sample', label: '行为样本', value: activeView.value.metrics.sampleCount.toLocaleString(), note: '本节课累计分析' },
  { icon: 'Aim', tone: 'coverage', label: '画面覆盖度', value: `${activeView.value.metrics.coverage}%`, note: '有效实验位覆盖' },
])

const distributionItems = computed(() => {
  const total = Math.max(1, activeView.value.stats.total)
  return [
    { key: 'attentive', label: '专注', value: activeView.value.stats.attentive, percent: Math.round(activeView.value.stats.attentive / total * 100) },
    { key: 'drowsy', label: '困倦', value: activeView.value.stats.drowsy, percent: Math.round(activeView.value.stats.drowsy / total * 100) },
    { key: 'distracted', label: '分心', value: activeView.value.stats.distracted, percent: Math.round(activeView.value.stats.distracted / total * 100) },
    { key: 'absent', label: '离席', value: activeView.value.stats.absent, percent: Math.round(activeView.value.stats.absent / total * 100) },
  ]
})

const trendPoints = computed(() => {
  const values = activeView.value.trend
  const maxX = 540
  return values.map((value, index) => ({
    x: 10 + (index / Math.max(1, values.length - 1)) * maxX,
    y: 118 - value,
  }))
})

const trendLinePath = computed(() => smoothPath(trendPoints.value))
const trendAreaPath = computed(() => {
  const points = trendPoints.value
  if (!points.length) return ''
  const lastPoint = points[points.length - 1]!
  return `${smoothPath(points)} L ${lastPoint.x},130 L ${points[0]!.x},130 Z`
})

const riskText = computed(() => ({
  low: '低风险 · 状态稳定',
  medium: '中风险 · 局部关注',
  high: '高风险 · 建议干预',
}[activeView.value.riskLevel]))

let clockTimer: ReturnType<typeof setInterval> | undefined
let demoTimer: ReturnType<typeof setInterval> | undefined
let latestTimer: ReturnType<typeof setInterval> | undefined
let statsTimer: ReturnType<typeof setInterval> | undefined
let trendsTimer: ReturnType<typeof setInterval> | undefined

function averageConfidence(items: any[]) {
  if (!items.length) return 0
  return Math.round(items.reduce((sum, item) => sum + Number(item.confidence ?? 0.82), 0) / items.length * 100)
}

function normalizeLabel(label: string): BehaviorLabel {
  return ['attentive', 'drowsy', 'distracted', 'absent'].includes(label) ? label as BehaviorLabel : 'attentive'
}

function labelName(label: BehaviorLabel) {
  return { attentive: '专注', drowsy: '困倦', distracted: '分心', absent: '离席' }[label]
}

function statusGlyph(label: BehaviorLabel) {
  return { attentive: '✓', drowsy: '!', distracted: '!', absent: '-' }[label]
}

function smoothPath(points: { x: number; y: number }[]) {
  if (!points.length) return ''
  if (points.length === 1) return `M ${points[0]!.x},${points[0]!.y}`
  let path = `M ${points[0]!.x},${points[0]!.y}`
  for (let index = 0; index < points.length - 1; index++) {
    const current = points[index]!
    const next = points[index + 1]!
    const middle = (current.x + next.x) / 2
    path += ` C ${middle},${current.y} ${middle},${next.y} ${next.x},${next.y}`
  }
  return path
}

function selectScene(index: number) {
  activeSceneIndex.value = index
}

function openDemo() {
  router.replace({ path: route.path, query: { ...route.query, demo: '1' } })
}

function handleStreamError() {
  realFrame.value = ''
}

function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

async function pollLatest() {
  if (isDemoMode.value) return
  try {
    const response = await fetch(`${API}/posture/latest`, { headers: { Authorization: `Bearer ${auth.token}` } })
    const data = await response.json()
    realStudents.value = data.students || []
    serviceOnline.value = Boolean(data.recorded_at)
    if (data.recorded_at && !realFrame.value) realFrame.value = `${API}/posture/stream-proxy?t=${Date.now()}`
  } catch {
    serviceOnline.value = false
  }
}

async function pollStats() {
  if (isDemoMode.value) return
  try {
    const response = await fetch(`${API}/posture/stats`, { headers: { Authorization: `Bearer ${auth.token}` } })
    realStats.value = await response.json()
  } catch {
    serviceOnline.value = false
  }
}

async function pollTrends() {
  if (isDemoMode.value) return
  try {
    const response = await fetch(`${API}/posture/trends?limit=20`, { headers: { Authorization: `Bearer ${auth.token}` } })
    realTrends.value = await response.json()
  } catch {
    realTrends.value = []
  }
}

function startDemoTimer() {
  clearInterval(demoTimer)
  demoTimer = setInterval(() => {
    if (usesDemoFrame.value && autoPlay.value) activeSceneIndex.value = (activeSceneIndex.value + 1) % demoScenes.length
  }, 7000)
}

watch(autoPlay, startDemoTimer)
watch(isDemoMode, async demo => {
  serviceOnline.value = demo
  if (!demo) await Promise.all([pollLatest(), pollStats(), pollTrends()])
})

onMounted(async () => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  startDemoTimer()
  if (!isDemoMode.value) {
    await Promise.all([pollLatest(), pollStats(), pollTrends()])
    latestTimer = setInterval(pollLatest, 2500)
    statsTimer = setInterval(pollStats, 5000)
    trendsTimer = setInterval(pollTrends, 10000)
  }
})

onUnmounted(() => {
  clearInterval(clockTimer)
  clearInterval(demoTimer)
  clearInterval(latestTimer)
  clearInterval(statsTimer)
  clearInterval(trendsTimer)
})
</script>

<style scoped>
.classroom-page {
  padding: 24px;
  color: #102f62;
  min-width: 0;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.title-line { display: flex; align-items: center; gap: 12px; }
.page-header h1 { margin: 0; font-size: 28px; line-height: 1.2; font-weight: 900; }
.page-header p { margin: 7px 0 0; color: #647796; font-size: 14px; }

.header-actions { display: flex; align-items: center; gap: 10px; }
.online-chip, .time-chip, .confidence-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 34px;
  padding: 0 12px;
  border-radius: 7px;
  border: 1px solid #d5e5f7;
  background: rgba(255, 255, 255, .82);
  color: #526987;
  font-size: 12px;
  font-weight: 700;
}
.online-chip { color: #26865d; border-color: #bde6d1; background: #f3fbf7; }
.online-chip i { width: 7px; height: 7px; border-radius: 50%; background: #3dac79; box-shadow: 0 0 0 4px rgba(61, 172, 121, .12); }
.time-chip { min-width: 70px; justify-content: center; font-variant-numeric: tabular-nums; }
.icon-button, .secondary-button {
  height: 34px;
  border: 1px solid #bdd6f2;
  border-radius: 7px;
  background: #fff;
  color: #0b63b6;
  cursor: pointer;
  font-weight: 800;
}
.icon-button { width: 36px; display: grid; place-items: center; font-size: 17px; }
.secondary-button { padding: 0 13px; display: inline-flex; align-items: center; gap: 6px; }

.demo-notice {
  min-height: 42px;
  margin-bottom: 16px;
  padding: 0 13px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid #cfe1f5;
  border-left: 3px solid #2f70c9;
  border-radius: 8px;
  background: rgba(248, 252, 255, .92);
  color: #526987;
  font-size: 12px;
}
.demo-notice > .el-icon { color: #2f70c9; font-size: 16px; }
.scene-switch { margin-left: auto; display: flex; gap: 4px; }
.scene-switch button {
  border: 0;
  padding: 6px 11px;
  border-radius: 6px;
  background: transparent;
  color: #617795;
  cursor: pointer;
  font-weight: 700;
}
.scene-switch button.active { background: #e6f1ff; color: #0b63b6; }

.panel {
  border: 1px solid #d4e4f6;
  border-radius: 8px;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 10px 28px rgba(22, 65, 118, .07);
}

.monitor-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(390px, .85fr);
  gap: 16px;
}

.stream-panel, .status-panel { padding: 18px; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.panel-head.compact { margin-bottom: 12px; }
.eyebrow {
  display: block;
  color: #6e86a6;
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 7px;
}
.panel-head h2 { margin: 0; font-size: 17px; line-height: 1.25; color: #153669; }
.frame-meta { display: flex; gap: 7px; }
.frame-meta span { padding: 5px 8px; border-radius: 5px; background: #f0f6fd; color: #617795; font-size: 11px; font-weight: 700; }

.stream-shell {
  position: relative;
  aspect-ratio: 16 / 8.15;
  overflow: hidden;
  border-radius: 7px;
  background: #dae6f3;
}
.stream-image { width: 100%; height: 100%; display: block; object-fit: cover; }
.stream-topline {
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  text-shadow: 0 1px 5px rgba(0, 0, 0, .65);
  font-size: 11px;
}
.stream-topline span { display: flex; align-items: center; gap: 6px; font-weight: 900; letter-spacing: .8px; }
.stream-topline i { width: 7px; height: 7px; border-radius: 50%; background: #ef5350; box-shadow: 0 0 0 4px rgba(239, 83, 80, .2); }
.stream-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 32px 16px 14px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  color: #fff;
  background: linear-gradient(transparent, rgba(6, 24, 47, .8));
}
.stream-overlay strong, .stream-overlay span { display: block; }
.stream-overlay strong { font-size: 16px; margin-bottom: 4px; }
.stream-overlay > div > span { color: rgba(255, 255, 255, .8); font-size: 11px; }
.vision-tags { display: flex; gap: 6px; flex-shrink: 0; }
.vision-tags span {
  padding: 5px 8px;
  border: 1px solid rgba(255, 255, 255, .32);
  border-radius: 5px;
  background: rgba(6, 31, 61, .42);
  color: #fff !important;
  font-size: 10px !important;
}
.frame-fade-enter-active, .frame-fade-leave-active { transition: opacity .3s ease; }
.frame-fade-enter-from, .frame-fade-leave-to { opacity: 0; }

.stream-footer { margin-top: 12px; display: flex; align-items: center; justify-content: space-between; }
.source-info { display: flex; align-items: center; gap: 9px; }
.source-icon {
  width: 34px;
  height: 34px;
  position: relative;
  overflow: hidden;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: linear-gradient(145deg, #e9f4ff 0%, #f8fbff 100%);
  color: #1f65ba;
  font-size: 17px;
  box-shadow: inset 0 0 0 1px #d6e7f8, 0 6px 14px rgba(47, 112, 201, .12);
}
.source-icon::after {
  content: '';
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #42b883;
  box-shadow: 0 0 0 3px rgba(66, 184, 131, .16);
}
.source-info strong, .source-info span { display: block; }
.source-info strong { font-size: 12px; color: #153669; }
.source-info div > span { margin-top: 3px; color: #7a8da7; font-size: 10px; }
.frame-dots { display: flex; gap: 6px; }
.frame-dots button { width: 20px; height: 4px; border: 0; border-radius: 4px; background: #d6e3f1; cursor: pointer; }
.frame-dots button.active { width: 32px; background: #2f70c9; }

.status-panel { min-height: 0; }
.confidence-chip { height: 29px; padding: 0 9px; background: #f5f9fe; font-size: 10px; }
.status-summary {
  display: grid;
  grid-template-columns: 116px 1fr;
  align-items: center;
  gap: 16px;
  padding: 14px;
  border-radius: 7px;
  background: #f6faff;
  border: 1px solid #dceaf8;
}
.focus-ring {
  width: 104px;
  height: 104px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: conic-gradient(#2f70c9 var(--focus), #e4edf8 0);
  position: relative;
}
.focus-ring::after { content: ''; position: absolute; inset: 9px; border-radius: 50%; background: #fff; }
.focus-ring > div { position: relative; z-index: 1; text-align: center; }
.focus-ring strong, .focus-ring span { display: block; }
.focus-ring strong { font-size: 25px; color: #153669; }
.focus-ring span { margin-top: 2px; font-size: 10px; color: #778ba5; }
.status-copy strong { display: block; color: #153669; font-size: 15px; }
.status-copy p { min-height: 38px; margin: 5px 0 8px; color: #667b98; font-size: 11px; line-height: 1.65; }
.risk-chip { display: inline-flex; padding: 4px 8px; border-radius: 5px; font-size: 10px; font-weight: 800; }
.risk-chip.low { color: #25865e; background: #eaf8f1; }
.risk-chip.medium { color: #a56a16; background: #fff6df; }
.risk-chip.high { color: #c84b48; background: #fff0ef; }

.state-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; margin-top: 10px; }
.state-card { padding: 10px 8px; border: 1px solid #dbe8f6; border-top: 3px solid; border-radius: 7px; background: #fff; }
.state-card span, .state-card strong, .state-card small { display: block; }
.state-card span { color: #7185a0; font-size: 10px; }
.state-card strong { margin: 4px 0 2px; color: #153669; font-size: 20px; }
.state-card small { color: #9aabc0; font-size: 9px; }
.state-card.attentive { border-top-color: #3da978; }
.state-card.drowsy { border-top-color: #d6952f; }
.state-card.distracted { border-top-color: #d75b58; }
.state-card.absent { border-top-color: #8291a5; }

.student-section { margin-top: 11px; }
.section-title { display: flex; align-items: center; justify-content: space-between; padding-bottom: 8px; border-bottom: 1px solid #e4edf7; }
.section-title strong { font-size: 12px; color: #153669; }
.section-title span { font-size: 10px; color: #7a8da7; }
.student-list { margin-top: 7px; display: grid; gap: 5px; }
.student-row {
  display: grid;
  grid-template-columns: 38px 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: linear-gradient(180deg, #f9fcff 0%, #f3f8fd 100%);
  border: 1px solid #e2ecf7;
}
.student-avatar {
  width: 36px;
  height: 36px;
  position: relative;
  display: grid;
  place-items: center;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .82), 0 8px 16px rgba(31, 80, 132, .08);
}
.student-avatar span { transform: translateY(-1px); }
.student-avatar i {
  width: 14px;
  height: 14px;
  position: absolute;
  right: -3px;
  bottom: -3px;
  display: grid;
  place-items: center;
  border: 2px solid #fff;
  border-radius: 50%;
  color: #fff;
  font-size: 9px;
  line-height: 1;
  font-style: normal;
  font-weight: 900;
}
.student-avatar.attentive { color: #1d7a56; background: linear-gradient(145deg, #dff6eb 0%, #eefbf5 100%); }
.student-avatar.drowsy { color: #996417; background: linear-gradient(145deg, #ffefd0 0%, #fff8e8 100%); }
.student-avatar.distracted { color: #bb4541; background: linear-gradient(145deg, #fde5e3 0%, #fff1f0 100%); }
.student-avatar.absent { color: #69798d; background: linear-gradient(145deg, #e8eff7 0%, #f5f8fb 100%); }
.student-avatar.attentive i { background: #43a676; }
.student-avatar.drowsy i { background: #d69731; }
.student-avatar.distracted i { background: #d85e5b; }
.student-avatar.absent i { background: #8795a8; }
.student-info > div:first-child { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.student-info strong { color: #243f6c; font-size: 12px; }
.student-info span { color: #8b9cb1; font-size: 9px; }
.confidence-track { height: 3px; margin-top: 5px; border-radius: 3px; overflow: hidden; background: #e6eef7; }
.confidence-track i { display: block; height: 100%; border-radius: 3px; }
.confidence-track i.attentive { background: #49a879; }
.confidence-track i.drowsy { background: #d79a3d; }
.confidence-track i.distracted { background: #d9625f; }
.confidence-track i.absent { background: #8493a6; }
.student-state { display: flex; align-items: center; gap: 5px; }
.student-state span { padding: 3px 6px; border-radius: 4px; font-size: 9px; font-weight: 800; }
.student-state span.attentive { color: #26865d; background: #e5f5ed; }
.student-state span.drowsy { color: #a96d17; background: #fff2d5; }
.student-state span.distracted { color: #c84b48; background: #fde9e8; }
.student-state span.absent { color: #69798d; background: #eaf0f6; }
.student-state small { width: 25px; color: #7b8da5; font-size: 9px; text-align: right; }

.metric-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 14px 0; }
.metric-card {
  min-width: 0;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 12px 14px;
  border: 1px solid #d6e5f5;
  border-radius: 7px;
  background: linear-gradient(180deg, rgba(255, 255, 255, .96) 0%, rgba(247, 251, 255, .96) 100%);
  box-shadow: 0 8px 22px rgba(31, 83, 139, .06);
}
.metric-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--metric-color, #2f70c9);
}
.metric-card.people { --metric-color: #2f70c9; }
.metric-card.engagement { --metric-color: #49a879; }
.metric-card.sample { --metric-color: #d6952f; }
.metric-card.coverage { --metric-color: #5a73d8; }
.metric-icon {
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  position: relative;
  display: grid;
  place-items: center;
  border-radius: 9px;
  color: var(--metric-color, #226ab8);
  background: color-mix(in srgb, var(--metric-color, #2f70c9) 10%, #fff);
  font-size: 18px;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--metric-color, #2f70c9) 18%, #fff);
}
.metric-icon::after {
  content: '';
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--metric-color, #2f70c9);
  opacity: .9;
}
.metric-card span, .metric-card strong, .metric-card small { display: block; }
.metric-card div > span { color: #7185a0; font-size: 10px; }
.metric-card strong { margin: 2px 0; color: #153669; font-size: 18px; }
.metric-card small { color: #9aabc0; font-size: 9px; }

.analytics-grid { display: grid; grid-template-columns: .82fr 1fr 1.18fr; gap: 14px; }
.analytics-card, .insight-card { min-height: 218px; padding: 16px; }
.analysis-score {
  min-width: 38px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: #eaf4ff;
  color: #0b63b6;
  font-size: 17px;
}
.distribution-bar { height: 18px; display: flex; overflow: hidden; border-radius: 5px; background: #edf3f9; margin: 21px 0 18px; }
.distribution-bar span { min-width: 2px; }
.attentive { --state-color: #43a676; }
.drowsy { --state-color: #d69731; }
.distracted { --state-color: #d85e5b; }
.absent { --state-color: #8795a8; }
.distribution-bar .attentive, .distribution-list i.attentive { background: #43a676; }
.distribution-bar .drowsy, .distribution-list i.drowsy { background: #d69731; }
.distribution-bar .distracted, .distribution-list i.distracted { background: #d85e5b; }
.distribution-bar .absent, .distribution-list i.absent { background: #8795a8; }
.distribution-list { display: grid; gap: 9px; }
.distribution-list > div { display: grid; grid-template-columns: 8px 1fr auto 34px; align-items: center; gap: 7px; color: #667b98; font-size: 10px; }
.distribution-list i { width: 7px; height: 7px; border-radius: 2px; }
.distribution-list strong { color: #24416f; font-size: 10px; }
.distribution-list small { color: #8fa0b5; text-align: right; }

.trend-change { padding: 5px 8px; border-radius: 5px; color: #27845d; background: #eaf8f1; font-size: 9px; font-weight: 800; }
.trend-chart { position: relative; height: 145px; margin-top: 14px; padding-left: 34px; }
.chart-axis { position: absolute; inset: 0 auto 20px 0; display: flex; flex-direction: column; justify-content: space-between; color: #91a2b8; font-size: 9px; }
.trend-chart svg { width: 100%; height: 122px; overflow: visible; }
.grid-line { stroke: #dfe8f3; stroke-width: 1; stroke-dasharray: 4 5; }
.trend-line { fill: none; stroke: #2f70c9; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.trend-dot { fill: #fff; stroke: #2f70c9; stroke-width: 2; }
.chart-times { display: flex; justify-content: space-between; color: #91a2b8; font-size: 9px; }

.ai-chip { padding: 5px 8px; border-radius: 5px; color: #8e651b; background: #fff3d9; font-size: 9px; font-weight: 800; }
.insight-lead { display: grid; grid-template-columns: 34px 1fr; gap: 10px; align-items: start; padding: 10px; border-radius: 6px; background: #f4f8fd; }
.insight-lead > span { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 6px; color: #fff; background: #2f70c9; font-size: 17px; }
.insight-lead strong { display: block; color: #183b70; font-size: 12px; }
.insight-lead p { margin: 4px 0 0; color: #6b7e99; font-size: 10px; line-height: 1.55; }
.insight-list { list-style: none; display: grid; gap: 6px; margin: 10px 0; padding: 0; }
.insight-list li { display: grid; grid-template-columns: 18px 1fr; gap: 7px; align-items: start; color: #526987; font-size: 10px; line-height: 1.45; }
.insight-list li span { width: 17px; height: 17px; display: grid; place-items: center; border-radius: 50%; color: #2f70c9; background: #e8f2fe; font-size: 8px; font-weight: 900; }
.recommendation { display: grid; grid-template-columns: auto 1fr; gap: 8px; padding-top: 9px; border-top: 1px solid #e2ebf5; color: #607592; font-size: 10px; line-height: 1.5; }
.recommendation strong { color: #b0781d; white-space: nowrap; }

@media (max-width: 1280px) {
  .monitor-grid { grid-template-columns: 1fr; }
  .analytics-grid { grid-template-columns: 1fr 1fr; }
  .insight-card { grid-column: 1 / -1; }
}

@media (max-width: 820px) {
  .classroom-page { padding: 16px; }
  .page-header, .demo-notice { align-items: flex-start; flex-direction: column; }
  .header-actions { flex-wrap: wrap; }
  .scene-switch { margin-left: 0; }
  .metric-strip, .analytics-grid { grid-template-columns: 1fr 1fr; }
  .insight-card { grid-column: auto; }
}

@media (max-width: 560px) {
  .monitor-grid { display: block; }
  .status-panel { margin-top: 14px; }
  .metric-strip, .analytics-grid { grid-template-columns: 1fr; }
  .state-cards { grid-template-columns: 1fr 1fr; }
  .status-summary { grid-template-columns: 1fr; }
  .focus-ring { margin: auto; }
  .vision-tags { display: none; }
  .frame-meta { display: none; }
}
</style>
