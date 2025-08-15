<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1>注册账户</h1>
        <p>加入Qlib Web量化投研平台</p>
      </div>
      
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="基本信息" />
        <el-step title="账户设置" />
      </el-steps>
      
      <!-- 第一步：基本信息 -->
      <el-form
        v-show="currentStep === 0"
        ref="step1FormRef"
        :model="registerForm"
        :rules="step1Rules"
        class="register-form"
      >
        <el-form-item prop="full_name">
          <el-input
            v-model="registerForm.full_name"
            placeholder="真实姓名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱地址"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item prop="company">
          <el-input
            v-model="registerForm.company"
            placeholder="所在公司（可选）"
            size="large"
            :prefix-icon="OfficeBuilding"
          />
        </el-form-item>
        
        <el-form-item prop="department">
          <el-input
            v-model="registerForm.department"
            placeholder="所在部门（可选）"
            size="large"
          />
        </el-form-item>
      </el-form>
      
      <!-- 第二步：账户设置 -->
      <el-form
        v-show="currentStep === 1"
        ref="step2FormRef"
        :model="registerForm"
        :rules="step2Rules"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
          <div class="form-tip">
            用户名只能包含字母、数字、下划线和短横线，3-50个字符
          </div>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
          <div class="form-tip">
            密码至少8位，需包含大小写字母和数字
          </div>
        </el-form-item>
        
        <el-form-item prop="confirm_password">
          <el-input
            v-model="registerForm.confirm_password"
            type="password"
            placeholder="确认密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <!-- 注册成功提示 -->
      <div v-show="currentStep === 2" class="verification-step">
        <el-result
          icon="success"
          title="注册成功！"
          sub-title="您的账户已创建成功，现在可以登录使用了"
        >
          <template #extra>
            <el-button type="primary" @click="$router.push('/login')">
              前往登录
            </el-button>
          </template>
        </el-result>
      </div>
      
      <!-- 操作按钮 -->
      <div v-show="currentStep < 2" class="form-actions">
        <el-button
          v-if="currentStep > 0"
          @click="prevStep"
        >
          上一步
        </el-button>
        
        <el-button
          v-if="currentStep === 0"
          type="primary"
          @click="nextStep"
        >
          下一步
        </el-button>
        
        <el-button
          v-if="currentStep === 1"
          type="primary"
          :loading="loading"
          @click="handleRegister"
        >
          注册
        </el-button>
      </div>
      
      <div class="login-link">
        已有账户？
        <el-link type="primary" @click="$router.push('/login')">
          立即登录
        </el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import { User, Lock, Message, OfficeBuilding } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const step1FormRef = ref<InstanceType<typeof ElForm>>()
const step2FormRef = ref<InstanceType<typeof ElForm>>()

const currentStep = ref(0)
const loading = ref(false)

const registerForm = reactive({
  full_name: '',
  email: '',
  company: '',
  department: '',
  position: '',
  username: '',
  password: '',
  confirm_password: ''
})

const step1Rules = {
  full_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const step2Rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和短横线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 50, message: '密码长度在 8 到 50 个字符', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (!value) {
          callback()
          return
        }
        if (!/(?=.*[a-z])/.test(value)) {
          callback(new Error('密码必须包含小写字母'))
          return
        }
        if (!/(?=.*[A-Z])/.test(value)) {
          callback(new Error('密码必须包含大写字母'))
          return
        }
        if (!/(?=.*\d)/.test(value)) {
          callback(new Error('密码必须包含数字'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    if (!step1FormRef.value) return
    const valid = await step1FormRef.value.validate().catch(() => false)
    if (valid) {
      currentStep.value = 1
    }
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value -= 1
  }
}

const handleRegister = async () => {
  if (!step2FormRef.value) return
  
  const valid = await step2FormRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  
  try {
    await authStore.register(registerForm)
    ElMessage.success('注册成功！')
    currentStep.value = 2
  } catch (error: any) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 500px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.register-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.register-form {
  margin: 30px 0;
}

.register-form .el-form-item {
  margin-bottom: 20px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}

.verification-step {
  margin: 30px 0;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin: 30px 0 20px;
}

.form-actions .el-button {
  min-width: 100px;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-top: 20px;
}
</style>