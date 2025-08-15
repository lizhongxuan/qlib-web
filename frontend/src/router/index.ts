import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 导入路由守卫
import { smartNavigationGuard } from './guards/smart-navigation-guard'
import { dependencyCheckGuard } from './guards/dependency-check-guard'
import { dataPreloadGuard } from './guards/data-preload-guard'

// 路由懒加载
const Layout = () => import('@/views/Layout.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
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

// Qlib专业页面路由懒加载
const QlibDashboard = () => import('@/views/QlibDashboard.vue')
const QlibDataBrowser = () => import('@/views/QlibDataBrowser.vue')
const QlibFactorWorkshop = () => import('@/views/QlibFactorWorkshop.vue')
const QlibModelLab = () => import('@/views/QlibModelLab.vue')
const QlibBacktestEngine = () => import('@/views/QlibBacktestEngine.vue')
const QlibStrategyBuilder = () => import('@/views/QlibStrategyBuilder.vue')

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
          title: '工作流控制台',
          icon: 'DataLine'
        }
      },
      {
        path: '/factors',
        name: 'FactorDevelopment',
        component: FactorDevelopment,
        meta: {
          title: 'AI因子助手',
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
        path: '/teams',
        name: 'TeamManagement',
        component: TeamManagement,
        meta: {
          title: '团队管理',
          icon: 'Avatar'
        }
      },
      
      // Qlib专业页面路由
      {
        path: '/qlib-dashboard',
        name: 'QlibDashboard',
        component: QlibDashboard,
        meta: {
          title: 'Qlib中心',
          icon: 'Monitor',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDataPreload: true,
          workflowStep: 'qlib-overview'
        }
      },
      {
        path: '/qlib-data-browser',
        name: 'QlibDataBrowser',
        component: QlibDataBrowser,
        meta: {
          title: 'Qlib数据浏览器',
          icon: 'DataBoard',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDataPreload: true,
          workflowStep: 'data-exploration'
        }
      },
      {
        path: '/qlib-factor-workshop',
        name: 'QlibFactorWorkshop',
        component: QlibFactorWorkshop,
        meta: {
          title: 'Qlib因子工作坊',
          icon: 'MagicStick',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: false,
          enableDataPreload: true,
          workflowStep: 'qlib-factor-development'
        }
      },
      {
        path: '/qlib-model-lab',
        name: 'QlibModelLab',
        component: QlibModelLab,
        meta: {
          title: 'Qlib模型实验室',
          icon: 'Cpu',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'qlib-model-training'
        }
      },
      {
        path: '/qlib-backtest-engine',
        name: 'QlibBacktestEngine',
        component: QlibBacktestEngine,
        meta: {
          title: 'Qlib回测引擎',
          icon: 'TrendCharts',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'qlib-backtesting'
        }
      },
      {
        path: '/qlib-strategy-builder',
        name: 'QlibStrategyBuilder',
        component: QlibStrategyBuilder,
        meta: {
          title: 'Qlib策略构建器',
          icon: 'Setting',
          requiresAuth: true,
          enableSmartNavigation: true,
          enableDependencyCheck: true,
          enableDataPreload: true,
          workflowStep: 'qlib-strategy-building'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 恢复的路由守卫（优化版本）
router.beforeEach(async (to, from, next) => {
  try {
    // 1. 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - Qlib Web Console`
    }
    
    // 2. 认证检查（最高优先级）
    const { useAuthStore } = await import('@/stores/auth')
    const authStore = useAuthStore()
    
    // 初始化认证状态
    try {
      await authStore.initAuth()
    } catch (authError) {
      console.warn('认证状态初始化失败:', authError)
    }
    
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
    
    // 3. 智能导航守卫（仅在需要时启用）
    if (to.meta?.enableSmartNavigation === true) {
      try {
        await smartNavigationGuard(to, from, (result) => {
          if (result === false) {
            return next(false)
          } else if (typeof result === 'string') {
            return next(result)
          }
        })
      } catch (smartNavError) {
        console.warn('智能导航守卫错误:', smartNavError)
      }
    }
    
    // 4. 依赖检查守卫（仅在明确启用时）
    if (to.meta?.enableDependencyCheck === true) {
      try {
        await dependencyCheckGuard(to, from, (result) => {
          if (result === false) {
            return next(false)
          } else if (typeof result === 'string') {
            return next(result)
          }
        })
      } catch (depError) {
        console.warn('依赖检查守卫错误:', depError)
      }
    }
    
    // 5. 数据预加载守卫（仅在明确启用时）
    if (to.meta?.enableDataPreload === true) {
      try {
        await dataPreloadGuard(to, from, (result) => {
          if (result === false) {
            return next(false)
          } else if (typeof result === 'string') {
            return next(result)
          }
        })
      } catch (preloadError) {
        console.warn('数据预加载守卫错误:', preloadError)
      }
    }
    
    // 所有检查通过，允许导航
    next()
    
  } catch (error) {
    console.error('路由守卫执行错误:', error)
    // 发生错误时允许导航，但记录错误
    next()
  }
})

// 简化的路由后置守卫
router.afterEach((to, from) => {
  // 简单的日志记录
  console.log(`导航到: ${to.path}`)
})

export default router