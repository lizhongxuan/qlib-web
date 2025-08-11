import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由懒加载
const Layout = () => import('@/views/Layout.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const CreateExperiment = () => import('@/views/CreateExperiment.vue')
const ExperimentHistory = () => import('@/views/ExperimentHistory.vue')
const ExperimentDetail = () => import('@/views/ExperimentDetail.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const TeamManagement = () => import('@/views/TeamManagement.vue')

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
        path: '/create',
        name: 'CreateExperiment',
        component: CreateExperiment,
        meta: {
          title: '新建实验',
          icon: 'Plus'
        }
      },
      {
        path: '/history',
        name: 'ExperimentHistory',
        component: ExperimentHistory,
        meta: {
          title: '历史记录',
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

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - Qlib Web Console`
  }
  
  // 动态导入认证store以避免循环依赖
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  
  // 检查认证状态
  const isAuthenticated = authStore.isAuthenticated
  
  // 需要认证但未登录
  if (to.meta?.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }
  
  // 已登录但访问guest页面（如登录、注册）
  if (to.meta?.requiresGuest && isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router