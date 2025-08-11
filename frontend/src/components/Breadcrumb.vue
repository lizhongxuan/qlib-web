<template>
  <el-breadcrumb class="app-breadcrumb" separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in breadcrumbs"
      :key="index"
      :to="item.path ? { path: item.path } : undefined"
    >
      <el-icon v-if="item.icon" class="breadcrumb-icon">
        <component :is="item.icon" />
      </el-icon>
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  HomeFilled, 
  DataAnalysis, 
  Plus, 
  List, 
  View, 
  Setting 
} from '@element-plus/icons-vue'

interface BreadcrumbItem {
  title: string
  path?: string
  icon?: any
}

const route = useRoute()

// 路由到面包屑的映射
const routeBreadcrumbMap: Record<string, BreadcrumbItem[]> = {
  '/': [
    { title: '首页', icon: HomeFilled }
  ],
  '/dashboard': [
    { title: '仪表盘', icon: HomeFilled }
  ],
  '/experiments/new': [
    { title: '仪表盘', path: '/dashboard', icon: HomeFilled },
    { title: '新建实验', icon: Plus }
  ],
  '/experiments': [
    { title: '仪表盘', path: '/dashboard', icon: HomeFilled },
    { title: '历史记录', icon: List }
  ],
  '/settings': [
    { title: '仪表盘', path: '/dashboard', icon: HomeFilled },
    { title: '系统设置', icon: Setting }
  ]
}

const breadcrumbs = computed(() => {
  const path = route.path
  
  // 检查是否是实验详情页面
  const experimentDetailMatch = path.match(/^\/experiments\/([^/]+)$/)
  if (experimentDetailMatch) {
    const experimentId = experimentDetailMatch[1]
    return [
      { title: '仪表盘', path: '/dashboard', icon: HomeFilled },
      { title: '历史记录', path: '/experiments', icon: List },
      { title: `实验详情 - ${experimentId.substring(0, 8)}...`, icon: View }
    ]
  }
  
  // 使用预定义的映射
  return routeBreadcrumbMap[path] || [
    { title: '仪表盘', path: '/dashboard', icon: HomeFilled }
  ]
})
</script>

<style scoped>
.app-breadcrumb {
  line-height: 50px;
  font-size: 14px;
}

.breadcrumb-icon {
  margin-right: 4px;
  vertical-align: middle;
}

:deep(.el-breadcrumb__item) {
  font-weight: 400;
}

:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

:deep(.el-breadcrumb__item:not(:last-child) .el-breadcrumb__inner:hover) {
  color: var(--el-color-primary);
  cursor: pointer;
}
</style>