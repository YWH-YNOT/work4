<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">我的成绩</h1>
    </div>
    <div v-if="grades.length === 0" class="empty">暂无成绩记录</div>
    <div v-else class="grades-grid">
      <div v-for="g in grades" :key="g.id" class="grade-card">
        <div class="course-name">{{ g.course_name }}</div>
        <div class="score" :class="scoreClass(g.score)">{{ g.score }}</div>
        <div class="grade-label">{{ scoreLabel(g.score) }}</div>
        <div v-if="g.comment" class="comment">{{ g.comment }}</div>
        <div class="date">{{ fmt(g.created_at) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const grades = ref<any[]>([])

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')

const scoreClass = (s: number) => {
  if (s >= 90) return 'excellent'
  if (s >= 75) return 'good'
  if (s >= 60) return 'pass'
  return 'fail'
}
const scoreLabel = (s: number) => {
  if (s >= 90) return '优秀'
  if (s >= 75) return '良好'
  if (s >= 60) return '及格'
  return '不及格'
}

onMounted(async () => { try { const r = await axios.get('/api/v1/grades/'); grades.value = r.data } catch {} })
</script>

<style scoped>
.page { padding: 32px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0 0 24px; }
.empty { text-align: center; color: var(--text-secondary); padding: 60px; font-size: 15px; }
.grades-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.grade-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 16px; padding: 20px; text-align: center; }
.course-name { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.score { font-size: 48px; font-weight: 900; line-height: 1; margin-bottom: 6px; }
.score.excellent { color: #34d399; }
.score.good { color: #818cf8; }
.score.pass { color: #fbbf24; }
.score.fail { color: #f87171; }
.grade-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
.comment { font-size: 12px; color: var(--text-secondary); font-style: italic; margin-bottom: 8px; }
.date { font-size: 11px; color: var(--text-secondary); }
</style>
