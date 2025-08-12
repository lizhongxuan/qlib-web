<template>
  <div class="hyperparameter-optimizer">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-content">
            <el-icon><MagicStick /></el-icon>
            <span>超参数自动优化</span>
            <el-tag :type="optimizationStatus === 'running' ? 'warning' : 'success'" size="small">
              {{ getStatusText() }}
            </el-tag>
          </div>
          <el-button 
            v-if="optimizationStatus === 'idle'"
            type="primary" 
            @click="startOptimization"
            :loading="optimizationStatus === 'running'"
          >
            开始优化
          </el-button>
          <el-button 
            v-else-if="optimizationStatus === 'running'"
            @click="stopOptimization"
          >
            停止优化
          </el-button>
        </div>
      </template>

      <!-- 优化配置 -->
      <div v-if="optimizationStatus === 'idle'" class="optimization-config">
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="优化算法">
              <el-select v-model="config.algorithm" style="width: 100%">
                <el-option label="贝叶斯优化" value="bayesian" />
                <el-option label="网格搜索" value="grid" />
                <el-option label="随机搜索" value="random" />
                <el-option label="遗传算法" value="genetic" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="优化目标">
              <el-select v-model="config.objective" style="width: 100%">
                <el-option label="最大化准确率" value="maximize_accuracy" />
                <el-option label="最大化AUC" value="maximize_auc" />
                <el-option label="最大化F1" value="maximize_f1" />
                <el-option label="最小化损失" value="minimize_loss" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="最大迭代数">
              <el-input-number 
                v-model="config.maxIterations" 
                :min="10" 
                :max="200" 
                :step="10"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">参数搜索范围</el-divider>
        
        <!-- 模型特定参数配置 -->
        <div class="parameter-ranges">
          <div v-for="param in availableParameters" :key="param.name" class="param-config">
            <div class="param-header">
              <el-checkbox 
                v-model="param.enabled"
                @change="updateParameterSelection"
              >
                <strong>{{ param.label }}</strong>
              </el-checkbox>
              <span class="param-description">{{ param.description }}</span>
            </div>
            
            <div v-if="param.enabled" class="param-range">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="最小值">
                    <el-input-number 
                      v-model="param.min" 
                      :precision="param.precision"
                      :step="param.step"
                      size="small"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="最大值">
                    <el-input-number 
                      v-model="param.max" 
                      :precision="param.precision"
                      :step="param.step"
                      size="small"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="分布类型">
                    <el-select v-model="param.distribution" size="small">
                      <el-option label="均匀分布" value="uniform" />
                      <el-option label="对数均匀" value="log-uniform" />
                      <el-option label="正态分布" value="normal" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </div>
        </div>
      </div>

      <!-- 优化进度 -->
      <div v-if="optimizationStatus === 'running'" class="optimization-progress">
        <div class="progress-header">
          <h3>优化进度</h3>
          <span class="iteration-info">
            第 {{ currentIteration }} / {{ config.maxIterations }} 次迭代
          </span>
        </div>
        
        <el-progress 
          :percentage="progressPercentage" 
          :stroke-width="8"
          class="main-progress"
        />
        
        <div class="current-trial">
          <h4>当前试验配置</h4>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item 
              v-for="(value, key) in currentTrialParams" 
              :key="key"
              :label="key"
            >
              {{ value }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="best-result">
          <h4>当前最佳结果</h4>
          <el-row :gutter="16">
            <el-col :span="6">
              <el-statistic title="最佳分数" :value="bestScore" :precision="4" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="已完成试验" :value="completedTrials" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="预计剩余时间" :value="estimatedTimeRemaining" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="改善次数" :value="improvementCount" />
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 优化结果 -->
      <div v-if="optimizationStatus === 'completed'" class="optimization-results">
        <el-result 
          icon="success" 
          title="优化完成!" 
          :sub-title="`经过 ${completedTrials} 次试验，找到最佳配置`"
        >
          <template #extra>
            <el-button type="primary" @click="applyBestParameters">
              应用最佳参数
            </el-button>
            <el-button @click="viewDetailedResults">
              查看详细结果
            </el-button>
            <el-button @click="resetOptimization">
              重新优化
            </el-button>
          </template>
        </el-result>

        <div class="best-params">
          <h3>最佳参数配置</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="最佳分数">
              <el-tag type="success">{{ bestScore.toFixed(4) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="改善幅度">
              <el-tag type="info">+{{ improvementPercentage }}%</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <div class="params-table">
            <el-table :data="bestParametersTable" size="small">
              <el-table-column prop="parameter" label="参数名" width="200" />
              <el-table-column prop="value" label="最佳值" />
              <el-table-column prop="range" label="搜索范围" />
              <el-table-column prop="improvement" label="重要性">
                <template #default="{ row }">
                  <el-progress 
                    :percentage="row.importance" 
                    :show-text="false"
                    :stroke-width="6"
                    :color="getImportanceColor(row.importance)"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <!-- 优化历史图表 -->
        <div class="optimization-history">
          <h3>优化历史</h3>
          <div ref="historyChart" class="history-chart"></div>
        </div>
      </div>

      <!-- 详细结果对话框 -->
      <el-dialog v-model="showDetailedResults" title="详细优化结果" width="80%">
        <div class="detailed-results">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="试验历史" name="history">
              <el-table :data="trialHistory" height="400">
                <el-table-column prop="trialId" label="试验ID" width="80" />
                <el-table-column prop="score" label="分数" width="100" sortable />
                <el-table-column prop="duration" label="耗时(秒)" width="100" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getStatusTagType(row.status)">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="参数" min-width="300">
                  <template #default="{ row }">
                    <div class="params-preview">
                      <el-tag 
                        v-for="(value, key) in row.params" 
                        :key="key"
                        size="small"
                        class="param-tag"
                      >
                        {{ key }}: {{ value }}
                      </el-tag>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            
            <el-tab-pane label="参数重要性" name="importance">
              <div class="importance-analysis">
                <div ref="importanceChart" class="importance-chart"></div>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="优化收敛" name="convergence">
              <div ref="convergenceChart" class="convergence-chart"></div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'

interface Props {
  modelType: string
}

interface ParameterConfig {
  name: string
  label: string
  description: string
  enabled: boolean
  min: number
  max: number
  precision: number
  step: number
  distribution: 'uniform' | 'log-uniform' | 'normal'
}

const props = defineProps<Props>()
const emit = defineEmits(['optimization-complete'])

// 响应式数据
const optimizationStatus = ref<'idle' | 'running' | 'completed'>('idle')
const currentIteration = ref(0)
const completedTrials = ref(0)
const bestScore = ref(0)
const improvementCount = ref(0)
const currentTrialParams = ref<Record<string, any>>({})
const showDetailedResults = ref(false)
const activeTab = ref('history')

// 图表DOM引用
const historyChart = ref<HTMLElement>()
const importanceChart = ref<HTMLElement>()
const convergenceChart = ref<HTMLElement>()

// 优化配置
const config = reactive({
  algorithm: 'bayesian',
  objective: 'maximize_accuracy',
  maxIterations: 50
})

// 可用参数配置
const availableParameters = ref<ParameterConfig[]>([])

// 试验历史
const trialHistory = ref<any[]>([])

// 计算属性
const progressPercentage = computed(() => {
  return Math.round((currentIteration.value / config.maxIterations) * 100)
})

const estimatedTimeRemaining = computed(() => {
  if (currentIteration.value === 0) return '--'
  const avgTimePerIteration = 30 // 秒
  const remainingIterations = config.maxIterations - currentIteration.value
  const remainingSeconds = remainingIterations * avgTimePerIteration
  
  if (remainingSeconds < 60) return `${remainingSeconds}秒`
  if (remainingSeconds < 3600) return `${Math.round(remainingSeconds / 60)}分钟`
  return `${Math.round(remainingSeconds / 3600)}小时`
})

const improvementPercentage = computed(() => {
  const baselineScore = 0.7 // 假设基准分数
  return Math.round(((bestScore.value - baselineScore) / baselineScore) * 100)
})

const bestParametersTable = computed(() => {
  // 模拟最佳参数表格数据
  return availableParameters.value
    .filter(p => p.enabled)
    .map(param => ({
      parameter: param.label,
      value: generateBestValue(param),
      range: `[${param.min}, ${param.max}]`,
      importance: Math.random() * 100
    }))
})

// 方法
const getStatusText = () => {
  switch (optimizationStatus.value) {
    case 'idle': return '就绪'
    case 'running': return '优化中'
    case 'completed': return '已完成'
    default: return '未知'
  }
}

const initializeParameters = () => {
  const paramConfigs: Record<string, ParameterConfig[]> = {
    'LightGBM': [
      {
        name: 'num_leaves',
        label: '叶子节点数',
        description: '控制模型复杂度，值越大模型越复杂',
        enabled: true,
        min: 10,
        max: 300,
        precision: 0,
        step: 10,
        distribution: 'uniform'
      },
      {
        name: 'learning_rate',
        label: '学习率',
        description: '控制学习步长，影响收敛速度和效果',
        enabled: true,
        min: 0.01,
        max: 0.3,
        precision: 3,
        step: 0.01,
        distribution: 'log-uniform'
      },
      {
        name: 'feature_fraction',
        label: '特征采样率',
        description: '每次迭代随机选择的特征比例',
        enabled: true,
        min: 0.4,
        max: 1.0,
        precision: 2,
        step: 0.1,
        distribution: 'uniform'
      }
    ],
    'XGBoost': [
      {
        name: 'max_depth',
        label: '最大深度',
        description: '树的最大深度，控制过拟合',
        enabled: true,
        min: 3,
        max: 10,
        precision: 0,
        step: 1,
        distribution: 'uniform'
      },
      {
        name: 'learning_rate',
        label: '学习率',
        description: '步长收缩，防止过拟合',
        enabled: true,
        min: 0.01,
        max: 0.3,
        precision: 3,
        step: 0.01,
        distribution: 'log-uniform'
      },
      {
        name: 'subsample',
        label: '样本采样率',
        description: '每次迭代的样本采样比例',
        enabled: true,
        min: 0.6,
        max: 1.0,
        precision: 2,
        step: 0.1,
        distribution: 'uniform'
      }
    ]
  }
  
  availableParameters.value = paramConfigs[props.modelType] || []
}

const updateParameterSelection = () => {
  // 更新参数选择
}

const startOptimization = async () => {
  optimizationStatus.value = 'running'
  currentIteration.value = 0
  completedTrials.value = 0
  bestScore.value = 0
  improvementCount.value = 0
  trialHistory.value = []
  
  // 模拟优化过程
  await simulateOptimization()
}

const simulateOptimization = async () => {
  for (let i = 1; i <= config.maxIterations; i++) {
    if (optimizationStatus.value !== 'running') break
    
    currentIteration.value = i
    
    // 生成随机试验参数
    const trialParams = generateTrialParams()
    currentTrialParams.value = trialParams
    
    // 模拟试验执行
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 生成模拟分数
    const score = Math.random() * 0.3 + 0.7 // 0.7-1.0之间
    
    // 更新最佳分数
    if (score > bestScore.value) {
      bestScore.value = score
      improvementCount.value++
    }
    
    // 记录试验历史
    trialHistory.value.push({
      trialId: i,
      score,
      duration: Math.random() * 60 + 10,
      status: 'completed',
      params: { ...trialParams }
    })
    
    completedTrials.value = i
  }
  
  if (optimizationStatus.value === 'running') {
    optimizationStatus.value = 'completed'
    ElMessage.success('超参数优化完成！')
  }
}

const generateTrialParams = () => {
  const params: Record<string, any> = {}
  
  availableParameters.value
    .filter(p => p.enabled)
    .forEach(param => {
      if (param.distribution === 'uniform') {
        params[param.name] = +(Math.random() * (param.max - param.min) + param.min).toFixed(param.precision)
      } else if (param.distribution === 'log-uniform') {
        const logMin = Math.log(param.min)
        const logMax = Math.log(param.max)
        params[param.name] = +(Math.exp(Math.random() * (logMax - logMin) + logMin)).toFixed(param.precision)
      }
    })
  
  return params
}

const generateBestValue = (param: ParameterConfig) => {
  // 生成模拟的最佳值
  const mid = (param.min + param.max) / 2
  const offset = (Math.random() - 0.5) * (param.max - param.min) * 0.3
  return (mid + offset).toFixed(param.precision)
}

const stopOptimization = () => {
  optimizationStatus.value = 'idle'
  ElMessage.warning('优化已停止')
}

const applyBestParameters = () => {
  const bestParams = availableParameters.value
    .filter(p => p.enabled)
    .reduce((acc, param) => {
      acc[param.name] = generateBestValue(param)
      return acc
    }, {} as Record<string, any>)
  
  emit('optimization-complete', bestParams)
  ElMessage.success('最佳参数已应用')
}

const viewDetailedResults = () => {
  showDetailedResults.value = true
  nextTick(() => {
    initializeCharts()
  })
}

const resetOptimization = () => {
  optimizationStatus.value = 'idle'
  currentIteration.value = 0
  completedTrials.value = 0
  bestScore.value = 0
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'warning'
    default: return 'info'
  }
}

const getImportanceColor = (importance: number) => {
  if (importance > 80) return '#f56c6c'
  if (importance > 60) return '#e6a23c'
  if (importance > 40) return '#409eff'
  return '#67c23a'
}

const initializeCharts = () => {
  // 这里可以集成实际的图表库如 ECharts
  // 暂时使用占位符
}

// 生命周期
onMounted(() => {
  initializeParameters()
})
</script>

<style scoped>
.hyperparameter-optimizer {
  margin-top: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.optimization-config {
  margin-bottom: 24px;
}

.parameter-ranges {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.param-config {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
}

.param-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.param-description {
  color: #909399;
  font-size: 13px;
}

.param-range {
  margin-left: 24px;
}

.optimization-progress {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-header h3 {
  margin: 0;
  color: #303133;
}

.iteration-info {
  font-size: 14px;
  color: #606266;
}

.main-progress {
  margin: 16px 0;
}

.current-trial, .best-result {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.current-trial h4, .best-result h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.optimization-results .best-params {
  margin-top: 24px;
}

.best-params h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.params-table {
  margin-top: 16px;
}

.optimization-history {
  margin-top: 32px;
}

.optimization-history h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.history-chart,
.importance-chart,
.convergence-chart {
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.detailed-results {
  min-height: 500px;
}

.params-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.param-tag {
  margin-bottom: 4px;
}

.importance-analysis {
  padding: 20px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .progress-header {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .param-config {
    padding: 12px;
  }
  
  .param-range {
    margin-left: 0;
    margin-top: 12px;
  }
}
</style>