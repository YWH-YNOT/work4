<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">作业管理</h1>
    </div>
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="load" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <button @click="showCreate=true" class="create-btn"><el-icon><Plus /></el-icon> 布置作业</button>
    </div>
    <table class="table">
      <thead><tr><th>作业名</th><th>课程</th><th>类型</th><th>截止日期</th><th>提交数</th></tr></thead>
      <tbody>
        <tr v-for="a in assignments" :key="a.id">
          <td class="name-cell">{{ a.title }}</td>
          <td class="course-cell">{{ courseMap[a.course_id] || '—' }}</td>
          <td><span class="badge" :class="a.type">{{ a.type==='homework'?'作业':'报告' }}</span></td>
          <td>{{ a.due_date ? fmt(a.due_date) : '无截止' }}</td>
          <td><span class="count-badge">{{ a.submissions_count ?? 0 }} 份</span></td>
        </tr>
        <tr v-if="assignments.length===0"><td colspan="5" class="empty-cell">暂无作业</td></tr>
      </tbody>
    </table>
    <el-dialog v-model="showCreate" title="布置新作业" width="480px">
      <div class="dialog-form">
        <label>所属课程</label>
        <select v-model="newA.course_id" class="inp-sel"><option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option></select>
        <label>作业名</label><input v-model="newA.title" class="inp" placeholder="作业标题"/>
        <label>类型</label>
        <select v-model="newA.type" class="inp-sel"><option value="homework">普通作业</option><option value="report">研究报告</option></select>
        <label>说明</label><textarea v-model="newA.description" class="ta" rows="3" placeholder="作业说明..."></textarea>
        <div class="dialog-actions">
          <button @click="showCreate=false" class="cancel-btn">取消</button>
          <button @click="createA" class="confirm-btn">发布</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
const assignments = ref<any[]>([])
const courses = ref<any[]>([])
const selectedCourse = ref('')
const showCreate = ref(false)
const newA = ref({ course_id: 0, title: '', type: 'homework', description: '' })
const courseMap = computed(() => Object.fromEntries(courses.value.map((c: any) => [c.id, c.name])))
const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
async function load() {
  let url = '/api/v1/assignments/'
  if (selectedCourse.value) url += `?course_id=${selectedCourse.value}`
  const r = await axios.get(url); assignments.value = r.data
}
async function createA() {
  try { await axios.post('/api/v1/assignments/', newA.value); showCreate.value = false; await load() } catch {}
}
onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my'); courses.value = c.data
  if (c.data.length) newA.value.course_id = c.data[0].id
  await load()
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.create-btn { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; border-radius: 10px; padding: 8px 18px; cursor: pointer; font-weight: 600; margin-left: auto; }
.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; padding: 12px 14px; font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; border-bottom: 1px solid rgba(16,185,129,0.1); }
.table td { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; color: var(--text-secondary); }
.name-cell { color: var(--text-main); font-weight: 500; }
.badge { font-size: 12px; padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.badge.homework { background: rgba(99,102,241,0.15); color: #818cf8; }
.badge.report { background: rgba(245,158,11,0.15); color: #fbbf24; }
.count-badge { font-size: 12px; color: #34d399; background: rgba(52,211,153,0.1); padding: 2px 10px; border-radius: 8px; font-weight: 600; }
.course-cell { font-size: 13px; color: #818cf8; }
.empty-cell { text-align: center; color: var(--text-secondary); padding: 30px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp, .inp-sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; }
.ta { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #059669, #10b981); border: none; color: white; cursor: pointer; font-weight: 600; }
</style>
