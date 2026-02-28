<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">课程签到</h1>
      <p class="page-sub">选择由您发布的签到任务进行签到</p>
    </div>
    
    <div class="courses-list">
      <div v-for="s in sessions" :key="s.id" class="course-card">
        <div class="course-info">
          <div class="avatar" :class="{ 'disabled': !s.is_active }">{{ s.course_name.charAt(0) }}</div>
          <div>
            <div class="course-name">{{ s.course_name }} - {{ s.title }}</div>
            <div class="course-code">
              发布时间: {{ new Date(s.created_at).toLocaleString() }} | 
              截止时间: <span :class="{'active-time': s.is_active, 'expired-time': !s.is_active}">{{ new Date(s.deadline).toLocaleTimeString() }}</span>
            </div>
          </div>
        </div>
        <div class="checkin-area">
          <span v-if="checkedIn[s.id]" class="checked">✓ 已签到</span>
          <span v-else-if="!s.is_active" class="expired">已截止</span>
          <button v-else @click="checkin(s.id)" :disabled="loading[s.id]" class="checkin-btn">
            {{ loading[s.id] ? '签到中...' : '立即签到' }}
          </button>
        </div>
      </div>
      <div v-if="sessions.length === 0" class="empty">当前没有开放的签到任务</div>
    </div>
    <div v-if="msg" class="toast" :class="msgType">{{ msg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const sessions = ref<any[]>([])
const checkedIn = ref<Record<number,boolean>>({})
const loading = ref<Record<number,boolean>>({})
const msg = ref('')
const msgType = ref('success')

async function checkin(sessionId: number) {
  loading.value[sessionId] = true
  try {
    await axios.post('/api/v1/attendance/checkin', { session_id: sessionId })
    checkedIn.value[sessionId] = true
    msg.value = '签到成功！'
    msgType.value = 'success'
  } catch(e:any) {
    msg.value = e.response?.data?.detail || '签到失败'
    msgType.value = 'error'
    if(e.response?.status === 400 && e.response?.data?.detail?.includes("已完成")) {
        checkedIn.value[sessionId] = true
    }
  } finally {
    loading.value[sessionId] = false
    setTimeout(() => msg.value = '', 3000)
  }
}

onMounted(async () => {
  try {
    // 获取当前所有签到任务
    const sessRes = await axios.get('/api/v1/attendance/sessions')
    sessions.value = sessRes.data
    
    // 检查我本人的签到记录
    const atRes = await axios.get('/api/v1/attendance/')
    for (const a of atRes.data) {
      if (a.session_id) checkedIn.value[a.session_id] = true
    }
  } catch(e) {
    console.error("加载签到数据失败", e)
  }
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.courses-list { display: flex; flex-direction: column; gap: 12px; }
.course-card { display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 14px; padding: 16px 20px; }
.course-info { display: flex; align-items: center; gap: 14px; }
.avatar { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; }
.avatar.disabled { background: #475569; }
.course-name { font-size: 15px; font-weight: 600; color: var(--text-main); margin-bottom: 2px;}
.course-code { font-size: 12px; color: var(--text-secondary); }
.active-time { color: #34d399; font-weight: 600; }
.expired-time { color: #f87171; }

.checked { color: #34d399; font-weight: 700; font-size: 14px; }
.expired { color: var(--text-secondary); font-size: 14px; font-style: italic; }

.checkin-btn { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border: none; border-radius: 8px; padding: 8px 20px; cursor: pointer; font-weight: 600; transition: all 0.2s; }
.checkin-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
.checkin-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 12px;}
.toast { position: fixed; bottom: 32px; right: 32px; padding: 12px 24px; border-radius: 12px; font-weight: 600; animation: fadein 0.3s; z-index: 1000; }
.toast.success { background: rgba(16,185,129,0.9); color: white; }
.toast.error { background: rgba(239,68,68,0.9); color: white; }
@keyframes fadein { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
</style>
