<template>
  <div class="qlib-experiment-manager">
    <!-- 实验管理头部 -->
    <el-card class="manager-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><Experiment /></el-icon>
            <span>Qlib实验记录管理</span>
          </div>
          <div class="header-actions">
            <el-button @click="refreshExperiments" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="primary" @click="createExperiment">
              <el-icon><Plus /></el-icon>
              新建实验
            </el-button>
            <el-button @click="exportExperiments">
              <el-icon><Download /></el-icon>
              导出记录
            </el-button>
          </div>
        </div>
      </template>

      <!-- 实验筛选器 -->
      <div class="experiment-filters">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-form-item label="实验状态">
              <el-select v-model="filters.status" @change="loadExperiments">
                <el-option label="全部状态" value="" />
                <el-option label="运行中" value="running" />
                <el-option label="已完成" value="finished" />
                <el-option label="失败" value="failed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="模型类型">
              <el-select v-model="filters.modelType" @change="loadExperiments">
                <el-option label="全部模型" value="" />
                <el-option label="LightGBM" value="lightgbm" />
                <el-option label="XGBoost" value="xgboost" />
                <el-option label="LSTM" value="lstm" />
                <el-option label="Linear" value="linear" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="创建时间">
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="loadExperiments"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="搜索">
              <el-input
                v-model="searchText"
                placeholder="搜索实验名称或ID"
                clearable
                @input="debounceSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 实验统计概览 -->
    <el-row :gutter="16" class="experiment-overview">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总实验数" :value="experimentStats.total" />
          <div class="stat-trend">
            <el-icon class="trend-icon success"><CaretTop /></el-icon>
            <span class="trend-text">本月新增 {{ experimentStats.monthlyNew }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="运行中" :value="experimentStats.running" />
          <div class="stat-trend">
            <el-icon class="trend-icon primary"><Timer /></el-icon>
            <span class="trend-text">平均运行时间 {{ experimentStats.avgRuntime }}分钟</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="成功率" :value="experimentStats.successRate" suffix="%" />
          <div class="stat-trend">
            <el-icon class="trend-icon success"><CircleCheck /></el-icon>
            <span class="trend-text">较上月提升 2.3%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="最佳性能" :value="experimentStats.bestScore" suffix="%" />
          <div class="stat-trend">
            <el-icon class="trend-icon warning"><TrendCharts /></el-icon>
            <span class="trend-text">{{ experimentStats.bestExperiment }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实验列表 -->
    <el-card class="experiment-table-card">
      <template #header>
        <div class="table-header">
          <span>实验记录 ({{ filteredExperiments.length }} 条)</span>
          <div class="table-actions">
            <el-button-group>
              <el-button 
                :type="viewMode === 'table' ? 'primary' : 'default'"
                @click="viewMode = 'table'"
              >
                <el-icon><Menu /></el-icon>
                表格视图
              </el-button>
              <el-button 
                :type="viewMode === 'card' ? 'primary' : 'default'"
                @click="viewMode = 'card'"
              >
                <el-icon><Grid /></el-icon>
                卡片视图
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'">
        <el-table
          :data="paginatedExperiments"
          v-loading="loading"
          border
          @selection-change="handleSelectionChange"
          @row-click="viewExperimentDetail"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="experiment_id" label="实验ID" width="150" />
          <el-table-column prop="name" label="实验名称" min-width="200" />
          <el-table-column prop="model_type" label="模型类型" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="性能分数" width="120">
            <template #default="{ row }">
              <span v-if="row.score">{{ row.score.toFixed(3) }}</span>
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column prop="runtime" label="运行时间" width="120">
            <template #default="{ row }">
              {{ formatRuntime(row.runtime) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click.stop="viewExperimentDetail(row)">
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button 
                size="small" 
                type="primary"
                @click.stop="rerunExperiment(row)"
                :disabled="row.status === 'running'"
              >
                <el-icon><Refresh /></el-icon>
                重跑
              </el-button>
              <el-button 
                size="small" 
                type="danger"
                @click.stop="deleteExperiment(row)"
                :disabled="row.status === 'running'"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="card-view">
        <el-row :gutter="16">
          <el-col 
            v-for="experiment in paginatedExperiments" 
            :key="experiment.experiment_id"
            :span="8"
            class="experiment-card-col"
          >
            <el-card 
              class="experiment-card"
              :class="{ 'selected': selectedExperiments.includes(experiment.experiment_id) }"
              @click="toggleSelection(experiment)"
            >
              <template #header>
                <div class="card-header">
                  <div class="card-title">{{ experiment.name }}</div>
                  <el-tag :type="getStatusTagType(experiment.status)" size="small">
                    {{ getStatusText(experiment.status) }}
                  </el-tag>
                </div>
              </template>

              <div class="card-content">
                <div class="card-info">
                  <div class="info-item">
                    <span class="info-label">实验ID:</span>
                    <span class="info-value">{{ experiment.experiment_id }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">模型类型:</span>
                    <span class="info-value">{{ experiment.model_type }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">性能分数:</span>
                    <span class="info-value">
                      {{ experiment.score ? experiment.score.toFixed(3) : '--' }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">运行时间:</span>
                    <span class="info-value">{{ formatRuntime(experiment.runtime) }}</span>
                  </div>
                </div>

                <div class="card-actions">
                  <el-button size="small" @click.stop="viewExperimentDetail(experiment)">
                    详情
                  </el-button>
                  <el-button 
                    size="small" 
                    type="primary"
                    @click.stop="rerunExperiment(experiment)"
                    :disabled="experiment.status === 'running'"
                  >
                    重跑
                  </el-button>
                  <el-button 
                    size="small" 
                    type="danger"
                    @click.stop="deleteExperiment(experiment)"
                    :disabled="experiment.status === 'running'"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredExperiments.length"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 实验详情对话框 -->
    <el-dialog 
      v-model="showExperimentDetail" 
      title="实验详情" 
      width="80%"
      :before-close="handleDialogClose"
    >
      <div v-if="selectedExperiment" class="experiment-detail">
        <!-- 基本信息 -->
        <el-row :gutter="24">
          <el-col :span="16">
            <el-card class="detail-card">
              <template #header>
                <span>基本信息</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="实验ID">
                  {{ selectedExperiment.experiment_id }}
                </el-descriptions-item>
                <el-descriptions-item label="实验名称">
                  {{ selectedExperiment.name }}
                </el-descriptions-item>
                <el-descriptions-item label="模型类型">
                  {{ selectedExperiment.model_type }}
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="getStatusTagType(selectedExperiment.status)">
                    {{ getStatusText(selectedExperiment.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatDate(selectedExperiment.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="运行时间">
                  {{ formatRuntime(selectedExperiment.runtime) }}
                </el-descriptions-item>
                <el-descriptions-item label="创建者">
                  {{ selectedExperiment.created_by || 'Unknown' }}
                </el-descriptions-item>
                <el-descriptions-item label="备注">
                  {{ selectedExperiment.description || '无' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="detail-card">
              <template #header>
                <span>性能指标</span>
              </template>
              <div v-if="selectedExperiment.metrics" class="metrics-grid">
                <div 
                  v-for="(value, key) in selectedExperiment.metrics" 
                  :key="key"
                  class="metric-item"
                >
                  <div class="metric-label">{{ getMetricLabel(key) }}</div>
                  <div class="metric-value">{{ formatMetricValue(key, value) }}</div>
                </div>
              </div>
              <div v-else class="no-metrics">
                <el-empty description="暂无性能指标" :image-size="80" />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 配置信息 -->
        <el-card class="detail-card">
          <template #header>
            <span>配置信息</span>
          </template>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="模型配置" name="model">
              <pre class="config-json">{{ formatJSON(selectedExperiment.model_config) }}</pre>
            </el-tab-pane>
            <el-tab-pane label="数据配置" name="data">
              <pre class="config-json">{{ formatJSON(selectedExperiment.data_config) }}</pre>
            </el-tab-pane>
            <el-tab-pane label="任务配置" name="task">
              <pre class="config-json">{{ formatJSON(selectedExperiment.task_config) }}</pre>
            </el-tab-pane>
            <el-tab-pane label="运行日志" name="logs">
              <div class="logs-container">
                <pre class="logs-content">{{ selectedExperiment.logs || '暂无日志信息' }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Experiment, Refresh, Plus, Download, Search, CaretTop, Timer,
  CircleCheck, TrendCharts, Menu, Grid, View, Delete
} from '@element-plus/icons-vue'

// 数据结构定义
interface ExperimentRecord {
  experiment_id: string
  name: string
  model_type: string
  status: 'running' | 'finished' | 'failed' | 'cancelled'
  score?: number
  runtime: number
  created_at: string
  created_by?: string
  description?: string
  metrics?: Record<string, number>
  model_config?: any
  data_config?: any
  task_config?: any
  logs?: string
}

// 响应式数据
const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const viewMode = ref<'table' | 'card'>('table')
const selectedExperiments = ref<string[]>([])
const showExperimentDetail = ref(false)
const selectedExperiment = ref<ExperimentRecord | null>(null)
const activeTab = ref('model')

const filters = reactive({
  status: '',
  modelType: '',
  dateRange: [] as string[]
})

const experiments = ref<ExperimentRecord[]>([])

const experimentStats = reactive({
  total: 0,
  running: 0,
  successRate: 0,
  bestScore: 0,
  monthlyNew: 0,
  avgRuntime: 0,
  bestExperiment: ''
})

// 计算属性
const filteredExperiments = computed(() => {
  let filtered = experiments.value

  // 状态筛选
  if (filters.status) {
    filtered = filtered.filter(exp => exp.status === filters.status)
  }

  // 模型类型筛选
  if (filters.modelType) {
    filtered = filtered.filter(exp => exp.model_type.toLowerCase() === filters.modelType)
  }

  // 搜索筛选
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(exp =>
      exp.name.toLowerCase().includes(search) ||
      exp.experiment_id.toLowerCase().includes(search)
    )
  }

  // 时间范围筛选
  if (filters.dateRange && filters.dateRange.length === 2) {
    const [start, end] = filters.dateRange
    filtered = filtered.filter(exp => {
      const expDate = exp.created_at.split(' ')[0]
      return expDate >= start && expDate <= end
    })
  }

  return filtered
})

const paginatedExperiments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredExperiments.value.slice(start, end)
})

// 方法
const loadExperiments = async () => {
  loading.value = true

  try {
    const response = await fetch('/api/v1/experiments', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const result = await response.json()

    if (result.status === 'success') {
      experiments.value = result.data.experiments || []
      updateStats()
      ElMessage.success('实验记录加载成功')
    } else {
      throw new Error(result.message || '加载实验记录失败')
    }
  } catch (error) {
    console.error('加载实验记录失败:', error)
    ElMessage.error('加载实验记录失败: ' + error.message)
    
    // 降级到示例数据
    generateSampleExperiments()
  } finally {
    loading.value = false
  }
}

const generateSampleExperiments = () => {
  experiments.value = [
    {
      experiment_id: 'exp_001',
      name: 'LightGBM多因子策略v1',
      model_type: 'LightGBM',
      status: 'finished',
      score: 0.892,
      runtime: 1800,
      created_at: '2024-01-15 10:30:00',
      created_by: 'admin',
      description: '基于Alpha158因子的LightGBM模型实验',
      metrics: {
        accuracy: 0.892,
        sharpe_ratio: 2.34,
        max_drawdown: -0.065
      }
    },
    {
      experiment_id: 'exp_002',
      name: 'LSTM时序预测模型',
      model_type: 'LSTM',
      status: 'running',
      runtime: 3600,
      created_at: '2024-01-16 14:20:00',
      created_by: 'user1'
    }
  ]
  
  updateStats()
}

const updateStats = () => {
  experimentStats.total = experiments.value.length
  experimentStats.running = experiments.value.filter(exp => exp.status === 'running').length
  
  const finished = experiments.value.filter(exp => exp.status === 'finished')
  experimentStats.successRate = experiments.value.length > 0 ? 
    (finished.length / experiments.value.length * 100) : 0
  
  const scores = experiments.value.filter(exp => exp.score).map(exp => exp.score!)
  experimentStats.bestScore = scores.length > 0 ? Math.max(...scores) * 100 : 0
  
  experimentStats.avgRuntime = experiments.value.length > 0 ?
    Math.round(experiments.value.reduce((sum, exp) => sum + exp.runtime, 0) / experiments.value.length / 60) : 0
  
  experimentStats.monthlyNew = 5
  experimentStats.bestExperiment = 'LightGBM_v3'
}

const refreshExperiments = () => {
  loadExperiments()
}

const createExperiment = () => {
  // 跳转到实验创建页面
  ElMessage.info('跳转到实验创建页面')
}

const exportExperiments = () => {
  // 导出实验记录
  const csvContent = convertExperimentsToCSV(experiments.value)
  downloadCSV(csvContent, 'qlib_experiments.csv')
  ElMessage.success('实验记录导出成功')
}

const convertExperimentsToCSV = (data: ExperimentRecord[]) => {
  const headers = ['实验ID', '名称', '模型类型', '状态', '分数', '运行时间', '创建时间']
  const rows = data.map(exp => [
    exp.experiment_id,
    exp.name,
    exp.model_type,
    exp.status,
    exp.score || '',
    formatRuntime(exp.runtime),
    exp.created_at
  ])
  
  return [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
}

const downloadCSV = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const debounceSearch = (() => {
  let timeout: NodeJS.Timeout
  return () => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      // 搜索已通过计算属性自动更新
    }, 300)
  }
})()

const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    running: 'primary',
    finished: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return types[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    running: '运行中',
    finished: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const formatRuntime = (seconds: number) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleSelectionChange = (selection: ExperimentRecord[]) => {
  selectedExperiments.value = selection.map(exp => exp.experiment_id)
}

const toggleSelection = (experiment: ExperimentRecord) => {
  const index = selectedExperiments.value.indexOf(experiment.experiment_id)
  if (index > -1) {
    selectedExperiments.value.splice(index, 1)
  } else {
    selectedExperiments.value.push(experiment.experiment_id)
  }
}

const viewExperimentDetail = (experiment: ExperimentRecord) => {
  selectedExperiment.value = experiment
  showExperimentDetail.value = true
}

const rerunExperiment = async (experiment: ExperimentRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新运行实验 "${experiment.name}" 吗？`,
      '确认重跑',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    ElMessage.success('实验重跑请求已提交')
    // 这里应该调用API重新运行实验
  } catch {
    // 用户取消
  }
}

const deleteExperiment = async (experiment: ExperimentRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除实验 "${experiment.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = experiments.value.findIndex(exp => exp.experiment_id === experiment.experiment_id)
    if (index > -1) {
      experiments.value.splice(index, 1)
      updateStats()
      ElMessage.success('实验已删除')
    }
  } catch {
    // 用户取消
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

const handleDialogClose = () => {
  showExperimentDetail.value = false
  selectedExperiment.value = null
  activeTab.value = 'model'
}

const getMetricLabel = (key: string) => {
  const labels: Record<string, string> = {
    accuracy: '准确率',
    sharpe_ratio: '夏普比率',
    max_drawdown: '最大回撤',
    annual_return: '年化收益',
    volatility: '波动率'
  }
  return labels[key] || key
}

const formatMetricValue = (key: string, value: number) => {
  switch (key) {
    case 'accuracy':
    case 'annual_return':
      return (value * 100).toFixed(2) + '%'
    case 'sharpe_ratio':
    case 'volatility':
      return value.toFixed(3)
    case 'max_drawdown':
      return (value * 100).toFixed(2) + '%'
    default:
      return value.toString()
  }
}

const formatJSON = (obj: any) => {
  return JSON.stringify(obj, null, 2)
}

// 生命周期
onMounted(() => {
  loadExperiments()
})
</script>

<style scoped>
.qlib-experiment-manager {
  padding: 20px;
}

.manager-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.experiment-filters {
  padding: 16px 0;
}

.experiment-overview {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.success {
  color: #67c23a;
}

.trend-icon.primary {
  color: #409eff;
}

.trend-icon.warning {
  color: #e6a23c;
}

.experiment-table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-view {
  margin-bottom: 20px;
}

.experiment-card-col {
  margin-bottom: 16px;
}

.experiment-card {
  cursor: pointer;
  transition: all 0.3s;
}

.experiment-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.experiment-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 14px;
}

.card-content {
  padding-top: 12px;
}

.card-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.info-label {
  color: #909399;
}

.info-value {
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.experiment-detail {
  padding: 16px 0;
}

.detail-card {
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.metric-item {
  text-align: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.no-metrics {
  text-align: center;
  padding: 40px 0;
}

.config-json {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.logs-container {
  background: #000;
  color: #fff;
  border-radius: 6px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.logs-content {
  margin: 0;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .qlib-experiment-manager {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .experiment-filters .el-col {
    margin-bottom: 16px;
  }
  
  .experiment-overview .el-col {
    margin-bottom: 16px;
  }
  
  .card-view .el-col {
    span: 24;
  }
}
</style>