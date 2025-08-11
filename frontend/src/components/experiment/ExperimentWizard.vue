<template>
  <div class="experiment-wizard">
    <el-card>
      <template #header>
        <div class="wizard-header">
          <h2>新建实验 - 智能向导</h2>
          <div class="progress-info">
            步骤 {{ currentStep }} / {{ totalSteps }}
          </div>
        </div>
      </template>

      <!-- 步骤进度条 -->
      <el-steps :active="currentStep - 1" finish-status="success" class="wizard-steps">
        <el-step title="实验信息" description="基本配置信息" />
        <el-step title="数据配置" description="选择数据源和时间" />
        <el-step title="模型配置" description="选择和配置模型" />
        <el-step title="策略配置" description="选择和配置策略" />
        <el-step title="预览确认" description="检查配置并提交" />
      </el-steps>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <!-- 步骤1: 实验信息 -->
        <div v-if="currentStep === 1" class="step-content">
          <el-form :model="experimentForm" :rules="stepRules.step1" ref="step1FormRef" label-width="120px">
            <el-card shadow="never" class="info-card">
              <template #header>
                <div class="card-header">
                  <el-icon><InfoFilled /></el-icon>
                  <span>实验基本信息</span>
                </div>
              </template>
              
              <el-form-item label="实验名称" prop="name">
                <el-input 
                  v-model="experimentForm.name" 
                  placeholder="请输入实验名称" 
                  @input="validateCurrentStep"
                />
                <div class="form-tip">
                  <el-icon><QuestionFilled /></el-icon>
                  建议使用有意义的名称，如"基于LSTM的股票预测-2024Q1"
                </div>
              </el-form-item>
              
              <el-form-item label="实验描述" prop="description">
                <el-input 
                  v-model="experimentForm.description" 
                  type="textarea" 
                  :rows="3"
                  placeholder="请简要描述实验目的和预期效果"
                  @input="validateCurrentStep"
                />
              </el-form-item>
              
              <el-form-item label="实验标签">
                <el-tag
                  v-for="tag in experimentForm.tags"
                  :key="tag"
                  closable
                  @close="removeTag(tag)"
                  style="margin-right: 8px;"
                >
                  {{ tag }}
                </el-tag>
                <el-input
                  v-if="showTagInput"
                  ref="tagInputRef"
                  v-model="newTag"
                  size="small"
                  style="width: 100px;"
                  @keyup.enter="addTag"
                  @blur="addTag"
                />
                <el-button v-else size="small" @click="showNewTagInput">+ 添加标签</el-button>
              </el-form-item>
            </el-card>

            <!-- 推荐模板 -->
            <el-card shadow="never" class="template-card" v-if="recommendedTemplates.length > 0">
              <template #header>
                <div class="card-header">
                  <el-icon><Star /></el-icon>
                  <span>推荐模板</span>
                </div>
              </template>
              
              <div class="template-list">
                <div 
                  v-for="template in recommendedTemplates" 
                  :key="template.id"
                  class="template-item"
                  @click="selectTemplate(template)"
                >
                  <div class="template-info">
                    <h4>{{ template.name }}</h4>
                    <p>{{ template.description }}</p>
                    <div class="template-stats">
                      <span><el-icon><View /></el-icon>使用 {{ template.usage_count }} 次</span>
                      <span><el-icon><Star /></el-icon>评分 {{ template.rating }}</span>
                    </div>
                  </div>
                  <el-button type="primary" size="small">使用此模板</el-button>
                </div>
              </div>
            </el-card>
          </el-form>
        </div>

        <!-- 步骤2: 数据配置 -->
        <div v-if="currentStep === 2" class="step-content">
          <el-form :model="experimentForm" :rules="stepRules.step2" ref="step2FormRef" label-width="120px">
            <el-card shadow="never" class="config-card">
              <template #header>
                <div class="card-header">
                  <el-icon><DataBoard /></el-icon>
                  <span>数据源配置</span>
                </div>
              </template>

              <el-form-item label="股票池" prop="data_config.stock_pool">
                <el-select 
                  v-model="experimentForm.data_config.stock_pool" 
                  placeholder="选择股票池"
                  @change="onStockPoolChange"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="pool in stockPools"
                    :key="pool.value"
                    :label="pool.label"
                    :value="pool.value"
                  >
                    <div class="option-detail">
                      <span>{{ pool.label }}</span>
                      <span class="option-desc">{{ pool.description }}</span>
                    </div>
                  </el-option>
                </el-select>
                <div class="form-tip">
                  <el-icon><QuestionFilled /></el-icon>
                  建议新手选择"沪深300"，包含优质蓝筹股，风险相对较低
                </div>
              </el-form-item>

              <el-form-item label="时间范围" prop="data_config.time_range">
                <el-date-picker
                  v-model="timeRange"
                  type="daterange"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  @change="onTimeRangeChange"
                  style="width: 100%;"
                />
                <div class="time-presets">
                  <el-button size="small" @click="setTimeRange('1y')">最近1年</el-button>
                  <el-button size="small" @click="setTimeRange('2y')">最近2年</el-button>
                  <el-button size="small" @click="setTimeRange('3y')">最近3年</el-button>
                  <el-button size="small" @click="setTimeRange('5y')">最近5年</el-button>
                </div>
                <div class="form-tip">
                  <el-icon><InfoFilled /></el-icon>
                  数据范围：{{ formatDataRange() }}，建议至少选择2年数据
                </div>
              </el-form-item>

              <!-- 智能推荐面板 -->
              <div class="smart-recommendation" v-if="dataRecommendations">
                <h4><el-icon><MagicStick /></el-icon>智能推荐</h4>
                <el-alert
                  :title="dataRecommendations.title"
                  :description="dataRecommendations.description"
                  :type="dataRecommendations.type"
                  show-icon
                  :closable="false"
                />
              </div>
            </el-card>
          </el-form>
        </div>

        <!-- 步骤3: 模型配置 -->
        <div v-if="currentStep === 3" class="step-content">
          <el-form :model="experimentForm" :rules="stepRules.step3" ref="step3FormRef" label-width="120px">
            <el-card shadow="never" class="config-card">
              <template #header>
                <div class="card-header">
                  <el-icon><Setting /></el-icon>
                  <span>模型选择</span>
                </div>
              </template>

              <el-form-item label="模型类型" prop="model_config.name">
                <el-radio-group v-model="experimentForm.model_config.name" @change="onModelChange">
                  <div class="model-options">
                    <div 
                      v-for="model in availableModels"
                      :key="model.name"
                      class="model-option"
                      :class="{ active: experimentForm.model_config.name === model.name }"
                    >
                      <el-radio :value="model.name">
                        <div class="model-info">
                          <h4>{{ model.display_name }}</h4>
                          <p>{{ model.description }}</p>
                          <div class="model-features">
                            <el-tag v-for="feature in model.features" :key="feature" size="small">
                              {{ feature }}
                            </el-tag>
                          </div>
                        </div>
                      </el-radio>
                      <div class="model-performance" v-if="model.performance">
                        <div class="perf-item">
                          <span>准确率</span>
                          <el-progress :percentage="model.performance.accuracy" :show-text="false" />
                          <span>{{ model.performance.accuracy }}%</span>
                        </div>
                        <div class="perf-item">
                          <span>训练速度</span>
                          <el-progress :percentage="model.performance.speed" :show-text="false" />
                          <span>{{ getSpeedText(model.performance.speed) }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-radio-group>
              </el-form-item>

              <!-- 智能参数推荐 -->
              <div class="param-config" v-if="experimentForm.model_config.name && modelParams.length > 0">
                <h4><el-icon><MagicStick /></el-icon>参数配置</h4>
                <div class="param-recommendations" v-if="paramRecommendations">
                  <el-alert
                    title="智能参数推荐"
                    :description="`基于历史${paramRecommendations.experiments_analyzed}个实验，为您推荐以下参数`"
                    type="success"
                    show-icon
                    :closable="false"
                    style="margin-bottom: 16px;"
                  />
                </div>

                <div class="params-grid">
                  <div 
                    v-for="param in modelParams"
                    :key="param.name"
                    class="param-item"
                  >
                    <div class="param-header">
                      <label>{{ param.display_name }}</label>
                      <el-tooltip :content="param.description" placement="top">
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    
                    <!-- 数值参数 -->
                    <div v-if="param.type === 'int' || param.type === 'float'" class="param-control">
                      <el-slider
                        v-model="experimentForm.model_config.params[param.name]"
                        :min="param.min"
                        :max="param.max"
                        :step="param.step || (param.type === 'int' ? 1 : 0.01)"
                        show-input
                        :input-size="'small'"
                        style="margin: 8px 0;"
                      />
                      <div class="param-recommendation" v-if="getParamRecommendation(param.name)">
                        <span class="rec-label">推荐值:</span>
                        <el-button 
                          size="small" 
                          type="primary" 
                          text
                          @click="useRecommendedValue(param.name)"
                        >
                          {{ getParamRecommendation(param.name) }}
                        </el-button>
                      </div>
                    </div>
                    
                    <!-- 布尔参数 -->
                    <div v-else-if="param.type === 'bool'" class="param-control">
                      <el-switch v-model="experimentForm.model_config.params[param.name]" />
                    </div>
                    
                    <!-- 选择参数 -->
                    <div v-else-if="param.type === 'choice'" class="param-control">
                      <el-select v-model="experimentForm.model_config.params[param.name]" style="width: 100%;">
                        <el-option
                          v-for="option in param.choices"
                          :key="option.value"
                          :label="option.label"
                          :value="option.value"
                        />
                      </el-select>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-form>
        </div>

        <!-- 步骤4: 策略配置 -->
        <div v-if="currentStep === 4" class="step-content">
          <el-form :model="experimentForm" :rules="stepRules.step4" ref="step4FormRef" label-width="120px">
            <el-card shadow="never" class="config-card">
              <template #header>
                <div class="card-header">
                  <el-icon><TrendCharts /></el-icon>
                  <span>策略配置</span>
                </div>
              </template>

              <el-form-item label="策略类型" prop="strategy_config.name">
                <el-select 
                  v-model="experimentForm.strategy_config.name" 
                  placeholder="选择策略"
                  @change="onStrategyChange"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="strategy in availableStrategies"
                    :key="strategy.name"
                    :label="strategy.display_name"
                    :value="strategy.name"
                  >
                    <div class="strategy-option">
                      <div class="strategy-name">{{ strategy.display_name }}</div>
                      <div class="strategy-desc">{{ strategy.description }}</div>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <!-- 策略参数 -->
              <div class="strategy-params" v-if="experimentForm.strategy_config.name && strategyParams.length > 0">
                <h4>策略参数</h4>
                <div class="params-grid">
                  <div 
                    v-for="param in strategyParams"
                    :key="param.name"
                    class="param-item"
                  >
                    <div class="param-header">
                      <label>{{ param.display_name }}</label>
                      <el-tooltip :content="param.description" placement="top">
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </div>
                    
                    <div v-if="param.type === 'int' || param.type === 'float'" class="param-control">
                      <el-input-number
                        v-model="experimentForm.strategy_config.params[param.name]"
                        :min="param.min"
                        :max="param.max"
                        :step="param.step || (param.type === 'int' ? 1 : 0.01)"
                        :precision="param.type === 'float' ? 2 : 0"
                        size="small"
                        style="width: 100%;"
                      />
                    </div>
                    
                    <div v-else-if="param.type === 'bool'" class="param-control">
                      <el-switch v-model="experimentForm.strategy_config.params[param.name]" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- 风险控制 -->
              <div class="risk-control">
                <h4>风险控制</h4>
                <el-row :gutter="16">
                  <el-col :span="8">
                    <el-form-item label="最大回撤限制">
                      <el-input-number
                        v-model="experimentForm.strategy_config.risk_control.max_drawdown"
                        :min="0.05"
                        :max="0.5"
                        :step="0.01"
                        :precision="2"
                        size="small"
                      />
                      <span style="margin-left: 8px; font-size: 12px; color: #999;">5% ~ 50%</span>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="单日最大损失">
                      <el-input-number
                        v-model="experimentForm.strategy_config.risk_control.daily_loss_limit"
                        :min="0.01"
                        :max="0.1"
                        :step="0.01"
                        :precision="2"
                        size="small"
                      />
                      <span style="margin-left: 8px; font-size: 12px; color: #999;">1% ~ 10%</span>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="止损点">
                      <el-input-number
                        v-model="experimentForm.strategy_config.risk_control.stop_loss"
                        :min="0.05"
                        :max="0.3"
                        :step="0.01"
                        :precision="2"
                        size="small"
                      />
                      <span style="margin-left: 8px; font-size: 12px; color: #999;">5% ~ 30%</span>
                    </el-form-item>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </el-form>
        </div>

        <!-- 步骤5: 预览确认 -->
        <div v-if="currentStep === 5" class="step-content">
          <el-card shadow="never" class="preview-card">
            <template #header>
              <div class="card-header">
                <el-icon><View /></el-icon>
                <span>配置预览</span>
              </div>
            </template>

            <div class="config-preview">
              <el-descriptions title="实验配置总览" :column="2" border>
                <el-descriptions-item label="实验名称">{{ experimentForm.name }}</el-descriptions-item>
                <el-descriptions-item label="实验描述">{{ experimentForm.description }}</el-descriptions-item>
                <el-descriptions-item label="股票池">{{ getStockPoolLabel() }}</el-descriptions-item>
                <el-descriptions-item label="时间范围">{{ formatTimeRange() }}</el-descriptions-item>
                <el-descriptions-item label="模型类型">{{ getModelLabel() }}</el-descriptions-item>
                <el-descriptions-item label="策略类型">{{ getStrategyLabel() }}</el-descriptions-item>
              </el-descriptions>

              <!-- 风险评估 -->
              <div class="risk-assessment">
                <h4>风险评估</h4>
                <div class="risk-indicators">
                  <div class="risk-item">
                    <span>整体风险等级</span>
                    <el-tag :type="riskLevel.type">{{ riskLevel.label }}</el-tag>
                  </div>
                  <div class="risk-item">
                    <span>预期年化收益</span>
                    <span class="risk-value">{{ estimatedPerformance.annual_return }}</span>
                  </div>
                  <div class="risk-item">
                    <span>预期最大回撤</span>
                    <span class="risk-value">{{ estimatedPerformance.max_drawdown }}</span>
                  </div>
                  <div class="risk-item">
                    <span>夏普比率预期</span>
                    <span class="risk-value">{{ estimatedPerformance.sharpe_ratio }}</span>
                  </div>
                </div>
              </div>

              <!-- 预计资源消耗 -->
              <div class="resource-estimation">
                <h4>预计资源消耗</h4>
                <el-row :gutter="16">
                  <el-col :span="8">
                    <div class="resource-item">
                      <el-icon><Timer /></el-icon>
                      <span>预计训练时间</span>
                      <strong>{{ resourceEstimation.training_time }}</strong>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="resource-item">
                      <el-icon><Monitor /></el-icon>
                      <span>内存使用</span>
                      <strong>{{ resourceEstimation.memory_usage }}</strong>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="resource-item">
                      <el-icon><CpuFill /></el-icon>
                      <span>CPU使用率</span>
                      <strong>{{ resourceEstimation.cpu_usage }}</strong>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="wizard-actions">
        <el-button 
          v-if="currentStep > 1" 
          @click="prevStep"
          :disabled="loading"
        >
          上一步
        </el-button>
        <el-button 
          v-if="currentStep < totalSteps" 
          type="primary" 
          @click="nextStep"
          :disabled="!canNextStep || loading"
          :loading="validating"
        >
          下一步
        </el-button>
        <el-button 
          v-if="currentStep === totalSteps" 
          type="success" 
          @click="submitExperiment"
          :loading="loading"
        >
          创建实验
        </el-button>
        <el-button @click="$emit('cancel')">取消</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang=\"ts\">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  InfoFilled,
  QuestionFilled,
  Star,
  View,
  DataBoard,
  Setting,
  TrendCharts,
  MagicStick,
  Timer,
  Monitor,
  CpuFill
} from '@element-plus/icons-vue'

interface ExperimentForm {
  name: string
  description: string
  tags: string[]
  data_config: {
    stock_pool: string
    start_date: string
    end_date: string
  }
  model_config: {
    name: string
    params: Record<string, any>
  }
  strategy_config: {
    name: string
    params: Record<string, any>
    risk_control: {
      max_drawdown: number
      daily_loss_limit: number
      stop_loss: number
    }
  }
}

const emit = defineEmits(['cancel', 'submit'])

// 响应式数据
const currentStep = ref(1)
const totalSteps = 5
const loading = ref(false)
const validating = ref(false)
const canNextStep = ref(false)

const experimentForm = reactive<ExperimentForm>({
  name: '',
  description: '',
  tags: [],
  data_config: {
    stock_pool: '',
    start_date: '',
    end_date: ''
  },
  model_config: {
    name: '',
    params: {}
  },
  strategy_config: {
    name: '',
    params: {},
    risk_control: {
      max_drawdown: 0.2,
      daily_loss_limit: 0.05,
      stop_loss: 0.15
    }
  }
})

// 表单验证规则
const stepRules = {
  step1: {
    name: [
      { required: true, message: '请输入实验名称', trigger: 'blur' },
      { min: 3, max: 50, message: '名称长度应为3-50个字符', trigger: 'blur' }
    ]
  },
  step2: {
    'data_config.stock_pool': [
      { required: true, message: '请选择股票池', trigger: 'change' }
    ]
  },
  step3: {
    'model_config.name': [
      { required: true, message: '请选择模型', trigger: 'change' }
    ]
  },
  step4: {
    'strategy_config.name': [
      { required: true, message: '请选择策略', trigger: 'change' }
    ]
  }
}

// 数据选项
const stockPools = ref([
  { value: 'csi300', label: '沪深300', description: '300只大盘蓝筹股' },
  { value: 'csi500', label: '中证500', description: '500只中盘股' },
  { value: 'all_a', label: '全A股', description: '所有A股市场股票' },
  { value: 'hs300_tech', label: '科技龙头', description: '科技行业龙头股票' }
])

const availableModels = ref([
  {
    name: 'LightGBM',
    display_name: 'LightGBM',
    description: '轻量级梯度提升模型，训练速度快，适合初学者',
    features: ['快速训练', '高准确率', '内存友好'],
    performance: { accuracy: 85, speed: 90 }
  },
  {
    name: 'LSTM',
    display_name: '长短期记忆网络',
    description: '深度学习模型，擅长处理时序数据',
    features: ['时序建模', '深度学习', '复杂模式'],
    performance: { accuracy: 78, speed: 60 }
  },
  {
    name: 'LinearModel',
    display_name: '线性模型',
    description: '简单的线性回归模型，运行速度极快',
    features: ['简单易懂', '快速预测', '基准模型'],
    performance: { accuracy: 65, speed: 95 }
  }
])

const availableStrategies = ref([
  {
    name: 'TopkDropoutStrategy',
    display_name: 'Top-k选股策略',
    description: '选择预测分数最高的k只股票进行投资'
  },
  {
    name: 'TopkLongShortStrategy',
    display_name: '多空策略',
    description: '同时做多高分股票和做空低分股票'
  }
])

// 推荐数据
const recommendedTemplates = ref([
  {
    id: '1',
    name: '稳健型量化策略',
    description: '适合新手的低风险策略配置',
    usage_count: 156,
    rating: '4.5'
  },
  {
    id: '2',
    name: '成长股精选',
    description: '专注成长股的中等风险策略',
    usage_count: 89,
    rating: '4.2'
  }
])

const modelParams = ref([])
const strategyParams = ref([])
const paramRecommendations = ref(null)

// 智能推荐
const dataRecommendations = ref(null)

// 时间相关
const timeRange = ref([])

// 标签相关
const showTagInput = ref(false)
const newTag = ref('')
const tagInputRef = ref()

// 表单引用
const step1FormRef = ref()
const step2FormRef = ref()
const step3FormRef = ref()
const step4FormRef = ref()

// 计算属性
const riskLevel = computed(() => {
  // 基于配置计算风险等级
  const modelRisk = experimentForm.model_config.name === 'LSTM' ? 3 : 
                   experimentForm.model_config.name === 'LightGBM' ? 2 : 1
  const strategyRisk = experimentForm.strategy_config.name === 'TopkLongShortStrategy' ? 3 : 2
  const avgRisk = (modelRisk + strategyRisk) / 2
  
  if (avgRisk <= 1.5) return { type: 'success', label: '低风险' }
  if (avgRisk <= 2.5) return { type: 'warning', label: '中风险' }
  return { type: 'danger', label: '高风险' }
})

const estimatedPerformance = computed(() => {
  return {
    annual_return: '12-18%',
    max_drawdown: '15-25%',
    sharpe_ratio: '0.8-1.2'
  }
})

const resourceEstimation = computed(() => {
  const isDeepLearning = experimentForm.model_config.name === 'LSTM'
  return {
    training_time: isDeepLearning ? '30-45分钟' : '5-15分钟',
    memory_usage: isDeepLearning ? '2-4GB' : '512MB-1GB',
    cpu_usage: isDeepLearning ? '70-90%' : '30-50%'
  }
})

// 方法
const nextStep = async () => {
  if (await validateCurrentStep()) {
    if (currentStep.value < totalSteps) {
      currentStep.value++
      await loadStepData()
    }
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const validateCurrentStep = async () => {
  const currentFormRef = getCurrentFormRef()
  if (!currentFormRef) return true
  
  try {
    validating.value = true
    await currentFormRef.validate()
    canNextStep.value = true
    return true
  } catch {
    canNextStep.value = false
    return false
  } finally {
    validating.value = false
  }
}

const getCurrentFormRef = () => {
  const refs = {
    1: step1FormRef.value,
    2: step2FormRef.value,
    3: step3FormRef.value,
    4: step4FormRef.value
  }
  return refs[currentStep.value]
}

const loadStepData = async () => {
  switch (currentStep.value) {
    case 2:
      await loadDataRecommendations()
      break
    case 3:
      await loadModelParams()
      await loadParameterRecommendations()
      break
    case 4:
      await loadStrategyParams()
      break
  }
}

const loadDataRecommendations = async () => {
  // 基于当前选择提供数据建议
  if (experimentForm.data_config.stock_pool === 'all_a') {
    dataRecommendations.value = {
      title: '数据量较大',
      description: '全A股数据量大，建议缩短时间范围或选择更大的模型',
      type: 'warning'
    }
  }
}

const loadModelParams = async () => {
  if (!experimentForm.model_config.name) return
  
  try {
    const response = await fetch(`/api/v1/config/model-params/${experimentForm.model_config.name}`)
    const data = await response.json()
    
    if (data.success) {
      modelParams.value = Object.entries(data.data).map(([name, config]: [string, any]) => ({
        name,
        display_name: config.display_name || name,
        description: config.description || '',
        type: config.type,
        min: config.min,
        max: config.max,
        step: config.step,
        choices: config.choices,
        default: config.default
      }))
      
      // 初始化参数默认值
      modelParams.value.forEach(param => {
        if (!(param.name in experimentForm.model_config.params)) {
          experimentForm.model_config.params[param.name] = param.default
        }
      })
    }
  } catch (error) {
    console.error('加载模型参数失败:', error)
  }
}

const loadParameterRecommendations = async () => {
  if (!experimentForm.model_config.name) return
  
  try {
    const response = await fetch(`/api/v1/recommendations/model-params/${experimentForm.model_config.name}?` + 
      new URLSearchParams({
        stock_pool: experimentForm.data_config.stock_pool
      }))
    const data = await response.json()
    
    if (data.success) {
      paramRecommendations.value = data.data
      
      // 应用推荐参数
      Object.assign(experimentForm.model_config.params, data.data.recommended_params)
    }
  } catch (error) {
    console.error('加载参数推荐失败:', error)
  }
}

const loadStrategyParams = async () => {
  if (!experimentForm.strategy_config.name) return
  
  try {
    const response = await fetch(`/api/v1/config/strategy-params/${experimentForm.strategy_config.name}`)
    const data = await response.json()
    
    if (data.success) {
      strategyParams.value = Object.entries(data.data).map(([name, config]: [string, any]) => ({
        name,
        display_name: config.display_name || name,
        description: config.description || '',
        type: config.type,
        min: config.min,
        max: config.max,
        step: config.step,
        default: config.default
      }))
      
      // 初始化参数默认值
      strategyParams.value.forEach(param => {
        if (!(param.name in experimentForm.strategy_config.params)) {
          experimentForm.strategy_config.params[param.name] = param.default
        }
      })
    }
  } catch (error) {
    console.error('加载策略参数失败:', error)
  }
}

// 事件处理
const onStockPoolChange = () => {
  validateCurrentStep()
  loadDataRecommendations()
}

const onTimeRangeChange = () => {
  if (timeRange.value && timeRange.value.length === 2) {
    experimentForm.data_config.start_date = timeRange.value[0]
    experimentForm.data_config.end_date = timeRange.value[1]
  }
}

const onModelChange = () => {
  experimentForm.model_config.params = {}
  loadModelParams()
  loadParameterRecommendations()
}

const onStrategyChange = () => {
  experimentForm.strategy_config.params = {}
  loadStrategyParams()
}

const setTimeRange = (range: string) => {
  const end = new Date()
  const start = new Date()
  
  switch (range) {
    case '1y':
      start.setFullYear(end.getFullYear() - 1)
      break
    case '2y':
      start.setFullYear(end.getFullYear() - 2)
      break
    case '3y':
      start.setFullYear(end.getFullYear() - 3)
      break
    case '5y':
      start.setFullYear(end.getFullYear() - 5)
      break
  }
  
  timeRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
  onTimeRangeChange()
}

const selectTemplate = (template: any) => {
  ElMessage.success(`已选择模板: ${template.name}`)
  // 这里可以填充模板数据
}

const addTag = () => {
  if (newTag.value.trim() && !experimentForm.tags.includes(newTag.value.trim())) {
    experimentForm.tags.push(newTag.value.trim())
  }
  newTag.value = ''
  showTagInput.value = false
}

const removeTag = (tag: string) => {
  const index = experimentForm.tags.indexOf(tag)
  if (index > -1) {
    experimentForm.tags.splice(index, 1)
  }
}

const showNewTagInput = () => {
  showTagInput.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const getParamRecommendation = (paramName: string) => {
  return paramRecommendations.value?.recommended_params?.[paramName]
}

const useRecommendedValue = (paramName: string) => {
  const recommended = getParamRecommendation(paramName)
  if (recommended !== undefined) {
    experimentForm.model_config.params[paramName] = recommended
    ElMessage.success(`已应用推荐值: ${recommended}`)
  }
}

const getSpeedText = (speed: number) => {
  if (speed >= 90) return '很快'
  if (speed >= 70) return '较快'
  if (speed >= 50) return '中等'
  return '较慢'
}

// 预览相关方法
const getStockPoolLabel = () => {
  const pool = stockPools.value.find(p => p.value === experimentForm.data_config.stock_pool)
  return pool?.label || ''
}

const getModelLabel = () => {
  const model = availableModels.value.find(m => m.name === experimentForm.model_config.name)
  return model?.display_name || ''
}

const getStrategyLabel = () => {
  const strategy = availableStrategies.value.find(s => s.name === experimentForm.strategy_config.name)
  return strategy?.display_name || ''
}

const formatTimeRange = () => {
  if (experimentForm.data_config.start_date && experimentForm.data_config.end_date) {
    return `${experimentForm.data_config.start_date} 至 ${experimentForm.data_config.end_date}`
  }
  return ''
}

const formatDataRange = () => {
  if (timeRange.value && timeRange.value.length === 2) {
    const start = new Date(timeRange.value[0])
    const end = new Date(timeRange.value[1])
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
    return `约 ${days} 天数据`
  }
  return ''
}

const submitExperiment = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/experiments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(experimentForm)
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('实验创建成功！')
      emit('submit', data.data)
    } else {
      ElMessage.error(data.message || '创建实验失败')
    }
  } catch (error) {
    ElMessage.error('网络错误，创建实验失败')
  } finally {
    loading.value = false
  }
}

// 监听步骤变化
watch(currentStep, () => {
  canNextStep.value = false
  nextTick(() => {
    validateCurrentStep()
  })
})

onMounted(() => {
  // 初始化默认时间范围
  setTimeRange('2y')
  validateCurrentStep()
})
</script>

<style scoped>
.experiment-wizard {
  max-width: 1000px;
  margin: 0 auto;
}

.wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wizard-header h2 {
  margin: 0;
}

.progress-info {
  color: #666;
  font-size: 14px;
}

.wizard-steps {
  margin: 20px 0;
}

.wizard-content {
  min-height: 400px;
  padding: 20px 0;
}

.step-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.template-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.template-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
}

.template-info p {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #666;
}

.template-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.template-stats span {
  display: flex;
  align-items: center;
  gap: 2px;
}

.option-detail {
  display: flex;
  flex-direction: column;
}

.option-desc {
  font-size: 12px;
  color: #999;
}

.time-presets {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.smart-recommendation {
  margin-top: 16px;
}

.smart-recommendation h4 {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.model-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-option {
  border: 2px solid #eee;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.model-option:hover,
.model-option.active {
  border-color: #409eff;
}

.model-option .el-radio {
  width: 100%;
}

.model-info h4 {
  margin: 0 0 8px 0;
}

.model-info p {
  margin: 0 0 8px 0;
  color: #666;
}

.model-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.model-performance {
  margin-top: 12px;
  display: flex;
  gap: 24px;
}

.perf-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.perf-item .el-progress {
  width: 60px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.param-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-header label {
  font-weight: 600;
  font-size: 14px;
}

.param-control {
  margin-top: 8px;
}

.param-recommendation {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}

.rec-label {
  color: #999;
}

.strategy-option {
  display: flex;
  flex-direction: column;
}

.strategy-name {
  font-weight: 600;
}

.strategy-desc {
  font-size: 12px;
  color: #999;
}

.risk-control h4,
.strategy-params h4 {
  margin: 16px 0 12px 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.config-preview {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.risk-assessment h4,
.resource-estimation h4 {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 16px;
}

.risk-indicators {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.risk-value {
  font-weight: 600;
  color: #409eff;
}

.resource-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.resource-item strong {
  color: #409eff;
}

.wizard-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}
</style>