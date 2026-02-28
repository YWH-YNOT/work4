<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">我的作业</h1>
    </div>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else>
      <div class="filter-bar">
        <button v-for="f in filters" :key="f.v" :class="['filter-btn', filter===f.v&&'active']" @click="filter=f.v">{{ f.l }}</button>
      </div>
      <div class="list">
        <div v-for="a in filteredItems" :key="a.id" class="assign-card">
          <div class="assign-info">
            <div class="assign-name">{{ a.title }}</div>
            <div class="assign-meta">
              <span class="badge" :class="a.type">{{ a.type === 'homework' ? '作业' : '报告' }}</span>
              <span v-if="a.due_date" class="due" :class="{ urgent: isUrgent(a.due_date) }">截止: {{ fmt(a.due_date) }}</span>
            </div>
          </div>
          <div class="assign-status">
            <span v-if="a.submitted" class="status submitted">
              {{ a.score != null ? `已批改: ${a.score}分` : '已提交' }}
            </span>
            <button v-else class="submit-btn" @click="openSubmit(a)">提交</button>
          </div>
        </div>
        <div v-if="filteredItems.length === 0" class="empty">暂无作业</div>
      </div>
    </div>

    <!-- Submit Dialog -->
    <el-dialog v-model="dialogVisible" title="提交作业" width="500px" :before-close="()=>dialogVisible=false" class="dark-dialog">
      <div class="dialog-inner">
        <label>作业内容</label>
        <textarea v-model="submitContent" placeholder="请填写作业内容或说明..." rows="6" class="dialog-textarea"></textarea>
        <div class="dialog-actions">
          <button @click="dialogVisible=false" class="cancel-btn">取消</button>
          <button @click="doSubmit" :disabled="submitting" class="confirm-btn">提交</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const assignments = ref<any[]>([])
const loading = ref(true)
const filter = ref('all')
const filters = [{v:'all',l:'全部'},{v:'pending',l:'待提交'},{v:'submitted',l:'已提交'}]
const filteredItems = computed(() => {
  if (filter.value === 'pending') return assignments.value.filter(a=>!a.submitted)
  if (filter.value === 'submitted') return assignments.value.filter(a=>a.submitted)
  return assignments.value
})

const dialogVisible = ref(false)
const currentId = ref<number|null>(null)
const submitContent = ref('')
const submitting = ref(false)

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')

// 截止日期是否紧急（距今 ≤ 3 天且未过期）
const isUrgent = (d: string) => {
  const diff = new Date(d).getTime() - Date.now()
  return diff > 0 && diff <= 3 * 24 * 60 * 60 * 1000
}

function openSubmit(a: any) { currentId.value = a.id; submitContent.value = ''; dialogVisible.value = true }

async function doSubmit() {
  if (!currentId.value) return
  submitting.value = true
  try {
    await axios.post(`/api/v1/assignments/${currentId.value}/submit`, { content: submitContent.value })
    await load()
    dialogVisible.value = false
  } catch(e:any) { alert(e.response?.data?.detail || '提交失败') }
  finally { submitting.value = false }
}

async function load() {
  const res = await axios.get('/api/v1/assignments/')
  assignments.value = res.data
}

onMounted(async () => { try { await load() } finally { loading.value = false } })
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.loading { color: var(--text-secondary); }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.filter-btn { padding: 6px 16px; border-radius: 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(99,102,241,0.2); color: var(--text-secondary); cursor: pointer; font-size: 13px; transition: all 0.18s; }
.filter-btn.active, .filter-btn:hover { background: rgba(99,102,241,0.12); border-color: #6366f1; color: #818cf8; }
.list { display: flex; flex-direction: column; gap: 12px; }
.assign-card { display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 14px; padding: 16px 20px; }
.assign-name { font-size: 15px; font-weight: 600; color: var(--text-main); }
.assign-meta { display: flex; gap: 10px; align-items: center; margin-top: 6px; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 10px; }
.badge.homework { background: rgba(99,102,241,0.15); color: #818cf8; }
.badge.report { background: rgba(245,158,11,0.15); color: #fbbf24; }
.due { font-size: 12px; color: var(--text-secondary); }
.due.urgent { color: #f87171; font-weight: 600; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.status.submitted { color: #34d399; font-size: 14px; font-weight: 600; }
.submit-btn { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border: none; border-radius: 10px; padding: 8px 18px; cursor: pointer; font-weight: 600; }
.empty { text-align: center; color: var(--text-secondary); padding: 30px; }
.dialog-inner { display: flex; flex-direction: column; gap: 12px; }
.dialog-inner label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.dialog-textarea { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 12px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #6366f1, #7c3aed); border: none; color: white; cursor: pointer; font-weight: 600; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
