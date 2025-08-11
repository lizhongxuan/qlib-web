<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <el-header class="layout-header">
      <div class="flex items-center justify-between" style="height: 100%; padding: 0 20px;">
        <div class="flex items-center">
          <el-button 
            type="text" 
            @click="toggleSidebar"
            style="margin-right: 16px;"
          >
            <el-icon><Menu /></el-icon>
          </el-button>
          <h1 style="margin: 0; font-size: 20px; color: #303133;">
            Qlib Web Console
          </h1>
        </div>
        <div class="flex items-center">
          <el-tooltip content="切换主题" placement="bottom">
            <el-button type="text" @click="toggleTheme">
              <el-icon><Sunny v-if="isDark" /><Moon v-else /></el-icon>
            </el-button>
          </el-tooltip>
          <el-dropdown>
            <el-button type="text">
              <el-icon><User /></el-icon>
              <span style="margin-left: 8px;">用户</span>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <!-- 主体内容 -->
    <el-container class="layout-content">
      <!-- 侧边栏 -->
      <el-aside :width="sidebarWidth" class="layout-sidebar">
        <el-menu
          :default-active="$route.path"
          :collapse="isCollapsed"
          :unique-opened="true"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataLine /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/create">
            <el-icon><Plus /></el-icon>
            <template #title>新建实验</template>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <template #title>历史记录</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主要内容区域 -->
      <el-main class="layout-main">
        <div class="breadcrumb-container">
          <Breadcrumb />
        </div>
        <div class="main-content">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Menu, Sunny, Moon, User, DataLine, Plus, Clock } from '@element-plus/icons-vue'
import Breadcrumb from '../components/Breadcrumb.vue'

// 响应式状态
const isCollapsed = ref(false)
const isDark = ref(false)

// 计算属性
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '200px')

// 方法
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}

// 生命周期
onMounted(() => {
  // 检查本地存储的主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

// 监听主题变化，保存到本地存储
const stopWatchTheme = watch(isDark, (newVal) => {
  try {
    localStorage.setItem('theme', newVal ? 'dark' : 'light')
  } catch (error) {
    console.warn('无法保存主题设置到本地存储:', error)
  }
})

// 清理监听器
onUnmounted(() => {
  stopWatchTheme()
})
</script>

<style scoped>
.layout-header {
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.layout-sidebar {
  transition: width 0.3s;
}

.layout-main {
  background: #f0f2f5;
  padding: 0;
}

.breadcrumb-container {
  background: #ffffff;
  padding: 0 20px;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.main-content {
  padding: 20px;
}

/* 暗黑主题 */
:global(.dark) .layout-header {
  background: #1f1f1f;
  border-bottom-color: #414243;
}

:global(.dark) .layout-main {
  background: #0a0a0a;
}

:global(.dark) .breadcrumb-container {
  background: #1f1f1f;
  border-bottom-color: #414243;
}
</style>