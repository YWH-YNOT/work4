<template>
  <div class="page">
    <div class="page-header-row">
      <h1 class="page-title">发布公告</h1>
      <button @click="showCreate=true" class="create-btn"><el-icon><Plus /></el-icon> 新公告</button>
    </div>
    <div class="list">
      <div v-for="a in announcements" :key="a.id" class="ann-card">
        <div class="priority-badge" :class="`p${a.priority}`">{{ ['普通','重要','紧急'][a.priority] }}</div>
        <div class="ann-body">
          <div class="ann-title">{{ a.title }}</div>
          <div class="ann-content">{{ a.content }}</div>
          <div class="ann-time">{{ fmt(a.created_at) }}</div>
        </div>
        <button @click="del(a.id)" class="del-btn"><el-icon><Delete /></el-icon></button>
      </div>
      <div v-if="announcements.length===0" class="empty">暂无公告</div>
    </div>
    <el-dialog v-model="showCreate" title="发布新公告" width="480px">
      <div class="dialog-form">
        <label>标题</label><input v-model="newA.title" class="inp" placeholder="公告标题"/>
        <label>内容</label><textarea v-model="newA.content" class="ta" rows="5"></textarea>
        <label>优先级</label>
        <select v-model="newA.priority" class="inp-sel"><option :value="0">普通</option><option :value="1">重要</option><option :value="2">紧急</option></select>
        <div class="dialog-actions">
          <button @click="showCreate=false" class="cancel-btn">取消</button>
          <button @click="create" class="confirm-btn">发布</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
const announcements = ref<any[]>([])
const showCreate = ref(false)
const newA = ref({ title: '', content: '', priority: 0 })
const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
async function load() {
  try { const r = await axios.get('/api/v1/announcements/'); announcements.value = r.data } catch {}
}
async function create() {
  if (!newA.value.title.trim()) { ElMessage.warning('请输入公告标题'); return }
  try {
    await axios.post('/api/v1/announcements/', newA.value)
    showCreate.value = false
    newA.value = { title: '', content: '', priority: 0 }
    ElMessage.success('公告发布成功')
    await load()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '发布失败') }
}
async function del(id: number) {
  try {
    await axios.delete(`/api/v1/announcements/${id}`)
    ElMessage.success('公告已删除')
    await load()
  } catch (e: any) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
onMounted(load)
</script>

<style scoped>
.page { padding: 32px; }
.page-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.create-btn { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; border-radius: 12px; padding: 10px 20px; cursor: pointer; font-weight: 600; }
.list { display: flex; flex-direction: column; gap: 12px; }
.ann-card { display: flex; gap: 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(16,185,129,0.12); border-radius: 14px; padding: 16px 20px; align-items: flex-start; }
.priority-badge { font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 20px; white-space: nowrap; }
.p0 { background: rgba(99,102,241,0.15); color: #818cf8; }
.p1 { background: rgba(245,158,11,0.15); color: #fbbf24; }
.p2 { background: rgba(239,68,68,0.15); color: #f87171; }
.ann-body { flex: 1; }
.ann-title { font-size: 15px; font-weight: 700; color: var(--text-main); }
.ann-content { font-size: 14px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
.ann-time { font-size: 12px; color: var(--text-secondary); margin-top: 6px; }
.del-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 4px; font-size: 16px; }
.del-btn:hover { color: #f87171; }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp, .inp-sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; }
.ta { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #059669, #10b981); border: none; color: white; cursor: pointer; font-weight: 600; }
</style>
