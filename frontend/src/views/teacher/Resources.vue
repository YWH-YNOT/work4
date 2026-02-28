<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">资源管理</h1>
    </div>

    <!-- 课程筛选 -->
    <div class="filter-bar">
      <select v-model="selectedCourse" @change="loadResources" class="sel">
        <option value="">请选择课程</option>
        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>

      <!-- 上传区 -->
      <label v-if="selectedCourse" class="upload-label" :class="{'drag-over': dragging}"
        @dragover.prevent="dragging=true"
        @dragleave="dragging=false"
        @drop.prevent="onDrop"
      >
        <input type="file" class="file-input" @change="onFileChange" ref="fileInput"/>
        <span>📁 点击或拖拽上传文件</span>
      </label>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{width: uploadPct+'%'}"></div>
      </div>
      <span class="progress-text">上传中... {{ uploadPct }}%</span>
    </div>

    <!-- 资源列表 -->
    <div v-if="!selectedCourse" class="empty">请先选择课程以查看资源</div>
    <div v-else-if="loading" class="empty">加载中...</div>
    <div v-else-if="resources.length===0" class="empty">该课程暂无资源，上传第一个文件</div>
    <div v-else class="resource-list">
      <div v-for="r in resources" :key="r.id" class="resource-card">
        <div class="res-icon">{{ fileIcon(r.filename) }}</div>
        <div class="res-info">
          <div class="res-name">{{ r.filename }}</div>
          <div class="res-meta">
            <span>{{ fmtSize(r.file_size) }}</span>
            <span>上传于 {{ fmt(r.created_at) }}</span>
          </div>
        </div>
        <div class="res-actions">
          <a :href="`/api/v1/resources/${r.id}/download`" target="_blank" class="dl-btn" download>⬇ 下载</a>
          <button @click="deleteResource(r)" class="del-btn">🗑 删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const courses = ref<any[]>([])
const resources = ref<any[]>([])
const selectedCourse = ref<number|''>('')
const loading = ref(false)
const uploading = ref(false)
const uploadPct = ref(0)
const dragging = ref(false)
const fileInput = ref<HTMLInputElement|null>(null)

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
const fmtSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024*1024) return `${(bytes/1024).toFixed(1)} KB`
  return `${(bytes/1024/1024).toFixed(2)} MB`
}
const fileIcon = (name: string) => {
  if (!name) return '📄'
  const ext = name.split('.').pop()?.toLowerCase()
  const map: Record<string, string> = {
    pdf: '📕', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊',
    ppt: '📊', pptx: '📊', jpg: '🖼', jpeg: '🖼', png: '🖼',
    gif: '🖼', zip: '📦', rar: '📦', mp4: '🎬', mp3: '🎵',
    py: '🐍', js: '📜', ts: '📜', txt: '📃',
  }
  return map[ext || ''] || '📄'
}

async function loadResources() {
  if (!selectedCourse.value) { resources.value = []; return }
  loading.value = true
  try {
    const r = await axios.get(`/api/v1/resources/?course_id=${selectedCourse.value}`)
    resources.value = r.data
  } finally { loading.value = false }
}

async function uploadFile(file: File) {
  if (!selectedCourse.value) { ElMessage.warning('请先选择课程'); return }
  uploading.value = true
  uploadPct.value = 0
  try {
    const form = new FormData()
    form.append('file', file)
    await axios.post(`/api/v1/resources/upload?course_id=${selectedCourse.value}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total) uploadPct.value = Math.round((e.loaded / e.total) * 100)
      }
    })
    ElMessage.success('文件上传成功')
    await loadResources()
  } catch(e: any) { ElMessage.error(e.response?.data?.detail || '上传失败') }
  finally { uploading.value = false }
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) uploadFile(file)
  if (fileInput.value) fileInput.value.value = ''
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) uploadFile(file)
}

async function deleteResource(r: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${r.filename}"？`, '删除资源', {
      confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
    })
    await axios.delete(`/api/v1/resources/${r.id}`)
    resources.value = resources.value.filter(x => x.id !== r.id)
    ElMessage.success('资源已删除')
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(async () => {
  const c = await axios.get('/api/v1/courses/my')
  courses.value = c.data
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.filter-bar { display: flex; gap: 16px; align-items: center; margin-bottom: 24px; flex-wrap: wrap; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(245,158,11,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.upload-label { display: flex; align-items: center; gap: 8px; background: rgba(245,158,11,0.08); border: 2px dashed rgba(245,158,11,0.3); border-radius: 10px; padding: 10px 20px; cursor: pointer; color: #fbbf24; font-size: 14px; font-weight: 500; transition: all 0.18s; }
.upload-label:hover, .upload-label.drag-over { border-color: #f59e0b; background: rgba(245,158,11,0.15); }
.file-input { display: none; }
.upload-progress { margin-bottom: 20px; display: flex; align-items: center; gap: 14px; }
.progress-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #f59e0b, #fbbf24); border-radius: 4px; transition: width 0.3s; }
.progress-text { font-size: 13px; color: #fbbf24; font-weight: 600; white-space: nowrap; }
.empty { color: var(--text-secondary); text-align: center; padding: 40px; font-size: 15px; }
.resource-list { display: flex; flex-direction: column; gap: 10px; }
.resource-card { display: flex; align-items: center; gap: 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(245,158,11,0.1); border-radius: 14px; padding: 16px 20px; transition: all 0.18s; }
.resource-card:hover { border-color: rgba(245,158,11,0.25); background: rgba(245,158,11,0.04); }
.res-icon { font-size: 28px; width: 40px; text-align: center; flex-shrink: 0; }
.res-info { flex: 1; min-width: 0; }
.res-name { font-size: 15px; font-weight: 600; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px; }
.res-meta { display: flex; gap: 14px; font-size: 12px; color: var(--text-secondary); }
.res-actions { display: flex; gap: 8px; flex-shrink: 0; }
.dl-btn { background: rgba(16,185,129,0.1); color: #34d399; border: 1px solid rgba(16,185,129,0.2); border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: 13px; font-weight: 500; text-decoration: none; transition: all 0.15s; }
.dl-btn:hover { background: rgba(16,185,129,0.2); }
.del-btn { background: rgba(248,113,113,0.1); color: #f87171; border: 1px solid rgba(248,113,113,0.2); border-radius: 8px; padding: 7px 14px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.del-btn:hover { background: rgba(248,113,113,0.2); }
</style>
