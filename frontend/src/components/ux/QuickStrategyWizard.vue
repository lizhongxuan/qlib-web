<template>
  <div class="quick-strategy-wizard">
    <!-- 向导头部 -->
    <div class="wizard-header">
      <h2>
        <el-icon><Magic /></el-icon>
        一键策略创建向导
      </h2>
      <p class="wizard-subtitle">快速创建和验证量化策略，只需几分钟</p>
      
      <!-- 进度条 -->
      <el-steps :active="currentStep" align-center class="wizard-steps">
        <el-step title="选择模板" icon="DocumentCopy" />
        <el-step title="配置参数" icon="Setting" />
        <el-step title="快速验证" icon="CircleCheck" />
        <el-step title="查看结果" icon="TrendCharts" />
      </el-steps>
    </div>

    <!-- 向导内容 -->
    <div class="wizard-content">
      <!-- 步骤1: 选择策略模板 -->
      <div v-if="currentStep === 0" class="step-content">
        <h3>选择策略模板</h3>
        <div class="template-grid">
          <div
            v-for="template in strategyTemplates"
            :key="template.id"
            class="template-card"
            :class="{ active: selectedTemplate?.id === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="template-icon">
              <el-icon size="32">
                <component :is="template.icon" />
              </el-icon>
            </div>
            <h4>{{ template.name }}</h4>
            <p>{{ template.description }}</p>
            <div class="template-stats">
              <span class="stat">
                <el-icon><Trophy /></el-icon>
                胜率: {{ template.winRate }}%
              </span>
              <span class="stat">
                <el-icon><TrendCharts /></el-icon>
                年化: {{ template.annualReturn }}%
              </span>
            </div>
            <div class="template-tags">
              <el-tag v-for="tag in template.tags" :key="tag" size="small">
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤2: 配置策略参数 -->
      <div v-if="currentStep === 1" class="step-content">
        <h3>配置策略参数</h3>
        <div class="config-layout">
          <div class="config-form">
            <el-form :model="strategyConfig" label-width="120px">
              <!-- 基础配置 -->
              <el-form-item label="策略名称">
                <el-input v-model="strategyConfig.name" placeholder="输入策略名称" />
              </el-form-item>
              
              <el-form-item label="股票池">
                <el-select v-model="strategyConfig.stockPool" placeholder="选择股票池">
                  <el-option label="沪深300" value="CSI300" />
                  <el-option label="中证500" value="CSI500" />
                  <el-option label="创业板" value="CHINEXT" />
                  <el-option label="全A股" value="ALL_A" />
                </el-select>
              </el-form-item>

              <el-form-item label="回测时间">
                <el-date-picker
                  v-model="strategyConfig.dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>

              <!-- 动态参数配置 -->
              <div v-if="selectedTemplate?.parameters">
                <h4>策略参数</h4>
                <el-form-item
                  v-for="param in selectedTemplate.parameters"
                  :key="param.name"
                  :label="param.label"
                >
                  <!-- 数值输入 -->
                  <el-input-number
                    v-if="param.type === 'number'"
                    v-model="strategyConfig.parameters[param.name]"
                    :min="param.min"
                    :max="param.max"
                    :step="param.step"
                    :placeholder="param.placeholder"
                  />
                  
                  <!-- 选择器 -->
                  <el-select
                    v-else-if="param.type === 'select'"
                    v-model="strategyConfig.parameters[param.name]"
                    :placeholder="param.placeholder"
                  >
                    <el-option
                      v-for="option in param.options"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  
                  <!-- 开关 -->
                  <el-switch
                    v-else-if="param.type === 'boolean'"
                    v-model="strategyConfig.parameters[param.name]"
                  />
                  
                  <!-- 滑块 -->
                  <el-slider
                    v-else-if="param.type === 'slider'"
                    v-model="strategyConfig.parameters[param.name]"
                    :min="param.min"
                    :max="param.max"
                    :step="param.step"
                    show-input
                  />
                </el-form-item>
              </div>

              <!-- 风险控制 -->
              <h4>风险控制</h4>
              <el-form-item label="最大持仓数">
                <el-input-number v-model="strategyConfig.maxPositions" :min="1" :max="100" />
              </el-form-item>
              
              <el-form-item label="止损比例">
                <el-input-number
                  v-model="strategyConfig.stopLoss"
                  :min="0"
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                />
              </el-form-item>

              <el-form-item label="止盈比例">
                <el-input-number
                  v-model="strategyConfig.takeProfit"
                  :min="0"
                  :max="2"
                  :step="0.01"
                  :precision="2"
                />
              </el-form-item>
            </el-form>
          </div>

          <!-- 参数预览 -->
          <div class="config-preview">
            <h4>配置预览</h4>
            <div class="preview-content">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="策略名称">
                  {{ strategyConfig.name || '未设置' }}
                </el-descriptions-item>
                <el-descriptions-item label="股票池">
                  {{ getStockPoolLabel(strategyConfig.stockPool) }}
                </el-descriptions-item>
                <el-descriptions-item label="回测期间">
                  {{ formatDateRange(strategyConfig.dateRange) }}
                </el-descriptions-item>
                <el-descriptions-item label="最大持仓">
                  {{ strategyConfig.maxPositions }} 只
                </el-descriptions-item>
                <el-descriptions-item label="风险控制">
                  止损: {{ (strategyConfig.stopLoss * 100).toFixed(1) }}% |
                  止盈: {{ (strategyConfig.takeProfit * 100).toFixed(1) }}%
                </el-descriptions-item>
              </el-descriptions>

              <!-- 参数建议 -->
              <div class="suggestions" v-if="parameterSuggestions.length > 0">
                <h5>参数建议</h5>
                <div v-for="suggestion in parameterSuggestions" :key="suggestion.type" class="suggestion-item">
                  <el-icon><Lightbulb /></el-icon>
                  <span>{{ suggestion.message }}</span>
                  <el-button
                    v-if="suggestion.action"
                    size="small"
                    type="primary"
                    link
                    @click="applySuggestion(suggestion)"
                  >
                    应用
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤3: 快速验证 -->
      <div v-if="currentStep === 2" class="step-content">
        <h3>快速验证</h3>
        <div class="validation-content">
          <!-- 验证选项 -->
          <div class="validation-options">
            <el-card>
              <h4>验证选项</h4>
              <el-checkbox-group v-model="validationOptions">
                <el-checkbox label="factor_check">因子有效性检查</el-checkbox>
                <el-checkbox label="data_quality">数据质量检查</el-checkbox>
                <el-checkbox label="quick_backtest">快速回测验证</el-checkbox>
                <el-checkbox label="risk_analysis">风险分析</el-checkbox>
                <el-checkbox label="performance_preview">性能预估</el-checkbox>
              </el-checkbox-group>
            </el-card>
          </div>

          <!-- 验证进度 -->
          <div class="validation-progress" v-if="isValidating">
            <el-card>
              <h4>验证进行中...</h4>
              <div v-for="(check, index) in validationChecks" :key="index" class="check-item">
                <div class="check-header">
                  <span class="check-name">{{ check.name }}</span>
                  <el-icon v-if="check.status === 'running'" class="is-loading">
                    <Loading />
                  </el-icon>
                  <el-icon v-else-if="check.status === 'success'" style="color: #67c23a">
                    <SuccessFilled />
                  </el-icon>
                  <el-icon v-else-if="check.status === 'error'" style="color: #f56c6c">
                    <CircleCloseFilled />
                  </el-icon>
                </div>
                <el-progress
                  :percentage="check.progress"
                  :status="check.status === 'error' ? 'exception' : undefined"
                  :stroke-width="6"
                />
                <p v-if="check.message" class="check-message">{{ check.message }}</p>
              </div>
            </el-card>
          </div>

          <!-- 验证结果 -->
          <div class="validation-results" v-if="validationResults && !isValidating">
            <el-card>
              <h4>验证结果</h4>
              <div class="results-summary">
                <div class="result-item">
                  <el-statistic title="整体评分" :value="validationResults.overallScore" suffix="/100">
                    <template #prefix>
                      <el-icon style="vertical-align: -0.125em">
                        <Trophy />
                      </el-icon>
                    </template>
                  </el-statistic>
                </div>
                <div class="result-item">
                  <el-statistic title="预期年化收益" :value="validationResults.expectedReturn" suffix="%" :precision="2">
                    <template #prefix>
                      <el-icon style="vertical-align: -0.125em">
                        <TrendCharts />
                      </el-icon>
                    </template>
                  </el-statistic>
                </div>
                <div class="result-item">
                  <el-statistic title="最大回撤" :value="validationResults.maxDrawdown" suffix="%" :precision="2">
                    <template #prefix>
                      <el-icon style="vertical-align: -0.125em">
                        <Warning />
                      </el-icon>
                    </template>
                  </el-statistic>
                </div>
                <div class="result-item">
                  <el-statistic title="夏普比率" :value="validationResults.sharpeRatio" :precision="2">
                    <template #prefix>
                      <el-icon style="vertical-align: -0.125em">
                        <DataAnalysis />
                      </el-icon>
                    </template>
                  </el-statistic>
                </div>
              </div>

              <!-- 详细结果 -->
              <el-tabs v-model="activeResultTab" class="result-tabs">
                <el-tab-pane label="因子分析" name="factors">
                  <div v-for="factor in validationResults.factorAnalysis" :key="factor.name" class="factor-item">
                    <div class="factor-header">
                      <span class="factor-name">{{ factor.name }}</span>
                      <el-rate v-model="factor.rating" disabled show-score text-color="#ff9900" />
                    </div>
                    <p class="factor-description">{{ factor.description }}</p>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="风险分析" name="risk">
                  <div class="risk-metrics">
                    <el-descriptions :column="2" border>
                      <el-descriptions-item label="波动率">
                        {{ validationResults.riskMetrics.volatility }}%
                      </el-descriptions-item>
                      <el-descriptions-item label="Beta系数">
                        {{ validationResults.riskMetrics.beta }}
                      </el-descriptions-item>
                      <el-descriptions-item label="VaR (95%)">
                        {{ validationResults.riskMetrics.var95 }}%
                      </el-descriptions-item>
                      <el-descriptions-item label="信息比率">
                        {{ validationResults.riskMetrics.informationRatio }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </div>
                </el-tab-pane>

                <el-tab-pane label="优化建议" name="suggestions">
                  <div class="optimization-suggestions">
                    <div v-for="suggestion in validationResults.suggestions" :key="suggestion.id" class="suggestion-card">
                      <div class="suggestion-header">
                        <el-icon><Lightbulb /></el-icon>
                        <span class="suggestion-title">{{ suggestion.title }}</span>
                        <el-tag :type="suggestion.priority === 'high' ? 'danger' : suggestion.priority === 'medium' ? 'warning' : 'info'">
                          {{ suggestion.priority === 'high' ? '高优先级' : suggestion.priority === 'medium' ? '中优先级' : '低优先级' }}
                        </el-tag>
                      </div>
                      <p class="suggestion-content">{{ suggestion.content }}</p>
                      <div class="suggestion-actions">
                        <el-button size="small" @click="applySuggestion(suggestion)">
                          应用建议
                        </el-button>
                        <el-button size="small" type="info" @click="learnMore(suggestion)">
                          了解更多
                        </el-button>
                      </div>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </el-card>
          </div>
        </div>
      </div>

      <!-- 步骤4: 查看结果 -->
      <div v-if="currentStep === 3" class="step-content">
        <h3>策略创建完成</h3>
        <div class="completion-content">
          <el-result icon="success" title="策略创建成功!" :sub-title="`策略「${strategyConfig.name}」已创建并通过验证`">
            <template #extra>
              <div class="completion-actions">
                <el-button type="primary" size="large" @click="startFullBacktest">
                  <el-icon><Position /></el-icon>
                  开始完整回测
                </el-button>
                <el-button size="large" @click="viewStrategy">
                  <el-icon><View /></el-icon>
                  查看策略详情
                </el-button>
                <el-button size="large" @click="createAnother">
                  <el-icon><Plus /></el-icon>
                  创建另一个策略
                </el-button>
              </div>
            </template>
          </el-result>

          <!-- 策略摘要 -->
          <el-card class="strategy-summary">
            <template #header>
              <h4>策略摘要</h4>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="策略名称">{{ strategyConfig.name }}</el-descriptions-item>
              <el-descriptions-item label="策略模板">{{ selectedTemplate?.name }}</el-descriptions-item>
              <el-descriptions-item label="股票池">{{ getStockPoolLabel(strategyConfig.stockPool) }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ new Date().toLocaleString() }}</el-descriptions-item>
              <el-descriptions-item label="验证评分">
                {{ validationResults?.overallScore || 0 }}/100
              </el-descriptions-item>
              <el-descriptions-item label="预期年化收益">
                {{ validationResults?.expectedReturn || 0 }}%
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 下一步建议 -->
          <el-card class="next-steps">
            <template #header>
              <h4>建议下一步操作</h4>
            </template>
            <div class="next-step-list">
              <div class="next-step-item">
                <el-icon><Document /></el-icon>
                <div class="step-content">
                  <h5>完整回测验证</h5>
                  <p>在完整的历史数据上验证策略性能</p>
                </div>
                <el-button type="primary" link>去执行</el-button>
              </div>
              <div class="next-step-item">
                <el-icon><Setting /></el-icon>
                <div class="step-content">
                  <h5>参数优化</h5>
                  <p>使用机器学习优化策略参数</p>
                </div>
                <el-button type="primary" link>去优化</el-button>
              </div>
              <div class="next-step-item">
                <el-icon><Share /></el-icon>
                <div class="step-content">
                  <h5>模拟交易</h5>
                  <p>在模拟环境中测试策略</p>
                </div>
                <el-button type="primary" link>去测试</el-button>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 向导控制 -->
    <div class="wizard-controls">
      <el-button v-if="currentStep > 0" @click="previousStep">
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      
      <div class="controls-right">
        <el-button v-if="currentStep < 3" @click="skipWizard" type="info">
          跳过向导
        </el-button>
        
        <el-button
          v-if="currentStep < 2"
          type="primary"
          :disabled="!canProceed"
          @click="nextStep"
        >
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        
        <el-button
          v-if="currentStep === 2"
          type="primary"
          :loading="isValidating"
          :disabled="validationOptions.length === 0"
          @click="startValidation"
        >
          <el-icon><CircleCheck /></el-icon>
          开始验证
        </el-button>
        
        <el-button
          v-if="currentStep === 3"
          type="success"
          @click="finishWizard"
        >
          <el-icon><Check /></el-icon>
          完成
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Magic, DocumentCopy, Setting, CircleCheck, TrendCharts,
  Trophy, Lightbulb, Loading, SuccessFilled, CircleCloseFilled,
  Warning, DataAnalysis, Position, View, Plus, Document,
  Share, ArrowLeft, ArrowRight, Check
} from '@element-plus/icons-vue'

// 策略模板接口
interface StrategyTemplate {
  id: string
  name: string
  description: string
  icon: string
  winRate: number
  annualReturn: number
  tags: string[]
  parameters: TemplateParameter[]
}

interface TemplateParameter {
  name: string
  label: string
  type: 'number' | 'select' | 'boolean' | 'slider'
  min?: number
  max?: number
  step?: number
  options?: { label: string; value: any }[]
  placeholder?: string
  defaultValue?: any
}

// 策略配置接口
interface StrategyConfig {
  name: string
  stockPool: string
  dateRange: [string, string] | null
  maxPositions: number
  stopLoss: number
  takeProfit: number
  parameters: Record<string, any>
}

// 验证结果接口
interface ValidationResults {
  overallScore: number
  expectedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  factorAnalysis: {
    name: string
    rating: number
    description: string
  }[]
  riskMetrics: {
    volatility: number
    beta: number
    var95: number
    informationRatio: number
  }
  suggestions: {
    id: string
    title: string
    content: string
    priority: 'high' | 'medium' | 'low'
    action?: () => void
  }[]
}

const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const selectedTemplate = ref<StrategyTemplate | null>(null)
const isValidating = ref(false)
const validationOptions = ref(['factor_check', 'data_quality', 'quick_backtest'])
const validationResults = ref<ValidationResults | null>(null)
const activeResultTab = ref('factors')

// 策略配置
const strategyConfig = reactive<StrategyConfig>({
  name: '',
  stockPool: 'CSI300',
  dateRange: null,
  maxPositions: 20,
  stopLoss: 0.1,
  takeProfit: 0.3,
  parameters: {}
})

// 策略模板数据
const strategyTemplates = ref<StrategyTemplate[]>([
  {
    id: 'momentum',
    name: '动量策略',
    description: '基于价格动量的选股策略，适合趋势市场',
    icon: 'TrendCharts',
    winRate: 65,
    annualReturn: 18.5,
    tags: ['趋势跟踪', '中频交易', '适合牛市'],
    parameters: [
      {
        name: 'lookback_period',
        label: '回看周期',
        type: 'slider',
        min: 5,
        max: 60,
        step: 5,
        defaultValue: 20
      },
      {
        name: 'momentum_threshold',
        label: '动量阈值',
        type: 'number',
        min: 0,
        max: 1,
        step: 0.01,
        defaultValue: 0.05
      }
    ]
  },
  {
    id: 'mean_reversion',
    name: '均值回归策略',
    description: '基于价格均值回归的选股策略，适合震荡市场',
    icon: 'DataAnalysis',
    winRate: 58,
    annualReturn: 15.2,
    tags: ['均值回归', '低频交易', '适合震荡市'],
    parameters: [
      {
        name: 'reversion_period',
        label: '回归周期',
        type: 'slider',
        min: 10,
        max: 120,
        step: 10,
        defaultValue: 60
      },
      {
        name: 'deviation_threshold',
        label: '偏离阈值',
        type: 'number',
        min: 0.5,
        max: 3,
        step: 0.1,
        defaultValue: 1.5
      }
    ]
  },
  {
    id: 'factor_model',
    name: '多因子模型',
    description: '基于多个因子的综合选股模型',
    icon: 'DataBoard',
    winRate: 72,
    annualReturn: 22.8,
    tags: ['多因子', '机器学习', '稳健性强'],
    parameters: [
      {
        name: 'factor_count',
        label: '因子数量',
        type: 'select',
        options: [
          { label: '5个核心因子', value: 5 },
          { label: '10个主要因子', value: 10 },
          { label: '20个综合因子', value: 20 }
        ],
        defaultValue: 10
      },
      {
        name: 'model_type',
        label: '模型类型',
        type: 'select',
        options: [
          { label: 'LightGBM', value: 'lightgbm' },
          { label: 'XGBoost', value: 'xgboost' },
          { label: '线性回归', value: 'linear' }
        ],
        defaultValue: 'lightgbm'
      }
    ]
  }
])

// 验证检查项
const validationChecks = ref([
  { name: '因子有效性检查', status: 'pending', progress: 0, message: '' },
  { name: '数据质量验证', status: 'pending', progress: 0, message: '' },
  { name: '快速回测验证', status: 'pending', progress: 0, message: '' },
  { name: '风险指标分析', status: 'pending', progress: 0, message: '' },
  { name: '性能预估计算', status: 'pending', progress: 0, message: '' }
])

// 参数建议
const parameterSuggestions = computed(() => {
  const suggestions = []
  
  if (strategyConfig.stopLoss > 0.2) {
    suggestions.push({
      type: 'stop_loss',
      message: '止损比例过高，可能错失反弹机会',
      action: () => { strategyConfig.stopLoss = 0.1 }
    })
  }
  
  if (strategyConfig.maxPositions > 50) {
    suggestions.push({
      type: 'max_positions',
      message: '持仓数量过多，建议控制在30只以内',
      action: () => { strategyConfig.maxPositions = 30 }
    })
  }
  
  return suggestions
})

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return selectedTemplate.value !== null
    case 1:
      return strategyConfig.name && strategyConfig.dateRange
    case 2:
      return validationResults.value !== null
    default:
      return true
  }
})

// 方法
const selectTemplate = (template: StrategyTemplate) => {
  selectedTemplate.value = template
  strategyConfig.name = `${template.name}_${Date.now().toString().slice(-4)}`
  
  // 初始化参数默认值
  template.parameters.forEach(param => {
    strategyConfig.parameters[param.name] = param.defaultValue
  })
}

const nextStep = () => {
  if (canProceed.value && currentStep.value < 3) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const startValidation = async () => {
  isValidating.value = true
  
  // 重置验证状态
  validationChecks.value.forEach(check => {
    check.status = 'pending'
    check.progress = 0
    check.message = ''
  })
  
  // 模拟验证过程
  for (let i = 0; i < validationChecks.value.length; i++) {
    const check = validationChecks.value[i]
    check.status = 'running'
    
    // 模拟进度更新
    for (let progress = 0; progress <= 100; progress += 20) {
      check.progress = progress
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    // 随机成功/失败
    check.status = Math.random() > 0.1 ? 'success' : 'error'
    if (check.status === 'success') {
      check.message = '验证通过'
    } else {
      check.message = '发现潜在问题，但不影响继续'
    }
  }
  
  // 生成验证结果
  await generateValidationResults()
  
  isValidating.value = false
  ElMessage.success('验证完成！')
}

const generateValidationResults = async () => {
  // 模拟生成验证结果
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  validationResults.value = {
    overallScore: Math.floor(Math.random() * 30) + 70, // 70-100
    expectedReturn: Math.random() * 20 + 10, // 10-30%
    maxDrawdown: Math.random() * 15 + 5, // 5-20%
    sharpeRatio: Math.random() * 1 + 1, // 1-2
    factorAnalysis: [
      { name: '价值因子', rating: 4, description: '估值指标表现良好，选股效果显著' },
      { name: '成长因子', rating: 3, description: '成长性指标中等，可考虑优化' },
      { name: '质量因子', rating: 5, description: '财务质量指标优秀，风险控制能力强' }
    ],
    riskMetrics: {
      volatility: Math.random() * 10 + 15, // 15-25%
      beta: Math.random() * 0.5 + 0.8, // 0.8-1.3
      var95: Math.random() * 5 + 3, // 3-8%
      informationRatio: Math.random() * 0.8 + 0.5 // 0.5-1.3
    },
    suggestions: [
      {
        id: 'opt1',
        title: '优化持仓集中度',
        content: '当前策略可能存在行业集中风险，建议增加行业分散化约束',
        priority: 'medium'
      },
      {
        id: 'opt2',
        title: '调整调仓频率',
        content: '建议将调仓频率从日频调整为周频，以降低交易成本',
        priority: 'high'
      }
    ]
  }
}

const applySuggestion = (suggestion: any) => {
  if (suggestion.action) {
    suggestion.action()
    ElMessage.success('建议已应用')
  }
}

const learnMore = (suggestion: any) => {
  ElMessageBox.alert(suggestion.content, suggestion.title)
}

const startFullBacktest = () => {
  router.push('/backtest')
}

const viewStrategy = () => {
  router.push('/results')
}

const createAnother = () => {
  // 重置向导
  currentStep.value = 0
  selectedTemplate.value = null
  validationResults.value = null
  Object.assign(strategyConfig, {
    name: '',
    stockPool: 'CSI300',
    dateRange: null,
    maxPositions: 20,
    stopLoss: 0.1,
    takeProfit: 0.3,
    parameters: {}
  })
}

const skipWizard = () => {
  router.push('/training')
}

const finishWizard = () => {
  ElMessage.success('策略创建完成！')
  router.push('/dashboard')
}

// 工具方法
const getStockPoolLabel = (value: string) => {
  const pools = {
    CSI300: '沪深300',
    CSI500: '中证500',
    CHINEXT: '创业板',
    ALL_A: '全A股'
  }
  return pools[value as keyof typeof pools] || value
}

const formatDateRange = (dateRange: [string, string] | null) => {
  if (!dateRange) return '未设置'
  return `${dateRange[0]} 至 ${dateRange[1]}`
}

// 初始化
onMounted(() => {
  // 设置默认日期范围（最近一年）
  const endDate = new Date()
  const startDate = new Date()
  startDate.setFullYear(endDate.getFullYear() - 1)
  
  strategyConfig.dateRange = [
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0]
  ]
})
</script>

<style scoped lang="scss">
.quick-strategy-wizard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;

  .wizard-header {
    text-align: center;
    margin-bottom: 32px;

    h2 {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin: 0 0 8px 0;
      font-size: 28px;
      color: var(--el-text-color-primary);
    }

    .wizard-subtitle {
      color: var(--el-text-color-regular);
      margin-bottom: 24px;
    }

    .wizard-steps {
      margin: 24px 0;
    }
  }

  .wizard-content {
    min-height: 500px;
    margin-bottom: 24px;

    .step-content {
      h3 {
        margin-bottom: 24px;
        color: var(--el-text-color-primary);
      }
    }
  }

  .template-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;

    .template-card {
      border: 2px solid var(--el-border-color);
      border-radius: 8px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        border-color: var(--el-color-primary);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      &.active {
        border-color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
      }

      .template-icon {
        text-align: center;
        margin-bottom: 12px;
        color: var(--el-color-primary);
      }

      h4 {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }

      p {
        color: var(--el-text-color-regular);
        margin-bottom: 12px;
        line-height: 1.5;
      }

      .template-stats {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;

        .stat {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }

      .template-tags {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
  }

  .config-layout {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 24px;

    .config-form {
      h4 {
        margin: 24px 0 16px 0;
        color: var(--el-text-color-primary);
        border-bottom: 1px solid var(--el-border-color);
        padding-bottom: 8px;
      }
    }

    .config-preview {
      .preview-content {
        h4 {
          margin-bottom: 16px;
        }

        .suggestions {
          margin-top: 16px;

          h5 {
            margin-bottom: 8px;
            color: var(--el-text-color-primary);
          }

          .suggestion-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            background-color: var(--el-color-warning-light-9);
            border-radius: 4px;
            margin-bottom: 8px;
          }
        }
      }
    }
  }

  .validation-content {
    .validation-options {
      margin-bottom: 24px;

      h4 {
        margin-bottom: 16px;
      }
    }

    .validation-progress {
      margin-bottom: 24px;

      .check-item {
        margin-bottom: 16px;

        .check-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;

          .check-name {
            font-weight: 500;
          }
        }

        .check-message {
          margin: 8px 0 0 0;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }

    .validation-results {
      .results-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;

        .result-item {
          text-align: center;
        }
      }

      .factor-item {
        margin-bottom: 16px;
        padding: 12px;
        border: 1px solid var(--el-border-color);
        border-radius: 4px;

        .factor-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;

          .factor-name {
            font-weight: 500;
          }
        }

        .factor-description {
          margin: 0;
          color: var(--el-text-color-regular);
        }
      }

      .optimization-suggestions {
        .suggestion-card {
          margin-bottom: 16px;
          padding: 16px;
          border: 1px solid var(--el-border-color);
          border-radius: 8px;

          .suggestion-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .suggestion-title {
              font-weight: 500;
              flex: 1;
            }
          }

          .suggestion-content {
            margin: 8px 0;
            color: var(--el-text-color-regular);
          }

          .suggestion-actions {
            display: flex;
            gap: 8px;
          }
        }
      }
    }
  }

  .completion-content {
    .completion-actions {
      display: flex;
      gap: 16px;
      justify-content: center;
      margin-bottom: 32px;
    }

    .strategy-summary {
      margin-bottom: 24px;
    }

    .next-steps {
      .next-step-list {
        .next-step-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          border: 1px solid var(--el-border-color);
          border-radius: 8px;
          margin-bottom: 12px;

          .step-content {
            flex: 1;

            h5 {
              margin: 0 0 4px 0;
            }

            p {
              margin: 0;
              color: var(--el-text-color-regular);
            }
          }
        }
      }
    }
  }

  .wizard-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-top: 1px solid var(--el-border-color);

    .controls-right {
      display: flex;
      gap: 12px;
    }
  }
}

@media (max-width: 768px) {
  .quick-strategy-wizard {
    padding: 16px;

    .config-layout {
      grid-template-columns: 1fr;
    }

    .template-grid {
      grid-template-columns: 1fr;
    }

    .completion-actions {
      flex-direction: column;

      .el-button {
        width: 100%;
      }
    }
  }
}
</style>