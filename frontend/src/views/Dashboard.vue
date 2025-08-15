<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><DataLine /></el-icon>
        工作流程控制中心
      </h1>
      <p class="page-subtitle">AI驱动的量化投资策略研发平台</p>
    </div>

    <!-- 系统状态概览 -->
    <el-card class="status-overview-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><TrendCharts /></el-icon>
          <span>系统状态</span>
        </div>
      </template>
      <div class="status-content">
        <div class="active-tasks">
          <el-icon><Loading /></el-icon>
          <span>活跃任务: {{ activeTasksCount }}个训练中 | {{ runningBacktests }}个回测中 | {{ deployedStrategies }}个部署运行</span>
        </div>
        <div class="smart-suggestions">
          <el-icon><Lightning /></el-icon>
          <span>建议操作: 查看LightGBM_v3训练结果 → 启动回测</span>
        </div>
      </div>
    </el-card>

    <!-- 工作流程快速启动 -->
    <el-card class="workflow-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><ArrowRight /></el-icon>
          <span>工作流程快速启动</span>
        </div>
      </template>
      <el-row :gutter="20" class="workflow-options">
        <el-col :xs="24" :sm="8">
          <div class="workflow-option complete-research" @click="startCompleteResearch">
            <div class="option-icon">
              <el-icon><MagicStick /></el-icon>
            </div>
            <div class="option-content">
              <h3>完整研发</h3>
              <p>从因子开发到策略部署</p>
              <el-button type="primary" size="small">开始研发</el-button>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="workflow-option quick-backtest" @click="startQuickBacktest">
            <div class="option-icon">
              <el-icon><Lightning /></el-icon>
            </div>
            <div class="option-content">
              <h3>快速回测</h3>
              <p>使用现有模型快速验证策略</p>
              <el-button type="success" size="small">快速验证</el-button>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="workflow-option manage-tasks" @click="manageAllTasks">
            <div class="option-icon">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="option-content">
              <h3>管理任务</h3>
              <p>查看所有进度管理资源</p>
              <el-button type="info" size="small">进入管理</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 最近活动与结果 -->
    <el-card class="recent-activities-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>最近活动与结果</span>
          <el-button type="text" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <div class="activities-content">
        <div class="activity-tabs">
          <el-tabs v-model="activeTab" class="demo-tabs">
            <el-tab-pane label="因子开发" name="factors">
              <div class="activity-list">
                <div v-for="factor in recentFactors" :key="factor.id" class="activity-item">
                  <div class="activity-icon">
                    <el-icon><MagicStick /></el-icon>
                  </div>
                  <div class="activity-content">
                    <div class="activity-title">{{ factor.name }}</div>
                    <div class="activity-desc">{{ factor.description }}</div>
                    <div class="activity-time">{{ formatDate(factor.createdAt) }}</div>
                  </div>
                  <div class="activity-actions">
                    <el-button type="text" size="small" @click="editFactor(factor.id)">编辑</el-button>
                    <el-button type="text" size="small" @click="useFactor(factor.id)">使用</el-button>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="模型训练" name="training">
              <div class="activity-list">
                <div v-for="model in recentModels" :key="model.id" class="activity-item">
                  <div class="activity-icon">
                    <el-icon><Cpu /></el-icon>
                  </div>
                  <div class="activity-content">
                    <div class="activity-title">{{ model.name }}</div>
                    <div class="activity-desc">准确率: {{ model.accuracy }}%</div>
                    <div class="activity-time">{{ formatDate(model.createdAt) }}</div>
                  </div>
                  <div class="activity-actions">
                    <el-button type="text" size="small" @click="viewModel(model.id)">查看</el-button>
                    <el-button type="text" size="small" @click="startBacktest(model.id)">回测</el-button>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="策略回测" name="backtest">
              <div class="activity-list">
                <div v-for="backtest in recentBacktests" :key="backtest.id" class="activity-item">
                  <div class="activity-icon">
                    <el-icon><TrendCharts /></el-icon>
                  </div>
                  <div class="activity-content">
                    <div class="activity-title">{{ backtest.name }}</div>
                    <div class="activity-desc">年化收益: {{ backtest.annualReturn }}%</div>
                    <div class="activity-time">{{ formatDate(backtest.createdAt) }}</div>
                  </div>
                  <div class="activity-actions">
                    <el-button type="text" size="small" @click="viewBacktest(backtest.id)">分析</el-button>
                    <el-button type="text" size="small" @click="deployStrategy(backtest.id)">部署</el-button>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-card>
  </div>
</template>
            <div class="stat-card-trend">
              <el-icon><WarningFilled /></el-icon>
              需关注
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作和最近实验 -->
    <el-row :gutter="16">
      <!-- 快速操作 -->
      <el-col :xs="24" :sm="24" :md="8">
        <el-card>
          <template #header>
            <div class="flex items-center justify-between">
              <span>快速操作</span>
              <el-icon><Lightning /></el-icon>
            </div>
          </template>
          <div class="quick-actions">
            <el-button 
              type="primary" 
              size="large" 
              style="width: 100%; margin-bottom: 12px;"
              @click="$router.push('/create')"
            >
              <el-icon><Plus /></el-icon>
              新建实验
            </el-button>
            <el-button 
              type="success" 
              size="large" 
              style="width: 100%; margin-bottom: 12px;"
              @click="$router.push('/history')"
            >
              <el-icon><Clock /></el-icon>
              查看历史
            </el-button>
            <el-button 
              type="info" 
              size="large" 
              style="width: 100%;"
              @click="refreshData"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 最近实验 -->
      <el-col :xs="24" :sm="24" :md="16">
        <el-card>
          <template #header>
            <div class="flex items-center justify-between">
              <span>最近实验</span>
              <el-button type="text" @click="$router.push('/history')">
                查看全部
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table 
            :data="recentExperiments" 
            style="width: 100%"
            @row-click="handleRowClick"
            class="experiment-table"
          >
            <el-table-column prop="name" label="实验名称" min-width="120">
              <template #default="{ row }">
                <div style="font-weight: 500;">{{ row.name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <span :class="['status-badge', row.status]">
                  {{ getStatusText(row.status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.progress" 
                  :status="row.status === 'completed' ? 'success' : ''"
                  :stroke-width="6"
                />
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="150">
              <template #default="{ row }">
                <div style="font-size: 12px; color: #909399;">
                  {{ formatDate(row.createdAt) }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="text" size="small" @click.stop="viewDetails(row.id)">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  TrendCharts, Loading, DataLine, Lightning, 
  Clock, Refresh, ArrowRight, MagicStick, Cpu
} from '@element-plus/icons-vue'
import { dashboardApi } from '@/api/experiment'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const activeTab = ref('factors')

// 系统状态数据
const activeTasksCount = ref(0)
const runningBacktests = ref(0)
const deployedStrategies = ref(0)

// 最近活动数据
const recentFactors = ref([
  { id: 1, name: '20日动量因子', description: '基于20日价格动量的技术指标', createdAt: '2025-08-15T10:30:00' },
  { id: 2, name: '市盈率倒数因子', description: '基于PE倒数的价值因子', createdAt: '2025-08-14T16:20:00' }
])

const recentModels = ref([
  { id: 1, name: 'LightGBM_v3', accuracy: 94.2, createdAt: '2025-08-15T14:30:00' },
  { id: 2, name: 'XGBoost_test', accuracy: 91.8, createdAt: '2025-08-14T11:15:00' }
])

const recentBacktests = ref([
  { id: 1, name: 'TopK_LightGBM_v3', annualReturn: 28.5, createdAt: '2025-08-15T09:45:00' },
  { id: 2, name: 'LSTM_momentum', annualReturn: 25.1, createdAt: '2025-08-14T17:30:00' }
])

// 方法
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 工作流程启动方法
const startCompleteResearch = () => {
  ElMessage.info('启动完整研发流程')
  router.push('/factors')
}

const startQuickBacktest = () => {
  ElMessage.info('启动快速回测')
  router.push('/backtest')
}

const manageAllTasks = () => {
  ElMessage.info('进入任务管理')
  router.push('/training-management')
}

// 活动相关方法
const editFactor = (factorId: number) => {
  ElMessage.info(`编辑因子 ${factorId}`)
  router.push(`/factors?edit=${factorId}`)
}

const useFactor = (factorId: number) => {
  ElMessage.info(`使用因子 ${factorId}`)
  router.push(`/training?factors=${factorId}`)
}

const viewModel = (modelId: number) => {
  ElMessage.info(`查看模型 ${modelId}`)
  router.push(`/training-management?model=${modelId}`)
}

const startBacktest = (modelId: number) => {
  ElMessage.info(`开始回测模型 ${modelId}`)
  router.push(`/backtest?model=${modelId}`)
}

const viewBacktest = (backtestId: number) => {
  ElMessage.info(`查看回测结果 ${backtestId}`)
  router.push(`/results?backtest=${backtestId}`)
}

const deployStrategy = (backtestId: number) => {
  ElMessage.info(`部署策略 ${backtestId}`)
  router.push(`/deployment?strategy=${backtestId}`)
}

const refreshData = async () => {
  loading.value = true
  try {
    await loadDashboardData()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const loadDashboardData = async () => {
  try {
    // 调用真实API获取仪表盘统计数据
    const summaryResponse = await dashboardApi.getSummary()
    if (summaryResponse.data.success) {
      const data = summaryResponse.data.data
      // 更新系统状态数据
      activeTasksCount.value = data.running_experiments || 0
      runningBacktests.value = data.running_experiments || 0  // 暂时使用相同数据
      deployedStrategies.value = 1 // 模拟数据
    }
    
    // 在实际项目中，这里应该调用具体的API获取因子、模型、回测数据
    // 目前使用模拟数据展示功能
    console.log('Dashboard数据加载完成')
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('加载仪表盘数据失败')
    // 如果API失败，使用模拟数据
    activeTasksCount.value = 0
    runningBacktests.value = 0
    deployedStrategies.value = 0
  }
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-subtitle {
  margin: 0;
  color: #7f8c8d;
  font-size: 16px;
}

.status-overview-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.status-content {
  padding: 16px 0;
}

.active-tasks, .smart-suggestions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #5a6c7d;
}

.active-tasks:last-child, .smart-suggestions:last-child {
  margin-bottom: 0;
}

.workflow-card {
  margin-bottom: 24px;
}

.workflow-options {
  margin-top: 20px;
}

.workflow-option {
  border: 2px solid #e1e8ed;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.workflow-option:hover {
  border-color: #409eff;
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.2);
}

.complete-research:hover {
  border-color: #409eff;
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.2);
}

.quick-backtest:hover {
  border-color: #67c23a;
  box-shadow: 0 8px 25px rgba(103, 194, 58, 0.2);
}

.manage-tasks:hover {
  border-color: #909399;
  box-shadow: 0 8px 25px rgba(144, 147, 153, 0.2);
}

.option-icon {
  font-size: 32px;
  margin-bottom: 16px;
  color: #409eff;
}

.quick-backtest .option-icon {
  color: #67c23a;
}

.manage-tasks .option-icon {
  color: #909399;
}

.option-content h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.option-content p {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #7f8c8d;
  line-height: 1.4;
}

.recent-activities-card {
  background: white;
}

.activities-content {
  padding: 0;
}

.activity-list {
  min-height: 200px;
}

.activity-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.activity-item:hover {
  background-color: #f8f9fa;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  margin-right: 16px;
  font-size: 20px;
  color: #409eff;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.activity-desc {
  font-size: 12px;
  color: #7f8c8d;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #bdc3c7;
}

.activity-actions {
  display: flex;
  gap: 8px;
}

:deep(.el-tabs__header) {
  margin: 0;
}

:deep(.el-tabs__content) {
  padding: 0;
}
</style>