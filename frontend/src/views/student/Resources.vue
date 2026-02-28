<template>
  <div class="page">
    <div class="page-header-row">
      <h1 class="page-title">课程资源</h1>
      <div class="course-select">
        <select v-model="selectedCourse" @change="load" class="sel">
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
    </div>
    <div v-if="resources.length === 0" class="empty">当前课程暂无资源</div>
    <div class="resources-list">
      <div v-for="r in resources" :key="r.id" class="res-card">
        <div class="res-icon"><el-icon><Document /></el-icon></div>
        <div class="res-info">
          <div class="res-name">{{ r.filename }}</div>
          <div class="res-size">{{ formatSize(r.file_size) }} · {{ fmt(r.created_at) }}</div>
        </div>
        <a :href="`/api/v1/resources/${r.id}/download`" class="download-btn" download>
          <el-icon><Download /></el-icon> 下载
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const courses = ref<any[]>([])
const resources = ref<any[]>([])
const selectedCourse = ref<number|null>(null)

const fmt = (d: string) => new Date(d).toLocaleDateString('zh-CN')
const formatSize = (bytes: number) => bytes < 1024*1024 ? `${Math.round(bytes/1024)}KB` : `${(bytes/1024/1024).toFixed(1)}MB`

async function load() {
  if (!selectedCourse.value) return
  try { const r = await axios.get(`/api/v1/resources/?course_id=${selectedCourse.value}`); resources.value = r.data } catch {}
}

onMounted(async () => {
  try {
    const c = await axios.get('/api/v1/courses/my')
    courses.value = c.data
    if (c.data.length) { selectedCourse.value = c.data[0].id; await load() }
  } catch {}
})
</script>

<style scoped>
.page { padding: 32px; }
.page-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.empty { text-align: center; color: var(--text-secondary); padding: 60px; font-size: 15px; }
.resources-list { display: flex; flex-direction: column; gap: 10px; }
.res-card { display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(99,102,241,0.12); border-radius: 14px; padding: 14px 20px; }
.res-icon { font-size: 24px; color: #6366f1; }
.res-info { flex: 1; }
.res-name { font-size: 14px; font-weight: 600; color: var(--text-main); }
.res-size { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.download-btn { display: flex; align-items: center; gap: 6px; background: rgba(99,102,241,0.12); color: #818cf8; border-radius: 10px; padding: 8px 14px; text-decoration: none; font-size: 13px; font-weight: 600; border: 1px solid rgba(99,102,241,0.2); transition: all 0.18s; }
.download-btn:hover { background: rgba(99,102,241,0.2); }
</style>
