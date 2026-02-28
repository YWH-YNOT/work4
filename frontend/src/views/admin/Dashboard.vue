<template>
  <div class="page">
    <div class="page-header-row">
      <h1 class="page-title">系统概览</h1>
    </div>
    <div class="stats-grid">
      <div class="stat-card amber">
        <div class="stat-icon"><el-icon><User /></el-icon></div>
        <div class="stat-num">{{ stats.total_users }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat-card indigo">
        <div class="stat-icon"><el-icon><Reading /></el-icon></div>
        <div class="stat-num">{{ stats.students }}</div>
        <div class="stat-label">学生人数</div>
      </div>
      <div class="stat-card emerald">
        <div class="stat-icon"><el-icon><Sugar /></el-icon></div>
        <div class="stat-num">{{ stats.teachers }}</div>
        <div class="stat-label">教师人数</div>
      </div>
      <div class="stat-card rose">
        <div class="stat-icon"><el-icon><Collection /></el-icon></div>
        <div class="stat-num">{{ stats.total_courses }}</div>
        <div class="stat-label">课程总数</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-icon"><el-icon><Document /></el-icon></div>
        <div class="stat-num">{{ stats.total_assignments }}</div>
        <div class="stat-label">作业总数</div>
      </div>
      <div class="stat-card teal">
        <div class="stat-icon"><el-icon><ChatDotRound /></el-icon></div>
        <div class="stat-num">{{ stats.total_chat_logs }}</div>
        <div class="stat-label">AI 对话总数</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stats = ref({ total_users:0, students:0, teachers:0, total_courses:0, total_assignments:0, total_chat_logs:0 })
onMounted(async () => { try { const r = await axios.get('/api/v1/admin/stats'); stats.value = r.data } catch {} })
</script>

<style scoped>
.page { padding: 32px; }
.page-header-row { margin-bottom: 28px; }
.page-title { font-size: 26px; font-weight: 800; color: var(--text-main); margin: 0; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.stat-card { border-radius: 18px; padding: 28px; border: 1px solid; display: flex; flex-direction: column; gap: 10px; }
.stat-card.amber { background: rgba(245,158,11,0.07); border-color: rgba(245,158,11,0.2); }
.stat-card.indigo { background: rgba(99,102,241,0.07); border-color: rgba(99,102,241,0.2); }
.stat-card.emerald { background: rgba(16,185,129,0.07); border-color: rgba(16,185,129,0.2); }
.stat-card.rose { background: rgba(244,63,94,0.07); border-color: rgba(244,63,94,0.2); }
.stat-card.purple { background: rgba(168,85,247,0.07); border-color: rgba(168,85,247,0.2); }
.stat-card.teal { background: rgba(20,184,166,0.07); border-color: rgba(20,184,166,0.2); }
.stat-icon { font-size: 28px; }
.stat-card.amber .stat-icon { color: #fbbf24; }
.stat-card.indigo .stat-icon { color: #818cf8; }
.stat-card.emerald .stat-icon { color: #34d399; }
.stat-card.rose .stat-icon { color: #fb7185; }
.stat-card.purple .stat-icon { color: #c084fc; }
.stat-card.teal .stat-icon { color: #2dd4bf; }
.stat-num { font-size: 42px; font-weight: 900; color: #f1f5f9; line-height: 1; }
.stat-label { font-size: 14px; color: var(--text-secondary); }
</style>
