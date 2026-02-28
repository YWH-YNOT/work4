<template>
  <div class="p-8 max-w-5xl mx-auto">
    <div class="mb-10 text-center">
      <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600 mb-4">
        AI 课程导入引擎
      </h1>
      <p class="text-slate-500 text-lg">拖拽您的教务系统课表截图，AI 将为您构建专属的学习宇宙。</p>
    </div>

    <!-- Upload Area -->
    <div 
      class="border-4 border-dashed rounded-3xl p-16 text-center transition-all duration-300 relative overflow-hidden"
      :class="isDragging ? 'border-indigo-500 bg-indigo-50 scale-105' : 'border-slate-300 hover:border-indigo-400 bg-white'"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div v-if="!isUploading" class="flex flex-col items-center gap-4">
        <el-icon class="text-indigo-400 text-6xl"><UploadFilled /></el-icon>
        <h3 class="text-2xl font-bold text-slate-700">拖拽课表截图至此</h3>
        <p class="text-slate-400">支持 PNG, JPG。AI 将自动识别课程、时间和授课教师</p>
        <p class="text-slate-400 text-sm">💡 提示：截图前确保课表完整显示，避免模糊或遮挡</p>
        <input 
          type="file" 
          ref="fileInput" 
          class="hidden" 
          accept="image/*"
          @change="handleFileSelect"
        >
        <button 
          @click="fileInput?.click()"
          class="mt-4 px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-semibold transition-colors shadow-lg shadow-indigo-200"
        >
          手动选择图片
        </button>
      </div>

      <!-- Uploading State -->
      <div v-else class="flex flex-col items-center gap-6 py-8">
        <div class="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
        <div class="text-xl font-bold text-indigo-600 animate-pulse">
          多模态大模型解析中，请稍候...
        </div>
        <p class="text-slate-400 text-sm">识别复杂课表通常需要 10-60 秒</p>
      </div>
    </div>

    <!-- Success Result -->
    <div v-if="importResult" class="mt-10">
      <!-- 统计卡片 -->
      <div class="flex items-center gap-4 mb-6 p-6 bg-green-50 border border-green-200 rounded-2xl">
        <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-600">
          <el-icon class="text-2xl"><Select /></el-icon>
        </div>
        <div>
          <h2 class="text-xl font-bold text-slate-800">导入成功</h2>
          <p class="text-slate-500">
            已识别 <span class="font-bold text-indigo-600">{{ importResult.timetable_entries_created }}</span> 条排课记录
            （含 <span class="font-bold text-indigo-600">{{ importResult.courses_imported }}</span> 门新课程）
          </p>
        </div>
      </div>

      <!-- 识别结果预览表 -->
      <div v-if="previewCourses.length > 0" class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-200">
          <h3 class="font-bold text-slate-700">识别结果预览（共 {{ previewCourses.length }} 条）</h3>
          <p class="text-sm text-slate-400 mt-1">如发现识别错误，请重新截图后再次上传</p>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-slate-500 uppercase text-xs">
              <tr>
                <th class="px-4 py-3 text-left">课程名称</th>
                <th class="px-4 py-3 text-left">教师</th>
                <th class="px-4 py-3 text-left">星期</th>
                <th class="px-4 py-3 text-left">节次</th>
                <th class="px-4 py-3 text-left">周次</th>
                <th class="px-4 py-3 text-left">教室</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(c, i) in previewCourses" :key="i" 
                  class="border-t border-slate-100 hover:bg-slate-50 transition-colors">
                <td class="px-4 py-3 font-medium text-slate-800">{{ c.course_name }}</td>
                <td class="px-4 py-3 text-slate-600">{{ c.teacher_name || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                    星期{{ weekdayName(c.day_of_week) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-slate-600">第 {{ c.start_session }}~{{ c.end_session }} 节</td>
                <td class="px-4 py-3 text-slate-500 text-xs">{{ c.weeks || '—' }}</td>
                <td class="px-4 py-3 text-slate-500 text-xs">{{ c.location || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button 
          @click="router.push('/student/timetable')"
          class="px-6 py-3 bg-white border border-slate-200 hover:border-indigo-400 text-slate-700 rounded-full font-semibold transition-colors"
        >
          查看课表
        </button>
        <button 
          @click="router.push('/student/chat')"
          class="px-8 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-full font-semibold transition-colors shadow-xl"
        >
          前往 AI 助教工作台 &rarr;
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Select } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const importResult = ref<any>(null)
const previewCourses = ref<any[]>([])

const weekdayName = (n: number) => (['', '一', '二', '三', '四', '五', '六', '日'][n] ?? String(n))

const handleDrop = async (e: DragEvent) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file) await uploadFile(file)
  }
}

const handleFileSelect = async (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    if (file) await uploadFile(file)
  }
}

const uploadFile = async (file: File) => {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请上传图片格式的文件！')
    return
  }
  
  isUploading.value = true
  importResult.value = null
  previewCourses.value = []
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await axios.post('/api/v1/timetable/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 200000  // 200s，等待模型识别
    })
    
    importResult.value = response.data

    // 导入成功后，获取最新的课表条目用于预览
    try {
      const timetableResp = await axios.get('/api/v1/timetable/')
      previewCourses.value = timetableResp.data || []
    } catch {
      // 预览失败不影响主流程
    }

    ElMessage.success(`AI 解析成功！共识别 ${response.data.timetable_entries_created} 条排课`)
  } catch (error: any) {
    const detail = error.response?.data?.detail || '课表解析失败，请检查图片是否清晰完整'
    ElMessage.error(detail)
    console.error('Timetable import failed:', error.response?.data, error.message)
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
