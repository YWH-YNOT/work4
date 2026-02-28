<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">👋 你好，{{ auth.user?.username }}</h1>
      <p class="page-sub">{{ today }} · 准备好开始今天的学习了吗？</p>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card indigo">
        <div class="stat-icon"><el-icon><Collection /></el-icon></div>
        <div class="stat-num">{{ courses.length }}</div>
        <div class="stat-label">门课程</div>
      </div>
      <div class="stat-card amber">
        <div class="stat-icon"><el-icon><Document /></el-icon></div>
        <div class="stat-num">{{ assignments.filter(a => !a.submitted).length }}</div>
        <div class="stat-label">待提交作业</div>
      </div>
      <div class="stat-card emerald">
        <div class="stat-icon"><el-icon><Bell /></el-icon></div>
        <div class="stat-num">{{ announcements.length }}</div>
        <div class="stat-label">条公告</div>
      </div>
      <div class="stat-card rose">
        <div class="stat-icon"><el-icon><Trophy /></el-icon></div>
        <div class="stat-num">{{ avgScore }}</div>
        <div class="stat-label">平均成绩</div>
      </div>
    </div>

    <!-- Grid -->
    <div class="content-grid">
      <!-- Announcements -->
      <div class="card">
        <div class="card-title"><el-icon><Bell /></el-icon> 最新公告</div>
        <div v-if="announcements.length === 0" class="empty">暂无公告</div>
        <div v-for="a in announcements.slice(0,4)" :key="a.id" class="ann-item">
          <span class="ann-priority" :class="`p${a.priority}`">
            {{ ['普通','重要','紧急'][a.priority] }}
          </span>
          <div>
            <div class="ann-title">{{ a.title }}</div>
            <div class="ann-time">{{ formatDate(a.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- My Courses -->
      <div class="card">
        <div class="card-title"><el-icon><Collection /></el-icon> 我的课程</div>
        <div v-if="courses.length === 0" class="empty">
          请先 <router-link to="/student/timetable">导入课表</router-link>
        </div>
        <div v-for="c in courses" :key="c.id" class="course-item">
          <div class="course-avatar">{{ c.name.charAt(0) }}</div>
          <div>
            <div class="course-name">{{ c.name }}</div>
            <div class="course-teacher">{{ c.teacher_name }} · {{ c.course_code }}</div>
          </div>
        </div>
      </div>

      <!-- Pending assignments -->
      <div class="card">
        <div class="card-title"><el-icon><Document /></el-icon> 待提交作业</div>
        <div v-if="pendingAssignments.length === 0" class="empty">暂无待提交作业 🎉</div>
        <div v-for="a in pendingAssignments.slice(0,4)" :key="a.id" class="assign-item">
          <div class="assign-name">{{ a.title }}</div>
          <div class="assign-due" v-if="a.due_date">{{ formatDate(a.due_date) }} 截止</div>
          <router-link to="/student/assignments" class="btn-sm">去提交</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const courses = ref<any[]>([])
const assignments = ref<any[]>([])
const announcements = ref<any[]>([])
const grades = ref<any[]>([])

const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
const pendingAssignments = computed(() => assignments.value.filter(a => !a.submitted))
const avgScore = computed(() => {
  const scores = grades.value.map(g => g.score).filter(s => s != null)
  return scores.length ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : '--'
})

const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('zh-CN') : ''

onMounted(async () => {
  try {
    const [c, a, ann, g] = await Promise.all([
      axios.get('/api/v1/courses/my'),
      axios.get('/api/v1/assignments/'),
      axios.get('/api/v1/announcements/'),
      axios.get('/api/v1/grades/'),
    ])
    courses.value = c.data
    assignments.value = a.data
    announcements.value = ann.data
    grades.value = g.data
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.page { padding: 32px; font-family: 'Inter', sans-serif; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 26px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
.stat-card {
  border-radius: 16px; padding: 20px; border: 1px solid;
  display: flex; flex-direction: column; gap: 8px;
}
.stat-card.indigo { background: rgba(99,102,241,0.08); border-color: rgba(99,102,241,0.2); }
.stat-card.amber { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.2); }
.stat-card.emerald { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); }
.stat-card.rose { background: rgba(244,63,94,0.08); border-color: rgba(244,63,94,0.2); }
.stat-icon { font-size: 22px; }
.stat-card.indigo .stat-icon { color: #818cf8; }
.stat-card.amber .stat-icon { color: #fbbf24; }
.stat-card.emerald .stat-icon { color: #34d399; }
.stat-card.rose .stat-icon { color: #fb7185; }
.stat-num { font-size: 32px; font-weight: 800; color: var(--text-main); line-height: 1; }
.stat-label { font-size: 13px; color: var(--text-secondary); }

.content-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.card { background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 16px; padding: 20px; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; color: #c7d2fe; margin-bottom: 16px; }

.empty { text-align: center; color: var(--text-secondary); padding: 20px; font-size: 14px; }
.empty a { color: #818cf8; }

.ann-item { display: flex; gap: 10px; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.ann-item:last-child { border-bottom: none; }
.ann-priority { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; white-space: nowrap; margin-top: 2px; }
.ann-priority.p0 { background: rgba(99,102,241,0.15); color: #818cf8; }
.ann-priority.p1 { background: rgba(245,158,11,0.15); color: #fbbf24; }
.ann-priority.p2 { background: rgba(239,68,68,0.15); color: #f87171; }
.ann-title { font-size: 14px; color: var(--text-main); font-weight: 500; }
.ann-time { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.course-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.course-item:last-child { border-bottom: none; }
.course-avatar { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, #6366f1, #7c3aed); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.course-name { font-size: 14px; color: var(--text-main); font-weight: 500; }
.course-teacher { font-size: 12px; color: var(--text-secondary); }

.assign-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.assign-item:last-child { border-bottom: none; }
.assign-name { flex: 1; font-size: 14px; color: var(--text-main); }
.assign-due { font-size: 12px; color: #f87171; }
.btn-sm { font-size: 12px; padding: 4px 10px; background: rgba(99,102,241,0.15); color: #818cf8; border-radius: 8px; text-decoration: none; white-space: nowrap; }
.btn-sm:hover { background: rgba(99,102,241,0.25); }
</style>
