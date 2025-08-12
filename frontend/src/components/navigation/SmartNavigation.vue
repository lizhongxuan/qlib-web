<template>
  <el-popover
    :visible="showNavAssistant"
    placement="bottom-end"
    :width="400"
    trigger="click"
  >
    <template #reference>
      <el-button circle @click="toggleNavAssistant" :class="{ 'active': showNavAssistant }">
        <el-icon><Guide /></el-icon>
      </el-button>
    </template>

    <div class="smart-navigation">
      <div class="nav-header">
        <h4>智能导航助手</h4>
        <el-button size="small" text @click="showNavAssistant = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>

      <!-- AI对话输入 -->
      <div class="nav-input-section">
        <el-input
          v-model="userQuery"
          placeholder="告诉我你想做什么，我来为你导航..."
          @keyup.enter="handleUserQuery"
          :loading="processingQuery"
        >
          <template #suffix>
            <el-button 
              size="small" 
              type="primary" 
              text
              @click="handleUserQuery"
              :loading="processingQuery"
            >
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>

      <!-- 快速建议 -->
      <div class="quick-suggestions">
        <div class="suggestions-title">快速建议</div>
        <div class="suggestions-list">
          <div
            v-for="suggestion in currentSuggestions"
            :key="suggestion.id"
            class="suggestion-item"
            @click="applySuggestion(suggestion)"
          >
            <div class="suggestion-icon">
              <el-icon :class="suggestion.icon">
                <component :is="suggestion.icon" />
              </el-icon>
            </div>
            <div class="suggestion-content">
              <div class="suggestion-title">{{ suggestion.title }}</div>
              <div class="suggestion-description">{{ suggestion.description }}</div>
            </div>
            <el-icon class="suggestion-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 最近访问 -->
      <div class="recent-pages">
        <div class="section-title">最近访问</div>
        <div class="recent-list">
          <div
            v-for="page in recentPages"
            :key="page.path"
            class="recent-item"
            @click="navigateToPage(page.path)"
          >
            <el-icon :class="page.icon">
              <component :is="page.icon" />
            </el-icon>
            <span class="recent-title">{{ page.title }}</span>
            <span class="recent-time">{{ formatRelativeTime(page.visitTime) }}</span>
          </div>
        </div>
      </div>

      <!-- 智能推荐 -->
      <div class="smart-recommendations">
        <div class="section-title">
          为你推荐
          <el-tag size="small" type="primary">AI</el-tag>
        </div>
        <div class="recommendations-list">
          <div
            v-for="rec in smartRecommendations"
            :key="rec.id"
            class="recommendation-item"
            @click="applyRecommendation(rec)"
          >
            <div class="rec-header">
              <div class="rec-title">{{ rec.title }}</div>
              <div class="rec-confidence">
                {{ Math.round(rec.confidence * 100) }}%
              </div>
            </div>
            <div class="rec-reason">{{ rec.reason }}</div>
            <div class="rec-actions">
              <el-button size="small" type="primary" text>立即前往</el-button>
              <el-button size="small" text @click.stop="dismissRecommendation(rec.id)">
                忽略
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 当前上下文信息 -->
      <div v-if="contextInfo" class="context-info">
        <div class="section-title">当前状态</div>
        <div class="context-content">
          <div class="context-item">
            <span class="context-label">当前页面:</span>
            <span class="context-value">{{ contextInfo.currentPage }}</span>
          </div>
          <div v-if="contextInfo.unsavedChanges" class="context-item warning">
            <el-icon><Warning /></el-icon>
            <span>有未保存的更改</span>
          </div>
          <div v-if="contextInfo.runningTasks > 0" class="context-item info">
            <el-icon><Loading /></el-icon>
            <span>{{ contextInfo.runningTasks }} 个任务运行中</span>
          </div>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNavigationStore } from '@/stores/navigation'
import { ElMessage } from 'element-plus'
import {
  Guide, Close, Search, ArrowRight, Warning, Loading,
  MagicStick, Cpu, TrendCharts, DataAnalysis, Upload, Odometer
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const navigationStore = useNavigationStore()

// 响应式数据
const showNavAssistant = ref(false)
const userQuery = ref('')
const processingQuery = ref(false)

// 快速建议 - 基于当前页面和用户行为动态生成
const currentSuggestions = computed(() => {
  const currentPath = route.path
  const suggestions = []

  // 基于当前页面的建议
  if (currentPath === '/dashboard') {
    suggestions.push(
      {
        id: 'create-factor',
        title: '开发新因子',
        description: '使用AI助手创建量化因子',
        icon: 'MagicStick',
        action: () => router.push('/factors')
      },
      {
        id: 'start-training',
        title: '开始模型训练',
        description: '训练新的预测模型',
        icon: 'Cpu',
        action: () => router.push('/training')
      }
    )
  } else if (currentPath === '/factors') {
    suggestions.push(
      {
        id: 'validate-factor',
        title: '因子验证',
        description: '测试因子历史表现',
        icon: 'TrendCharts',
        action: () => scrollToSection('validation')
      },
      {
        id: 'train-with-factor',
        title: '用于模型训练',
        description: '使用当前因子训练模型',
        icon: 'Cpu',
        action: () => router.push('/training')
      }
    )
  } else if (currentPath === '/training') {
    suggestions.push(
      {
        id: 'backtest-model',
        title: '回测模型',
        description: '测试模型策略表现',
        icon: 'TrendCharts',
        action: () => router.push('/backtest')
      },
      {
        id: 'analyze-results',
        title: '分析结果',
        description: '查看训练结果分析',
        icon: 'DataAnalysis',
        action: () => router.push('/results')
      }
    )
  }

  return suggestions
})

// 最近访问的页面
const recentPages = computed(() => navigationStore.recentPages)

// AI智能推荐
const smartRecommendations = ref([
  {
    id: 'optimize-strategy',
    title: '优化现有策略',
    reason: '检测到你的策略表现有下降趋势',
    confidence: 0.85,
    action: () => router.push('/results?tab=suggestions')
  },
  {
    id: 'deploy-best-model',
    title: '部署最佳模型',
    reason: '你有一个表现优异的模型可以部署',
    confidence: 0.92,
    action: () => router.push('/deployment')
  }
])

// 当前上下文信息
const contextInfo = computed(() => navigationStore.contextInfo)

// 方法
const toggleNavAssistant = () => {
  showNavAssistant.value = !showNavAssistant.value
  if (showNavAssistant.value) {
    navigationStore.recordNavAssistantOpen()
  }
}

const handleUserQuery = async () => {
  if (!userQuery.value.trim()) return

  processingQuery.value = true
  
  try {
    // 模拟AI处理用户查询
    const response = await processNaturalLanguageQuery(userQuery.value)
    
    if (response.action === 'navigate') {
      router.push(response.target)
      ElMessage.success(`已为您导航到: ${response.description}`)
    } else if (response.action === 'suggest') {
      ElMessage.info(response.message)
    }
    
    userQuery.value = ''
    showNavAssistant.value = false
  } catch (error) {
    ElMessage.error('导航助手暂时不可用')
  } finally {
    processingQuery.value = false
  }
}

const applySuggestion = (suggestion: any) => {
  suggestion.action()
  navigationStore.recordSuggestionUsed(suggestion.id)
  showNavAssistant.value = false
}

const navigateToPage = (path: string) => {
  router.push(path)
  showNavAssistant.value = false
}

const applyRecommendation = (rec: any) => {
  rec.action()
  navigationStore.recordRecommendationUsed(rec.id)
  showNavAssistant.value = false
}

const dismissRecommendation = (recId: string) => {
  navigationStore.dismissRecommendation(recId)
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

const scrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
    showNavAssistant.value = false
  }
}

// 模拟AI自然语言处理
const processNaturalLanguageQuery = async (query: string) => {
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 简单的关键词匹配逻辑
  const lowerQuery = query.toLowerCase()
  
  if (lowerQuery.includes('因子') || lowerQuery.includes('factor')) {
    return {
      action: 'navigate',
      target: '/factors',
      description: '因子开发页面'
    }
  } else if (lowerQuery.includes('训练') || lowerQuery.includes('模型')) {
    return {
      action: 'navigate',
      target: '/training',
      description: '模型训练页面'
    }
  } else if (lowerQuery.includes('回测') || lowerQuery.includes('策略')) {
    return {
      action: 'navigate',
      target: '/backtest',
      description: '策略回测页面'
    }
  } else if (lowerQuery.includes('部署') || lowerQuery.includes('上线')) {
    return {
      action: 'navigate',
      target: '/deployment',
      description: '策略部署页面'
    }
  } else if (lowerQuery.includes('分析') || lowerQuery.includes('结果')) {
    return {
      action: 'navigate',
      target: '/results',
      description: '结果分析页面'
    }
  } else {
    return {
      action: 'suggest',
      message: '抱歉，我没有理解您的需求。您可以尝试说"开发因子"、"训练模型"等关键词。'
    }
  }
}

onMounted(() => {
  // 初始化时更新当前页面访问记录
  navigationStore.recordPageVisit(route.path, route.meta?.title as string || '未知页面')
})
</script>

<style scoped>
.smart-navigation {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 500px;
  overflow-y: auto;
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 12px;
}

.nav-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.nav-input-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title,
.suggestions-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.suggestions-list,
.recent-list,
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item,
.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.suggestion-item:hover,
.recent-item:hover {
  background: #f0f8ff;
  border-color: #409eff;
}

.suggestion-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.suggestion-content {
  flex: 1;
}

.suggestion-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.suggestion-description {
  font-size: 12px;
  color: #909399;
}

.suggestion-arrow {
  color: #c0c4cc;
  font-size: 12px;
}

.recent-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
}

.recent-time {
  font-size: 12px;
  color: #909399;
}

.recommendation-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f0f8ff;
  border-left: 4px solid #409eff;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rec-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.rec-confidence {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.rec-reason {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.4;
}

.rec-actions {
  display: flex;
  gap: 8px;
}

.context-info {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.context-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.context-item.warning {
  color: #e6a23c;
}

.context-item.info {
  color: #409eff;
}

.context-label {
  color: #909399;
  font-weight: 500;
}

.context-value {
  color: #303133;
}

/* 按钮激活状态 */
.active {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}
</style>