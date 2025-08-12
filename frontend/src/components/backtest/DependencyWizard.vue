<template>
  <div class="dependency-wizard">
    <el-card class="wizard-card">
      <template #header>
        <div class="wizard-header">
          <h3>依赖检查向导</h3>
          <el-steps :active="currentStep" finish-status="success" simple>
            <el-step title="因子检查" icon="MagicStick" />
            <el-step title="模型验证" icon="Cpu" />
            <el-step title="数据确认" icon="Database" />
            <el-step title="依赖解决" icon="Check" />
          </el-steps>
        </div>
      </template>

      <!-- 步骤1: 因子依赖检查 -->
      <div v-if="currentStep === 0" class="step-content">
        <h4>检查因子依赖</h4>
        <div class="dependency-section">
          <div class="section-header">
            <span>所需因子列表</span>
            <el-button size="small" @click="refreshFactorCheck">
              <el-icon><Refresh /></el-icon>
              重新检查
            </el-button>
          </div>
          
          <div class="dependency-list">
            <div
              v-for="factor in requiredFactors"
              :key="factor.id"
              class="dependency-item"
              :class="getDependencyItemClass(factor.status)"
            >
              <div class="dependency-info">
                <div class="dependency-name">
                  <el-icon>
                    <Check v-if="factor.status === 'available'" />
                    <Warning v-else-if="factor.status === 'warning'" />
                    <Close v-else />
                  </el-icon>
                  {{ factor.name }}
                </div>
                <div class="dependency-description">{{ factor.description }}</div>
                <div v-if="factor.lastUpdated" class="dependency-meta">
                  最后更新: {{ formatTime(factor.lastUpdated) }}
                </div>
              </div>
              
              <div class="dependency-actions">
                <el-tag :type="getStatusTagType(factor.status)" size="small">
                  {{ getStatusText(factor.status) }}
                </el-tag>
                
                <el-button
                  v-if="factor.status === 'missing'"
                  size="small"
                  type="primary"
                  @click="createFactor(factor)"
                >
                  创建因子
                </el-button>
                
                <el-button
                  v-if="factor.status === 'outdated'"
                  size="small"
                  type="warning"
                  @click="updateFactor(factor)"
                >
                  更新因子
                </el-button>
              </div>
            </div>
          </div>
          
          <div class="summary-info">
            <el-alert
              :title="getFactorSummaryTitle()"
              :type="getFactorSummaryType()"
              :description="getFactorSummaryDescription()"
              show-icon
              :closable="false"
            />
          </div>
        </div>
      </div>

      <!-- 步骤2: 模型依赖检查 -->
      <div v-if="currentStep === 1" class="step-content">
        <h4>检查模型依赖</h4>
        <div class="dependency-section">
          <div class="section-header">
            <span>可用模型列表</span>
            <el-select 
              v-model="selectedModelType" 
              placeholder="筛选模型类型"
              size="small"
              style="width: 150px"
              @change="filterModels"
            >
              <el-option label="全部" value="" />
              <el-option label="LightGBM" value="lgb" />
              <el-option label="XGBoost" value="xgb" />
              <el-option label="LSTM" value="lstm" />
            </el-select>
          </div>

          <div class="models-grid">
            <div
              v-for="model in filteredModels"
              :key="model.id"
              class="model-card"
              :class="{ 'selected': selectedModel?.id === model.id }"
              @click="selectModel(model)"
            >
              <div class="model-header">
                <div class="model-name">{{ model.name }}</div>
                <el-tag :type="getModelTagType(model.type)" size="small">
                  {{ model.type }}
                </el-tag>
              </div>
              
              <div class="model-metrics">
                <div class="metric">
                  <span class="metric-label">准确率</span>
                  <span class="metric-value">{{ model.accuracy.toFixed(1) }}%</span>
                </div>
                <div class="metric">
                  <span class="metric-label">IC</span>
                  <span class="metric-value">{{ model.ic.toFixed(3) }}</span>
                </div>
                <div class="metric">
                  <span class="metric-label">训练时间</span>
                  <span class="metric-value">{{ model.trainingTime }}</span>
                </div>
              </div>
              
              <div class="model-status">
                <el-tag 
                  :type="model.status === 'ready' ? 'success' : 'warning'"
                  size="small"
                >
                  {{ model.status === 'ready' ? '可用' : '训练中' }}
                </el-tag>
                
                <span class="model-date">
                  {{ formatDate(model.updatedAt) }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="selectedModel" class="model-details">
            <el-alert
              title="模型详情"
              type="info"
              :closable="false"
            >
              <template #default>
                <div class="model-detail-content">
                  <p><strong>选择模型:</strong> {{ selectedModel.name }}</p>
                  <p><strong>模型类型:</strong> {{ selectedModel.type }}</p>
                  <p><strong>因子数量:</strong> {{ selectedModel.factorCount }} 个</p>
                  <p><strong>训练数据:</strong> {{ selectedModel.trainPeriod }}</p>
                  <p><strong>验证准确率:</strong> {{ selectedModel.accuracy.toFixed(2) }}%</p>
                </div>
              </template>
            </el-alert>
          </div>
        </div>
      </div>

      <!-- 步骤3: 数据依赖检查 -->
      <div v-if="currentStep === 2" class="step-content">
        <h4>数据可用性检查</h4>
        <div class="dependency-section">
          <div class="data-sources">
            <div
              v-for="source in dataSources"
              :key="source.id"
              class="data-source-item"
            >
              <div class="source-header">
                <div class="source-info">
                  <h5>{{ source.name }}</h5>
                  <p>{{ source.description }}</p>
                </div>
                <el-tag 
                  :type="source.status === 'available' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ source.status === 'available' ? '可用' : '不可用' }}
                </el-tag>
              </div>
              
              <div class="source-details">
                <el-row :gutter="16">
                  <el-col :span="8">
                    <div class="detail-item">
                      <span class="detail-label">数据范围:</span>
                      <span class="detail-value">{{ source.dateRange }}</span>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="detail-item">
                      <span class="detail-label">更新频率:</span>
                      <span class="detail-value">{{ source.updateFreq }}</span>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="detail-item">
                      <span class="detail-label">最后更新:</span>
                      <span class="detail-value">{{ formatTime(source.lastUpdate) }}</span>
                    </div>
                  </el-col>
                </el-row>
              </div>
              
              <div v-if="source.status !== 'available'" class="source-actions">
                <el-button size="small" type="primary" @click="fixDataSource(source)">
                  修复数据源
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤4: 依赖解决方案 -->
      <div v-if="currentStep === 3" class="step-content">
        <h4>依赖问题解决</h4>
        <div class="resolution-section">
          <div v-if="hasUnresolvedDependencies" class="unresolved-issues">
            <el-alert
              title="发现依赖问题"
              type="warning"
              :closable="false"
            >
              <template #default>
                <div class="issues-list">
                  <div v-for="issue in unresolvedIssues" :key="issue.id" class="issue-item">
                    <div class="issue-description">{{ issue.description }}</div>
                    <div class="issue-solution">
                      <strong>建议解决方案:</strong> {{ issue.solution }}
                    </div>
                    <div class="issue-actions">
                      <el-button
                        size="small"
                        type="primary"
                        @click="resolveIssue(issue)"
                        :loading="issue.resolving"
                      >
                        {{ issue.autoResolvable ? '自动解决' : '手动处理' }}
                      </el-button>
                    </div>
                  </div>
                </div>
              </template>
            </el-alert>
          </div>

          <div v-else class="all-resolved">
            <el-result
              icon="success"
              title="依赖检查通过"
              sub-title="所有必要的因子、模型和数据都已就绪，可以开始回测配置"
            >
              <template #extra>
                <el-button type="primary" @click="proceedToBacktest">
                  进入回测配置
                </el-button>
              </template>
            </el-result>
          </div>
        </div>
      </div>

      <!-- 向导控制按钮 -->
      <div class="wizard-controls">
        <el-button
          v-if="currentStep > 0"
          @click="prevStep"
          :disabled="isProcessing"
        >
          上一步
        </el-button>
        
        <el-button
          v-if="currentStep < 3"
          type="primary"
          @click="nextStep"
          :disabled="!canProceedToNextStep || isProcessing"
          :loading="isProcessing"
        >
          下一步
        </el-button>
        
        <el-button
          v-if="currentStep === 3 && !hasUnresolvedDependencies"
          type="success"
          @click="completeDependencyCheck"
        >
          完成检查
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Check, Warning, Close, Refresh, MagicStick, Cpu, Database
} from '@element-plus/icons-vue'

// Props and Emits
interface Props {
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true
})

const emit = defineEmits<{
  'dependency-resolved': []
  'proceed-to-backtest': []
}>()

// 响应式数据
const currentStep = ref(0)
const isProcessing = ref(false)
const selectedModel = ref(null)
const selectedModelType = ref('')

// 因子依赖数据
const requiredFactors = ref([
  {
    id: 'momentum_20',
    name: '20日动量因子',
    description: '基于20日价格动量的因子',
    status: 'available',
    lastUpdated: Date.now() - 3600000
  },
  {
    id: 'pe_ratio',
    name: '市盈率倒数',
    description: '股票估值因子',
    status: 'available',
    lastUpdated: Date.now() - 7200000
  },
  {
    id: 'rsi_14',
    name: 'RSI相对强弱指标',
    description: '技术分析因子',
    status: 'missing',
    lastUpdated: null
  }
])

// 模型数据
const availableModels = ref([
  {
    id: 'lgb_v3',
    name: 'LightGBM_v3.2',
    type: 'LightGBM',
    accuracy: 94.2,
    ic: 0.075,
    trainingTime: '45分钟',
    status: 'ready',
    factorCount: 20,
    trainPeriod: '2020-01-01 至 2023-12-31',
    updatedAt: Date.now() - 86400000
  },
  {
    id: 'xgb_v2',
    name: 'XGBoost_v2.1',
    type: 'XGBoost',
    accuracy: 91.8,
    ic: 0.068,
    trainingTime: '32分钟',
    status: 'ready',
    factorCount: 18,
    trainPeriod: '2020-01-01 至 2023-12-31',
    updatedAt: Date.now() - 172800000
  }
])

// 数据源
const dataSources = ref([
  {
    id: 'stock_data',
    name: '股票行情数据',
    description: '日级别股票价格、成交量等基础数据',
    status: 'available',
    dateRange: '2015-01-01 至 今',
    updateFreq: '每日更新',
    lastUpdate: Date.now() - 3600000
  },
  {
    id: 'financial_data',
    name: '财务数据',
    description: '上市公司财报数据',
    status: 'available',
    dateRange: '2015-01-01 至 2023-12-31',
    updateFreq: '季度更新',
    lastUpdate: Date.now() - 86400000 * 7
  }
])

// 计算属性
const filteredModels = computed(() => {
  if (!selectedModelType.value) return availableModels.value
  return availableModels.value.filter(model => 
    model.type.toLowerCase().includes(selectedModelType.value)
  )
})

const canProceedToNextStep = computed(() => {
  switch (currentStep.value) {
    case 0:
      return requiredFactors.value.every(factor => factor.status === 'available')
    case 1:
      return selectedModel.value !== null
    case 2:
      return dataSources.value.every(source => source.status === 'available')
    case 3:
      return !hasUnresolvedDependencies.value
    default:
      return false
  }
})

const hasUnresolvedDependencies = computed(() => {
  return unresolvedIssues.value.length > 0
})

const unresolvedIssues = computed(() => {
  const issues = []
  
  // 检查缺失的因子
  const missingFactors = requiredFactors.value.filter(f => f.status === 'missing')
  if (missingFactors.length > 0) {
    issues.push({
      id: 'missing_factors',
      description: `缺少 ${missingFactors.length} 个必需因子`,
      solution: '可以自动创建基础版本的因子',
      autoResolvable: true,
      resolving: false
    })
  }
  
  return issues
})

// 方法
const nextStep = () => {
  if (canProceedToNextStep.value && currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const refreshFactorCheck = async () => {
  isProcessing.value = true
  
  // 模拟检查过程
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 更新因子状态
  requiredFactors.value.forEach(factor => {
    if (factor.status === 'missing') {
      // 模拟检查结果
      if (Math.random() > 0.5) {
        factor.status = 'available'
        factor.lastUpdated = Date.now()
      }
    }
  })
  
  isProcessing.value = false
  ElMessage.success('因子依赖检查完成')
}

const createFactor = async (factor: any) => {
  ElMessage.info(`开始创建因子: ${factor.name}`)
  
  // 模拟创建过程
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  factor.status = 'available'
  factor.lastUpdated = Date.now()
  
  ElMessage.success(`因子 ${factor.name} 创建成功`)
}

const updateFactor = async (factor: any) => {
  ElMessage.info(`开始更新因子: ${factor.name}`)
  
  // 模拟更新过程
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  factor.status = 'available'
  factor.lastUpdated = Date.now()
  
  ElMessage.success(`因子 ${factor.name} 更新成功`)
}

const selectModel = (model: any) => {
  selectedModel.value = model
  ElMessage.info(`已选择模型: ${model.name}`)
}

const filterModels = () => {
  // 筛选逻辑在计算属性中处理
}

const fixDataSource = async (source: any) => {
  ElMessage.info(`正在修复数据源: ${source.name}`)
  
  // 模拟修复过程
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  source.status = 'available'
  source.lastUpdate = Date.now()
  
  ElMessage.success(`数据源 ${source.name} 修复成功`)
}

const resolveIssue = async (issue: any) => {
  issue.resolving = true
  
  try {
    // 模拟解决过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    if (issue.id === 'missing_factors') {
      // 自动创建缺失的因子
      const missingFactors = requiredFactors.value.filter(f => f.status === 'missing')
      for (const factor of missingFactors) {
        factor.status = 'available'
        factor.lastUpdated = Date.now()
      }
    }
    
    ElMessage.success('依赖问题已解决')
  } catch (error) {
    ElMessage.error('解决依赖问题失败')
  } finally {
    issue.resolving = false
  }
}

const proceedToBacktest = () => {
  emit('proceed-to-backtest')
}

const completeDependencyCheck = () => {
  emit('dependency-resolved')
  ElMessage.success('依赖检查完成，可以开始配置回测')
}

// 辅助方法
const getDependencyItemClass = (status: string) => {
  return {
    'available': status === 'available',
    'warning': status === 'warning' || status === 'outdated',
    'error': status === 'missing'
  }
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'available': return 'success'
    case 'warning': case 'outdated': return 'warning'
    case 'missing': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'available': return '可用'
    case 'warning': return '警告'
    case 'outdated': return '需更新'
    case 'missing': return '缺失'
    default: return '未知'
  }
}

const getModelTagType = (type: string) => {
  switch (type) {
    case 'LightGBM': return 'success'
    case 'XGBoost': return 'warning'
    case 'LSTM': return 'info'
    default: return 'info'
  }
}

const getFactorSummaryTitle = () => {
  const availableCount = requiredFactors.value.filter(f => f.status === 'available').length
  const totalCount = requiredFactors.value.length
  
  if (availableCount === totalCount) {
    return '所有因子依赖已满足'
  } else {
    return `因子依赖检查: ${availableCount}/${totalCount} 可用`
  }
}

const getFactorSummaryType = () => {
  const availableCount = requiredFactors.value.filter(f => f.status === 'available').length
  const totalCount = requiredFactors.value.length
  
  if (availableCount === totalCount) return 'success'
  if (availableCount > totalCount / 2) return 'warning'
  return 'error'
}

const getFactorSummaryDescription = () => {
  const missingCount = requiredFactors.value.filter(f => f.status === 'missing').length
  const outdatedCount = requiredFactors.value.filter(f => f.status === 'outdated').length
  
  if (missingCount === 0 && outdatedCount === 0) {
    return '所有必需的因子都已准备就绪，可以进入下一步'
  }
  
  const issues = []
  if (missingCount > 0) issues.push(`${missingCount}个因子缺失`)
  if (outdatedCount > 0) issues.push(`${outdatedCount}个因子需要更新`)
  
  return `发现问题: ${issues.join('，')}。请先解决这些问题再继续。`
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  // 初始化时自动检查依赖
  refreshFactorCheck()
})
</script>

<style scoped>
.dependency-wizard {
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
  min-height: 400px;
}

.step-content h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.dependency-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.dependency-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dependency-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.dependency-item.available {
  background: #f0f9ff;
  border-color: #67c23a;
}

.dependency-item.warning {
  background: #fdf6ec;
  border-color: #e6a23c;
}

.dependency-item.error {
  background: #fef0f0;
  border-color: #f56c6c;
}

.dependency-info {
  flex: 1;
}

.dependency-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.dependency-description {
  color: #606266;
  font-size: 14px;
  margin-bottom: 4px;
}

.dependency-meta {
  color: #909399;
  font-size: 12px;
}

.dependency-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.model-card {
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
}

.model-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.model-card.selected {
  border-color: #409eff;
  background: #f0f8ff;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.model-name {
  font-weight: 600;
  color: #303133;
}

.model-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.metric {
  display: flex;
  flex-direction: column;
  text-align: center;
}

.metric-label {
  color: #909399;
  font-size: 12px;
  margin-bottom: 4px;
}

.metric-value {
  color: #303133;
  font-weight: 600;
}

.model-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-date {
  color: #909399;
  font-size: 12px;
}

.model-details {
  margin-top: 20px;
}

.model-detail-content p {
  margin: 8px 0;
}

.data-sources {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.data-source-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.source-info h5 {
  margin: 0 0 4px 0;
  color: #303133;
}

.source-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.source-details {
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
}

.detail-label {
  color: #909399;
  font-size: 14px;
}

.detail-value {
  color: #303133;
  font-weight: 500;
}

.resolution-section {
  padding: 20px 0;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #e6a23c;
}

.issue-description {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.issue-solution {
  color: #606266;
  margin-bottom: 12px;
}

.issue-actions {
  display: flex;
  gap: 8px;
}

.summary-info {
  margin-top: 20px;
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
  .models-grid {
    grid-template-columns: 1fr;
  }
  
  .dependency-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .dependency-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .wizard-controls {
    flex-direction: column;
  }
}
</style>