<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">历史记录</h1>
      <p class="page-subtitle">查看和管理所有实验记录</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-section mb-24">
      <el-row :gutter="16" class="mb-16">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索实验名称..."
            clearable
            @change="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select 
            v-model="statusFilter" 
            placeholder="筛选状态"
            clearable
            @change="handleFilter"
          >
            <el-option label="全部状态" value="" />
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="24" :md="10" class="text-right">
          <el-button @click="handleRefresh" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="$router.push('/create')">
            <el-icon><Plus /></el-icon>
            新建实验
          </el-button>
          <el-button 
            type="danger" 
            :disabled="selectedRows.length === 0"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 实验列表 -->
    <el-card>
      <!-- 批量操作工具栏 -->
      <div v-if="selectedRows.length > 0" class="batch-toolbar mb-16">
        <span class="selected-count">已选择 {{ selectedRows.length }} 个实验</span>
        <el-button 
          type="danger" 
          size="small"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <!-- 虚拟滚动表格 -->
      <VirtualScrollTable
        :data="allFilteredExperiments"
        :columns="tableColumns"
        :loading="loading"
        :container-height="600"
        :item-height="80"
        :buffer-size="5"
        @row-click="handleRowClick"
        class="virtual-experiment-table"
      >
        <!-- 选择框列 -->
        <template #selection="{ row, index }">
          <el-checkbox
            :model-value="isRowSelected(row)"
            @change="handleRowSelection(row, $event)"
          />
        </template>

        <!-- 实验名称列 -->
        <template #name="{ row }">
          <div class="experiment-name">
            <div style="font-weight: 500; margin-bottom: 4px;">{{ row.name }}</div>
            <div style="font-size: 12px; color: #909399;">ID: {{ row.id }}</div>
          </div>
        </template>

        <!-- 状态列 -->
        <template #status="{ row }">
          <span :class="['status-badge', row.status]">
            <el-icon v-if="row.status === 'running'"><Loading /></el-icon>
            <el-icon v-else-if="row.status === 'completed'"><SuccessFilled /></el-icon>
            <el-icon v-else-if="row.status === 'failed'"><WarningFilled /></el-icon>
            <el-icon v-else><Clock /></el-icon>
            {{ getStatusText(row.status) }}
          </span>
        </template>

        <!-- 进度列 -->
        <template #progress="{ row }">
          <div class="progress-container">
            <el-progress 
              :percentage="row.progress" 
              :status="getProgressStatus(row.status)"
              :stroke-width="8"
              :show-text="false"
            />
            <span class="progress-text">{{ row.progress }}%</span>
          </div>
        </template>

        <!-- 创建时间列 -->
        <template #createdAt="{ row }">
          <div class="time-info">
            <div>{{ formatDate(row.createdAt) }}</div>
            <div style="font-size: 12px; color: #909399;">
              {{ formatTime(row.createdAt) }}
            </div>
          </div>
        </template>

        <!-- 完成时间列 -->
        <template #completedAt="{ row }">
          <div v-if="row.completedAt" class="time-info">
            <div>{{ formatDate(row.completedAt) }}</div>
            <div style="font-size: 12px; color: #909399;">
              {{ formatTime(row.completedAt) }}
            </div>
          </div>
          <span v-else style="color: #c0c4cc;">-</span>
        </template>

        <!-- 操作列 -->
        <template #actions="{ row }">
          <div class="action-buttons">
            <el-button 
              type="text" 
              size="small"
              @click.stop="viewDetails(row.id)"
              :disabled="row.status !== 'completed'"
            >
              查看详情
            </el-button>
            <el-button 
              type="text" 
              size="small"
              @click.stop="duplicateExperiment(row.id)"
            >
              复制
            </el-button>
            <el-popconfirm
              title="确定删除这个实验吗？"
              @confirm="deleteExperiment(row.id)"
            >
              <template #reference>
                <el-button 
                  type="text" 
                  size="small"
                  style="color: #f56c6c;"
                  @click.stop
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </template>
      </VirtualScrollTable>

      <!-- 统计信息 -->
      <div class="table-footer mt-16">
        <div class="total-info">
          共 {{ allFilteredExperiments.length }} 个实验
          <el-divider direction="vertical" />
          已完成: {{ getStatusCount('completed') }}
          <el-divider direction="vertical" />
          运行中: {{ getStatusCount('running') }}
          <el-divider direction="vertical" />
          失败: {{ getStatusCount('failed') }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Refresh, Plus, Delete, Loading, 
  SuccessFilled, WarningFilled, Clock 
} from '@element-plus/icons-vue'
import { useExperimentStore } from '@/stores/experiment'
import VirtualScrollTable from '@/components/VirtualScrollTable.vue'
import type { ExperimentStatus } from '@/types/experiment'

const router = useRouter()
const experimentStore = useExperimentStore()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')
const selectedRows = ref<ExperimentStatus[]>([])

// 实验数据
const experiments = ref<ExperimentStatus[]>([])

// 表格列配置
const tableColumns = [
  { key: 'selection', title: '选择', width: 60, slot: 'selection' },
  { key: 'name', title: '实验名称', width: 200, slot: 'name' },
  { key: 'status', title: '状态', width: 120, slot: 'status' },
  { key: 'progress', title: '进度', width: 150, slot: 'progress' },
  { key: 'createdAt', title: '创建时间', width: 160, slot: 'createdAt' },
  { key: 'completedAt', title: '完成时间', width: 160, slot: 'completedAt' },
  { key: 'actions', title: '操作', width: 180, slot: 'actions' }
]

// 计算属性 - 所有过滤后的实验数据（用于虚拟滚动）
const allFilteredExperiments = computed(() => {
  let filtered = experiments.value

  // 搜索过滤
  if (searchKeyword.value) {
    filtered = filtered.filter(exp => 
      exp.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter(exp => exp.status === statusFilter.value)
  }

  return filtered
})

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

const getProgressStatus = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'exception'
    case 'running':
      return undefined
    default:
      return undefined
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-CN', { 
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

const handleSelectionChange = (selection: ExperimentStatus[]) => {
  selectedRows.value = selection
}

// 行选择相关方法
const isRowSelected = (row: ExperimentStatus): boolean => {
  return selectedRows.value.some(selected => selected.id === row.id)
}

const handleRowSelection = (row: ExperimentStatus, checked: boolean) => {
  if (checked) {
    if (!isRowSelected(row)) {
      selectedRows.value.push(row)
    }
  } else {
    const index = selectedRows.value.findIndex(selected => selected.id === row.id)
    if (index > -1) {
      selectedRows.value.splice(index, 1)
    }
  }
}

// 获取状态统计
const getStatusCount = (status: string): number => {
  return allFilteredExperiments.value.filter(exp => exp.status === status).length
}

const handleSearch = () => {
  // 搜索时清空选择
  selectedRows.value = []
}

const handleFilter = () => {
  // 过滤时清空选择
  selectedRows.value = []
}

const handleRefresh = async () => {
  await loadExperiments()
  selectedRows.value = []
  ElMessage.success('数据刷新成功')
}

const viewDetails = (id: string) => {
  router.push(`/experiment/${id}`)
}

const duplicateExperiment = async (id: string) => {
  try {
    // TODO: 实现复制实验功能
    ElMessage.success('实验复制成功')
    await loadExperiments()
  } catch (error) {
    ElMessage.error('实验复制失败')
  }
}

const deleteExperiment = async (id: string) => {
  try {
    await experimentStore.deleteExperiment(id)
    ElMessage.success('实验删除成功')
    await loadExperiments()
  } catch (error) {
    ElMessage.error('实验删除失败')
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedRows.value.length} 个实验吗？`,
      '批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // TODO: 实现批量删除
    for (const row of selectedRows.value) {
      await experimentStore.deleteExperiment(row.id)
    }

    ElMessage.success('批量删除成功')
    await loadExperiments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const loadExperiments = async () => {
  loading.value = true
  try {
    await experimentStore.fetchExperimentList()
    experiments.value = experimentStore.experimentList
  } finally {
    loading.value = false
  }
}

// 监听状态变化，自动刷新运行中的实验
let refreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  refreshTimer = setInterval(async () => {
    const hasRunning = experiments.value.some(exp => exp.status === 'running')
    if (hasRunning) {
      await loadExperiments()
    }
  }, 10000) // 每10秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(() => {
  loadExperiments()
  startAutoRefresh()
})

// 监听路由变化，停止自动刷新
watch(() => router.currentRoute.value.path, () => {
  stopAutoRefresh()
})

// 组件卸载时清理定时器
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.filter-section {
  background: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.experiment-name {
  cursor: pointer;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
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

.progress-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  min-width: 35px;
}

.time-info {
  line-height: 1.4;
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

.experiment-table :deep(.el-table__row) {
  cursor: pointer;
}

.experiment-table :deep(.el-table__row:hover) {
  background: #f5f7fa;
}

/* 批量操作工具栏 */
.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.selected-count {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

/* 虚拟滚动表格样式 */
.virtual-experiment-table {
  min-height: 600px;
}

/* 表格底部统计信息 */
.table-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid #e4e7ed;
}

.total-info {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .batch-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .total-info {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  
  .virtual-experiment-table {
    min-height: 500px;
  }
}
</style>