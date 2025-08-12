<template>
  <div class="training-monitor">
    <el-card>
      <template #header>
        <div class="monitor-header">
          <div class="header-info">
            <el-icon><Monitor /></el-icon>
            <span>训练监控 - {{ trainingTask?.name }}</span>
            <el-tag 
              :type="getStatusTagType(trainingTask?.status || 'pending')"
              size="small"
            >
              {{ getStatusText(trainingTask?.status || 'pending') }}
            </el-tag>
          </div>
          
          <div class="header-actions">
            <el-button 
              v-if="trainingTask?.status === 'running'"
              size="small" 
              @click="pauseTraining"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button 
              v-if="trainingTask?.status === 'paused'"
              size="small" 
              type="primary"
              @click="resumeTraining"
            >
              <el-icon><VideoPlay /></el-icon>
              继续
            </el-button>
            <el-button 
              v-if="['running', 'paused'].includes(trainingTask?.status || '')"
              size="small" 
              type="danger"
              @click="stopTraining"
            >
              <el-icon><Close /></el-icon>
              停止
            </el-button>
          </div>
        </div>
      </template>

      <!-- 总体进度 -->
      <div class="overall-progress">
        <div class="progress-section">
          <h3>总体进度</h3>
          <el-progress 
            :percentage="overallProgress" 
            :status="getProgressStatus()"
            :stroke-width="12"
            text-inside
          />
          <div class="progress-info">
            <span>轮次: {{ currentEpoch }} / {{ totalEpochs }}</span>
            <span>已用时间: {{ formatDuration(elapsedTime) }}</span>
            <span>预计剩余: {{ formatDuration(estimatedRemaining) }}</span>
          </div>
        </div>
      </div>

      <!-- 实时指标 -->
      <div class="metrics-dashboard">
        <el-row :gutter="24">
          <el-col :span="6">
            <el-card class="metric-card">
              <el-statistic title="训练损失" :value="metrics.trainLoss" :precision="4">
                <template #suffix>
                  <el-icon :class="getLossChangeIcon()">
                    <component :is="getLossChangeIcon()" />
                  </el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="metric-card">
              <el-statistic title="验证损失" :value="metrics.valLoss" :precision="4">
                <template #suffix>
                  <el-icon :class="getValLossChangeIcon()">
                    <component :is="getValLossChangeIcon()" />
                  </el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="metric-card">
              <el-statistic title="训练准确率" :value="metrics.trainAcc" :precision="2" suffix="%">
                <template #suffix>
                  <span>%</span>
                  <el-icon :class="getAccChangeIcon()">
                    <component :is="getAccChangeIcon()" />
                  </el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="metric-card">
              <el-statistic title="验证准确率" :value="metrics.valAcc" :precision="2" suffix="%">
                <template #suffix>
                  <span>%</span>
                  <el-icon :class="getValAccChangeIcon()">
                    <component :is="getValAccChangeIcon()" />
                  </el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 详细监控 -->
      <div class="detailed-monitoring">
        <el-tabs v-model="activeMonitorTab" type="card">
          <!-- 训练曲线 -->
          <el-tab-pane label="训练曲线" name="curves">
            <div class="charts-container">
              <div class="chart-row">
                <div class="chart-item">
                  <h4>损失曲线</h4>
                  <div ref="lossChart" class="metric-chart"></div>
                </div>
                <div class="chart-item">
                  <h4>准确率曲线</h4>
                  <div ref="accChart" class="metric-chart"></div>
                </div>
              </div>
              
              <div class="chart-row" v-if="isDeepLearningModel">
                <div class="chart-item">
                  <h4>学习率变化</h4>
                  <div ref="lrChart" class="metric-chart"></div>
                </div>
                <div class="chart-item">
                  <h4>梯度范数</h4>
                  <div ref="gradChart" class="metric-chart"></div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 系统资源 -->
          <el-tab-pane label="系统资源" name="resources">
            <div class="resource-monitoring">
              <el-row :gutter="24">
                <el-col :span="12">
                  <div class="resource-item">
                    <h4>CPU 使用率</h4>
                    <el-progress 
                      :percentage="resourceMetrics.cpuUsage" 
                      :color="getResourceColor(resourceMetrics.cpuUsage)"
                    />
                    <div class="resource-details">
                      <span>核心数: {{ resourceMetrics.cpuCores }}</span>
                      <span>负载: {{ resourceMetrics.cpuLoad }}</span>
                    </div>
                  </div>
                </el-col>
                
                <el-col :span="12">
                  <div class="resource-item">
                    <h4>内存使用</h4>
                    <el-progress 
                      :percentage="resourceMetrics.memoryUsage" 
                      :color="getResourceColor(resourceMetrics.memoryUsage)"
                    />
                    <div class="resource-details">
                      <span>已用: {{ resourceMetrics.memoryUsed }}GB</span>
                      <span>总计: {{ resourceMetrics.memoryTotal }}GB</span>
                    </div>
                  </div>
                </el-col>
              </el-row>

              <el-row :gutter="24" v-if="resourceMetrics.gpuAvailable">
                <el-col :span="12">
                  <div class="resource-item">
                    <h4>GPU 使用率</h4>
                    <el-progress 
                      :percentage="resourceMetrics.gpuUsage" 
                      :color="getResourceColor(resourceMetrics.gpuUsage)"
                    />
                    <div class="resource-details">
                      <span>型号: {{ resourceMetrics.gpuModel }}</span>
                      <span>温度: {{ resourceMetrics.gpuTemp }}°C</span>
                    </div>
                  </div>
                </el-col>
                
                <el-col :span="12">
                  <div class="resource-item">
                    <h4>GPU 内存</h4>
                    <el-progress 
                      :percentage="resourceMetrics.gpuMemoryUsage" 
                      :color="getResourceColor(resourceMetrics.gpuMemoryUsage)"
                    />
                    <div class="resource-details">
                      <span>已用: {{ resourceMetrics.gpuMemoryUsed }}GB</span>
                      <span>总计: {{ resourceMetrics.gpuMemoryTotal }}GB</span>
                    </div>
                  </div>
                </el-col>
              </el-row>

              <div class="resource-chart">
                <h4>资源使用历史</h4>
                <div ref="resourceChart" class="resource-history-chart"></div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 训练日志 -->
          <el-tab-pane label="训练日志" name="logs">
            <div class="training-logs">
              <div class="logs-header">
                <div class="log-controls">
                  <el-select v-model="logLevel" size="small" style="width: 120px">
                    <el-option label="全部" value="all" />
                    <el-option label="信息" value="info" />
                    <el-option label="警告" value="warning" />
                    <el-option label="错误" value="error" />
                  </el-select>
                  <el-button size="small" @click="clearLogs">清空日志</el-button>
                  <el-button size="small" @click="downloadLogs">下载日志</el-button>
                </div>
                <el-switch 
                  v-model="autoScroll" 
                  active-text="自动滚动"
                  inactive-text=""
                  size="small"
                />
              </div>
              
              <div class="logs-content" ref="logsContainer">
                <div 
                  v-for="log in filteredLogs" 
                  :key="log.id"
                  :class="['log-entry', `log-${log.level}`]"
                >
                  <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
                  <span class="log-level">{{ log.level.toUpperCase() }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 模型检查点 -->
          <el-tab-pane label="检查点" name="checkpoints">
            <div class="checkpoint-management">
              <div class="checkpoint-controls">
                <el-button @click="saveCheckpoint" :loading="savingCheckpoint">
                  <el-icon><DocumentAdd /></el-icon>
                  保存检查点
                </el-button>
                <el-button @click="loadCheckpoint" :disabled="checkpoints.length === 0">
                  <el-icon><FolderOpened /></el-icon>
                  加载检查点
                </el-button>
              </div>

              <el-table :data="checkpoints" class="checkpoints-table">
                <el-table-column prop="epoch" label="轮次" width="80" />
                <el-table-column prop="timestamp" label="保存时间" width="180">
                  <template #default="{ row }">
                    {{ formatTimestamp(row.timestamp) }}
                  </template>
                </el-table-column>
                <el-table-column prop="metrics" label="性能指标">
                  <template #default="{ row }">
                    <div class="checkpoint-metrics">
                      <el-tag size="small">损失: {{ row.metrics.loss.toFixed(4) }}</el-tag>
                      <el-tag size="small" type="success">准确率: {{ row.metrics.acc.toFixed(2) }}%</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="size" label="文件大小" width="100" />
                <el-table-column label="操作" width="150">
                  <template #default="{ row, $index }">
                    <el-button size="small" @click="restoreCheckpoint(row)">恢复</el-button>
                    <el-button size="small" type="danger" @click="deleteCheckpoint($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 训练完成结果 -->
      <div v-if="trainingTask?.status === 'completed'" class="training-results">
        <el-result 
          icon="success" 
          title="训练完成!" 
          :sub-title="`耗时 ${formatDuration(elapsedTime)}，最佳验证准确率: ${metrics.bestValAcc.toFixed(2)}%`"
        >
          <template #extra>
            <el-button type="primary" @click="viewResults">查看详细结果</el-button>
            <el-button @click="downloadModel">下载模型</el-button>
            <el-button @click="startNewTraining">开始新训练</el-button>
          </template>
        </el-result>
      </div>

      <!-- 训练失败 -->
      <div v-if="trainingTask?.status === 'failed'" class="training-error">
        <el-result 
          icon="error" 
          title="训练失败" 
          :sub-title="errorMessage"
        >
          <template #extra>
            <el-button type="primary" @click="retryTraining">重试训练</el-button>
            <el-button @click="viewErrorLogs">查看错误日志</el-button>
            <el-button @click="contactSupport">联系支持</el-button>
          </template>
        </el-result>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor, VideoPause, VideoPlay, Close, DocumentAdd, FolderOpened,
  CaretTop, CaretBottom
} from '@element-plus/icons-vue'

interface TrainingTask {
  id: string
  name: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed'
  progress: number
  createdAt: Date
  config: any
  factors: any[]
}

interface TrainingMetrics {
  trainLoss: number
  valLoss: number
  trainAcc: number
  valAcc: number
  bestValAcc: number
  learningRate?: number
  gradNorm?: number
}

interface ResourceMetrics {
  cpuUsage: number
  cpuCores: number
  cpuLoad: number
  memoryUsage: number
  memoryUsed: number
  memoryTotal: number
  gpuAvailable: boolean
  gpuUsage: number
  gpuMemoryUsage: number
  gpuMemoryUsed: number
  gpuMemoryTotal: number
  gpuModel: string
  gpuTemp: number
}

interface LogEntry {
  id: number
  timestamp: Date
  level: 'info' | 'warning' | 'error'
  message: string
}

const props = defineProps<{
  trainingTask: TrainingTask | null
}>()

const emit = defineEmits(['training-complete', 'training-stopped'])

// 响应式数据
const activeMonitorTab = ref('curves')
const currentEpoch = ref(0)
const totalEpochs = ref(100)
const elapsedTime = ref(0)
const estimatedRemaining = ref(0)
const logLevel = ref('all')
const autoScroll = ref(true)
const savingCheckpoint = ref(false)
const errorMessage = ref('')

// 图表DOM引用
const lossChart = ref<HTMLElement>()
const accChart = ref<HTMLElement>()
const lrChart = ref<HTMLElement>()
const gradChart = ref<HTMLElement>()
const resourceChart = ref<HTMLElement>()
const logsContainer = ref<HTMLElement>()

// 训练指标
const metrics = reactive<TrainingMetrics>({
  trainLoss: 0.5,
  valLoss: 0.55,
  trainAcc: 75.2,
  valAcc: 73.8,
  bestValAcc: 73.8,
  learningRate: 0.001,
  gradNorm: 1.2
})

// 资源指标
const resourceMetrics = reactive<ResourceMetrics>({
  cpuUsage: 65,
  cpuCores: 8,
  cpuLoad: 2.1,
  memoryUsage: 40,
  memoryUsed: 6.4,
  memoryTotal: 16,
  gpuAvailable: true,
  gpuUsage: 85,
  gpuMemoryUsage: 70,
  gpuMemoryUsed: 5.6,
  gpuMemoryTotal: 8,
  gpuModel: 'NVIDIA RTX 4090',
  gpuTemp: 72
})

// 训练日志
const logs = ref<LogEntry[]>([])
const checkpoints = ref<any[]>([])

let monitorInterval: NodeJS.Timeout | null = null

// 计算属性
const overallProgress = computed(() => {
  if (!totalEpochs.value) return 0
  return Math.round((currentEpoch.value / totalEpochs.value) * 100)
})

const isDeepLearningModel = computed(() => {
  const modelType = props.trainingTask?.config?.modelConfig?.type
  return ['LSTM', 'GRU', 'Transformer'].includes(modelType)
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const getStatusTagType = (status: string) => {
  switch (status) {
    case 'running': return 'warning'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'paused': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '准备中'
    case 'running': return '训练中'
    case 'paused': return '已暂停'
    case 'completed': return '已完成'
    case 'failed': return '训练失败'
    default: return '未知'
  }
}

const getProgressStatus = () => {
  if (props.trainingTask?.status === 'failed') return 'exception'
  if (props.trainingTask?.status === 'completed') return 'success'
  return undefined
}

const getLossChangeIcon = () => {
  // 基于损失变化趋势返回图标
  return 'CaretBottom' // 损失下降
}

const getValLossChangeIcon = () => {
  return 'CaretBottom'
}

const getAccChangeIcon = () => {
  return 'CaretTop' // 准确率上升
}

const getValAccChangeIcon = () => {
  return 'CaretTop'
}

const getResourceColor = (usage: number) => {
  if (usage > 90) return '#f56c6c'
  if (usage > 70) return '#e6a23c'
  return '#67c23a'
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}时${minutes}分${secs}秒`
  }
  if (minutes > 0) {
    return `${minutes}分${secs}秒`
  }
  return `${secs}秒`
}

const formatTimestamp = (timestamp: Date) => {
  return timestamp.toLocaleString('zh-CN')
}

const pauseTraining = async () => {
  try {
    await ElMessageBox.confirm('确认暂停当前训练？', '确认暂停', {
      type: 'warning'
    })
    
    // 模拟API调用
    ElMessage.success('训练已暂停')
    if (props.trainingTask) {
      props.trainingTask.status = 'paused'
    }
  } catch {
    // 用户取消
  }
}

const resumeTraining = () => {
  ElMessage.info('训练已恢复')
  if (props.trainingTask) {
    props.trainingTask.status = 'running'
  }
}

const stopTraining = async () => {
  try {
    await ElMessageBox.confirm('确认停止当前训练？训练进度将会丢失！', '确认停止', {
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    
    // 模拟API调用
    ElMessage.success('训练已停止')
    emit('training-stopped')
  } catch {
    // 用户取消
  }
}

const clearLogs = () => {
  logs.value = []
  ElMessage.success('日志已清空')
}

const downloadLogs = () => {
  const logContent = logs.value.map(log => 
    `[${formatTimestamp(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}`
  ).join('\n')
  
  const blob = new Blob([logContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `training_logs_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const saveCheckpoint = async () => {
  savingCheckpoint.value = true
  
  // 模拟保存过程
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  const checkpoint = {
    epoch: currentEpoch.value,
    timestamp: new Date(),
    metrics: {
      loss: metrics.valLoss,
      acc: metrics.valAcc
    },
    size: `${Math.random() * 100 + 50}MB`
  }
  
  checkpoints.value.unshift(checkpoint)
  savingCheckpoint.value = false
  ElMessage.success('检查点保存成功')
}

const loadCheckpoint = () => {
  // 实现检查点加载逻辑
  ElMessage.info('检查点加载功能开发中')
}

const restoreCheckpoint = (checkpoint: any) => {
  ElMessage.success(`已恢复到第 ${checkpoint.epoch} 轮的检查点`)
}

const deleteCheckpoint = (index: number) => {
  checkpoints.value.splice(index, 1)
  ElMessage.success('检查点已删除')
}

const viewResults = () => {
  emit('training-complete', {
    metrics: metrics,
    checkpoints: checkpoints.value
  })
}

const downloadModel = () => {
  ElMessage.success('模型下载已开始')
}

const startNewTraining = () => {
  ElMessage.info('跳转到新建训练页面')
}

const retryTraining = () => {
  ElMessage.info('正在重试训练...')
}

const viewErrorLogs = () => {
  activeMonitorTab.value = 'logs'
  logLevel.value = 'error'
}

const contactSupport = () => {
  ElMessage.info('正在打开技术支持')
}

const startMonitoring = () => {
  if (!monitorInterval) {
    monitorInterval = setInterval(() => {
      updateMetrics()
      updateResourceMetrics()
      addRandomLog()
      
      if (props.trainingTask?.status === 'running') {
        elapsedTime.value += 1
        
        // 模拟训练进度
        if (Math.random() < 0.1) { // 10% 概率增加epoch
          currentEpoch.value = Math.min(currentEpoch.value + 1, totalEpochs.value)
          
          if (currentEpoch.value >= totalEpochs.value) {
            if (props.trainingTask) {
              props.trainingTask.status = 'completed'
            }
            stopMonitoring()
          }
        }
      }
    }, 1000)
  }
}

const stopMonitoring = () => {
  if (monitorInterval) {
    clearInterval(monitorInterval)
    monitorInterval = null
  }
}

const updateMetrics = () => {
  // 模拟指标更新
  metrics.trainLoss = Math.max(0.1, metrics.trainLoss - Math.random() * 0.01)
  metrics.valLoss = Math.max(0.1, metrics.valLoss - Math.random() * 0.008)
  metrics.trainAcc = Math.min(100, metrics.trainAcc + Math.random() * 0.5)
  metrics.valAcc = Math.min(100, metrics.valAcc + Math.random() * 0.3)
  
  if (metrics.valAcc > metrics.bestValAcc) {
    metrics.bestValAcc = metrics.valAcc
  }
  
  if (isDeepLearningModel.value) {
    metrics.learningRate = metrics.learningRate! * (0.99 + Math.random() * 0.02)
    metrics.gradNorm = 0.5 + Math.random() * 2
  }
}

const updateResourceMetrics = () => {
  // 模拟资源指标更新
  resourceMetrics.cpuUsage = Math.max(20, Math.min(100, resourceMetrics.cpuUsage + (Math.random() - 0.5) * 10))
  resourceMetrics.memoryUsage = Math.max(20, Math.min(90, resourceMetrics.memoryUsage + (Math.random() - 0.5) * 5))
  
  if (resourceMetrics.gpuAvailable) {
    resourceMetrics.gpuUsage = Math.max(60, Math.min(100, resourceMetrics.gpuUsage + (Math.random() - 0.5) * 8))
    resourceMetrics.gpuMemoryUsage = Math.max(40, Math.min(95, resourceMetrics.gpuMemoryUsage + (Math.random() - 0.5) * 6))
    resourceMetrics.gpuTemp = Math.max(65, Math.min(85, resourceMetrics.gpuTemp + (Math.random() - 0.5) * 2))
  }
}

const addRandomLog = () => {
  const messages = [
    'Epoch completed successfully',
    'Validation metrics updated',
    'Learning rate adjusted',
    'Checkpoint saved',
    'Memory usage optimized'
  ]
  
  const levels: ('info' | 'warning' | 'error')[] = ['info', 'info', 'info', 'warning', 'error']
  
  if (Math.random() < 0.3) { // 30% 概率添加日志
    const log: LogEntry = {
      id: Date.now(),
      timestamp: new Date(),
      level: levels[Math.floor(Math.random() * levels.length)],
      message: messages[Math.floor(Math.random() * messages.length)]
    }
    
    logs.value.push(log)
    
    // 保持日志数量在合理范围
    if (logs.value.length > 1000) {
      logs.value = logs.value.slice(-500)
    }
    
    // 自动滚动
    if (autoScroll.value) {
      nextTick(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      })
    }
  }
}

// 生命周期
onMounted(() => {
  if (props.trainingTask?.config?.trainingParams?.epochs) {
    totalEpochs.value = props.trainingTask.config.trainingParams.epochs
  }
  
  // 添加一些初始日志
  logs.value = [
    {
      id: 1,
      timestamp: new Date(),
      level: 'info',
      message: 'Training session started'
    },
    {
      id: 2,
      timestamp: new Date(),
      level: 'info',
      message: 'Model initialization completed'
    },
    {
      id: 3,
      timestamp: new Date(),
      level: 'info',
      message: 'Data loading completed'
    }
  ]
  
  startMonitoring()
})

onUnmounted(() => {
  stopMonitoring()
})
</script>

<style scoped>
.training-monitor {
  margin-top: 24px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overall-progress {
  margin-bottom: 24px;
}

.progress-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.metrics-dashboard {
  margin-bottom: 32px;
}

.metric-card {
  text-align: center;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.detailed-monitoring {
  margin-top: 24px;
}

.charts-container {
  padding: 20px;
}

.chart-row {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.chart-item {
  flex: 1;
}

.chart-item h4 {
  margin: 0 0 16px 0;
  color: #303133;
  text-align: center;
}

.metric-chart {
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.resource-monitoring {
  padding: 20px;
}

.resource-item {
  margin-bottom: 24px;
}

.resource-item h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.resource-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
}

.resource-chart {
  margin-top: 32px;
}

.resource-chart h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.resource-history-chart {
  width: 100%;
  height: 300px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.training-logs {
  padding: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.log-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.logs-content {
  height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #e8e8e8;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.4;
}

.log-entry {
  margin-bottom: 4px;
  display: flex;
  gap: 12px;
}

.log-timestamp {
  color: #666;
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  width: 60px;
  font-weight: bold;
}

.log-info .log-level {
  color: #67c23a;
}

.log-warning .log-level {
  color: #e6a23c;
}

.log-error .log-level {
  color: #f56c6c;
}

.log-message {
  flex: 1;
}

.checkpoint-management {
  padding: 20px;
}

.checkpoint-controls {
  margin-bottom: 24px;
  display: flex;
  gap: 12px;
}

.checkpoints-table {
  width: 100%;
}

.checkpoint-metrics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.training-results,
.training-error {
  margin-top: 32px;
}

@media (max-width: 768px) {
  .monitor-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .progress-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .chart-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .logs-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .log-controls {
    justify-content: center;
  }
  
  .checkpoint-controls {
    flex-direction: column;
  }
}
</style>