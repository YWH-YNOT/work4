<template>
  <div class="page">
    <div class="page-header-row">
      <h1 class="page-title">我的课程</h1>
      <button @click="showCreate=true" class="create-btn"><el-icon><Plus /></el-icon> 创建课程</button>
    </div>
    <div class="courses-grid">
      <div v-for="c in courses" :key="c.id" class="course-card">
        <div class="course-avatar">{{ c.name.charAt(0) }}</div>
        <div class="course-name">{{ c.name }}</div>
        <div class="course-code">{{ c.course_code || '无课号' }}</div>
        <div class="course-desc">{{ c.description || '暂无描述' }}</div>
        <button @click="deleteCourse(c.id)" class="del-btn"><el-icon><Delete /></el-icon></button>
      </div>
      <div v-if="courses.length===0" class="empty">暂无课程，点击创建第一门课</div>
    </div>
    <el-dialog v-model="showCreate" title="创建新课程" width="440px">
      <div class="dialog-form">
        <label>课程名称</label><input v-model="newCourse.name" class="inp" placeholder="例如：高等数学A"/>
        <label>课程代号</label><input v-model="newCourse.course_code" class="inp" placeholder="例如：2523114"/>
        <label>课程简介</label><textarea v-model="newCourse.description" class="ta" rows="3" placeholder="课程简介（选填）"></textarea>
        <div class="dialog-actions">
          <button @click="showCreate=false" class="cancel-btn">取消</button>
          <button @click="createCourse" class="confirm-btn">创建</button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const courses = ref<any[]>([])
const showCreate = ref(false)
const newCourse = ref({ name: '', course_code: '', description: '' })

async function load() {
  try { const r = await axios.get('/api/v1/courses/my'); courses.value = r.data }
  catch { ElMessage.error('加载课程列表失败') }
}

async function createCourse() {
  if (!newCourse.value.name.trim()) { ElMessage.warning('请输入课程名称'); return }
  try {
    await axios.post('/api/v1/courses/', newCourse.value)
    showCreate.value = false
    newCourse.value = { name: '', course_code: '', description: '' }
    ElMessage.success('课程创建成功')
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败，请重试')
  }
}

async function deleteCourse(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这门课程？相关数据将一并清除。', '删除课程', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
    await axios.delete(`/api/v1/courses/${id}`)
    ElMessage.success('课程已删除')
    await load()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}
onMounted(load)
</script>

<style scoped>
.page { padding: 32px; }
.page-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.create-btn { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; border-radius: 12px; padding: 10px 20px; cursor: pointer; font-weight: 600; }
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.course-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(16,185,129,0.15); border-radius: 16px; padding: 20px; position: relative; }
.course-avatar { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #059669, #10b981); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; margin-bottom: 12px; }
.course-name { font-size: 15px; font-weight: 700; color: var(--text-main); }
.course-code { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.course-desc { font-size: 13px; color: var(--text-secondary); margin-top: 8px; line-height: 1.5; }
.del-btn { position: absolute; top: 12px; right: 12px; background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 4px; border-radius: 6px; transition: all 0.18s; font-size: 16px; }
.del-btn:hover { background: rgba(239,68,68,0.1); color: #f87171; }
.empty { grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 60px; }
.dialog-form { display: flex; flex-direction: column; gap: 10px; }
.dialog-form label { font-size: 13px; color: var(--text-secondary); font-weight: 600; }
.inp { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; width: 100%; }
.ta { background: rgba(255,255,255,0.05); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; color: var(--text-main); font-size: 14px; outline: none; resize: vertical; width: 100%; }
.dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
.cancel-btn { padding: 8px 20px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary); cursor: pointer; }
.confirm-btn { padding: 8px 20px; border-radius: 10px; background: linear-gradient(135deg, #059669, #10b981); border: none; color: white; cursor: pointer; font-weight: 600; }
</style>
