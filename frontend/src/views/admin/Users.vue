<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
    </div>
    <div class="filter-bar">
      <input v-model="search" placeholder="搜索用户名..." class="search-inp" @input="load"/>
      <select v-model="roleFilter" @change="load" class="sel">
        <option value="">所有角色</option>
        <option value="student">学生</option>
        <option value="teacher">教师</option>
        <option value="admin">管理员</option>
      </select>
    </div>
    <table class="users-table">
      <thead>
        <tr><th>ID</th><th>用户名</th><th>全名</th><th>邮箱</th><th>角色</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="u in filteredUsers" :key="u.id">
          <td class="id-cell">{{ u.id }}</td>
          <td class="name-cell"><div class="avatar-sm">{{ u.username.charAt(0).toUpperCase() }}</div>{{ u.username }}</td>
          <td>{{ u.full_name || '-' }}</td>
          <td>{{ u.email || '-' }}</td>
          <td><span class="badge" :class="u.role">{{ {'student':'学生','teacher':'教师','admin':'管理员'}[u.role] }}</span></td>
          <td><span class="status" :class="u.is_active?'active':'inactive'">{{ u.is_active?'正常':'禁用' }}</span></td>
          <td class="actions">
            <button @click="toggleUser(u)" class="action-btn toggle" :title="u.is_active?'禁用':'激活'">
              <el-icon><component :is="u.is_active?'Close':'Check'" /></el-icon>
            </button>
            <button @click="deleteUser(u.id)" class="action-btn delete" title="删除">
              <el-icon><Delete /></el-icon>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const users = ref<any[]>([])
const search = ref('')
const roleFilter = ref('')

const filteredUsers = computed(() => {
  let list = users.value
  if (search.value) list = list.filter(u => u.username.includes(search.value))
  if (roleFilter.value) list = list.filter(u => u.role === roleFilter.value)
  return list
})

async function load() { try { const r = await axios.get('/api/v1/admin/users'); users.value = r.data } catch {} }
async function deleteUser(id: number) {
  if (!confirm('确认删除该用户吗？')) return
  try { await axios.delete(`/api/v1/admin/users/${id}`); await load() } catch(e:any) { alert(e.response?.data?.detail || '删除失败') }
}
async function toggleUser(u: any) {
  try { await axios.patch(`/api/v1/admin/users/${u.id}/toggle`); u.is_active = !u.is_active } catch {}
}

onMounted(load)
</script>

<style scoped>
.page { padding: 32px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 800; color: var(--text-main); margin: 0; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.search-inp, .sel { background: rgba(255,255,255,0.05); border: 1px solid rgba(245,158,11,0.2); border-radius: 10px; padding: 8px 14px; color: var(--text-main); font-size: 14px; outline: none; }
.search-inp { flex: 1; }
.users-table { width: 100%; border-collapse: collapse; }
.users-table th { text-align: left; padding: 12px 14px; font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(245,158,11,0.1); }
.users-table td { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; color: var(--text-secondary); }
.users-table tr:hover td { background: rgba(245,158,11,0.03); }
.id-cell { color: var(--text-secondary); font-size: 12px; }
.name-cell { display: flex; align-items: center; gap: 8px; color: var(--text-main); font-weight: 500; }
.avatar-sm { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #d97706, #f59e0b); color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.badge { font-size: 12px; padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.badge.student { background: rgba(99,102,241,0.15); color: #818cf8; }
.badge.teacher { background: rgba(16,185,129,0.15); color: #34d399; }
.badge.admin { background: rgba(245,158,11,0.15); color: #fbbf24; }
.status { font-size: 12px; font-weight: 600; }
.status.active { color: #34d399; }
.status.inactive { color: #f87171; }
.actions { display: flex; gap: 6px; }
.action-btn { width: 30px; height: 30px; border-radius: 8px; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.18s; }
.action-btn.toggle { background: rgba(245,158,11,0.1); color: #fbbf24; }
.action-btn.toggle:hover { background: rgba(245,158,11,0.2); }
.action-btn.delete { background: rgba(239,68,68,0.1); color: #f87171; }
.action-btn.delete:hover { background: rgba(239,68,68,0.2); }
</style>
