<template>
  <div class="page">
    <div class="page-header"><h1 class="page-title">对话日志</h1></div>
    <div class="filter-bar">
      <input v-model="keyword" placeholder="搜索提问/回答关键词..." class="inp" @input="resetAndLoad"/>
      <input v-model="student" placeholder="学号/姓名" class="inp small" @input="resetAndLoad"/>
      <input v-model="start" type="date" class="inp date" @change="resetAndLoad"/>
      <input v-model="end" type="date" class="inp date" @change="resetAndLoad"/>
      <button class="clear-btn" @click="clearFilters">清空</button>
    </div>
    <div class="stats-panel" v-if="stats">
      <div class="stat-box"><span>学生提问</span><strong>{{ stats.summary.total_questions }}</strong></div>
      <div class="stat-box"><span>AI 回答</span><strong>{{ stats.summary.total_answers }}</strong></div>
      <div class="stat-box"><span>活跃学生</span><strong>{{ stats.summary.active_students }}</strong></div>
      <div class="stat-box"><span>平均响应</span><strong>{{ msText(stats.summary.avg_response_ms) }}</strong></div>
      <div class="top-users">
        <div class="top-title">提问排行</div>
        <div v-if="stats.students.length===0" class="top-empty">当前筛选范围暂无学生提问</div>
        <div v-for="s in stats.students.slice(0, 5)" :key="s.student_id" class="top-user">
          <span>{{ s.student_name || s.username }}</span>
          <b>{{ s.questions }} 问</b>
        </div>
      </div>
    </div>
    <div class="log-list">
      <div v-for="l in logs" :key="l.id" class="log-item" :class="l.role">
        <div class="log-header">
          <span class="log-user">{{ l.user }}</span>
          <span class="log-role">{{ l.role==='user'?'问':'答' }}</span>
          <span class="log-course" v-if="l.course">{{ l.course }}</span>
          <span class="log-latency" v-if="l.role==='assistant' && l.latency_ms">响应 {{ msText(l.latency_ms) }}</span>
          <span class="log-time">{{ fmt(l.created_at) }}</span>
        </div>
        <div class="log-content">{{ l.content }}</div>
      </div>
      <div v-if="logs.length===0" class="empty">暂无对话记录</div>
    </div>
    <div class="pagination">
      <button @click="prev" :disabled="page<=1" class="page-btn">← 上页</button>
      <span class="page-info">第 {{ page }} 页 / 共 {{ total }} 条</span>
      <button @click="next" :disabled="page*pageSize>=total" class="page-btn">下页 →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
const logs = ref<any[]>([])
const total = ref(0)
const stats = ref<any | null>(null)
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const student = ref('')
const start = ref('')
const end = ref('')
const fmt = (d: string) => new Date(d).toLocaleString('zh-CN')
const msText = (ms: number | null | undefined) => {
  if (ms === null || ms === undefined) return '暂无'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`
}

function buildQuery(extra: Record<string, string | number> = {}) {
  const params = new URLSearchParams()
  Object.entries(extra).forEach(([k, v]) => params.set(k, String(v)))
  if (keyword.value) params.set('keyword', keyword.value)
  if (student.value) params.set('student', student.value)
  if (start.value) params.set('start', start.value)
  if (end.value) params.set('end', end.value)
  return params.toString()
}

async function load() {
  const query = buildQuery({ page: page.value, page_size: pageSize })
  const url = `/api/v1/logs/?${query}`
  try { const r = await axios.get(url); logs.value = r.data.items; total.value = r.data.total } catch {}
}

async function loadStats() {
  const query = buildQuery({ limit: 20 })
  try { const r = await axios.get(`/api/v1/logs/stats?${query}`); stats.value = r.data } catch {}
}

function resetAndLoad() { page.value = 1; load(); loadStats() }
function clearFilters() {
  keyword.value = ''
  student.value = ''
  start.value = ''
  end.value = ''
  resetAndLoad()
}
function prev() { if (page.value > 1) { page.value--; load() } }
function next() { if (page.value * pageSize < total.value) { page.value++; load() } }
onMounted(() => { load(); loadStats() })
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.inp { flex: 1; background: rgba(255,255,255,0.9); border: 1px solid #c8ddf4; border-radius: 10px; padding: 8px 14px; color: #0f2f64; font-size: 14px; outline: none; }
.inp.small { flex: 0 0 150px; }
.inp.date { flex: 0 0 150px; color-scheme: light; }
.clear-btn { border: 1px solid #c8ddf4; background: #f8fbff; color: #5b6f92; border-radius: 10px; padding: 8px 14px; cursor: pointer; }
.clear-btn:hover { color: #34d399; border-color: rgba(16,185,129,0.3); }
.stats-panel { display: grid; grid-template-columns: repeat(4, minmax(110px, 1fr)) minmax(260px, 1.4fr); gap: 12px; margin-bottom: 18px; }
.stat-box, .top-users { background: rgba(255,255,255,0.84); border: 1px solid #d8e7f8; border-radius: 14px; padding: 16px; box-shadow: 0 10px 24px rgba(15,47,100,0.05); }
.stat-box span { display: block; color: var(--text-secondary); font-size: 13px; margin-bottom: 8px; }
.stat-box strong { color: #34d399; font-size: 28px; line-height: 1; }
.top-title { color: var(--text-main); font-weight: 800; margin-bottom: 8px; }
.top-user { display: flex; justify-content: space-between; gap: 10px; color: var(--text-secondary); font-size: 13px; line-height: 1.9; }
.top-user b { color: #93c5fd; }
.top-empty { color: var(--text-secondary); font-size: 13px; padding: 8px 0; }
.log-list { display: flex; flex-direction: column; gap: 8px; }
.log-item { padding: 12px 16px; border-radius: 12px; border: 1px solid; }
.log-item.user { background: rgba(99,102,241,0.06); border-color: rgba(99,102,241,0.15); }
.log-item.assistant { background: rgba(16,185,129,0.04); border-color: rgba(16,185,129,0.12); }
.log-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 12px; }
.log-user { font-weight: 700; color: #818cf8; }
.log-role { background: rgba(99,102,241,0.15); color: #818cf8; padding: 2px 8px; border-radius: 6px; }
.log-item.assistant .log-role { background: rgba(16,185,129,0.15); color: #34d399; }
.log-item.assistant .log-user { color: #34d399; }
.log-course { color: #5b6f92; background: #f7fbff; border: 1px solid #e3edf8; padding: 2px 8px; border-radius: 6px; }
.log-latency { color: #93c5fd; background: rgba(59,130,246,0.12); padding: 2px 8px; border-radius: 6px; }
.log-time { color: var(--text-secondary); margin-left: auto; }
.log-content { font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-height: 80px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; }
.pagination { display: flex; align-items: center; gap: 16px; justify-content: center; margin-top: 20px; }
.page-btn { padding: 6px 16px; border-radius: 8px; background: #f8fbff; border: 1px solid #c8ddf4; color: #5b6f92; cursor: pointer; }
.page-btn:hover:not(:disabled) { background: #ecfdf5; color: #0b7d56; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 14px; color: var(--text-secondary); }
</style>
