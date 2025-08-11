<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-subtitle">量化投资策略研究平台概览</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-24">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-card-content">
            <div class="stat-card-title">总实验数</div>
            <div class="stat-card-value">{{ summary.totalExperiments }}</div>
            <div class="stat-card-trend">
              <el-icon><TrendCharts /></el-icon>
              较昨日 +3
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <div class="stat-card-content">
            <div class="stat-card-title">运行中</div>
            <div class="stat-card-value">{{ summary.runningExperiments }}</div>
            <div class="stat-card-trend">
              <el-icon><Loading /></el-icon>
              实时更新
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <div class="stat-card-content">
            <div class="stat-card-title">已完成</div>
            <div class="stat-card-value">{{ summary.completedExperiments }}</div>
            <div class="stat-card-trend">
              <el-icon><SuccessFilled /></el-icon>
              成功率 95%
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
          <div class="stat-card-content">
            <div class="stat-card-title">失败数</div>
            <div class="stat-card-value">{{ summary.failedExperiments }}</div>
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
  TrendCharts, Loading, SuccessFilled, WarningFilled, 
  Lightning, Plus, Clock, Refresh, ArrowRight 
} from '@element-plus/icons-vue'
import { useExperimentStore } from '@/stores/experiment'
import { dashboardApi } from '@/api/experiment'
import type { ExperimentStatus } from '@/types/experiment'

const router = useRouter()
const experimentStore = useExperimentStore()

// 响应式数据
const loading = ref(false)
const summary = ref({
  totalExperiments: 0,
  runningExperiments: 0,
  completedExperiments: 0,
  failedExperiments: 0
})
const recentExperiments = ref<ExperimentStatus[]>([])

// 方法
const getStatusText = (status: string) => {
  const statusMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status as keyof typeof statusMap] || status
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleRowClick = (row: ExperimentStatus) => {
  if (row.status === 'completed') {
    router.push(`/experiment/${row.id}`)
  } else {
    ElMessage.info('实验尚未完成，无法查看详情')
  }
}

const viewDetails = (id: string) => {
  router.push(`/experiment/${id}`)
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
      summary.value = {
        totalExperiments: data.totalExperiments,
        runningExperiments: data.runningExperiments,
        completedExperiments: data.completedExperiments,
        failedExperiments: data.failedExperiments
      }
    }
    
    // 调用真实API获取最近实验列表
    const recentResponse = await dashboardApi.getRecentExperiments()
    if (recentResponse.data.success) {
      recentExperiments.value = recentResponse.data.data.map((exp: any) => ({
        id: exp.id,
        name: exp.name,
        status: exp.status,
        progress: exp.progress || 0,
        createdAt: exp.created_at || exp.createdAt,
        completedAt: exp.completed_at || exp.completedAt
      }))
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('加载仪表盘数据失败')
    // 如果API失败，使用基础的默认值
    summary.value = {
      totalExperiments: 0,
      runningExperiments: 0,
      completedExperiments: 0,
      failedExperiments: 0
    }
    recentExperiments.value = []
  }
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.stat-card {
  margin-bottom: 16px;
}

.stat-card :deep(.el-card__body) {
  padding: 24px;
}

.stat-card-content {
  color: white;
}

.stat-card-title {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-card-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-card-trend {
  font-size: 12px;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.quick-actions {
  text-align: center;
}

.experiment-table :deep(.el-table__row) {
  cursor: pointer;
}

.experiment-table :deep(.el-table__row:hover) {
  background: #f5f7fa;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: #e6f7ff;
  color: #1890ff;
}

.status-badge.running {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.completed {
  background: #f0f9ff;
  color: #1677ff;
}

.status-badge.failed {
  background: #fff2f0;
  color: #ff4d4f;
}
</style>