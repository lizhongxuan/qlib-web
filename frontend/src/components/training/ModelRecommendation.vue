<template>
  <div class="model-recommendation">
    <div class="recommendation-header">
      <el-alert
        title="智能推荐"
        description="基于您的因子特征和数据规模，我们为您推荐以下模型配置"
        type="info"
        show-icon
        :closable="false"
      />
    </div>

    <div class="model-grid">
      <div 
        v-for="model in recommendedModels" 
        :key="model.type"
        class="model-card"
        :class="{ 'selected': selectedModel === model.type }"
        @click="selectModel(model)"
      >
        <div class="model-header">
          <div class="model-icon">{{ model.icon }}</div>
          <div class="model-info">
            <h3 class="model-name">{{ model.name }}</h3>
            <p class="model-description">{{ model.description }}</p>
          </div>
          <el-tag 
            :type="getRecommendationTagType(model.score)"
            size="small"
          >
            {{ getRecommendationText(model.score) }}
          </el-tag>
        </div>

        <div class="model-metrics">
          <div class="metric">
            <span class="metric-label">预期准确率</span>
            <div class="metric-value">
              <el-progress 
                :percentage="model.expectedAccuracy" 
                :show-text="false"
                :stroke-width="4"
              />
              <span class="percentage">{{ model.expectedAccuracy }}%</span>
            </div>
          </div>
          
          <div class="metric">
            <span class="metric-label">训练速度</span>
            <div class="metric-value">
              <el-progress 
                :percentage="model.trainingSpeed" 
                :show-text="false"
                :stroke-width="4"
                color="#67c23a"
              />
              <span class="percentage">{{ getSpeedText(model.trainingSpeed) }}</span>
            </div>
          </div>

          <div class="metric">
            <span class="metric-label">资源消耗</span>
            <div class="metric-value">
              <el-progress 
                :percentage="model.resourceUsage" 
                :show-text="false"
                :stroke-width="4"
                :color="getResourceColor(model.resourceUsage)"
              />
              <span class="percentage">{{ getResourceText(model.resourceUsage) }}</span>
            </div>
          </div>
        </div>

        <div class="model-features">
          <el-tag 
            v-for="feature in model.features" 
            :key="feature"
            size="small"
            class="feature-tag"
          >
            {{ feature }}
          </el-tag>
        </div>

        <div class="model-actions" v-if="selectedModel === model.type">
          <el-button size="small" @click.stop="viewModelDetails(model)">
            详细配置
          </el-button>
          <el-button size="small" type="primary">
            选择此模型
          </el-button>
        </div>
      </div>
    </div>

    <div class="custom-model-section">
      <el-divider>或</el-divider>
      <el-button @click="$emit('custom-model')" size="large" plain>
        <el-icon><Setting /></el-icon>
        自定义模型配置
      </el-button>
    </div>

    <!-- 模型详情对话框 -->
    <el-dialog v-model="showModelDetails" :title="`${selectedModelDetails?.name} - 详细配置`" width="600px">
      <div v-if="selectedModelDetails" class="model-details">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="模型类型">
            {{ selectedModelDetails.type }}
          </el-descriptions-item>
          <el-descriptions-item label="适用场景">
            {{ selectedModelDetails.scenario }}
          </el-descriptions-item>
          <el-descriptions-item label="推荐理由">
            {{ selectedModelDetails.reason }}
          </el-descriptions-item>
          <el-descriptions-item label="数据要求">
            {{ selectedModelDetails.dataRequirements }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="parameter-preview" v-if="selectedModelDetails.defaultParams">
          <h4>默认参数配置</h4>
          <el-table :data="Object.entries(selectedModelDetails.defaultParams)" size="small">
            <el-table-column prop="0" label="参数名" width="150" />
            <el-table-column prop="1" label="默认值" />
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import type { FactorDefinition } from '@/types/factor'

interface ModelConfig {
  type: string
  name: string
  description: string
  icon: string
  score: number // 0-100 推荐分数
  expectedAccuracy: number
  trainingSpeed: number // 0-100
  resourceUsage: number // 0-100
  features: string[]
  scenario: string
  reason: string
  dataRequirements: string
  defaultParams: Record<string, any>
}

interface Props {
  factors: FactorDefinition[]
  dataConfig: any
}

const props = defineProps<Props>()
const emit = defineEmits(['model-selected', 'custom-model'])

const selectedModel = ref<string>('')
const showModelDetails = ref(false)
const selectedModelDetails = ref<ModelConfig | null>(null)

// 基础模型配置
const baseModels: ModelConfig[] = [
  {
    type: 'LightGBM',
    name: 'LightGBM',
    description: '轻量级梯度提升模型，训练快速，效果优秀',
    icon: '⚡',
    score: 0,
    expectedAccuracy: 85,
    trainingSpeed: 90,
    resourceUsage: 30,
    features: ['快速训练', '内存友好', '特征重要性', '过拟合控制'],
    scenario: '中小规模数据集，需要快速迭代',
    reason: '基于您的因子数量和数据规模，LightGBM能够快速训练并提供良好的预测效果',
    dataRequirements: '支持数值型和类别型特征，对缺失值有较好的处理',
    defaultParams: {
      'num_leaves': 31,
      'learning_rate': 0.05,
      'feature_fraction': 0.9,
      'bagging_fraction': 0.8,
      'bagging_freq': 5,
      'verbose': 0
    }
  },
  {
    type: 'XGBoost',
    name: 'XGBoost',
    description: '极端梯度提升，在表格数据上表现卓越',
    icon: '🚀',
    score: 0,
    expectedAccuracy: 83,
    trainingSpeed: 75,
    resourceUsage: 45,
    features: ['高准确率', '特征重要性', '正则化', '并行训练'],
    scenario: '需要高精度预测的场景',
    reason: 'XGBoost在金融数据上有优秀的表现，适合您的投资因子建模',
    dataRequirements: '适合结构化数据，需要适当的参数调优',
    defaultParams: {
      'max_depth': 6,
      'learning_rate': 0.05,
      'n_estimators': 100,
      'subsample': 0.8,
      'colsample_bytree': 0.8,
      'random_state': 42
    }
  },
  {
    type: 'CatBoost',
    name: 'CatBoost',
    description: '对类别特征友好的梯度提升模型',
    icon: '🐱',
    score: 0,
    expectedAccuracy: 86,
    trainingSpeed: 70,
    resourceUsage: 50,
    features: ['自动特征处理', '类别特征优化', '过拟合防护', '稳定性好'],
    scenario: '包含大量类别特征的数据',
    reason: '如果您的因子包含类别型特征，CatBoost会自动处理并优化',
    dataRequirements: '对类别特征和缺失值有优秀的内置处理',
    defaultParams: {
      'iterations': 1000,
      'learning_rate': 0.05,
      'depth': 6,
      'l2_leaf_reg': 3,
      'random_seed': 42,
      'verbose': False
    }
  },
  {
    type: 'LSTM',
    name: 'LSTM',
    description: '长短期记忆网络，擅长捕捉时间序列模式',
    icon: '🧠',
    score: 0,
    expectedAccuracy: 82,
    trainingSpeed: 40,
    resourceUsage: 85,
    features: ['时序建模', '长期依赖', '非线性关系', '深度学习'],
    scenario: '时间序列预测，需要捕捉长期依赖关系',
    reason: '股价预测具有时间序列特性，LSTM能够学习历史价格的长期模式',
    dataRequirements: '需要时序数据，建议使用GPU加速训练',
    defaultParams: {
      'hidden_size': 64,
      'num_layers': 2,
      'dropout': 0.2,
      'batch_size': 32,
      'learning_rate': 0.001,
      'epochs': 100
    }
  },
  {
    type: 'Transformer',
    name: 'Transformer',
    description: '基于注意力机制的现代深度学习模型',
    icon: '🎯',
    score: 0,
    expectedAccuracy: 88,
    trainingSpeed: 30,
    resourceUsage: 95,
    features: ['注意力机制', '并行训练', '长序列建模', '最先进技术'],
    scenario: '复杂的多变量时间序列预测',
    reason: '对于复杂的多因子模型，Transformer能够学习因子间的复杂交互关系',
    dataRequirements: '需要大量数据和计算资源，建议使用高性能GPU',
    defaultParams: {
      'd_model': 128,
      'nhead': 8,
      'num_layers': 4,
      'dropout': 0.1,
      'batch_size': 16,
      'learning_rate': 0.0001,
      'epochs': 200
    }
  },
  {
    type: 'LinearRegression',
    name: '线性回归',
    description: '简单快速的线性模型，适合基准测试',
    icon: '📊',
    score: 0,
    expectedAccuracy: 68,
    trainingSpeed: 100,
    resourceUsage: 10,
    features: ['快速训练', '可解释性强', '基准模型', '低资源消耗'],
    scenario: '快速验证和基准比较',
    reason: '作为基准模型，快速验证因子的线性预测能力',
    dataRequirements: '适合线性关系明显的数据，对特征工程要求较高',
    defaultParams: {
      'fit_intercept': true,
      'normalize': false,
      'alpha': 1.0
    }
  }
]

// 计算推荐模型
const recommendedModels = computed(() => {
  return baseModels.map(model => {
    const score = calculateRecommendationScore(model)
    return {
      ...model,
      score
    }
  }).sort((a, b) => b.score - a.score)
})

// 计算推荐分数
const calculateRecommendationScore = (model: ModelConfig): number => {
  let score = 50 // 基础分数
  
  // 基于因子数量调整
  const factorCount = props.factors.length
  if (factorCount < 10) {
    if (model.type === 'LinearRegression') score += 20
    if (model.type === 'LightGBM') score += 15
  } else if (factorCount < 30) {
    if (model.type === 'LightGBM') score += 25
    if (model.type === 'XGBoost') score += 20
    if (model.type === 'CatBoost') score += 15
  } else {
    if (model.type === 'CatBoost') score += 25
    if (model.type === 'XGBoost') score += 20
    if (model.type === 'Transformer') score += 15
  }
  
  // 基于数据规模调整
  const isLargeDataset = props.dataConfig?.stockPool === 'ALL'
  if (isLargeDataset) {
    if (model.type === 'LightGBM') score += 15
    if (model.type === 'LSTM') score -= 10
    if (model.type === 'Transformer') score -= 15
  }
  
  // 基于时间范围调整（时序模型优势）
  const hasTimeFeatures = props.factors.some(f => f.category === 'temporal')
  if (hasTimeFeatures) {
    if (model.type === 'LSTM') score += 20
    if (model.type === 'Transformer') score += 15
  }
  
  return Math.min(Math.max(score, 0), 100)
}

const selectModel = (model: ModelConfig) => {
  selectedModel.value = model.type
  emit('model-selected', {
    type: model.type,
    params: model.defaultParams
  })
}

const viewModelDetails = (model: ModelConfig) => {
  selectedModelDetails.value = model
  showModelDetails.value = true
}

const getRecommendationTagType = (score: number) => {
  if (score >= 80) return 'success'
  if (score >= 65) return 'warning'
  return 'info'
}

const getRecommendationText = (score: number) => {
  if (score >= 80) return '强烈推荐'
  if (score >= 65) return '推荐'
  return '可选'
}

const getSpeedText = (speed: number) => {
  if (speed >= 80) return '很快'
  if (speed >= 60) return '较快'
  if (speed >= 40) return '中等'
  return '较慢'
}

const getResourceText = (usage: number) => {
  if (usage >= 80) return '高'
  if (usage >= 50) return '中'
  return '低'
}

const getResourceColor = (usage: number) => {
  if (usage >= 80) return '#f56c6c'
  if (usage >= 50) return '#e6a23c'
  return '#67c23a'
}

onMounted(() => {
  // 自动选择推荐度最高的模型
  if (recommendedModels.value.length > 0) {
    const topModel = recommendedModels.value[0]
    selectModel(topModel)
  }
})
</script>

<style scoped>
.model-recommendation {
  padding: 24px;
}

.recommendation-header {
  margin-bottom: 24px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.model-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
}

.model-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.model-card.selected {
  border-color: #409eff;
  background: #f0f8ff;
}

.model-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.model-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.model-info {
  flex: 1;
}

.model-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.model-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.model-metrics {
  margin-bottom: 16px;
}

.metric {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.metric:last-child {
  margin-bottom: 0;
}

.metric-label {
  width: 80px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}

.metric-value {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-value .el-progress {
  flex: 1;
}

.percentage {
  font-size: 12px;
  color: #606266;
  width: 40px;
  text-align: right;
}

.model-features {
  margin-bottom: 16px;
}

.feature-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

.model-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.custom-model-section {
  text-align: center;
  padding-top: 24px;
}

.model-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.parameter-preview h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
}

@media (max-width: 768px) {
  .model-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .model-card {
    padding: 16px;
  }
  
  .model-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .model-actions {
    flex-direction: column;
  }
}
</style>