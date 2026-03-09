<template>
  <div class="posture-history">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <div class="page-title">📊 我的姿态记录</div>
        <div class="page-sub">课堂专注度历史 · {{ myStats.my_name || '加载中...' }}</div>
      </div>
      <div class="rate-badge" :class="rateClass">专注率 {{ myStats.attentive_rate ?? 0 }}%</div>
    </div>

    <!-- 无数据提示 -->
    <div v-if="!loading && myStats.total === 0" class="empty-state">
      <div class="empty-icon">�</div>
      <div class="empty-text">暂无姿态记录</div>
      <div class="empty-sub">尚未被 Jetson 摄像头识别到，或人脸数据未注册。</div>
    </div>

    <template v-else>
      <!-- 四格统计 -->
      <div class="stat-grid">
        <div v-for="item in statItems" :key="item.key" class="stat-card" :style="{ borderColor: item.color }">
          <div class="stat-num" :style="{ color: item.color }">{{ myStats[item.key] ?? 0 }}</div>
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-pct" :style="{ color: item.color }">
            {{ myStats.total > 0 ? ((myStats[item.key] ?? 0) / myStats.total * 100).toFixed(1) : 0 }}%
          </div>
        </div>
      </div>

      <!-- SVG 饼图 -->
      <div class="pie-section">
        <div class="panel-label">姿态分布</div>
        <div class="pie-wrap">
          <svg viewBox="0 0 100 100" class="pie-svg">
            <template v-for="(seg, i) in pieSegments" :key="i">
              <path :d="seg.d" :fill="seg.color" opacity="0.85" />
            </template>
            <!-- 中心文字 -->
            <circle cx="50" cy="50" r="26" fill="#050e1a" />
            <text x="50" y="47" text-anchor="middle" fill="#10b981" font-size="9" font-weight="700">{{ myStats.attentive_rate ?? 0 }}%</text>
            <text x="50" y="57" text-anchor="middle" fill="#9ca3af" font-size="5.5">专注率</text>
          </svg>
          <!-- 图例 -->
          <div class="pie-legend">
            <div v-for="item in statItems" :key="item.key" class="legend-item">
              <div class="legend-dot" :style="{ background: item.color }"></div>
              <span class="legend-label">{{ item.label }}</span>
              <span class="legend-val">{{ myStats[item.key] ?? 0 }} 次</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近记录列表 -->
      <div class="records-section">
        <div class="panel-label">最近 {{ records.length }} 条记录</div>
        <div class="records-list">
          <div v-if="records.length === 0" class="empty-tip">暂无记录</div>
          <div v-for="(r, i) in records" :key="i" class="record-row">
            <div class="rec-time">{{ r.t }}</div>
            <div class="rec-badge" :class="r.label">{{ labelCN[r.label] || r.label }}</div>
          </div>
        </div>
      </div>
    </template>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrap">
      <div class="spinner"></div> 加载中...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const API  = '/api/v1'

const loading  = ref(true)
const myStats  = ref<Record<string, any>>({ attentive: 0, drowsy: 0, distracted: 0, absent: 0, total: 0, attentive_rate: 0, my_name: '', records: [] })
const records  = ref<{t: string; label: string}[]>([])

const labelCN: Record<string, string> = {
  attentive: '专注', drowsy: '困倦', distracted: '分心', absent: '离席'
}

const statItems = [
  { key: 'attentive',  label: '专注',  color: '#10b981' },
  { key: 'drowsy',     label: '困倦',  color: '#f59e0b' },
  { key: 'distracted', label: '分心',  color: '#ef4444' },
  { key: 'absent',     label: '离席',  color: '#6b7280' },
]

const rateClass = computed(() => {
  const r = myStats.value.attentive_rate ?? 0
  if (r >= 70) return 'good'
  if (r >= 40) return 'mid'
  return 'bad'
})

// ─── 饼图计算 ─────────────────────────────────
const pieSegments = computed(() => {
  const total = myStats.value.total || 1
  const vals  = statItems.map(i => ({ pct: (myStats.value[i.key] ?? 0) / total, color: i.color }))
  const segs: {d: string; color: string}[] = []
  let startAngle = -Math.PI / 2
  vals.forEach(v => {
    if (v.pct === 0) return
    const endAngle = startAngle + v.pct * 2 * Math.PI
    const cx = 50, cy = 50, r = 38
    const x1 = cx + r * Math.cos(startAngle)
    const y1 = cy + r * Math.sin(startAngle)
    const x2 = cx + r * Math.cos(endAngle)
    const y2 = cy + r * Math.sin(endAngle)
    const large = endAngle - startAngle > Math.PI ? 1 : 0
    segs.push({ d: `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`, color: v.color })
    startAngle = endAngle
  })
  return segs
})

async function loadStats() {
  loading.value  = true
  try {
    const data = await fetch(`${API}/posture/my-stats`, {
      headers: { Authorization: `Bearer ${auth.token}` }
    }).then(r => r.json())
    myStats.value = data
    records.value = (data.records ?? []).reverse()
  } catch { /* 忽略 */ }
  finally { loading.value = false }
}

onMounted(loadStats)
</script>

<style scoped>
.posture-history { padding: 28px; color: #c8d6e5; font-family: 'Inter', sans-serif; }

/* ── 页头 ── */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title  { font-size: 1.6rem; font-weight: 700; color: #a8ff78; }
.page-sub    { font-size: .8rem; color: #6b7280; margin-top: 4px; }
.rate-badge  { padding: 8px 20px; border-radius: 20px; font-size: 1rem; font-weight: 700; border: 1px solid; }
.rate-badge.good { color: #10b981; border-color: #10b981; background: rgba(16,185,129,.1); }
.rate-badge.mid  { color: #f59e0b; border-color: #f59e0b; background: rgba(245,158,11,.1); }
.rate-badge.bad  { color: #ef4444; border-color: #ef4444; background: rgba(239,68,68,.1); }

/* ── 空状态 ── */
.empty-state { text-align: center; padding: 80px 20px; color: #6b7280; }
.empty-icon  { font-size: 3rem; margin-bottom: 12px; }
.empty-text  { font-size: 1.2rem; font-weight: 600; color: #9ca3af; }
.empty-sub   { font-size: .85rem; margin-top: 8px; }

/* ── 四格统计 ── */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.stat-card { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); border-top-width: 3px; border-radius: 14px; padding: 18px 16px; text-align: center; }
.stat-num  { font-size: 2.2rem; font-weight: 800; line-height: 1; }
.stat-label{ font-size: .8rem; color: #9ca3af; margin-top: 6px; }
.stat-pct  { font-size: .85rem; font-weight: 600; margin-top: 4px; opacity: .8; }

/* ── 饼图 ── */
.pie-section { background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.05); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
.panel-label { font-size: .82rem; color: #10b981; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 14px; }
.pie-wrap    { display: flex; align-items: center; gap: 36px; }
.pie-svg     { width: 160px; height: 160px; flex-shrink: 0; }
.pie-legend  { display: flex; flex-direction: column; gap: 10px; }
.legend-item { display: flex; align-items: center; gap: 10px; }
.legend-dot  { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }
.legend-label{ font-size: .88rem; color: #9ca3af; width: 36px; }
.legend-val  { font-size: .9rem; font-weight: 600; color: #f3f4f6; }

/* ── 记录列表 ── */
.records-section { background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.05); border-radius: 16px; padding: 20px; }
.records-list    { max-height: 300px; overflow-y: auto; }
.records-list::-webkit-scrollbar { width: 4px; }
.records-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 4px; }
.record-row  { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; margin-bottom: 4px; background: rgba(255,255,255,.02); }
.record-row:hover { background: rgba(255,255,255,.04); }
.rec-time    { font-size: .82rem; color: #6b7280; font-family: monospace; }
.rec-badge   { font-size: .75rem; padding: 3px 10px; border-radius: 6px; font-weight: 600; border: 1px solid transparent; }
.rec-badge.attentive  { background: rgba(16,185,129,.1);  color: #34d399; border-color: rgba(16,185,129,.3); }
.rec-badge.drowsy     { background: rgba(245,158,11,.1);  color: #fbbf24; border-color: rgba(245,158,11,.3); }
.rec-badge.distracted { background: rgba(239,68,68,.1);   color: #f87171; border-color: rgba(239,68,68,.3); }
.rec-badge.absent     { background: rgba(107,114,128,.1); color: #9ca3af; border-color: rgba(107,114,128,.3); }
.empty-tip { color: #6b7280; font-size: .85rem; text-align: center; padding: 20px 0; font-style: italic; }

/* ── 加载 ── */
.loading-wrap { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 80px; color: #6b7280; font-size: .9rem; }
.spinner      { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,.1); border-top-color: #10b981; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
