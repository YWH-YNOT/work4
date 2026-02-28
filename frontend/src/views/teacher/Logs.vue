<template>
  <div class="page">
    <div class="page-header"><h1 class="page-title">对话日志</h1></div>
    <div class="filter-bar">
      <input v-model="keyword" placeholder="搜索关键词..." class="inp" @input="load"/>
      <input v-model="studentId" placeholder="学生ID" class="inp small" @input="load" type="number"/>
    </div>
    <div class="log-list">
      <div v-for="l in logs" :key="l.id" class="log-item" :class="l.role">
        <div class="log-header">
          <span class="log-user">{{ l.user }}</span>
          <span class="log-role">{{ l.role==='user'?'问':'答' }}</span>
          <span class="log-course" v-if="l.course">{{ l.course }}</span>
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
const page = ref(1)
const pageSize = 20
const keyword = ref('')
const studentId = ref('')
const fmt = (d: string) => new Date(d).toLocaleString('zh-CN')
async function load() {
  let url = `/api/v1/logs/?page=${page.value}&page_size=${pageSize}`
  if (keyword.value) url += `&keyword=${keyword.value}`
  if (studentId.value) url += `&student_id=${studentId.value}`
  try { const r = await axios.get(url); logs.value = r.data.items; total.value = r.data.total } catch {}
}
function prev() { if (page.value > 1) { page.value--; load() } }
function next() { if (page.value * pageSize < total.value) { page.value++; load() } }
onMounted(load)
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; }
.inp { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.inp.small { flex: 0 0 120px; }
.log-list { display: flex; flex-direction: column; gap: 8px; }
.log-item { padding: 12px 16px; border-radius: 12px; border: 1px solid; }
.log-item.user { background: rgba(99,102,241,0.06); border-color: rgba(99,102,241,0.15); }
.log-item.assistant { background: rgba(16,185,129,0.04); border-color: rgba(16,185,129,0.12); }
.log-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 12px; }
.log-user { font-weight: 700; color: #818cf8; }
.log-role { background: rgba(99,102,241,0.15); color: #818cf8; padding: 2px 8px; border-radius: 6px; }
.log-item.assistant .log-role { background: rgba(16,185,129,0.15); color: #34d399; }
.log-item.assistant .log-user { color: #34d399; }
.log-course { color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 6px; }
.log-time { color: var(--text-secondary); margin-left: auto; }
.log-content { font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-height: 80px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; }
.pagination { display: flex; align-items: center; gap: 16px; justify-content: center; margin-top: 20px; }
.page-btn { padding: 6px 16px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.page-btn:hover:not(:disabled) { background: rgba(16,185,129,0.1); color: #34d399; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 14px; color: var(--text-secondary); }
</style>
