<template>
  <div class="page">
    <div class="page-header-row">
      <div>
        <h1 class="page-title">课程讨论</h1>
        <p class="page-sub">课程答疑、同学交流与教师回复</p>
      </div>
      <button @click="showCreate=true" class="create-btn"><span>+</span> 发帖</button>
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

    <div class="posts-list">
      <div v-for="d in discussions" :key="d.id" :class="['post-card', roleClass(d.author_role)]" @click="openPost(d)">
        <div class="post-info">
          <div class="post-title">{{ d.title }}</div>
          <div class="post-meta">
            <span :class="['role-badge', roleClass(d.author_role)]">{{ roleLabel(d) }}</span>
            <span>{{ d.author }}</span>
            <span>{{ fmt(d.created_at) }}</span>
          </div>
        </div>
        <div class="post-stats">
          <span><strong>{{ d.views }}</strong> 浏览</span>
          <span><strong>{{ d.reply_count }}</strong> 回复</span>
        </div>
      </div>
      <div v-if="discussions.length===0" class="empty">暂无讨论，来发起第一个吧！</div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreate" title="发起讨论" width="500px">
      <div class="dialog-form">
        <label>课程</label>
        <select v-model="newPost.course_id" class="sel">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <label>标题</label>
        <input v-model="newPost.title" class="inp" placeholder="帖子标题"/>
        <label>内容</label>
        <textarea v-model="newPost.content" class="ta" rows="5" placeholder="讨论内容..."></textarea>
        <div class="dialog-actions">
          <button @click="showCreate=false" class="cancel-btn">取消</button>
          <button @click="createPost" class="confirm-btn">发布</button>
        </div>
      </div>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetail" :title="currentPost?.title" width="600px">
      <div class="post-detail" v-if="currentPost">
        <div class="detail-meta">
          <span :class="['role-badge', roleClass(currentPost.author_role)]">{{ roleLabel(currentPost) }}</span>
          <span class="detail-author">{{ currentPost.author }}</span>
          <span>{{ fmt(currentPost.created_at) }}</span>
        </div>
        <div class="post-content">{{ currentPost.content }}</div>
        <div class="comments-title">评论 ({{ currentPost.comments?.length || 0 }})</div>
        <div v-for="c in currentPost.comments" :key="c.id" :class="['comment-item', roleClass(c.author_role)]">
          <div class="comment-head">
            <span :class="['role-badge', roleClass(c.author_role)]">{{ roleLabel(c) }}</span>
            <strong class="comment-author">{{ c.author }}</strong>
            <span class="comment-time">{{ fmt(c.created_at) }}</span>
          </div>
          <div class="comment-body">{{ c.content }}</div>
        </div>
        <div class="reply-area">
          <input v-model="replyContent" class="inp" placeholder="写下你的评论..."/>
          <button @click="addComment" class="confirm-btn">回复</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const discussions = ref<any[]>([])
const courses = ref<any[]>([])
const showCreate = ref(false)
const showDetail = ref(false)
const currentPost = ref<any>(null)
const replyContent = ref('')
const selectedCourse = ref<number|''>('')
const newPost = ref({ course_id: 0, title: '', content: '' })
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

async function load() {
  const params = selectedCourse.value ? { course_id: selectedCourse.value } : {}
  const [d, c] = await Promise.all([
    axios.get('/api/v1/discussions/', { params }),
    axios.get('/api/v1/courses/my')
  ])
  discussions.value = d.data; courses.value = c.data
  if (c.data.length && !newPost.value.course_id) newPost.value.course_id = c.data[0].id
}

async function createPost() {
  try { await axios.post('/api/v1/discussions/', newPost.value); showCreate.value = false; await load() } catch {}
}

async function openPost(d: any) {
  const res = await axios.get(`/api/v1/discussions/${d.id}`)
  currentPost.value = res.data; showDetail.value = true
}

async function addComment() {
  if (!replyContent.value || !currentPost.value) return
  try {
    await axios.post(`/api/v1/discussions/${currentPost.value.id}/comments`, { content: replyContent.value })
    replyContent.value = ''; await openPost(currentPost.value)
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.page { padding: 32px; }
.page-header-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 22px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.create-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #0b63b6, #0a88df); color: white; border: none; border-radius: 10px; padding: 10px 18px; cursor: pointer; font-weight: 700; box-shadow: 0 12px 28px rgba(11,99,182,0.18); }
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
.filter-current { color: #0a88df; font-size: 13px; }
.posts-list { display: flex; flex-direction: column; gap: 12px; }
.post-card { display: flex; justify-content: space-between; align-items: center; gap: 18px; background: rgba(255,255,255,0.82); border: 1px solid #d8e7f8; border-left: 3px solid #9fc8f1; border-radius: 14px; padding: 17px 20px; cursor: pointer; transition: all 0.18s; box-shadow: 0 8px 18px rgba(15,47,100,0.04); }
.post-card.teacher { border-left-color: #10b981; }
.post-card.student { border-left-color: #3b82f6; }
.post-card:hover { background: #f8fbff; border-color: #9fc8f1; box-shadow: 0 12px 24px rgba(15,47,100,0.08); }
.post-info { min-width: 0; }
.post-title { font-size: 15px; font-weight: 600; color: var(--text-main); }
.post-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 12px; color: var(--text-secondary); margin-top: 6px; }
.post-stats { display: grid; grid-template-columns: repeat(2, 72px); gap: 8px; align-items: center; color: var(--text-secondary); font-size: 12px; flex-shrink: 0; }
.post-stats span { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 50px; border-radius: 10px; background: #eaf3ff; border: 1px solid #c8ddf4; color: #5b6f92; }
.post-stats strong { color: #075da8; font-size: 17px; line-height: 1.1; }
.role-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 42px; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 800; line-height: 1.4; border: 1px solid #c8ddf4; color: #5b6f92; background: #f7fbff; }
.role-badge.teacher { color: #34d399; background: rgba(16,185,129,0.16); border-color: rgba(16,185,129,0.42); }
.role-badge.student { color: #93c5fd; background: rgba(59,130,246,0.14); border-color: rgba(59,130,246,0.38); }
.role-badge.admin { color: #fbbf24; background: rgba(245,158,11,0.14); border-color: rgba(245,158,11,0.38); }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.sel, .inp { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; }
.filter-bar .sel { width: auto; min-width: 180px; padding: 8px 14px; }
.ta { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions, .reply-area { display: flex; gap: 10px; justify-content: flex-end; margin-top: 8px; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #6366f1, #7c3aed); border: none; color: white; cursor: pointer; font-weight: 600; }
.detail-meta { display: flex; align-items: center; gap: 10px; color: var(--text-secondary); font-size: 12px; margin-bottom: 14px; }
.detail-author { color: var(--text-main); font-weight: 700; }
.post-content { color: var(--text-secondary); font-size: 14px; line-height: 1.7; margin-bottom: 20px; white-space: pre-wrap; }
.comments-title { font-size: 14px; font-weight: 700; color: #c7d2fe; margin-bottom: 12px; }
.comment-item { padding: 12px; border: 1px solid #d8e7f8; border-left: 3px solid #9fc8f1; border-radius: 10px; margin-bottom: 10px; background: #f8fbff; }
.comment-item.teacher { border-left-color: #10b981; background: rgba(16,185,129,0.06); }
.comment-item.student { border-left-color: #3b82f6; background: rgba(59,130,246,0.05); }
.comment-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.comment-author { color: var(--text-main); font-size: 13px; }
.comment-body { color: var(--text-secondary); font-size: 14px; line-height: 1.7; }
.comment-time { font-size: 11px; color: var(--text-secondary); margin-left: auto; }
.reply-area input { flex: 1; }
@media (max-width: 900px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-bar, .post-card { flex-direction: column; align-items: stretch; }
  .post-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
