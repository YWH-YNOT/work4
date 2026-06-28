<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">我的授课课程</h1>
        <p class="page-sub">课程、选课和授课关系由管理员导入。教师端用于查看课程、维护资源、重建 RAG 和查看知识图谱。</p>
      </div>
      <button class="ghost-btn" @click="load" :disabled="loading">
        <el-icon><Refresh /></el-icon>
        {{ loading ? '刷新中' : '刷新课程' }}
      </button>
    </div>

    <div class="notice-band">
      <strong>数据来源</strong>
      <span>学生名单、选课表和授课表由管理员在“课程与教务数据”中统一导入，教师端不再直接创建或导入学生。</span>
    </div>

    <div class="courses-grid">
      <article v-for="course in courses" :key="course.id" class="course-card">
        <div class="course-top">
          <div class="course-avatar">{{ initial(course.name) }}</div>
          <span class="course-status">授课中</span>
        </div>
        <h2>{{ course.name }}</h2>
        <p class="course-code">{{ course.course_code || '未设置课程代码' }}</p>
        <p class="course-desc">{{ course.description || '暂无课程简介，管理员导入教学大纲后可在课程知识库补充。' }}</p>
        <div class="course-actions">
          <button class="small-btn" @click="router.push('/teacher/resources')">课程知识库</button>
          <button class="small-btn" @click="router.push('/teacher/course-progress')">课程学情</button>
          <button v-if="isAutoTest(course)" class="small-btn primary" @click="reindexRag(course)">重建 RAG</button>
          <button v-if="isAutoTest(course)" class="small-btn" @click="seedGraph(course)">初始化图谱</button>
          <button v-if="isAutoTest(course)" class="small-btn" @click="router.push('/teacher/knowledge')">查看图谱</button>
        </div>
      </article>
      <div v-if="!loading && courses.length === 0" class="empty">
        暂无授课课程，请联系管理员导入授课表。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const courses = ref<any[]>([])
const loading = ref(false)

const initial = (name: string) => (name || '课').slice(0, 1)
const isAutoTest = (course: any) => String(course.name || '').includes('自动测试系统')

async function load() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/courses/my')
    courses.value = res.data || []
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '课程加载失败')
  } finally {
    loading.value = false
  }
}

async function reindexRag(course: any) {
  try {
    const res = await axios.post(`/api/v1/rag/courses/${course.id}/reindex`)
    ElMessage.success(`RAG 已重建：${res.data.indexed_resources} 个资源，${res.data.indexed_chunks} 个片段`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || 'RAG 重建失败')
  }
}

async function seedGraph(course: any) {
  try {
    const res = await axios.post(`/api/v1/knowledge/courses/${course.id}/seed-auto-test-system`)
    ElMessage.success(`知识图谱已初始化：${res.data.nodes} 个节点，${res.data.edges} 条关系`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '知识图谱初始化失败')
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 32px; color: #0f2f64; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 16px; }
.page-title { font-size: 28px; font-weight: 900; color: #0f2f64; margin: 0; }
.page-sub { color: #5b6f92; font-size: 13px; line-height: 1.6; margin: 6px 0 0; }
.ghost-btn { display: inline-flex; align-items: center; gap: 6px; background: #ffffff; color: #0b63b6; border: 1px solid #c8ddf4; border-radius: 8px; padding: 9px 14px; cursor: pointer; font-weight: 800; white-space: nowrap; }
.ghost-btn:disabled { opacity: .55; cursor: wait; }
.notice-band { display: flex; align-items: center; gap: 10px; background: #ffffff; border: 1px solid #d9e7f7; border-radius: 9px; padding: 12px 14px; margin-bottom: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.05); }
.notice-band strong { color: #0b63b6; }
.notice-band span { color: #5b6f92; font-size: 13px; line-height: 1.5; }
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.course-card { background: #ffffff; border: 1px solid #d9e7f7; border-radius: 10px; padding: 18px; box-shadow: 0 10px 24px rgba(15,47,100,.06); min-height: 230px; display: flex; flex-direction: column; }
.course-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.course-avatar { width: 44px; height: 44px; border-radius: 9px; background: #eaf3ff; color: #0b63b6; border: 1px solid #c8ddf4; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 18px; }
.course-status { color: #0b7d56; background: #e8f7f0; border: 1px solid #b6e6ce; border-radius: 999px; padding: 4px 9px; font-size: 12px; font-weight: 800; }
.course-card h2 { font-size: 17px; font-weight: 900; color: #0f2f64; margin: 0; line-height: 1.35; }
.course-code { font-size: 12px; color: #5b6f92; margin: 5px 0 0; }
.course-desc { font-size: 13px; color: #5b6f92; margin: 10px 0 0; line-height: 1.65; min-height: 66px; }
.course-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: auto; padding-top: 14px; }
.small-btn { border: 1px solid #c8ddf4; background: #f8fbff; color: #0b63b6; border-radius: 7px; padding: 7px 10px; cursor: pointer; font-weight: 800; font-size: 12px; }
.small-btn.primary { background: #0b63b6; border-color: #0b63b6; color: #ffffff; }
.small-btn:hover, .ghost-btn:hover { filter: brightness(.98); }
.empty { grid-column: 1 / -1; text-align: center; color: #5b6f92; padding: 60px; background: #ffffff; border: 1px dashed #c8ddf4; border-radius: 10px; }
@media (max-width: 760px) {
  .page { padding: 20px; }
  .page-header, .notice-band { flex-direction: column; align-items: flex-start; }
}
</style>
