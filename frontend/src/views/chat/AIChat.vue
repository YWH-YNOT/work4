<template>
  <div class="h-screen flex bg-slate-50 overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-80 bg-white border-r border-slate-200 flex flex-col hidden md:flex shrink-0 shadow-sm relative z-10">
      <div class="p-6 border-b border-slate-100">
        <h2 class="text-2xl font-extrabold text-slate-800 tracking-tight flex items-center gap-2">
          <el-icon class="text-indigo-600"><ChatDotRound /></el-icon>
          AI 助教宇宙
        </h2>
        <p class="text-sm text-slate-500 mt-1 font-medium">智能代理 · RAG增强</p>
      </div>
      
      <div class="flex-1 overflow-y-auto p-4 space-y-2">
        <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 px-2">当前课程上下文</div>
        
        <!-- Mock Course selector for MVP -->
        <button 
          v-for="course in courses" 
          :key="course.id"
          @click="selectCourse(course.id)"
          class="w-full text-left px-4 py-3 rounded-xl transition-all duration-200 border border-transparent flex items-center gap-3"
          :class="activeCourseId === course.id ? 'bg-indigo-50 border-indigo-100 text-indigo-700 shadow-sm' : 'hover:bg-slate-50 text-slate-600'"
        >
          <div class="w-8 h-8 rounded-lg flex items-center justify-center font-bold"
               :class="activeCourseId === course.id ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'">
            {{ course.name.charAt(0) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ course.name }}</div>
            <div class="text-xs mt-0.5 truncate"
                 :class="activeCourseId === course.id ? 'text-indigo-400' : 'text-slate-400'">
              <span v-if="course.course_code">{{ course.course_code }} · </span>{{ course.teacher_name }}
            </div>
          </div>
        </button>
      </div>

      <div class="p-4 border-t border-slate-100 bg-slate-50/50">
        <button @click="$router.push('/timetable')" class="w-full flex items-center justify-center gap-2 py-2 px-4 text-sm font-medium text-slate-600 hover:text-indigo-600 hover:bg-white rounded-lg transition-colors border border-transparent hover:border-slate-200 shadow-sm">
          <el-icon><Back /></el-icon>
          返回课表导入
        </button>
      </div>
    </aside>

    <!-- Chat Area -->
    <main class="flex-1 flex flex-col bg-slate-50/50 relative">
      <!-- Chat Header -->
      <header class="h-16 px-6 glass flex items-center justify-between z-10 sticky top-0 shadow-sm">
        <div class="flex items-center gap-3">
          <h3 class="font-bold text-slate-800 text-lg">
            {{ activeCourse?.name || '请选择课程' }} 的 AI 助教
          </h3>
          <span v-if="activeCourse" class="px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-full flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
            Agent 在线就绪
          </span>
        </div>
      </header>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth" ref="messagesContainer">
        <template v-for="(msg, index) in messages" :key="index">
          <div 
            class="flex max-w-4xl mx-auto"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <!-- Assistant Avatar -->
            <div v-if="msg.role === 'assistant'" class="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md shadow-indigo-200/50 mr-4 shrink-0 mt-1">
              <el-icon><Cpu /></el-icon>
            </div>

            <!-- Message Bubble -->
            <div 
              class="relative group rounded-3xl p-5 shadow-sm text-[15px] leading-relaxed"
              :class="[
                msg.role === 'user' 
                  ? 'bg-slate-900 text-white rounded-tr-sm ml-12' 
                  : 'bg-white text-slate-700 rounded-tl-sm mr-12 border border-slate-100'
              ]"
            >
              <div class="whitespace-pre-wrap break-words" v-html="formatMessage(msg.content)"></div>
              
              <!-- Citations UI (Premium aesthetic for RAG) -->
              <div v-if="msg.role === 'assistant' && hasCitations(msg.content)" class="mt-4 pt-4 border-t border-slate-100">
                <div class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1 mb-2">
                  <el-icon><Link /></el-icon> 获取自知识库引用
                </div>
                <div class="flex flex-wrap gap-2">
                   <!-- Extraction logic simplified for mockup -->
                   <span class="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-md border border-indigo-100 hover:bg-indigo-100 transition-colors cursor-pointer">
                     <el-icon><Document /></el-icon>
                     Lecture_Notes.pdf
                   </span>
                </div>
              </div>
            </div>

            <!-- User Avatar -->
            <div v-if="msg.role === 'user'" class="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-500 ml-4 shrink-0 shadow-inner mt-1">
              <el-icon><User /></el-icon>
            </div>
          </div>
        </template>
        
        <!-- Loading State -->
        <div v-if="isStreaming" class="flex max-w-3xl mx-auto justify-start">
           <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-md shadow-indigo-200/50 mr-4 shrink-0">
             <el-icon class="animate-spin"><Loading /></el-icon>
           </div>
           <div class="bg-white rounded-3xl rounded-tl-sm p-5 shadow-sm border border-slate-100 mr-12 text-slate-400 italic">
             <span class="animate-pulse">Agent 正在检索知识库并进行思考(Reason-Act)...</span>
           </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-6 bg-white/80 backdrop-blur-xl border-t border-slate-200 relative z-10">
        <div class="max-w-4xl mx-auto relative group">
          <textarea
            v-model="inputMsg"
            @keydown.enter.prevent="sendMessage"
            placeholder="向 AI 助教提问关于该课程的问题 (支持 RAG 文档召回)..."
            class="w-full bg-slate-100/50 border-2 border-transparent hover:border-slate-200 focus:border-indigo-500 focus:bg-white rounded-2xl py-4 pl-6 pr-16 text-slate-700 focus:outline-none transition-all duration-300 resize-none shadow-sm"
            rows="2"
            :disabled="isStreaming || !activeCourseId"
          ></textarea>
          <button 
            @click="sendMessage"
            :disabled="!inputMsg.trim() || isStreaming || !activeCourseId"
            class="absolute right-3 bottom-3 p-3 rounded-xl transition-all duration-200 flex items-center justify-center shadow-md"
            :class="inputMsg.trim() && !isStreaming ? 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-105' : 'bg-slate-200 text-slate-400 cursor-not-allowed'"
          >
            <el-icon class="text-xl font-bold"><Position /></el-icon>
          </button>
        </div>
        <div class="text-center mt-3 text-xs text-slate-400 font-medium">
          基于 LangChain Agent 架构支撑，系统具备大模型幻觉抑制与溯源引用能力。
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ChatDotRound, Cpu, User, Back, Position, Loading, Document, Link } from '@element-plus/icons-vue'
import { v4 as uuidv4 } from 'uuid'
import { marked } from 'marked'

const courses = ref<{id: number, name: string, course_code: string, teacher_name: string}[]>([])

const loadCourses = async () => {
  try {
    const res = await fetch('/api/v1/courses')
    const data = await res.json()
    courses.value = data
    if (data.length > 0) activeCourseId.value = data[0].id
  } catch (e) {
    console.error('Failed to load courses:', e)
  }
}

const activeCourseId = ref(1)
const activeCourse = computed(() => courses.value.find(c => c.id === activeCourseId.value))

const messages = ref<{role: string, content: string}[]>([
  { role: 'assistant', content: '你好！我是你的 AI 专属助教。我已经阅读了你上传的全部讲义和资料。有关这门课的任何问题，随时问我！' }
])

const inputMsg = ref('')
const isStreaming = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const conversationId = ref(uuidv4())

const selectCourse = (id: number) => {
  activeCourseId.value = id
  messages.value = [
    { role: 'assistant', content: `切换至 **${activeCourse.value?.name}** 频道。随时解答你的疑惑！` }
  ]
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (text: string) => {
  return marked.parse(text)
}

const hasCitations = (text: string) => {
  return text.includes('资料引用来源') || text.includes('Citations')
}

const sendMessage = async () => {
  if (!inputMsg.value.trim() || isStreaming.value || !activeCourseId.value) return

  const userText = inputMsg.value
  messages.value.push({ role: 'user', content: userText })
  inputMsg.value = ''
  isStreaming.value = true
  scrollToBottom()

  // We append a blank assistant message to stream into.
  const assistantMsgIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })

  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: userText,
        course_id: activeCourseId.value,
        conversation_id: conversationId.value
      })
    })

    if (!response.body) throw new Error('No response body')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      
      // Parse SSE Format: data: {"content": "..."}
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6)
          if (dataStr === '[DONE]') {
            continue
          }
          
          try {
            const dataObj = JSON.parse(dataStr)
            if (dataObj.content && messages.value[assistantMsgIndex]) {
              messages.value[assistantMsgIndex].content += dataObj.content
              scrollToBottom()
            }
          } catch (e) {
            // Ignore parse errors on partial chunks
            console.error("Parse short chunk error:", e)
          }
        }
      }
    }
  } catch (error) {
    console.error('Chat stream error', error)
    if (messages.value[assistantMsgIndex]) {
      messages.value[assistantMsgIndex].content = '对不起，API代理层出现了一些问题，无法完成推理响应。'
    }
  } finally {
    isStreaming.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  loadCourses()
  scrollToBottom()
})
</script>

<style>
/* Prose stylings for markdown */
.whitespace-pre-wrap p {
    margin-bottom: 0.5em;
}
.whitespace-pre-wrap ul, .whitespace-pre-wrap ol {
    margin-left: 1.5em;
    margin-bottom: 1em;
}
.whitespace-pre-wrap ul {
    list-style-type: disc;
}
.whitespace-pre-wrap ol {
    list-style-type: decimal;
}
</style>
