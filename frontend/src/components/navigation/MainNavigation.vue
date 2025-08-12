<template>
  <div class="main-navigation">
    <div class="nav-header">
      <div class="brand">
        <el-icon class="brand-icon"><TrendCharts /></el-icon>
        <span class="brand-name">Qlib Web</span>
      </div>
      
      <!-- 工作流程进度条 -->
      <WorkflowProgressBar v-if="showWorkflowProgress" />
    </div>

    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      class="nav-menu"
      :ellipsis="false"
      @select="handleMenuSelect"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      
      <el-menu-item index="/factors">
        <el-icon><MagicStick /></el-icon>
        <span>因子开发</span>
        <el-badge
          v-if="factorNotifications > 0"
          :value="factorNotifications"
          class="nav-badge"
        />
      </el-menu-item>
      
      <el-menu-item index="/training">
        <el-icon><cpu /></el-icon>
        <span>模型训练</span>
        <el-badge
          v-if="trainingNotifications > 0"
          :value="trainingNotifications"
          class="nav-badge"
        />
      </el-menu-item>
      
      <el-menu-item index="/training-management">
        <el-icon><DataBoard /></el-icon>
        <span>训练管理</span>
      </el-menu-item>
      
      <el-menu-item index="/backtest">
        <el-icon><TrendCharts /></el-icon>
        <span>策略回测</span>
      </el-menu-item>
      
      <el-menu-item index="/results">
        <el-icon><DataAnalysis /></el-icon>
        <span>结果分析</span>
      </el-menu-item>
      
      <el-menu-item index="/deployment">
        <el-icon><Upload /></el-icon>
        <span>策略部署</span>
        <el-badge
          v-if="deploymentNotifications > 0"
          :value="deploymentNotifications"
          class="nav-badge"
          type="danger"
        />
      </el-menu-item>
    </el-menu>

    <div class="nav-actions">
      <!-- 智能导航助手 -->
      <SmartNavigation />
      
      <!-- 快速操作面板 -->
      <QuickActionPanel />
      
      <!-- 通知中心 -->
      <el-badge :value="totalNotifications" :hidden="totalNotifications === 0">
        <el-button circle @click="showNotifications">
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
      
      <!-- 用户菜单 -->
      <el-dropdown @command="handleUserCommand">
        <div class="user-avatar">
          <el-avatar :size="32" :src="userInfo.avatar" />
          <span class="username">{{ userInfo.name }}</span>
          <el-icon><CaretBottom /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人设置
            </el-dropdown-item>
            <el-dropdown-item command="preferences">
              <el-icon><Setting /></el-icon>
              偏好设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import {
  TrendCharts, Odometer, MagicStick, DataBoard, DataAnalysis,
  Upload, Bell, User, Setting, SwitchButton, CaretBottom
} from '@element-plus/icons-vue'
import WorkflowProgressBar from './WorkflowProgressBar.vue'
import SmartNavigation from './SmartNavigation.vue'
import QuickActionPanel from './QuickActionPanel.vue'

const router = useRouter()
const route = useRoute()
const navigationStore = useNavigationStore()
const notificationStore = useNotificationStore()
const userStore = useUserStore()

// 响应式数据
const activeMenu = ref(route.path)
const showWorkflowProgress = computed(() => navigationStore.showWorkflowProgress)

// 通知计数
const factorNotifications = computed(() => notificationStore.getNotificationCount('factor'))
const trainingNotifications = computed(() => notificationStore.getNotificationCount('training'))
const deploymentNotifications = computed(() => notificationStore.getNotificationCount('deployment'))
const totalNotifications = computed(() => notificationStore.totalUnread)

// 用户信息
const userInfo = computed(() => userStore.userInfo)

// 监听路由变化
watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
  navigationStore.updateCurrentPath(newPath)
})

// 方法
const handleMenuSelect = (index: string) => {
  if (index !== route.path) {
    // 检查是否需要确认离开当前页面
    navigationStore.navigateTo(index)
    router.push(index)
  }
}

const showNotifications = () => {
  notificationStore.toggleNotificationPanel()
}

const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'preferences':
      router.push('/preferences')
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.main-navigation {
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.nav-header {
  display: flex;
  align-items: center;
  margin-right: 32px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 24px;
}

.brand-icon {
  font-size: 24px;
  color: #409eff;
}

.brand-name {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.nav-menu {
  flex: 1;
  border-bottom: none;
  background: transparent;
}

.nav-menu .el-menu-item {
  height: 60px;
  line-height: 60px;
  border-bottom: 3px solid transparent;
  color: #606266;
  font-weight: 500;
  position: relative;
  transition: all 0.3s ease;
}

.nav-menu .el-menu-item:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.nav-menu .el-menu-item.is-active {
  color: #409eff;
  border-bottom-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.nav-badge {
  position: absolute;
  top: 12px;
  right: 8px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 24px;
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.user-avatar:hover {
  background: rgba(64, 158, 255, 0.1);
}

.username {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .nav-menu .el-menu-item span {
    display: none;
  }
  
  .brand-name {
    display: none;
  }
  
  .username {
    display: none;
  }
}

@media (max-width: 768px) {
  .main-navigation {
    padding: 0 16px;
  }
  
  .nav-header {
    margin-right: 16px;
  }
  
  .nav-actions {
    gap: 12px;
    margin-left: 16px;
  }
}
</style>