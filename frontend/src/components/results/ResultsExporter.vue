<template>
  <div class="results-exporter">
    <!-- 导出配置 -->
    <el-card class="export-config">
      <template #header>
        <div class="config-header">
          <span>
            <el-icon><Download /></el-icon>
            结果导出配置
          </span>
          <el-button @click="resetConfig" size="small" text>
            <el-icon><RefreshLeft /></el-icon>
            重置配置
          </el-button>
        </div>
      </template>
      
      <div class="config-content">
        <!-- 导出类型选择 -->
        <div class="config-section">
          <label class="section-label">导出类型</label>
          <el-radio-group v-model="exportConfig.type" class="export-types">
            <el-radio-button value="report">完整报告</el-radio-button>
            <el-radio-button value="data">原始数据</el-radio-button>
            <el-radio-button value="charts">图表集合</el-radio-button>
            <el-radio-button value="summary">摘要报告</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 策略选择 -->
        <div class="config-section">
          <label class="section-label">选择策略</label>
          <el-select
            v-model="exportConfig.strategies"
            multiple
            filterable
            placeholder="请选择要导出的策略"
            style="width: 100%"
            :max-collapse-tags="3"
          >
            <el-option
              v-for="strategy in availableStrategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            >
              <div class="strategy-option">
                <span class="strategy-name">{{ strategy.name }}</span>
                <el-tag :type="getPerformanceTagType(strategy.score)" size="small">
                  {{ strategy.score.toFixed(1) }}分
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 时间范围 -->
        <div class="config-section">
          <label class="section-label">时间范围</label>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-date-picker
                v-model="exportConfig.dateRange[0]"
                type="date"
                placeholder="开始日期"
                style="width: 100%"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-col>
            <el-col :span="12">
              <el-date-picker
                v-model="exportConfig.dateRange[1]"
                type="date"
                placeholder="结束日期"
                style="width: 100%"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 内容选择 -->
        <div class="config-section">
          <label class="section-label">导出内容</label>
          <div class="content-options">
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="option-group">
                  <h4 class="group-title">基础信息</h4>
                  <el-checkbox-group v-model="exportConfig.content.basic">
                    <el-checkbox label="strategy_info">策略基本信息</el-checkbox>
                    <el-checkbox label="performance_metrics">性能指标</el-checkbox>
                    <el-checkbox label="risk_metrics">风险指标</el-checkbox>
                    <el-checkbox label="attribution">归因分析</el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-col>
              
              <el-col :span="12">
                <div class="option-group">
                  <h4 class="group-title">详细数据</h4>
                  <el-checkbox-group v-model="exportConfig.content.detailed">
                    <el-checkbox label="daily_returns">日度收益率</el-checkbox>
                    <el-checkbox label="positions">持仓明细</el-checkbox>
                    <el-checkbox label="trades">交易记录</el-checkbox>
                    <el-checkbox label="nav_curve">净值曲线</el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-col>
            </el-row>
            
            <el-row :gutter="16" style="margin-top: 16px;">
              <el-col :span="12">
                <div class="option-group">
                  <h4 class="group-title">图表内容</h4>
                  <el-checkbox-group v-model="exportConfig.content.charts">
                    <el-checkbox label="nav_chart">净值走势图</el-checkbox>
                    <el-checkbox label="drawdown_chart">回撤分析图</el-checkbox>
                    <el-checkbox label="return_distribution">收益分布图</el-checkbox>
                    <el-checkbox label="sector_allocation">行业配置图</el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-col>
              
              <el-col :span="12">
                <div class="option-group">
                  <h4 class="group-title">分析报告</h4>
                  <el-checkbox-group v-model="exportConfig.content.analysis">
                    <el-checkbox label="executive_summary">执行摘要</el-checkbox>
                    <el-checkbox label="ai_insights">AI分析洞察</el-checkbox>
                    <el-checkbox label="optimization_suggestions">优化建议</el-checkbox>
                    <el-checkbox label="comparison_analysis">对比分析</el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 格式设置 -->
        <div class="config-section">
          <label class="section-label">导出格式</label>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="format-option">
                <el-select v-model="exportConfig.format" style="width: 100%">
                  <el-option label="PDF报告" value="pdf" />
                  <el-option label="Excel文件" value="excel" />
                  <el-option label="Word文档" value="word" />
                  <el-option label="PowerPoint" value="ppt" />
                  <el-option label="JSON数据" value="json" />
                  <el-option label="CSV数据" value="csv" />
                </el-select>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="format-option">
                <el-select v-model="exportConfig.language" style="width: 100%">
                  <el-option label="中文" value="zh" />
                  <el-option label="English" value="en" />
                </el-select>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="format-option">
                <el-select v-model="exportConfig.template" style="width: 100%">
                  <el-option label="标准模板" value="standard" />
                  <el-option label="简洁模板" value="simple" />
                  <el-option label="详细模板" value="detailed" />
                  <el-option label="投资者模板" value="investor" />
                </el-select>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 高级选项 -->
        <div class="config-section">
          <label class="section-label">高级选项</label>
          <div class="advanced-options">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-checkbox v-model="exportConfig.options.includeWatermark">包含水印</el-checkbox>
                <el-checkbox v-model="exportConfig.options.compressFile">压缩文件</el-checkbox>
                <el-checkbox v-model="exportConfig.options.encryptFile">文件加密</el-checkbox>
              </el-col>
              
              <el-col :span="12">
                <el-checkbox v-model="exportConfig.options.emailNotify">邮件通知</el-checkbox>
                <el-checkbox v-model="exportConfig.options.autoSchedule">定时导出</el-checkbox>
                <el-checkbox v-model="exportConfig.options.cloudBackup">云端备份</el-checkbox>
              </el-col>
            </el-row>
          </div>
        </div>

        <!-- 预览信息 -->
        <div class="config-section">
          <label class="section-label">导出预览</label>
          <div class="export-preview">
            <div class="preview-item">
              <span class="preview-label">文件名:</span>
              <span class="preview-value">{{ generateFileName() }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">预计大小:</span>
              <span class="preview-value">{{ estimatedFileSize }}</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">包含策略:</span>
              <span class="preview-value">{{ exportConfig.strategies.length }}个</span>
            </div>
            <div class="preview-item">
              <span class="preview-label">导出内容:</span>
              <span class="preview-value">{{ totalSelectedItems }}项</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 快速导出模板 -->
    <el-card class="quick-templates">
      <template #header>
        <span>
          <el-icon><Lightning /></el-icon>
          快速导出模板
        </span>
      </template>
      
      <div class="templates-grid">
        <div 
          v-for="template in quickTemplates"
          :key="template.id"
          class="template-card"
          @click="applyTemplate(template)"
        >
          <div class="template-icon">
            <el-icon>
              <component :is="template.icon" />
            </el-icon>
          </div>
          <div class="template-content">
            <h4 class="template-title">{{ template.name }}</h4>
            <p class="template-description">{{ template.description }}</p>
            <div class="template-meta">
              <span class="template-format">{{ template.format.toUpperCase() }}</span>
              <span class="template-size">{{ template.estimatedSize }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 导出历史 -->
    <el-card class="export-history">
      <template #header>
        <div class="history-header">
          <span>
            <el-icon><Clock /></el-icon>
            导出历史
          </span>
          <el-button @click="clearHistory" size="small" text>
            <el-icon><Delete /></el-icon>
            清空历史
          </el-button>
        </div>
      </template>
      
      <el-table :data="exportHistory" size="small" max-height="300">
        <el-table-column prop="fileName" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="format" label="格式" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.format.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="100" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusTagType(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="导出时间" width="150" align="center" />
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="downloadFile(row)"
              :disabled="row.status !== 'completed'"
              text
            >
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button 
              size="small" 
              @click="deleteExport(row)"
              text
              type="danger"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 导出操作 -->
    <div class="export-actions">
      <el-button 
        type="primary" 
        size="large"
        @click="startExport"
        :loading="exporting"
        :disabled="!canExport"
      >
        <el-icon><Download /></el-icon>
        开始导出
      </el-button>
      
      <el-button 
        size="large"
        @click="previewExport"
        :disabled="!canExport"
      >
        <el-icon><View /></el-icon>
        预览效果
      </el-button>
      
      <el-button 
        size="large"
        @click="saveAsTemplate"
      >
        <el-icon><DocumentAdd /></el-icon>
        保存为模板
      </el-button>
    </div>

    <!-- 导出进度对话框 -->
    <el-dialog
      v-model="progressDialogVisible"
      title="导出进度"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="export-progress">
        <div class="progress-info">
          <div class="current-task">
            <span class="task-label">当前任务:</span>
            <span class="task-name">{{ currentTask }}</span>
          </div>
          <div class="progress-stats">
            <span>{{ completedTasks }}/{{ totalTasks }} 已完成</span>
          </div>
        </div>
        
        <el-progress 
          :percentage="exportProgress" 
          :status="progressStatus"
          :stroke-width="12"
        />
        
        <div class="task-details">
          <div class="task-list">
            <div 
              v-for="task in exportTasks"
              :key="task.id"
              class="task-item"
              :class="{ 'completed': task.completed, 'current': task.current }"
            >
              <el-icon v-if="task.completed" class="task-icon completed">
                <Check />
              </el-icon>
              <el-icon v-else-if="task.current" class="task-icon current">
                <Loading />
              </el-icon>
              <el-icon v-else class="task-icon pending">
                <Clock />
              </el-icon>
              <span class="task-name">{{ task.name }}</span>
              <span v-if="task.completed" class="task-time">{{ task.duration }}s</span>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="cancelExport" :disabled="exportProgress === 100">
          {{ exportProgress === 100 ? '完成' : '取消' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="导出预览"
      width="80%"
      top="5vh"
    >
      <div class="export-preview-content">
        <div class="preview-toolbar">
          <el-radio-group v-model="previewMode" size="small">
            <el-radio-button label="structure">结构预览</el-radio-button>
            <el-radio-button label="content">内容预览</el-radio-button>
            <el-radio-button label="layout">布局预览</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="preview-body">
          <!-- 结构预览 -->
          <div v-if="previewMode === 'structure'" class="structure-preview">
            <el-tree
              :data="reportStructure"
              :props="{ children: 'children', label: 'label' }"
              show-checkbox
              default-expand-all
            />
          </div>
          
          <!-- 内容预览 -->
          <div v-if="previewMode === 'content'" class="content-preview">
            <div class="preview-page">
              <h2>策略分析报告</h2>
              <div class="preview-section">
                <h3>执行摘要</h3>
                <p>本报告分析了{{ exportConfig.strategies.length }}个策略的表现...</p>
              </div>
              <div class="preview-section">
                <h3>策略概览</h3>
                <div class="strategies-summary">
                  <div 
                    v-for="strategyId in exportConfig.strategies.slice(0, 3)"
                    :key="strategyId"
                    class="strategy-summary"
                  >
                    {{ getStrategyName(strategyId) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 布局预览 -->
          <div v-if="previewMode === 'layout'" class="layout-preview">
            <div class="page-layout">
              <div class="layout-header">页眉区域</div>
              <div class="layout-content">
                <div class="layout-sidebar">导航栏</div>
                <div class="layout-main">主要内容区域</div>
              </div>
              <div class="layout-footer">页脚区域</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Download, RefreshLeft, Lightning, Clock, Delete, View, DocumentAdd,
  Check, Loading, Document, PieChart, TrendCharts, DataLine
} from '@element-plus/icons-vue'

// 接口定义
interface Strategy {
  id: string
  name: string
  score: number
}

interface ExportConfig {
  type: 'report' | 'data' | 'charts' | 'summary'
  strategies: string[]
  dateRange: [string, string]
  content: {
    basic: string[]
    detailed: string[]
    charts: string[]
    analysis: string[]
  }
  format: string
  language: string
  template: string
  options: {
    includeWatermark: boolean
    compressFile: boolean
    encryptFile: boolean
    emailNotify: boolean
    autoSchedule: boolean
    cloudBackup: boolean
  }
}

interface QuickTemplate {
  id: string
  name: string
  description: string
  format: string
  estimatedSize: string
  icon: any
  config: Partial<ExportConfig>
}

interface ExportHistoryItem {
  id: string
  fileName: string
  format: string
  size: string
  status: 'completed' | 'failed' | 'processing'
  createTime: string
}

interface ExportTask {
  id: string
  name: string
  completed: boolean
  current: boolean
  duration?: number
}

// 响应式数据
const exporting = ref(false)
const progressDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const exportProgress = ref(0)
const currentTask = ref('')
const completedTasks = ref(0)
const totalTasks = ref(0)
const previewMode = ref('structure')

// 导出配置
const exportConfig = ref<ExportConfig>({
  type: 'report',
  strategies: [],
  dateRange: ['2023-01-01', '2023-12-31'],
  content: {
    basic: ['strategy_info', 'performance_metrics'],
    detailed: ['daily_returns', 'nav_curve'],
    charts: ['nav_chart', 'drawdown_chart'],
    analysis: ['executive_summary', 'ai_insights']
  },
  format: 'pdf',
  language: 'zh',
  template: 'standard',
  options: {
    includeWatermark: true,
    compressFile: false,
    encryptFile: false,
    emailNotify: false,
    autoSchedule: false,
    cloudBackup: false
  }
})

// 可用策略
const availableStrategies = ref<Strategy[]>([
  { id: 'strategy_1', name: 'LightGBM多因子策略v3.2', score: 9.2 },
  { id: 'strategy_2', name: 'XGBoost量化选股v2.8', score: 8.7 },
  { id: 'strategy_3', name: 'LSTM深度学习策略v1.5', score: 8.3 },
  { id: 'strategy_4', name: '多空对冲策略v2.1', score: 7.8 },
  { id: 'strategy_5', name: '动量反转混合策略v1.8', score: 7.3 }
])

// 快速模板
const quickTemplates = ref<QuickTemplate[]>([
  {
    id: 'investor_report',
    name: '投资者报告',
    description: '适合向投资者展示的专业报告',
    format: 'pdf',
    estimatedSize: '2-5MB',
    icon: Document,
    config: {
      type: 'report',
      content: {
        basic: ['strategy_info', 'performance_metrics', 'risk_metrics'],
        detailed: ['nav_curve'],
        charts: ['nav_chart', 'drawdown_chart', 'return_distribution'],
        analysis: ['executive_summary', 'ai_insights']
      },
      template: 'investor'
    }
  },
  {
    id: 'data_export',
    name: '数据导出',
    description: '导出完整的原始数据用于进一步分析',
    format: 'excel',
    estimatedSize: '5-15MB',
    icon: PieChart,
    config: {
      type: 'data',
      content: {
        basic: ['strategy_info', 'performance_metrics', 'risk_metrics'],
        detailed: ['daily_returns', 'positions', 'trades', 'nav_curve'],
        charts: [],
        analysis: []
      }
    }
  },
  {
    id: 'charts_collection',
    name: '图表集合',
    description: '导出所有图表用于演示',
    format: 'ppt',
    estimatedSize: '10-20MB',
    icon: TrendCharts,
    config: {
      type: 'charts',
      content: {
        basic: ['strategy_info'],
        detailed: [],
        charts: ['nav_chart', 'drawdown_chart', 'return_distribution', 'sector_allocation'],
        analysis: []
      }
    }
  },
  {
    id: 'executive_summary',
    name: '高管摘要',
    description: '简洁的高管层汇报材料',
    format: 'word',
    estimatedSize: '1-3MB',
    icon: DataLine,
    config: {
      type: 'summary',
      content: {
        basic: ['strategy_info', 'performance_metrics'],
        detailed: [],
        charts: ['nav_chart'],
        analysis: ['executive_summary']
      },
      template: 'simple'
    }
  }
])

// 导出历史
const exportHistory = ref<ExportHistoryItem[]>([
  {
    id: 'export_1',
    fileName: 'LightGBM策略分析报告_20231215.pdf',
    format: 'pdf',
    size: '3.2MB',
    status: 'completed',
    createTime: '2023-12-15 14:30:25'
  },
  {
    id: 'export_2',
    fileName: '多策略对比数据_20231214.xlsx',
    format: 'excel',
    size: '8.7MB',
    status: 'completed',
    createTime: '2023-12-14 16:45:12'
  },
  {
    id: 'export_3',
    fileName: '图表集合_20231213.pptx',
    format: 'ppt',
    size: '15.3MB',
    status: 'failed',
    createTime: '2023-12-13 10:22:08'
  }
])

// 导出任务
const exportTasks = ref<ExportTask[]>([
  { id: 'task_1', name: '准备数据', completed: false, current: false },
  { id: 'task_2', name: '生成图表', completed: false, current: false },
  { id: 'task_3', name: '渲染报告', completed: false, current: false },
  { id: 'task_4', name: '文件打包', completed: false, current: false },
  { id: 'task_5', name: '上传存储', completed: false, current: false }
])

// 报告结构
const reportStructure = ref([
  {
    label: '策略分析报告',
    children: [
      { label: '封面页' },
      { label: '目录' },
      {
        label: '执行摘要',
        children: [
          { label: '策略概述' },
          { label: '核心指标' },
          { label: '主要结论' }
        ]
      },
      {
        label: '策略详情',
        children: [
          { label: '策略信息' },
          { label: '性能指标' },
          { label: '风险分析' }
        ]
      },
      {
        label: '图表分析',
        children: [
          { label: '净值走势' },
          { label: '回撤分析' },
          { label: '收益分布' }
        ]
      },
      { label: 'AI分析洞察' },
      { label: '附录' }
    ]
  }
])

// 计算属性
const canExport = computed(() => {
  return exportConfig.value.strategies.length > 0
})

const totalSelectedItems = computed(() => {
  const { basic, detailed, charts, analysis } = exportConfig.value.content
  return basic.length + detailed.length + charts.length + analysis.length
})

const estimatedFileSize = computed(() => {
  let sizeKB = 500 // 基础大小
  
  // 根据策略数量
  sizeKB += exportConfig.value.strategies.length * 200
  
  // 根据内容类型
  sizeKB += exportConfig.value.content.basic.length * 50
  sizeKB += exportConfig.value.content.detailed.length * 500
  sizeKB += exportConfig.value.content.charts.length * 1000
  sizeKB += exportConfig.value.content.analysis.length * 300
  
  // 根据格式
  if (exportConfig.value.format === 'pdf') sizeKB *= 1.2
  if (exportConfig.value.format === 'ppt') sizeKB *= 2
  
  if (sizeKB < 1024) return `${Math.round(sizeKB)}KB`
  return `${(sizeKB / 1024).toFixed(1)}MB`
})

const progressStatus = computed(() => {
  if (exportProgress.value === 100) return 'success'
  if (exportProgress.value > 0) return undefined
  return 'exception'
})

// 方法
const getPerformanceTagType = (score: number) => {
  if (score >= 9) return 'success'
  if (score >= 8) return 'primary'
  if (score >= 7) return 'warning'
  return 'danger'
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'primary'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'processing': return '处理中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

const getStrategyName = (strategyId: string) => {
  const strategy = availableStrategies.value.find(s => s.id === strategyId)
  return strategy ? strategy.name : '未知策略'
}

const generateFileName = () => {
  const typeMap = {
    report: '分析报告',
    data: '数据导出',
    charts: '图表集合',
    summary: '摘要报告'
  }
  
  const formatMap = {
    pdf: 'pdf',
    excel: 'xlsx',
    word: 'docx',
    ppt: 'pptx',
    json: 'json',
    csv: 'csv'
  }
  
  const date = new Date().toISOString().split('T')[0].replace(/-/g, '')
  const typeName = typeMap[exportConfig.value.type]
  const ext = formatMap[exportConfig.value.format] || 'pdf'
  
  return `${typeName}_${date}.${ext}`
}

const resetConfig = () => {
  exportConfig.value = {
    type: 'report',
    strategies: [],
    dateRange: ['2023-01-01', '2023-12-31'],
    content: {
      basic: ['strategy_info', 'performance_metrics'],
      detailed: ['daily_returns', 'nav_curve'],
      charts: ['nav_chart', 'drawdown_chart'],
      analysis: ['executive_summary', 'ai_insights']
    },
    format: 'pdf',
    language: 'zh',
    template: 'standard',
    options: {
      includeWatermark: true,
      compressFile: false,
      encryptFile: false,
      emailNotify: false,
      autoSchedule: false,
      cloudBackup: false
    }
  }
  ElMessage.info('配置已重置')
}

const applyTemplate = (template: QuickTemplate) => {
  Object.assign(exportConfig.value, template.config)
  exportConfig.value.format = template.format
  ElMessage.success(`已应用模板: ${template.name}`)
}

const startExport = () => {
  if (!canExport.value) {
    ElMessage.warning('请先选择要导出的策略')
    return
  }
  
  exporting.value = true
  progressDialogVisible.value = true
  exportProgress.value = 0
  completedTasks.value = 0
  totalTasks.value = exportTasks.value.length
  
  // 重置任务状态
  exportTasks.value.forEach(task => {
    task.completed = false
    task.current = false
    task.duration = undefined
  })
  
  // 模拟导出过程
  let currentTaskIndex = 0
  
  const executeTask = () => {
    if (currentTaskIndex >= exportTasks.value.length) {
      // 导出完成
      exporting.value = false
      exportProgress.value = 100
      currentTask.value = '导出完成'
      
      // 添加到历史记录
      const newExport: ExportHistoryItem = {
        id: `export_${Date.now()}`,
        fileName: generateFileName(),
        format: exportConfig.value.format,
        size: estimatedFileSize.value,
        status: 'completed',
        createTime: new Date().toLocaleString('zh-CN')
      }
      exportHistory.value.unshift(newExport)
      
      ElMessage.success('导出完成！')
      return
    }
    
    const task = exportTasks.value[currentTaskIndex]
    task.current = true
    currentTask.value = task.name
    
    setTimeout(() => {
      task.completed = true
      task.current = false
      task.duration = Math.floor(Math.random() * 3) + 1
      completedTasks.value++
      exportProgress.value = Math.round((completedTasks.value / totalTasks.value) * 100)
      
      currentTaskIndex++
      executeTask()
    }, 1000 + Math.random() * 2000)
  }
  
  executeTask()
}

const cancelExport = () => {
  if (exportProgress.value === 100) {
    progressDialogVisible.value = false
    return
  }
  
  ElMessageBox.confirm('确定要取消导出吗？', '确认', {
    confirmButtonText: '确定',
    cancelButtonText: '继续导出',
    type: 'warning',
  }).then(() => {
    exporting.value = false
    progressDialogVisible.value = false
    ElMessage.info('导出已取消')
  }).catch(() => {
    // 继续导出
  })
}

const previewExport = () => {
  if (!canExport.value) {
    ElMessage.warning('请先选择要导出的策略')
    return
  }
  
  previewDialogVisible.value = true
}

const saveAsTemplate = () => {
  ElMessage.success('配置已保存为自定义模板')
}

const clearHistory = () => {
  ElMessageBox.confirm('确定要清空导出历史吗？', '确认清空', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    exportHistory.value = []
    ElMessage.success('历史记录已清空')
  })
}

const downloadFile = (item: ExportHistoryItem) => {
  ElMessage.success(`开始下载 ${item.fileName}`)
}

const deleteExport = (item: ExportHistoryItem) => {
  ElMessageBox.confirm(`确定要删除 "${item.fileName}" 吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    const index = exportHistory.value.findIndex(h => h.id === item.id)
    if (index > -1) {
      exportHistory.value.splice(index, 1)
      ElMessage.success('文件已删除')
    }
  })
}

// 暴露给父组件的方法
defineExpose({
  startExport,
  setStrategies: (strategies: string[]) => {
    exportConfig.value.strategies = strategies
  },
  applyTemplate,
  getExportHistory: () => exportHistory.value
})

onMounted(() => {
  // 初始化，选择第一个策略
  if (availableStrategies.value.length > 0) {
    exportConfig.value.strategies = [availableStrategies.value[0].id]
  }
})
</script>

<style scoped>
.results-exporter {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.export-config {
  margin-bottom: 24px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.export-types {
  display: flex;
  gap: 8px;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.strategy-name {
  font-weight: 600;
  color: #303133;
}

.content-options {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.option-group {
  margin-bottom: 16px;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.format-option {
  width: 100%;
}

.advanced-options {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.export-preview {
  padding: 16px;
  background: #f0f8ff;
  border-radius: 6px;
  border: 1px solid #d4e4fd;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.preview-label {
  color: #606266;
}

.preview-value {
  color: #303133;
  font-weight: 600;
}

.quick-templates {
  margin-bottom: 24px;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.template-card {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.template-card:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

.template-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  flex-shrink: 0;
}

.template-content {
  flex: 1;
}

.template-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.template-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.template-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.template-format {
  padding: 2px 6px;
  background: #e4e7ed;
  border-radius: 3px;
}

.export-history {
  margin-bottom: 24px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.export-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
}

.export-progress {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.current-task {
  display: flex;
  gap: 8px;
  align-items: center;
}

.task-label {
  color: #606266;
}

.task-name {
  color: #303133;
  font-weight: 600;
}

.progress-stats {
  color: #909399;
  font-size: 14px;
}

.task-details {
  margin-top: 16px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.task-item.completed {
  background: #f0f9ff;
}

.task-item.current {
  background: #fff7e6;
}

.task-icon {
  font-size: 16px;
}

.task-icon.completed {
  color: #67c23a;
}

.task-icon.current {
  color: #e6a23c;
}

.task-icon.pending {
  color: #c0c4cc;
}

.task-name {
  flex: 1;
  color: #303133;
}

.task-time {
  color: #909399;
  font-size: 12px;
}

.export-preview-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 60vh;
}

.preview-toolbar {
  display: flex;
  justify-content: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.preview-body {
  flex: 1;
  overflow: auto;
  padding: 16px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.structure-preview {
  height: 100%;
}

.content-preview {
  height: 100%;
}

.preview-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.preview-page h2 {
  text-align: center;
  color: #303133;
  margin-bottom: 40px;
}

.preview-section {
  margin-bottom: 32px;
}

.preview-section h3 {
  color: #409eff;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.strategies-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.strategy-summary {
  padding: 12px;
  background: #f0f8ff;
  border-radius: 4px;
  color: #303133;
}

.layout-preview {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.page-layout {
  width: 600px;
  height: 400px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.layout-header {
  height: 60px;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px 6px 0 0;
}

.layout-content {
  flex: 1;
  display: flex;
}

.layout-sidebar {
  width: 150px;
  background: #f0f8ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
}

.layout-main {
  flex: 1;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #303133;
}

.layout-footer {
  height: 40px;
  background: #909399;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0 0 6px 6px;
}

@media (max-width: 768px) {
  .export-types {
    flex-direction: column;
  }
  
  .templates-grid {
    grid-template-columns: 1fr;
  }
  
  .template-card {
    flex-direction: column;
    text-align: center;
  }
  
  .export-actions {
    flex-direction: column;
  }
  
  .progress-info {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .impact-metrics {
    flex-direction: column;
  }
}
</style>