<template>
  <div class="deployment-wizard">
    <el-steps :active="currentStep" align-center class="wizard-steps">
      <el-step title="选择策略" icon="DocumentChecked" />
      <el-step title="配置部署" icon="Setting" />
      <el-step title="风险确认" icon="Warning" />
      <el-step title="启动部署" icon="VideoPlay" />
    </el-steps>

    <!-- 步骤 1: 选择策略 -->
    <div v-if="currentStep === 0" class="step-content">
      <h3>选择要部署的策略</h3>
      <div class="strategy-selection">
        <el-row :gutter="24">
          <el-col :span="8" v-for="strategy in strategies" :key="strategy.id">
            <div 
              :class="['strategy-card', { selected: modelValue.strategyId === strategy.id }]"
              @click="selectStrategy(strategy.id)"
            >
              <div class="strategy-header">
                <div class="strategy-name">{{ strategy.name }}</div>
                <el-tag :type="getStrategyTagType(strategy.type)" size="small">
                  {{ strategy.type }}
                </el-tag>
              </div>
              
              <div class="strategy-metrics">
                <div class="metric">
                  <span class="metric-label">回测收益率</span>
                  <span class="metric-value positive">{{ strategy.backtestReturn.toFixed(2) }}%</span>
                </div>
                <div class="metric">
                  <span class="metric-label">夏普比率</span>
                  <span class="metric-value">{{ strategy.sharpeRatio.toFixed(2) }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">最大回撤</span>
                  <span class="metric-value negative">{{ (strategy.maxDrawdown * 100).toFixed(2) }}%</span>
                </div>
              </div>
              
              <div class="strategy-status">
                <el-tag v-if="strategy.status === 'ready'" type="success" size="small">
                  可部署
                </el-tag>
                <el-tag v-else-if="strategy.status === 'deployed'" type="warning" size="small">
                  已部署
                </el-tag>
                <el-tag v-else type="info" size="small">
                  开发中
                </el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 步骤 2: 配置部署 -->
    <div v-if="currentStep === 1" class="step-content">
      <h3>部署配置</h3>
      <el-form :model="modelValue" label-width="120px" ref="configFormRef" :rules="configRules">
        <!-- 基本配置 -->
        <div class="config-section">
          <h4>基本配置</h4>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="部署名称" prop="name" required>
                <el-input v-model="modelValue.name" placeholder="输入部署名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="部署环境" prop="environment">
                <el-select v-model="modelValue.environment" style="width: 100%">
                  <el-option label="模拟交易" value="simulation" />
                  <el-option label="实盘交易" value="live" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="启动资金" prop="initialCapital">
                <el-input-number 
                  v-model="modelValue.initialCapital" 
                  :min="10000" 
                  :max="100000000"
                  :step="10000"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 交易配置 -->
        <div class="config-section">
          <h4>交易配置</h4>
          <el-row :gutter="24">
            <el-col :span="6">
              <el-form-item label="券商接口" prop="broker">
                <el-select v-model="modelValue.broker" style="width: 100%">
                  <el-option label="模拟券商" value="mock" />
                  <el-option label="华泰证券" value="huatai" />
                  <el-option label="中信证券" value="zhongxin" />
                  <el-option label="招商证券" value="zhaoshang" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="调仓频率" prop="rebalanceFreq">
                <el-select v-model="modelValue.rebalanceFreq" style="width: 100%">
                  <el-option label="日调仓" value="daily" />
                  <el-option label="周调仓" value="weekly" />
                  <el-option label="月调仓" value="monthly" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="持仓数量" prop="positionCount">
                <el-input-number 
                  v-model="modelValue.positionCount" 
                  :min="5" 
                  :max="50"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="单股权重上限" prop="maxSingleWeight">
                <el-input-number 
                  v-model="modelValue.maxSingleWeight" 
                  :min="0.01" 
                  :max="0.2"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 风险控制 -->
        <div class="config-section">
          <h4>风险控制</h4>
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="止损阈值" prop="stopLossThreshold">
                <el-input-number 
                  v-model="modelValue.stopLossThreshold" 
                  :min="0.05" 
                  :max="0.3"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="最大回撤限制" prop="maxDrawdownLimit">
                <el-input-number 
                  v-model="modelValue.maxDrawdownLimit" 
                  :min="0.1" 
                  :max="0.5"
                  :step="0.01"
                  :precision="2"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="日交易限额" prop="dailyTradingLimit">
                <el-input-number 
                  v-model="modelValue.dailyTradingLimit" 
                  :min="1000" 
                  :max="1000000"
                  :step="1000"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="监控设置">
                <el-checkbox-group v-model="modelValue.monitoring">
                  <el-checkbox label="realtime">实时监控</el-checkbox>
                  <el-checkbox label="alerts">异常告警</el-checkbox>
                  <el-checkbox label="daily_report">日报推送</el-checkbox>
                  <el-checkbox label="weekly_report">周报推送</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通知方式">
                <el-checkbox-group v-model="modelValue.notifications">
                  <el-checkbox label="email">邮件</el-checkbox>
                  <el-checkbox label="sms">短信</el-checkbox>
                  <el-checkbox label="wechat">微信</el-checkbox>
                  <el-checkbox label="app">APP推送</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-form>
    </div>

    <!-- 步骤 3: 风险确认 -->
    <div v-if="currentStep === 2" class="step-content">
      <h3>风险确认与免责声明</h3>
      <div class="risk-warnings">
        <el-alert
          title="重要风险提示"
          type="warning"
          :closable="false"
        >
          <template #default>
            <div class="risk-content">
              <h4>请仔细阅读以下风险提示：</h4>
              <ul class="risk-list">
                <li>量化交易存在本金损失风险，过往业绩不代表未来收益</li>
                <li>市场环境变化可能导致策略失效或表现不佳</li>
                <li>技术故障、网络中断等可能影响交易执行</li>
                <li>流动性风险可能导致无法及时止损</li>
                <li>监管政策变化可能影响策略合规性</li>
              </ul>
            </div>
          </template>
        </el-alert>

        <div class="strategy-risks">
          <h4>策略风险评估</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="风险等级">
              <el-tag type="danger">高风险</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="预期最大回撤">
              {{ (selectedStrategy?.maxDrawdown * 100).toFixed(2) }}%
            </el-descriptions-item>
            <el-descriptions-item label="历史最大亏损">
              {{ (modelValue.initialCapital * (selectedStrategy?.maxDrawdown || 0.15)).toFixed(0) }} 元
            </el-descriptions-item>
            <el-descriptions-item label="适合投资者">
              专业投资者
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="confirmations">
          <el-checkbox v-model="riskConfirmations.understand">
            我已充分了解量化交易的风险特性
          </el-checkbox>
          <el-checkbox v-model="riskConfirmations.accept">
            我愿意承担投资损失风险
          </el-checkbox>
          <el-checkbox v-model="riskConfirmations.professional">
            我具备相应的投资经验和风险识别能力
          </el-checkbox>
          <el-checkbox v-model="riskConfirmations.disclaimer">
            我已阅读并同意《策略部署免责声明》
          </el-checkbox>
        </div>
      </div>
    </div>

    <!-- 步骤 4: 启动部署 -->
    <div v-if="currentStep === 3" class="step-content">
      <h3>部署确认</h3>
      <div class="deployment-summary">
        <el-descriptions title="部署配置摘要" :column="2" border>
          <el-descriptions-item label="策略名称">
            {{ selectedStrategy?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="部署名称">
            {{ modelValue.name }}
          </el-descriptions-item>
          <el-descriptions-item label="部署环境">
            <el-tag :type="modelValue.environment === 'live' ? 'danger' : 'success'">
              {{ modelValue.environment === 'live' ? '实盘交易' : '模拟交易' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="启动资金">
            ¥{{ modelValue.initialCapital.toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="调仓频率">
            {{ getFrequencyText(modelValue.rebalanceFreq) }}
          </el-descriptions-item>
          <el-descriptions-item label="持仓数量">
            {{ modelValue.positionCount }} 只股票
          </el-descriptions-item>
        </el-descriptions>

        <div class="final-confirmation">
          <el-alert
            title="最终确认"
            type="info"
            :closable="false"
          >
            请再次确认所有配置信息，点击"启动部署"后策略将开始运行
          </el-alert>
        </div>
      </div>
    </div>

    <!-- 向导操作按钮 -->
    <div class="wizard-actions">
      <el-button v-if="currentStep > 0" @click="prevStep">
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      
      <el-button 
        v-if="currentStep < 3" 
        type="primary" 
        @click="nextStep"
        :disabled="!canProceed"
      >
        下一步
        <el-icon><ArrowRight /></el-icon>
      </el-button>
      
      <el-button 
        v-if="currentStep === 3" 
        type="danger" 
        @click="startDeployment"
        :loading="deploying"
        :disabled="!allRiskConfirmed"
      >
        <el-icon><VideoPlay /></el-icon>
        启动部署
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DocumentChecked, Setting, Warning, VideoPlay,
  ArrowLeft, ArrowRight
} from '@element-plus/icons-vue'

interface Strategy {
  id: string
  name: string
  type: string
  backtestReturn: number
  sharpeRatio: number
  maxDrawdown: number
  status: string
}

interface DeploymentConfig {
  strategyId: string
  name: string
  environment: string
  initialCapital: number
  broker: string
  rebalanceFreq: string
  positionCount: number
  maxSingleWeight: number
  stopLossThreshold: number
  maxDrawdownLimit: number
  dailyTradingLimit: number
  monitoring: string[]
  notifications: string[]
}

interface Props {
  modelValue: DeploymentConfig
  strategies: Strategy[]
  deploying?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: DeploymentConfig): void
  (e: 'deploy', config: DeploymentConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const currentStep = ref(0)
const configFormRef = ref()

// 风险确认状态
const riskConfirmations = reactive({
  understand: false,
  accept: false,
  professional: false,
  disclaimer: false
})

// 表单验证规则
const configRules = {
  name: [
    { required: true, message: '请输入部署名称', trigger: 'blur' }
  ],
  strategyId: [
    { required: true, message: '请选择策略', trigger: 'change' }
  ]
}

// 计算属性
const selectedStrategy = computed(() => {
  return props.strategies.find(s => s.id === props.modelValue.strategyId)
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return props.modelValue.strategyId !== ''
    case 1:
      return props.modelValue.name !== ''
    case 2:
      return allRiskConfirmed.value
    default:
      return true
  }
})

const allRiskConfirmed = computed(() => {
  return Object.values(riskConfirmations).every(confirmed => confirmed)
})

// 方法
const getStrategyTagType = (type: string) => {
  switch (type) {
    case '机器学习': return 'success'
    case '深度学习': return 'primary'
    case '技术指标': return 'warning'
    default: return 'info'
  }
}

const selectStrategy = (strategyId: string) => {
  const updatedConfig = { ...props.modelValue, strategyId }
  const strategy = props.strategies.find(s => s.id === strategyId)
  if (strategy && !updatedConfig.name) {
    updatedConfig.name = `${strategy.name}_部署_${new Date().toLocaleDateString()}`
  }
  emit('update:modelValue', updatedConfig)
}

const getFrequencyText = (freq: string) => {
  switch (freq) {
    case 'daily': return '日调仓'
    case 'weekly': return '周调仓'
    case 'monthly': return '月调仓'
    default: return freq
  }
}

const prevStep = () => {
  currentStep.value = Math.max(0, currentStep.value - 1)
}

const nextStep = async () => {
  if (!canProceed.value) {
    ElMessage.warning('请完成当前步骤的配置')
    return
  }

  // 在步骤1时验证表单
  if (currentStep.value === 1 && configFormRef.value) {
    try {
      await configFormRef.value.validate()
    } catch {
      ElMessage.warning('请检查配置信息')
      return
    }
  }

  currentStep.value = Math.min(3, currentStep.value + 1)
}

const startDeployment = async () => {
  if (!allRiskConfirmed.value) {
    ElMessage.warning('请完成所有风险确认')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要启动策略部署吗？启动后策略将开始自动交易。',
      '确认部署',
      { type: 'warning' }
    )

    emit('deploy', props.modelValue)
  } catch {
    // 用户取消
  }
}

// 暴露方法给父组件
defineExpose({
  resetWizard: () => {
    currentStep.value = 0
    Object.assign(riskConfirmations, {
      understand: false,
      accept: false,
      professional: false,
      disclaimer: false
    })
  }
})
</script>

<style scoped>
.deployment-wizard {
  width: 100%;
}

.wizard-steps {
  margin: 0 0 32px 0;
}

.step-content {
  padding: 32px 0;
  min-height: 400px;
}

.step-content h3 {
  margin: 0 0 24px 0;
  color: #303133;
  font-size: 20px;
}

.strategy-selection {
  margin-top: 24px;
}

.strategy-card {
  padding: 20px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.strategy-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.strategy-card.selected {
  border-color: #409eff;
  background: #f0f8ff;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.3;
}

.strategy-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.metric-value {
  font-weight: 600;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.config-section {
  margin-bottom: 32px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

.config-section h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.risk-warnings {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.risk-content h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.risk-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.6;
}

.risk-list li {
  margin-bottom: 8px;
}

.strategy-risks h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.confirmations {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: #f0f8ff;
  border-radius: 8px;
}

.deployment-summary {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.final-confirmation {
  margin-top: 24px;
}

.wizard-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 32px;
  border-top: 1px solid #e4e7ed;
  margin-top: 32px;
}

@media (max-width: 768px) {
  .step-content {
    padding: 16px 0;
  }
  
  .config-section {
    padding: 16px;
  }
  
  .wizard-actions {
    flex-direction: column;
  }
}
</style>