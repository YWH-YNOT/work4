<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">AI 助学</h1>
        <p class="page-sub">{{ activeCourse ? `当前课程：${activeCourse.name}` : '默认展示全部课程对话记录，选择课程后开始新的课程问答。' }}</p>
      </div>
      <div class="header-actions">
        <select v-model.number="activeCourseId" @change="onCourseChanged" class="course-select">
          <option :value="0">全部课程历史</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <button class="new-chat-btn" @click="startNewConversation()" :disabled="!activeCourseId">新建对话</button>
      </div>
    </div>

    <div class="chat-shell">
      <aside class="history-panel">
        <div class="history-head">
          <strong>对话记录</strong>
          <span>{{ conversations.length }} 条</span>
        </div>
        <div v-if="historyError" class="history-empty error">{{ historyError }}</div>
        <div v-else-if="conversations.length === 0" class="history-empty">暂无历史记录</div>
        <button
          v-for="item in conversations"
          :key="item.conversation_id"
          :class="['history-item', item.conversation_id === conversationId && 'active']"
          @click="openConversation(item)"
        >
          <strong>{{ item.title }}</strong>
          <span>{{ item.course_name }}</span>
          <em>{{ item.message_count }} 条 · {{ item.last_at ? fmtTime(item.last_at) : '--' }}</em>
        </button>
      </aside>

      <section class="chat-area">
        <div class="chat-header">
          <div>
            <strong>{{ activeCourse?.name || '选择课程开始问答' }}</strong>
            <span>{{ activeCourse ? '课程问答记录会自动保存' : '左侧可查看全部历史记录' }}</span>
          </div>
        </div>

        <div class="messages" ref="msgEl">
          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <div v-if="m.role === 'assistant'" class="msg-avatar ai">助</div>
            <div class="msg-bubble" v-html="formatMsg(m.content)"></div>
            <div v-if="m.role === 'user'" class="msg-avatar user">我</div>
          </div>
          <div v-if="streaming" class="msg assistant">
            <div class="msg-avatar ai">助</div>
            <div class="msg-bubble thinking">正在整理回答<span class="dots">...</span></div>
          </div>
        </div>

        <div class="input-area">
          <textarea
            v-model="inputText"
            @keydown.enter.prevent="send"
            :placeholder="activeCourseId ? '输入课程问题、知识点疑问或作业思路...' : '请先选择课程'"
            :disabled="streaming || !activeCourseId"
            rows="2"
          ></textarea>
          <button @click="send" :disabled="!inputText.trim() || streaming || !activeCourseId" class="send-btn">
            <el-icon><Position /></el-icon>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { v4 as uuid } from 'uuid'
import { marked } from 'marked'
import { Position } from '@element-plus/icons-vue'
import axios from 'axios'

const courses = ref<any[]>([])
const conversations = ref<any[]>([])
const activeCourseId = ref<number>(0)
const activeCourse = computed(() => courses.value.find(c => c.id === activeCourseId.value) ?? null)
const messages = ref<{role:string, content:string}[]>([])
const inputText = ref('')
const streaming = ref(false)
const historyError = ref('')
const msgEl = ref<HTMLElement|null>(null)
const conversationId = ref(uuid())

const formatMsg = (t: string) => marked.parse(t || '') as string
const fmtTime = (d: string) => new Date(d).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })

function defaultMessage() {
  return [{
    role: 'assistant',
    content: activeCourse.value
      ? `已切换到 **${activeCourse.value.name}**。可以提问课程知识点、作业思路、测验错题或复习计划。`
      : '请先选择一门课程开始问答；左侧会显示全部课程的历史对话。',
  }]
}

async function loadConversations() {
  historyError.value = ''
  try {
    const params: any = {}
    if (activeCourseId.value) params.course_id = activeCourseId.value
    const r = await axios.get('/api/v1/chat/conversations', { params })
    conversations.value = r.data
  } catch (e: any) {
    conversations.value = []
    historyError.value = e.response?.status === 404
      ? '后端对话记录接口尚未加载，请重启后端服务。'
      : '对话记录加载失败，请稍后重试。'
  }
}

async function onCourseChanged() {
  startNewConversation(false)
  await loadConversations()
}

function startNewConversation(resetHistory = true) {
  conversationId.value = uuid()
  messages.value = defaultMessage()
  if (resetHistory) loadConversations()
}

async function openConversation(item: any) {
  conversationId.value = item.conversation_id
  if (item.course_id) activeCourseId.value = item.course_id
  const r = await axios.get(`/api/v1/chat/conversations/${item.conversation_id}`)
  messages.value = r.data.messages.map((m: any) => ({ role: m.role, content: m.content }))
  await nextTick()
  scrollToBottom()
}

async function send() {
  if (!inputText.value.trim() || streaming.value || !activeCourseId.value) return
  const text = inputText.value
  messages.value.push({role:'user', content:text})
  inputText.value = ''
  streaming.value = true
  const idx = messages.value.length
  messages.value.push({role:'assistant', content:''})
  await nextTick()
  scrollToBottom()

  try {
    const res = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {'Content-Type':'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}`},
      body: JSON.stringify({message:text, course_id:activeCourseId.value, conversation_id:conversationId.value}),
    })
    const reader = res.body!.getReader()
    const dec = new TextDecoder()
    while (true) {
      const {value, done} = await reader.read()
      if (done) break
      const lines = dec.decode(value, {stream:true}).split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const d = JSON.parse(line.slice(6))
            if (d.content && messages.value[idx]) {
              messages.value[idx]!.content += d.content
              scrollToBottom()
            }
          } catch {}
        }
      }
    }
    await loadConversations()
  } catch(e) {
    if (messages.value[idx]) messages.value[idx]!.content = '请求失败，请检查网络或稍后重试。'
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => { if (msgEl.value) msgEl.value.scrollTop = msgEl.value.scrollHeight })
}

onMounted(async () => {
  const res = await axios.get('/api/v1/courses/my')
  courses.value = res.data
  const autoTestCourse = courses.value.find((course: any) =>
    (course.course_code || '').includes('XZ0800195X0') || (course.name || '').includes('自动测试系统A')
  )
  if (autoTestCourse) activeCourseId.value = autoTestCourse.id
  messages.value = defaultMessage()
  await loadConversations()
})
</script>

<style scoped>
.page { padding: 28px; height: 100%; display: flex; flex-direction: column; color: #0f2f64; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; flex-shrink: 0; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { font-size: 13px; color: #5b6f92; margin: 6px 0 0; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.course-select { min-width: 220px; background: #ffffff; border: 1px solid #c8ddf4; border-radius: 8px; color: #0f2f64; padding: 9px 12px; outline: none; }
.new-chat-btn { background: #0b63b6; border: 1px solid #0b63b6; color: #ffffff; border-radius: 8px; padding: 9px 13px; font-weight: 800; cursor: pointer; }
.new-chat-btn:disabled { opacity: .45; cursor: not-allowed; }
.chat-shell { flex: 1; min-height: 0; display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 14px; }
.history-panel, .chat-area { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; min-height: 0; box-shadow: 0 10px 24px rgba(15,47,100,.06); }
.history-panel { padding: 12px; overflow-y: auto; }
.history-head { display: flex; justify-content: space-between; color: #0f2f64; font-size: 14px; margin-bottom: 10px; }
.history-head span { color: #5b6f92; font-size: 12px; }
.history-empty { color: #5b6f92; border: 1px dashed #c8ddf4; border-radius: 8px; padding: 18px; text-align: center; font-size: 13px; background: #f8fbff; }
.history-empty.error { color: #cf3434; background: #fff4f2; border-color: #ffd5cf; }
.history-item { width: 100%; text-align: left; background: #f8fbff; border: 1px solid #e1ecf8; border-radius: 8px; padding: 11px; margin-bottom: 8px; cursor: pointer; transition: all .16s; }
.history-item:hover, .history-item.active { border-color: #9ec8f1; background: #eaf3ff; }
.history-item strong { color: #0f2f64; font-size: 13px; display: block; line-height: 1.45; }
.history-item span, .history-item em { color: #5b6f92; font-size: 11px; display: block; margin-top: 4px; font-style: normal; }
.chat-area { display: flex; flex-direction: column; overflow: hidden; }
.chat-header { padding: 14px 18px; border-bottom: 1px solid #edf3fb; display: flex; justify-content: space-between; background: #f8fbff; }
.chat-header strong { display: block; color: #0f2f64; font-size: 15px; }
.chat-header span { color: #5b6f92; font-size: 12px; margin-top: 3px; display: block; }
.messages { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.msg { display: flex; align-items: flex-start; gap: 10px; }
.msg.user { flex-direction: row-reverse; }
.msg-avatar { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 900; flex-shrink: 0; }
.msg-avatar.ai { background: #0b63b6; color: white; }
.msg-avatar.user { background: #eaf3ff; color: #0b63b6; border: 1px solid #c8ddf4; }
.msg-bubble { max-width: 76%; padding: 12px 15px; border-radius: 12px; font-size: 14px; line-height: 1.65; }
.msg.assistant .msg-bubble { background: #f5f9ff; color: #0f2f64; border: 1px solid #e1ecf8; border-top-left-radius: 4px; }
.msg.user .msg-bubble { background: #0b63b6; color: #ffffff; border-top-right-radius: 4px; }
.thinking { color: #5b6f92; font-style: italic; }
.dots { animation: blink 1.2s step-end infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.input-area { display: flex; gap: 10px; padding: 14px; border-top: 1px solid #edf3fb; flex-shrink: 0; background: #f8fbff; }
.input-area textarea { flex: 1; background: #ffffff; border: 1px solid #c8ddf4; border-radius: 10px; padding: 10px 12px; color: #0f2f64; font-size: 14px; outline: none; resize: none; font-family: inherit; }
.send-btn { width: 44px; height: 44px; border-radius: 10px; background: #0b63b6; border: none; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; align-self: flex-end; }
.send-btn:disabled { opacity: .45; cursor: not-allowed; }
@media (max-width: 960px) {
  .chat-shell { grid-template-columns: 1fr; }
  .history-panel { max-height: 240px; }
  .page-header { flex-direction: column; }
}
</style>
