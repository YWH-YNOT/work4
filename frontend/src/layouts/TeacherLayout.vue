<template>
  <div class="layout-wrap">
    <!-- Cyber Sidebar -->
    <aside class="sidebar">
      <!-- GUET Header -->
      <div class="brand-header">
        <div class="guet-logo">GUET</div>
        <div class="eea-text">电子工程与自动化学院</div>
      </div>
      
      <div class="brand">
        <div class="brand-name">AI 智能教学平台</div>
        <div class="brand-role teacher">教师端</div>
      </div>

      <nav class="nav">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <el-icon><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
          <div class="nav-glow"></div>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar teacher">{{ auth.user?.username?.charAt(0).toUpperCase() }}</div>
          <div>
            <div class="username">{{ auth.user?.username }}</div>
            <div class="user-role">
              教师 · <router-link to="/teacher/profile" class="profile-link">个人中心</router-link>
            </div>
          </div>
        </div>
        <button @click="handleLogout" class="logout-btn" title="断开连接">
          <el-icon><SwitchButton /></el-icon>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
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

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}

const navItems = [
  { to: '/teacher/dashboard', icon: 'House', label: '指挥中心' },
  { to: '/teacher/posture', icon: 'View', label: '姿态监控' },
  { to: '/teacher/courses', icon: 'Collection', label: '矩阵管理' },
  { to: '/teacher/assignments', icon: 'Document', label: '作业布控' },
  { to: '/teacher/quiz', icon: 'Memo', label: '考核配置' },
  { to: '/teacher/resources', icon: 'FolderOpened', label: '资源引擎' },
  { to: '/teacher/attendance', icon: 'Check', label: '考勤监控' },
  { to: '/teacher/grades', icon: 'TrophyBase', label: '学情分析' },
  { to: '/teacher/announcements', icon: 'Bell', label: '全局广播' },
  { to: '/teacher/discussions', icon: 'ChatRound', label: '研讨中心' },
  { to: '/teacher/logs', icon: 'DataLine', label: '终端日志' },
]
</script>

<style scoped>
.layout-wrap { 
  display: flex; height: 100vh; background: #030712; 
  font-family: 'Inter', system-ui, sans-serif; 
}

/* Sidebar */
.sidebar {
  width: 250px; flex-shrink: 0; background: rgba(2, 6, 23, 0.95);
  border-right: 1px solid rgba(16, 185, 129, 0.2); 
  display: flex; flex-direction: column; position: relative;
  box-shadow: 5px 0 30px rgba(16, 185, 129, 0.05);
  z-index: 10;
}

.brand-header {
  padding: 24px 20px 16px; 
  border-bottom: 1px dashed rgba(16, 185, 129, 0.2);
  text-align: center;
}
.guet-logo {
  font-size: 24px; font-weight: 900; letter-spacing: 3px; color: var(--text-main);
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.8); font-family: 'Roboto Mono', monospace;
}
.eea-text {
  font-size: 10px; color: #6ee7b7; letter-spacing: 1px; margin-top: 6px; opacity: 0.8;
  font-family: 'Roboto Mono', monospace;
}

.brand {
  padding: 20px; text-align: center;
  border-bottom: 1px solid rgba(16, 185, 129, 0.1);
}
.brand-name { font-weight: 800; font-size: 15px; color: var(--text-main); letter-spacing: 1px; }
.brand-role { 
  font-size: 10px; font-weight: 700; letter-spacing: 1.5px; 
  margin-top: 4px; font-family: 'Roboto Mono', monospace; 
}
.brand-role.teacher { color: #10b981; }

.nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.nav::-webkit-scrollbar { width: 4px; }
.nav::-webkit-scrollbar-thumb { background: rgba(16, 185, 129, 0.3); border-radius: 2px; }

.nav-item {
  position: relative; overflow: hidden;
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 8px; border: 1px solid transparent;
  color: var(--text-secondary); text-decoration: none; font-size: 13px; font-weight: 600;
  transition: all 0.3s;
  font-family: 'Roboto Mono', monospace;
}
.nav-item::before {
  content: ''; position: absolute; left: 0; top: 0; height: 100%; width: 2px;
  background: transparent; transition: background 0.3s;
}
.nav-item:hover { 
  background: rgba(16, 185, 129, 0.05); color: var(--text-main); 
  border-color: rgba(16, 185, 129, 0.3);
}
.nav-item.router-link-active { 
  background: rgba(16, 185, 129, 0.1); color: #34d399; 
  border-color: rgba(16, 185, 129, 0.4); box-shadow: 0 0 15px rgba(16, 185, 129, 0.1) inset;
}
.nav-item.router-link-active::before { background: #10b981; box-shadow: 0 0 10px #10b981; }

.nav-item .el-icon { font-size: 16px; flex-shrink: 0; color: #10b981; }
.nav-label { flex: 1; letter-spacing: 0.5px; }

.sidebar-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px; border-top: 1px solid rgba(16, 185, 129, 0.2);
  background: rgba(2, 6, 23, 0.8);
}
.user-info { display: flex; align-items: center; gap: 12px; }
.avatar.teacher {
  width: 36px; height: 36px; border-radius: 8px;
  background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-main); font-weight: 800; font-size: 16px;
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}
.username { font-size: 13px; font-weight: 700; color: var(--text-main); font-family: 'Roboto Mono', monospace;}
.user-role { font-size: 11px; color: #10b981; margin-top: 2px; display: flex; gap: 4px; align-items: center; }
.profile-link { color: #10b981; text-decoration: none; font-size: 11px; transition: color .2s; }
.profile-link:hover { color: #34d399; text-decoration: underline; }

.logout-btn {
  background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); 
  color: #fca5a5; cursor: pointer; padding: 8px; border-radius: 8px; transition: all 0.3s;
}
.logout-btn:hover { background: rgba(239, 68, 68, 0.2); border-color: #ef4444; box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }

/* Main Content */
.main-content {
  flex: 1; position: relative; overflow: hidden;
  background: radial-gradient(ellipse at 80% 20%, #061f1a 0%, #030712 100%);
}

.cyber-grid-bg {
  position: absolute; inset: 0; pointer-events: none;
  background-image: 
    linear-gradient(rgba(16, 185, 129, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
  -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%);
}

.content-wrapper {
  position: relative; height: 100%; overflow-y: auto; z-index: 1;
}
.content-wrapper::-webkit-scrollbar { width: 6px; }
.content-wrapper::-webkit-scrollbar-thumb { background: rgba(16, 185, 129, 0.3); border-radius: 3px; }
</style>
