<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">教师控制台</h1>
      <p class="page-sub">{{ today }}</p>
    </div>
    <div class="stats-grid">
      <div class="stat-card emerald">
        <div class="stat-icon"><el-icon><Collection /></el-icon></div>
        <div class="stat-num">{{ stats.courses }}</div>
        <div class="stat-label">我的课程</div>
      </div>
      <div class="stat-card indigo">
        <div class="stat-icon"><el-icon><Document /></el-icon></div>
        <div class="stat-num">{{ stats.assignments }}</div>
        <div class="stat-label">已发布作业</div>
      </div>
      <div class="stat-card amber">
        <div class="stat-icon"><el-icon><Memo /></el-icon></div>
        <div class="stat-num">{{ stats.submissions }}</div>
        <div class="stat-label">待批改提交</div>
      </div>
      <div class="stat-card rose">
        <div class="stat-icon"><el-icon><DataLine /></el-icon></div>
        <div class="stat-num">{{ stats.logs }}</div>
        <div class="stat-label">学生提问总数</div>
      </div>
    </div>
    <div class="quick-links">
      <router-link to="/teacher/courses" class="quick-card emerald"><el-icon><Collection /></el-icon><span>管理课程</span></router-link>
      <router-link to="/teacher/assignments" class="quick-card indigo"><el-icon><Document /></el-icon><span>布置作业</span></router-link>
      <router-link to="/teacher/announcements" class="quick-card amber"><el-icon><Bell /></el-icon><span>发布公告</span></router-link>
      <router-link to="/teacher/grades" class="quick-card rose"><el-icon><TrophyBase /></el-icon><span>录入成绩</span></router-link>
      <router-link to="/teacher/quiz" class="quick-card purple"><el-icon><Memo /></el-icon><span>创建测验</span></router-link>
      <router-link to="/teacher/logs" class="quick-card teal"><el-icon><DataLine /></el-icon><span>查看日志</span></router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const today = new Date().toLocaleDateString('zh-CN', { year:'numeric', month:'long', day:'numeric', weekday:'long' })
const stats = ref({ courses: 0, assignments: 0, submissions: 0, logs: 0 })

onMounted(async () => {
  try {
    const [c, a, l] = await Promise.all([
      axios.get('/api/v1/courses/my'),
      axios.get('/api/v1/assignments/'),
      axios.get('/api/v1/logs/?page_size=1'),
    ])
    stats.value.courses = c.data.length
    stats.value.assignments = a.data.length
    stats.value.logs = l.data.total || 0
  } catch {}
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 26px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
.stat-card { border-radius: 16px; padding: 20px; border: 1px solid; display: flex; flex-direction: column; gap: 8px; }
.stat-card.emerald { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); }
.stat-card.indigo { background: rgba(99,102,241,0.08); border-color: rgba(99,102,241,0.2); }
.stat-card.amber { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.2); }
.stat-card.rose { background: rgba(244,63,94,0.08); border-color: rgba(244,63,94,0.2); }
.stat-icon { font-size: 22px; }
.stat-card.emerald .stat-icon { color: #34d399; }
.stat-card.indigo .stat-icon { color: #818cf8; }
.stat-card.amber .stat-icon { color: #fbbf24; }
.stat-card.rose .stat-icon { color: #fb7185; }
.stat-num { font-size: 32px; font-weight: 800; color: var(--text-main); line-height: 1; }
.stat-label { font-size: 13px; color: var(--text-secondary); }
.quick-links { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.quick-card { display: flex; align-items: center; gap: 12px; padding: 18px 20px; border-radius: 16px; border: 1px solid; text-decoration: none; font-size: 15px; font-weight: 600; transition: all 0.18s; }
.quick-card:hover { transform: translateY(-2px); }
.quick-card.emerald { background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.2); color: #34d399; }
.quick-card.indigo { background: rgba(99,102,241,0.06); border-color: rgba(99,102,241,0.2); color: #818cf8; }
.quick-card.amber { background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.2); color: #fbbf24; }
.quick-card.rose { background: rgba(244,63,94,0.06); border-color: rgba(244,63,94,0.2); color: #fb7185; }
.quick-card.purple { background: rgba(168,85,247,0.06); border-color: rgba(168,85,247,0.2); color: #c084fc; }
.quick-card.teal { background: rgba(20,184,166,0.06); border-color: rgba(20,184,166,0.2); color: #2dd4bf; }
.quick-card .el-icon { font-size: 20px; }
</style>
