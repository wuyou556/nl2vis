<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({
  username: '',
  email: '',
  password: '',
})

async function handleRegister() {
  if (!form.value.username || !form.value.email || !form.value.password) {
    ElMessage.warning('请填写所有字段')
    return
  }
  if (form.value.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  try {
    await auth.register(form.value.username, form.value.email, form.value.password)
    router.push('/')
  } catch {
    // 错误已在拦截器处理
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-card">
      <h2>📊 ChatChart</h2>
      <p class="subtitle">创建你的账号</p>

      <el-form @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.email"
            placeholder="邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（至少 6 位）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="register-btn"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <p class="link">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.register-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.register-card h2 {
  margin-bottom: 8px;
  font-size: 28px;
  color: #303133;
}

.subtitle {
  margin-bottom: 32px;
  color: #909399;
  font-size: 14px;
}

.register-btn {
  width: 100%;
}

.link {
  margin-top: 16px;
  font-size: 14px;
  color: #909399;
}

.link a {
  color: #667eea;
  text-decoration: none;
}
</style>
