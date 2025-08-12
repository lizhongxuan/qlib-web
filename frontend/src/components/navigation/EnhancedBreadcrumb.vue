<template>
  <div class="enhanced-breadcrumb">
    <div class="breadcrumb-container">
      <!-- 返回按钮 -->
      <el-button
        v-if="canGoBack"
        circle
        size="small"
        @click="goBack"
        class="back-button"
      >
        <el-icon><ArrowLeft /></el-icon>
      </el-button>

      <!-- 面包屑导航 -->
      <el-breadcrumb separator="/" class="breadcrumb-nav">
        <el-breadcrumb-item
          v-for="(item, index) in breadcrumbItems"
          :key="item.path || index"
          :class="{ 'current-page': index === breadcrumbItems.length - 1 }"
        >
          <div class="breadcrumb-item-content">
            <el-icon v-if="item.icon">
              <component :is="item.icon" />
            </el-icon>
            
            <!-- 可点击的面包屑项 -->
            <span
              v-if="item.path && index < breadcrumbItems.length - 1"
              @click="navigateToPath(item.path)"
              class="breadcrumb-link"
            >
              {{ item.title }}
            </span>
            
            <!-- 当前页面项 -->
            <span v-else class="breadcrumb-current">
              {{ item.title }}
            </span>
            
            <!-- 页面状态指示器 -->
            <div v-if="item.status" class="page-status" :class="`status-${item.status}`">
              <el-icon v-if="item.status === 'loading'"><Loading /></el-icon>
              <el-icon v-else-if="item.status === 'error'"><Warning /></el-icon>
              <el-icon v-else-if="item.status === 'success'"><Check /></el-icon>
            </div>
            
            <!-- 页面标签 -->
            <el-tag
              v-if="item.tag"
              :type="item.tag.type"
              size="small"
              class="page-tag"
            >
              {{ item.tag.text }}
            </el-tag>
          </div>
        </el-breadcrumb-item>
      </el-breadcrumb>

      <!-- 页面操作菜单 -->
      <div class="breadcrumb-actions">
        <!-- 页面收藏 -->
        <el-button
          circle
          size="small"
          :type="isCurrentPageBookmarked ? 'primary' : 'default'"
          @click="toggleBookmark"
        >
          <el-icon>
            <Star v-if="isCurrentPageBookmarked" />
            <StarFilled v-else />
          </el-icon>
        </el-button>

        <!-- 页面分享 -->
        <el-dropdown @command="handleShareCommand">
          <el-button circle size="small">
            <el-icon><Share /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="copy-url">
                <el-icon><Link /></el-icon>
                复制链接
              </el-dropdown-item>
              <el-dropdown-item command="bookmark">
                <el-icon><Collection /></el-icon>
                添加书签
              </el-dropdown-item>
              <el-dropdown-item command="new-tab">
                <el-icon><FolderOpened /></el-icon>
                新标签页打开
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 页面选项菜单 -->
        <el-dropdown @command="handlePageCommand">
          <el-button circle size="small">
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="refresh">
                <el-icon><Refresh /></el-icon>
                刷新页面
              </el-dropdown-item>
              <el-dropdown-item command="print">
                <el-icon><Printer /></el-icon>
                打印页面
              </el-dropdown-item>
              <el-dropdown-item command="export">
                <el-icon><Download /></el-icon>
                导出数据
              </el-dropdown-item>
              <el-dropdown-item divided command="settings">
                <el-icon><Setting /></el-icon>
                页面设置
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 子导航栏 -->
    <div v-if="showSubNavigation && subNavigationItems.length > 0" class="sub-navigation">
      <el-menu
        :default-active="activeSubNav"
        mode="horizontal"
        class="sub-nav-menu"
        @select="handleSubNavSelect"
      >
        <el-menu-item
          v-for="item in subNavigationItems"
          :key="item.key"
          :index="item.key"
          :disabled="item.disabled"
        >
          <el-icon v-if="item.icon">
            <component :is="item.icon" />
          </el-icon>
          {{ item.title }}
          <el-badge
            v-if="item.badge"
            :value="item.badge"
            :type="item.badgeType || 'primary'"
            class="sub-nav-badge"
          />
        </el-menu-item>
      </el-menu>
      
      <!-- 子导航操作 -->
      <div class="sub-nav-actions">
        <el-input
          v-if="showSearch"
          v-model="searchQuery"
          placeholder="搜索..."
          size="small"
          style="width: 200px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-button
          v-for="action in subNavigationActions"
          :key="action.key"
          :type="action.type"
          :size="action.size || 'small'"
          @click="action.handler"
          :loading="action.loading"
        >
          <el-icon v-if="action.icon">
            <component :is="action.icon" />
          </el-icon>
          {{ action.title }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { useBookmarkStore } from '@/stores/bookmark'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Loading, Warning, Check, Star, StarFilled, Share,
  Link, Collection, FolderOpened, MoreFilled, Refresh, Printer,
  Download, Setting, Search
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const navigationStore = useNavigationStore()
const bookmarkStore = useBookmarkStore()

// 响应式数据
const searchQuery = ref('')

// 计算属性
const breadcrumbItems = computed(() => navigationStore.breadcrumbItems)
const canGoBack = computed(() => navigationStore.canGoBack)
const isCurrentPageBookmarked = computed(() => 
  bookmarkStore.isBookmarked(route.path)
)
const subNavigationItems = computed(() => navigationStore.subNavigationItems)
const subNavigationActions = computed(() => navigationStore.subNavigationActions)
const activeSubNav = computed(() => navigationStore.activeSubNav)
const showSubNavigation = computed(() => navigationStore.showSubNavigation)
const showSearch = computed(() => navigationStore.showSubNavSearch)

// 监听路由变化，更新面包屑
watch(() => route.path, (newPath) => {
  navigationStore.updateBreadcrumb(newPath, route.meta, route.params, route.query)
}, { immediate: true })

// 方法
const goBack = () => {
  if (navigationStore.hasNavigationHistory) {
    router.go(-1)
  } else {
    // 智能返回到合适的上级页面
    const parentPath = getParentPath(route.path)
    if (parentPath) {
      router.push(parentPath)
    }
  }
}

const navigateToPath = (path: string) => {
  router.push(path)
}

const toggleBookmark = () => {
  const currentPage = {
    path: route.path,
    title: route.meta?.title as string || '未命名页面',
    icon: route.meta?.icon as string,
    params: route.params,
    query: route.query
  }
  
  if (isCurrentPageBookmarked.value) {
    bookmarkStore.removeBookmark(route.path)
    ElMessage.success('已从书签中移除')
  } else {
    bookmarkStore.addBookmark(currentPage)
    ElMessage.success('已添加到书签')
  }
}

const handleShareCommand = (command: string) => {
  switch (command) {
    case 'copy-url':
      const url = window.location.href
      navigator.clipboard.writeText(url).then(() => {
        ElMessage.success('链接已复制到剪贴板')
      })
      break
      
    case 'bookmark':
      toggleBookmark()
      break
      
    case 'new-tab':
      window.open(window.location.href, '_blank')
      break
  }
}

const handlePageCommand = (command: string) => {
  switch (command) {
    case 'refresh':
      window.location.reload()
      break
      
    case 'print':
      window.print()
      break
      
    case 'export':
      navigationStore.exportCurrentPageData()
      break
      
    case 'settings':
      // 打开页面设置对话框
      navigationStore.openPageSettings()
      break
  }
}

const handleSubNavSelect = (key: string) => {
  navigationStore.setActiveSubNav(key)
  
  // 如果子导航项有路由，则导航到该路由
  const item = subNavigationItems.value.find(item => item.key === key)
  if (item?.route) {
    router.push(item.route)
  }
  
  // 如果有自定义处理函数，则执行
  if (item?.handler) {
    item.handler()
  }
}

const handleSearch = (query: string) => {
  navigationStore.handleSubNavSearch(query)
}

const getParentPath = (currentPath: string) => {
  const pathSegments = currentPath.split('/').filter(segment => segment)
  
  // 根据路径规则推断父级路径
  if (pathSegments.length <= 1) return '/dashboard'
  
  const parentSegments = pathSegments.slice(0, -1)
  return '/' + parentSegments.join('/')
}
</script>

<style scoped>
.enhanced-breadcrumb {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.breadcrumb-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  min-height: 48px;
}

.back-button {
  color: #606266;
  border-color: #dcdfe6;
}

.back-button:hover {
  color: #409eff;
  border-color: #409eff;
}

.breadcrumb-nav {
  flex: 1;
  font-size: 14px;
}

.breadcrumb-item-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.breadcrumb-link {
  color: #606266;
  cursor: pointer;
  transition: color 0.3s ease;
}

.breadcrumb-link:hover {
  color: #409eff;
}

.breadcrumb-current {
  color: #303133;
  font-weight: 500;
}

.current-page {
  color: #303133;
}

.page-status {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.status-loading {
  color: #409eff;
}

.status-error {
  color: #f56c6c;
}

.status-success {
  color: #67c23a;
}

.page-tag {
  margin-left: 4px;
}

.breadcrumb-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #f8f9fa;
  border-top: 1px solid #e4e7ed;
}

.sub-nav-menu {
  flex: 1;
  border-bottom: none;
  background: transparent;
}

.sub-nav-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  color: #606266;
  border-bottom: 2px solid transparent;
  position: relative;
}

.sub-nav-menu .el-menu-item:hover {
  color: #409eff;
}

.sub-nav-menu .el-menu-item.is-active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.sub-nav-badge {
  position: absolute;
  top: 8px;
  right: 4px;
}

.sub-nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .breadcrumb-container {
    padding: 8px 16px;
    flex-wrap: wrap;
  }
  
  .breadcrumb-actions {
    order: 1;
    width: 100%;
    justify-content: flex-end;
    margin-top: 8px;
  }
  
  .sub-navigation {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }
  
  .sub-nav-actions {
    width: 100%;
    justify-content: center;
  }
  
  .sub-nav-menu {
    width: 100%;
  }
  
  .sub-nav-menu .el-menu-item {
    flex: 1;
    text-align: center;
  }
}
</style>