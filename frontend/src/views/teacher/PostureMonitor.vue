<template>
  <div class="posture-monitor">
    <!-- 页头 -->
    <div class="page-header">
      <div class="header-left">
        <div class="page-title"><span class="title-icon">👁</span>姿态监控</div>
        <div class="page-sub">YOLO11-npose / Jetson Edge AI</div>
      </div>
      <div class="header-right">
        <div class="jetson-badge" :class="jetsonOnline ? 'online' : 'offline'">
          <span class="dot"></span>{{ jetsonOnline ? 'Jetson 在线' : 'Jetson 离线' }}
        </div>
        <div class="stat-pill attentive">专注 {{ trendsAvg }}%</div>
      </div>
    </div>

    <!-- 警报横幅（分心率 > 40% 时显示） -->
    <transition name="alert-slide">
      <div v-if="alertMsg" class="alert-banner">
        <span class="alert-icon">⚠️</span>
        {{ alertMsg }}
        <button class="alert-close" @click="alertMsg = ''">✕</button>
      </div>
    </transition>

    <!-- 主体上排：视频 + 状态 -->
    <div class="monitor-body">
      <!-- 左：视频流 -->
      <div class="stream-panel">
        <div class="panel-label">实时视频流</div>
        <div class="stream-wrap">
          <img v-if="currentFrameSrc" :src="currentFrameSrc" class="stream-img" alt="姿态检测视频流" />
          <div v-else class="stream-placeholder">等待 Jetson 推送...</div>
        </div>
        <div class="stream-meta">
          {{ jetsonOnline ? '🟢 Jetson 在线' : '⚫ 等待数据...' }} · {{ updateTime }}
        </div>
      </div>

      <!-- 右：当前状态 -->
      <div class="status-panel">
        <div class="panel-label">当前课堂状态 <span class="update-time">{{ updateTime }}</span></div>

        <!-- 四格统计（实时） -->
        <div class="stat-grid">
          <div v-for="item in statItems" :key="item.key" class="stat-card" :style="{ borderColor: item.color }">
            <div class="stat-num" :style="{ color: item.color }">{{ stats[item.key] ?? 0 }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>

        <!-- 学生列表 -->
        <div class="student-list">
          <div class="list-header">检测到的学生 ({{ students.length }})</div>
          <div v-if="students.length === 0" class="empty-tip">暂无检测数据，等待 Jetson 推送...</div>
          <div v-for="s in students" :key="s.id" class="student-row" :class="s.label">
            <div class="s-avatar" :class="{'unknown': !s.student_name}">
              <span v-if="s.student_name">{{ s.student_name[0] }}</span>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </div>
            <div class="s-info">
              <div class="s-name" :class="{'unknown-text': !s.student_name}">
                {{ s.student_name || `未知学生 #${s.id}` }}
              </div>
              <!-- 置信度进度条 -->
              <div class="conf-bar-wrap" v-if="s.confidence != null">
                <div class="conf-bar" :style="{ width: `${Math.round((s.confidence ?? 0) * 100)}%`, background: labelBarColor(s.label) }"></div>
              </div>
            </div>
            <div class="s-right">
              <!-- 困倦持续告警 -->
              <div v-if="s.drowsy_duration > 0" class="drowsy-dur">⏳{{ s.drowsy_duration }}s</div>
              <div class="s-badge" :class="s.label">{{ s.label_cn }}</div>
              <div v-if="s.confidence != null" class="s-conf">{{ Math.round((s.confidence ?? 0) * 100) }}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 下排：专注率趋势图 -->
    <div class="trend-panel">
      <div class="panel-label">专注率趋势（最近 {{ trends.length }} 次记录）</div>
      
      <div v-if="trends.length > 1" class="trend-chart">
        <!-- y 轴文字刻度 (用 HTML 定位在左侧避免被 SVG 遮挡切割) -->
        <div class="y-axis">
          <div class="y-label" style="top: 0%;">100%</div>
          <div class="y-label" style="top: 25%;">75%</div>
          <div class="y-label" style="top: 50%;">50%</div>
          <div class="y-label" style="top: 75%;">25%</div>
        </div>

        <svg :viewBox="`0 0 ${chartW} ${chartH}`" preserveAspectRatio="none" class="chart-svg">
          <!-- 网格线 -->
          <line v-for="y in [25,50,75]" :key="y" x1="0" :x2="chartW" :y1="pct(y)" :y2="pct(y)" stroke="#334" stroke-width="0.5" stroke-dasharray="2 3" />
          
          <!-- 专注区域 -->
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#10b981" stop-opacity="0.4"/>
              <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          <path :d="smoothPathArgs.area" fill="url(#grad)" />
          <path :d="smoothPathArgs.d" fill="none" stroke="#10b981" stroke-width="2" stroke-linejoin="round" filter="url(#glow)" />
          
          <!-- 数据点 -->
          <circle v-for="(p,i) in dotPoints" :key="i" :cx="p.x" :cy="p.y" r="3" fill="#050e1a" stroke="#10b981" stroke-width="1.5" />
        </svg>
      </div>

      <div v-else class="trend-empty">
        <div class="spinner"></div> 数据积累中，请等待...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const API = '/api/v1'

// ─── 状态 ───────────────────────────────────
const currentFrameSrc = ref('')
const jetsonOnline    = ref(false)
const students        = ref<any[]>([])
const updateTime      = ref('--')
const stats           = ref<Record<string, any>>({
  attentive: 0, drowsy: 0, distracted: 0, absent: 0,
  attentive_rate: 0, total: 0
})
const trends = ref<{t: string; rate: number}[]>([])
const alertMsg = ref('')   // 警报横幅文字，空字符串 = 无警报

const statItems = [
  { key: 'attentive',  label: '专注',  color: '#10b981' },
  { key: 'drowsy',     label: '困倦',  color: '#f59e0b' },
  { key: 'distracted', label: '分心',  color: '#ef4444' },
  { key: 'absent',     label: '离席',  color: '#6b7280' },
]


// ─── 趋势图计算 ──────────────────────────────
const chartW = 400
const chartH = 80
const pct = (v: number) => chartH - (v / 100) * chartH
// 趋势历史平均专注率（代替瞬时 0/100% 显示在顶部徽章）
const trendsAvg = computed(() => {
  if (!trends.value.length) return stats.value.attentive_rate ?? 0
  const avg = trends.value.reduce((s, d) => s + d.rate, 0) / trends.value.length
  return Math.round(avg)
})

const dotPoints = computed(() =>
  trends.value.map((d, i) => ({
    x: trends.value.length > 1 ? (i / (trends.value.length - 1)) * chartW : chartW / 2,
    y: pct(d.rate),
  }))
)
// 将折线改为平滑的曲线 (三次贝塞尔曲线)
const smoothPathArgs = computed(() => {
  if (dotPoints.value.length < 2) return { d: '', area: '' }
  const pts = dotPoints.value
  const first = pts[0]
  const last = pts[pts.length - 1]
  if (!first || !last) return { d: '', area: '' }
  let d = `M ${first.x},${first.y}`
  for (let i = 0; i < pts.length - 1; i++) {
    const cur = pts[i]
    const nxt = pts[i + 1]
    if (!cur || !nxt) continue
    const cp1x = (cur.x + nxt.x) / 2
    const cp2x = cp1x
    d += ` C ${cp1x},${cur.y} ${cp2x},${nxt.y} ${nxt.x},${nxt.y}`
  }
  const area = `${d} L ${last.x},${chartH} L ${first.x},${chartH} Z`
  return { d, area }
})

// ─── API 请求 ─────────────────────────────
const headers = () => ({ Authorization: `Bearer ${auth.token}` })

async function pollLatest() {
  try {
    const data = await fetch(`${API}/posture/latest`, { headers: headers() }).then(r => r.json())
    students.value     = data.students ?? []
    jetsonOnline.value = !!data.recorded_at
    if (data.recorded_at) updateTime.value = new Date(data.recorded_at).toLocaleTimeString('zh-CN')
  } catch { /* 忽略 */ }
}

async function pollStats() {
  try {
    const data = await fetch(`${API}/posture/stats`, { headers: headers() }).then(r => r.json())
    stats.value = data
    // 警报逻辑：分心+困倦 > 40% 触发
    const total = data.total ?? 0
    if (total > 0) {
      const badRate = ((data.distracted ?? 0) + (data.drowsy ?? 0)) / total
      if (badRate >= 0.4) {
        const n = (data.distracted ?? 0) + (data.drowsy ?? 0)
        alertMsg.value = `当前 ${n} 名学生注意力分散（分心/困倦），请留意！`
      } else if (data.attentive_rate >= 60) {
        alertMsg.value = ''   // 恢复正常，自动清除警报
      }
    }
  } catch { /* 忽略 */ }
}

async function pollTrends() {
  try {
    trends.value = await fetch(`${API}/posture/trends?limit=20`, { headers: headers() }).then(r => r.json())
  } catch { /* 忽略 */ }
}

// 不同状态对应的进度条颜色
function labelBarColor(label: string): string {
  const map: Record<string, string> = {
    attentive:  '#10b981',
    drowsy:     '#f59e0b',
    distracted: '#ef4444',
    absent:     '#6b7280',
  }
  return map[label] ?? '#6b7280'
}

// ─── SSE 实时帧流 ─────────────────────────
let es: EventSource | null = null
function connectSSE() {
  es = new EventSource(`${API}/posture/frame-stream`)
  es.onmessage = (e) => {
    if (e.data === 'timeout') { es?.close(); setTimeout(connectSSE, 500); return }
    currentFrameSrc.value = `data:image/jpeg;base64,${e.data}`
  }
  es.onerror = () => { es?.close(); setTimeout(connectSSE, 1000) }
}

// ─── 定时器 ─────────────────────────────
let latestTimer: ReturnType<typeof setInterval>
let statsTimer:  ReturnType<typeof setInterval>
let trendsTimer: ReturnType<typeof setInterval>

onMounted(async () => {
  await Promise.all([pollLatest(), pollStats(), pollTrends()])
  latestTimer = setInterval(pollLatest, 2000)
  statsTimer  = setInterval(pollStats, 5000)
  trendsTimer = setInterval(pollTrends, 10000)
  connectSSE()
})

onUnmounted(() => {
  clearInterval(latestTimer)
  clearInterval(statsTimer)
  clearInterval(trendsTimer)
  es?.close()
})
</script>

<style scoped>
.posture-monitor { padding: 28px; color: #c8d6e5; font-family: 'Inter', sans-serif; }

/* ── 页头 ── */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 1.6rem; font-weight: 700; color: #a8ff78; }
.title-icon { margin-right: 8px; }
.page-sub { font-size: .8rem; color: #556; margin-top: 4px; font-family: monospace; }
.header-right { display: flex; gap: 12px; align-items: center; }
.jetson-badge { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: .8rem; border: 1px solid; }
.jetson-badge.online  { border-color: #10b981; color: #10b981; }
.jetson-badge.offline { border-color: #4b5563; color: #4b5563; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.stat-pill { padding: 6px 14px; border-radius: 20px; font-size: .85rem; font-weight: 600; background: rgba(16,185,129,.15); color: #10b981; border: 1px solid #10b981; }

/* ── 主体 ── */
.monitor-body { 
  display: grid; 
  grid-template-columns: 1fr 1.2fr; 
  gap: 20px; 
  margin-bottom: 20px; 
}

/* 响应式调整：视口较窄时，改为上下堆叠布局 */
@media screen and (max-width: 1024px) {
  .monitor-body {
    grid-template-columns: 1fr;
  }
}

/* ── 视频面板 ── */
.stream-panel { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; }
.panel-label { font-size: .8rem; color: #10b981; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 12px; display: flex; justify-content: space-between; }
.update-time { color: #556; font-size: .75rem; }
.stream-wrap { position: relative; background: #050e1a; border-radius: 8px; overflow: hidden; width: 100%; aspect-ratio: 4/3; }
.stream-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.stream-placeholder { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #334; font-size: .85rem; }
.stream-meta { margin-top: 8px; font-size: .75rem; color: #556; text-align: center; }

/* ── 状态面板 ── */
.status-panel { background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.05); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }

/* ── 四格统计 ── */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 12px; }
.stat-card { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); border-left-width: 4px; border-radius: 12px; padding: 16px 14px; text-align: center; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.stat-num { font-size: 2rem; font-weight: 800; line-height: 1; letter-spacing: -0.5px; }
.stat-label { font-size: .8rem; color: #9ca3af; margin-top: 6px; font-weight: 500; }

/* ── 学生列表 ── */
.student-list { flex: 1; overflow-y: auto; padding-right: 4px; margin-right: -4px; /* hide scrollbar slightly */ }
.student-list::-webkit-scrollbar { width: 4px; }
.student-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
.list-header { font-size: .85rem; color: #9ca3af; margin-bottom: 12px; font-weight: 600; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.empty-tip { color: #6b7280; font-size: .85rem; padding: 20px 0; text-align: center; font-style: italic; }
.student-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 10px; margin-bottom: 8px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.03); transition: all .2s; }
.student-row:hover { background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.08); transform: translateX(2px); }
.s-avatar { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; background: linear-gradient(135deg, rgba(16,185,129,.2), rgba(16,185,129,.05)); color: #10b981; flex-shrink: 0; border: 1px solid rgba(16,185,129,.2); box-shadow: inset 0 0 10px rgba(16,185,129,.1); }
.s-avatar.unknown { background: rgba(107,114,128,.15); color: #9ca3af; border-color: rgba(107,114,128,.2); box-shadow: none; }
.s-info { flex: 1; }
.s-name { font-size: .95rem; font-weight: 600; color: #f3f4f6; letter-spacing: 0.5px; }
.s-name.unknown-text { color: #9ca3af; font-style: italic; font-weight: 400; }
.s-badge { font-size: .75rem; padding: 4px 10px; border-radius: 6px; font-weight: 600; flex-shrink: 0; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid transparent; }
.s-badge.attentive  { background: rgba(16,185,129,.1); color: #34d399; border-color: rgba(16,185,129,.3); }
.s-badge.drowsy     { background: rgba(245,158,11,.1); color: #fbbf24; border-color: rgba(245,158,11,.3); }
.s-badge.distracted { background: rgba(239,68,68,.1);  color: #f87171; border-color: rgba(239,68,68,.3); }
.s-badge.absent     { background: rgba(107,114,128,.1); color: #9ca3af; border-color: rgba(107,114,128,.3); }

/* ── 置信度进度条 ── */
.conf-bar-wrap { height: 3px; border-radius: 2px; background: rgba(255,255,255,.06); margin-top: 5px; overflow: hidden; }
.conf-bar { height: 100%; border-radius: 2px; transition: width .4s ease; }

/* ── 右侧区：困倦告警 + 标签 + 置信度 ── */
.s-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.drowsy-dur { font-size: .72rem; color: #fbbf24; font-weight: 700; background: rgba(245,158,11,.12); border: 1px solid rgba(245,158,11,.3); padding: 2px 6px; border-radius: 5px; }
.s-conf { font-size: .72rem; color: #6b7280; letter-spacing: 0.3px; min-width: 28px; text-align: right; }


/* ── 趋势图 ── */
.trend-panel { background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.05); border-radius: 16px; padding: 20px; padding-left: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.trend-chart { height: 110px; position: relative; margin-top: 10px; display: flex; padding-left: 45px; } /* 左侧留多点空间放刻度 */
.y-axis { position: absolute; left: 0; top: 0; bottom: 0; width: 40px; }
.y-label { position: absolute; left: 0; transform: translateY(-50%); font-size: 0.85rem; font-weight: 700; color: #a8ff78; font-family: 'Inter', monospace; letter-spacing: 0.5px; text-shadow: 0 0 8px rgba(168, 255, 120, 0.4); }
.chart-svg { width: 100%; height: 100%; overflow: visible; flex: 1; margin-left: 4px; }
.trend-empty { display: flex; align-items: center; justify-content: center; gap: 12px; height: 110px; color: #6b7280; font-size: .9rem; }
.spinner { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.1); border-top-color: #10b981; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 警报横幅 ── */
.alert-banner {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 18px; padding: 12px 18px;
  border-radius: 12px; font-size: .9rem; font-weight: 600; color: #fff;
  background: linear-gradient(90deg, rgba(239,68,68,.25), rgba(245,158,11,.18));
  border: 1px solid rgba(239,68,68,.4);
  box-shadow: 0 0 16px rgba(239,68,68,.2);
  animation: pulse-alert 2s ease-in-out infinite;
}
.alert-icon { font-size: 1.1rem; }
.alert-close {
  margin-left: auto; background: none; border: none; color: rgba(255,255,255,.6);
  cursor: pointer; font-size: 1rem; padding: 0 4px; line-height: 1;
  transition: color .2s;
}
.alert-close:hover { color: #fff; }
@keyframes pulse-alert {
  0%, 100% { box-shadow: 0 0 16px rgba(239,68,68,.2); }
  50%       { box-shadow: 0 0 28px rgba(239,68,68,.45); }
}
/* 过渡动画 */
.alert-slide-enter-active, .alert-slide-leave-active { transition: all .35s ease; }
.alert-slide-enter-from, .alert-slide-leave-to { opacity: 0; transform: translateY(-12px); max-height: 0; margin-bottom: 0; padding-top: 0; padding-bottom: 0; }
</style>
