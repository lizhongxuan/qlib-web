<template>
  <el-popover
    :visible="showQuickActions"
    placement="bottom-end"
    :width="350"
    trigger="click"
  >
    <template #reference>
      <el-badge :value="pendingActions" :hidden="pendingActions === 0" type="warning">
        <el-button circle @click="toggleQuickActions" :class="{ 'active': showQuickActions }">
          <el-icon><Lightning /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="quick-action-panel">
      <div class="panel-header">
        <h4>快速操作</h4>
        <el-button size="small" text @click="showQuickActions = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <!-- 一键操作 -->
      <div class="quick-actions-section">
        <div class="section-title">一键操作</div>
        <div class="actions-grid">
          <div
            v-for="action in quickActions"
            :key="action.id"
            class="action-item"
            :class="{ disabled: action.disabled }"
            @click="executeQuickAction(action)"
          >
            <div class="action-icon" :style="{ background: action.color }">
              <el-icon>
                <component :is="action.icon" />
              </el-icon>
            </div>
            <div class="action-content">
              <div class="action-title">{{ action.title }}</div>
              <div class="action-desc">{{ action.description }}</div>
            </div>
            <div v-if="action.badge" class="action-badge">
              <el-badge :value="action.badge" type="danger" />
            </div>
          </div>
        </div>
      </div>

      <!-- 待办事项 -->
      <div v-if="todoItems.length > 0" class="todo-section">
        <div class="section-title">
          待办事项
          <el-tag size="small" type="warning">{{ todoItems.length }}</el-tag>
        </div>
        <div class="todo-list">
          <div
            v-for="todo in todoItems"
            :key="todo.id"
            class="todo-item"
            :class="{ completed: todo.completed }"
          >
            <el-checkbox
              v-model="todo.completed"
              @change="updateTodoStatus(todo)"
            />
            <div class="todo-content">
              <div class="todo-title">{{ todo.title }}</div>
              <div class="todo-meta">
                <span class="todo-priority" :class="`priority-${todo.priority}`">
                  {{ getPriorityText(todo.priority) }}
                </span>
                <span class="todo-time">{{ formatDueTime(todo.dueTime) }}</span>
              </div>
            </div>
            <el-button size="small" text @click="goToTodoAction(todo)">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 快速创建 -->
      <div class="quick-create-section">
        <div class="section-title">快速创建</div>
        <div class="create-actions">
          <el-button
            v-for="create in createActions"
            :key="create.id"
            :type="create.type"
            size="small"
            @click="executeCreateAction(create)"
            :loading="create.loading"
          >
            <el-icon>
              <component :is="create.icon" />
            </el-icon>
            {{ create.title }}
          </el-button>
        </div>
      </div>

      <!-- 最近使用的操作 -->
      <div class="recent-actions-section">
        <div class="section-title">最近使用</div>
        <div class="recent-actions">
          <div
            v-for="recent in recentActions"
            :key="recent.id"
            class="recent-action"
            @click="executeRecentAction(recent)"
          >
            <el-icon>
              <component :is="recent.icon" />
            </el-icon>
            <span>{{ recent.title }}</span>
            <span class="recent-time">{{ formatRelativeTime(recent.lastUsed) }}</span>
          </div>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="system-status-section">
        <div class="section-title">系统状态</div>
        <div class="status-indicators">
          <div class="status-item">
            <div class="status-dot success"></div>
            <span>数据连接正常</span>
          </div>
          <div class="status-item">
            <div class="status-dot" :class="getServiceStatus('training')"></div>
            <span>训练服务</span>
            <span v-if="runningTasks > 0" class="status-detail">
              {{ runningTasks }}个任务
            </span>
          </div>
          <div class="status-item">
            <div class="status-dot" :class="getServiceStatus('deployment')"></div>
            <span>部署服务</span>
            <span v-if="activeDeployments > 0" class="status-detail">
              {{ activeDeployments }}个实例
            </span>
          </div>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuickActionStore } from '@/stores/quickAction'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Lightning, Close, ArrowRight, Plus, MagicStick, Cpu,
  TrendCharts, Upload, DocumentAdd, FolderAdd
} from '@element-plus/icons-vue'

const router = useRouter()
const quickActionStore = useQuickActionStore()

// 响应式数据
const showQuickActions = ref(false)

// 计算属性
const pendingActions = computed(() => quickActionStore.pendingActionsCount)
const todoItems = computed(() => quickActionStore.todoItems)
const runningTasks = computed(() => quickActionStore.systemStatus.runningTasks)
const activeDeployments = computed(() => quickActionStore.systemStatus.activeDeployments)

// 快速操作配置
const quickActions = ref([
  {
    id: 'new-experiment',
    title: '新建实验',
    description: '快速创建训练实验',
    icon: 'Plus',
    color: '#409eff',
    action: 'create-experiment',
    disabled: false
  },
  {
    id: 'emergency-stop',
    title: '紧急停止',
    description: '停止所有运行任务',
    icon: 'Close',
    color: '#f56c6c',
    action: 'emergency-stop',
    disabled: false,
    badge: runningTasks.value > 0 ? runningTasks.value : null
  },
  {
    id: 'backup-data',
    title: '数据备份',
    description: '备份重要数据',
    icon: 'DocumentAdd',
    color: '#e6a23c',
    action: 'backup-data',
    disabled: false
  },
  {
    id: 'sync-models',
    title: '模型同步',
    description: '同步最新模型',
    icon: 'Refresh',
    color: '#67c23a',
    action: 'sync-models',
    disabled: false
  }
])

// 快速创建操作
const createActions = ref([
  {
    id: 'create-factor',
    title: '因子',
    icon: 'MagicStick',
    type: 'primary',
    action: '/factors',
    loading: false
  },
  {
    id: 'create-model',
    title: '模型',
    icon: 'Cpu',
    type: 'success',
    action: '/training',
    loading: false
  },
  {
    id: 'create-strategy',
    title: '策略',
    icon: 'TrendCharts',
    type: 'warning',
    action: '/backtest',
    loading: false
  },
  {
    id: 'create-deployment',
    title: '部署',
    icon: 'Upload',
    type: 'danger',
    action: '/deployment',
    loading: false
  }
])

// 最近使用的操作
const recentActions = computed(() => quickActionStore.recentActions)

// 方法
const toggleQuickActions = () => {
  showQuickActions.value = !showQuickActions.value
  if (showQuickActions.value) {
    quickActionStore.recordPanelOpen()
  }
}

const executeQuickAction = async (action: any) => {
  if (action.disabled) return

  try {
    switch (action.action) {
      case 'create-experiment':
        router.push('/training')
        ElMessage.success('已跳转到实验创建页面')
        break
        
      case 'emergency-stop':
        if (runningTasks.value === 0) {
          ElMessage.info('当前没有运行中的任务')
          return
        }
        
        await ElMessageBox.confirm(
          `确定要停止所有 ${runningTasks.value} 个运行中的任务吗？`,
          '紧急停止确认',
          { type: 'warning' }
        )
        
        await quickActionStore.emergencyStopAllTasks()
        ElMessage.success('所有任务已停止')
        break
        
      case 'backup-data':
        await quickActionStore.startDataBackup()
        ElMessage.success('数据备份已开始')
        break
        
      case 'sync-models':
        await quickActionStore.syncModels()
        ElMessage.success('模型同步完成')
        break
    }
    
    quickActionStore.recordActionUsed(action.id)
    showQuickActions.value = false
    
  } catch (error) {
    console.error('执行快速操作失败:', error)
  }
}

const updateTodoStatus = (todo: any) => {
  quickActionStore.updateTodoStatus(todo.id, todo.completed)
  
  if (todo.completed) {
    ElMessage.success(`任务"${todo.title}"已完成`)
  }
}

const goToTodoAction = (todo: any) => {
  if (todo.actionUrl) {
    router.push(todo.actionUrl)
    showQuickActions.value = false
  }
}

const executeCreateAction = async (create: any) => {
  create.loading = true
  
  try {
    // 模拟创建过程
    await new Promise(resolve => setTimeout(resolve, 500))
    
    router.push(create.action)
    quickActionStore.recordActionUsed(create.id)
    showQuickActions.value = false
    
  } finally {
    create.loading = false
  }
}

const executeRecentAction = (recent: any) => {
  if (recent.actionUrl) {
    router.push(recent.actionUrl)
  } else if (recent.callback) {
    recent.callback()
  }
  
  quickActionStore.recordActionUsed(recent.id)
  showQuickActions.value = false
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'high': return '高'
    case 'medium': return '中'
    case 'low': return '低'
    default: return '普通'
  }
}

const formatDueTime = (timestamp: number) => {
  const now = Date.now()
  const diff = timestamp - now
  
  if (diff < 0) return '已逾期'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟后`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时后`
  
  const days = Math.floor(diff / 86400000)
  return `${days}天后`
}

const formatRelativeTime = (timestamp: number) => {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  return `${days}天前`
}

const getServiceStatus = (service: string) => {
  const status = quickActionStore.systemStatus.services[service]
  switch (status) {
    case 'healthy': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'danger'
    default: return 'info'
  }
}

onMounted(() => {
  // 初始化快速操作数据
  quickActionStore.initializeQuickActions()
})
</script>

<style scoped>
.quick-action-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 12px;
}

.panel-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  position: relative;
}

.action-item:hover:not(.disabled) {
  background: #f0f8ff;
  border-color: #409eff;
  transform: translateY(-1px);
}

.action-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
}

.action-content {
  flex: 1;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
}

.action-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.todo-item:hover {
  background: #f8f9fa;
}

.todo-item.completed {
  opacity: 0.6;
}

.todo-item.completed .todo-title {
  text-decoration: line-through;
}

.todo-content {
  flex: 1;
}

.todo-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.todo-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.todo-priority {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.priority-high {
  background: #fef0f0;
  color: #f56c6c;
}

.priority-medium {
  background: #fdf6ec;
  color: #e6a23c;
}

.priority-low {
  background: #f0f9ff;
  color: #409eff;
}

.todo-time {
  color: #909399;
}

.create-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recent-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  font-size: 14px;
}

.recent-action:hover {
  background: #f5f7fa;
}

.recent-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

.status-indicators {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.success {
  background: #67c23a;
}

.status-dot.warning {
  background: #e6a23c;
}

.status-dot.danger {
  background: #f56c6c;
}

.status-dot.info {
  background: #909399;
}

.status-detail {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}

/* 按钮激活状态 */
.active {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}
</style>