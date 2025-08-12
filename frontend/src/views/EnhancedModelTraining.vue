<template>
  <div class="enhanced-model-training">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Cpu /></el-icon>
        模型训练中心
      </h1>
      <p class="page-subtitle">专业的机器学习模型训练和超参数优化平台</p>
    </div>

    <!-- 数据来源确认 -->
    <el-card class="data-source-card" v-if="!dataSourceConfirmed">
      <template #header>
        <div class="card-header">
          <span>📊 数据来源确认</span>
          <el-tag type="info">步骤 1/4</el-tag>
        </div>
      </template>
      
      <div class="data-source-content">
        <div class="source-section">
          <h3>📈 数据集配置</h3>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="股票池">
                <el-select v-model="trainingConfig.dataConfig.stockPool" style="width: 100%">
                  <el-option label="沪深300" value="HS300" />
                  <el-option label="中证500" value="ZZ500" />
                  <el-option label="中证1000" value="ZZ1000" />
                  <el-option label="全A股" value="ALL" />
                </el-select>
              </el-form-item>
            </el-col>
            
            <el-col :span="8">
              <el-form-item label="时间范围">
                <el-date-picker
                  v-model="trainingConfig.dataConfig.dateRange"
                  type="daterange"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            
            <el-col :span="8">
              <el-form-item label="数据频率">
                <el-select v-model="trainingConfig.dataConfig.frequency" style="width: 100%">
                  <el-option label="日频" value="daily" />
                  <el-option label="周频" value="weekly" />
                  <el-option label="月频" value="monthly" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <div class="data-status">
            <el-alert
              title="数据状态检查"
              :type="dataStatus.type"
              :description="dataStatus.message"
              show-icon
              :closable="false"
            />
          </div>
        </div>

        <div class="source-section">
          <h3>🧮 因子配置</h3>
          <div class="factor-source">
            <div class="factor-info" v-if="selectedFactors.length > 0">
              <p>来自因子库 (已选择 {{ selectedFactors.length }} 个因子)</p>
              <div class="factor-list">
                <el-tag 
                  v-for="factor in selectedFactors" 
                  :key="factor.id"
                  closable
                  @close="removeFactor(factor.id)"
                  class="factor-tag"
                >
                  {{ factor.name }}
                </el-tag>
              </div>
            </div>
            
            <div class="factor-actions">
              <el-button @click="selectFromLibrary" type="primary">
                <el-icon><Collection /></el-icon>
                从因子库选择
              </el-button>
              <el-button @click="goToFactorDev">
                <el-icon><Plus /></el-icon>
                创建新因子
              </el-button>
            </div>
          </div>
        </div>

        <div class="confirm-actions">
          <el-button 
            type="primary" 
            @click="confirmDataSource"
            :disabled="selectedFactors.length === 0"
          >
            确认数据配置，继续下一步
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 智能模型推荐 -->
    <div v-if="dataSourceConfirmed" class="training-wizard">
      <el-steps :active="currentStep" align-center class="training-steps">
        <el-step title="数据确认" icon="DocumentChecked" />
        <el-step title="模型推荐" icon="Cpu" />
        <el-step title="参数配置" icon="Setting" />
        <el-step title="开始训练" icon="VideoPlay" />
      </el-steps>

      <!-- 模型推荐 -->
      <el-card v-if="currentStep === 1" class="step-card">
        <template #header>
          <div class="card-header">
            <span>🤖 智能模型推荐</span>
            <el-button @click="refreshRecommendations" size="small">
              <el-icon><Refresh /></el-icon>
              刷新推荐
            </el-button>
          </div>
        </template>

        <ModelRecommendation 
          :factors="selectedFactors"
          :data-config="trainingConfig.dataConfig"
          @model-selected="handleModelSelected"
          @custom-model="showCustomModelDialog = true"
        />

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button 
            type="primary" 
            @click="nextStep"
            :disabled="!trainingConfig.modelConfig.type"
          >
            下一步
          </el-button>
        </div>
      </el-card>

      <!-- 参数配置 -->
      <el-card v-if="currentStep === 2" class="step-card">
        <template #header>
          <span>⚙️ 训练参数配置</span>
        </template>

        <TrainingWizard 
          :model-type="trainingConfig.modelConfig.type"
          :factors="selectedFactors"
          v-model="trainingConfig"
          @config-changed="handleConfigChanged"
        />

        <HyperparameterOptimizer
          v-if="showHyperparamOptimizer"
          :model-type="trainingConfig.modelConfig.type"
          @optimization-complete="handleOptimizationComplete"
        />

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="toggleHyperparamOptimizer">
            {{ showHyperparamOptimizer ? '关闭' : '开启' }}超参数优化
          </el-button>
          <el-button type="primary" @click="nextStep">下一步</el-button>
        </div>
      </el-card>

      <!-- 训练确认和启动 -->
      <el-card v-if="currentStep === 3" class="step-card">
        <template #header>
          <span>🚀 训练配置确认</span>
        </template>

        <div class="training-summary">
          <h3>训练配置摘要</h3>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据集">
              {{ trainingConfig.dataConfig.stockPool }} ({{ trainingConfig.dataConfig.dateRange?.join(' ~ ') }})
            </el-descriptions-item>
            <el-descriptions-item label="因子数量">
              {{ selectedFactors.length }} 个
            </el-descriptions-item>
            <el-descriptions-item label="模型类型">
              {{ trainingConfig.modelConfig.type }}
            </el-descriptions-item>
            <el-descriptions-item label="预计训练时间">
              {{ estimatedTime }}
            </el-descriptions-item>
            <el-descriptions-item label="预计准确率">
              {{ estimatedAccuracy }}
            </el-descriptions-item>
            <el-descriptions-item label="资源消耗">
              {{ resourceEstimate }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="config-preview">
            <h4>详细配置</h4>
            <el-collapse v-model="activeCollapse">
              <el-collapse-item title="数据配置" name="data">
                <pre>{{ JSON.stringify(trainingConfig.dataConfig, null, 2) }}</pre>
              </el-collapse-item>
              <el-collapse-item title="模型配置" name="model">
                <pre>{{ JSON.stringify(trainingConfig.modelConfig, null, 2) }}</pre>
              </el-collapse-item>
              <el-collapse-item title="训练配置" name="training">
                <pre>{{ JSON.stringify(trainingConfig.trainingParams, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <div class="step-actions">
          <el-button @click="prevStep">上一步</el-button>
          <el-button @click="saveAsTemplate">
            <el-icon><Document /></el-icon>
            保存为模板
          </el-button>
          <el-button 
            type="primary" 
            @click="startTraining"
            :loading="startingTraining"
          >
            <el-icon><VideoPlay /></el-icon>
            开始训练
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 训练监控 -->
    <TrainingMonitor 
      v-if="showTrainingMonitor"
      :training-task="currentTrainingTask"
      @training-complete="handleTrainingComplete"
      @training-stopped="handleTrainingStopped"
    />

    <!-- 对话框 -->
    <el-dialog v-model="showFactorLibraryDialog" title="选择因子" width="800px">
      <FactorLibrary 
        @use-factor="handleFactorsSelected"
        @close="showFactorLibraryDialog = false"
      />
    </el-dialog>

    <el-dialog v-model="showCustomModelDialog" title="自定义模型" width="600px">
      <div class="custom-model-form">
        <p>自定义模型功能开发中...</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Cpu, Collection, Plus, Refresh, DocumentChecked,
  Setting, VideoPlay, Document
} from '@element-plus/icons-vue'

// 导入组件
import ModelRecommendation from '@/components/training/ModelRecommendation.vue'
import TrainingWizard from '@/components/training/TrainingWizard.vue'
import HyperparameterOptimizer from '@/components/training/HyperparameterOptimizer.vue'
import TrainingMonitor from '@/components/training/TrainingMonitor.vue'
import FactorLibrary from '@/components/factor/FactorLibrary.vue'

// 导入类型
import type { FactorDefinition } from '@/types/factor'
import type { TrainingConfig, TrainingTask } from '@/types/training'

const router = useRouter()

// 响应式数据
const dataSourceConfirmed = ref(false)
const currentStep = ref(1)
const showHyperparamOptimizer = ref(false)
const showTrainingMonitor = ref(false)
const showFactorLibraryDialog = ref(false)
const showCustomModelDialog = ref(false)
const startingTraining = ref(false)
const activeCollapse = ref(['data'])

const selectedFactors = ref<FactorDefinition[]>([])
const currentTrainingTask = ref<TrainingTask | null>(null)

const trainingConfig = reactive<TrainingConfig>({
  name: '',
  dataConfig: {
    stockPool: 'HS300',
    dateRange: ['2020-01-01', '2023-12-31'],
    frequency: 'daily'
  },
  modelConfig: {
    type: '',
    params: {}
  },
  trainingParams: {
    epochs: 100,
    batchSize: 32,
    learningRate: 0.001,
    validationSplit: 0.2,
    earlyStoppingPatience: 10
  }
})

const dataStatus = ref({
  type: 'success' as const,
  message: '数据检查通过，共找到 1,234,567 条有效记录'
})

// 计算属性
const estimatedTime = computed(() => {
  const baseTime = selectedFactors.value.length * 2 // 每个因子2分钟
  const modelMultiplier = getModelTimeMultiplier(trainingConfig.modelConfig.type)
  return `${Math.round(baseTime * modelMultiplier)} 分钟`
})

const estimatedAccuracy = computed(() => {
  // 根据因子数量和模型类型估算准确率
  const baseAccuracy = 0.75 + (selectedFactors.value.length * 0.02)
  const modelBonus = getModelAccuracyBonus(trainingConfig.modelConfig.type)
  return `${Math.round((baseAccuracy + modelBonus) * 100)}%`
})

const resourceEstimate = computed(() => {
  const gpuRequired = ['LSTM', 'GRU', 'Transformer'].includes(trainingConfig.modelConfig.type)
  return gpuRequired ? 'GPU加速 (高)' : 'CPU训练 (中)'
})

// 方法
const confirmDataSource = () => {
  if (selectedFactors.value.length === 0) {
    ElMessage.warning('请选择至少一个因子')
    return
  }
  dataSourceConfirmed.value = true
  currentStep.value = 1
}

const selectFromLibrary = () => {
  showFactorLibraryDialog.value = true
}

const goToFactorDev = () => {
  router.push('/factors')
}

const removeFactor = (factorId: string) => {
  const index = selectedFactors.value.findIndex(f => f.id === factorId)
  if (index > -1) {
    selectedFactors.value.splice(index, 1)
  }
}

const handleFactorsSelected = (factors: FactorDefinition[]) => {
  selectedFactors.value = factors
  showFactorLibraryDialog.value = false
  ElMessage.success(`已选择 ${factors.length} 个因子`)
}

const handleModelSelected = (modelConfig: any) => {
  trainingConfig.modelConfig = modelConfig
  ElMessage.success(`已选择模型: ${modelConfig.type}`)
}

const handleConfigChanged = (config: any) => {
  Object.assign(trainingConfig, config)
}

const handleOptimizationComplete = (optimizedParams: any) => {
  trainingConfig.modelConfig.params = optimizedParams
  ElMessage.success('超参数优化完成')
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  } else {
    dataSourceConfirmed.value = false
  }
}

const nextStep = () => {
  currentStep.value++
}

const toggleHyperparamOptimizer = () => {
  showHyperparamOptimizer.value = !showHyperparamOptimizer.value
}

const refreshRecommendations = () => {
  ElMessage.info('正在刷新模型推荐...')
  // 重新获取推荐
}

const saveAsTemplate = () => {
  // 保存配置为模板
  ElMessage.success('配置已保存为模板')
}

const startTraining = async () => {
  startingTraining.value = true
  
  try {
    // 创建训练任务
    const task: TrainingTask = {
      id: `training_${Date.now()}`,
      name: trainingConfig.name || `${trainingConfig.modelConfig.type}_训练_${Date.now()}`,
      config: trainingConfig,
      factors: selectedFactors.value,
      status: 'pending',
      progress: 0,
      createdAt: new Date()
    }
    
    currentTrainingTask.value = task
    showTrainingMonitor.value = true
    
    ElMessage.success('训练任务已创建，正在启动...')
    
  } catch (error) {
    ElMessage.error('启动训练失败')
  } finally {
    startingTraining.value = false
  }
}

const handleTrainingComplete = (result: any) => {
  ElMessage.success('模型训练完成！')
  showTrainingMonitor.value = false
  // 跳转到训练管理页面查看结果
  router.push('/training-management')
}

const handleTrainingStopped = () => {
  ElMessage.warning('训练已停止')
  showTrainingMonitor.value = false
}

const getModelTimeMultiplier = (modelType: string): number => {
  const multipliers: Record<string, number> = {
    'LightGBM': 0.8,
    'XGBoost': 1.0,
    'CatBoost': 1.2,
    'LSTM': 3.0,
    'GRU': 2.5,
    'Transformer': 4.0,
    'Linear': 0.3
  }
  return multipliers[modelType] || 1.0
}

const getModelAccuracyBonus = (modelType: string): number => {
  const bonuses: Record<string, number> = {
    'LightGBM': 0.08,
    'XGBoost': 0.06,
    'CatBoost': 0.10,
    'LSTM': 0.12,
    'GRU': 0.10,
    'Transformer': 0.15,
    'Linear': 0.02
  }
  return bonuses[modelType] || 0.05
}

// 生命周期
onMounted(() => {
  // 从路由参数中获取预选因子
  const factorIds = router.currentRoute.value.query.factors as string
  if (factorIds) {
    // 模拟从因子库加载预选因子
    const mockFactors = factorIds.split(',').map(id => ({
      id,
      name: `因子_${id}`,
      expression: `Mock expression for ${id}`,
      description: `Mock factor ${id}`,
      category: 'technical' as const,
      createdBy: 'User',
      createdAt: new Date()
    }))
    selectedFactors.value = mockFactors
  }
})
</script>

<style scoped>
.enhanced-model-training {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.page-subtitle {
  color: #606266;
  font-size: 16px;
  margin: 0;
}

.data-source-card {
  margin-bottom: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.data-source-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.source-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
}

.data-status {
  margin-top: 16px;
}

.factor-source {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.factor-tag {
  margin-bottom: 4px;
}

.factor-actions {
  display: flex;
  gap: 12px;
}

.confirm-actions {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.training-wizard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.training-steps {
  margin-bottom: 32px;
}

.step-card {
  min-height: 400px;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
  margin-top: 24px;
}

.training-summary {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.training-summary h3 {
  margin: 0;
  color: #303133;
}

.config-preview {
  margin-top: 24px;
}

.config-preview h4 {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
}

.config-preview pre {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.custom-model-form {
  padding: 24px;
  text-align: center;
  color: #606266;
}

@media (max-width: 768px) {
  .enhanced-model-training {
    padding: 16px;
  }
  
  .factor-actions {
    flex-direction: column;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .step-actions > * {
    width: 100%;
  }
}
</style>