<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">我的课表</h1>
      <p class="page-sub">查看课程安排，或上传教务截图智能导入</p>
    </div>

    <!-- 已有课表展示 (当有数据且不在"重新导入"模式下时) -->
    <div v-if="timetable.length > 0 && !showImport" class="timetable-view">
      <div class="toolbar">
        <button class="action-btn" @click="showImport = true">
          重新导入课表
        </button>
      </div>

      <div class="timetable-grid-wrapper">
        <table class="timetable-table">
          <thead>
            <tr>
              <th class="time-col">节次</th>
              <th v-for="day in days" :key="day">{{ day }}</th>
            </tr>
          </thead>
          <tbody>
            <!-- 行高 = 该节次全局最大课程数 × 基准 72px，确保所有格子等高 -->
            <tr
              v-for="session in 11"
              :key="session"
              :style="{ height: maxCoursesForSession(session) * 72 + 'px' }"
            >
              <td class="time-col">第 {{ session }} 节</td>
              <td v-for="(_, dIndex) in days" :key="dIndex" class="slot-cell">
                <div class="slot-content">
                  <div
                    v-for="c in getCoursesFor(dIndex + 1, session)"
                    :key="c.id"
                    class="course-block"
                    :style="{
                      background: getCourseColor(c.course_name),
                      borderLeftColor: getCourseAccent(c.course_name),
                    }"
                  >
                    <div class="c-name">{{ c.course_name }}</div>
                    <div class="c-loc">{{ c.location || '教室未定' }}</div>
                    <div class="c-weeks-badge">{{ formatWeeks(c.weeks) }}</div>
                  </div>
                  <!-- 空格占位：保证空格子高度也撑满整行 -->
                  <div v-if="getCoursesFor(dIndex + 1, session).length === 0" class="slot-placeholder"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 课表导入区 (当无数据或主动点击重新导入时显示) -->
    <div v-else class="import-view">
      <div class="import-toolbar" v-if="timetable.length > 0">
        <button class="back-btn" @click="showImport = false">← 取消并返回课表</button>
      </div>

      <div class="drop-zone" :class="{dragging}" @dragover.prevent="dragging=true" @dragleave="dragging=false" @drop.prevent="onDrop" @click="fileInput?.click()">
        <div v-if="!loading">
          <el-icon class="drop-icon"><Upload /></el-icon>
          <div class="drop-text">拖拽课表截图至此</div>
          <div class="drop-sub">支持 PNG、JPG，多模态 AI 将智能识别全部课程信息</div>
          <button class="pick-btn">手动选择图片</button>
        </div>
        <div v-else class="loading-state">
          <div class="spinner"></div>
          <div class="loading-text">多模态大模型视觉解析中，请稍候...</div>
        </div>
        <input ref="fileInput" type="file" accept="image/*" hidden @change="onFileChange" />
      </div>

      <div v-if="result" class="result-card" :class="result.success ? 'success' : 'error'">
        <div class="result-icon">{{ result.success ? '✓' : '✕' }}</div>
        <div>
          <div class="result-title">{{ result.success ? '导入成功' : '导入失败' }}</div>
          <div class="result-msg">{{ result.message }}</div>
        </div>
        <button v-if="result.success" @click="loadTimetable" class="goto-btn">查看课表 →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const days = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
const timetable = ref<any[]>([])
const showImport = ref(false)

// 导入相关状态
const fileInput = ref<HTMLInputElement|null>(null)
const loading = ref(false)
const dragging = ref(false)
const result = ref<{success:boolean, message:string}|null>(null)

// 颜色系统：背景色 + 对应边框强调色
const colorPalettes = [
  { bg: 'rgba(99,102,241,0.12)',  accent: '#6366f1' },  // Indigo
  { bg: 'rgba(16,185,129,0.12)',  accent: '#10b981' },  // Emerald
  { bg: 'rgba(245,158,11,0.12)',  accent: '#f59e0b' },  // Amber
  { bg: 'rgba(236,72,153,0.12)',  accent: '#ec4899' },  // Pink
  { bg: 'rgba(14,165,233,0.12)', accent: '#0ea5e9' },  // Sky
  { bg: 'rgba(168,85,247,0.12)',  accent: '#a855f7' },  // Purple
  { bg: 'rgba(244,63,94,0.12)',   accent: '#f43f5e' },  // Rose
]
const courseColorIndex = ref<Record<string, number>>({})

function _getIdx(courseName: string): number {
  if (!(courseName in courseColorIndex.value)) {
    courseColorIndex.value[courseName] = Object.keys(courseColorIndex.value).length % colorPalettes.length
  }
  return courseColorIndex.value[courseName] ?? 0
}
function getCourseColor(courseName: string): string {
  return colorPalettes[_getIdx(courseName)]?.bg ?? 'rgba(99,102,241,0.12)'
}
function getCourseAccent(courseName: string): string {
  return colorPalettes[_getIdx(courseName)]?.accent ?? '#6366f1'
}

/** 周次格式化：[1,2,3,4] → "第1~4周"，[5] → "第5周" */
function formatWeeks(weeks: any): string {
  if (!weeks) return ''
  let arr: number[] = []
  if (Array.isArray(weeks)) {
    arr = weeks.map(Number).filter(n => !isNaN(n))
  } else if (typeof weeks === 'string') {
    // 支持 "1-16" 、"[1,2,3]" 、"1,2,3" 等多种模式
    const cleaned = weeks.replace(/[\[\]]/g, '')
    if (cleaned.includes('-') && !cleaned.includes(',')) {
      return `第${cleaned.trim()}周`
    }
    arr = cleaned.split(',').map(s => Number(s.trim())).filter(n => !isNaN(n))
  } else if (typeof weeks === 'number') {
    return `第${weeks}周`
  }
  if (arr.length === 0) return String(weeks)
  if (arr.length === 1) return `第${arr[0] ?? '?'}周`
  const min = Math.min(...arr)
  const max = Math.max(...arr)
  return `第${min}~${max}周`
}

/** 获取某天某节开始的所有课（只在 start_session 行渲染） */
function getCoursesFor(dayOfWeek: number, session: number) {
  return timetable.value.filter(item => {
    if (item.day_of_week !== dayOfWeek) return false
    return parseInt(item.start_session) === session
  })
}

/**
 * 计算某节次在所有 7 天中最多有几门课同时开始。
 * 用于动态设置整行高度：行高 = N × 72px。
 */
function maxCoursesForSession(session: number): number {
  let max = 1  // 最少撑满 1 格高度
  for (let day = 1; day <= 7; day++) {
    const count = getCoursesFor(day, session).length
    if (count > max) max = count
  }
  return max
}

async function loadTimetable() {
  try {
    const res = await axios.get('/api/v1/timetable/')
    timetable.value = res.data
    if (timetable.value.length > 0) {
      showImport.value = false
    } else {
      showImport.value = true
    }
  } catch (error) {
    console.error("加载课表失败", error)
  }
}

async function upload(file: File) {
  loading.value = true; result.value = null
  const form = new FormData()
  form.append('file', file)
  try {
    const res = await axios.post('/api/v1/timetable/import', form, { headers: {'Content-Type': 'multipart/form-data'}, timeout: 180000 })
    result.value = { success: true, message: `已成功解析 ${res.data.courses_imported} 门课程和 ${res.data.timetable_entries_created} 条排课记录` }
  } catch(e: any) {
    result.value = { success: false, message: e.response?.data?.detail || '解析失败，请确保截图清晰' }
  } finally { loading.value = false }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files[0]
  if (f && f.type.startsWith('image/')) upload(f)
}

function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) upload(f)
}

onMounted(() => {
  loadTimetable()
})
</script>

<style scoped>
.page { padding: 32px; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.page-header { margin-bottom: 24px; flex-shrink: 0; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.page-sub { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

/* 课表展示区 */
.timetable-view { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.toolbar { margin-bottom: 16px; display: flex; justify-content: flex-end; flex-shrink: 0; }
.action-btn { background: rgba(99,102,241,0.1); color: #818cf8; border: 1px solid rgba(99,102,241,0.3); border-radius: 8px; padding: 8px 16px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.action-btn:hover { background: rgba(99,102,241,0.2); color: #a5b4fc; }

.timetable-grid-wrapper {
  flex: 1; overflow: auto; border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.05); background: rgba(15,23,42,0.6);
}
.timetable-table { width: 100%; border-collapse: collapse; min-width: 800px; }
.timetable-table th {
  position: sticky; top: 0; z-index: 10;
  background: #1e293b; color: var(--text-secondary); font-weight: 600; font-size: 13px;
  padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center;
}
.timetable-table td {
  border: 1px solid rgba(255,255,255,0.03); vertical-align: top;
  min-height: 0; min-width: 120px; padding: 0;
}

.time-col { width: 60px; text-align: center; font-size: 11px; color: var(--text-secondary); background: rgba(255,255,255,0.01); }
.slot-cell { position: relative; padding: 3px; vertical-align: top; }

/* slot-content：垂直堆叠，gap 分隔多课，不拉伸 */
.slot-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100%;
}

/* 每个 course-block 固定高 64px，多课就多块，行高随之扩展 */
.course-block {
  height: 64px;
  flex-shrink: 0;          /* 不允许压缩 */
  border-radius: 8px;
  padding: 6px 8px;
  border-left: 3px solid #6366f1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  transition: box-shadow 0.15s;
  box-sizing: border-box;
}
.course-block:hover {
  box-shadow: 0 0 0 1px rgba(255,255,255,0.12);
  filter: brightness(1.08);
}

.c-name {
  color: var(--text-main);
  font-weight: 700;
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.c-loc {
  color: var(--text-secondary);
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 周次胶囊标签 */
.c-weeks-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 20px;
  font-size: 9px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  white-space: nowrap;
  align-self: flex-start;
}
/* 空格占位 div，撑满整行但透明 */
.slot-placeholder { flex: 1; }


/* 课表导入区原样保留 */
.import-view { display: flex; flex-direction: column; gap: 20px; }
.import-toolbar { margin-bottom: 8px; }
.back-btn { background: transparent; color: var(--text-secondary); border: none; cursor: pointer; font-size: 14px; padding: 0; }
.back-btn:hover { color: var(--text-main); text-decoration: underline; }

.drop-zone {
  border: 2px dashed rgba(99,102,241,0.3); border-radius: 20px;
  padding: 60px; text-align: center; cursor: pointer; transition: all 0.2s;
  background: rgba(99,102,241,0.03); max-width: 600px; margin: 0 auto; width: 100%;
}
.drop-zone:hover, .drop-zone.dragging { border-color: #6366f1; background: rgba(99,102,241,0.07); }
.drop-icon { font-size: 48px; color: #6366f1; margin-bottom: 16px; display: inline-block;}
.drop-text { font-size: 20px; font-weight: 700; color: var(--text-main); margin-bottom: 8px; }
.drop-sub { color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; }
.pick-btn { background: linear-gradient(135deg, #6366f1, #7c3aed); color: white; border: none; border-radius: 50px; padding: 12px 28px; font-weight: 700; cursor: pointer; font-size: 15px; }

.loading-state { display: flex; flex-direction: column; align-items: center; gap: 16px; }
.spinner { width: 48px; height: 48px; border: 3px solid rgba(99,102,241,0.2); border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { color: #818cf8; font-size: 15px; }

.result-card {
  display: flex; align-items: center; gap: 16px; padding: 20px 24px;
  border-radius: 16px; margin-top: 10px; max-width: 600px; margin-left: auto; margin-right: auto;
  border: 1px solid; width: 100%; box-sizing: border-box;
}
.result-card.success { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.3); }
.result-card.error { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.3); }
.result-icon { font-size: 24px; font-weight: 700; }
.result-card.success .result-icon { color: #34d399; }
.result-card.error .result-icon { color: #f87171; }
.result-title { font-size: 16px; font-weight: 700; color: var(--text-main); }
.result-msg { font-size: 14px; color: var(--text-secondary); margin-top: 2px; }
.goto-btn { margin-left: auto; background: #1e1b4b; color: #818cf8; padding: 10px 18px; border-radius: 10px; border: 1px solid rgba(99,102,241,0.3); font-weight: 600; cursor: pointer; transition: all 0.2s;}
.goto-btn:hover { background: rgba(99,102,241,0.15); color: white; }
</style>
