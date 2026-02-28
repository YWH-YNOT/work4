<template>
  <div class="auth-container">
    <div class="cyber-grid"></div>

    <!-- Theme Toggle -->
    <button class="theme-toggle" @click="toggleTheme" :title="isLightMode ? '切换到深色模式' : '切换到浅色模式'">
      <el-icon v-if="isLightMode"><Moon /></el-icon>
      <el-icon v-else><Sunny /></el-icon>
    </button>

    <div class="auth-card">
      <div class="brand-header">
        <div class="guet-logo">GUET</div>
        <div class="eea-text">桂林电子科技大学 · 电子工程与自动化学院</div>
      </div>

      <div class="logo-block">
        <h1 class="logo-title">系统接入申请</h1>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="field">
          <label>分配标识符</label>
          <div class="input-wrap">
            <el-icon><User /></el-icon>
            <input v-model="form.username" placeholder="输入学工号/用户名" required />
            <div class="input-glow"></div>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="field">
            <label>实名记录</label>
            <div class="input-wrap">
              <el-icon><Avatar /></el-icon>
              <input v-model="form.full_name" placeholder="真实姓名 (选填)" />
              <div class="input-glow"></div>
            </div>
          </div>
          <div class="field">
            <label>通信邮箱</label>
            <div class="input-wrap">
              <el-icon><Message /></el-icon>
              <input v-model="form.email" type="email" placeholder="电子邮箱 (选填)" />
              <div class="input-glow"></div>
            </div>
          </div>
        </div>

        <div class="field">
          <label>授权密钥</label>
          <div class="input-wrap">
            <el-icon><Lock /></el-icon>
            <input v-model="form.password" type="password" placeholder="至少6位密码" required minlength="6"/>
            <div class="input-glow"></div>
          </div>
        </div>

        <div class="field">
          <label>系统角色</label>
          <div class="role-select">
            <button
              v-for="r in roles" :key="r.value" type="button"
              :class="['role-btn', form.role === r.value && 'active']"
              @click="form.role = r.value"
            >
              <el-icon><component :is="r.icon" /></el-icon>
              {{ r.label }}
            </button>
          </div>
        </div>

        <div v-if="error" class="error-msg">⚠ {{ error }}</div>
        <div v-if="success" class="success-msg">✓ {{ success }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="loading" class="sys-text">处理中...</span>
          <span v-else class="sys-text">立 即 注 册</span>
        </button>
      </form>

      <p class="auth-switch">
        已持有接入凭证？<router-link to="/login">返回登录矩阵 →</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
const form = ref({ username: '', password: '', full_name: '', email: '', role: 'student' })
const error = ref('')
const success = ref('')
const loading = ref(false)

const roles = [
  { value: 'student', label: '学生', icon: 'Reading' },
  { value: 'teacher', label: '教师', icon: 'Sugar' },
  { value: 'admin',   label: '管理', icon: 'Setting' },
]

async function handleRegister() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    const payload = {
      ...form.value,
      email: form.value.email.trim() || null,
      full_name: form.value.full_name.trim() || null,
    }
    await axios.post('/api/v1/auth/register', payload)
    success.value = '档案初始化成功！链路建立中，跳转登录...'
    setTimeout(() => router.push('/login'), 3000)
  } catch (e: any) {
    error.value = e.response?.data?.detail || '初始化失败，产生未定义错误'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: radial-gradient(ellipse at 50% 50%, #081121 0%, #030712 100%);
  display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden; font-family: 'Inter', system-ui, sans-serif;
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
  background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(6, 182, 212, 0.3);
  backdrop-filter: blur(20px); border-radius: 16px; padding: 40px;
  width: 520px; box-shadow: 0 0 80px rgba(6, 182, 212, 0.1), 0 0 0 1px rgba(6, 182, 212, 0.1) inset;
  position: relative; z-index: 10;
}
.auth-card::before {
  content: ''; position: absolute; top: -1px; left: 10%; width: 80%; height: 2px;
  background: linear-gradient(90deg, transparent, #06b6d4, transparent);
}

.brand-header { text-align: center; margin-bottom: 24px; }
.guet-logo {
  font-size: 24px; font-weight: 900; letter-spacing: 4px; color: var(--text-main);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.8); font-family: 'Roboto Mono', monospace;
}
.eea-text { font-size: 11px; color: #67e8f9; letter-spacing: 1px; margin-top: 4px; opacity: 0.8; }

.logo-block { text-align: center; margin-bottom: 30px; }
.logo-title { font-size: 20px; font-weight: 800; color: var(--text-main); margin: 0; }
.logo-sub { color: var(--text-secondary); font-size: 11px; margin-top: 6px; font-family: 'Roboto Mono', monospace; letter-spacing: 0.5px; }

.auth-form { display: flex; flex-direction: column; gap: 16px; }
.row-fields { display: flex; gap: 16px; }
.row-fields .field { flex: 1; }

.field label { display: block; font-size: 11px; font-weight: 600; color: #22d3ee; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }

.input-wrap {
  position: relative; display: flex; align-items: center; gap: 10px;
  background: rgba(2, 6, 23, 0.5); border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px; padding: 12px 14px; transition: all 0.3s; overflow: hidden;
}
.input-glow {
  position: absolute; bottom: 0; left: 0; height: 2px; width: 0;
  background: #06b6d4; transition: width 0.3s ease;
}
.input-wrap:focus-within { border-color: rgba(6, 182, 212, 0.5); background: rgba(2, 6, 23, 0.8); }
.input-wrap:focus-within .input-glow { width: 100%; box-shadow: 0 0 10px #06b6d4; }
.input-wrap .el-icon { color: #06b6d4; font-size: 16px; flex-shrink: 0; }
.input-wrap input { flex:1; background:none; border:none; outline:none; color: var(--text-main); font-size:14px; font-family: 'Roboto Mono', monospace; }
.input-wrap input::placeholder { color: var(--text-secondary); font-family: 'Inter', sans-serif; }

.role-select { display: flex; gap: 10px; }
.role-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px; background: rgba(2, 6, 23, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px;
  color: var(--text-secondary); cursor: pointer; transition: all 0.3s; font-size: 13px; font-weight: 600;
}
.role-btn.active { background: rgba(6, 182, 212, 0.15); border-color: #06b6d4; color: var(--text-main); box-shadow: 0 0 15px rgba(6, 182, 212, 0.2); }
.role-btn:hover { border-color: rgba(6, 182, 212, 0.5); color: var(--text-main); }

.error-msg { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 12px; border-radius: 8px; font-size: 13px; }
.success-msg { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 13px; }

.btn-primary {
  background: rgba(6, 182, 212, 0.1); color: var(--text-main); border: 1px solid #06b6d4;
  border-radius: 8px; padding: 16px; font-size: 14px; font-weight: 700; cursor: pointer;
  transition: all 0.3s; letter-spacing: 2px; margin-top: 8px; position: relative; overflow: hidden; text-align: center;
}
.btn-primary::before {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.4), transparent); transition: left 0.5s ease;
}
.btn-primary:hover:not(:disabled) { background: rgba(6, 182, 212, 0.2); box-shadow: 0 0 20px rgba(6, 182, 212, 0.4); }
.btn-primary:hover:not(:disabled)::before { left: 100%; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sys-text { font-family: 'Roboto Mono', monospace; }

.auth-switch { text-align: center; color: var(--text-secondary); font-size: 13px; margin-top: 24px; }
.auth-switch a { color: #22d3ee; text-decoration: none; font-weight: 600; transition: color 0.3s; }
.auth-switch a:hover { color: #67e8f9; text-shadow: 0 0 8px rgba(34, 211, 238, 0.6); }
</style>
