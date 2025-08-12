import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface TodoItem {
  id: string
  title: string
  priority: 'high' | 'medium' | 'low'
  dueTime: number
  completed: boolean
  actionUrl?: string
}

interface RecentAction {
  id: string
  title: string
  icon: string
  lastUsed: number
  actionUrl?: string
  callback?: () => void
}

interface SystemStatus {
  runningTasks: number
  activeDeployments: number
  services: Record<string, 'healthy' | 'warning' | 'error'>
}

export const useQuickActionStore = defineStore('quickAction', () => {
  // 状态
  const todoItems = ref<TodoItem[]>([])
  const recentActions = ref<RecentAction[]>([])
  const systemStatus = ref<SystemStatus>({
    runningTasks: 2,
    activeDeployments: 1,
    services: {
      training: 'healthy',
      deployment: 'healthy',
      data: 'healthy'
    }
  })
  const actionUsageCount = ref<Record<string, number>>({})

  // 计算属性
  const pendingActionsCount = computed(() => {
    return todoItems.value.filter(item => !item.completed).length +
           systemStatus.value.runningTasks
  })

  const highPriorityTodos = computed(() => {
    return todoItems.value.filter(item => !item.completed && item.priority === 'high')
  })

  const overdueTodos = computed(() => {
    const now = Date.now()
    return todoItems.value.filter(item => !item.completed && item.dueTime < now)
  })

  // 动作
  const initializeQuickActions = () => {
    // 初始化待办事项
    todoItems.value = [
      {
        id: 'review-factor-1',
        title: '检查动量因子表现',
        priority: 'high',
        dueTime: Date.now() + 3600000, // 1小时后
        completed: false,
        actionUrl: '/factors#library'
      },
      {
        id: 'complete-training',
        title: '完成模型训练配置',
        priority: 'medium',
        dueTime: Date.now() + 86400000, // 1天后
        completed: false,
        actionUrl: '/training'
      },
      {
        id: 'analyze-backtest',
        title: '分析上周回测结果',
        priority: 'low',
        dueTime: Date.now() + 172800000, // 2天后
        completed: false,
        actionUrl: '/results'
      }
    ]

    // 初始化最近操作
    recentActions.value = [
      {
        id: 'create-factor',
        title: '创建新因子',
        icon: 'MagicStick',
        lastUsed: Date.now() - 1800000, // 30分钟前
        actionUrl: '/factors'
      },
      {
        id: 'start-training',
        title: '开始模型训练',
        icon: 'Cpu',
        lastUsed: Date.now() - 3600000, // 1小时前
        actionUrl: '/training'
      },
      {
        id: 'view-results',
        title: '查看分析结果',
        icon: 'DataAnalysis',
        lastUsed: Date.now() - 7200000, // 2小时前
        actionUrl: '/results'
      }
    ]
  }

  const recordPanelOpen = () => {
    // 记录面板打开
  }

  const recordActionUsed = (actionId: string) => {
    actionUsageCount.value[actionId] = (actionUsageCount.value[actionId] || 0) + 1
    
    // 更新最近操作
    const existingIndex = recentActions.value.findIndex(action => action.id === actionId)
    if (existingIndex > -1) {
      recentActions.value[existingIndex].lastUsed = Date.now()
      // 将最近使用的移到前面
      const action = recentActions.value.splice(existingIndex, 1)[0]
      recentActions.value.unshift(action)
    }
  }

  const updateTodoStatus = (todoId: string, completed: boolean) => {
    const todo = todoItems.value.find(item => item.id === todoId)
    if (todo) {
      todo.completed = completed
    }
  }

  const addTodoItem = (todo: Omit<TodoItem, 'id'>) => {
    const newTodo: TodoItem = {
      ...todo,
      id: `todo-${Date.now()}`
    }
    todoItems.value.push(newTodo)
  }

  const removeTodoItem = (todoId: string) => {
    const index = todoItems.value.findIndex(item => item.id === todoId)
    if (index > -1) {
      todoItems.value.splice(index, 1)
    }
  }

  const emergencyStopAllTasks = async () => {
    // 模拟停止所有任务
    await new Promise(resolve => setTimeout(resolve, 1000))
    systemStatus.value.runningTasks = 0
    systemStatus.value.services.training = 'warning'
  }

  const startDataBackup = async () => {
    // 模拟开始数据备份
    await new Promise(resolve => setTimeout(resolve, 500))
    addTodoItem({
      title: '数据备份进行中',
      priority: 'medium',
      dueTime: Date.now() + 1800000, // 30分钟后完成
      completed: false
    })
  }

  const syncModels = async () => {
    // 模拟模型同步
    await new Promise(resolve => setTimeout(resolve, 1500))
    // 可以添加同步完成的通知
  }

  const updateSystemStatus = (updates: Partial<SystemStatus>) => {
    Object.assign(systemStatus.value, updates)
  }

  const getActionSuggestions = () => {
    const suggestions = []
    
    // 根据当前系统状态提供建议
    if (systemStatus.value.runningTasks > 0) {
      suggestions.push({
        title: '监控运行任务',
        description: `有 ${systemStatus.value.runningTasks} 个任务正在运行`,
        action: 'monitor-tasks',
        priority: 'high'
      })
    }
    
    if (overdueTodos.value.length > 0) {
      suggestions.push({
        title: '处理逾期任务',
        description: `有 ${overdueTodos.value.length} 个任务已逾期`,
        action: 'handle-overdue',
        priority: 'high'
      })
    }
    
    if (highPriorityTodos.value.length > 0) {
      suggestions.push({
        title: '完成高优先级任务',
        description: `有 ${highPriorityTodos.value.length} 个高优先级任务待处理`,
        action: 'handle-high-priority',
        priority: 'medium'
      })
    }
    
    return suggestions
  }

  return {
    // 状态
    todoItems,
    recentActions,
    systemStatus,
    
    // 计算属性
    pendingActionsCount,
    highPriorityTodos,
    overdueTodos,
    
    // 动作
    initializeQuickActions,
    recordPanelOpen,
    recordActionUsed,
    updateTodoStatus,
    addTodoItem,
    removeTodoItem,
    emergencyStopAllTasks,
    startDataBackup,
    syncModels,
    updateSystemStatus,
    getActionSuggestions
  }
})