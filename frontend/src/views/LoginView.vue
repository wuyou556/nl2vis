<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({
  username: '',
  password: '',
})

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  try {
    await auth.login(form.value.username, form.value.password)
    router.push('/')
  } catch {
    // 错误已在拦截器处理
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h2>📊 ChatChart</h2>
      <p class="subtitle">自然语言驱动的数据可视化</p>

      <el-form @submit.prevent="handleLogin">
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
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <p class="link">
        还没有账号？<router-link to="/register">去注册</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.login-card h2 {
  margin-bottom: 8px;
  font-size: 28px;
  color: #303133;
}

.subtitle {
  margin-bottom: 32px;
  color: #909399;
  font-size: 14px;
}

.login-btn {
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
