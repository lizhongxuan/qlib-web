<template>
  <div class="resource-monitor">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Monitor /></el-icon>
            <span>系统资源监控</span>
          </div>
          <div class="header-right">
            <el-switch 
              v-model="autoRefresh" 
              active-text="自动刷新" 
              @change="toggleAutoRefresh"
            />
            <el-button @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 系统概览 -->
      <div class="system-overview">
        <el-row :gutter="16">
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon cpu">
                <el-icon><CpuFill /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ systemMetrics.cpu_usage }}%</div>
                <div class="metric-label">CPU 使用率</div>
                <el-progress 
                  :percentage="systemMetrics.cpu_usage" 
                  :color="getCpuColor(systemMetrics.cpu_usage)"
                  :show-text="false"
                />
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon memory">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ systemMetrics.memory_usage }}%</div>
                <div class="metric-label">内存使用率</div>
                <el-progress 
                  :percentage="systemMetrics.memory_usage" 
                  :color="getMemoryColor(systemMetrics.memory_usage)"
                  :show-text="false"
                />
                <div class="metric-detail">
                  {{ formatBytes(systemMetrics.memory_used) }} / {{ formatBytes(systemMetrics.memory_total) }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon disk">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ systemMetrics.disk_usage }}%</div>
                <div class="metric-label">磁盘使用率</div>
                <el-progress 
                  :percentage="systemMetrics.disk_usage" 
                  :color="getDiskColor(systemMetrics.disk_usage)"
                  :show-text="false"
                />
                <div class="metric-detail">
                  {{ formatBytes(systemMetrics.disk_used) }} / {{ formatBytes(systemMetrics.disk_total) }}
                </div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon tasks">
                <el-icon><List /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-value">{{ taskQueue.active }}</div>
                <div class="metric-label">活跃任务</div>
                <div class="task-breakdown">
                  <div class="task-item">
                    <span>等待: {{ taskQueue.pending }}</span>
                    <span>完成: {{ taskQueue.completed }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 实时图表 -->
      <div class="realtime-charts">
        <el-row :gutter="16">
          <el-col :span="12">
            <div class="chart-container">
              <h4>CPU & 内存使用趋势</h4>
              <div ref="systemChartRef" class="chart"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <h4>任务队列状态</h4>
              <div ref="taskChartRef" class="chart"></div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 进程列表 -->
      <div class="process-list">
        <h4>运行中的实验</h4>
        <el-table :data="runningExperiments" v-loading="loadingExperiments">
          <el-table-column prop="name" label="实验名称" min-width="200" />
          <el-table-column prop="progress" label="进度" width="150">
            <template #default="scope">
              <el-progress 
                :percentage="scope.row.progress || 0" 
                :show-text="true"
                :format="(percentage) => `${percentage}%`"
              />
            </template>
          </el-table-column>
          <el-table-column prop="cpu_usage" label="CPU使用" width="100">
            <template #default="scope">
              {{ scope.row.cpu_usage || 0 }}%
            </template>
          </el-table-column>
          <el-table-column prop="memory_usage" label="内存使用" width="120">
            <template #default="scope">
              {{ formatBytes(scope.row.memory_usage || 0) }}
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始时间" width="150">
            <template #default="scope">
              {{ formatTime(scope.row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="estimated_remaining" label="预计剩余" width="120">
            <template #default="scope">
              <span v-if="scope.row.estimated_remaining">
                {{ formatDuration(scope.row.estimated_remaining) }}
              </span>
              <span v-else class="text-muted">未知</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button 
                type="text" 
                size="small"
                @click="viewExperiment(scope.row.id)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 系统信息 -->
      <div class="system-info">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-descriptions title="系统信息" :column="1" size="small" border>
              <el-descriptions-item label="操作系统">
                {{ systemInfo.os_name }} {{ systemInfo.os_version }}
              </el-descriptions-item>
              <el-descriptions-item label="Python版本">
                {{ systemInfo.python_version }}
              </el-descriptions-item>
              <el-descriptions-item label="Qlib版本">
                {{ systemInfo.qlib_version }}
              </el-descriptions-item>
              <el-descriptions-item label="系统启动时间">
                {{ formatTime(systemInfo.boot_time) }}
              </el-descriptions-item>
              <el-descriptions-item label="运行时长">
                {{ formatDuration(systemInfo.uptime) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <el-descriptions title="硬件信息" :column="1" size="small" border>
              <el-descriptions-item label="CPU核心数">
                {{ systemInfo.cpu_cores }}
              </el-descriptions-item>
              <el-descriptions-item label="CPU频率">
                {{ systemInfo.cpu_frequency }} GHz
              </el-descriptions-item>
              <el-descriptions-item label="总内存">
                {{ formatBytes(systemInfo.total_memory) }}
              </el-descriptions-item>
              <el-descriptions-item label="GPU信息">
                {{ systemInfo.gpu_info || '未检测到GPU' }}
              </el-descriptions-item>
              <el-descriptions-item label="网络接口">
                {{ systemInfo.network_interfaces?.join(', ') || '无' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </div>

      <!-- 警告和建议 -->
      <div class="alerts-section" v-if="systemAlerts.length > 0">
        <h4>系统警告</h4>
        <div class="alerts-list">
          <el-alert
            v-for="alert in systemAlerts"
            :key="alert.id"
            :title="alert.title"
            :description="alert.message"
            :type="alert.type"
            show-icon
            :closable="false"
            style="margin-bottom: 8px;"
          >
            <template #default>
              <div class="alert-content">
                <div>{{ alert.message }}</div>
                <div class="alert-suggestion" v-if="alert.suggestion">
                  <strong>建议:</strong> {{ alert.suggestion }}
                </div>
              </div>
            </template>
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  Monitor,
  Refresh,
  CpuFill,
  FolderOpened,
  List
} from '@element-plus/icons-vue'
import { useWebSocket } from '@/utils/websocket'

interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  memory_used: number
  memory_total: number
  disk_usage: number
  disk_used: number
  disk_total: number
  timestamp: string
}

interface TaskQueue {
  active: number
  pending: number
  completed: number
  failed: number
}

interface RunningExperiment {
  id: string
  name: string
  progress: number
  cpu_usage: number
  memory_usage: number
  start_time: string
  estimated_remaining: number
}

interface SystemInfo {
  os_name: string
  os_version: string
  python_version: string
  qlib_version: string
  boot_time: string
  uptime: number
  cpu_cores: number
  cpu_frequency: number
  total_memory: number
  gpu_info: string
  network_interfaces: string[]
}

interface SystemAlert {
  id: string
  title: string
  message: string
  type: 'warning' | 'error' | 'info'
  suggestion?: string
}

const router = useRouter()
const { subscribe, unsubscribe } = useWebSocket()

// 响应式数据
const loading = ref(false)
const loadingExperiments = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<number>()

const systemMetrics = reactive<SystemMetrics>({
  cpu_usage: 0,
  memory_usage: 0,
  memory_used: 0,
  memory_total: 0,
  disk_usage: 0,
  disk_used: 0,
  disk_total: 0,
  timestamp: ''
})

const taskQueue = reactive<TaskQueue>({
  active: 0,
  pending: 0,
  completed: 0,
  failed: 0
})

const runningExperiments = ref<RunningExperiment[]>([])
const systemInfo = reactive<SystemInfo>({
  os_name: '',
  os_version: '',
  python_version: '',
  qlib_version: '',
  boot_time: '',
  uptime: 0,
  cpu_cores: 0,
  cpu_frequency: 0,
  total_memory: 0,
  gpu_info: '',
  network_interfaces: []
})

const systemAlerts = ref<SystemAlert[]>([])

// 图表相关
const systemChartRef = ref()
const taskChartRef = ref()
let systemChart: echarts.ECharts | null = null
let taskChart: echarts.ECharts | null = null

// 历史数据存储（用于图表）
const systemHistory = reactive({
  timestamps: [] as string[],
  cpuUsage: [] as number[],
  memoryUsage: [] as number[]
})

const taskHistory = reactive({
  timestamps: [] as string[],
  active: [] as number[],
  pending: [] as number[],
  completed: [] as number[]
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchSystemMetrics(),
      fetchTaskQueue(),
      fetchRunningExperiments(),
      fetchSystemInfo()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchSystemMetrics = async () => {
  try {
    const response = await fetch('/api/v1/system/metrics')
    const data = await response.json()
    
    if (data.success) {
      Object.assign(systemMetrics, data.data)
      updateSystemHistory()
      checkSystemAlerts()
    }
  } catch (error) {
    console.error('获取系统指标失败:', error)
  }
}

const fetchTaskQueue = async () => {
  try {
    const response = await fetch('/api/v1/system/task-queue')
    const data = await response.json()
    
    if (data.success) {
      Object.assign(taskQueue, data.data)
      updateTaskHistory()
    }
  } catch (error) {
    console.error('获取任务队列状态失败:', error)
  }
}

const fetchRunningExperiments = async () => {
  loadingExperiments.value = true
  try {
    const response = await fetch('/api/v1/experiments?status=running')
    const data = await response.json()
    
    if (data.success) {
      runningExperiments.value = data.data.items.map((exp: any) => ({
        id: exp.id,
        name: exp.name,
        progress: exp.progress || 0,
        cpu_usage: exp.resource_usage?.cpu || 0,
        memory_usage: exp.resource_usage?.memory || 0,
        start_time: exp.created_at,
        estimated_remaining: exp.estimated_remaining || 0
      }))
    }
  } catch (error) {
    console.error('获取运行中实验失败:', error)
  } finally {
    loadingExperiments.value = false
  }
}

const fetchSystemInfo = async () => {
  try {
    const response = await fetch('/api/v1/system/info')
    const data = await response.json()
    
    if (data.success) {
      Object.assign(systemInfo, data.data)
    }
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

const updateSystemHistory = () => {
  const maxPoints = 50
  const now = new Date().toLocaleTimeString()
  
  systemHistory.timestamps.push(now)
  systemHistory.cpuUsage.push(systemMetrics.cpu_usage)
  systemHistory.memoryUsage.push(systemMetrics.memory_usage)
  
  // 保持固定长度
  if (systemHistory.timestamps.length > maxPoints) {
    systemHistory.timestamps.shift()
    systemHistory.cpuUsage.shift()
    systemHistory.memoryUsage.shift()
  }
  
  updateSystemChart()
}

const updateTaskHistory = () => {
  const maxPoints = 50
  const now = new Date().toLocaleTimeString()
  
  taskHistory.timestamps.push(now)
  taskHistory.active.push(taskQueue.active)
  taskHistory.pending.push(taskQueue.pending)
  taskHistory.completed.push(taskQueue.completed)
  
  // 保持固定长度
  if (taskHistory.timestamps.length > maxPoints) {
    taskHistory.timestamps.shift()
    taskHistory.active.shift()
    taskHistory.pending.shift()
    taskHistory.completed.shift()
  }
  
  updateTaskChart()
}

const checkSystemAlerts = () => {
  const alerts: SystemAlert[] = []
  
  // CPU使用率警告
  if (systemMetrics.cpu_usage > 90) {
    alerts.push({
      id: 'high-cpu',
      title: 'CPU使用率过高',
      message: `当前CPU使用率为${systemMetrics.cpu_usage}%`,
      type: 'error',
      suggestion: '考虑暂停一些非关键实验或优化实验配置'
    })
  } else if (systemMetrics.cpu_usage > 80) {
    alerts.push({
      id: 'medium-cpu',
      title: 'CPU使用率较高',
      message: `当前CPU使用率为${systemMetrics.cpu_usage}%`,
      type: 'warning',
      suggestion: '建议监控系统负载，必要时调整实验并发数'
    })
  }
  
  // 内存使用率警告
  if (systemMetrics.memory_usage > 90) {
    alerts.push({
      id: 'high-memory',
      title: '内存使用率过高',
      message: `当前内存使用率为${systemMetrics.memory_usage}%`,
      type: 'error',
      suggestion: '建议暂停一些内存密集型实验或重启系统'
    })
  } else if (systemMetrics.memory_usage > 85) {
    alerts.push({
      id: 'medium-memory',
      title: '内存使用率较高',
      message: `当前内存使用率为${systemMetrics.memory_usage}%`,
      type: 'warning',
      suggestion: '建议清理不必要的进程或调整实验参数'
    })
  }
  
  // 磁盘使用率警告
  if (systemMetrics.disk_usage > 95) {
    alerts.push({
      id: 'high-disk',
      title: '磁盘空间不足',
      message: `当前磁盘使用率为${systemMetrics.disk_usage}%`,
      type: 'error',
      suggestion: '立即清理不必要的文件或实验结果数据'
    })
  } else if (systemMetrics.disk_usage > 85) {
    alerts.push({
      id: 'medium-disk',
      title: '磁盘空间较少',
      message: `当前磁盘使用率为${systemMetrics.disk_usage}%`,
      type: 'warning',
      suggestion: '建议定期清理过期的实验数据'
    })
  }
  
  systemAlerts.value = alerts
}

const initSystemChart = () => {
  if (!systemChartRef.value) return
  
  systemChart = echarts.init(systemChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['CPU使用率', '内存使用率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: systemHistory.timestamps
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        data: systemHistory.cpuUsage,
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
          opacity: 0.3
        }
      },
      {
        name: '内存使用率',
        type: 'line',
        data: systemHistory.memoryUsage,
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          opacity: 0.3
        }
      }
    ]
  }
  
  systemChart.setOption(option)
}

const initTaskChart = () => {
  if (!taskChartRef.value) return
  
  taskChart = echarts.init(taskChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['活跃任务', '等待任务', '完成任务']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: taskHistory.timestamps
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '活跃任务',
        type: 'line',
        data: taskHistory.active,
        itemStyle: {
          color: '#e6a23c'
        }
      },
      {
        name: '等待任务',
        type: 'line',
        data: taskHistory.pending,
        itemStyle: {
          color: '#f56c6c'
        }
      },
      {
        name: '完成任务',
        type: 'line',
        data: taskHistory.completed,
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
  }
  
  taskChart.setOption(option)
}

const updateSystemChart = () => {
  if (systemChart) {
    systemChart.setOption({
      xAxis: {
        data: systemHistory.timestamps
      },
      series: [
        { data: systemHistory.cpuUsage },
        { data: systemHistory.memoryUsage }
      ]
    })
  }
}

const updateTaskChart = () => {
  if (taskChart) {
    taskChart.setOption({
      xAxis: {
        data: taskHistory.timestamps
      },
      series: [
        { data: taskHistory.active },
        { data: taskHistory.pending },
        { data: taskHistory.completed }
      ]
    })
  }
}

const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  refreshInterval.value = window.setInterval(() => {
    refreshData()
  }, 5000) // 每5秒刷新
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = undefined
  }
}

const viewExperiment = (experimentId: string) => {
  router.push(`/experiments/${experimentId}`)
}

// 工具函数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString()
}

const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return `${Math.floor(seconds)}秒`
  }
}

const getCpuColor = (usage: number): string => {
  if (usage > 90) return '#f56c6c'
  if (usage > 80) return '#e6a23c'
  if (usage > 60) return '#409eff'
  return '#67c23a'
}

const getMemoryColor = (usage: number): string => {
  if (usage > 90) return '#f56c6c'
  if (usage > 85) return '#e6a23c'
  if (usage > 70) return '#409eff'
  return '#67c23a'
}

const getDiskColor = (usage: number): string => {
  if (usage > 95) return '#f56c6c'
  if (usage > 85) return '#e6a23c'
  if (usage > 70) return '#409eff'
  return '#67c23a'
}

// WebSocket消息处理
const handleSystemUpdate = (message: any) => {
  if (message.data) {
    Object.assign(systemMetrics, message.data)
    updateSystemHistory()
    checkSystemAlerts()
  }
}

const handleTaskQueueUpdate = (message: any) => {
  if (message.data) {
    Object.assign(taskQueue, message.data)
    updateTaskHistory()
  }
}

// 生命周期
onMounted(async () => {
  await refreshData()
  
  // 初始化图表
  await nextTick()
  initSystemChart()
  initTaskChart()
  
  // 开始自动刷新
  if (autoRefresh.value) {
    startAutoRefresh()
  }
  
  // 订阅WebSocket消息
  subscribe('system', handleSystemUpdate)
  subscribe('task_queue', handleTaskQueueUpdate)
  
  // 窗口大小变化时调整图表
  window.addEventListener('resize', () => {
    systemChart?.resize()
    taskChart?.resize()
  })
})

onUnmounted(() => {
  stopAutoRefresh()
  
  // 销毁图表
  systemChart?.dispose()
  taskChart?.dispose()
  
  // 取消订阅
  unsubscribe('system', handleSystemUpdate)
  unsubscribe('task_queue', handleTaskQueueUpdate)
  
  // 移除事件监听
  window.removeEventListener('resize', () => {
    systemChart?.resize()
    taskChart?.resize()
  })
})
</script>

<style scoped>
.resource-monitor {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.system-overview {
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  height: 120px;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  flex-shrink: 0;
}

.metric-icon.cpu {
  background: linear-gradient(135deg, #409eff, #67c23a);
}

.metric-icon.memory {
  background: linear-gradient(135deg, #67c23a, #e6a23c);
}

.metric-icon.disk {
  background: linear-gradient(135deg, #e6a23c, #f56c6c);
}

.metric-icon.tasks {
  background: linear-gradient(135deg, #f56c6c, #409eff);
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-detail {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.task-breakdown {
  margin-top: 8px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.realtime-charts {
  margin-bottom: 24px;
}

.chart-container {
  padding: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.chart-container h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.chart {
  height: 300px;
}

.process-list {
  margin-bottom: 24px;
}

.process-list h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.text-muted {
  color: #999;
}

.system-info {
  margin-bottom: 24px;
}

.alerts-section h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #f56c6c;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-content {
  width: 100%;
}

.alert-suggestion {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}
</style>