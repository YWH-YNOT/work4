<template>
  <div class="auth-container">
    <div class="cyber-grid"></div>

    <!-- Theme Toggle -->
    <button class="theme-toggle" @click="toggleTheme" :title="isLightMode ? '切换到深色模式' : '切换到浅色模式'">
      <el-icon v-if="isLightMode"><Moon /></el-icon>
      <el-icon v-else><Sunny /></el-icon>
    </button>

    <div class="auth-card">
      <!-- GUET & EEA Branding -->
      <div class="brand-header">
        <div class="guet-logo">GUET</div>
        <div class="eea-text">桂林电子科技大学 · 电子工程与自动化学院</div>
      </div>

      <div class="logo-block">
        <h1 class="logo-title">AI 智能教学平台</h1>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="field">
          <label>统一身份认证</label>
          <div class="input-wrap">
            <el-icon><User /></el-icon>
            <input v-model="form.username" placeholder="输入学工号/用户名" required autocomplete="username" />
            <div class="input-glow"></div>
          </div>
        </div>
        <div class="field">
          <label>认证密码</label>
          <div class="input-wrap">
            <el-icon><Lock /></el-icon>
            <input v-model="form.password" type="password" placeholder="输入密码" required autocomplete="current-password"/>
            <div class="input-glow"></div>
          </div>
        </div>

        <div v-if="error" class="error-msg">⚠ {{ error }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="loading" class="sys-text">登录中...</span>
          <span v-else class="sys-text">登 录</span>
        </button>
      </form>

      <div class="separator">
        <span>或</span>
      </div>

      <p class="auth-switch">
        未注册账号？
        <router-link to="/register">申请接入网络 →</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const isLightMode = ref(localStorage.getItem('theme') === 'light')
function toggleTheme() {
  isLightMode.value = !isLightMode.value
  const theme = isLightMode.value ? 'light' : 'dark'
  localStorage.setItem('theme', theme)
  document.documentElement.className = theme === 'light' ? 'light-mode' : ''
}

onMounted(() => {
  if (isLightMode.value) document.documentElement.className = 'light-mode'
})

const router = useRouter()
const auth = useAuthStore()

const form = ref({ username: '', password: '' })
const error = ref('')
const loading = ref(false)

const portals: Record<string, string> = {
  student: '/student/dashboard',
  teacher: '/teacher/dashboard',
  admin: '/admin/dashboard',
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  // 登录前先删除旧的 Authorization header，防止旧 token 干扰登录接口
  delete axios.defaults.headers.common['Authorization']
  try {
    const params = new URLSearchParams()
    params.append('username', form.value.username)
    params.append('password', form.value.password)
    const { data } = await axios.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    const meRes = await axios.get('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${data.access_token}` }
    })
    auth.setAuth(data.access_token, meRes.data)
    router.push(portals[data.role] || '/student/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败，请检查账户凭证'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: radial-gradient(ellipse at 50% 50%, #081121 0%, #030712 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text-main);
}

/* Theme Toggle Button */
.theme-toggle {
  position: absolute; top: 24px; right: 24px; width: 44px; height: 44px;
  background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.3);
  color: #06b6d4; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 50; transition: all 0.3s ease; backdrop-filter: blur(10px);
}
.theme-toggle:hover { background: rgba(6, 182, 212, 0.2); transform: scale(1.05); box-shadow: 0 0 15px rgba(6, 182, 212, 0.3); }
.theme-toggle .el-icon { font-size: 20px; }

/* Cyber Grid */
.cyber-grid {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(rgba(6, 182, 212, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(6, 182, 212, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  transform: perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px);
  animation: gridMove 20s linear infinite;
  pointer-events: none;
}
@keyframes gridMove {
  0% { background-position: 0 0; }
  100% { background-position: 0 40px; }
}

.auth-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(6, 182, 212, 0.3);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 48px 40px;
  width: 440px;
  box-shadow: 0 0 80px rgba(6, 182, 212, 0.1), 0 0 0 1px rgba(6, 182, 212, 0.1) inset;
  position: relative;
  z-index: 10;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: -1px; left: 10%; width: 80%; height: 2px;
  background: linear-gradient(90deg, transparent, #06b6d4, transparent);
}

.brand-header {
  text-align: center;
  margin-bottom: 32px;
}
.guet-logo {
  font-size: 28px;
  font-weight: 900;
  letter-spacing: 4px;
  color: var(--text-main);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.8), 0 0 20px rgba(6, 182, 212, 0.4);
  font-family: 'Roboto Mono', monospace;
}
.eea-text {
  font-size: 12px;
  color: #67e8f9;
  letter-spacing: 1px;
  margin-top: 6px;
  opacity: 0.8;
}

.logo-block { text-align: center; margin-bottom: 40px; }
.logo-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}
.logo-sub { color: var(--text-secondary); font-size: 12px; margin-top: 6px; font-family: 'Roboto Mono', monospace; letter-spacing: 0.5px; }

.auth-form { display: flex; flex-direction: column; gap: 20px; }
.field label { display: block; font-size: 11px; font-weight: 600; color: #22d3ee; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(2, 6, 23, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  padding: 14px 16px;
  transition: all 0.3s;
  overflow: hidden;
}
.input-glow {
  position: absolute; bottom: 0; left: 0; height: 2px; width: 0;
  background: #06b6d4; transition: width 0.3s ease;
}
.input-wrap:focus-within {
  border-color: rgba(6, 182, 212, 0.5);
  background: rgba(2, 6, 23, 0.8);
}
.input-wrap:focus-within .input-glow { width: 100%; box-shadow: 0 0 10px #06b6d4; }

.input-wrap .el-icon { color: #06b6d4; font-size: 16px; flex-shrink: 0; }
.input-wrap input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-main);
  font-size: 15px;
  font-family: 'Roboto Mono', monospace;
}
.input-wrap input::placeholder { color: var(--text-secondary); font-family: 'Inter', sans-serif; }

.error-msg {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}

.btn-primary {
  background: rgba(6, 182, 212, 0.1);
  color: var(--text-main);
  border: 1px solid #06b6d4;
  border-radius: 8px;
  padding: 16px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 2px;
  margin-top: 8px;
  position: relative;
  overflow: hidden;
  text-align: center;
}
.btn-primary::before {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.4), transparent);
  transition: left 0.5s ease;
}
.btn-primary:hover:not(:disabled) {
  background: rgba(6, 182, 212, 0.2);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.4);
}
.btn-primary:hover:not(:disabled)::before { left: 100%; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sys-text { font-family: 'Roboto Mono', monospace; }

.separator {
  position: relative; text-align: center; margin: 32px 0;
}
.separator::before {
  content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 1px;
  background: rgba(148, 163, 184, 0.2);
}
.separator span {
  position: relative; background: #0f172a; padding: 0 16px; font-size: 12px; color: var(--text-secondary); font-family: 'Roboto Mono', monospace;
}

.auth-switch {
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}
.auth-switch a { color: #22d3ee; text-decoration: none; font-weight: 600; transition: color 0.3s; }
.auth-switch a:hover { color: #67e8f9; text-shadow: 0 0 8px rgba(34, 211, 238, 0.6); }
</style>
