<template>
  <div class="training-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><List /></el-icon>
          训练管理中心
        </h1>
        <p class="page-subtitle">管理和监控您的所有模型训练任务</p>
      </div>
      
      <div class="header-actions">
        <el-button @click="refreshTasks">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="createNewTraining">
          <el-icon><Plus /></el-icon>
          新建训练
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-icon running">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ runningTasks }}</div>
                <div class="stat-label">正在训练</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-icon completed">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ completedTasks }}</div>
                <div class="stat-label">训练完成</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-icon failed">
                <el-icon><CircleCloseFilled /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ failedTasks }}</div>
                <div class="stat-label">训练失败</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-icon total">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ totalTasks }}</div>
                <div class="stat-label">总任务数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-section">
      <div class="filter-content">
        <div class="filter-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索训练任务..."
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 150px">
            <el-option label="全部状态" value="" />
            <el-option label="正在训练" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="已失败" value="failed" />
            <el-option label="已暂停" value="paused" />
          </el-select>
          
          <el-select v-model="modelTypeFilter" placeholder="模型类型" style="width: 150px">
            <el-option label="全部模型" value="" />
            <el-option label="LightGBM" value="LightGBM" />
            <el-option label="XGBoost" value="XGBoost" />
            <el-option label="CatBoost" value="CatBoost" />
            <el-option label="LSTM" value="LSTM" />
            <el-option label="Transformer" value="Transformer" />
          </el-select>
          
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </div>
        
        <div class="filter-right">
          <el-button-group>
            <el-button
              :type="viewMode === 'table' ? 'primary' : ''"
              @click="viewMode = 'table'"
            >
              <el-icon><Grid /></el-icon>
              列表视图
            </el-button>
            <el-button
              :type="viewMode === 'card' ? 'primary' : ''"
              @click="viewMode = 'card'"
            >
              <el-icon><Postcard /></el-icon>
              卡片视图
            </el-button>
          </el-button-group>
          
          <el-dropdown @command="handleBatchAction" trigger="click">
            <el-button>
              批量操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="delete" :disabled="selectedTasks.length === 0">
                  批量删除
                </el-dropdown-item>
                <el-dropdown-item command="stop" :disabled="selectedTasks.length === 0">
                  批量停止
                </el-dropdown-item>
                <el-dropdown-item command="export" :disabled="selectedTasks.length === 0">
                  导出结果
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-card>

    <!-- 任务列表 - 表格视图 -->
    <el-card v-if="viewMode === 'table'" class="table-container">
      <el-table
        :data="filteredTasks"
        style="width: 100%"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <div class="task-name">
              <span class="name-text" @click="viewTaskDetail(row)" style="cursor: pointer; color: #409eff;">
                {{ row.name }}
              </span>
              <el-tag v-if="row.isTemplate" size="small" type="info">模板</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="modelType" label="模型类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getModelTagType(row.modelType)" size="small">
              {{ row.modelType }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="getProgressStatus(row.status)"
              :show-text="false"
              :stroke-width="6"
            />
            <span class="progress-text">{{ row.progress }}%</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="metrics" label="最佳性能" width="120">
          <template #default="{ row }">
            <div v-if="row.bestMetrics" class="metrics-display">
              <span class="metric-value">{{ row.bestMetrics.accuracy.toFixed(2) }}%</span>
              <span class="metric-label">准确率</span>
            </div>
            <span v-else class="no-metrics">--</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="用时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                size="small" 
                @click="viewTaskDetail(row)"
              >
                详情
              </el-button>
              
              <el-button 
                v-if="row.status === 'running'"
                size="small" 
                type="warning"
                @click="pauseTask(row)"
              >
                暂停
              </el-button>
              
              <el-button 
                v-if="row.status === 'paused'"
                size="small" 
                type="success"
                @click="resumeTask(row)"
              >
                继续
              </el-button>
              
              <el-button 
                v-if="['running', 'paused'].includes(row.status)"
                size="small" 
                type="danger"
                @click="stopTask(row)"
              >
                停止
              </el-button>
              
              <el-dropdown 
                @command="(command) => handleTaskAction(command, row)" 
                trigger="click"
                size="small"
              >
                <el-button size="small">
                  更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="clone" :disabled="row.status === 'running'">
                      克隆训练
                    </el-dropdown-item>
                    <el-dropdown-item command="template" :disabled="row.status !== 'completed'">
                      存为模板
                    </el-dropdown-item>
                    <el-dropdown-item command="export" :disabled="!row.bestMetrics">
                      导出模型
                    </el-dropdown-item>
                    <el-dropdown-item command="compare">
                      添加到比较
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalItems"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 任务列表 - 卡片视图 -->
    <div v-if="viewMode === 'card'" class="card-container" v-loading="loading">
      <div class="task-grid">
        <div v-for="task in filteredTasks" :key="task.id" class="task-card">
          <el-card @click="viewTaskDetail(task)" class="clickable-card">
            <template #header>
              <div class="card-header">
                <div class="card-title">
                  <span class="task-name">{{ task.name }}</span>
                  <el-tag v-if="task.isTemplate" size="small" type="info">模板</el-tag>
                </div>
                <el-tag :type="getStatusTagType(task.status)" size="small">
                  {{ getStatusText(task.status) }}
                </el-tag>
              </div>
            </template>

            <div class="card-content">
              <div class="model-info">
                <el-icon><Cpu /></el-icon>
                <span>{{ task.modelType }}</span>
              </div>
              
              <div class="progress-section">
                <div class="progress-header">
                  <span>训练进度</span>
                  <span>{{ task.progress }}%</span>
                </div>
                <el-progress 
                  :percentage="task.progress"
                  :status="getProgressStatus(task.status)"
                  :stroke-width="8"
                  :show-text="false"
                />
              </div>
              
              <div v-if="task.bestMetrics" class="metrics-section">
                <div class="metric-item">
                  <span class="metric-label">准确率</span>
                  <span class="metric-value">{{ task.bestMetrics.accuracy.toFixed(2) }}%</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">F1分数</span>
                  <span class="metric-value">{{ (task.bestMetrics.f1Score || 0).toFixed(3) }}</span>
                </div>
              </div>
              
              <div class="time-info">
                <div class="time-item">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatDuration(task.duration) }}</span>
                </div>
                <div class="time-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDateTime(task.createdAt) }}</span>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="card-actions" @click.stop>
                <el-button 
                  v-if="task.status === 'running'"
                  size="small" 
                  type="warning"
                  @click="pauseTask(task)"
                >
                  <el-icon><VideoPause /></el-icon>
                  暂停
                </el-button>
                
                <el-button 
                  v-if="task.status === 'paused'"
                  size="small" 
                  type="success"
                  @click="resumeTask(task)"
                >
                  <el-icon><VideoPlay /></el-icon>
                  继续
                </el-button>
                
                <el-button 
                  v-if="['running', 'paused'].includes(task.status)"
                  size="small" 
                  type="danger"
                  @click="stopTask(task)"
                >
                  <el-icon><Close /></el-icon>
                  停止
                </el-button>
                
                <el-button size="small" @click="cloneTask(task)">
                  <el-icon><CopyDocument /></el-icon>
                  克隆
                </el-button>
                
                <el-dropdown 
                  @command="(command) => handleTaskAction(command, task)" 
                  trigger="click"
                  size="small"
                >
                  <el-button size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="template">存为模板</el-dropdown-item>
                      <el-dropdown-item command="export">导出模型</el-dropdown-item>
                      <el-dropdown-item command="compare">添加到比较</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-card>
        </div>
      </div>
      
      <!-- 卡片视图分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[9, 18, 36]"
          :total="totalItems"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 模型性能排行榜 -->
    <ModelRanking @model-selected="handleModelSelected" />

    <!-- 模型对比分析 -->
    <ModelComparison 
      v-if="comparisonTasks.length > 0"
      :tasks="comparisonTasks"
      @remove-task="removeFromComparison"
    />

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showTaskDetail" :title="`训练任务详情 - ${selectedTask?.name}`" width="80%">
      <div v-if="selectedTask" class="task-detail">
        <!-- 任务详情内容 -->
        <TrainingTaskDetail :task="selectedTask" @task-updated="handleTaskUpdated" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  List, Refresh, Plus, Timer, SuccessFilled, CircleCloseFilled,
  DataAnalysis, Search, Grid, Postcard, ArrowDown, Cpu, Clock,
  Calendar, VideoPause, VideoPlay, Close, CopyDocument, MoreFilled
} from '@element-plus/icons-vue'

// 导入组件
import ModelRanking from '@/components/training/ModelRanking.vue'
import ModelComparison from '@/components/training/ModelComparison.vue'
import TrainingTaskDetail from '@/components/training/TrainingTaskDetail.vue'

// 导入类型
import type { TrainingTask } from '@/types/training'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const viewMode = ref<'table' | 'card'>('table')
const currentPage = ref(1)
const pageSize = ref(20)
const totalItems = ref(0)
const selectedTasks = ref<TrainingTask[]>([])
const comparisonTasks = ref<TrainingTask[]>([])

// 筛选条件
const searchQuery = ref('')
const statusFilter = ref('')
const modelTypeFilter = ref('')
const dateRange = ref<[string, string] | null>(null)

// 对话框状态
const showTaskDetail = ref(false)
const selectedTask = ref<TrainingTask | null>(null)

// 模拟训练任务数据
const tasks = ref<TrainingTask[]>([
  {
    id: '1',
    name: 'LightGBM_沪深300_因子模型',
    config: {
      name: 'LightGBM_沪深300_因子模型',
      dataConfig: {
        stockPool: 'HS300',
        dateRange: ['2020-01-01', '2023-12-31'],
        frequency: 'daily'
      },
      modelConfig: {
        type: 'LightGBM',
        params: {}
      },
      trainingParams: {
        epochs: 100,
        batchSize: 32,
        learningRate: 0.05,
        validationSplit: 0.2,
        earlyStoppingPatience: 10,
        saveBestModel: true
      }
    },
    factors: [],
    status: 'completed',
    progress: 100,
    createdAt: new Date('2024-01-15'),
    modelType: 'LightGBM',
    duration: 1800, // 30分钟
    bestMetrics: {
      accuracy: 87.5,
      f1Score: 0.84
    }
  },
  {
    id: '2',
    name: 'LSTM_时序预测模型',
    config: {
      name: 'LSTM_时序预测模型',
      dataConfig: {
        stockPool: 'ZZ500',
        dateRange: ['2019-01-01', '2023-12-31'],
        frequency: 'daily'
      },
      modelConfig: {
        type: 'LSTM',
        params: {}
      },
      trainingParams: {
        epochs: 200,
        batchSize: 64,
        learningRate: 0.001,
        validationSplit: 0.2,
        earlyStoppingPatience: 15,
        saveBestModel: true
      }
    },
    factors: [],
    status: 'running',
    progress: 65,
    createdAt: new Date('2024-01-20'),
    modelType: 'LSTM',
    duration: 7200 // 2小时
  },
  {
    id: '3',
    name: 'XGBoost_多因子策略',
    config: {
      name: 'XGBoost_多因子策略',
      dataConfig: {
        stockPool: 'ALL',
        dateRange: ['2018-01-01', '2023-12-31'],
        frequency: 'daily'
      },
      modelConfig: {
        type: 'XGBoost',
        params: {}
      },
      trainingParams: {
        epochs: 150,
        batchSize: 128,
        learningRate: 0.03,
        validationSplit: 0.25,
        earlyStoppingPatience: 20,
        saveBestModel: true
      }
    },
    factors: [],
    status: 'failed',
    progress: 25,
    createdAt: new Date('2024-01-18'),
    modelType: 'XGBoost',
    duration: 900 // 15分钟
  }
])

// 计算属性
const runningTasks = computed(() => tasks.value.filter(t => t.status === 'running').length)
const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed').length)
const totalTasks = computed(() => tasks.value.length)

const filteredTasks = computed(() => {
  let filtered = tasks.value

  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(task =>
      task.name.toLowerCase().includes(query) ||
      task.modelType.toLowerCase().includes(query)
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter(task => task.status === statusFilter.value)
  }

  // 模型类型过滤
  if (modelTypeFilter.value) {
    filtered = filtered.filter(task => task.modelType === modelTypeFilter.value)
  }

  // 日期范围过滤
  if (dateRange.value) {
    const [startDate, endDate] = dateRange.value
    filtered = filtered.filter(task => {
      const taskDate = task.createdAt.toISOString().split('T')[0]
      return taskDate >= startDate && taskDate <= endDate
    })
  }

  totalItems.value = filtered.length
  
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filtered.slice(start, end)
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
    case 'running': return '训练中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'paused': return '暂停'
    default: return '未知'
  }
}

const getProgressStatus = (status: string) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return undefined
}

const getModelTagType = (modelType: string) => {
  switch (modelType) {
    case 'LightGBM': return 'success'
    case 'XGBoost': return 'warning'
    case 'LSTM': return 'info'
    case 'Transformer': return 'danger'
    default: return 'info'
  }
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}时${minutes}分`
  }
  return `${minutes}分`
}

const formatDateTime = (date: Date) => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleSelectionChange = (selection: TrainingTask[]) => {
  selectedTasks.value = selection
}

const handleBatchAction = async (command: string) => {
  switch (command) {
    case 'delete':
      await handleBatchDelete()
      break
    case 'stop':
      await handleBatchStop()
      break
    case 'export':
      handleBatchExport()
      break
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`,
      '批量删除',
      { type: 'warning' }
    )
    
    ElMessage.success(`已删除 ${selectedTasks.value.length} 个任务`)
    selectedTasks.value = []
    refreshTasks()
  } catch {
    // 用户取消
  }
}

const handleBatchStop = async () => {
  const runningTasks = selectedTasks.value.filter(t => t.status === 'running')
  if (runningTasks.length === 0) {
    ElMessage.warning('没有正在运行的任务')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要停止选中的 ${runningTasks.length} 个正在运行的任务吗？`,
      '批量停止',
      { type: 'warning' }
    )
    
    ElMessage.success(`已停止 ${runningTasks.length} 个任务`)
    refreshTasks()
  } catch {
    // 用户取消
  }
}

const handleBatchExport = () => {
  const completedTasks = selectedTasks.value.filter(t => t.status === 'completed')
  if (completedTasks.length === 0) {
    ElMessage.warning('没有已完成的任务可以导出')
    return
  }
  
  ElMessage.success(`开始导出 ${completedTasks.length} 个模型`)
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const viewTaskDetail = (task: TrainingTask) => {
  selectedTask.value = task
  showTaskDetail.value = true
}

const pauseTask = async (task: TrainingTask) => {
  try {
    await ElMessageBox.confirm('确定要暂停这个训练任务吗？', '确认暂停', {
      type: 'warning'
    })
    
    task.status = 'paused'
    ElMessage.success('任务已暂停')
  } catch {
    // 用户取消
  }
}

const resumeTask = (task: TrainingTask) => {
  task.status = 'running'
  ElMessage.success('任务已恢复')
}

const stopTask = async (task: TrainingTask) => {
  try {
    await ElMessageBox.confirm(
      '确定要停止这个训练任务吗？训练进度将会丢失！',
      '确认停止',
      { type: 'warning' }
    )
    
    task.status = 'failed'
    ElMessage.success('任务已停止')
  } catch {
    // 用户取消
  }
}

const cloneTask = (task: TrainingTask) => {
  router.push({
    path: '/training',
    query: {
      template: task.id,
      clone: 'true'
    }
  })
}

const handleTaskAction = async (command: string, task: TrainingTask) => {
  switch (command) {
    case 'clone':
      cloneTask(task)
      break
    case 'template':
      await saveAsTemplate(task)
      break
    case 'export':
      exportModel(task)
      break
    case 'compare':
      addToComparison(task)
      break
    case 'delete':
      await deleteTask(task)
      break
  }
}

const saveAsTemplate = async (task: TrainingTask) => {
  try {
    await ElMessageBox.prompt('请输入模板名称', '保存模板', {
      inputValue: `${task.name}_模板`
    })
    
    ElMessage.success('模板保存成功')
  } catch {
    // 用户取消
  }
}

const exportModel = (task: TrainingTask) => {
  if (!task.bestMetrics) {
    ElMessage.warning('该任务还没有可导出的模型')
    return
  }
  
  ElMessage.success('模型导出已开始')
}

const addToComparison = (task: TrainingTask) => {
  if (comparisonTasks.value.find(t => t.id === task.id)) {
    ElMessage.warning('该任务已在比较列表中')
    return
  }
  
  if (comparisonTasks.value.length >= 5) {
    ElMessage.warning('最多只能比较5个任务')
    return
  }
  
  comparisonTasks.value.push(task)
  ElMessage.success(`已添加到比较列表 (${comparisonTasks.value.length}/5)`)
}

const removeFromComparison = (taskId: string) => {
  const index = comparisonTasks.value.findIndex(t => t.id === taskId)
  if (index > -1) {
    comparisonTasks.value.splice(index, 1)
  }
}

const deleteTask = async (task: TrainingTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除训练任务"${task.name}"吗？`,
      '删除任务',
      { type: 'warning' }
    )
    
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index > -1) {
      tasks.value.splice(index, 1)
    }
    
    ElMessage.success('任务已删除')
  } catch {
    // 用户取消
  }
}

const refreshTasks = () => {
  loading.value = true
  
  // 模拟API调用
  setTimeout(() => {
    loading.value = false
    ElMessage.success('刷新完成')
  }, 1000)
}

const createNewTraining = () => {
  router.push('/training')
}

const handleModelSelected = (model: any) => {
  // 处理从排行榜选择模型
  viewTaskDetail(model)
}

const handleTaskUpdated = (updatedTask: TrainingTask) => {
  const index = tasks.value.findIndex(t => t.id === updatedTask.id)
  if (index > -1) {
    tasks.value[index] = updatedTask
  }
}

// 生命周期
onMounted(() => {
  refreshTasks()
})
</script>

<style scoped>
.training-management {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-content .page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: #606266;
  font-size: 16px;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-overview {
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border: 1px solid #d4e4fd;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}

.stat-icon.running {
  background: linear-gradient(135deg, #e6a23c, #f56c6c);
}

.stat-icon.completed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.failed {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.filter-section {
  margin-bottom: 24px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-left {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-container {
  margin-bottom: 24px;
}

.task-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  font-weight: 500;
}

.progress-text {
  margin-left: 8px;
  font-size: 12px;
  color: #606266;
}

.metrics-display {
  text-align: center;
}

.metric-value {
  display: block;
  font-weight: 600;
  color: #67c23a;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.no-metrics {
  color: #c0c4cc;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 卡片视图样式 */
.card-container {
  margin-bottom: 24px;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.task-card {
  height: 100%;
}

.clickable-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.clickable-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.task-name {
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
}

.metrics-section {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-item {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-weight: 600;
  color: #67c23a;
}

.time-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #909399;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.task-detail {
  min-height: 500px;
}

@media (max-width: 768px) {
  .training-management {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .filter-content {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .filter-left,
  .filter-right {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .task-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .card-actions {
    justify-content: center;
  }
  
  .time-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>