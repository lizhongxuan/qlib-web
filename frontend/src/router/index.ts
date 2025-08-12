import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 导入路由守卫
import { smartNavigationGuard } from './guards/smart-navigation-guard'
import { dependencyCheckGuard } from './guards/dependency-check-guard'
import { dataPreloadGuard } from './guards/data-preload-guard'

// 路由懒加载
const Layout = () => import('@/views/Layout.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const CreateExperiment = () => import('@/views/CreateExperiment.vue')
const ExperimentHistory = () => import('@/views/ExperimentHistory.vue')
const ExperimentDetail = () => import('@/views/ExperimentDetail.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const TeamManagement = () => import('@/views/TeamManagement.vue')

// 新增页面路由懒加载
const FactorDevelopment = () => import('@/views/FactorDevelopment.vue')
const EnhancedModelTraining = () => import('@/views/EnhancedModelTraining.vue')
const TrainingManagement = () => import('@/views/TrainingManagement.vue')
const StrategyBacktest = () => import('@/views/StrategyBacktest.vue')
const ResultsAnalysis = () => import('@/views/ResultsAnalysis.vue')
const StrategyDeployment = () => import('@/views/StrategyDeployment.vue')

const routes: Array<RouteRecordRaw> = [
  // 认证路由
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresGuest: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: {
      title: '注册',
      requiresGuest: true
    }
  },
  
  // 主应用路由
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
          title: '仪表盘',
          icon: 'DataLine'
        }
      },
      {
        path: '/factors',
        name: 'FactorDevelopment',
        component: FactorDevelopment,
        meta: {
          title: '因子开发',
          icon: 'MagicStick',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: false,
          enableDataPreload: true,
          workflowStep: 'factor-development'
        }
      },
      {
        path: '/training',
        name: 'EnhancedModelTraining',
        component: EnhancedModelTraining,
        meta: {
          title: '模型训练',
          icon: 'Cpu',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'model-training'
        }
      },
      {
        path: '/training-management',
        name: 'TrainingManagement',
        component: TrainingManagement,
        meta: {
          title: '训练管理',
          icon: 'List'
        }
      },
      {
        path: '/backtest',
        name: 'StrategyBacktest',
        component: StrategyBacktest,
        meta: {
          title: '策略回测',
          icon: 'TrendCharts',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'strategy-backtest'
        }
      },
      {
        path: '/results',
        name: 'ResultsAnalysis',
        component: ResultsAnalysis,
        meta: {
          title: '结果分析',
          icon: 'DataAnalysis',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'results-analysis'
        }
      },
      {
        path: '/deployment',
        name: 'StrategyDeployment',
        component: StrategyDeployment,
        meta: {
          title: '策略部署',
          icon: 'Upload',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'strategy-deployment'
        }
      },
      {
        path: '/create',
        name: 'CreateExperiment',
        component: CreateExperiment,
        meta: {
          title: '新建实验(旧)',
          icon: 'Plus'
        }
      },
      {
        path: '/history',
        name: 'ExperimentHistory',
        component: ExperimentHistory,
        meta: {
          title: '历史记录(旧)',
          icon: 'Clock'
        }
      },
      {
        path: '/experiment/:id',
        name: 'ExperimentDetail',
        component: ExperimentDetail,
        meta: {
          title: '实验详情',
          icon: 'Document'
        }
      },
      {
        path: '/teams',
        name: 'TeamManagement',
        component: TeamManagement,
        meta: {
          title: '团队管理',
          icon: 'Avatar'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫（执行顺序很重要）
router.beforeEach(async (to, from, next) => {
  try {
    // 1. 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - Qlib Web Console`
    }
    
    // 2. 认证检查（最高优先级）
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    const isAuthenticated = authStore.isAuthenticated
    
    // 需要认证但未登录
    if (to.meta?.requiresAuth && !isAuthenticated) {
      next('/login')
      return
    }
    
    // 已登录但访问guest页面
    if (to.meta?.requiresGuest && isAuthenticated) {
      next('/dashboard')
      return
    }
    
    // 3. 智能导航守卫
    if (to.meta?.enableSmartNavigation !== false) {
      const smartNavResult = await smartNavigationGuard(to, from, (result) => {
        if (result === false) {
          return next(false)
        } else if (typeof result === 'string') {
          return next(result)
        }
        // 继续执行后续守卫
      })
      
      // 如果智能导航守卫决定阻止导航，直接返回
      if (smartNavResult === false) {
        return
      }
      
      // 如果智能导航守卫重定向到其他页面
      if (typeof smartNavResult === 'string' && smartNavResult !== to.path) {
        next(smartNavResult)
        return
      }
    }
    
    // 4. 依赖检查守卫
    if (to.meta?.enableDependencyCheck === true) {
      await dependencyCheckGuard(to, from, (result) => {
        if (result === false) {
          return next(false)
        } else if (typeof result === 'string') {
          return next(result)
        }
        // 继续执行
      })
    }
    
    // 5. 数据预加载守卫
    if (to.meta?.enableDataPreload === true) {
      await dataPreloadGuard(to, from, (result) => {
        if (result === false) {
          return next(false)
        } else if (typeof result === 'string') {
          return next(result)
        }
        // 继续执行
      })
    }
    
    // 6. 工作流状态更新
    if (to.meta?.workflowStep) {
      const { useWorkflowStore } = await import('@/stores/workflow')
      const workflowStore = useWorkflowStore()
      
      // 如果工作流激活，更新当前步骤
      if (workflowStore.isWorkflowActive) {
        const stepIndex = workflowStore.workflowSteps.findIndex(
          step => step.key === to.meta.workflowStep
        )
        if (stepIndex > -1) {
          workflowStore.jumpToStep(stepIndex)
        }
      }
    }
    
    // 7. 记录页面访问
    const { useNavigationStore } = await import('@/stores/navigation')
    const navigationStore = useNavigationStore()
    navigationStore.recordPageVisit(to.path, to.meta?.title as string || '未知页面', to.meta?.icon as string)
    
    // 所有守卫通过，允许导航
    next()
    
  } catch (error) {
    console.error('路由守卫执行错误:', error)
    // 发生错误时允许导航，但记录错误
    next()
  }
})

// 路由后置守卫
router.afterEach((to, from) => {
  // 1. 更新导航状态
  const { useNavigationStore } = require('@/stores/navigation')
  const navigationStore = useNavigationStore()
  navigationStore.updateBreadcrumb(to.path, to.meta, to.params, to.query)
  
  // 2. 清除过期缓存
  if (Math.random() < 0.1) { // 10% 概率执行清理
    const { clearExpiredCache } = require('./guards/data-preload-guard')
    clearExpiredCache()
  }
  
  // 3. 记录页面性能
  const navigationEndTime = performance.now()
  const navigationStartTime = (window as any).navigationStartTime || navigationEndTime
  const duration = navigationEndTime - navigationStartTime
  
  if (duration > 1000) {
    console.warn(`页面导航耗时较长: ${to.path} (${duration.toFixed(1)}ms)`)
  }
  
  // 重置导航开始时间
  ;(window as any).navigationStartTime = performance.now()
})

export default router