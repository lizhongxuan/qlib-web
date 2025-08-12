import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

interface BreadcrumbItem {
  title: string
  path?: string
  icon?: string
  status?: 'loading' | 'error' | 'success'
  tag?: {
    text: string
    type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  }
}

interface SubNavigationItem {
  key: string
  title: string
  icon?: string
  route?: string
  handler?: () => void
  disabled?: boolean
  badge?: number
  badgeType?: string
}

interface SubNavigationAction {
  key: string
  title: string
  icon?: string
  type?: string
  size?: string
  handler: () => void
  loading?: boolean
}

interface RecentPage {
  path: string
  title: string
  icon?: string
  visitTime: number
}

interface ContextInfo {
  currentPage: string
  unsavedChanges: boolean
  runningTasks: number
}

export const useNavigationStore = defineStore('navigation', () => {
  // 状态
  const currentPath = ref('')
  const breadcrumbItems = ref<BreadcrumbItem[]>([])
  const navigationHistory = ref<string[]>([])
  const recentPages = ref<RecentPage[]>([])
  const showWorkflowProgress = ref(false)
  const subNavigationItems = ref<SubNavigationItem[]>([])
  const subNavigationActions = ref<SubNavigationAction[]>([])
  const activeSubNav = ref('')
  const showSubNavigation = ref(false)
  const showSubNavSearch = ref(false)
  
  // 计算属性
  const canGoBack = computed(() => navigationHistory.value.length > 0)
  const hasNavigationHistory = computed(() => navigationHistory.value.length > 0)
  
  const contextInfo = computed((): ContextInfo => ({
    currentPage: getCurrentPageTitle(),
    unsavedChanges: checkUnsavedChanges(),
    runningTasks: getRunningTasksCount()
  }))

  // 动作
  const updateCurrentPath = (path: string) => {
    if (currentPath.value !== path) {
      if (currentPath.value) {
        navigationHistory.value.push(currentPath.value)
        // 限制历史记录长度
        if (navigationHistory.value.length > 10) {
          navigationHistory.value = navigationHistory.value.slice(-10)
        }
      }
      currentPath.value = path
    }
  }

  const updateBreadcrumb = (path: string, meta: any, params: any, query: any) => {
    const items: BreadcrumbItem[] = []
    
    // 根路径
    if (path !== '/dashboard') {
      items.push({
        title: '仪表盘',
        path: '/dashboard',
        icon: 'Odometer'
      })
    }
    
    // 根据路径生成面包屑
    const pathSegments = path.split('/').filter(segment => segment)
    
    pathSegments.forEach((segment, index) => {
      const segmentPath = '/' + pathSegments.slice(0, index + 1).join('/')
      const isLast = index === pathSegments.length - 1
      
      let title = segment
      let icon = ''
      
      // 路径映射
      switch (segment) {
        case 'factors':
          title = '因子开发'
          icon = 'MagicStick'
          break
        case 'training':
          title = '模型训练'
          icon = 'Cpu'
          break
        case 'training-management':
          title = '训练管理'
          icon = 'DataBoard'
          break
        case 'backtest':
          title = '策略回测'
          icon = 'TrendCharts'
          break
        case 'results':
          title = '结果分析'
          icon = 'DataAnalysis'
          break
        case 'deployment':
          title = '策略部署'
          icon = 'Upload'
          break
        default:
          title = meta?.title || segment
          icon = meta?.icon || ''
      }
      
      items.push({
        title,
        path: isLast ? undefined : segmentPath,
        icon,
        status: isLast ? getPageStatus(segmentPath) : undefined,
        tag: isLast ? getPageTag(segmentPath) : undefined
      })
    })
    
    breadcrumbItems.value = items
    updateSubNavigation(path, meta)
  }

  const updateSubNavigation = (path: string, meta: any) => {
    const items: SubNavigationItem[] = []
    const actions: SubNavigationAction[] = []
    
    // 根据当前页面设置子导航
    switch (path) {
      case '/factors':
        items.push(
          { key: 'ai-assistant', title: 'AI助手', icon: 'MagicStick', route: '/factors#ai' },
          { key: 'editor', title: '因子编辑器', icon: 'Edit', route: '/factors#editor' },
          { key: 'library', title: '因子库', icon: 'Collection', route: '/factors#library' },
          { key: 'validation', title: '因子验证', icon: 'Check', route: '/factors#validation' },
          { key: 'preview', title: '效果预览', icon: 'View', route: '/factors#preview' }
        )
        actions.push(
          { key: 'new-factor', title: '新建因子', icon: 'Plus', type: 'primary', handler: () => {} },
          { key: 'import-factor', title: '导入因子', icon: 'Upload', handler: () => {} }
        )
        showSubNavSearch.value = true
        break
        
      case '/training':
        items.push(
          { key: 'config', title: '训练配置', icon: 'Setting', route: '/training#config' },
          { key: 'monitor', title: '训练监控', icon: 'Monitor', route: '/training#monitor' },
          { key: 'optimization', title: '参数优化', icon: 'Tools', route: '/training#optimization' }
        )
        actions.push(
          { key: 'start-training', title: '开始训练', icon: 'VideoPlay', type: 'primary', handler: () => {} },
          { key: 'load-template', title: '加载模板', icon: 'Document', handler: () => {} }
        )
        showSubNavSearch.value = false
        break
        
      case '/backtest':
        items.push(
          { key: 'config', title: '回测配置', icon: 'Setting', route: '/backtest#config' },
          { key: 'execution', title: '执行监控', icon: 'Monitor', route: '/backtest#execution' },
          { key: 'results', title: '结果分析', icon: 'DataAnalysis', route: '/backtest#results' }
        )
        actions.push(
          { key: 'start-backtest', title: '开始回测', icon: 'VideoPlay', type: 'primary', handler: () => {} },
          { key: 'save-config', title: '保存配置', icon: 'DocumentAdd', handler: () => {} }
        )
        showSubNavSearch.value = false
        break
        
      case '/results':
        items.push(
          { key: 'returns', title: '收益分析', icon: 'TrendCharts' },
          { key: 'risk', title: '风险分析', icon: 'Warning' },
          { key: 'positions', title: '持仓分析', icon: 'PieChart' },
          { key: 'trading', title: '交易分析', icon: 'DataBoard' },
          { key: 'suggestions', title: 'AI建议', icon: 'MagicStick' }
        )
        actions.push(
          { key: 'export-report', title: '导出报告', icon: 'Download', handler: () => {} },
          { key: 'compare-results', title: '结果对比', icon: 'DataAnalysis', handler: () => {} }
        )
        showSubNavSearch.value = true
        break
        
      case '/deployment':
        items.push(
          { key: 'wizard', title: '部署向导', icon: 'Guide' },
          { key: 'monitoring', title: '实时监控', icon: 'Monitor' },
          { key: 'management', title: '部署管理', icon: 'Setting' }
        )
        actions.push(
          { key: 'new-deployment', title: '新建部署', icon: 'Plus', type: 'primary', handler: () => {} },
          { key: 'emergency-stop', title: '紧急停止', icon: 'Close', type: 'danger', handler: () => {} }
        )
        showSubNavSearch.value = false
        break
        
      default:
        showSubNavSearch.value = false
    }
    
    subNavigationItems.value = items
    subNavigationActions.value = actions
    showSubNavigation.value = items.length > 0
    
    // 设置默认激活的子导航
    if (items.length > 0) {
      activeSubNav.value = items[0].key
    }
  }

  const navigateTo = (path: string) => {
    // 在导航前检查是否有未保存的更改
    if (checkUnsavedChanges()) {
      // 这里可以显示确认对话框
      console.log('检测到未保存的更改')
    }
    
    updateCurrentPath(path)
  }

  const recordPageVisit = (path: string, title: string, icon?: string) => {
    const existingIndex = recentPages.value.findIndex(page => page.path === path)
    
    if (existingIndex > -1) {
      // 更新访问时间
      recentPages.value[existingIndex].visitTime = Date.now()
    } else {
      // 添加新记录
      recentPages.value.unshift({
        path,
        title,
        icon,
        visitTime: Date.now()
      })
      
      // 限制记录数量
      if (recentPages.value.length > 10) {
        recentPages.value = recentPages.value.slice(0, 10)
      }
    }
  }

  const setActiveSubNav = (key: string) => {
    activeSubNav.value = key
  }

  const handleSubNavSearch = (query: string) => {
    // 根据当前页面处理搜索
    console.log('子导航搜索:', query)
  }

  const recordNavAssistantOpen = () => {
    // 记录导航助手使用
  }

  const recordSuggestionUsed = (suggestionId: string) => {
    // 记录建议使用情况
  }

  const recordRecommendationUsed = (recId: string) => {
    // 记录推荐使用情况
  }

  const dismissRecommendation = (recId: string) => {
    // 忽略推荐
  }

  const exportCurrentPageData = () => {
    ElMessage.success('数据导出已开始')
  }

  const openPageSettings = () => {
    ElMessage.info('页面设置功能开发中')
  }

  const hideWorkflowProgress = () => {
    showWorkflowProgress.value = false
  }

  // 辅助函数
  const getCurrentPageTitle = () => {
    return breadcrumbItems.value[breadcrumbItems.value.length - 1]?.title || '未知页面'
  }

  const checkUnsavedChanges = () => {
    // 检查当前页面是否有未保存的更改
    return false
  }

  const getRunningTasksCount = () => {
    // 获取运行中的任务数量
    return 0
  }

  const getPageStatus = (path: string) => {
    // 根据路径获取页面状态
    return undefined
  }

  const getPageTag = (path: string) => {
    // 根据路径获取页面标签
    return undefined
  }

  return {
    // 状态
    currentPath,
    breadcrumbItems,
    recentPages,
    showWorkflowProgress,
    subNavigationItems,
    subNavigationActions,
    activeSubNav,
    showSubNavigation,
    showSubNavSearch,
    
    // 计算属性
    canGoBack,
    hasNavigationHistory,
    contextInfo,
    
    // 动作
    updateCurrentPath,
    updateBreadcrumb,
    navigateTo,
    recordPageVisit,
    setActiveSubNav,
    handleSubNavSearch,
    recordNavAssistantOpen,
    recordSuggestionUsed,
    recordRecommendationUsed,
    dismissRecommendation,
    exportCurrentPageData,
    openPageSettings,
    hideWorkflowProgress
  }
})