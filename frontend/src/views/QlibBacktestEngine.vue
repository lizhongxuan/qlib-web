<template>
  <div class="qlib-backtest-engine">
    <div class="toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">
          <el-icon><TrendCharts /></el-icon>
          Qlib回测引擎
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/qlib-dashboard' }">Qlib中心</el-breadcrumb-item>
          <el-breadcrumb-item>回测引擎</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button type="primary" @click="createBacktest">
            <el-icon><Plus /></el-icon>
            新建回测
          </el-button>
          <el-button @click="refreshResults" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-button-group>
      </div>
    </div>

    <div class="main-content">
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="回测结果" name="results">
          <el-card shadow="never">
            <div class="results-stats">
              <div class="stat-card">
                <div class="stat-value">{{ backtestStats.total_results }}</div>
                <div class="stat-label">回测结果</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ backtestStats.running_tasks }}</div>
                <div class="stat-label">运行中</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ formatPercent(backtestStats.success_rate) }}</div>
                <div class="stat-label">成功率</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ formatNumber(backtestStats.avg_sharpe, 3) }}</div>
                <div class="stat-label">平均夏普</div>
              </div>
            </div>
            
            <el-table :data="backtestResults" :loading="loading" stripe>
              <el-table-column prop="name" label="回测名称" width="200" />
              <el-table-column prop="meta_info.model_name" label="模型" width="150" />
              <el-table-column prop="return_metrics.annual_return" label="年化收益" width="120">
                <template #default="scope">
                  {{ formatPercent(scope.row.return_metrics.annual_return * 100) }}
                </template>
              </el-table-column>
              <el-table-column prop="risk_metrics.sharpe_ratio" label="夏普比率" width="120">
                <template #default="scope">
                  {{ formatNumber(scope.row.risk_metrics.sharpe_ratio, 3) }}
                </template>
              </el-table-column>
              <el-table-column prop="risk_metrics.max_drawdown" label="最大回撤" width="120">
                <template #default="scope">
                  {{ formatPercent(scope.row.risk_metrics.max_drawdown * 100) }}
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="150" />
              <el-table-column label="操作" fixed="right">
                <template #default="scope">
                  <el-button-group size="small">
                    <el-button type="primary" link @click="viewResult(scope.row)">查看</el-button>
                    <el-button type="success" link @click="compareResult(scope.row)">对比</el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
        
        <el-tab-pane label="活跃任务" name="tasks">
          <el-card shadow="never">
            <div v-if="activeBacktestTasks.length === 0" class="no-tasks">
              <el-icon size="48"><CircleCheck /></el-icon>
              <p>暂无活跃回测任务</p>
            </div>
            <div v-else class="tasks-list">
              <div v-for="task in activeBacktestTasks" :key="task.task_id" class="task-item">
                <div class="task-header">
                  <h4>{{ task.name }}</h4>
                  <el-tag :type="getTaskStatusType(task.status)">{{ task.status }}</el-tag>
                </div>
                <div class="task-progress">
                  <el-progress :percentage="task.progress" :stroke-width="8" />
                  <span class="progress-text">{{ task.progress }}%</span>
                </div>
                <div v-if="task.real_time_metrics" class="task-metrics">
                  <div class="metric">
                    <span class="label">当前收益:</span>
                    <span class="value">{{ formatPercent(task.real_time_metrics.current_return * 100) }}</span>
                  </div>
                  <div class="metric">
                    <span class="label">夏普比率:</span>
                    <span class="value">{{ formatNumber(task.real_time_metrics.sharpe_ratio, 3) }}</span>
                  </div>
                  <div class="metric">
                    <span class="label">最大回撤:</span>
                    <span class="value">{{ formatPercent(task.real_time_metrics.max_drawdown * 100) }}</span>
                  </div>
                </div>
                <div class="task-actions">
                  <el-button size="small" @click="cancelTask(task)" :disabled="task.status !== 'running'">
                    <el-icon><Close /></el-icon>
                    取消
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Plus, Refresh, CircleCheck, Close } from '@element-plus/icons-vue'
import { useQlibBacktestStore } from '@/stores/qlib-backtest'

const qlibBacktestStore = useQlibBacktestStore()
const loading = ref(false)
const activeTab = ref('results')

const backtestResults = computed(() => qlibBacktestStore.backtestResults)
const backtestStats = computed(() => qlibBacktestStore.backtestStats)
const activeBacktestTasks = computed(() => qlibBacktestStore.activeBacktestTasks)

const formatNumber = (num: number, decimals = 0) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return num.toLocaleString('zh-CN', { maximumFractionDigits: decimals })
}

const formatPercent = (num: number) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return `${num.toFixed(1)}%`
}

const getTaskStatusType = (status: string) => {
  const types: Record<string, string> = {
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'pending': 'info'
  }
  return types[status] || 'info'
}

const createBacktest = () => {
  ElMessage.info('创建回测功能')
}

const refreshResults = async () => {
  loading.value = true
  try {
    await qlibBacktestStore.loadBacktestResults()
    ElMessage.success('回测结果刷新成功')
  } finally {
    loading.value = false
  }
}

const viewResult = (result: any) => {
  ElMessage.info(`查看回测结果: ${result.name}`)
}

const compareResult = (result: any) => {
  ElMessage.info(`对比回测结果: ${result.name}`)
}

const cancelTask = async (task: any) => {
  try {
    await qlibBacktestStore.cancelBacktest(task.task_id)
    ElMessage.success('任务已取消')
  } catch (error) {
    ElMessage.error('取消任务失败')
  }
}

onMounted(() => {
  refreshResults()
})
</script>

<style scoped lang="scss">
.qlib-backtest-engine {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  
  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    
    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 500;
    }
  }
  
  .main-content {
    flex: 1;
    padding: 24px;
    
    .results-stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
      
      .stat-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #409eff;
        }
        
        .stat-label {
          font-size: 12px;
          color: #909399;
        }
      }
    }
    
    .no-tasks {
      text-align: center;
      color: #909399;
      padding: 80px 0;
      
      .el-icon {
        margin-bottom: 16px;
      }
    }
    
    .tasks-list {
      .task-item {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid #e4e7ed;
        
        .task-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
          
          h4 {
            margin: 0;
            color: #409eff;
          }
        }
        
        .task-progress {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          
          .el-progress {
            flex: 1;
          }
          
          .progress-text {
            font-size: 14px;
            font-weight: 500;
            min-width: 40px;
          }
        }
        
        .task-metrics {
          display: flex;
          gap: 24px;
          margin-bottom: 16px;
          
          .metric {
            .label {
              color: #909399;
              font-size: 12px;
            }
            
            .value {
              margin-left: 4px;
              font-weight: 500;
              color: #409eff;
            }
          }
        }
        
        .task-actions {
          text-align: right;
        }
      }
    }
  }
}
</style>