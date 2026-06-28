<template>
  <div class="auth-container">
    <div class="campus-bg"></div>

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
        <h1 class="logo-title">智能教学平台</h1>
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

        <div v-if="error" class="error-msg">{{ error }}</div>

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
    const target = data.username === 'classroom_demo'
      ? '/teacher/posture'
      : (portals[data.role] || '/student/dashboard')
    router.push(target)
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
  background:
    linear-gradient(180deg, rgba(238, 247, 255, 0.96), rgba(248, 252, 255, 0.98)),
    radial-gradient(circle at 20% 12%, rgba(11, 99, 182, 0.16), transparent 24%);
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
  background: #ffffff; border: 1px solid #c8ddf4;
  color: #0b63b6; border-radius: 10px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 50; transition: all 0.2s ease;
  box-shadow: 0 10px 28px rgba(15,47,100,0.1);
}
.theme-toggle:hover { background: #eef6ff; transform: translateY(-1px); }
.theme-toggle .el-icon { font-size: 20px; }

.campus-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(rgba(11, 99, 182, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11, 99, 182, 0.045) 1px, transparent 1px);
  background-size: 34px 34px;
  pointer-events: none;
}

.auth-card {
  background: #ffffff;
  border: 1px solid #d9e7f7;
  border-radius: 10px;
  padding: 48px 40px;
  width: 440px;
  box-shadow: 0 24px 60px rgba(15, 47, 100, 0.14);
  position: relative;
  z-index: 10;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: -1px; left: 10%; width: 80%; height: 2px;
  background: linear-gradient(90deg, transparent, #0b63b6, transparent);
}

.brand-header {
  text-align: center;
  margin-bottom: 32px;
}
.guet-logo {
  font-size: 28px;
  font-weight: 900;
  letter-spacing: 4px;
  color: #075da8;
  font-family: 'Roboto Mono', monospace;
}
.eea-text {
  font-size: 12px;
  color: #5b6f92;
  letter-spacing: 0;
  margin-top: 6px;
}

.logo-block { text-align: center; margin-bottom: 40px; }
.logo-title {
  font-size: 22px;
  font-weight: 800;
  color: #0f2f64;
  margin: 0;
}
.logo-sub { color: var(--text-secondary); font-size: 12px; margin-top: 6px; font-family: 'Roboto Mono', monospace; letter-spacing: 0.5px; }

.auth-form { display: flex; flex-direction: column; gap: 20px; }
.field label { display: block; font-size: 13px; font-weight: 700; color: #0f2f64; margin-bottom: 8px; letter-spacing: 0; }

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fbff;
  border: 1px solid #c8ddf4;
  border-radius: 8px;
  padding: 14px 16px;
  transition: all 0.3s;
  overflow: hidden;
}
.input-glow {
  position: absolute; bottom: 0; left: 0; height: 2px; width: 0;
  background: #0b63b6; transition: width 0.3s ease;
}
.input-wrap:focus-within {
  border-color: #0b63b6;
  background: #ffffff;
}
.input-wrap:focus-within .input-glow { width: 100%; }

.input-wrap .el-icon { color: #0b63b6; font-size: 16px; flex-shrink: 0; }
.input-wrap input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #0f2f64;
  font-size: 15px;
  font-family: 'Roboto Mono', monospace;
}
.input-wrap input::placeholder { color: #90a4c1; font-family: 'Inter', sans-serif; }

.error-msg {
  background: #fff4f2;
  border: 1px solid #ffd5cf;
  color: #cf3434;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}

.btn-primary {
  background: #0b63b6;
  color: #ffffff;
  border: 1px solid #0b63b6;
  border-radius: 8px;
  padding: 16px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s;
  letter-spacing: 0;
  margin-top: 8px;
  position: relative;
  overflow: hidden;
  text-align: center;
}
.btn-primary::before {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.28), transparent);
  transition: left 0.5s ease;
}
.btn-primary:hover:not(:disabled) {
  background: #075da8;
  box-shadow: 0 12px 24px rgba(11, 99, 182, 0.22);
}
.btn-primary:hover:not(:disabled)::before { left: 100%; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sys-text { font-family: 'Inter', system-ui, sans-serif; }

.separator {
  position: relative; text-align: center; margin: 32px 0;
}
.separator::before {
  content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 1px;
  background: #d9e7f7;
}
.separator span {
  position: relative; background: #ffffff; padding: 0 16px; font-size: 12px; color: #5b6f92;
}

.auth-switch {
  text-align: center;
  color: #5b6f92;
  font-size: 13px;
}
.auth-switch a { color: #0b63b6; text-decoration: none; font-weight: 700; transition: color 0.2s; }
.auth-switch a:hover { color: #053b7a; text-decoration: underline; }
</style>
