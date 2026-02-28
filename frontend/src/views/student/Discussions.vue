<template>
  <div class="page">
    <div class="page-header-row">
      <div>
        <h1 class="page-title">讨论区</h1>
        <p class="page-sub">交流分享，共同进步</p>
      </div>
      <button @click="showCreate=true" class="create-btn"><el-icon><Plus /></el-icon> 发帖</button>
    </div>

    <div class="posts-list">
      <div v-for="d in discussions" :key="d.id" class="post-card" @click="openPost(d)">
        <div class="post-info">
          <div class="post-title">{{ d.title }}</div>
          <div class="post-meta">{{ d.author }} · {{ fmt(d.created_at) }}</div>
        </div>
        <div class="post-stats">
          <span><el-icon><View /></el-icon> {{ d.views }}</span>
          <span><el-icon><ChatRound /></el-icon> {{ d.reply_count }}</span>
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
        <div class="post-content">{{ currentPost.content }}</div>
        <div class="comments-title">评论 ({{ currentPost.comments?.length || 0 }})</div>
        <div v-for="c in currentPost.comments" :key="c.id" class="comment-item">
          <strong class="comment-author">{{ c.author }}</strong>：{{ c.content }}
          <div class="comment-time">{{ fmt(c.created_at) }}</div>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'

const discussions = ref<any[]>([])
const courses = ref<any[]>([])
const showCreate = ref(false)
const showDetail = ref(false)
const currentPost = ref<any>(null)
const replyContent = ref('')
const newPost = ref({ course_id: 0, title: '', content: '' })
const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')

async function load() {
  const [d, c] = await Promise.all([axios.get('/api/v1/discussions/'), axios.get('/api/v1/courses/my')])
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
.page-header-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.create-btn { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border: none; border-radius: 12px; padding: 10px 20px; cursor: pointer; font-weight: 600; }
.posts-list { display: flex; flex-direction: column; gap: 10px; }
.post-card { display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 14px; padding: 16px 20px; cursor: pointer; transition: all 0.18s; }
.post-card:hover { background: rgba(99,102,241,0.06); border-color: rgba(99,102,241,0.3); }
.post-title { font-size: 15px; font-weight: 600; color: var(--text-main); }
.post-meta { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.post-stats { display: flex; gap: 14px; align-items: center; color: var(--text-secondary); font-size: 13px; }
.post-stats span { display: flex; align-items: center; gap: 4px; }
.empty { text-align: center; color: var(--text-secondary); padding: 40px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.sel, .inp { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; }
.ta { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions, .reply-area { display: flex; gap: 10px; justify-content: flex-end; margin-top: 8px; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #6366f1, #7c3aed); border: none; color: white; cursor: pointer; font-weight: 600; }
.post-content { color: var(--text-secondary); font-size: 14px; line-height: 1.7; margin-bottom: 20px; white-space: pre-wrap; }
.comments-title { font-size: 14px; font-weight: 700; color: #c7d2fe; margin-bottom: 12px; }
.comment-item { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.comment-author { color: #818cf8; font-size: 13px; }
.comment-time { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.reply-area input { flex: 1; }
</style>
