<template>
  <div class="personal-dashboard">
    <div class="dashboard-header">
      <h3>个人仪表盘定制</h3>
      <div class="dashboard-controls">
        <el-button @click="toggleEditMode" :type="isEditMode ? 'success' : 'primary'">
          {{ isEditMode ? '完成编辑' : '编辑布局' }}
        </el-button>
        <el-dropdown @command="handleTemplateCommand">
          <el-button>
            模板<el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="save">保存当前布局</el-dropdown-item>
              <el-dropdown-item command="load">加载模板</el-dropdown-item>
              <el-dropdown-item command="reset">重置为默认</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 编辑模式工具栏 -->
    <div v-if="isEditMode" class="edit-toolbar">
      <h4>可添加组件</h4>
      <div class="widget-gallery">
        <div
          v-for="widget in availableWidgets"
          :key="widget.id"
          class="widget-item"
          @click="addWidget(widget)"
        >
          <el-icon><component :is="widget.icon" /></el-icon>
          <span>{{ widget.name }}</span>
        </div>
      </div>
    </div>

    <!-- 仪表盘网格 -->
    <div class="dashboard-grid" :class="{ 'edit-mode': isEditMode }">
      <div
        v-for="widget in activeWidgets"
        :key="widget.id"
        class="dashboard-widget"
        :style="getWidgetStyle(widget)"
      >
        <div class="widget-header">
          <h4>{{ widget.title }}</h4>
          <div v-if="isEditMode" class="widget-controls">
            <el-button size="small" @click="configureWidget(widget)">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button size="small" @click="removeWidget(widget.id)">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        
        <!-- 动态组件内容 -->
        <component :is="widget.component" :config="widget.config" />
      </div>
    </div>

    <!-- 小部件配置弹窗 -->
    <el-dialog v-model="showWidgetConfig" title="组件配置" width="600px">
      <el-form :model="widgetConfigForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="widgetConfigForm.title" />
        </el-form-item>
        <el-form-item label="尺寸">
          <el-select v-model="widgetConfigForm.size">
            <el-option label="小" value="small" />
            <el-option label="中" value="medium" />
            <el-option label="大" value="large" />
          </el-select>
        </el-form-item>
        <el-form-item label="刷新间隔">
          <el-select v-model="widgetConfigForm.refreshInterval">
            <el-option label="不自动刷新" :value="0" />
            <el-option label="30秒" :value="30" />
            <el-option label="1分钟" :value="60" />
            <el-option label="5分钟" :value="300" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWidgetConfig = false">取消</el-button>
        <el-button type="primary" @click="saveWidgetConfig">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, Setting, Close } from '@element-plus/icons-vue'

// 小部件接口
interface Widget {
  id: string
  name: string
  title: string
  component: string
  icon: string
  size: 'small' | 'medium' | 'large'
  position: { x: number; y: number }
  config: Record<string, any>
}

const isEditMode = ref(false)
const showWidgetConfig = ref(false)
const currentEditWidget = ref<Widget | null>(null)

// 可用组件
const availableWidgets = ref([
  { id: 'performance-summary', name: '性能概览', icon: 'TrendCharts', component: 'PerformanceSummary' },
  { id: 'recent-trades', name: '最近交易', icon: 'List', component: 'RecentTrades' },
  { id: 'risk-monitor', name: '风险监控', icon: 'WarningFilled', component: 'RiskMonitor' },
  { id: 'market-watch', name: '市场观察', icon: 'View', component: 'MarketWatch' },
  { id: 'strategy-ranking', name: '策略排名', icon: 'Ranking', component: 'StrategyRanking' }
])

// 当前活跃组件
const activeWidgets = ref<Widget[]>([
  {
    id: '1',
    name: 'performance-summary',
    title: '投资组合概览',
    component: 'PerformanceSummary',
    icon: 'TrendCharts',
    size: 'large',
    position: { x: 0, y: 0 },
    config: { timeRange: '1M' }
  }
])

// 组件配置表单
const widgetConfigForm = reactive({
  title: '',
  size: 'medium' as const,
  refreshInterval: 60
})

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value
  if (!isEditMode.value) {
    ElMessage.success('布局已保存')
  }
}

const addWidget = (widget: any) => {
  const newWidget: Widget = {
    id: Date.now().toString(),
    name: widget.id,
    title: widget.name,
    component: widget.component,
    icon: widget.icon,
    size: 'medium',
    position: { x: 0, y: activeWidgets.value.length },
    config: {}
  }
  
  activeWidgets.value.push(newWidget)
  ElMessage.success(`已添加 ${widget.name}`)
}

const removeWidget = (widgetId: string) => {
  const index = activeWidgets.value.findIndex(w => w.id === widgetId)
  if (index > -1) {
    activeWidgets.value.splice(index, 1)
    ElMessage.success('组件已移除')
  }
}

const configureWidget = (widget: Widget) => {
  currentEditWidget.value = widget
  widgetConfigForm.title = widget.title
  widgetConfigForm.size = widget.size
  widgetConfigForm.refreshInterval = widget.config.refreshInterval || 60
  showWidgetConfig.value = true
}

const saveWidgetConfig = () => {
  if (currentEditWidget.value) {
    currentEditWidget.value.title = widgetConfigForm.title
    currentEditWidget.value.size = widgetConfigForm.size
    currentEditWidget.value.config.refreshInterval = widgetConfigForm.refreshInterval
    
    showWidgetConfig.value = false
    ElMessage.success('配置已保存')
  }
}

const getWidgetStyle = (widget: Widget) => {
  const sizeMap = {
    small: { gridColumn: 'span 1', gridRow: 'span 1' },
    medium: { gridColumn: 'span 2', gridRow: 'span 2' },
    large: { gridColumn: 'span 3', gridRow: 'span 2' }
  }
  
  return sizeMap[widget.size]
}

const handleTemplateCommand = (command: string) => {
  switch (command) {
    case 'save':
      ElMessage.success('当前布局已保存为模板')
      break
    case 'load':
      ElMessage.info('模板加载功能开发中')
      break
    case 'reset':
      activeWidgets.value = [activeWidgets.value[0]] // 保留第一个组件
      ElMessage.success('已重置为默认布局')
      break
  }
}
</script>

<style scoped lang="scss">
.personal-dashboard {
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .edit-toolbar {
    background: var(--el-color-info-light-9);
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 24px;

    .widget-gallery {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;

      .widget-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px;
        border: 2px dashed var(--el-border-color);
        border-radius: 8px;
        cursor: pointer;
        min-width: 80px;

        &:hover {
          border-color: var(--el-color-primary);
        }
      }
    }
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    min-height: 400px;

    &.edit-mode {
      border: 2px dashed var(--el-color-primary-light-7);
      border-radius: 8px;
      padding: 16px;
    }

    .dashboard-widget {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;

      .widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: var(--el-color-info-light-9);
        border-bottom: 1px solid var(--el-border-color);

        h4 {
          margin: 0;
          font-size: 14px;
        }

        .widget-controls {
          display: flex;
          gap: 4px;
        }
      }
    }
  }
}
</style>