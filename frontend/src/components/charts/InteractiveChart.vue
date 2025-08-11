<template>
  <div class="interactive-chart">
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-tooltip content="缩放" placement="top">
            <el-button 
              :type="tool === 'zoom' ? 'primary' : 'default'" 
              @click="setTool('zoom')"
              size="small"
            >
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="平移" placement="top">
            <el-button 
              :type="tool === 'pan' ? 'primary' : 'default'" 
              @click="setTool('pan')"
              size="small"
            >
              <el-icon><Rank /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="选择" placement="top">
            <el-button 
              :type="tool === 'select' ? 'primary' : 'default'" 
              @click="setTool('select')"
              size="small"
            >
              <el-icon><Pointer /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="标注" placement="top">
            <el-button 
              :type="tool === 'annotate' ? 'primary' : 'default'" 
              @click="setTool('annotate')"
              size="small"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
        </el-button-group>
        
        <el-divider direction="vertical" />
        
        <el-button-group>
          <el-tooltip content="重置缩放" placement="top">
            <el-button @click="resetZoom" size="small">
              <el-icon><RefreshLeft /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="全屏" placement="top">
            <el-button @click="toggleFullscreen" size="small">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="导出" placement="top">
            <el-button @click="exportChart" size="small">
              <el-icon><Download /></el-icon>
            </el-button>
          </el-tooltip>
        </el-button-group>
      </div>
      
      <div class="toolbar-right">
        <el-select 
          v-model="theme" 
          @change="changeTheme"
          size="small"
          style="width: 100px;"
        >
          <el-option label="明亮" value="light" />
          <el-option label="暗黑" value="dark" />
          <el-option label="蓝色" value="blue" />
        </el-select>
        
        <el-dropdown @command="handleQuickAction">
          <el-button size="small">
            快速操作
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="saveView">保存视图</el-dropdown-item>
              <el-dropdown-item command="loadView">加载视图</el-dropdown-item>
              <el-dropdown-item divided command="copyData">复制数据</el-dropdown-item>
              <el-dropdown-item command="showData">显示数据表</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div 
      ref="chartContainer" 
      class="chart-container"
      :class="{ fullscreen: isFullscreen }"
      @contextmenu.prevent="showContextMenu"
    >
      <div ref="chartRef" class="chart"></div>
      
      <!-- 十字准线信息 -->
      <div 
        v-if="crosshairData" 
        class="crosshair-info"
        :style="crosshairStyle"
      >
        <div class="crosshair-content">
          <div class="crosshair-title">{{ crosshairData.title }}</div>
          <div 
            v-for="item in crosshairData.data" 
            :key="item.name"
            class="crosshair-item"
          >
            <span class="item-color" :style="{ backgroundColor: item.color }"></span>
            <span class="item-name">{{ item.name }}:</span>
            <span class="item-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
      
      <!-- 选择框 -->
      <div 
        v-if="selectionBox" 
        class="selection-box"
        :style="selectionBoxStyle"
      ></div>
      
      <!-- 标注 -->
      <div 
        v-for="annotation in annotations" 
        :key="annotation.id"
        class="annotation"
        :class="annotation.type"
        :style="getAnnotationStyle(annotation)"
        @click="editAnnotation(annotation)"
      >
        <div class="annotation-content">
          {{ annotation.text }}
        </div>
        <div class="annotation-actions">
          <el-button type="text" size="small" @click="removeAnnotation(annotation.id)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div 
      v-if="contextMenu.show" 
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="menu-item" @click="addAnnotation">添加标注</div>
      <div class="menu-item" @click="addMarkLine">添加标记线</div>
      <div class="menu-item" @click="copyCoordinates">复制坐标</div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="exportSelectedData">导出选中数据</div>
      <div class="menu-item" @click="hideContextMenu">取消</div>
    </div>

    <!-- 标注编辑对话框 -->
    <el-dialog v-model="showAnnotationDialog" title="编辑标注" width="400px">
      <el-form :model="editingAnnotation" label-width="80px">
        <el-form-item label="文本">
          <el-input v-model="editingAnnotation.text" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editingAnnotation.type">
            <el-option label="普通" value="normal" />
            <el-option label="重要" value="important" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="editingAnnotation.color" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAnnotationDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAnnotation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 数据表对话框 -->
    <el-dialog v-model="showDataTable" title="图表数据" width="80%">
      <el-table :data="chartData" max-height="400">
        <el-table-column 
          v-for="column in dataColumns" 
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          :formatter="column.formatter"
        />
      </el-table>
      
      <template #footer>
        <el-button @click="exportTableData">导出CSV</el-button>
        <el-button type="primary" @click="showDataTable = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  ZoomIn,
  Rank,
  Pointer,
  Edit,
  RefreshLeft,
  FullScreen,
  Download,
  ArrowDown,
  Close
} from '@element-plus/icons-vue'

interface Annotation {
  id: string
  x: number
  y: number
  text: string
  type: 'normal' | 'important' | 'warning' | 'error'
  color?: string
  dataX?: any
  dataY?: any
}

interface CrosshairData {
  title: string
  data: Array<{
    name: string
    value: string
    color: string
  }>
}

const props = defineProps<{
  option: any
  data?: any[]
  height?: number
  interactive?: boolean
}>()

const emit = defineEmits(['dataSelect', 'annotationAdd', 'annotationEdit', 'annotationRemove'])

// 响应式数据
const chartRef = ref()
const chartContainer = ref()
const tool = ref('zoom')
const theme = ref('light')
const isFullscreen = ref(false)

let chart: echarts.ECharts | null = null

const crosshairData = ref<CrosshairData | null>(null)
const crosshairStyle = ref({})

const selectionBox = ref<any>(null)
const selectionBoxStyle = ref({})

const annotations = ref<Annotation[]>([])
const showAnnotationDialog = ref(false)
const editingAnnotation = reactive<Partial<Annotation>>({
  text: '',
  type: 'normal',
  color: '#409eff'
})

const contextMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  dataX: null,
  dataY: null
})

const showDataTable = ref(false)
const chartData = ref<any[]>([])
const dataColumns = ref<any[]>([])

const savedViews = ref<any[]>([])
let isSelecting = false
let selectionStart = { x: 0, y: 0 }

// 方法
const initChart = () => {
  if (!chartRef.value) return
  
  // 根据主题初始化图表
  const themeMap: Record<string, any> = {
    light: null,
    dark: 'dark',
    blue: null // 可以自定义蓝色主题
  }
  
  chart = echarts.init(chartRef.value, themeMap[theme.value])
  updateChart()
  
  // 绑定事件
  bindChartEvents()
}

const updateChart = () => {
  if (!chart) return
  
  const option = { ...props.option }
  
  // 添加交互配置
  if (props.interactive !== false) {
    option.toolbox = {
      feature: {
        dataZoom: { show: false }, // 使用自定义工具栏
        brush: { show: false },
        saveAsImage: { show: false }
      }
    }
    
    option.brush = tool.value === 'select' ? {
      toolbox: ['rect', 'polygon', 'clear'],
      xAxisIndex: 'all'
    } : undefined
    
    option.dataZoom = [
      {
        type: 'inside',
        disabled: tool.value !== 'zoom'
      }
    ]
  }
  
  // 添加标记线
  if (annotations.value.length > 0) {
    const markLines = annotations.value
      .filter(ann => ann.type === 'important')
      .map(ann => ({
        name: ann.text,
        xAxis: ann.dataX,
        lineStyle: { color: ann.color || '#f56c6c' }
      }))
    
    if (option.series && option.series[0] && markLines.length > 0) {
      option.series[0].markLine = {
        data: markLines
      }
    }
  }
  
  chart.setOption(option, true)
}

const bindChartEvents = () => {
  if (!chart) return
  
  // 鼠标移动事件 - 十字准线
  chart.on('mousemove', (params) => {
    if (tool.value === 'select' || tool.value === 'annotate') return
    
    updateCrosshair(params)
  })
  
  // 鼠标离开
  chart.on('globalout', () => {
    crosshairData.value = null
  })
  
  // 点击事件
  chart.on('click', (params) => {
    handleChartClick(params)
  })
  
  // 数据缩放事件
  chart.on('datazoom', (params) => {
    console.log('数据缩放:', params)
  })
  
  // 刷选事件
  chart.on('brushselected', (params) => {
    handleBrushSelect(params)
  })
  
  // 图例选择事件
  chart.on('legendselectchanged', (params) => {
    console.log('图例选择变化:', params)
  })
}

const updateCrosshair = (params: any) => {
  if (!params || params.componentType !== 'series') return
  
  const data: CrosshairData = {
    title: params.name || params.axisValue || '',
    data: []
  }
  
  if (Array.isArray(params.value)) {
    // 多维数据
    params.value.forEach((val: any, index: number) => {
      if (index > 0) { // 跳过x轴数据
        data.data.push({
          name: `系列${index}`,
          value: typeof val === 'number' ? val.toFixed(2) : String(val),
          color: params.color || '#409eff'
        })
      }
    })
  } else {
    // 单值数据
    data.data.push({
      name: params.seriesName || '数值',
      value: typeof params.value === 'number' ? params.value.toFixed(2) : String(params.value),
      color: params.color || '#409eff'
    })
  }
  
  crosshairData.value = data
  
  // 更新十字准线位置
  const rect = chartRef.value.getBoundingClientRect()
  crosshairStyle.value = {
    left: (params.offsetX || 0) + 10 + 'px',
    top: (params.offsetY || 0) - 10 + 'px'
  }
}

const handleChartClick = (params: any) => {
  if (tool.value === 'annotate') {
    // 添加标注模式
    const annotation: Annotation = {
      id: Date.now().toString(),
      x: params.offsetX || 0,
      y: params.offsetY || 0,
      text: '新标注',
      type: 'normal',
      color: '#409eff',
      dataX: params.data?.[0] || params.axisValue,
      dataY: params.data?.[1] || params.value
    }
    
    annotations.value.push(annotation)
    editAnnotation(annotation)
  } else if (tool.value === 'select') {
    // 选择模式 - 可以扩展为多选
    emit('dataSelect', params)
  }
}

const handleBrushSelect = (params: any) => {
  if (!params.batch || params.batch.length === 0) return
  
  const selectedData = params.batch[0].selected[0]
  if (selectedData && selectedData.dataIndex) {
    emit('dataSelect', {
      dataIndices: selectedData.dataIndex,
      seriesIndex: 0
    })
  }
}

const setTool = (newTool: string) => {
  tool.value = newTool
  
  // 更新图表配置
  updateChart()
  
  // 更新鼠标样式
  const cursorMap: Record<string, string> = {
    zoom: 'zoom-in',
    pan: 'grab',
    select: 'crosshair',
    annotate: 'crosshair'
  }
  
  if (chartRef.value) {
    chartRef.value.style.cursor = cursorMap[newTool] || 'default'
  }
}

const resetZoom = () => {
  if (!chart) return
  
  chart.dispatchAction({
    type: 'dataZoom',
    start: 0,
    end: 100
  })
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  if (isFullscreen.value) {
    document.documentElement.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
  
  // 延迟调整图表大小
  setTimeout(() => {
    chart?.resize()
  }, 100)
}

const exportChart = () => {
  if (!chart) return
  
  const url = chart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: theme.value === 'dark' ? '#1f1f1f' : '#fff'
  })
  
  const link = document.createElement('a')
  link.download = `chart-${Date.now()}.png`
  link.href = url
  link.click()
}

const changeTheme = () => {
  if (chart) {
    chart.dispose()
  }
  initChart()
}

const handleQuickAction = (command: string) => {
  switch (command) {
    case 'saveView':
      saveCurrentView()
      break
    case 'loadView':
      // 可以扩展为选择已保存的视图
      loadView()
      break
    case 'copyData':
      copyChartData()
      break
    case 'showData':
      showChartData()
      break
  }
}

const saveCurrentView = () => {
  if (!chart) return
  
  const option = chart.getOption()
  const view = {
    id: Date.now().toString(),
    name: `视图_${new Date().toLocaleTimeString()}`,
    option: JSON.stringify(option),
    timestamp: new Date().toISOString()
  }
  
  savedViews.value.push(view)
  localStorage.setItem('chartViews', JSON.stringify(savedViews.value))
  
  ElMessage.success('视图已保存')
}

const loadView = () => {
  const saved = localStorage.getItem('chartViews')
  if (saved) {
    const views = JSON.parse(saved)
    if (views.length > 0) {
      const lastView = views[views.length - 1]
      const option = JSON.parse(lastView.option)
      chart?.setOption(option)
      ElMessage.success('视图已加载')
    }
  }
}

const copyChartData = () => {
  if (!props.data) return
  
  const dataStr = JSON.stringify(props.data, null, 2)
  navigator.clipboard.writeText(dataStr).then(() => {
    ElMessage.success('数据已复制到剪贴板')
  })
}

const showChartData = () => {
  if (!props.data) return
  
  chartData.value = props.data
  
  // 动态生成列配置
  if (props.data.length > 0) {
    const firstItem = props.data[0]
    dataColumns.value = Object.keys(firstItem).map(key => ({
      key,
      label: key,
      formatter: (row: any) => {
        const value = row[key]
        if (typeof value === 'number') {
          return value.toFixed(2)
        }
        return String(value)
      }
    }))
  }
  
  showDataTable.value = true
}

const exportTableData = () => {
  if (!chartData.value.length) return
  
  // 生成CSV
  const headers = dataColumns.value.map(col => col.label).join(',')
  const rows = chartData.value.map(row => 
    dataColumns.value.map(col => row[col.key]).join(',')
  ).join('\n')
  
  const csv = headers + '\n' + rows
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.download = `chart-data-${Date.now()}.csv`
  link.href = url
  link.click()
  
  URL.revokeObjectURL(url)
}

// 右键菜单相关
const showContextMenu = (event: MouseEvent) => {
  event.preventDefault()
  
  contextMenu.x = event.offsetX
  contextMenu.y = event.offsetY
  contextMenu.show = true
  
  // 获取数据坐标
  if (chart) {
    const point = chart.convertFromPixel('grid', [event.offsetX, event.offsetY])
    contextMenu.dataX = point?.[0]
    contextMenu.dataY = point?.[1]
  }
  
  // 点击其他地方隐藏菜单
  document.addEventListener('click', hideContextMenu, { once: true })
}

const hideContextMenu = () => {
  contextMenu.show = false
}

const addAnnotation = () => {
  const annotation: Annotation = {
    id: Date.now().toString(),
    x: contextMenu.x,
    y: contextMenu.y,
    text: '新标注',
    type: 'normal',
    color: '#409eff',
    dataX: contextMenu.dataX,
    dataY: contextMenu.dataY
  }
  
  annotations.value.push(annotation)
  editAnnotation(annotation)
  hideContextMenu()
}

const addMarkLine = () => {
  if (!chart || contextMenu.dataX === null) return
  
  const option = chart.getOption()
  if (option.series && option.series[0]) {
    const markLine = option.series[0].markLine || { data: [] }
    markLine.data.push({
      name: '标记线',
      xAxis: contextMenu.dataX,
      lineStyle: { color: '#f56c6c', type: 'dashed' }
    })
    
    option.series[0].markLine = markLine
    chart.setOption(option)
  }
  
  hideContextMenu()
}

const copyCoordinates = () => {
  const coords = `坐标: (${contextMenu.dataX}, ${contextMenu.dataY})`
  navigator.clipboard.writeText(coords).then(() => {
    ElMessage.success('坐标已复制')
  })
  hideContextMenu()
}

const exportSelectedData = () => {
  // 导出选中区域的数据
  ElMessage.info('导出选中数据功能开发中')
  hideContextMenu()
}

// 标注相关
const editAnnotation = (annotation: Annotation) => {
  Object.assign(editingAnnotation, annotation)
  showAnnotationDialog.value = true
}

const saveAnnotation = () => {
  const annotation = annotations.value.find(a => a.id === editingAnnotation.id)
  if (annotation) {
    Object.assign(annotation, editingAnnotation)
    emit('annotationEdit', annotation)
  }
  
  showAnnotationDialog.value = false
}

const removeAnnotation = (id: string) => {
  const index = annotations.value.findIndex(a => a.id === id)
  if (index > -1) {
    const annotation = annotations.value[index]
    annotations.value.splice(index, 1)
    emit('annotationRemove', annotation)
  }
}

const getAnnotationStyle = (annotation: Annotation) => {
  return {
    left: annotation.x + 'px',
    top: annotation.y + 'px',
    borderColor: annotation.color || '#409eff'
  }
}

// 监听器
watch(() => props.option, () => {
  updateChart()
}, { deep: true })

watch(() => props.height, () => {
  nextTick(() => {
    chart?.resize()
  })
})

// 生命周期
onMounted(async () => {
  await nextTick()
  initChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    chart?.resize()
  })
  
  // 监听全屏变化
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) {
      isFullscreen.value = false
    }
    setTimeout(() => {
      chart?.resize()
    }, 100)
  })
})

onUnmounted(() => {
  chart?.dispose()
  
  window.removeEventListener('resize', () => {
    chart?.resize()
  })
  
  document.removeEventListener('fullscreenchange', () => {
    setTimeout(() => {
      chart?.resize()
    }, 100)
  })
})
</script>

<style scoped>
.interactive-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-bottom: none;
  border-radius: 8px 8px 0 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  flex: 1;
  position: relative;
  border: 1px solid #e4e7ed;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.chart-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  border-radius: 0;
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

.crosshair-info {
  position: absolute;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 100;
  min-width: 120px;
}

.crosshair-title {
  font-weight: 600;
  margin-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 4px;
}

.crosshair-item {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.item-color {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.item-name {
  flex: 1;
}

.item-value {
  font-weight: 600;
}

.selection-box {
  position: absolute;
  border: 1px dashed #409eff;
  background: rgba(64, 158, 255, 0.1);
  pointer-events: none;
  z-index: 50;
}

.annotation {
  position: absolute;
  background: white;
  border: 2px solid #409eff;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  z-index: 60;
  cursor: pointer;
  max-width: 200px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.annotation.important {
  border-color: #f56c6c;
  background: #fef0f0;
}

.annotation.warning {
  border-color: #e6a23c;
  background: #fdf6ec;
}

.annotation.error {
  border-color: #f56c6c;
  background: #fef0f0;
}

.annotation:hover .annotation-actions {
  display: block;
}

.annotation-content {
  margin-bottom: 4px;
  line-height: 1.2;
}

.annotation-actions {
  display: none;
  text-align: right;
}

.context-menu {
  position: absolute;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 200;
  min-width: 120px;
}

.menu-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  transition: background-color 0.3s;
}

.menu-item:hover {
  background: #f5f7fa;
}

.menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 4px 0;
}

/* 暗黑主题适配 */
.chart-container.dark {
  background: #1f1f1f;
  border-color: #3a3a3a;
}

.dark .chart-toolbar {
  background: #2d2d2d;
  border-color: #3a3a3a;
  color: #ccc;
}

.dark .context-menu {
  background: #2d2d2d;
  border-color: #3a3a3a;
  color: #ccc;
}

.dark .menu-item:hover {
  background: #3a3a3a;
}
</style>