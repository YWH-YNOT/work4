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
            <th>视觉到课</th>
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
            <td>
              <button @click="syncVision(s)" class="mini-btn" :disabled="syncingId === s.id">
                {{ syncingId === s.id ? '同步中...' : '同步' }}
              </button>
            </td>
          </tr>
          <tr v-if="sessions.length === 0">
            <td colspan="6" class="empty-cell">暂无发布的签到任务</td>
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
const syncingId = ref<number | null>(null)

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

async function syncVision(s: any) {
  syncingId.value = s.id
  try {
    const res = await axios.post(`/api/v1/attendance/sessions/${s.id}/sync-vision`, {
      lookback_minutes: 30
    })
    const data = res.data
    showMessage(`视觉同步完成：匹配 ${data.matched_students} 人，新增到课 ${data.created} 人`)
    await fetchSessions()
    if (data.unmatched_names?.length) {
      console.warn('未匹配视觉姓名', data.unmatched_names)
    }
  } catch (e: any) {
    showMessage(e.response?.data?.detail || "视觉同步失败", "error")
  } finally {
    syncingId.value = null
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
  background: rgba(255,255,255,0.84); border: 1px solid #d8e7f8;
  border-radius: 16px; padding: 24px; max-width: 600px;
  box-shadow: 0 12px 28px rgba(15,47,100,0.06);
}
.publish-card h3 { margin: 0 0 16px 0; color: #0f2f64; font-size: 16px; font-weight: 800; }
.form-row { display: flex; gap: 12px; margin-bottom: 16px; }

.select-input {
  background: #ffffff; border: 1px solid #c8ddf4;
  color: #0f2f64; border-radius: 8px; padding: 10px 14px; font-size: 14px;
  outline: none; flex: 1; min-width: 200px;
}
.select-input:focus { border-color: #0b63b6; box-shadow: 0 0 0 3px rgba(11,99,182,0.08); }
.select-input.duration { flex: 0 0 150px; min-width: unset; }
.select-input option { background: #ffffff; color: #0f2f64; }

.btn { border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 14px;}
.btn.primary { background: linear-gradient(135deg, #0b63b6, #0a88df); color: white; display: inline-flex; align-items: center; justify-content: center;}
.btn.primary:hover:not(:disabled) { box-shadow: 0 8px 18px rgba(11,99,182,0.22); transform: translateY(-1px); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.mini-btn { border: 1px solid #a7f3d0; background: #ecfdf5; color: #0b7d56; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-weight: 700; }
.mini-btn:hover:not(:disabled) { background: #d7f8e9; }
.mini-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.sessions-list {
  background: rgba(255,255,255,0.86);
  border: 1px solid #d8e7f8;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 14px 32px rgba(15,47,100,0.07);
}
.sessions-list h3 { margin: 0 0 16px 0; font-size: 16px; font-weight: 800; color: #0f2f64; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 12px 16px;
  color: #5b6f92;
  font-weight: 800;
  font-size: 13px;
  background: #f1f7ff;
  border-top: 1px solid #d8e7f8;
  border-bottom: 1px solid #cfe0f4;
}
.data-table th:first-child { border-radius: 8px 0 0 8px; }
.data-table th:last-child { border-radius: 0 8px 8px 0; }
.data-table td { padding: 16px; border-bottom: 1px solid #e3edf8; color: #0f2f64; font-size: 14px; }
.data-table tbody tr { transition: background 0.16s; }
.data-table tbody tr:hover { background: #f7fbff; }
.data-table tbody tr:last-child td { border-bottom: none; }
.empty-cell { text-align: center !important; color: var(--text-secondary) !important; padding: 40px !important; }

.tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.tag.active { background: #ecfdf5; color: #0b7d56; border: 1px solid #a7f3d0; }
.tag.expired { background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; }

.toast { position: fixed; bottom: 32px; right: 32px; padding: 12px 24px; border-radius: 12px; font-weight: 600; animation: fadein 0.3s; z-index: 1000; }
.toast.success { background: rgba(16,185,129,0.9); color: white; }
.toast.error { background: rgba(239,68,68,0.9); color: white; }
@keyframes fadein { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
</style>
