<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">签到管理</h1>
      <p class="page-sub">发布临时签到任务，实时查看学生签到状况</p>
    </div>

    <!-- 上方操作区 -->
    <div class="top-controls">
      <div class="publish-card">
        <h3>发布新签到</h3>
        <div class="form-row">
          <select v-model="selectedCourseId" class="select-input">
            <option disabled :value="null">请选择课程</option>
            <option v-for="c in myCourses" :key="c.id" :value="c.id">{{ c.name }} ({{ c.course_code }})</option>
          </select>
          <select v-model="durationMinutes" class="select-input duration">
            <option :value="5">限时 5 分钟</option>
            <option :value="10">限时 10 分钟</option>
            <option :value="15">限时 15 分钟</option>
          </select>
        </div>
        <button @click="publishSession" class="btn primary" :disabled="!selectedCourseId || publishing">
          {{ publishing ? '发布中...' : '立即发布' }}
        </button>
      </div>
    </div>

    <!-- 已发布签到记录 -->
    <div class="sessions-list">
      <h3>历史签到记录</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>课程名称</th>
            <th>发布时间</th>
            <th>限时截止时间</th>
            <th>状态</th>
            <th>已签到人数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sessions" :key="s.id">
            <td>{{ s.course_name }}</td>
            <td>{{ new Date(s.created_at).toLocaleString() }}</td>
            <td>{{ new Date(s.deadline).toLocaleTimeString() }}</td>
            <td>
              <span v-if="s.is_active" class="tag active">进行中</span>
              <span v-else class="tag expired">已截止</span>
            </td>
            <td>{{ s.attendees }} 人</td>
          </tr>
          <tr v-if="sessions.length === 0">
            <td colspan="5" class="empty-cell">暂无发布的签到任务</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="msg" class="toast" :class="msgType">{{ msg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const myCourses = ref<any[]>([])
const selectedCourseId = ref<number | null>(null)
const durationMinutes = ref(5)
const publishing = ref(false)
const sessions = ref<any[]>([])

const msg = ref('')
const msgType = ref('success')

function showMessage(text: string, type = 'success') {
  msg.value = text
  msgType.value = type
  setTimeout(() => msg.value = '', 3000)
}

async function fetchCourses() {
  try {
    const res = await axios.get('/api/v1/courses/my')
    myCourses.value = res.data
  } catch (e) {
    console.error("Failed to load courses", e)
  }
}

async function fetchSessions() {
  try {
    const res = await axios.get('/api/v1/attendance/sessions')
    sessions.value = res.data
  } catch (e) {
    console.error("Failed to load sessions", e)
  }
}

async function publishSession() {
  if (!selectedCourseId.value) return
  publishing.value = true
  try {
    await axios.post('/api/v1/attendance/sessions', {
      course_id: selectedCourseId.value,
      duration_minutes: durationMinutes.value,
      title: "课堂签到"
    })
    showMessage("签到任务发布成功！")
    fetchSessions()
  } catch(e: any) {
    showMessage(e.response?.data?.detail || "发布失败", "error")
  } finally {
    publishing.value = false
  }
}

let refreshTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchCourses()
  fetchSessions()
  
  // 定期刷新状态(每10秒)，组件卸载时清除
  refreshTimer = setInterval(() => {
    fetchSessions()
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.page { padding: 32px; font-family: 'Inter', sans-serif; }
.page-header { margin-bottom: 32px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

.top-controls { margin-bottom: 32px; }
.publish-card {
  background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.2);
  border-radius: 16px; padding: 24px; max-width: 600px;
}
.publish-card h3 { margin: 0 0 16px 0; color: var(--text-main); font-size: 16px; font-weight: 600; }
.form-row { display: flex; gap: 12px; margin-bottom: 16px; }

.select-input {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
  color: var(--text-main); border-radius: 8px; padding: 10px 14px; font-size: 14px;
  outline: none; flex: 1; min-width: 200px;
}
.select-input:focus { border-color: #6366f1; }
.select-input.duration { flex: 0 0 150px; min-width: unset; }
.select-input option { background: #1e293b; color: var(--text-main); }

.btn { border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 14px;}
.btn.primary { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; display: inline-flex; align-items: center; justify-content: center;}
.btn.primary:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(99,102,241,0.3); transform: translateY(-1px); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.sessions-list { background: rgba(15,23,42,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; }
.sessions-list h3 { margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: var(--text-main); }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th { text-align: left; padding: 12px 16px; color: var(--text-secondary); font-weight: 600; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.data-table td { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.03); color: var(--text-main); font-size: 14px; }
.empty-cell { text-align: center !important; color: var(--text-secondary) !important; padding: 40px !important; }

.tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.tag.active { background: rgba(16,185,129,0.15); color: #34d399; }
.tag.expired { background: rgba(255,255,255,0.05); color: var(--text-secondary); }

.toast { position: fixed; bottom: 32px; right: 32px; padding: 12px 24px; border-radius: 12px; font-weight: 600; animation: fadein 0.3s; z-index: 1000; }
.toast.success { background: rgba(16,185,129,0.9); color: white; }
.toast.error { background: rgba(239,68,68,0.9); color: white; }
@keyframes fadein { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
</style>
