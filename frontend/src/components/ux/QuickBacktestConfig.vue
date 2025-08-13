<template>
  <div class="quick-backtest-config">
    <div class="config-header">
      <h3>
        <el-icon><Histogram /></el-icon>
        快速回测配置
      </h3>
      <p>简化配置流程，快速验证策略效果</p>
    </div>

    <!-- 快速配置模式选择 -->
    <el-card class="mode-selector" shadow="never">
      <template #header>
        <h4>配置模式</h4>
      </template>
      <el-radio-group v-model="configMode" class="mode-options">
        <el-radio-button label="express">极速模式</el-radio-button>
        <el-radio-button label="guided">引导模式</el-radio-button>
        <el-radio-button label="template">模板模式</el-radio-button>
      </el-radio-group>
      <div class="mode-description">
        <p v-if="configMode === 'express'">
          使用默认最优参数，1分钟内完成配置
        </p>
        <p v-else-if="configMode === 'guided'">
          分步骤引导配置，适合新手用户
        </p>
        <p v-else>
          从预设模板开始，快速定制配置
        </p>
      </div>
    </el-card>

    <!-- 极速模式 -->
    <div v-if="configMode === 'express'" class="config-content">
      <el-card class="express-config">
        <template #header>
          <div class="card-header">
            <h4>极速配置</h4>
            <el-tag type="success">推荐</el-tag>
          </div>
        </template>

        <el-form :model="expressConfig" label-width="100px">
          <el-form-item label="策略选择">
            <el-select v-model="expressConfig.strategy" placeholder="选择已有策略">
              <el-option
                v-for="strategy in availableStrategies"
                :key="strategy.id"
                :label="strategy.name"
                :value="strategy.id"
              >
                <div class="strategy-option">
                  <span class="strategy-name">{{ strategy.name }}</span>
                  <span class="strategy-performance">年化: {{ strategy.annualReturn }}%</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="时间范围">
            <el-select v-model="expressConfig.timeRange">
              <el-option label="最近1年" value="1y" />
              <el-option label="最近2年" value="2y" />
              <el-option label="最近3年" value="3y" />
              <el-option label="最近5年" value="5y" />
            </el-select>
          </el-form-item>

          <el-form-item label="股票池">
            <el-select v-model="expressConfig.universe">
              <el-option label="沪深300" value="CSI300" />
              <el-option label="中证500" value="CSI500" />
              <el-option label="创业板" value="CHINEXT" />
            </el-select>
          </el-form-item>

          <!-- 预估结果 -->
          <div class="express-preview">
            <h5>预估结果</h5>
            <el-row :gutter="16">
              <el-col :span="6">
                <el-statistic title="预计耗时" value="2-5" suffix="分钟" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="数据量" :value="estimatedDataSize" suffix="万条" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="预期胜率" :value="estimatedWinRate" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="信心指数" :value="confidenceScore" suffix="/100" />
              </el-col>
            </el-row>
          </div>
        </el-form>

        <div class="express-actions">
          <el-button type="primary" size="large" @click="startExpressBacktest" :loading="isRunning">
            <el-icon><VideoPlay /></el-icon>
            立即开始回测
          </el-button>
          <el-button @click="configMode = 'guided'">
            更多配置选项
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 引导模式 -->
    <div v-if="configMode === 'guided'" class="config-content">
      <el-steps :active="guidedStep" align-center class="guided-steps">
        <el-step title="基础设置" />
        <el-step title="策略配置" />
        <el-step title="风险控制" />
        <el-step title="执行确认" />
      </el-steps>

      <!-- 步骤1: 基础设置 -->
      <el-card v-if="guidedStep === 0" class="guided-card">
        <template #header>
          <h4>步骤 1: 基础设置</h4>
        </template>

        <el-form :model="guidedConfig" label-width="120px">
          <el-form-item label="回测名称" required>
            <el-input v-model="guidedConfig.name" placeholder="为本次回测起个名字" />
          </el-form-item>

          <el-form-item label="回测时间范围" required>
            <el-date-picker
              v-model="guidedConfig.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <el-form-item label="交易频率">
            <el-radio-group v-model="guidedConfig.frequency">
              <el-radio label="daily">日频交易</el-radio>
              <el-radio label="weekly">周频交易</el-radio>
              <el-radio label="monthly">月频交易</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="基准指数">
            <el-select v-model="guidedConfig.benchmark">
              <el-option label="沪深300指数" value="CSI300" />
              <el-option label="中证500指数" value="CSI500" />
              <el-option label="创业板指数" value="CHINEXT" />
              <el-option label="上证指数" value="SZZS" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 步骤2: 策略配置 -->
      <el-card v-if="guidedStep === 1" class="guided-card">
        <template #header>
          <h4>步骤 2: 策略配置</h4>
        </template>

        <el-form :model="guidedConfig" label-width="120px">
          <el-form-item label="策略类型">
            <el-select v-model="guidedConfig.strategyType" @change="onStrategyTypeChange">
              <el-option label="因子选股策略" value="factor" />
              <el-option label="机器学习策略" value="ml" />
              <el-option label="技术指标策略" value="technical" />
              <el-option label="基本面策略" value="fundamental" />
            </el-select>
          </el-form-item>

          <!-- 因子选股配置 -->
          <div v-if="guidedConfig.strategyType === 'factor'">
            <el-form-item label="选择因子">
              <el-transfer
                v-model="guidedConfig.selectedFactors"
                :data="availableFactors"
                :titles="['可用因子', '已选因子']"
                filterable
              />
            </el-form-item>

            <el-form-item label="因子权重">
              <el-radio-group v-model="guidedConfig.factorWeighting">
                <el-radio label="equal">等权重</el-radio>
                <el-radio label="ic">IC加权</el-radio>
                <el-radio label="custom">自定义</el-radio>
              </el-radio-group>
            </el-form-item>
          </div>

          <!-- 机器学习配置 -->
          <div v-if="guidedConfig.strategyType === 'ml'">
            <el-form-item label="模型选择">
              <el-select v-model="guidedConfig.mlModel">
                <el-option label="LightGBM" value="lightgbm" />
                <el-option label="XGBoost" value="xgboost" />
                <el-option label="随机森林" value="rf" />
                <el-option label="线性回归" value="linear" />
              </el-select>
            </el-form-item>

            <el-form-item label="特征选择">
              <el-checkbox-group v-model="guidedConfig.features">
                <el-checkbox label="price">价格特征</el-checkbox>
                <el-checkbox label="volume">成交量特征</el-checkbox>
                <el-checkbox label="technical">技术指标</el-checkbox>
                <el-checkbox label="fundamental">基本面数据</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>

          <el-form-item label="股票池">
            <el-checkbox-group v-model="guidedConfig.stockUniverse">
              <el-checkbox label="CSI300">沪深300</el-checkbox>
              <el-checkbox label="CSI500">中证500</el-checkbox>
              <el-checkbox label="CHINEXT">创业板</el-checkbox>
              <el-checkbox label="ALL_A">全A股</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 步骤3: 风险控制 -->
      <el-card v-if="guidedStep === 2" class="guided-card">
        <template #header>
          <h4>步骤 3: 风险控制</h4>
        </template>

        <el-form :model="guidedConfig" label-width="120px">
          <el-form-item label="持仓控制">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.maxPositions"
                  :min="1"
                  :max="100"
                  controls-position="right"
                />
                <span class="input-suffix">最大持仓数</span>
              </el-col>
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.maxWeight"
                  :min="0.01"
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                  controls-position="right"
                />
                <span class="input-suffix">单股最大权重</span>
              </el-col>
            </el-row>
          </el-form-item>

          <el-form-item label="止损止盈">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.stopLoss"
                  :min="0"
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                  controls-position="right"
                />
                <span class="input-suffix">止损比例</span>
              </el-col>
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.takeProfit"
                  :min="0"
                  :max="2"
                  :step="0.01"
                  :precision="2"
                  controls-position="right"
                />
                <span class="input-suffix">止盈比例</span>
              </el-col>
            </el-row>
          </el-form-item>

          <el-form-item label="行业限制">
            <el-switch v-model="guidedConfig.industryLimit" />
            <span class="form-help">启用行业分散化约束</span>
          </el-form-item>

          <el-form-item v-if="guidedConfig.industryLimit" label="行业权重限制">
            <el-slider
              v-model="guidedConfig.maxIndustryWeight"
              :min="0.05"
              :max="0.5"
              :step="0.05"
              :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
              show-input
            />
          </el-form-item>

          <el-form-item label="交易成本">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.commissionRate"
                  :min="0"
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  controls-position="right"
                />
                <span class="input-suffix">佣金费率</span>
              </el-col>
              <el-col :span="12">
                <el-input-number
                  v-model="guidedConfig.impactCost"
                  :min="0"
                  :max="0.01"
                  :step="0.0001"
                  :precision="4"
                  controls-position="right"
                />
                <span class="input-suffix">冲击成本</span>
              </el-col>
            </el-row>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 步骤4: 执行确认 -->
      <el-card v-if="guidedStep === 3" class="guided-card">
        <template #header>
          <h4>步骤 4: 执行确认</h4>
        </template>

        <div class="config-summary">
          <h5>配置摘要</h5>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="回测名称">{{ guidedConfig.name }}</el-descriptions-item>
            <el-descriptions-item label="时间范围">{{ formatDateRange(guidedConfig.dateRange) }}</el-descriptions-item>
            <el-descriptions-item label="策略类型">{{ getStrategyTypeLabel(guidedConfig.strategyType) }}</el-descriptions-item>
            <el-descriptions-item label="交易频率">{{ getFrequencyLabel(guidedConfig.frequency) }}</el-descriptions-item>
            <el-descriptions-item label="股票池">{{ guidedConfig.stockUniverse.join(', ') }}</el-descriptions-item>
            <el-descriptions-item label="基准指数">{{ getBenchmarkLabel(guidedConfig.benchmark) }}</el-descriptions-item>
          </el-descriptions>

          <div class="risk-summary">
            <h5>风险参数</h5>
            <el-row :gutter="16">
              <el-col :span="6">
                <el-statistic title="最大持仓" :value="guidedConfig.maxPositions" suffix="只" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="止损比例" :value="guidedConfig.stopLoss * 100" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="止盈比例" :value="guidedConfig.takeProfit * 100" suffix="%" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="佣金费率" :value="guidedConfig.commissionRate * 10000" suffix="‱" />
              </el-col>
            </el-row>
          </div>

          <div class="execution-estimate">
            <h5>执行预估</h5>
            <el-alert type="info" :closable="false">
              <p>预计执行时间: {{ estimatedExecutionTime }} 分钟</p>
              <p>数据处理量: {{ estimatedDataVolume }} 万条记录</p>
              <p>计算复杂度: {{ estimatedComplexity }}</p>
            </el-alert>
          </div>
        </div>
      </el-card>

      <!-- 引导模式控制按钮 -->
      <div class="guided-controls">
        <el-button v-if="guidedStep > 0" @click="guidedStep--">
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
        
        <div class="controls-right">
          <el-button v-if="guidedStep < 3" type="primary" @click="guidedStep++">
            下一步
            <el-icon><ArrowRight /></el-icon>
          </el-button>
          
          <el-button
            v-if="guidedStep === 3"
            type="success"
            @click="startGuidedBacktest"
            :loading="isRunning"
          >
            <el-icon><VideoPlay /></el-icon>
            开始回测
          </el-button>
        </div>
      </div>
    </div>

    <!-- 模板模式 -->
    <div v-if="configMode === 'template'" class="config-content">
      <el-card class="template-selector">
        <template #header>
          <h4>选择配置模板</h4>
        </template>

        <div class="template-grid">
          <div
            v-for="template in configTemplates"
            :key="template.id"
            class="template-item"
            :class="{ active: selectedTemplate?.id === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="template-header">
              <h5>{{ template.name }}</h5>
              <el-tag :type="template.difficulty === 'easy' ? 'success' : template.difficulty === 'medium' ? 'warning' : 'danger'">
                {{ getDifficultyLabel(template.difficulty) }}
              </el-tag>
            </div>
            <p class="template-description">{{ template.description }}</p>
            <div class="template-features">
              <el-tag v-for="feature in template.features" :key="feature" size="small">
                {{ feature }}
              </el-tag>
            </div>
            <div class="template-stats">
              <span>适用场景: {{ template.scenario }}</span>
              <span>预计耗时: {{ template.estimatedTime }}分钟</span>
            </div>
          </div>
        </div>

        <!-- 模板配置 -->
        <div v-if="selectedTemplate" class="template-config">
          <h5>模板配置</h5>
          <el-form :model="templateConfig" label-width="120px">
            <el-form-item
              v-for="param in selectedTemplate.parameters"
              :key="param.name"
              :label="param.label"
            >
              <component
                :is="getFormComponent(param.type)"
                v-model="templateConfig[param.name]"
                v-bind="getComponentProps(param)"
              />
              <span v-if="param.help" class="form-help">{{ param.help }}</span>
            </el-form-item>
          </el-form>

          <div class="template-actions">
            <el-button type="primary" @click="startTemplateBacktest" :loading="isRunning">
              <el-icon><VideoPlay /></el-icon>
              使用此模板开始回测
            </el-button>
            <el-button @click="customizeTemplate">
              自定义模板
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 运行状态显示 -->
    <el-dialog v-model="showProgress" title="回测进行中" width="600px" :close-on-click-modal="false">
      <div class="progress-content">
        <el-progress :percentage="progressPercentage" :status="progressStatus" />
        <p class="progress-message">{{ progressMessage }}</p>
        
        <div class="progress-details">
          <el-timeline>
            <el-timeline-item
              v-for="step in progressSteps"
              :key="step.name"
              :timestamp="step.timestamp"
              :type="step.status"
            >
              {{ step.message }}
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="cancelBacktest" :disabled="progressPercentage === 100">
          {{ progressPercentage === 100 ? '完成' : '取消' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Histogram, VideoPlay, ArrowLeft, ArrowRight
} from '@element-plus/icons-vue'

interface Strategy {
  id: string
  name: string
  annualReturn: number
  description: string
}

interface ConfigTemplate {
  id: string
  name: string
  description: string
  difficulty: 'easy' | 'medium' | 'hard'
  features: string[]
  scenario: string
  estimatedTime: number
  parameters: TemplateParameter[]
}

interface TemplateParameter {
  name: string
  label: string
  type: string
  options?: any[]
  min?: number
  max?: number
  step?: number
  help?: string
  defaultValue?: any
}

const router = useRouter()

// 响应式数据
const configMode = ref('express')
const guidedStep = ref(0)
const selectedTemplate = ref<ConfigTemplate | null>(null)
const isRunning = ref(false)
const showProgress = ref(false)
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | 'warning' | ''>('')
const progressMessage = ref('')

// 配置数据
const expressConfig = reactive({
  strategy: '',
  timeRange: '2y',
  universe: 'CSI300'
})

const guidedConfig = reactive({
  name: '',
  dateRange: null as [string, string] | null,
  frequency: 'daily',
  benchmark: 'CSI300',
  strategyType: 'factor',
  selectedFactors: [] as string[],
  factorWeighting: 'equal',
  mlModel: 'lightgbm',
  features: [] as string[],
  stockUniverse: ['CSI300'],
  maxPositions: 20,
  maxWeight: 0.1,
  stopLoss: 0.1,
  takeProfit: 0.3,
  industryLimit: false,
  maxIndustryWeight: 0.3,
  commissionRate: 0.0003,
  impactCost: 0.001
})

const templateConfig = reactive<Record<string, any>>({})

// 模拟数据
const availableStrategies = ref<Strategy[]>([
  { id: '1', name: '多因子选股策略', annualReturn: 18.5, description: '基于多个财务和技术因子的选股策略' },
  { id: '2', name: '动量策略', annualReturn: 15.2, description: '基于价格动量的趋势跟踪策略' },
  { id: '3', name: '价值投资策略', annualReturn: 12.8, description: '基于估值指标的价值投资策略' }
])

const availableFactors = ref([
  { key: 'pe', label: '市盈率' },
  { key: 'pb', label: '市净率' },
  { key: 'roe', label: 'ROE' },
  { key: 'roa', label: 'ROA' },
  { key: 'momentum', label: '动量因子' },
  { key: 'reversal', label: '反转因子' }
])

const configTemplates = ref<ConfigTemplate[]>([
  {
    id: 'quick_factor',
    name: '快速因子策略',
    description: '使用经典因子的简单策略模板',
    difficulty: 'easy',
    features: ['多因子', '风险控制', '自动调仓'],
    scenario: '适合初学者快速体验',
    estimatedTime: 5,
    parameters: [
      {
        name: 'factor_count',
        label: '因子数量',
        type: 'select',
        options: [
          { label: '3个核心因子', value: 3 },
          { label: '5个主要因子', value: 5 },
          { label: '10个综合因子', value: 10 }
        ],
        defaultValue: 5
      },
      {
        name: 'rebalance_freq',
        label: '调仓频率',
        type: 'select',
        options: [
          { label: '日频', value: 'daily' },
          { label: '周频', value: 'weekly' },
          { label: '月频', value: 'monthly' }
        ],
        defaultValue: 'weekly'
      }
    ]
  },
  {
    id: 'ml_strategy',
    name: '机器学习策略',
    description: '基于机器学习模型的高级策略模板',
    difficulty: 'medium',
    features: ['机器学习', '特征工程', '模型调优'],
    scenario: '适合有一定经验的用户',
    estimatedTime: 15,
    parameters: [
      {
        name: 'model_type',
        label: '模型类型',
        type: 'select',
        options: [
          { label: 'LightGBM', value: 'lightgbm' },
          { label: 'XGBoost', value: 'xgboost' },
          { label: '随机森林', value: 'rf' }
        ],
        defaultValue: 'lightgbm'
      },
      {
        name: 'feature_importance_threshold',
        label: '特征重要性阈值',
        type: 'slider',
        min: 0.01,
        max: 0.1,
        step: 0.01,
        defaultValue: 0.05
      }
    ]
  }
])

const progressSteps = ref([
  { name: 'init', message: '初始化回测环境', timestamp: '', status: 'primary' },
  { name: 'data', message: '加载历史数据', timestamp: '', status: 'primary' },
  { name: 'factor', message: '计算因子值', timestamp: '', status: 'primary' },
  { name: 'signal', message: '生成交易信号', timestamp: '', status: 'primary' },
  { name: 'backtest', message: '执行回测', timestamp: '', status: 'primary' },
  { name: 'analysis', message: '分析结果', timestamp: '', status: 'primary' }
])

// 计算属性
const estimatedDataSize = computed(() => {
  const timeRangeMultiplier = { '1y': 50, '2y': 100, '3y': 150, '5y': 250 }
  return timeRangeMultiplier[expressConfig.timeRange as keyof typeof timeRangeMultiplier] || 100
})

const estimatedWinRate = computed(() => {
  const selectedStrategy = availableStrategies.value.find(s => s.id === expressConfig.strategy)
  return selectedStrategy ? Math.floor(selectedStrategy.annualReturn * 3) : 65
})

const confidenceScore = computed(() => {
  return Math.min(95, Math.floor(estimatedWinRate.value + Math.random() * 10))
})

const estimatedExecutionTime = computed(() => {
  let baseTime = 5
  if (guidedConfig.strategyType === 'ml') baseTime += 10
  if (guidedConfig.stockUniverse.length > 1) baseTime += 5
  return baseTime
})

const estimatedDataVolume = computed(() => {
  return Math.floor(guidedConfig.stockUniverse.length * 50 * 2.5)
})

const estimatedComplexity = computed(() => {
  if (guidedConfig.strategyType === 'ml') return '高'
  if (guidedConfig.selectedFactors.length > 5) return '中'
  return '低'
})

// 方法
const startExpressBacktest = async () => {
  if (!expressConfig.strategy) {
    ElMessage.warning('请选择策略')
    return
  }
  
  isRunning.value = true
  showProgress.value = true
  await simulateBacktestExecution()
}

const startGuidedBacktest = async () => {
  if (!guidedConfig.name || !guidedConfig.dateRange) {
    ElMessage.warning('请完善必填信息')
    return
  }
  
  isRunning.value = true
  showProgress.value = true
  await simulateBacktestExecution()
}

const startTemplateBacktest = async () => {
  if (!selectedTemplate.value) {
    ElMessage.warning('请选择模板')
    return
  }
  
  isRunning.value = true
  showProgress.value = true
  await simulateBacktestExecution()
}

const simulateBacktestExecution = async () => {
  progressPercentage.value = 0
  progressMessage.value = '准备开始回测...'
  
  for (let i = 0; i < progressSteps.value.length; i++) {
    const step = progressSteps.value[i]
    step.status = 'warning'
    step.timestamp = new Date().toLocaleTimeString()
    progressMessage.value = step.message + '中...'
    
    // 模拟执行时间
    for (let j = 0; j < 100; j += 20) {
      progressPercentage.value = Math.floor((i * 100 + j) / progressSteps.value.length)
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    step.status = 'success'
    step.timestamp = new Date().toLocaleTimeString()
  }
  
  progressPercentage.value = 100
  progressStatus.value = 'success'
  progressMessage.value = '回测完成！'
  
  ElMessage.success('回测执行完成！')
  
  // 跳转到结果页面
  setTimeout(() => {
    showProgress.value = false
    isRunning.value = false
    router.push('/results')
  }, 2000)
}

const cancelBacktest = () => {
  if (progressPercentage.value === 100) {
    showProgress.value = false
    isRunning.value = false
  } else {
    ElMessageBox.confirm('确定要取消回测吗？', '确认', {
      type: 'warning'
    }).then(() => {
      showProgress.value = false
      isRunning.value = false
      progressPercentage.value = 0
      ElMessage.info('回测已取消')
    })
  }
}

const selectTemplate = (template: ConfigTemplate) => {
  selectedTemplate.value = template
  
  // 初始化模板配置
  template.parameters.forEach(param => {
    templateConfig[param.name] = param.defaultValue
  })
}

const customizeTemplate = () => {
  configMode.value = 'guided'
  guidedStep.value = 0
}

const onStrategyTypeChange = (type: string) => {
  // 根据策略类型清空相关配置
  if (type !== 'factor') {
    guidedConfig.selectedFactors = []
  }
  if (type !== 'ml') {
    guidedConfig.features = []
  }
}

// 工具方法
const getStrategyTypeLabel = (type: string) => {
  const labels = {
    factor: '因子选股策略',
    ml: '机器学习策略',
    technical: '技术指标策略',
    fundamental: '基本面策略'
  }
  return labels[type as keyof typeof labels] || type
}

const getFrequencyLabel = (freq: string) => {
  const labels = {
    daily: '日频交易',
    weekly: '周频交易',
    monthly: '月频交易'
  }
  return labels[freq as keyof typeof labels] || freq
}

const getBenchmarkLabel = (benchmark: string) => {
  const labels = {
    CSI300: '沪深300指数',
    CSI500: '中证500指数',
    CHINEXT: '创业板指数',
    SZZS: '上证指数'
  }
  return labels[benchmark as keyof typeof labels] || benchmark
}

const getDifficultyLabel = (difficulty: string) => {
  const labels = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return labels[difficulty as keyof typeof labels] || difficulty
}

const formatDateRange = (dateRange: [string, string] | null) => {
  if (!dateRange) return '未设置'
  return `${dateRange[0]} 至 ${dateRange[1]}`
}

const getFormComponent = (type: string) => {
  const components = {
    select: 'el-select',
    slider: 'el-slider',
    number: 'el-input-number',
    text: 'el-input'
  }
  return components[type as keyof typeof components] || 'el-input'
}

const getComponentProps = (param: TemplateParameter) => {
  const props: any = {}
  
  if (param.type === 'select' && param.options) {
    props.options = param.options
  }
  
  if (param.type === 'slider') {
    props.min = param.min
    props.max = param.max
    props.step = param.step
  }
  
  if (param.type === 'number') {
    props.min = param.min
    props.max = param.max
    props.step = param.step
  }
  
  return props
}

// 监听器
watch(configMode, (newMode) => {
  if (newMode === 'guided') {
    guidedStep.value = 0
  }
})
</script>

<style scoped lang="scss">
.quick-backtest-config {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;

  .config-header {
    text-align: center;
    margin-bottom: 32px;

    h3 {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin: 0 0 8px 0;
      font-size: 24px;
      color: var(--el-text-color-primary);
    }

    p {
      color: var(--el-text-color-regular);
      margin: 0;
    }
  }

  .mode-selector {
    margin-bottom: 24px;

    .mode-options {
      display: flex;
      justify-content: center;
      margin-bottom: 16px;
    }

    .mode-description {
      text-align: center;
      color: var(--el-text-color-regular);
    }
  }

  .config-content {
    .express-config {
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .strategy-option {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .strategy-performance {
          color: var(--el-color-success);
          font-size: 12px;
        }
      }

      .express-preview {
        margin: 24px 0;
        padding: 16px;
        background-color: var(--el-color-info-light-9);
        border-radius: 8px;

        h5 {
          margin-bottom: 16px;
        }
      }

      .express-actions {
        text-align: center;
        margin-top: 24px;

        .el-button {
          margin: 0 8px;
        }
      }
    }

    .guided-steps {
      margin-bottom: 24px;
    }

    .guided-card {
      margin-bottom: 24px;
      min-height: 400px;
    }

    .guided-controls {
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

    .template-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 16px;
      margin-bottom: 24px;

      .template-item {
        border: 2px solid var(--el-border-color);
        border-radius: 8px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          border-color: var(--el-color-primary);
        }

        &.active {
          border-color: var(--el-color-primary);
          background-color: var(--el-color-primary-light-9);
        }

        .template-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          h5 {
            margin: 0;
          }
        }

        .template-description {
          color: var(--el-text-color-regular);
          margin-bottom: 12px;
        }

        .template-features {
          margin-bottom: 12px;

          .el-tag {
            margin-right: 8px;
            margin-bottom: 4px;
          }
        }

        .template-stats {
          font-size: 14px;
          color: var(--el-text-color-regular);

          span {
            display: block;
            margin-bottom: 4px;
          }
        }
      }
    }

    .template-config {
      border-top: 1px solid var(--el-border-color);
      padding-top: 16px;

      h5 {
        margin-bottom: 16px;
      }

      .template-actions {
        text-align: center;
        margin-top: 24px;

        .el-button {
          margin: 0 8px;
        }
      }
    }
  }

  .input-suffix {
    margin-left: 8px;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }

  .form-help {
    margin-left: 8px;
    color: var(--el-text-color-placeholder);
    font-size: 12px;
  }

  .config-summary {
    h5 {
      margin-bottom: 16px;
      color: var(--el-text-color-primary);
    }

    .risk-summary {
      margin: 24px 0;
    }

    .execution-estimate {
      margin: 24px 0;
    }
  }

  .progress-content {
    .progress-message {
      text-align: center;
      margin: 16px 0;
      color: var(--el-text-color-regular);
    }

    .progress-details {
      margin-top: 24px;
      max-height: 300px;
      overflow-y: auto;
    }
  }
}

@media (max-width: 768px) {
  .quick-backtest-config {
    padding: 16px;

    .template-grid {
      grid-template-columns: 1fr;
    }

    .express-actions,
    .template-actions {
      .el-button {
        width: 100%;
        margin: 4px 0;
      }
    }
  }
}
</style>