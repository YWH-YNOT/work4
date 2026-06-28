<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">讨论区管理</h1>
        <p class="page-sub">课程讨论、答疑回复与师生互动记录</p>
      </div>
      <button @click="openCreate" class="create-btn"><span>+</span> 发起讨论</button>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <span>讨论帖</span>
        <strong>{{ discussions.length }}</strong>
      </div>
      <div class="summary-card">
        <span>回复数</span>
        <strong>{{ totalReplies }}</strong>
      </div>
      <div class="summary-card teacher">
        <span>教师发起</span>
        <strong>{{ teacherPosts }}</strong>
      </div>
      <div class="summary-card student">
        <span>学生发起</span>
        <strong>{{ studentPosts }}</strong>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-left">
        <span class="filter-label">课程范围</span>
        <select v-model="selectedCourse" @change="load" class="sel">
          <option value="">所有课程</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="filter-current">{{ selectedCourseName }}</div>
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
            <div class="disc-topline">
              <span :class="['role-badge', roleClass(d.author_role)]">{{ roleLabel(d) }}</span>
              <span class="disc-author">{{ d.author }}</span>
              <span class="disc-date">{{ fmt(d.created_at) }}</span>
            </div>
            <div class="disc-title">{{ d.title }}</div>
            <div class="disc-content">{{ d.content }}</div>
          </div>
          <div class="disc-meta">
            <span class="meta-chip"><b>{{ d.views }}</b> 浏览</span>
            <span class="meta-chip"><b>{{ d.reply_count }}</b> 回复</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子详情 & 回复 -->
    <div v-else class="detail-view">
      <button @click="activeDiscussion=null;load()" class="back-btn">← 返回列表</button>
      <div class="detail-card">
        <h2 class="detail-title">{{ activeDiscussion.title }}</h2>
        <div class="detail-meta">
          <span :class="['role-badge', roleClass(activeDiscussion.author_role)]">{{ roleLabel(activeDiscussion) }}</span>
          <span class="detail-author">{{ activeDiscussion.author }}</span>
          <span>{{ fmt(activeDiscussion.created_at) }}</span>
        </div>
        <div class="detail-content">{{ activeDiscussion.content }}</div>
        <div class="detail-footer">{{ activeDiscussion.views }} 次浏览</div>
      </div>

      <div class="comments-section">
        <div class="comments-headline">
          <div>
            <div class="comments-title">全部回复</div>
            <p>教师回复 {{ detailTeacherComments }} 条，学生回复 {{ detailStudentComments }} 条</p>
          </div>
          <strong>{{ activeDiscussion.comments?.length || 0 }}</strong>
        </div>
        <div v-if="!activeDiscussion.comments?.length" class="empty sm">暂无回复，率先发表看法</div>
        <div v-else class="comment-list">
          <div v-for="c in activeDiscussion.comments" :key="c.id" :class="['comment-item', roleClass(c.author_role)]">
            <div class="comment-head">
              <span :class="['role-badge', roleClass(c.author_role)]">{{ roleLabel(c) }}</span>
              <span class="comment-author">{{ c.author }}</span>
              <span class="comment-time">{{ fmt(c.created_at) }}</span>
            </div>
            <div class="comment-body">{{ c.content }}</div>
          </div>
        </div>
      </div>

      <!-- 回复框 -->
      <div class="reply-box">
        <div class="reply-title">教师回复</div>
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
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

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
const roleLabels: Record<string, string> = { teacher: '教师', student: '学生', admin: '管理员' }
const roleClass = (role?: string) => role && roleLabels[role] ? role : 'unknown'
const roleLabel = (item: any) => item?.author_role_label || roleLabels[item?.author_role] || '未知'
const totalReplies = computed(() => discussions.value.reduce((sum, item) => sum + Number(item.reply_count || 0), 0))
const teacherPosts = computed(() => discussions.value.filter(item => item.author_role === 'teacher').length)
const studentPosts = computed(() => discussions.value.filter(item => item.author_role === 'student').length)
const selectedCourseName = computed(() => {
  if (!selectedCourse.value) return '当前显示全部课程讨论'
  const course = courses.value.find(item => String(item.id) === String(selectedCourse.value))
  return course ? `当前课程：${course.name}` : '当前课程'
})
const detailTeacherComments = computed(() => (activeDiscussion.value?.comments || []).filter((item: any) => item.author_role === 'teacher').length)
const detailStudentComments = computed(() => (activeDiscussion.value?.comments || []).filter((item: any) => item.author_role === 'student').length)

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
  } catch(e: any) { ElMessage.error(e.response?.data?.detail || '回复失败') }
  finally { saving.value = false }
}

function openCreate() {
  createForm.value = { course_id: courses.value[0]?.id || 0, title: '', content: '' }
  showCreate.value = true
}

async function createDiscussion() {
  if (!createForm.value.title.trim() || !createForm.value.content.trim()) { ElMessage.warning('请填写标题和内容'); return }
  saving.value = true
  try {
    await axios.post('/api/v1/discussions/', createForm.value)
    showCreate.value = false
    await load()
  } catch(e: any) { ElMessage.error(e.response?.data?.detail || '发布失败') }
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
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 22px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { color: var(--text-secondary); font-size: 13px; margin: 6px 0 0; }
.create-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; border: none; border-radius: 10px; padding: 10px 18px; cursor: pointer; font-weight: 700; font-size: 14px; box-shadow: 0 12px 28px rgba(14,165,233,0.18); }
.create-btn span { font-size: 18px; line-height: 1; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-card { background: rgba(255,255,255,0.76); border: 1px solid #d8e7f8; border-radius: 12px; padding: 14px 16px; }
.summary-card span { display: block; color: var(--text-secondary); font-size: 12px; margin-bottom: 8px; }
.summary-card strong { color: var(--text-main); font-size: 24px; line-height: 1; }
.summary-card.teacher { border-color: rgba(16,185,129,0.28); background: rgba(16,185,129,0.06); }
.summary-card.student { border-color: rgba(59,130,246,0.28); background: rgba(59,130,246,0.055); }
.filter-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; background: rgba(255,255,255,0.76); border: 1px solid #d8e7f8; border-radius: 12px; padding: 12px 14px; }
.filter-left { display: flex; align-items: center; gap: 10px; }
.filter-label { color: var(--text-secondary); font-size: 13px; font-weight: 700; }
.filter-current { color: #7dd3fc; font-size: 13px; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(14,165,233,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; min-width: 180px; }
.empty { color: var(--text-secondary); text-align: center; padding: 40px; font-size: 15px; }
.empty.sm { padding: 20px; }
.discussion-list { display: flex; flex-direction: column; gap: 12px; }
.disc-card { background: rgba(255,255,255,0.82); border: 1px solid #d8e7f8; border-left: 3px solid #9fc8f1; border-radius: 14px; padding: 18px 20px; cursor: pointer; transition: all 0.18s; display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; box-shadow: 0 8px 18px rgba(15,47,100,0.04); }
.disc-card:hover { border-color: #9fc8f1; background: #f8fbff; transform: translateY(-1px); box-shadow: 0 12px 24px rgba(15,47,100,0.08); }
.disc-main { flex: 1; min-width: 0; }
.disc-topline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.disc-author { color: var(--text-main); font-size: 13px; font-weight: 700; }
.disc-date { color: var(--text-secondary); font-size: 12px; }
.disc-title { font-size: 15px; font-weight: 700; color: var(--text-main); margin-bottom: 6px; }
.disc-content { font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.disc-meta { display: grid; grid-template-columns: repeat(2, 72px); gap: 8px; flex-shrink: 0; }
.meta-chip { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 52px; border-radius: 10px; background: #eaf3ff; border: 1px solid #c8ddf4; font-size: 11px; color: #5b6f92; white-space: nowrap; }
.meta-chip b { color: #075da8; font-size: 18px; line-height: 1.1; }
.role-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 42px; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 800; line-height: 1.4; border: 1px solid #c8ddf4; color: #5b6f92; background: #f7fbff; }
.role-badge.teacher { color: #34d399; background: rgba(16,185,129,0.16); border-color: rgba(16,185,129,0.42); }
.role-badge.student { color: #93c5fd; background: rgba(59,130,246,0.14); border-color: rgba(59,130,246,0.38); }
.role-badge.admin { color: #fbbf24; background: rgba(245,158,11,0.14); border-color: rgba(245,158,11,0.38); }
/* Detail */
.detail-view { display: flex; flex-direction: column; gap: 20px; }
.back-btn { align-self: flex-start; background: #f7fbff; border: 1px solid #c8ddf4; color: #5b6f92; border-radius: 8px; padding: 7px 16px; cursor: pointer; font-size: 13px; transition: all 0.15s; }
.back-btn:hover { background: #eaf3ff; color: #075da8; }
.detail-card { background: rgba(255,255,255,0.82); border: 1px solid #d8e7f8; border-radius: 16px; padding: 24px; }
.detail-title { font-size: 20px; font-weight: 800; color: var(--text-main); margin: 0 0 14px; }
.detail-meta { display: flex; align-items: center; gap: 10px; color: var(--text-secondary); font-size: 12px; margin: -4px 0 16px; }
.detail-author { color: var(--text-main); font-weight: 700; }
.detail-content { font-size: 15px; color: var(--text-secondary); line-height: 1.8; white-space: pre-wrap; }
.detail-footer { margin-top: 14px; font-size: 12px; color: var(--text-secondary); }
.comments-section { background: rgba(255,255,255,0.78); border: 1px solid #d8e7f8; border-radius: 14px; padding: 20px; }
.comments-headline { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.comments-headline strong { display: inline-flex; align-items: center; justify-content: center; width: 42px; height: 42px; border-radius: 10px; color: var(--text-main); background: rgba(14,165,233,0.12); border: 1px solid rgba(14,165,233,0.22); }
.comments-headline p { margin: 4px 0 0; color: var(--text-secondary); font-size: 12px; }
.comments-title { font-size: 14px; font-weight: 800; color: var(--text-main); }
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-item { background: #f8fbff; border: 1px solid #d8e7f8; border-left: 3px solid #9fc8f1; border-radius: 10px; padding: 14px; }
.comment-item.teacher { border-left-color: #10b981; background: rgba(16,185,129,0.06); }
.comment-item.student { border-left-color: #3b82f6; background: rgba(59,130,246,0.05); }
.comment-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.comment-author { font-size: 13px; font-weight: 700; color: var(--text-main); }
.comment-body { font-size: 14px; color: var(--text-secondary); line-height: 1.7; }
.comment-time { font-size: 11px; color: var(--text-secondary); margin-left: auto; }
.reply-box { background: rgba(255,255,255,0.82); border: 1px solid #d8e7f8; border-radius: 14px; padding: 18px; }
.reply-title { color: var(--text-main); font-size: 14px; font-weight: 800; margin-bottom: 10px; }
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
@media (max-width: 900px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-bar, .disc-card { flex-direction: column; align-items: stretch; }
  .disc-meta { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
