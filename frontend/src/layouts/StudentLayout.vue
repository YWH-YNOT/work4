<template>
  <div class="layout-wrap">
    <aside class="sidebar">
      <div class="brand-header">
        <div class="guet-logo">GUET</div>
        <div class="eea-text">电子工程与自动化学院</div>
      </div>

      <div class="brand">
        <div class="brand-name">智能教学平台</div>
        <div class="brand-role student">学生端</div>
      </div>

      <nav class="nav">
        <section v-for="group in navGroups" :key="group.title" class="nav-group">
          <div class="nav-group-head">
            <span>{{ group.title }}</span>
            <small>{{ group.subtitle }}</small>
          </div>
          <router-link v-for="item in group.items" :key="item.to" :to="item.to" class="nav-item">
            <el-icon><component :is="item.icon" /></el-icon>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </section>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar student">{{ auth.user?.username?.charAt(0).toUpperCase() }}</div>
          <div>
            <div class="username">{{ auth.user?.username }}</div>
            <div class="user-role">
              学生 · <router-link to="/student/profile" class="profile-link">个人中心</router-link>
            </div>
          </div>
        </div>
        <button @click="handleLogout" class="logout-btn" title="退出登录">
          <el-icon><SwitchButton /></el-icon>
        </button>
      </div>
    </aside>

    <main class="main-content">
      <div class="cyber-grid-bg"></div>
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

type NavItem = {
  to: string
  icon: string
  label: string
}

type NavGroup = {
  title: string
  subtitle: string
  items: NavItem[]
}

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}

const navGroups: NavGroup[] = [
  {
    title: 'AI助学',
    subtitle: '课程问答与知识追踪',
    items: [
      { to: '/student/chat', icon: 'ChatDotRound', label: 'AI课程问答' },
    ],
  },
  {
    title: '课堂表现智能分析',
    subtitle: '自动点名与课堂行为',
    items: [
      { to: '/student/posture', icon: 'DataLine', label: '我的课堂表现' },
      { to: '/student/attendance', icon: 'Check', label: '我的考勤记录' },
    ],
  },
  {
    title: '课程全过程考核与评价',
    subtitle: '学习任务、测验与成绩',
    items: [
      { to: '/student/dashboard', icon: 'House', label: '学习驾驶舱' },
      { to: '/student/timetable', icon: 'Calendar', label: '排课计划' },
      { to: '/student/course-progress', icon: 'DataAnalysis', label: '我的课程学情' },
      { to: '/student/analysis', icon: 'DataBoard', label: '我的AI学情分析' },
      { to: '/student/resources', icon: 'FolderOpened', label: '课程资源' },
      { to: '/student/assignments', icon: 'Document', label: '作业/实验/报告' },
      { to: '/student/quiz', icon: 'Memo', label: '课堂测验' },
      { to: '/student/discussions', icon: 'ChatRound', label: '课程讨论' },
      { to: '/student/grades', icon: 'TrophyBase', label: '成绩数据' },
    ],
  },
]
</script>

<style scoped>
.layout-wrap {
  display: flex;
  height: 100vh;
  background: #f3f8ff;
  font-family: 'Inter', system-ui, sans-serif;
}

.sidebar {
  width: 286px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #d8e7f8;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 8px 0 28px rgba(15, 47, 100, 0.08);
  z-index: 10;
}

.brand-header {
  padding: 22px 20px 14px;
  border-bottom: 1px solid #e4eef9;
  text-align: center;
}

.guet-logo {
  font-size: 26px;
  font-weight: 900;
  letter-spacing: 3px;
  color: #075da8;
  font-family: 'Roboto Mono', monospace;
}

.eea-text {
  font-size: 11px;
  color: #5b6f92;
  letter-spacing: 0;
  margin-top: 6px;
}

.brand {
  padding: 16px 20px;
  text-align: center;
  border-bottom: 1px solid #e4eef9;
}

.brand-name {
  font-weight: 900;
  font-size: 16px;
  color: #0f2f64;
  letter-spacing: 0;
}

.brand-role {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  margin-top: 8px;
  border-radius: 999px;
  padding: 3px 10px;
  background: #eaf3ff;
}

.brand-role.student {
  color: #075da8;
}

.nav {
  flex: 1;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.nav::-webkit-scrollbar {
  width: 4px;
}

.nav::-webkit-scrollbar-thumb {
  background: rgba(11, 99, 182, 0.24);
  border-radius: 2px;
}

.nav-group {
  border: 1px solid #dbeafa;
  border-radius: 10px;
  padding: 10px;
  background: linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
}

.nav-group-head {
  padding: 0 4px 8px;
  display: grid;
  gap: 2px;
  border-bottom: 1px solid #e4eef9;
  margin-bottom: 8px;
}

.nav-group-head span {
  color: #0f2f64;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.2;
}

.nav-group-head small {
  color: #6c7f9f;
  font-size: 10px;
  line-height: 1.4;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 9px 10px;
  border-radius: 8px;
  border: 1px solid transparent;
  color: #526783;
  text-decoration: none;
  font-size: 13px;
  font-weight: 800;
  transition: all 0.18s;
}

.nav-item:hover {
  background: #eef6ff;
  color: #0f2f64;
  border-color: #d7e7f8;
}

.nav-item.router-link-active {
  background: #e7f2ff;
  color: #075da8;
  border-color: #b8d8f8;
  box-shadow: inset 3px 0 0 #0b63b6;
}

.nav-item .el-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: #0b63b6;
}

.nav-label {
  flex: 1;
  min-width: 0;
  letter-spacing: 0;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 16px;
  border-top: 1px solid #e4eef9;
  background: #f7fbff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.avatar.student {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #0b63b6;
  border: 1px solid #0b63b6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 900;
  font-size: 16px;
  flex-shrink: 0;
}

.username {
  font-size: 13px;
  font-weight: 800;
  color: #0f2f64;
  font-family: 'Inter', system-ui, sans-serif;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 155px;
}

.user-role {
  font-size: 11px;
  color: #5b6f92;
  margin-top: 2px;
  display: flex;
  gap: 4px;
  align-items: center;
}

.profile-link {
  color: #0b63b6;
  text-decoration: none;
  font-size: 11px;
  transition: color .2s;
}

.profile-link:hover {
  color: #053b7a;
  text-decoration: underline;
}

.logout-btn {
  background: #fff4f2;
  border: 1px solid #ffd5cf;
  color: #cf3434;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.18s;
  flex-shrink: 0;
}

.logout-btn:hover {
  background: #ffe9e5;
  border-color: #f3a59b;
}

.main-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #f7fbff 0%, #edf5ff 100%);
}

.cyber-grid-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(11, 99, 182, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11, 99, 182, 0.045) 1px, transparent 1px);
  background-size: 30px 30px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
  -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
}

.content-wrapper {
  position: relative;
  height: 100%;
  overflow-y: auto;
  z-index: 1;
}

.content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: rgba(11, 99, 182, 0.28);
  border-radius: 3px;
}
</style>
