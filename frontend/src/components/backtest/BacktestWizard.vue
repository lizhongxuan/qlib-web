<template>
  <div class="backtest-wizard">
    <el-card class="wizard-card">
      <template #header>
        <div class="wizard-header">
          <h3>回测配置向导</h3>
          <el-steps :active="currentStep" finish-status="success" align-center>
            <el-step title="基本配置" icon="Setting" />
            <el-step title="策略参数" icon="Tools" />
            <el-step title="风险控制" icon="Warning" />
            <el-step title="确认启动" icon="VideoPlay" />
          </el-steps>
        </div>
      </template>

      <!-- 步骤1: 基本配置 -->
      <div v-if="currentStep === 0" class="step-content">
        <h4>基本配置</h4>
        
        <div class="config-section">
          <h5>策略信息</h5>
          <el-form :model="config.basic" label-width="120px" :rules="basicRules" ref="basicFormRef">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="策略名称" prop="name" required>
                  <el-input 
                    v-model="config.basic.name" 
                    placeholder="输入策略名称"
                    maxlength="50"
                    show-word-limit
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="策略类型" prop="type">
                  <el-select v-model="config.basic.type" style="width: 100%">
                    <el-option label="TopK选股策略" value="topk" />
                    <el-option label="权重优化策略" value="weight_opt" />
                    <el-option label="对冲策略" value="hedge" />
                    <el-option label="自定义策略" value="custom" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="股票池" prop="universe">
                  <el-select v-model="config.basic.universe" style="width: 100%">
                    <el-option label="沪深300" value="HS300" />
                    <el-option label="中证500" value="ZZ500" />
                    <el-option label="中证1000" value="ZZ1000" />
                    <el-option label="全A股" value="ALL" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="基准指数" prop="benchmark">
                  <el-select v-model="config.basic.benchmark" style="width: 100%">
                    <el-option label="沪深300" value="000300" />
                    <el-option label="中证500" value="000905" />
                    <el-option label="上证50" value="000016" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="初始资金" prop="initialCapital">
                  <el-input-number 
                    v-model="config.basic.initialCapital" 
                    :min="100000" 
                    :max="100000000"
                    :step="100000"
                    style="width: 100%"
                    controls-position="right"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="回测时间范围" prop="dateRange" required>
              <el-date-picker
                v-model="config.basic.dateRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                :disabled-date="disabledDate"
              />
            </el-form-item>
          </el-form>
        </div>

        <div class="config-section">
          <h5>数据源配置</h5>
          <el-form :model="config.basic" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="数据频率">
                  <el-select v-model="config.basic.dataFreq" style="width: 100%">
                    <el-option label="日频" value="daily" />
                    <el-option label="周频" value="weekly" />
                    <el-option label="月频" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="复权方式">
                  <el-select v-model="config.basic.adjustType" style="width: 100%">
                    <el-option label="前复权" value="pre" />
                    <el-option label="后复权" value="post" />
                    <el-option label="不复权" value="none" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </div>

      <!-- 步骤2: 策略参数 -->
      <div v-if="currentStep === 1" class="step-content">
        <h4>策略参数配置</h4>
        
        <div class="config-section">
          <h5>选股配置</h5>
          <el-form :model="config.strategy" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="持仓数量">
                  <el-input-number 
                    v-model="config.strategy.topK" 
                    :min="5" 
                    :max="100"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="调仓频率">
                  <el-select v-model="config.strategy.rebalanceFreq" style="width: 100%">
                    <el-option label="每日调仓" value="daily" />
                    <el-option label="每周调仓" value="weekly" />
                    <el-option label="每月调仓" value="monthly" />
                    <el-option label="每季度调仓" value="quarterly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="换仓阈值">
                  <el-input-number 
                    v-model="config.strategy.turnoverThreshold" 
                    :min="0" 
                    :max="1"
                    :step="0.1"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="config-section">
          <h5>交易成本</h5>
          <el-form :model="config.strategy" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="手续费率">
                  <el-input-number 
                    v-model="config.strategy.commission" 
                    :min="0" 
                    :max="0.01"
                    :step="0.0001"
                    :precision="4"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="印花税">
                  <el-input-number 
                    v-model="config.strategy.stampDuty" 
                    :min="0" 
                    :max="0.01"
                    :step="0.0001"
                    :precision="4"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="滑点">
                  <el-input-number 
                    v-model="config.strategy.slippage" 
                    :min="0" 
                    :max="0.01"
                    :step="0.0001"
                    :precision="4"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="config-section">
          <h5>高级配置</h5>
          <el-form :model="config.strategy" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="涨跌停处理">
                  <el-switch
                    v-model="config.strategy.handleLimit"
                    active-text="自动处理"
                    inactive-text="忽略"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="停牌股票">
                  <el-switch
                    v-model="config.strategy.handleSuspension"
                    active-text="自动剔除"
                    inactive-text="保持持仓"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </div>

      <!-- 步骤3: 风险控制 -->
      <div v-if="currentStep === 2" class="step-content">
        <h4>风险控制配置</h4>
        
        <div class="config-section">
          <h5>风险限制</h5>
          <el-form :model="config.risk" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="8">
                <el-form-item label="最大回撤限制">
                  <el-input-number 
                    v-model="config.risk.maxDrawdown" 
                    :min="0" 
                    :max="1"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="单股最大权重">
                  <el-input-number 
                    v-model="config.risk.maxWeight" 
                    :min="0" 
                    :max="0.5"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="止损阈值">
                  <el-input-number 
                    v-model="config.risk.stopLoss" 
                    :min="0" 
                    :max="0.5"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <div class="config-section">
          <h5>行业限制</h5>
          <el-form :model="config.risk" label-width="120px">
            <el-form-item label="启用行业限制">
              <el-switch
                v-model="config.risk.enableSectorLimit"
                active-text="启用"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <div v-if="config.risk.enableSectorLimit" class="sector-limits">
              <el-table :data="sectorLimits" size="small">
                <el-table-column prop="sector" label="行业" width="120" />
                <el-table-column label="权重限制">
                  <template #default="{ row }">
                    <el-input-number
                      v-model="row.limit"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      :precision="2"
                      size="small"
                      style="width: 120px"
                    />
                  </template>
                </el-table-column>
                <el-table-column prop="current" label="当前权重" width="100">
                  <template #default="{ row }">
                    {{ (row.current * 100).toFixed(1) }}%
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-form>
        </div>

        <div class="config-section">
          <h5>动态风控</h5>
          <el-form :model="config.risk" label-width="120px">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="市场波动调整">
                  <el-switch
                    v-model="config.risk.volatilityAdjust"
                    active-text="启用"
                    inactive-text="关闭"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="相关性检查">
                  <el-switch
                    v-model="config.risk.correlationCheck"
                    active-text="启用"
                    inactive-text="关闭"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </div>

      <!-- 步骤4: 确认启动 -->
      <div v-if="currentStep === 3" class="step-content">
        <h4>配置确认</h4>
        
        <div class="config-summary">
          <el-descriptions title="回测配置摘要" :column="2" border>
            <el-descriptions-item label="策略名称">
              {{ config.basic.name }}
            </el-descriptions-item>
            <el-descriptions-item label="策略类型">
              {{ getStrategyTypeText(config.basic.type) }}
            </el-descriptions-item>
            <el-descriptions-item label="股票池">
              {{ config.basic.universe }}
            </el-descriptions-item>
            <el-descriptions-item label="基准指数">
              {{ config.basic.benchmark }}
            </el-descriptions-item>
            <el-descriptions-item label="初始资金">
              ¥{{ config.basic.initialCapital.toLocaleString() }}
            </el-descriptions-item>
            <el-descriptions-item label="回测时间">
              {{ config.basic.dateRange[0] }} 至 {{ config.basic.dateRange[1] }}
            </el-descriptions-item>
            <el-descriptions-item label="持仓数量">
              {{ config.strategy.topK }} 只股票
            </el-descriptions-item>
            <el-descriptions-item label="调仓频率">
              {{ getRebalanceFreqText(config.strategy.rebalanceFreq) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="risk-summary">
          <el-alert
            title="风险提示"
            type="warning"
            :closable="false"
          >
            <template #default>
              <ul class="risk-list">
                <li>回测结果仅供参考，不构成投资建议</li>
                <li>历史表现不代表未来收益，投资有风险</li>
                <li>请确保理解所有配置参数的含义</li>
                <li>建议在实盘前进行多轮回测验证</li>
              </ul>
            </template>
          </el-alert>
        </div>

        <div class="estimated-time">
          <el-card class="time-card">
            <template #header>
              <span>预计回测时间</span>
            </template>
            <div class="time-content">
              <div class="time-estimate">
                <el-statistic title="预计耗时" :value="estimatedTime" suffix="分钟" />
              </div>
              <div class="time-factors">
                <p><strong>影响因素:</strong></p>
                <ul>
                  <li>回测时间范围: {{ getDateRangeDays() }} 天</li>
                  <li>股票池大小: {{ getUniverseSize() }} 只股票</li>
                  <li>调仓频率: {{ getRebalanceFreqText(config.strategy.rebalanceFreq) }}</li>
                  <li>模型复杂度: {{ getModelComplexity() }}</li>
                </ul>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 向导控制按钮 -->
      <div class="wizard-controls">
        <el-button
          v-if="currentStep > 0"
          @click="prevStep"
          :disabled="isValidating"
        >
          上一步
        </el-button>
        
        <el-button
          v-if="currentStep < 3"
          type="primary"
          @click="nextStep"
          :disabled="!canProceedToNextStep"
          :loading="isValidating"
        >
          下一步
        </el-button>
        
        <el-button
          v-if="currentStep === 3"
          type="success"
          @click="startBacktest"
          :loading="isStarting"
        >
          <el-icon><VideoPlay /></el-icon>
          开始回测
        </el-button>
        
        <el-button @click="saveAsTemplate" :loading="isSaving">
          <el-icon><DocumentAdd /></el-icon>
          保存为模板
        </el-button>
        
        <el-button @click="loadTemplate">
          <el-icon><Document /></el-icon>
          加载模板
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting, Tools, Warning, VideoPlay, DocumentAdd, Document
} from '@element-plus/icons-vue'

// Props and Emits
interface Props {
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true
})

const emit = defineEmits<{
  'config-completed': [config: any]
  'backtest-started': [config: any]
}>()

// 响应式数据
const currentStep = ref(0)
const isValidating = ref(false)
const isStarting = ref(false)
const isSaving = ref(false)
const basicFormRef = ref()

// 配置数据
const config = reactive({
  basic: {
    name: '',
    type: 'topk',
    universe: 'HS300',
    benchmark: '000300',
    initialCapital: 1000000,
    dateRange: ['2022-01-01', '2023-12-31'],
    dataFreq: 'daily',
    adjustType: 'pre'
  },
  strategy: {
    topK: 30,
    rebalanceFreq: 'monthly',
    turnoverThreshold: 0.3,
    commission: 0.0003,
    stampDuty: 0.001,
    slippage: 0.0001,
    handleLimit: true,
    handleSuspension: true
  },
  risk: {
    maxDrawdown: 0.3,
    maxWeight: 0.1,
    stopLoss: 0.15,
    enableSectorLimit: false,
    volatilityAdjust: true,
    correlationCheck: true
  }
})

// 表单验证规则
const basicRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  dateRange: [
    { required: true, message: '请选择回测时间范围', trigger: 'change' }
  ]
}

// 行业限制数据
const sectorLimits = ref([
  { sector: '金融', limit: 0.15, current: 0.12 },
  { sector: '房地产', limit: 0.10, current: 0.08 },
  { sector: '医药', limit: 0.20, current: 0.15 },
  { sector: '科技', limit: 0.25, current: 0.18 }
])

// 计算属性
const canProceedToNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return config.basic.name && config.basic.dateRange && config.basic.dateRange.length === 2
    case 1:
      return config.strategy.topK > 0 && config.strategy.commission >= 0
    case 2:
      return true // 风险控制步骤总是可以继续
    case 3:
      return true
    default:
      return false
  }
})

const estimatedTime = computed(() => {
  const days = getDateRangeDays()
  const universeSize = getUniverseSize()
  const rebalanceMultiplier = getRebalanceMultiplier()
  
  // 简单的时间估算公式
  const baseTime = Math.ceil((days * universeSize * rebalanceMultiplier) / 10000)
  return Math.max(1, Math.min(baseTime, 60)) // 限制在1-60分钟之间
})

// 方法
const nextStep = async () => {
  if (!canProceedToNextStep.value) {
    ElMessage.warning('请完成当前步骤的配置')
    return
  }
  
  // 验证当前步骤
  if (currentStep.value === 0) {
    try {
      await basicFormRef.value?.validate()
    } catch (error) {
      ElMessage.error('请检查基本配置信息')
      return
    }
  }
  
  isValidating.value = true
  
  try {
    // 模拟验证过程
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (currentStep.value < 3) {
      currentStep.value++
    }
  } finally {
    isValidating.value = false
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const startBacktest = async () => {
  isStarting.value = true
  
  try {
    // 模拟启动过程
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    emit('backtest-started', { ...config })
    ElMessage.success('回测任务已启动')
  } catch (error) {
    ElMessage.error('启动回测失败')
  } finally {
    isStarting.value = false
  }
}

const saveAsTemplate = async () => {
  if (!config.basic.name) {
    ElMessage.warning('请先输入策略名称')
    return
  }
  
  isSaving.value = true
  
  try {
    // 模拟保存过程
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const template = {
      name: `${config.basic.name}_模板`,
      config: { ...config },
      createdAt: Date.now()
    }
    
    // 保存到本地存储
    const templates = JSON.parse(localStorage.getItem('backtest-templates') || '[]')
    templates.push(template)
    localStorage.setItem('backtest-templates', JSON.stringify(templates))
    
    ElMessage.success('模板保存成功')
  } catch (error) {
    ElMessage.error('保存模板失败')
  } finally {
    isSaving.value = false
  }
}

const loadTemplate = () => {
  ElMessage.info('模板加载功能开发中')
}

const disabledDate = (time: Date) => {
  // 禁用未来日期
  return time.getTime() > Date.now()
}

// 辅助方法
const getStrategyTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    'topk': 'TopK选股策略',
    'weight_opt': '权重优化策略',
    'hedge': '对冲策略',
    'custom': '自定义策略'
  }
  return typeMap[type] || type
}

const getRebalanceFreqText = (freq: string) => {
  const freqMap: Record<string, string> = {
    'daily': '每日调仓',
    'weekly': '每周调仓',
    'monthly': '每月调仓',
    'quarterly': '每季度调仓'
  }
  return freqMap[freq] || freq
}

const getDateRangeDays = () => {
  if (!config.basic.dateRange || config.basic.dateRange.length !== 2) return 0
  
  const start = new Date(config.basic.dateRange[0])
  const end = new Date(config.basic.dateRange[1])
  const diffTime = Math.abs(end.getTime() - start.getTime())
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

const getUniverseSize = () => {
  const sizeMap: Record<string, number> = {
    'HS300': 300,
    'ZZ500': 500,
    'ZZ1000': 1000,
    'ALL': 4000
  }
  return sizeMap[config.basic.universe] || 300
}

const getRebalanceMultiplier = () => {
  const multiplierMap: Record<string, number> = {
    'daily': 5,
    'weekly': 3,
    'monthly': 1,
    'quarterly': 0.5
  }
  return multiplierMap[config.strategy.rebalanceFreq] || 1
}

const getModelComplexity = () => {
  // 根据所选模型返回复杂度描述
  return '中等复杂度'
}
</script>

<style scoped>
.backtest-wizard {
  width: 100%;
}

.wizard-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.wizard-header {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wizard-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.step-content {
  padding: 20px 0;
  min-height: 500px;
}

.step-content h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.config-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.config-section h5 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.sector-limits {
  margin-top: 16px;
}

.config-summary {
  margin-bottom: 24px;
}

.risk-summary {
  margin-bottom: 24px;
}

.risk-list {
  margin: 0;
  padding-left: 20px;
}

.risk-list li {
  margin-bottom: 8px;
  color: #606266;
}

.estimated-time {
  margin-bottom: 24px;
}

.time-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.time-content {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.time-estimate {
  min-width: 150px;
  text-align: center;
}

.time-factors {
  flex: 1;
}

.time-factors p {
  margin: 0 0 8px 0;
  color: #303133;
}

.time-factors ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.time-factors li {
  margin-bottom: 4px;
  font-size: 14px;
}

.wizard-controls {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .config-section {
    padding: 16px;
  }
  
  .time-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .wizard-controls {
    flex-direction: column;
  }
  
  .step-content {
    min-height: 400px;
  }
}
</style>