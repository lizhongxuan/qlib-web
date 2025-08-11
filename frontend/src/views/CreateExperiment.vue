<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">新建实验</h1>
      <p class="page-subtitle">创建并配置量化投资策略回测实验</p>
    </div>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      size="large"
    >
      <!-- 基础信息 -->
      <div class="form-section">
        <h3 class="form-section-title">基础信息</h3>
        <div class="form-row">
          <el-form-item label="实验名称" prop="name">
            <el-input 
              v-model="formData.name" 
              placeholder="请输入实验名称"
              clearable
            />
          </el-form-item>
        </div>
      </div>

      <!-- 数据配置 -->
      <div class="form-section">
        <h3 class="form-section-title">数据配置</h3>
        <div class="form-row">
          <el-form-item label="股票池" prop="dataConfig.stockPool">
            <el-select 
              v-model="formData.dataConfig.stockPool" 
              placeholder="请选择股票池"
              style="width: 100%;"
            >
              <el-option 
                v-for="pool in stockPools" 
                :key="pool" 
                :label="pool" 
                :value="pool"
              />
            </el-select>
          </el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="开始时间" prop="dataConfig.startTime">
            <el-date-picker
              v-model="formData.dataConfig.startTime"
              type="date"
              placeholder="选择开始日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="结束时间" prop="dataConfig.endTime">
            <el-date-picker
              v-model="formData.dataConfig.endTime"
              type="date"
              placeholder="选择结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%;"
            />
          </el-form-item>
        </div>
      </div>

      <!-- 模型配置 -->
      <div class="form-section">
        <h3 class="form-section-title">模型配置</h3>
        <div class="form-row">
          <el-form-item label="模型类型" prop="modelConfig.name">
            <el-select 
              v-model="formData.modelConfig.name" 
              placeholder="请选择模型"
              style="width: 100%;"
              @change="onModelChange"
            >
              <el-option 
                v-for="model in models" 
                :key="model" 
                :label="model" 
                :value="model"
              />
            </el-select>
          </el-form-item>
        </div>
        
        <!-- 动态模型参数 -->
        <div v-if="formData.modelConfig.name" class="model-params">
          <el-divider content-position="left">模型参数</el-divider>
          <div class="form-row" v-if="formData.modelConfig.name === 'LightGBM'">
            <el-form-item label="估计器数量">
              <el-input-number 
                v-model="formData.modelConfig.params.n_estimators" 
                :min="10" 
                :max="1000" 
                :step="10"
                style="width: 100%;"
              />
            </el-form-item>
            <el-form-item label="学习率">
              <el-input-number 
                v-model="formData.modelConfig.params.learning_rate" 
                :min="0.01" 
                :max="1" 
                :step="0.01" 
                :precision="2"
                style="width: 100%;"
              />
            </el-form-item>
          </div>
          <div class="form-row" v-if="formData.modelConfig.name === 'LSTM'">
            <el-form-item label="隐藏层大小">
              <el-input-number 
                v-model="formData.modelConfig.params.hidden_size" 
                :min="16" 
                :max="512" 
                :step="16"
                style="width: 100%;"
              />
            </el-form-item>
            <el-form-item label="层数">
              <el-input-number 
                v-model="formData.modelConfig.params.num_layers" 
                :min="1" 
                :max="10" 
                :step="1"
                style="width: 100%;"
              />
            </el-form-item>
          </div>
        </div>
      </div>

      <!-- 策略配置 -->
      <div class="form-section">
        <h3 class="form-section-title">策略配置</h3>
        <div class="form-row">
          <el-form-item label="策略类型" prop="strategyConfig.name">
            <el-select 
              v-model="formData.strategyConfig.name" 
              placeholder="请选择策略"
              style="width: 100%;"
              @change="onStrategyChange"
            >
              <el-option 
                v-for="strategy in strategies" 
                :key="strategy" 
                :label="strategy" 
                :value="strategy"
              />
            </el-select>
          </el-form-item>
        </div>
        
        <!-- 动态策略参数 -->
        <div v-if="formData.strategyConfig.name" class="strategy-params">
          <el-divider content-position="left">策略参数</el-divider>
          <div class="form-row" v-if="formData.strategyConfig.name === 'TopkDropoutStrategy'">
            <el-form-item label="选股数量">
              <el-input-number 
                v-model="formData.strategyConfig.params.topk" 
                :min="5" 
                :max="100" 
                :step="5"
                style="width: 100%;"
              />
            </el-form-item>
            <el-form-item label="剔除天数">
              <el-input-number 
                v-model="formData.strategyConfig.params.n_drop_days" 
                :min="1" 
                :max="30" 
                :step="1"
                style="width: 100%;"
              />
            </el-form-item>
          </div>
        </div>
      </div>

      <!-- 回测配置 -->
      <div class="form-section">
        <h3 class="form-section-title">回测配置</h3>
        <div class="form-row">
          <el-form-item label="交易费用" prop="backtestConfig.tradeCost">
            <el-input-number 
              v-model="formData.backtestConfig.tradeCost" 
              :min="0" 
              :max="0.01" 
              :step="0.0001" 
              :precision="4"
              style="width: 100%;"
            />
            <template #append>%</template>
          </el-form-item>
        </div>
      </div>

      <!-- 配置预览 -->
      <div class="form-section">
        <h3 class="form-section-title">配置预览</h3>
        <el-card>
          <pre class="config-preview">{{ JSON.stringify(formData, null, 2) }}</pre>
        </el-card>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <el-button size="large" @click="resetForm">重置</el-button>
        <el-button 
          type="primary" 
          size="large" 
          @click="submitForm"
          :loading="submitting"
        >
          启动回测
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useExperimentStore } from '@/stores/experiment'
import type { ExperimentConfig } from '@/types/experiment'

const router = useRouter()
const experimentStore = useExperimentStore()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<ExperimentConfig>({
  name: '',
  dataConfig: {
    stockPool: '',
    startTime: '2020-01-01',
    endTime: '2023-12-31'
  },
  modelConfig: {
    name: '',
    params: {}
  },
  strategyConfig: {
    name: '',
    params: {}
  },
  backtestConfig: {
    tradeCost: 0.0015
  }
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入实验名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  'dataConfig.stockPool': [
    { required: true, message: '请选择股票池', trigger: 'change' }
  ],
  'dataConfig.startTime': [
    { required: true, message: '请选择开始时间', trigger: 'change' }
  ],
  'dataConfig.endTime': [
    { required: true, message: '请选择结束时间', trigger: 'change' }
  ],
  'modelConfig.name': [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  'strategyConfig.name': [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  'backtestConfig.tradeCost': [
    { required: true, message: '请输入交易费用', trigger: 'blur' }
  ]
}

// 配置选项
const stockPools = ref(['CSI300', 'CSI500', 'CSI800', 'CSI1000'])
const models = ref(['LightGBM', 'LSTM', 'GRU', 'Linear'])
const strategies = ref(['TopkDropoutStrategy', 'SignalStrategy'])

// 状态
const submitting = ref(false)

// 方法
const onModelChange = (modelName: string) => {
  // 根据模型类型设置默认参数
  switch (modelName) {
    case 'LightGBM':
      formData.modelConfig.params = {
        n_estimators: 100,
        learning_rate: 0.1
      }
      break
    case 'LSTM':
      formData.modelConfig.params = {
        hidden_size: 64,
        num_layers: 2
      }
      break
    default:
      formData.modelConfig.params = {}
  }
}

const onStrategyChange = (strategyName: string) => {
  // 根据策略类型设置默认参数
  switch (strategyName) {
    case 'TopkDropoutStrategy':
      formData.strategyConfig.params = {
        topk: 50,
        n_drop_days: 5
      }
      break
    default:
      formData.strategyConfig.params = {}
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  formData.modelConfig.params = {}
  formData.strategyConfig.params = {}
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 提交实验配置
    const result = await experimentStore.createExperiment(formData)
    
    if (result.success) {
      ElMessage.success('实验创建成功，正在启动回测...')
      router.push('/history')
    } else {
      ElMessage.error('实验创建失败')
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitting.value = false
  }
}

// 生命周期
onMounted(() => {
  // 可以在这里加载配置选项
  console.log('新建实验页面已加载')
})
</script>

<style scoped>
.form-section {
  margin-bottom: 32px;
}

.form-section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row :deep(.el-form-item) {
  flex: 1;
  margin-bottom: 0;
}

.model-params,
.strategy-params {
  margin-left: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.config-preview {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.form-actions {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.form-actions .el-button {
  min-width: 120px;
  margin: 0 8px;
}

@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 0;
  }
  
  .form-row :deep(.el-form-item) {
    margin-bottom: 16px;
  }
}
</style>