<template>
  <div class="qlib-dashboard">
    <!-- 顶部状态栏 -->
    <div class="dashboard-header">
      <div class="system-status-card">
        <div class="status-item">
          <div class="status-icon" :class="systemHealth">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="status-info">
            <h3>Qlib系统状态</h3>
            <p :class="systemHealthClass">{{ systemHealthText }}</p>
            <small>最后检查: {{ formatTime(systemStatus.last_health_check) }}</small>
          </div>
        </div>
        <div class="status-metrics">
          <div class="metric">
            <div class="metric-value">{{ systemStatus.qlib_version || 'N/A' }}</div>
            <div class="metric-label">Qlib版本</div>
          </div>
          <div class="metric">
            <div class="metric-value" :class="getStatusColor(systemStatus.data_status)">
              {{ getStatusText(systemStatus.data_status) }}
            </div>
            <div class="metric-label">数据源状态</div>
          </div>
          <div class="metric">
            <div class="metric-value" :class="getStatusColor(systemStatus.cache_status)">
              {{ getStatusText(systemStatus.cache_status) }}
            </div>
            <div class="metric-label">缓存状态</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <el-row :gutter="24">
        <!-- 左侧列 -->
        <el-col :span="8">
          <!-- 数据概况卡片 -->
          <el-card class="data-overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><DataBoard /></el-icon>
                <span>数据概况</span>
                <el-button text size="small" @click="refreshData">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="data-stats">
              <div class="stat-item">
                <div class="stat-number">{{ formatNumber(dataStats.stockCount) }}</div>
                <div class="stat-label">股票数量</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ formatNumber(dataStats.tradingDays) }}</div>
                <div class="stat-label">交易日</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ formatPercent(dataStats.coverage) }}</div>
                <div class="stat-label">数据覆盖率</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ formatDate(dataStats.lastUpdate) }}</div>
                <div class="stat-label">最后更新</div>
              </div>
            </div>
          </el-card>

          <!-- 因子库状态 -->
          <el-card class="factor-status-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><MagicStick /></el-icon>
                <span>因子库状态</span>
              </div>
            </template>
            <div class="factor-stats">
              <div class="progress-item">
                <div class="progress-label">
                  <span>内置因子</span>
                  <span class="progress-value">{{ factorStats.builtIn }} / {{ factorStats.total }}</span>
                </div>
                <el-progress
                  :percentage="factorStats.total ? (factorStats.builtIn / factorStats.total * 100) : 0"
                  :stroke-width="8"
                  color="#409eff"
                />
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>自定义因子</span>
                  <span class="progress-value">{{ factorStats.custom }}</span>
                </div>
                <el-progress
                  :percentage="factorStats.total ? (factorStats.custom / factorStats.total * 100) : 0"
                  :stroke-width="8"
                  color="#67c23a"
                />
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>已验证因子</span>
                  <span class="progress-value">{{ factorStats.validated }}</span>
                </div>
                <el-progress
                  :percentage="factorStats.total ? (factorStats.validated / factorStats.total * 100) : 0"
                  :stroke-width="8"
                  color="#e6a23c"
                />
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 中间列 -->
        <el-col :span="8">
          <!-- 模型训练状态 -->
          <el-card class="model-status-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Cpu /></el-icon>
                <span>模型状态</span>
              </div>
            </template>
            <div class="model-stats">
              <div class="stat-row">
                <div class="stat-item">
                  <div class="stat-number text-success">{{ modelStats.trained }}</div>
                  <div class="stat-label">已训练</div>
                </div>
                <div class="stat-item">
                  <div class="stat-number text-warning">{{ modelStats.training }}</div>
                  <div class="stat-label">训练中</div>
                </div>
                <div class="stat-item">
                  <div class="stat-number text-danger">{{ modelStats.failed }}</div>
                  <div class="stat-label">失败</div>
                </div>
              </div>
              <div class="performance-metric">
                <div class="metric-label">平均表现 (Sharpe)</div>
                <div class="metric-value large">{{ formatNumber(modelStats.avg_performance, 3) }}</div>
              </div>
            </div>
          </el-card>

          <!-- 活跃任务 -->
          <el-card class="active-tasks-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Loading /></el-icon>
                <span>活跃任务</span>
              </div>
            </template>
            <div class="active-tasks">
              <div v-if="activeTasks.length === 0" class="no-tasks">
                <el-icon><CircleCheck /></el-icon>
                <p>暂无活跃任务</p>
              </div>
              <div v-else class="tasks-list">
                <div v-for="task in activeTasks.slice(0, 3)" :key="task.id" class="task-item">
                  <div class="task-info">
                    <div class="task-name">{{ task.name }}</div>
                    <div class="task-type">{{ task.type }}</div>
                  </div>
                  <div class="task-progress">
                    <el-progress
                      :percentage="task.progress"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getTaskColor(task.type)"
                    />
                    <span class="progress-text">{{ task.progress }}%</span>
                  </div>
                </div>
                <el-button v-if="activeTasks.length > 3" text type="primary" @click="viewAllTasks">
                  查看全部 {{ activeTasks.length }} 个任务
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧列 -->
        <el-col :span="8">
          <!-- 回测结果概览 -->
          <el-card class="backtest-overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><TrendCharts /></el-icon>
                <span>回测概览</span>
              </div>
            </template>
            <div class="backtest-stats">
              <div class="stat-grid">
                <div class="stat-cell">
                  <div class="stat-number text-primary">{{ backtestStats.total_results }}</div>
                  <div class="stat-label">回测结果</div>
                </div>
                <div class="stat-cell">
                  <div class="stat-number text-warning">{{ backtestStats.running_tasks }}</div>
                  <div class="stat-label">运行中</div>
                </div>
                <div class="stat-cell">
                  <div class="stat-number text-success">{{ formatPercent(backtestStats.success_rate) }}</div>
                  <div class="stat-label">成功率</div>
                </div>
                <div class="stat-cell">
                  <div class="stat-number text-info">{{ formatNumber(backtestStats.avg_sharpe, 3) }}</div>
                  <div class="stat-label">平均夏普</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 快速操作 -->
          <el-card class="quick-actions-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Lightning /></el-icon>
                <span>快速操作</span>
              </div>
            </template>
            <div class="quick-actions">
              <el-button-group class="action-group">
                <el-button type="primary" @click="navigateTo('/qlib-data-browser')">
                  <el-icon><DataBoard /></el-icon>
                  数据浏览
                </el-button>
                <el-button type="success" @click="navigateTo('/qlib-factor-workshop')">
                  <el-icon><MagicStick /></el-icon>
                  因子开发
                </el-button>
              </el-button-group>
              <el-button-group class="action-group">
                <el-button type="warning" @click="navigateTo('/qlib-model-lab')">
                  <el-icon><Cpu /></el-icon>
                  模型实验
                </el-button>
                <el-button type="info" @click="navigateTo('/qlib-backtest-engine')">
                  <el-icon><TrendCharts /></el-icon>
                  回测引擎
                </el-button>
              </el-button-group>
              <el-button-group class="action-group">
                <el-button @click="navigateTo('/qlib-strategy-builder')">
                  <el-icon><Setting /></el-icon>
                  策略构建
                </el-button>
                <el-button @click="checkSystemHealth">
                  <el-icon><Monitor /></el-icon>
                  系统检查
                </el-button>
              </el-button-group>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 底部性能图表区域 -->
      <el-row :gutter="24" class="charts-row">
        <el-col :span="12">
          <el-card class="performance-chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><DataLine /></el-icon>
                <span>系统性能趋势</span>
              </div>
            </template>
            <div class="chart-placeholder">
              <div class="placeholder-content">
                <el-icon size="48"><DataLine /></el-icon>
                <p>性能监控图表</p>
                <small>显示CPU、内存、磁盘使用情况</small>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="resource-chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><PieChart /></el-icon>
                <span>资源使用分布</span>
              </div>
            </template>
            <div class="chart-placeholder">
              <div class="placeholder-content">
                <el-icon size="48"><PieChart /></el-icon>
                <p>资源分配图表</p>
                <small>显示任务类型资源占用比例</small>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  DataBoard,
  Refresh,
  MagicStick,
  Cpu,
  Loading,
  CircleCheck,
  TrendCharts,
  Lightning,
  Setting,
  DataLine,
  PieChart
} from '@element-plus/icons-vue'

// Store imports
import { useQlibDataStore } from '@/stores/qlib-data'
import { useQlibFactorsStore } from '@/stores/qlib-factors'
import { useQlibModelsStore } from '@/stores/qlib-models'
import { useQlibBacktestStore } from '@/stores/qlib-backtest'
import { useQlibConfigStore } from '@/stores/qlib-config'

const router = useRouter()

// Store instances
const qlibDataStore = useQlibDataStore()
const qlibFactorsStore = useQlibFactorsStore()
const qlibModelsStore = useQlibModelsStore()
const qlibBacktestStore = useQlibBacktestStore()
const qlibConfigStore = useQlibConfigStore()

// 响应式数据
const loading = ref(false)

// 计算属性
const systemStatus = computed(() => qlibConfigStore.systemStatus)
const systemHealth = computed(() => qlibConfigStore.systemHealth)
const dataStats = computed(() => qlibDataStore.dataStats)
const factorStats = computed(() => qlibFactorsStore.factorStats)
const modelStats = computed(() => qlibModelsStore.modelStats)
const backtestStats = computed(() => qlibBacktestStore.backtestStats)

const systemHealthClass = computed(() => ({
  'text-success': systemHealth.value === 'healthy',
  'text-warning': systemHealth.value === 'warning',
  'text-danger': systemHealth.value === 'error'
}))

const systemHealthText = computed(() => {
  switch (systemHealth.value) {
    case 'healthy': return '运行正常'
    case 'warning': return '存在警告'
    case 'error': return '系统异常'
    default: return '状态未知'
  }
})

const activeTasks = computed(() => {
  const tasks = []
  
  // 添加训练任务
  qlibModelsStore.activeTrainingTasks.forEach(task => {
    tasks.push({
      id: task.task_id,
      name: task.name || '模型训练',
      type: '模型训练',
      progress: task.progress
    })
  })
  
  // 添加回测任务
  qlibBacktestStore.activeBacktestTasks.forEach(task => {
    tasks.push({
      id: task.task_id,
      name: task.name,
      type: '策略回测',
      progress: task.progress
    })
  })
  
  return tasks.slice(0, 10) // 最多显示10个任务
})

// 方法
const formatNumber = (num: number, decimals = 0) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return num.toLocaleString('zh-CN', { 
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals 
  })
}

const formatPercent = (num: number) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return `${num.toFixed(1)}%`
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatTime = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'connected':
    case 'active':
      return 'text-success'
    case 'disconnected':
    case 'inactive':
      return 'text-warning'
    case 'error':
      return 'text-danger'
    default:
      return 'text-info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'connected': return '已连接'
    case 'disconnected': return '断开连接'
    case 'active': return '激活'
    case 'inactive': return '未激活'
    case 'error': return '错误'
    default: return '未知'
  }
}

const getTaskColor = (type: string) => {
  switch (type) {
    case '模型训练': return '#409eff'
    case '策略回测': return '#67c23a'
    case '因子分析': return '#e6a23c'
    default: return '#909399'
  }
}

const navigateTo = (path: string) => {
  router.push(path)
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      qlibDataStore.updateDataStats(),
      qlibFactorsStore.loadFactorLibrary(),
      qlibModelsStore.loadModelRegistry(),
      qlibBacktestStore.loadBacktestResults()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const checkSystemHealth = async () => {
  loading.value = true
  try {
    await qlibConfigStore.checkSystemHealth()
    ElMessage.success('系统健康检查完成')
  } catch (error) {
    console.error('系统健康检查失败:', error)
    ElMessage.error('系统健康检查失败')
  } finally {
    loading.value = false
  }
}

const viewAllTasks = () => {
  router.push('/training-management')
}

// 生命周期
onMounted(async () => {
  // 初始化加载所有数据
  await refreshData()
  await qlibConfigStore.loadCurrentConfig()
})
</script>

<style scoped lang="scss">
.qlib-dashboard {
  height: 100vh;
  overflow-y: auto;
  background: #f5f7fa;
  
  .dashboard-header {
    padding: 20px 24px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    
    .system-status-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .status-item {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .status-icon {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          
          &.healthy {
            background: #f0f9ff;
            color: #67c23a;
          }
          
          &.warning {
            background: #fdf6ec;
            color: #e6a23c;
          }
          
          &.error {
            background: #fef0f0;
            color: #f56c6c;
          }
        }
        
        .status-info {
          h3 {
            margin: 0 0 4px 0;
            font-size: 18px;
            font-weight: 500;
          }
          
          p {
            margin: 0 0 4px 0;
            font-size: 14px;
            font-weight: 600;
          }
          
          small {
            color: #909399;
            font-size: 12px;
          }
        }
      }
      
      .status-metrics {
        display: flex;
        gap: 24px;
        
        .metric {
          text-align: center;
          
          .metric-value {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
          }
          
          .metric-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .dashboard-content {
    padding: 24px;
    
    .el-card {
      margin-bottom: 20px;
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
        
        .el-button {
          margin-left: auto;
        }
      }
    }
    
    .data-stats {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      .stat-item {
        text-align: center;
        
        .stat-number {
          font-size: 24px;
          font-weight: 600;
          color: #409eff;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 12px;
          color: #909399;
        }
      }
    }
    
    .factor-stats {
      .progress-item {
        margin-bottom: 20px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .progress-label {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;
          
          .progress-value {
            font-weight: 600;
            color: #409eff;
          }
        }
      }
    }
    
    .model-stats {
      .stat-row {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        
        .stat-item {
          text-align: center;
          
          .stat-number {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
            
            &.text-success { color: #67c23a; }
            &.text-warning { color: #e6a23c; }
            &.text-danger { color: #f56c6c; }
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
      
      .performance-metric {
        text-align: center;
        padding-top: 16px;
        border-top: 1px solid #f0f2f5;
        
        .metric-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 8px;
        }
        
        .metric-value.large {
          font-size: 32px;
          font-weight: 600;
          color: #409eff;
        }
      }
    }
    
    .active-tasks {
      .no-tasks {
        text-align: center;
        padding: 40px 0;
        color: #909399;
        
        .el-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }
        
        p {
          margin: 0;
          font-size: 14px;
        }
      }
      
      .tasks-list {
        .task-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 0;
          border-bottom: 1px solid #f0f2f5;
          
          &:last-child {
            border-bottom: none;
          }
          
          .task-info {
            flex: 1;
            
            .task-name {
              font-size: 14px;
              font-weight: 500;
              margin-bottom: 4px;
            }
            
            .task-type {
              font-size: 12px;
              color: #909399;
            }
          }
          
          .task-progress {
            display: flex;
            align-items: center;
            gap: 8px;
            width: 120px;
            
            .el-progress {
              flex: 1;
            }
            
            .progress-text {
              font-size: 12px;
              color: #909399;
              min-width: 36px;
              text-align: right;
            }
          }
        }
      }
    }
    
    .backtest-stats {
      .stat-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        
        .stat-cell {
          text-align: center;
          padding: 12px;
          background: #fafbfc;
          border-radius: 8px;
          
          .stat-number {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
            
            &.text-primary { color: #409eff; }
            &.text-success { color: #67c23a; }
            &.text-warning { color: #e6a23c; }
            &.text-info { color: #909399; }
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
    
    .quick-actions {
      .action-group {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .el-button {
          flex: 1;
          margin: 0 !important;
          
          &:first-child {
            border-top-right-radius: 0;
            border-bottom-right-radius: 0;
          }
          
          &:last-child {
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
          }
        }
      }
    }
    
    .charts-row {
      margin-top: 24px;
    }
    
    .chart-placeholder {
      height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fafbfc;
      border-radius: 8px;
      
      .placeholder-content {
        text-align: center;
        color: #909399;
        
        .el-icon {
          margin-bottom: 12px;
        }
        
        p {
          margin: 0 0 4px 0;
          font-size: 16px;
        }
        
        small {
          font-size: 12px;
        }
      }
    }
  }
}

// 通用样式类
.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.text-info { color: #909399; }
.text-primary { color: #409eff; }
</style>