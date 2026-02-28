<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">讨论区管理</h1>
      <button @click="openCreate" class="create-btn">＋ 发起讨论</button>
    </div>

    <!-- 课程筛选 -->
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="load" class="sel">
        <option value="">所有课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <!-- 讨论列表 / 帖子详情 -->
    <div v-if="!activeDiscussion">
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="discussions.length===0" class="empty">暂无讨论帖，点击发起讨论</div>
      <div v-else class="discussion-list">
        <div
          v-for="d in discussions" :key="d.id"
          class="disc-card"
          @click="openDetail(d)"
        >
          <div class="disc-main">
            <div class="disc-title">{{ d.title }}</div>
            <div class="disc-content">{{ d.content }}</div>
          </div>
          <div class="disc-meta">
            <span class="meta-chip">👁 {{ d.views }}</span>
            <span class="meta-chip">💬 {{ d.reply_count }}</span>
            <span class="meta-author">{{ d.author }}</span>
            <span class="meta-date">{{ fmt(d.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子详情 & 回复 -->
    <div v-else class="detail-view">
      <button @click="activeDiscussion=null;load()" class="back-btn">← 返回列表</button>
      <div class="detail-card">
        <h2 class="detail-title">{{ activeDiscussion.title }}</h2>
        <div class="detail-content">{{ activeDiscussion.content }}</div>
        <div class="detail-footer">👁 {{ activeDiscussion.views }} 次浏览</div>
      </div>

      <div class="comments-section">
        <div class="comments-title">全部回复（{{ activeDiscussion.comments?.length || 0 }}）</div>
        <div v-if="!activeDiscussion.comments?.length" class="empty sm">暂无回复，率先发表看法</div>
        <div v-else class="comment-list">
          <div v-for="c in activeDiscussion.comments" :key="c.id" class="comment-item">
            <div class="comment-author">{{ c.author }}</div>
            <div class="comment-body">{{ c.content }}</div>
            <div class="comment-time">{{ fmt(c.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- 回复框 -->
      <div class="reply-box">
        <textarea v-model="replyContent" class="reply-ta" rows="4" placeholder="作为老师发表你的意见..."></textarea>
        <div class="reply-actions">
          <button @click="postReply" :disabled="!replyContent.trim()||saving" class="reply-btn">
            {{ saving ? '发送中...' : '发表回复' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 新建讨论对话框 -->
    <el-dialog v-model="showCreate" title="发起讨论" width="520px">
      <div class="dialog-form">
        <label>所属课程</label>
        <select v-model="createForm.course_id" class="inp-sel">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label>讨论标题</label>
        <input v-model="createForm.title" class="inp" placeholder="简明概括讨论主题..."/>
        <label>内容</label>
        <textarea v-model="createForm.content" class="ta" rows="5" placeholder="详细描述..."></textarea>
        <div class="dialog-actions">
          <button @click="showCreate=false" class="cancel-btn">取消</button>
          <button @click="createDiscussion" :disabled="saving" class="confirm-btn">发布</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const courses = ref<any[]>([])
const discussions = ref<any[]>([])
const activeDiscussion = ref<any>(null)
const selectedCourse = ref<number|''>('')
const loading = ref(false)
const saving = ref(false)
const showCreate = ref(false)
const replyContent = ref('')
const createForm = ref({ course_id: 0, title: '', content: '' })

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')

async function load() {
  loading.value = true
  try {
    let url = '/api/v1/discussions/'
    if (selectedCourse.value) url += `?course_id=${selectedCourse.value}`
    const r = await axios.get(url)
    discussions.value = r.data
  } finally { loading.value = false }
}

async function openDetail(d: any) {
  try {
    const r = await axios.get(`/api/v1/discussions/${d.id}`)
    activeDiscussion.value = r.data
    replyContent.value = ''
  } catch {}
}

async function postReply() {
  if (!replyContent.value.trim() || !activeDiscussion.value) return
  saving.value = true
  try {
    await axios.post(`/api/v1/discussions/${activeDiscussion.value.id}/comments`, { content: replyContent.value })
    replyContent.value = ''
    const r = await axios.get(`/api/v1/discussions/${activeDiscussion.value.id}`)
    activeDiscussion.value = r.data
  } catch(e: any) { alert(e.response?.data?.detail || '回复失败') }
  finally { saving.value = false }
}

function openCreate() {
  createForm.value = { course_id: courses.value[0]?.id || 0, title: '', content: '' }
  showCreate.value = true
}

async function createDiscussion() {
  if (!createForm.value.title.trim() || !createForm.value.content.trim()) { alert('请填写标题和内容'); return }
  saving.value = true
  try {
    await axios.post('/api/v1/discussions/', createForm.value)
    showCreate.value = false
    await load()
  } catch(e: any) { alert(e.response?.data?.detail || '发布失败') }
  finally { saving.value = false }
}

onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my')
  courses.value = c.data
  if (c.data.length) createForm.value.course_id = c.data[0].id
  await load()
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.create-btn { background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; border: none; border-radius: 10px; padding: 9px 20px; cursor: pointer; font-weight: 600; font-size: 14px; }
.filter-bar { margin-bottom: 20px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(14,165,233,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.empty { color: var(--text-secondary); text-align: center; padding: 40px; font-size: 15px; }
.empty.sm { padding: 20px; }
.discussion-list { display: flex; flex-direction: column; gap: 10px; }
.disc-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(14,165,233,0.1); border-radius: 14px; padding: 18px 20px; cursor: pointer; transition: all 0.18s; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.disc-card:hover { border-color: rgba(14,165,233,0.3); background: rgba(14,165,233,0.04); transform: translateY(-1px); }
.disc-main { flex: 1; min-width: 0; }
.disc-title { font-size: 15px; font-weight: 700; color: var(--text-main); margin-bottom: 6px; }
.disc-content { font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.disc-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.meta-chip { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.meta-author { font-size: 12px; font-weight: 600; color: #38bdf8; }
.meta-date { font-size: 11px; color: var(--text-secondary); }
/* Detail */
.detail-view { display: flex; flex-direction: column; gap: 20px; }
.back-btn { align-self: flex-start; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); border-radius: 8px; padding: 7px 16px; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.back-btn:hover { background: rgba(255,255,255,0.1); color: var(--text-main); }
.detail-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(14,165,233,0.15); border-radius: 16px; padding: 24px; }
.detail-title { font-size: 20px; font-weight: 800; color: var(--text-main); margin: 0 0 14px; }
.detail-content { font-size: 15px; color: var(--text-secondary); line-height: 1.8; white-space: pre-wrap; }
.detail-footer { margin-top: 14px; font-size: 12px; color: var(--text-secondary); }
.comments-section { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 20px; }
.comments-title { font-size: 14px; font-weight: 700; color: var(--text-secondary); margin-bottom: 14px; }
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-item { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 14px; }
.comment-author { font-size: 13px; font-weight: 700; color: #38bdf8; margin-bottom: 6px; }
.comment-body { font-size: 14px; color: var(--text-secondary); line-height: 1.7; }
.comment-time { font-size: 11px; color: var(--text-secondary); margin-top: 6px; }
.reply-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(14,165,233,0.12); border-radius: 14px; padding: 18px; }
.reply-ta { width: 100%; box-sizing: border-box; background: rgba(255,255,255,0.06); border: 1px solid rgba(14,165,233,0.2); border-radius: 10px; padding: 12px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; }
.reply-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
.reply-btn { background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; border: none; border-radius: 10px; padding: 9px 22px; cursor: pointer; font-weight: 600; font-size: 14px; }
.reply-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp, .inp-sel { background: rgba(255,255,255,0.06); border: 1px solid rgba(14,165,233,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; box-sizing: border-box; }
.ta { background: rgba(255,255,255,0.06); border: 1px solid rgba(14,165,233,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; box-sizing: border-box; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #0ea5e9, #6366f1); border: none; color: white; cursor: pointer; font-weight: 600; }
</style>
