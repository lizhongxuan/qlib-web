<template>
  <div class="optimization-suggestions">
    <!-- 头部控制 -->
    <div class="suggestions-header">
      <div class="header-info">
        <h3 class="title">
          <el-icon><MagicStick /></el-icon>
          AI策略优化建议
        </h3>
        <p class="subtitle">基于深度学习分析的智能化投资策略优化方案</p>
      </div>
      
      <div class="header-controls">
        <el-select v-model="selectedStrategy" @change="handleStrategyChange" style="width: 250px; margin-right: 12px;">
          <el-option 
            v-for="strategy in strategies" 
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          />
        </el-select>
        
        <el-button @click="regenerateSuggestions" :loading="generating" type="primary">
          <el-icon><Refresh /></el-icon>
          重新生成
        </el-button>
        
        <el-button @click="exportSuggestions">
          <el-icon><Download /></el-icon>
          导出建议
        </el-button>
      </div>
    </div>

    <!-- 分析状态 -->
    <el-card v-if="currentStrategy" class="analysis-status">
      <div class="status-content">
        <div class="strategy-info">
          <div class="strategy-avatar">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="strategy-details">
            <h4 class="strategy-name">{{ currentStrategy.name }}</h4>
            <div class="strategy-metrics">
              <span class="metric">年化收益: <strong>{{ formatPercent(currentStrategy.annualReturn) }}</strong></span>
              <span class="metric">夏普比率: <strong>{{ currentStrategy.sharpeRatio.toFixed(2) }}</strong></span>
              <span class="metric">最大回撤: <strong>{{ formatPercent(Math.abs(currentStrategy.maxDrawdown)) }}</strong></span>
            </div>
          </div>
        </div>
        
        <div class="analysis-progress">
          <div class="progress-info">
            <span class="progress-label">AI分析进度</span>
            <span class="progress-status">{{ analysisStatus }}</span>
          </div>
          <el-progress 
            :percentage="analysisProgress" 
            :status="progressStatus"
            :stroke-width="8"
          />
        </div>
      </div>
    </el-card>

    <!-- 优化建议主内容 -->
    <div v-if="suggestions.length > 0" class="suggestions-content">
      <!-- 总览摘要 -->
      <el-card class="summary-card">
        <template #header>
          <div class="summary-header">
            <span>
              <el-icon><DataLine /></el-icon>
              优化潜力评估
            </span>
            <el-tag :type="getSummaryTagType(optimizationSummary.potential)" size="large">
              {{ optimizationSummary.potential }}
            </el-tag>
          </div>
        </template>
        
        <div class="summary-content">
          <el-row :gutter="24">
            <el-col :span="8">
              <div class="summary-metric">
                <div class="metric-icon positive">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="metric-content">
                  <div class="metric-value">+{{ optimizationSummary.expectedReturn }}%</div>
                  <div class="metric-label">预期收益提升</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="summary-metric">
                <div class="metric-icon info">
                  <el-icon><Shield /></el-icon>
                </div>
                <div class="metric-content">
                  <div class="metric-value">-{{ optimizationSummary.riskReduction }}%</div>
                  <div class="metric-label">风险降低</div>
                </div>
              </div>
            </el-col>
            
            <el-col :span="8">
              <div class="summary-metric">
                <div class="metric-icon warning">
                  <el-icon><Clock /></el-icon>
                </div>
                <div class="metric-content">
                  <div class="metric-value">{{ optimizationSummary.implementationTime }}</div>
                  <div class="metric-label">实施周期</div>
                </div>
              </div>
            </el-col>
          </el-row>
          
          <div class="summary-description">
            <p>{{ optimizationSummary.description }}</p>
          </div>
        </div>
      </el-card>

      <!-- 分类建议 -->
      <div class="suggestions-categories">
        <el-tabs v-model="activeCategory" type="card">
          <!-- 收益优化 -->
          <el-tab-pane label="收益优化" name="returns">
            <div class="category-content">
              <div class="category-intro">
                <el-alert
                  title="收益优化建议"
                  description="通过因子调整、模型优化等方式提升策略收益能力"
                  type="success"
                  :closable="false"
                  show-icon
                />
              </div>
              
              <div class="suggestions-list">
                <div 
                  v-for="suggestion in categorizedSuggestions.returns" 
                  :key="suggestion.id"
                  class="suggestion-item"
                  :class="[`priority-${suggestion.priority}`, { 'implemented': suggestion.implemented }]"
                >
                  <div class="suggestion-header">
                    <div class="suggestion-meta">
                      <el-tag 
                        :type="getPriorityTagType(suggestion.priority)" 
                        size="small"
                        class="priority-tag"
                      >
                        {{ getPriorityText(suggestion.priority) }}优先级
                      </el-tag>
                      
                      <span class="suggestion-category">{{ suggestion.category }}</span>
                      
                      <el-tag 
                        v-if="suggestion.implemented" 
                        type="success" 
                        size="small"
                      >
                        已实施
                      </el-tag>
                    </div>
                    
                    <div class="suggestion-actions">
                      <el-button 
                        size="small" 
                        @click="toggleSuggestionDetail(suggestion.id)"
                        text
                      >
                        <el-icon><View /></el-icon>
                        详情
                      </el-button>
                      
                      <el-button 
                        size="small" 
                        type="primary"
                        @click="implementSuggestion(suggestion)"
                        :disabled="suggestion.implemented"
                      >
                        <el-icon><Check /></el-icon>
                        {{ suggestion.implemented ? '已实施' : '实施' }}
                      </el-button>
                    </div>
                  </div>
                  
                  <div class="suggestion-content">
                    <h4 class="suggestion-title">{{ suggestion.title }}</h4>
                    <p class="suggestion-description">{{ suggestion.description }}</p>
                    
                    <div class="suggestion-impact">
                      <div class="impact-metrics">
                        <div class="impact-item">
                          <span class="impact-label">预期收益提升:</span>
                          <span class="impact-value positive">+{{ suggestion.expectedImprovement.return }}%</span>
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">实施难度:</span>
                          <el-rate 
                            v-model="suggestion.difficulty" 
                            disabled 
                            show-score 
                            text-color="#ff9900"
                            max="5"
                            size="small"
                          />
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">实施时间:</span>
                          <span class="impact-value">{{ suggestion.estimatedTime }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 详细信息（可展开） -->
                    <el-collapse-transition>
                      <div v-show="expandedSuggestions.includes(suggestion.id)" class="suggestion-details">
                        <el-divider />
                        
                        <div class="detail-section">
                          <h5>实施步骤</h5>
                          <ol class="implementation-steps">
                            <li v-for="step in suggestion.implementationSteps" :key="step">
                              {{ step }}
                            </li>
                          </ol>
                        </div>
                        
                        <div class="detail-section">
                          <h5>风险评估</h5>
                          <div class="risk-assessment">
                            <el-tag 
                              :type="getRiskTagType(suggestion.riskLevel)" 
                              size="small"
                            >
                              {{ suggestion.riskLevel }}风险
                            </el-tag>
                            <span class="risk-description">{{ suggestion.riskDescription }}</span>
                          </div>
                        </div>
                        
                        <div class="detail-section">
                          <h5>历史案例</h5>
                          <div class="historical-cases">
                            <div 
                              v-for="case_ in suggestion.historicalCases" 
                              :key="case_.name"
                              class="case-item"
                            >
                              <span class="case-name">{{ case_.name }}</span>
                              <span class="case-result" :class="case_.success ? 'positive' : 'negative'">
                                {{ case_.success ? '成功' : '失败' }}: {{ case_.result }}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </el-collapse-transition>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 风险控制 -->
          <el-tab-pane label="风险控制" name="risk">
            <div class="category-content">
              <div class="category-intro">
                <el-alert
                  title="风险控制建议"
                  description="通过优化止损、仓位管理等方式降低策略风险"
                  type="warning"
                  :closable="false"
                  show-icon
                />
              </div>
              
              <div class="suggestions-list">
                <div 
                  v-for="suggestion in categorizedSuggestions.risk" 
                  :key="suggestion.id"
                  class="suggestion-item"
                  :class="[`priority-${suggestion.priority}`, { 'implemented': suggestion.implemented }]"
                >
                  <div class="suggestion-header">
                    <div class="suggestion-meta">
                      <el-tag 
                        :type="getPriorityTagType(suggestion.priority)" 
                        size="small"
                        class="priority-tag"
                      >
                        {{ getPriorityText(suggestion.priority) }}优先级
                      </el-tag>
                      
                      <span class="suggestion-category">{{ suggestion.category }}</span>
                      
                      <el-tag 
                        v-if="suggestion.implemented" 
                        type="success" 
                        size="small"
                      >
                        已实施
                      </el-tag>
                    </div>
                    
                    <div class="suggestion-actions">
                      <el-button 
                        size="small" 
                        @click="toggleSuggestionDetail(suggestion.id)"
                        text
                      >
                        <el-icon><View /></el-icon>
                        详情
                      </el-button>
                      
                      <el-button 
                        size="small" 
                        type="primary"
                        @click="implementSuggestion(suggestion)"
                        :disabled="suggestion.implemented"
                      >
                        <el-icon><Check /></el-icon>
                        {{ suggestion.implemented ? '已实施' : '实施' }}
                      </el-button>
                    </div>
                  </div>
                  
                  <div class="suggestion-content">
                    <h4 class="suggestion-title">{{ suggestion.title }}</h4>
                    <p class="suggestion-description">{{ suggestion.description }}</p>
                    
                    <div class="suggestion-impact">
                      <div class="impact-metrics">
                        <div class="impact-item">
                          <span class="impact-label">风险降低:</span>
                          <span class="impact-value info">-{{ suggestion.expectedImprovement.risk }}%</span>
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">实施难度:</span>
                          <el-rate 
                            v-model="suggestion.difficulty" 
                            disabled 
                            show-score 
                            text-color="#ff9900"
                            max="5"
                            size="small"
                          />
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">实施时间:</span>
                          <span class="impact-value">{{ suggestion.estimatedTime }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 执行效率 -->
          <el-tab-pane label="执行效率" name="execution">
            <div class="category-content">
              <div class="category-intro">
                <el-alert
                  title="执行效率优化"
                  description="通过优化交易频率、降低成本等方式提升策略执行效率"
                  type="info"
                  :closable="false"
                  show-icon
                />
              </div>
              
              <div class="suggestions-list">
                <div 
                  v-for="suggestion in categorizedSuggestions.execution" 
                  :key="suggestion.id"
                  class="suggestion-item"
                  :class="[`priority-${suggestion.priority}`, { 'implemented': suggestion.implemented }]"
                >
                  <div class="suggestion-header">
                    <div class="suggestion-meta">
                      <el-tag 
                        :type="getPriorityTagType(suggestion.priority)" 
                        size="small"
                        class="priority-tag"
                      >
                        {{ getPriorityText(suggestion.priority) }}优先级
                      </el-tag>
                      
                      <span class="suggestion-category">{{ suggestion.category }}</span>
                      
                      <el-tag 
                        v-if="suggestion.implemented" 
                        type="success" 
                        size="small"
                      >
                        已实施
                      </el-tag>
                    </div>
                    
                    <div class="suggestion-actions">
                      <el-button 
                        size="small" 
                        @click="toggleSuggestionDetail(suggestion.id)"
                        text
                      >
                        <el-icon><View /></el-icon>
                        详情
                      </el-button>
                      
                      <el-button 
                        size="small" 
                        type="primary"
                        @click="implementSuggestion(suggestion)"
                        :disabled="suggestion.implemented"
                      >
                        <el-icon><Check /></el-icon>
                        {{ suggestion.implemented ? '已实施' : '实施' }}
                      </el-button>
                    </div>
                  </div>
                  
                  <div class="suggestion-content">
                    <h4 class="suggestion-title">{{ suggestion.title }}</h4>
                    <p class="suggestion-description">{{ suggestion.description }}</p>
                    
                    <div class="suggestion-impact">
                      <div class="impact-metrics">
                        <div class="impact-item">
                          <span class="impact-label">效率提升:</span>
                          <span class="impact-value warning">+{{ suggestion.expectedImprovement.efficiency }}%</span>
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">成本节约:</span>
                          <span class="impact-value positive">-{{ suggestion.expectedImprovement.cost }}%</span>
                        </div>
                        <div class="impact-item">
                          <span class="impact-label">实施时间:</span>
                          <span class="impact-value">{{ suggestion.estimatedTime }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 实施计划 -->
      <el-card class="implementation-plan">
        <template #header>
          <span>
            <el-icon><Calendar /></el-icon>
            优化实施计划
          </span>
        </template>
        
        <div class="plan-content">
          <div class="plan-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="phase in implementationPlan"
                :key="phase.id"
                :timestamp="phase.timeframe"
                placement="top"
                :type="getPhaseType(phase.priority)"
                :hollow="!phase.started"
              >
                <el-card class="timeline-card">
                  <div class="phase-header">
                    <h4 class="phase-title">{{ phase.title }}</h4>
                    <el-tag :type="getPhaseStatusType(phase.status)" size="small">
                      {{ getPhaseStatusText(phase.status) }}
                    </el-tag>
                  </div>
                  
                  <div class="phase-content">
                    <p class="phase-description">{{ phase.description }}</p>
                    
                    <div class="phase-suggestions">
                      <span class="suggestions-label">包含建议:</span>
                      <div class="suggestion-tags">
                        <el-tag 
                          v-for="suggestionId in phase.suggestionIds"
                          :key="suggestionId"
                          size="small"
                          class="suggestion-tag"
                        >
                          {{ getSuggestionTitle(suggestionId) }}
                        </el-tag>
                      </div>
                    </div>
                    
                    <div class="phase-metrics">
                      <div class="metric">
                        <span class="label">预期收益提升:</span>
                        <span class="value positive">+{{ phase.expectedImprovement.return }}%</span>
                      </div>
                      <div class="metric">
                        <span class="label">风险降低:</span>
                        <span class="value info">-{{ phase.expectedImprovement.risk }}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="phase-actions">
                    <el-button 
                      size="small" 
                      type="primary"
                      @click="startPhase(phase)"
                      :disabled="phase.started"
                    >
                      {{ phase.started ? '已开始' : '开始实施' }}
                    </el-button>
                    
                    <el-button 
                      size="small"
                      @click="viewPhaseDetail(phase)"
                    >
                      查看详情
                    </el-button>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无优化建议，请先选择策略进行分析" image-size="120">
      <el-button type="primary" @click="generateInitialSuggestions">
        开始AI分析
      </el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick, Refresh, Download, TrendCharts, DataLine, Shield, Clock,
  View, Check, Calendar
} from '@element-plus/icons-vue'

// 接口定义
interface Strategy {
  id: string
  name: string
  annualReturn: number
  sharpeRatio: number
  maxDrawdown: number
}

interface Suggestion {
  id: string
  title: string
  description: string
  category: string
  priority: 'high' | 'medium' | 'low'
  type: 'returns' | 'risk' | 'execution'
  difficulty: number
  estimatedTime: string
  implemented: boolean
  expectedImprovement: {
    return?: number
    risk?: number
    efficiency?: number
    cost?: number
  }
  implementationSteps: string[]
  riskLevel: 'low' | 'medium' | 'high'
  riskDescription: string
  historicalCases: Array<{
    name: string
    success: boolean
    result: string
  }>
}

interface ImplementationPhase {
  id: string
  title: string
  description: string
  timeframe: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed'
  started: boolean
  suggestionIds: string[]
  expectedImprovement: {
    return: number
    risk: number
  }
}

// 响应式数据
const generating = ref(false)
const selectedStrategy = ref('strategy_1')
const activeCategory = ref('returns')
const analysisProgress = ref(0)
const analysisStatus = ref('准备分析')
const expandedSuggestions = ref<string[]>([])

// 模拟数据
const strategies = ref<Strategy[]>([
  {
    id: 'strategy_1',
    name: 'LightGBM多因子策略v3.2',
    annualReturn: 0.285,
    sharpeRatio: 1.45,
    maxDrawdown: -0.082
  },
  {
    id: 'strategy_2',
    name: 'XGBoost量化选股v2.8',
    annualReturn: 0.231,
    sharpeRatio: 1.28,
    maxDrawdown: -0.095
  }
])

const optimizationSummary = ref({
  potential: '高潜力',
  expectedReturn: 3.2,
  riskReduction: 15,
  implementationTime: '4-6周',
  description: '通过因子权重优化、风险管理改进和交易执行优化，该策略有望在保持当前收益水平的基础上，显著降低风险并提升整体表现。'
})

const suggestions = ref<Suggestion[]>([
  {
    id: 'suggestion_1',
    title: '优化因子权重配置',
    description: '基于最新市场数据重新训练模型，调整各因子权重分配，提升策略在不同市场环境下的适应性',
    category: '模型优化',
    priority: 'high',
    type: 'returns',
    difficulty: 3,
    estimatedTime: '2-3周',
    implemented: false,
    expectedImprovement: {
      return: 2.3,
      risk: 8
    },
    implementationSteps: [
      '收集最近6个月的市场数据',
      '重新训练因子权重模型',
      '回测验证新权重配置',
      '逐步部署到生产环境'
    ],
    riskLevel: 'medium',
    riskDescription: '模型重训可能导致短期性能波动',
    historicalCases: [
      {
        name: '2023年Q2因子权重调整',
        success: true,
        result: '收益提升1.8%，夏普比率提升0.12'
      }
    ]
  },
  {
    id: 'suggestion_2',
    title: '增强止损机制',
    description: '实施动态止损策略，根据市场波动率和个股特性调整止损阈值，减少大幅回撤风险',
    category: '风险控制',
    priority: 'high',
    type: 'risk',
    difficulty: 2,
    estimatedTime: '1-2周',
    implemented: false,
    expectedImprovement: {
      risk: 20,
      return: -0.5
    },
    implementationSteps: [
      '分析历史回撤模式',
      '设计动态止损算法',
      '回测验证止损效果',
      '部署止损监控系统'
    ],
    riskLevel: 'low',
    riskDescription: '可能略微降低收益率，但风险控制效果显著',
    historicalCases: [
      {
        name: '2023年市场调整期止损应用',
        success: true,
        result: '最大回撤从-12%降至-8%'
      }
    ]
  },
  {
    id: 'suggestion_3',
    title: '优化交易执行策略',
    description: '改进交易时机选择和订单执行方式，减少市场冲击成本和滑点损失',
    category: '执行优化',
    priority: 'medium',
    type: 'execution',
    difficulty: 2,
    estimatedTime: '2-3周',
    implemented: false,
    expectedImprovement: {
      efficiency: 15,
      cost: 25
    },
    implementationSteps: [
      '分析交易成本构成',
      '优化订单拆分策略',
      '改进交易时机算法',
      '监控执行效果'
    ],
    riskLevel: 'low',
    riskDescription: '执行优化风险较低，主要关注系统稳定性',
    historicalCases: [
      {
        name: '大单拆分策略优化',
        success: true,
        result: '交易成本降低0.3%，年化收益提升0.8%'
      }
    ]
  }
])

const implementationPlan = ref<ImplementationPhase[]>([
  {
    id: 'phase_1',
    title: '第一阶段：紧急风险控制',
    description: '优先实施风险控制相关建议，确保策略安全性',
    timeframe: '第1-2周',
    priority: 'high',
    status: 'pending',
    started: false,
    suggestionIds: ['suggestion_2'],
    expectedImprovement: {
      return: -0.5,
      risk: 20
    }
  },
  {
    id: 'phase_2',
    title: '第二阶段：收益优化',
    description: '实施收益提升相关建议，提高策略盈利能力',
    timeframe: '第3-5周',
    priority: 'high',
    status: 'pending',
    started: false,
    suggestionIds: ['suggestion_1'],
    expectedImprovement: {
      return: 2.3,
      risk: 8
    }
  },
  {
    id: 'phase_3',
    title: '第三阶段：执行优化',
    description: '优化交易执行和成本控制，提升整体效率',
    timeframe: '第6-8周',
    priority: 'medium',
    status: 'pending',
    started: false,
    suggestionIds: ['suggestion_3'],
    expectedImprovement: {
      return: 0.8,
      risk: 0
    }
  }
])

// 计算属性
const currentStrategy = computed(() => {
  return strategies.value.find(s => s.id === selectedStrategy.value)
})

const categorizedSuggestions = computed(() => {
  return {
    returns: suggestions.value.filter(s => s.type === 'returns'),
    risk: suggestions.value.filter(s => s.type === 'risk'),
    execution: suggestions.value.filter(s => s.type === 'execution')
  }
})

const progressStatus = computed(() => {
  if (analysisProgress.value === 100) return 'success'
  if (analysisProgress.value > 0) return undefined
  return 'exception'
})

// 方法
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`
}

const getSummaryTagType = (potential: string) => {
  switch (potential) {
    case '高潜力': return 'success'
    case '中等潜力': return 'warning'
    case '低潜力': return 'info'
    default: return 'info'
  }
}

const getPriorityTagType = (priority: string) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'info'
  }
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'high': return '高'
    case 'medium': return '中'
    case 'low': return '低'
    default: return '普通'
  }
}

const getRiskTagType = (riskLevel: string) => {
  switch (riskLevel) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'success'
    default: return 'info'
  }
}

const getPhaseType = (priority: string) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'primary'
  }
}

const getPhaseStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'in_progress': return 'primary'
    case 'pending': return 'info'
    default: return 'info'
  }
}

const getPhaseStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'in_progress': return '进行中'
    case 'pending': return '待开始'
    default: return '未知'
  }
}

const getSuggestionTitle = (suggestionId: string) => {
  const suggestion = suggestions.value.find(s => s.id === suggestionId)
  return suggestion ? suggestion.title : '未知建议'
}

const handleStrategyChange = () => {
  // 重新生成建议
  regenerateSuggestions()
}

const regenerateSuggestions = () => {
  generating.value = true
  analysisProgress.value = 0
  analysisStatus.value = '开始分析...'
  
  // 模拟分析进度
  const progressInterval = setInterval(() => {
    analysisProgress.value += 10
    
    if (analysisProgress.value <= 30) {
      analysisStatus.value = '数据收集中...'
    } else if (analysisProgress.value <= 60) {
      analysisStatus.value = 'AI模型分析中...'
    } else if (analysisProgress.value <= 90) {
      analysisStatus.value = '生成优化建议...'
    } else {
      analysisStatus.value = '分析完成'
      clearInterval(progressInterval)
      generating.value = false
      ElMessage.success('AI优化建议已更新')
    }
  }, 200)
}

const toggleSuggestionDetail = (suggestionId: string) => {
  const index = expandedSuggestions.value.indexOf(suggestionId)
  if (index > -1) {
    expandedSuggestions.value.splice(index, 1)
  } else {
    expandedSuggestions.value.push(suggestionId)
  }
}

const implementSuggestion = (suggestion: Suggestion) => {
  ElMessageBox.confirm(
    `确定要实施建议 "${suggestion.title}" 吗？此操作将修改策略配置。`,
    '确认实施',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    suggestion.implemented = true
    ElMessage.success(`建议 "${suggestion.title}" 已标记为实施`)
  }).catch(() => {
    ElMessage.info('已取消实施')
  })
}

const startPhase = (phase: ImplementationPhase) => {
  ElMessageBox.confirm(
    `确定要开始实施 "${phase.title}" 吗？`,
    '确认开始',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    }
  ).then(() => {
    phase.started = true
    phase.status = 'in_progress'
    ElMessage.success(`${phase.title} 已开始实施`)
  }).catch(() => {
    ElMessage.info('已取消')
  })
}

const viewPhaseDetail = (phase: ImplementationPhase) => {
  ElMessage.info(`查看 ${phase.title} 详细信息`)
}

const exportSuggestions = () => {
  ElMessage.success('优化建议报告导出已开始')
}

const generateInitialSuggestions = () => {
  regenerateSuggestions()
}

// 暴露给父组件的方法
defineExpose({
  regenerateSuggestions,
  getSuggestionsByType: (type: string) => suggestions.value.filter(s => s.type === type),
  getImplementationPlan: () => implementationPlan.value
})

onMounted(() => {
  // 初始加载
  if (currentStrategy.value) {
    regenerateSuggestions()
  }
})
</script>

<style scoped>
.optimization-suggestions {
  width: 100%;
}

.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 0 8px;
}

.header-info {
  flex: 1;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.analysis-status {
  margin-bottom: 24px;
}

.status-content {
  display: flex;
  gap: 24px;
  align-items: center;
}

.strategy-info {
  display: flex;
  gap: 16px;
  align-items: center;
  flex: 1;
}

.strategy-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
}

.strategy-details {
  flex: 1;
}

.strategy-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.strategy-metrics {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.metric strong {
  color: #303133;
}

.analysis-progress {
  width: 300px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.progress-label {
  color: #303133;
  font-weight: 600;
}

.progress-status {
  color: #606266;
}

.suggestions-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-card {
  margin-bottom: 24px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-metric {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}

.metric-icon.positive {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.metric-icon.info {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.metric-icon.warning {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
}

.summary-description {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.summary-description p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.suggestions-categories {
  margin-bottom: 24px;
}

.category-content {
  padding: 16px 0;
}

.category-intro {
  margin-bottom: 20px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.suggestion-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s;
}

.suggestion-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.suggestion-item.priority-high {
  border-left: 4px solid #f56c6c;
}

.suggestion-item.priority-medium {
  border-left: 4px solid #e6a23c;
}

.suggestion-item.priority-low {
  border-left: 4px solid #409eff;
}

.suggestion-item.implemented {
  background: #f0f9ff;
  border-color: #b3d8ff;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.suggestion-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.suggestion-category {
  color: #909399;
  font-size: 14px;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
}

.suggestion-content {
  padding: 20px;
}

.suggestion-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.suggestion-description {
  color: #606266;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.suggestion-impact {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 16px;
}

.impact-metrics {
  display: flex;
  gap: 24px;
  align-items: center;
}

.impact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.impact-label {
  color: #606266;
}

.impact-value {
  font-weight: 600;
}

.impact-value.positive {
  color: #67c23a;
}

.impact-value.info {
  color: #409eff;
}

.impact-value.warning {
  color: #e6a23c;
}

.suggestion-details {
  padding-top: 20px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h5 {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.implementation-steps {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.implementation-steps li {
  margin-bottom: 4px;
  line-height: 1.5;
}

.risk-assessment {
  display: flex;
  align-items: center;
  gap: 12px;
}

.risk-description {
  color: #606266;
  font-size: 14px;
}

.historical-cases {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.case-name {
  color: #303133;
  font-weight: 500;
}

.case-result.positive {
  color: #67c23a;
}

.case-result.negative {
  color: #f56c6c;
}

.implementation-plan {
  margin-top: 24px;
}

.plan-content {
  padding: 16px;
}

.timeline-card {
  box-shadow: none;
  border: 1px solid #e4e7ed;
}

.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.phase-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.phase-content {
  margin-bottom: 16px;
}

.phase-description {
  color: #606266;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.phase-suggestions {
  margin-bottom: 12px;
}

.suggestions-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  display: block;
}

.suggestion-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-tag {
  font-size: 12px;
}

.phase-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.metric .label {
  color: #606266;
}

.metric .value {
  font-weight: 600;
}

.metric .value.positive {
  color: #67c23a;
}

.metric .value.info {
  color: #409eff;
}

.phase-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .suggestions-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-controls {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .status-content {
    flex-direction: column;
    text-align: center;
  }
  
  .analysis-progress {
    width: 100%;
  }
  
  .impact-metrics {
    flex-direction: column;
    gap: 12px;
  }
  
  .phase-metrics {
    flex-direction: column;
    gap: 8px;
  }
  
  .phase-actions {
    flex-direction: column;
  }
}
</style>