<template>
  <div class="profile-page">
    <div class="page-header">
      <div class="page-title">个人中心</div>
      <div class="page-sub">管理您的基本信息与安全设置</div>
    </div>

    <div class="profile-content">
      <!-- 基础信息与密码修改卡片 -->
      <div class="card info-card">
        <h3 class="card-title">基本信息</h3>
        <form @submit.prevent="handleUpdate" class="form-grid">
          <div class="form-group">
            <label>账号 / 学号</label>
            <input type="text" :value="auth.user?.username" disabled class="input disabled" />
          </div>
          <div class="form-group">
            <label>角色</label>
            <input type="text" :value="roleText" disabled class="input disabled" />
          </div>
          <div class="form-group full-width">
            <label>真实姓名 (用于识别系统)</label>
            <input type="text" v-model="form.full_name" class="input" placeholder="输入真实姓名" required />
          </div>
          
          <div class="divider">修改密码 (可选)</div>

          <div class="form-group full-width">
            <label>新密码</label>
            <input type="password" v-model="form.password" class="input" placeholder="不修改请留空" />
          </div>

          <div class="form-actions mt-4">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner"></span>
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
            <span v-if="successMsg" class="msg-success">{{ successMsg }}</span>
            <span v-if="errorMsg" class="msg-error">{{ errorMsg }}</span>
          </div>
        </form>
      </div>

      <!-- 照片上传卡片 (仅学生) -->
      <div v-if="auth.isStudent" class="card face-card">
        <h3 class="card-title">人脸信息采集</h3>
        <!-- 未设置姓名时提示 -->
        <div v-if="!form.full_name.trim()" class="no-name-tip">
          ⚠️ 请先在左侧设置「真实姓名」并保存，再来上传人脸照片。
        </div>
        <template v-else>
        <p class="card-desc">使用教室采集终端现场拍照注册。建议每人采集 3-5 张：正脸、左右轻微转头、自然上课坐姿；每次确认都会追加到人脸库。</p>

        <div class="camera-panel">
          <div class="camera-stage">
            <img v-if="previewUrl" :src="previewUrl" class="preview-img" alt="人脸预览" />
            <div v-if="!previewUrl" class="camera-placeholder">
              <div class="icon">📸</div>
              <div class="text">现场拍照注册</div>
            </div>
          </div>
          <div class="camera-actions">
            <button type="button" class="btn btn-secondary" :disabled="deviceCapturing" @click="captureDevicePhoto">
              <span v-if="deviceCapturing" class="spinner"></span>
              {{ deviceCapturing ? '拍照中...' : '现场拍照' }}
            </button>
            <button v-if="previewUrl" type="button" class="btn btn-ghost" @click="clearSelectedFace">
              重新拍/选
            </button>
          </div>
        </div>
        
        <div v-if="!previewUrl" class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
          <input type="file" ref="fileInput" accept="image/jpeg,image/png" class="hidden" @change="handleFileChange" />
          <div class="upload-placeholder">
            <div class="icon">📷</div>
            <div class="text">点击或拖拽照片到此处上传</div>
          </div>
        </div>

        <div class="form-actions mt-4">
          <button @click="uploadFace" class="btn btn-emerald" :disabled="!selectedFile || uploading">
            <span v-if="uploading" class="spinner"></span>
            {{ uploading ? '上传中...' : '确认注册人脸' }}
          </button>
          <span v-if="faceSuccessMsg" class="msg-success">{{ faceSuccessMsg }}</span>
          <span v-if="faceErrorMsg" class="msg-error">{{ faceErrorMsg }}</span>
        </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const auth = useAuthStore()

const roleText = computed(() => {
  if (auth.isStudent) return '学生'
  if (auth.isTeacher) return '教师'
  return '管理员'
})

// === 基本信息表单 ===
const form = ref({
  full_name: auth.user?.full_name || '',
  password: ''
})
const saving = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

async function handleUpdate() {
  saving.value = true
  successMsg.value = ''
  errorMsg.value = ''
  try {
    const res = await axios.put('/api/v1/auth/profile', {
      full_name: form.value.full_name,
      password: form.value.password || undefined
    })
    auth.updateUser({ full_name: res.data.full_name })
    successMsg.value = '信息更新成功！'
    form.value.password = '' // 清空密码框
    setTimeout(() => successMsg.value = '', 3000)
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || '更新失败'
  } finally {
    saving.value = false
  }
}

// === 照片上传 ===
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const uploading = ref(false)
const faceSuccessMsg = ref('')
const faceErrorMsg = ref('')
const deviceCapturing = ref(false)

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.item(0)
  if (file) setFile(file)
}

function handleDrop(e: DragEvent) {
  const file = e.dataTransfer?.files.item(0)
  if (file) setFile(file)
}

function setFile(file: File) {
  faceSuccessMsg.value = ''
  faceErrorMsg.value = ''
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    faceErrorMsg.value = '请上传 JPG 或 PNG 格式的图片'
    return
  }
  selectedFile.value = file
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = URL.createObjectURL(file)
}

async function captureDevicePhoto() {
  faceSuccessMsg.value = ''
  faceErrorMsg.value = ''
  clearSelectedFace()
  deviceCapturing.value = true

  try {
    const res = await axios.get('/api/v1/auth/jetson-face-snapshot', {
      responseType: 'blob'
    })
    const blob = res.data as Blob
    setFile(new File([blob], `现场人脸_${Date.now()}.jpg`, { type: 'image/jpeg' }))
  } catch (err: any) {
    faceErrorMsg.value = err.response?.data?.detail || '现场拍照失败，请确认采集终端在线且画面中有清晰人脸'
  } finally {
    deviceCapturing.value = false
  }
}

function clearSelectedFace() {
  selectedFile.value = null
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  if (fileInput.value) fileInput.value.value = ''
}

async function uploadFace() {
  if (!selectedFile.value) return
  uploading.value = true
  faceSuccessMsg.value = ''
  faceErrorMsg.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    await axios.post('/api/v1/auth/upload-face', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    faceSuccessMsg.value = '人脸样本已追加，识别库已更新。建议继续采集到 3-5 张。'
    setTimeout(() => faceSuccessMsg.value = '', 5000)
  } catch (err: any) {
    faceErrorMsg.value = err.response?.data?.detail || '上传失败'
  } finally {
    uploading.value = false
  }
}

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<style scoped>
.profile-page { padding: 28px; color: #c8d6e5; max-width: 1000px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 1.6rem; font-weight: 700; color: #a8ff78; }
.page-sub { font-size: .85rem; color: #6b7280; margin-top: 6px; }

.profile-content { display: grid; grid-template-columns: 1fr; gap: 24px; }
@media (min-width: 800px) {
  .profile-content { grid-template-columns: 1fr 1fr; align-items: start; }
}

.card { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07); border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
.card-title { font-size: 1.1rem; font-weight: 600; color: #f3f4f6; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,.05); padding-bottom: 12px; }
.card-desc { font-size: .85rem; color: #9ca3af; margin-bottom: 20px; line-height: 1.5; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.full-width { grid-column: 1 / -1; }
.form-group label { font-size: .85rem; color: #9ca3af; font-weight: 500; }
.input { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); color: #fff; padding: 10px 14px; border-radius: 8px; font-size: .95rem; transition: border-color .2s; }
.input:focus { border-color: #10b981; outline: none; }
.input.disabled { background: rgba(255,255,255,.02); color: #6b7280; cursor: not-allowed; }

.divider { grid-column: 1 / -1; margin: 12px 0 4px; font-size: .85rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

.btn { padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: .95rem; cursor: pointer; border: none; transition: all .2s; display: inline-flex; align-items: center; gap: 8px; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; box-shadow: 0 4px 12px rgba(59,130,246,0.3); }
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(59,130,246,0.4); }
.btn-emerald { background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 4px 12px rgba(16,185,129,0.3); }
.btn-emerald:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(16,185,129,0.4); }
.btn-secondary { background: rgba(59,130,246,.16); color: #bfdbfe; border: 1px solid rgba(96,165,250,.35); }
.btn-secondary:hover:not(:disabled) { background: rgba(59,130,246,.24); }
.btn-ghost { background: rgba(255,255,255,.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,.12); }
.btn-ghost:hover:not(:disabled) { background: rgba(255,255,255,.1); }

.mt-4 { margin-top: 16px; grid-column: 1 / -1; display: flex; align-items: center; gap: 16px; }

.msg-success { color: #10b981; font-size: .85rem; font-weight: 500; }
.msg-error { color: #ef4444; font-size: .85rem; font-weight: 500; }

.spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 上传区 */
.upload-area { border: 2px dashed rgba(255,255,255,.15); border-radius: 12px; height: 180px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all .2s; overflow: hidden; background: rgba(0,0,0,0.1); }
.upload-area:hover { border-color: #10b981; background: rgba(16,185,129,.05); }
.hidden { display: none; }
.upload-placeholder { text-align: center; color: #6b7280; }
.upload-placeholder .icon { font-size: 2rem; margin-bottom: 8px; color: #9ca3af; }
.upload-placeholder .text { font-size: .85rem; }
.preview-img { width: 100%; height: 100%; object-fit: contain; }

.camera-panel { margin-bottom: 16px; }
.camera-stage { height: 260px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(16,185,129,.22); background: rgba(0,0,0,.22); display: flex; align-items: center; justify-content: center; }
.camera-placeholder { text-align: center; color: #8aa0b6; }
.camera-placeholder .icon { font-size: 2rem; margin-bottom: 8px; }
.camera-placeholder .text { font-size: .9rem; font-weight: 600; }
.camera-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }

/* 未设置姓名提示 */
.no-name-tip {
  padding: 16px 18px;
  border-radius: 10px;
  background: rgba(245,158,11,.1);
  border: 1px solid rgba(245,158,11,.3);
  color: #f59e0b;
  font-size: .88rem;
  line-height: 1.5;
}
</style>
