<template>
  <div class="page">
    <div class="page-header">
      <div class="header-row">
        <div>
          <h1 class="page-title">AI 助教</h1>
          <p class="page-sub">{{ activeCourse ? `当前课程：${activeCourse.name}` : '请选择课程后开始智能问答' }}</p>
        </div>
        <!-- 课程切换器 -->
        <div class="course-picker" ref="pickerRef">
          <button class="picker-trigger" @click="showPicker = !showPicker">
            <template v-if="activeCourse">
              <span class="course-avatar-mini">{{ activeCourse.name.charAt(0) }}</span>
              {{ activeCourse.name }}
            </template>
            <template v-else>选择课程</template>
            <span class="chevron" :class="{ open: showPicker }">▾</span>
          </button>

          <!-- 下拉面板 -->
          <div v-if="showPicker" class="picker-dropdown">
            <div class="picker-title">选择课程</div>
            <div v-if="courses.length === 0" class="empty-courses">
              请先
              <router-link to="/student/timetable" class="import-link" @click="showPicker = false">导入课表</router-link>
              再返回此页
            </div>
            <button
              v-for="c in courses"
              :key="c.id"
              :class="['picker-item', activeCourseId === c.id && 'active']"
              @click="selectCourse(c)"
            >
              <span class="course-avatar-mini">{{ c.name.charAt(0) }}</span>
              <div class="picker-item-info">
                <div>{{ c.name }}</div>
                <div class="picker-sub">{{ c.course_code }} · {{ c.teacher_name }}</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Area (全宽) -->
    <div class="chat-area">
      <div class="messages" ref="msgEl">
        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div v-if="m.role === 'assistant'" class="msg-avatar ai">AI</div>
          <div class="msg-bubble" v-html="formatMsg(m.content)"></div>
          <div v-if="m.role === 'user'" class="msg-avatar user">我</div>
        </div>
        <div v-if="streaming" class="msg assistant">
          <div class="msg-avatar ai">AI</div>
          <div class="msg-bubble thinking">思考中<span class="dots">...</span></div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputText"
          @keydown.enter.prevent="send"
          :placeholder="activeCourseId ? '向 AI 助教提问...' : '请先点击右上角选择课程'"
          :disabled="streaming || !activeCourseId"
          rows="2"
        ></textarea>
        <button @click="send" :disabled="!inputText.trim() || streaming || !activeCourseId" class="send-btn">
          <el-icon><Position /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { v4 as uuid } from 'uuid'
import { marked } from 'marked'
import { Position } from '@element-plus/icons-vue'
import axios from 'axios'

const courses = ref<any[]>([])
const activeCourseId = ref<number | null>(null)
const activeCourse = computed(() => courses.value.find(c => c.id === activeCourseId.value) ?? null)

const messages = ref<{role:string, content:string}[]>([
  {role:'assistant', content:'你好！请先点击右上角选择课程，然后向我提问。'}
])
const inputText = ref('')
const streaming = ref(false)
const msgEl = ref<HTMLElement|null>(null)
const conversationId = ref(uuid())
const showPicker = ref(false)
const pickerRef = ref<HTMLElement|null>(null)

const formatMsg = (t: string) => marked.parse(t)

// 点击外部关闭下拉
function onDocClick(e: MouseEvent) {
  if (pickerRef.value && !pickerRef.value.contains(e.target as Node)) {
    showPicker.value = false
  }
}
onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))

async function selectCourse(c: any) {
  activeCourseId.value = c.id
  conversationId.value = uuid()
  showPicker.value = false
  messages.value = [{role:'assistant', content:`已切换到 **${c.name}** 课程，有问题尽管问！`}]
}

async function send() {
  if (!inputText.value.trim() || streaming.value || !activeCourseId.value) return
  const text = inputText.value
  messages.value.push({role:'user', content:text})
  inputText.value = ''
  streaming.value = true
  const idx = messages.value.length
  messages.value.push({role:'assistant', content:''})
  await nextTick(); scrollToBottom()

  try {
    const res = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {'Content-Type':'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}`},
      body: JSON.stringify({message:text, course_id:activeCourseId.value, conversation_id:conversationId.value})
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
            if (d.content && messages.value[idx]) { messages.value[idx]!.content += d.content; scrollToBottom() }
          } catch {}
        }
      }
    }
  } catch(e) {
    if (messages.value[idx]) messages.value[idx]!.content = '请求失败，请检查网络或重试。'
  } finally { streaming.value = false; scrollToBottom() }
}

function scrollToBottom() {
  nextTick(() => { if (msgEl.value) msgEl.value.scrollTop = msgEl.value.scrollHeight })
}

onMounted(async () => {
  try { const res = await axios.get('/api/v1/courses/my'); courses.value = res.data } catch {}
})
</script>

<style scoped>
.page { padding: 32px; height: 100%; display: flex; flex-direction: column; font-family: 'Inter', sans-serif; }
.page-header { margin-bottom: 16px; flex-shrink: 0; }

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

/* ── 课程切换器 ── */
.course-picker {
  position: relative;
  flex-shrink: 0;
}
.picker-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.3);
  border-radius: 10px;
  color: #c7d2fe;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
  white-space: nowrap;
}
.picker-trigger:hover { background: rgba(99,102,241,0.18); border-color: #6366f1; }
.course-avatar-mini {
  width: 24px; height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #6366f1, #7c3aed);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.chevron { font-size: 12px; transition: transform 0.2s; display: inline-block; }
.chevron.open { transform: rotate(180deg); }

/* 下拉面板 */
.picker-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  max-height: 420px;
  overflow-y: auto;
  background: #1e293b;
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 14px;
  padding: 8px;
  z-index: 100;
  box-shadow: 0 16px 48px rgba(0,0,0,0.4);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.picker-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 8px 8px;
}
.empty-courses { color: var(--text-secondary); font-size: 13px; padding: 8px; }
.import-link { color: #6366f1; text-decoration: underline; cursor: pointer; }

.picker-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  width: 100%;
}
.picker-item:hover { background: rgba(99,102,241,0.08); border-color: rgba(99,102,241,0.2); }
.picker-item.active { background: rgba(99,102,241,0.15); border-color: #6366f1; }
.picker-item-info { font-size: 13px; color: #c7d2fe; font-weight: 500; }
.picker-sub { font-size: 11px; color: var(--text-secondary); margin-top: 1px; }

/* ── 聊天区 ── */
.chat-area { flex: 1; display: flex; flex-direction: column; background: rgba(255,255,255,0.02); border: 1px solid rgba(99,102,241,0.12); border-radius: 16px; overflow: hidden; }
.messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.msg { display: flex; align-items: flex-start; gap: 12px; }
.msg.user { flex-direction: row-reverse; }
.msg-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.msg-avatar.ai { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; }
.msg-avatar.user { background: #334155; color: var(--text-secondary); }
.msg-bubble { max-width: 70%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; }
.msg.assistant .msg-bubble { background: rgba(255,255,255,0.05); color: var(--text-main); border-radius: 4px 16px 16px 16px; }
.msg.user .msg-bubble { background: rgba(99,102,241,0.2); color: #c7d2fe; border-radius: 16px 4px 16px 16px; }
.thinking { color: var(--text-secondary); font-style: italic; }
.dots { animation: blink 1.2s step-end infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.input-area { display: flex; gap: 10px; padding: 16px; border-top: 1px solid rgba(255,255,255,0.05); flex-shrink: 0; }
.input-area textarea {
  flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2);
  border-radius: 12px; padding: 10px 14px; color: var(--text-main); font-size: 14px;
  outline: none; resize: none; font-family: 'Inter', sans-serif;
}
.input-area textarea:focus { border-color: #6366f1; }
.input-area textarea::placeholder { color: var(--text-secondary); }
.send-btn {
  width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #6366f1, #7c3aed);
  border: none; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center;
  align-self: flex-end; flex-shrink: 0; transition: all 0.2s; font-size: 18px;
}
.send-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(99,102,241,0.4); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
