<template>
  <div class="auth-container">
    <div class="campus-bg"></div>

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

        <div v-if="error" class="error-msg">提示：{{ error }}</div>
        <div v-if="success" class="success-msg">完成：{{ success }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="loading" class="sys-text">处理中...</span>
          <span v-else class="sys-text">立即注册</span>
        </button>
      </form>

      <p class="auth-switch">
        已持有接入凭证？<router-link to="/login">返回登录</router-link>
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
  background:
    radial-gradient(circle at 18% 14%, rgba(52, 152, 219, 0.16), transparent 28%),
    linear-gradient(135deg, #f7fbff 0%, #eaf4ff 52%, #f8fbff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', system-ui, sans-serif;
  color: #0f2f64;
  padding: 32px 18px;
}

.theme-toggle {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  background: #ffffff;
  border: 1px solid #cfe3f8;
  color: #075da8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 50;
  transition: all 0.2s ease;
  box-shadow: 0 10px 24px rgba(15, 47, 100, 0.12);
}
.theme-toggle:hover { background: #eef7ff; transform: translateY(-1px); }
.theme-toggle .el-icon { font-size: 20px; }

.campus-bg {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(11, 99, 182, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(11, 99, 182, 0.055) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
}

.auth-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #d8e7f8;
  backdrop-filter: blur(16px);
  border-radius: 14px;
  padding: 38px;
  width: min(520px, 100%);
  box-shadow: 0 24px 60px rgba(15, 47, 100, 0.14);
  position: relative;
  z-index: 10;
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #075da8, #32a4ff, #7ac2ff);
  border-radius: 14px 14px 0 0;
}

.brand-header { text-align: center; margin-bottom: 24px; }
.guet-logo {
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 3px;
  color: #075da8;
  font-family: 'Roboto Mono', monospace;
}
.eea-text { font-size: 12px; color: #5b6f92; letter-spacing: 0; margin-top: 5px; }

.logo-block { text-align: center; margin-bottom: 30px; }
.logo-title { font-size: 22px; font-weight: 900; color: #0f2f64; margin: 0; }
.logo-sub { color: #5b6f92; font-size: 11px; margin-top: 6px; font-family: 'Roboto Mono', monospace; letter-spacing: 0; }

.auth-form { display: flex; flex-direction: column; gap: 16px; }
.row-fields { display: flex; gap: 16px; }
.row-fields .field { flex: 1; }

.field label {
  display: block;
  font-size: 12px;
  font-weight: 800;
  color: #0f2f64;
  margin-bottom: 8px;
  letter-spacing: 0;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8fbff;
  border: 1px solid #cfe0f4;
  border-radius: 8px;
  padding: 12px 14px;
  transition: all 0.2s;
  overflow: hidden;
}
.input-glow {
  position: absolute; bottom: 0; left: 0; height: 2px; width: 0;
  background: #0b63b6; transition: width 0.2s ease;
}
.input-wrap:focus-within { border-color: #71ace9; background: #ffffff; box-shadow: 0 0 0 3px rgba(11, 99, 182, 0.09); }
.input-wrap:focus-within .input-glow { width: 100%; }
.input-wrap .el-icon { color: #0b63b6; font-size: 16px; flex-shrink: 0; }
.input-wrap input { flex:1; background:none; border:none; outline:none; color: #0f2f64; font-size:14px; font-family: 'Inter', system-ui, sans-serif; }
.input-wrap input::placeholder { color: #8a9bb4; font-family: 'Inter', system-ui, sans-serif; }

.role-select { display: flex; gap: 10px; }
.role-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px; background: #ffffff;
  border: 1px solid #cfe0f4; border-radius: 8px;
  color: #5b6f92; cursor: pointer; transition: all 0.2s; font-size: 13px; font-weight: 800;
}
.role-btn.active { background: #e7f2ff; border-color: #0b63b6; color: #075da8; box-shadow: inset 3px 0 0 #0b63b6; }
.role-btn:hover { border-color: #71ace9; color: #0f2f64; }

.error-msg { background: #fff4f2; border: 1px solid #ffd5cf; color: #b42318; padding: 12px; border-radius: 8px; font-size: 13px; }
.success-msg { background: #ecfdf5; border: 1px solid #a7f3d0; color: #047857; padding: 12px; border-radius: 8px; font-size: 13px; }

.btn-primary {
  background: linear-gradient(135deg, #0b63b6 0%, #0a88df 100%); color: #ffffff; border: 1px solid #0b63b6;
  border-radius: 8px; padding: 16px; font-size: 14px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; letter-spacing: 0; margin-top: 8px; position: relative; overflow: hidden; text-align: center;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 12px 22px rgba(11, 99, 182, 0.24); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sys-text { font-family: 'Inter', system-ui, sans-serif; }

.auth-switch { text-align: center; color: #5b6f92; font-size: 13px; margin-top: 24px; }
.auth-switch a { color: #075da8; text-decoration: none; font-weight: 800; transition: color 0.2s; }
.auth-switch a:hover { color: #053b7a; text-decoration: underline; }

@media (max-width: 640px) {
  .auth-card { padding: 28px 20px; }
  .row-fields { flex-direction: column; }
  .theme-toggle { top: 14px; right: 14px; }
}
</style>
