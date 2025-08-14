<template>
  <div class="training-wizard">
    <el-form :model="localConfig" :rules="rules" ref="formRef" label-width="120px">
      <!-- 实验基本信息 -->
      <el-card class="config-section">
        <template #header>
          <div class="section-header">
            <el-icon><Document /></el-icon>
            <span>实验基本信息</span>
          </div>
        </template>
        
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="实验名称" prop="name">
              <el-input 
                v-model="localConfig.name" 
                placeholder="请输入实验名称"
                @blur="generateNameIfEmpty"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实验描述">
              <el-input 
                v-model="localConfig.description" 
                placeholder="简要描述实验目的（可选）"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 模型特定配置 -->
      <el-card class="config-section">
        <template #header>
          <div class="section-header">
            <el-icon><Setting /></el-icon>
            <span>{{ modelType }} 模型配置</span>
          </div>
        </template>

        <!-- LightGBM 配置 -->
        <div v-if="modelType === 'LightGBM'" class="model-config">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="叶子节点数">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.num_leaves" 
                  :min="10" 
                  :max="1000" 
                  :step="10"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="学习率">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.learning_rate" 
                  :min="0.001" 
                  :max="0.3" 
                  :step="0.001"
                  :precision="3"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="特征采样率">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.feature_fraction" 
                  :min="0.1" 
                  :max="1.0" 
                  :step="0.1"
                  :precision="1"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- XGBoost 配置 -->
        <div v-else-if="modelType === 'XGBoost'" class="model-config">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="最大深度">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.max_depth" 
                  :min="1" 
                  :max="15" 
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="学习率">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.learning_rate" 
                  :min="0.001" 
                  :max="0.3" 
                  :step="0.001"
                  :precision="3"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="树的数量">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.n_estimators" 
                  :min="10" 
                  :max="1000" 
                  :step="10"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- LSTM 配置 -->
        <div v-else-if="modelType === 'LSTM'" class="model-config">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="隐藏层大小">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.hidden_size" 
                  :min="16" 
                  :max="512" 
                  :step="16"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="LSTM层数">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.num_layers" 
                  :min="1" 
                  :max="5" 
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Dropout率">
                <el-input-number 
                  v-model="localConfig.modelConfig.params.dropout" 
                  :min="0.0" 
                  :max="0.5" 
                  :step="0.1"
                  :precision="1"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 通用深度学习配置 -->
        <div v-if="isDeepLearningModel" class="dl-config">
          <el-divider content-position="left">深度学习特定配置</el-divider>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="优化器">
                <el-select v-model="localConfig.modelConfig.params.optimizer" style="width: 100%">
                  <el-option label="Adam" value="adam" />
                  <el-option label="SGD" value="sgd" />
                  <el-option label="RMSprop" value="rmsprop" />
                  <el-option label="AdamW" value="adamw" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="学习率调度器">
                <el-select v-model="localConfig.trainingParams.scheduler" style="width: 100%">
                  <el-option label="无" value="none" />
                  <el-option label="StepLR" value="step" />
                  <el-option label="CosineAnnealingLR" value="cosine" />
                  <el-option label="ReduceLROnPlateau" value="plateau" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 训练参数配置 -->
      <el-card class="config-section">
        <template #header>
          <div class="section-header">
            <el-icon><Timer /></el-icon>
            <span>训练参数</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="训练轮数" prop="trainingParams.epochs">
              <el-input-number 
                v-model="localConfig.trainingParams.epochs" 
                :min="1" 
                :max="1000" 
                :step="10"
              />
              <div class="param-hint">
                推荐值: {{ getRecommendedEpochs() }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="批次大小">
              <el-input-number 
                v-model="localConfig.trainingParams.batchSize" 
                :min="1" 
                :max="512" 
                :step="8"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="验证集比例">
              <el-input-number 
                v-model="localConfig.trainingParams.validationSplit" 
                :min="0.1" 
                :max="0.5" 
                :step="0.05"
                :precision="2"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="早停耐心值">
              <el-input-number 
                v-model="localConfig.trainingParams.earlyStoppingPatience" 
                :min="5" 
                :max="50" 
                :step="5"
              />
              <div class="param-hint">
                连续多少轮无改善后停止训练
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="保存最佳模型">
              <el-switch 
                v-model="localConfig.trainingParams.saveBestModel" 
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 评估配置 -->
      <el-card class="config-section">
        <template #header>
          <div class="section-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>评估配置</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="主要指标">
              <el-select v-model="localConfig.evaluationConfig.primaryMetric" style="width: 100%">
                <el-option label="准确率 (Accuracy)" value="accuracy" />
                <el-option label="精确率 (Precision)" value="precision" />
                <el-option label="召回率 (Recall)" value="recall" />
                <el-option label="F1分数" value="f1" />
                <el-option label="AUC" value="auc" />
                <el-option label="夏普比率" value="sharpe" />
                <el-option label="信息比率" value="information_ratio" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交叉验证">
              <el-switch 
                v-model="localConfig.evaluationConfig.crossValidation" 
                active-text="启用"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div v-if="localConfig.evaluationConfig.crossValidation">
          <el-form-item label="折数">
            <el-input-number 
              v-model="localConfig.evaluationConfig.cvFolds" 
              :min="3" 
              :max="10" 
            />
          </el-form-item>
        </div>
      </el-card>

      <!-- 高级选项 -->
      <el-card class="config-section">
        <template #header>
          <div class="section-header">
            <el-icon><Tools /></el-icon>
            <span>高级选项</span>
            <el-button 
              text 
              size="small" 
              @click="showAdvanced = !showAdvanced"
            >
              {{ showAdvanced ? '收起' : '展开' }}
            </el-button>
          </div>
        </template>

        <el-collapse-transition>
          <div v-show="showAdvanced">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="随机种子">
                  <el-input-number 
                    v-model="localConfig.trainingParams.randomSeed" 
                    :min="0" 
                    :max="999999" 
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="并行进程数">
                  <el-input-number 
                    v-model="localConfig.trainingParams.nJobs" 
                    :min="1" 
                    :max="16" 
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="详细输出">
                  <el-switch 
                    v-model="localConfig.trainingParams.verbose" 
                    active-text="开启"
                    inactive-text="关闭"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="回调函数">
              <el-checkbox-group v-model="localConfig.trainingParams.callbacks">
                <el-checkbox label="model_checkpoint">模型检查点</el-checkbox>
                <el-checkbox label="early_stopping">早停</el-checkbox>
                <el-checkbox label="reduce_lr">学习率衰减</el-checkbox>
                <el-checkbox label="tensorboard">TensorBoard日志</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>
        </el-collapse-transition>
      </el-card>

      <!-- 预估信息 -->
      <el-card class="estimation-card">
        <template #header>
          <div class="section-header">
            <el-icon><Odometer /></el-icon>
            <span>训练预估</span>
          </div>
        </template>

        <el-row :gutter="24" class="estimation-row">
          <el-col :span="6">
            <div class="estimation-item">
              <div class="estimation-label">预计时间</div>
              <div class="estimation-value">{{ estimatedTime }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="estimation-item">
              <div class="estimation-label">内存需求</div>
              <div class="estimation-value">{{ estimatedMemory }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="estimation-item">
              <div class="estimation-label">预期性能</div>
              <div class="estimation-value">{{ estimatedPerformance }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="estimation-item">
              <div class="estimation-label">计算资源</div>
              <div class="estimation-value">{{ computeRequirement }}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { 
  Document, Setting, Timer, DataAnalysis, Tools, Odometer 
} from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import type { FactorDefinition } from '@/types/factor'

interface Props {
  modelType: string
  factors: FactorDefinition[]
  modelValue: any
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'config-changed', config: any): void
  (e: 'training-started', data: {taskId: string, config: any}): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const showAdvanced = ref(false)

// 本地配置数据
const localConfig = reactive({
  name: '',
  description: '',
  modelConfig: {
    type: props.modelType,
    params: {}
  },
  trainingParams: {
    epochs: 100,
    batchSize: 32,
    learningRate: 0.001,
    validationSplit: 0.2,
    earlyStoppingPatience: 10,
    saveBestModel: true,
    randomSeed: 42,
    nJobs: 4,
    verbose: true,
    callbacks: ['early_stopping', 'model_checkpoint'],
    scheduler: 'none'
  },
  evaluationConfig: {
    primaryMetric: 'accuracy',
    crossValidation: false,
    cvFolds: 5
  }
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入实验名称', trigger: 'blur' }
  ],
  'trainingParams.epochs': [
    { required: true, message: '请设置训练轮数', trigger: 'blur' },
    { type: 'number', min: 1, max: 1000, message: '训练轮数应在1-1000之间', trigger: 'blur' }
  ]
}

// 计算属性
const isDeepLearningModel = computed(() => {
  return ['LSTM', 'GRU', 'Transformer'].includes(props.modelType)
})

const estimatedTime = computed(() => {
  const baseTime = props.factors.length * 2 // 每个因子2分钟
  const modelMultiplier = getModelTimeMultiplier()
  const epochMultiplier = localConfig.trainingParams.epochs / 100
  return `${Math.round(baseTime * modelMultiplier * epochMultiplier)} 分钟`
})

const estimatedMemory = computed(() => {
  const baseMemory = props.factors.length * 0.1 // 每个因子100MB
  const batchMultiplier = localConfig.trainingParams.batchSize / 32
  const memory = baseMemory * batchMultiplier
  
  if (memory < 1) return `${Math.round(memory * 1000)}MB`
  return `${memory.toFixed(1)}GB`
})

const estimatedPerformance = computed(() => {
  const baseAccuracy = 0.75 + (props.factors.length * 0.01)
  const modelBonus = getModelAccuracyBonus()
  const epochBonus = Math.min(localConfig.trainingParams.epochs / 200, 0.05)
  
  return `${Math.round((baseAccuracy + modelBonus + epochBonus) * 100)}%`
})

const computeRequirement = computed(() => {
  if (isDeepLearningModel.value) {
    return localConfig.trainingParams.batchSize > 64 ? 'GPU(高)' : 'GPU(中)'
  }
  return 'CPU'
})

// 启动qlib模型训练
const startTraining = async () => {
  try {
    // 构建qlib训练请求
    const trainingRequest = {
      model_name: props.modelType,
      model_params: localConfig.modelConfig.params,
      dataset_config: {
        class: 'DatasetH',
        kwargs: {
          handler: {
            class: 'Alpha158',
            kwargs: {}
          },
          segments: {
            train: ['2018-01-01', '2020-12-31'],
            valid: ['2021-01-01', '2021-12-31'],
            test: ['2022-01-01', '2022-12-31']
          }
        }
      },
      task_config: {
        task: {
          model: {
            class: `qlib.contrib.model.${props.modelType.toLowerCase()}.${props.modelType}Model`,
            kwargs: localConfig.modelConfig.params
          },
          dataset: {
            class: 'DatasetH',
            kwargs: {
              handler: {
                class: 'Alpha158',
                kwargs: {}
              }
            }
          }
        }
      },
      experiment_name: localConfig.name
    }

    const response = await fetch('/api/v1/models/train', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(trainingRequest)
    })

    const result = await response.json()

    if (result.status === 'success') {
      emit('training-started', {
        taskId: result.data.task_id,
        config: localConfig
      })
      return result.data
    } else {
      throw new Error(result.message || '启动训练失败')
    }
  } catch (error) {
    console.error('启动训练失败:', error)
    throw error
  }
}

// 暴露训练方法给父组件
defineExpose({
  startTraining,
  validateConfig: () => formRef.value?.validate()
})

// 方法
const generateNameIfEmpty = () => {
  if (!localConfig.name.trim()) {
    const timestamp = new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
    localConfig.name = `${props.modelType}_训练_${timestamp}`
  }
}

const getRecommendedEpochs = () => {
  const recommendations: Record<string, number> = {
    'LightGBM': 100,
    'XGBoost': 100,
    'CatBoost': 1000,
    'LSTM': 200,
    'GRU': 150,
    'Transformer': 300,
    'LinearRegression': 50
  }
  return recommendations[props.modelType] || 100
}

const getModelTimeMultiplier = (): number => {
  const multipliers: Record<string, number> = {
    'LightGBM': 0.8,
    'XGBoost': 1.0,
    'CatBoost': 1.2,
    'LSTM': 3.0,
    'GRU': 2.5,
    'Transformer': 4.0,
    'LinearRegression': 0.3
  }
  return multipliers[props.modelType] || 1.0
}

const getModelAccuracyBonus = (): number => {
  const bonuses: Record<string, number> = {
    'LightGBM': 0.08,
    'XGBoost': 0.06,
    'CatBoost': 0.10,
    'LSTM': 0.12,
    'GRU': 0.10,
    'Transformer': 0.15,
    'LinearRegression': 0.02
  }
  return bonuses[props.modelType] || 0.05
}

// 初始化默认参数
const initializeDefaultParams = () => {
  const defaultParams: Record<string, any> = {
    'LightGBM': {
      num_leaves: 31,
      learning_rate: 0.05,
      feature_fraction: 0.9,
      bagging_fraction: 0.8,
      bagging_freq: 5
    },
    'XGBoost': {
      max_depth: 6,
      learning_rate: 0.05,
      n_estimators: 100,
      subsample: 0.8,
      colsample_bytree: 0.8
    },
    'CatBoost': {
      iterations: 1000,
      learning_rate: 0.05,
      depth: 6,
      l2_leaf_reg: 3
    },
    'LSTM': {
      hidden_size: 64,
      num_layers: 2,
      dropout: 0.2,
      optimizer: 'adam'
    },
    'GRU': {
      hidden_size: 64,
      num_layers: 2,
      dropout: 0.2,
      optimizer: 'adam'
    },
    'Transformer': {
      d_model: 128,
      nhead: 8,
      num_layers: 4,
      dropout: 0.1,
      optimizer: 'adamw'
    },
    'LinearRegression': {
      fit_intercept: true,
      normalize: false
    }
  }
  
  localConfig.modelConfig.params = defaultParams[props.modelType] || {}
}

// 监听配置变化
watch(
  localConfig,
  (newConfig) => {
    emit('update:modelValue', newConfig)
    emit('config-changed', newConfig)
  },
  { deep: true }
)

// 监听modelType变化
watch(
  () => props.modelType,
  (newType) => {
    localConfig.modelConfig.type = newType
    initializeDefaultParams()
  },
  { immediate: true }
)

// 初始化
initializeDefaultParams()

// 从父组件接收配置更新
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      Object.assign(localConfig, newValue)
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.training-wizard {
  max-width: 100%;
}

.config-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.estimation-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.estimation-row {
  margin: 0;
}

.estimation-item {
  text-align: center;
  padding: 16px;
}

.estimation-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.estimation-value {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
}

.model-config {
  padding: 16px 0;
}

.dl-config {
  margin-top: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-card__header) {
  background: #fafafa;
}

@media (max-width: 768px) {
  .estimation-row .el-col {
    margin-bottom: 16px;
  }
  
  .estimation-item {
    padding: 12px;
  }
  
  .model-config .el-row .el-col {
    margin-bottom: 16px;
  }
}
</style>