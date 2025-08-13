<template>
  <div class="smart-config-assistant">
    <!-- 助手头部 -->
    <div class="assistant-header">
      <div class="header-content">
        <el-icon class="assistant-icon"><Setting /></el-icon>
        <div class="header-text">
          <h3>智能配置助手</h3>
          <p>基于您的历史偏好和市场环境，为您推荐最优配置</p>
        </div>
        <el-switch
          v-model="assistantEnabled"
          active-text="开启智能建议"
          inactive-text="关闭智能建议"
        />
      </div>
    </div>

    <!-- 配置向导 -->
    <div v-if="assistantEnabled" class="config-wizard">
      <!-- 用户偏好分析 -->
      <el-card class="preference-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><User /></el-icon>
            <span>用户偏好分析</span>
            <el-button type="primary" link @click="refreshPreferences">
              <el-icon><Refresh /></el-icon>
              刷新分析
            </el-button>
          </div>
        </template>

        <div class="preferences-grid">
          <div class="preference-item">
            <div class="preference-label">投资风格</div>
            <div class="preference-value">
              <el-tag :type="getStyleTagType(userPreferences.investmentStyle)">
                {{ userPreferences.investmentStyle }}
              </el-tag>
            </div>
          </div>
          
          <div class="preference-item">
            <div class="preference-label">风险偏好</div>
            <div class="preference-value">
              <el-progress 
                :percentage="userPreferences.riskTolerance" 
                :color="getRiskColor(userPreferences.riskTolerance)"
                :show-text="false"
              />
              <span class="risk-text">{{ getRiskLabel(userPreferences.riskTolerance) }}</span>
            </div>
          </div>

          <div class="preference-item">
            <div class="preference-label">常用算法</div>
            <div class="preference-value">
              <el-tag 
                v-for="algo in userPreferences.preferredAlgorithms" 
                :key="algo"
                size="small"
                class="algo-tag"
              >
                {{ algo }}
              </el-tag>
            </div>
          </div>

          <div class="preference-item">
            <div class="preference-label">历史成功率</div>
            <div class="preference-value">
              <el-statistic :value="userPreferences.historicalSuccessRate" suffix="%" />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 智能参数推荐 -->
      <el-card class="recommendation-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><MagicStick /></el-icon>
            <span>智能参数推荐</span>
            <el-select v-model="selectedScenario" placeholder="选择应用场景" @change="updateRecommendations">
              <el-option 
                v-for="scenario in scenarios" 
                :key="scenario.value"
                :label="scenario.label" 
                :value="scenario.value" 
              />
            </el-select>
          </div>
        </template>

        <div class="recommendations-container">
          <div class="recommendation-section" v-for="section in recommendations" :key="section.category">
            <div class="section-header">
              <el-icon><component :is="section.icon" /></el-icon>
              <span>{{ section.title }}</span>
              <el-tag size="small" :type="section.confidence > 80 ? 'success' : 'warning'">
                置信度 {{ section.confidence }}%
              </el-tag>
            </div>

            <div class="params-grid">
              <div 
                v-for="param in section.parameters" 
                :key="param.name"
                class="param-item"
                :class="{ 'param-modified': param.isModified }"
              >
                <div class="param-header">
                  <span class="param-name">{{ param.name }}</span>
                  <el-tooltip :content="param.description" placement="top">
                    <el-icon class="param-help"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
                
                <div class="param-content">
                  <div class="param-recommendation">
                    <span class="recommend-label">推荐：</span>
                    <span class="recommend-value">{{ param.recommendedValue }}</span>
                    <el-button 
                      size="small" 
                      type="primary" 
                      link
                      @click="applyRecommendation(param)"
                    >
                      应用
                    </el-button>
                  </div>

                  <div v-if="param.currentValue !== param.recommendedValue" class="param-current">
                    <span class="current-label">当前：</span>
                    <span class="current-value">{{ param.currentValue }}</span>
                  </div>

                  <div class="param-reason">
                    <el-text size="small" type="info">{{ param.reason }}</el-text>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 配置模板推荐 -->
      <el-card class="template-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Document /></el-icon>
            <span>配置模板推荐</span>
            <el-button type="primary" link @click="showTemplateDialog = true">
              <el-icon><Plus /></el-icon>
              创建模板
            </el-button>
          </div>
        </template>

        <div class="templates-grid">
          <div 
            v-for="template in recommendedTemplates" 
            :key="template.id"
            class="template-item"
            @click="selectTemplate(template)"
          >
            <div class="template-header">
              <div class="template-info">
                <h4>{{ template.name }}</h4>
                <el-text size="small" type="info">{{ template.description }}</el-text>
              </div>
              <div class="template-meta">
                <el-rate 
                  v-model="template.rating" 
                  disabled 
                  show-score 
                  text-color="#ff9900" 
                  size="small"
                />
                <el-text size="small" type="info">使用 {{ template.usageCount }} 次</el-text>
              </div>
            </div>

            <div class="template-preview">
              <div class="preview-item" v-for="(value, key) in template.preview" :key="key">
                <span class="preview-key">{{ key }}:</span>
                <span class="preview-value">{{ value }}</span>
              </div>
            </div>

            <div class="template-actions">
              <el-button size="small" type="primary" @click.stop="applyTemplate(template)">
                <el-icon><Check /></el-icon>
                应用模板
              </el-button>
              <el-button size="small" @click.stop="previewTemplate(template)">
                <el-icon><View /></el-icon>
                预览
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 历史最优配置 -->
      <el-card class="history-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><TrendCharts /></el-icon>
            <span>历史最优配置</span>
            <el-date-picker
              v-model="historyDateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              @change="loadHistoryConfigs"
            />
          </div>
        </template>

        <div class="history-list">
          <div 
            v-for="config in historyConfigs" 
            :key="config.id"
            class="history-item"
          >
            <div class="history-header">
              <div class="config-info">
                <h4>{{ config.name }}</h4>
                <el-text size="small">{{ formatDate(config.createdAt) }}</el-text>
              </div>
              <div class="performance-badge">
                <el-tag :type="getPerformanceType(config.performance)">
                  {{ config.performance > 0 ? '+' : '' }}{{ config.performance.toFixed(2) }}%
                </el-tag>
              </div>
            </div>

            <div class="config-metrics">
              <div class="metric-item">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">{{ config.sharpeRatio.toFixed(2) }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value">{{ config.maxDrawdown.toFixed(2) }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">胜率</span>
                <span class="metric-value">{{ config.winRate.toFixed(1) }}%</span>
              </div>
            </div>

            <div class="config-actions">
              <el-button size="small" type="primary" @click="reapplyConfig(config)">
                <el-icon><RefreshRight /></el-icon>
                重新应用
              </el-button>
              <el-button size="small" @click="compareWithCurrent(config)">
                <el-icon><Position /></el-icon>
                对比当前
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 市场环境适配 -->
      <el-card class="market-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>市场环境适配</span>
            <el-button type="primary" link @click="analyzeMarketEnvironment">
              <el-icon><Refresh /></el-icon>
              更新市场分析
            </el-button>
          </div>
        </template>

        <div class="market-analysis">
          <div class="market-overview">
            <div class="market-indicator">
              <div class="indicator-label">市场趋势</div>
              <div class="indicator-value">
                <el-tag :type="getMarketTrendType(marketEnvironment.trend)">
                  {{ marketEnvironment.trend }}
                </el-tag>
              </div>
            </div>
            
            <div class="market-indicator">
              <div class="indicator-label">波动率水平</div>
              <div class="indicator-value">
                <el-progress 
                  :percentage="marketEnvironment.volatility" 
                  :color="getVolatilityColor(marketEnvironment.volatility)"
                />
              </div>
            </div>

            <div class="market-indicator">
              <div class="indicator-label">流动性</div>
              <div class="indicator-value">
                <el-rate 
                  v-model="marketEnvironment.liquidity" 
                  disabled 
                  size="small"
                />
              </div>
            </div>
          </div>

          <div class="market-recommendations">
            <h4>基于当前市场环境的建议</h4>
            <ul class="recommendation-list">
              <li v-for="rec in marketEnvironment.recommendations" :key="rec.id">
                <el-icon><component :is="rec.icon" /></el-icon>
                <span>{{ rec.text }}</span>
                <el-button 
                  v-if="rec.actionable" 
                  size="small" 
                  type="primary" 
                  link
                  @click="applyMarketRecommendation(rec)"
                >
                  应用
                </el-button>
              </li>
            </ul>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建模板对话框 -->
    <el-dialog 
      v-model="showTemplateDialog" 
      title="创建配置模板" 
      width="600px"
    >
      <el-form :model="newTemplate" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="newTemplate.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="newTemplate.description" 
            type="textarea" 
            :rows="3"
            placeholder="请描述模板的用途和特点"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input 
            v-model="newTemplate.tags" 
            placeholder="用逗号分隔多个标签"
          />
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="newTemplate.isPublic" />
          <el-text size="small" type="info">公开模板可被其他用户使用</el-text>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTemplate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  User,
  Refresh,
  MagicStick,
  QuestionFilled,
  Document,
  Plus,
  Check,
  View,
  TrendCharts,
  RefreshRight,
  Position,
  DataAnalysis,
  Cpu,
  TrendDown,
  TrendUp,
  WarningFilled
} from '@element-plus/icons-vue'

// 接口定义
interface UserPreferences {
  investmentStyle: string
  riskTolerance: number
  preferredAlgorithms: string[]
  historicalSuccessRate: number
}

interface Parameter {
  name: string
  currentValue: string
  recommendedValue: string
  description: string
  reason: string
  isModified: boolean
}

interface Recommendation {
  category: string
  title: string
  icon: string
  confidence: number
  parameters: Parameter[]
}

interface ConfigTemplate {
  id: string
  name: string
  description: string
  rating: number
  usageCount: number
  preview: Record<string, string>
}

interface HistoryConfig {
  id: string
  name: string
  createdAt: Date
  performance: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
}

interface MarketEnvironment {
  trend: string
  volatility: number
  liquidity: number
  recommendations: Array<{
    id: string
    text: string
    icon: string
    actionable: boolean
  }>
}

// 响应式数据
const assistantEnabled = ref(true)
const selectedScenario = ref('general')
const historyDateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
  new Date()
])
const showTemplateDialog = ref(false)

const userPreferences = ref<UserPreferences>({
  investmentStyle: '价值成长',
  riskTolerance: 65,
  preferredAlgorithms: ['LightGBM', 'XGBoost', 'Linear'],
  historicalSuccessRate: 72.5
})

const scenarios = [
  { value: 'general', label: '通用场景' },
  { value: 'bull_market', label: '牛市环境' },
  { value: 'bear_market', label: '熊市环境' },
  { value: 'high_volatility', label: '高波动环境' },
  { value: 'low_volatility', label: '低波动环境' }
]

const recommendations = ref<Recommendation[]>([
  {
    category: 'model',
    title: '模型配置',
    icon: 'Cpu',
    confidence: 85,
    parameters: [
      {
        name: '学习率',
        currentValue: '0.1',
        recommendedValue: '0.08',
        description: '控制模型训练速度的参数',
        reason: '基于您的历史数据特征，较低的学习率能获得更稳定的收敛',
        isModified: false
      },
      {
        name: '树的深度',
        currentValue: '6',
        recommendedValue: '8',
        description: '决策树的最大深度',
        reason: '当前市场复杂度较高，建议增加模型复杂度以捕捉更多特征',
        isModified: false
      }
    ]
  },
  {
    category: 'strategy',
    title: '策略配置',
    icon: 'TrendCharts',
    confidence: 92,
    parameters: [
      {
        name: '选股数量',
        currentValue: '20',
        recommendedValue: '25',
        description: '策略每次调仓选择的股票数量',
        reason: '适当增加选股数量可以分散风险，提高策略稳定性',
        isModified: false
      },
      {
        name: '调仓频率',
        currentValue: '周度',
        recommendedValue: '月度',
        description: '策略重新平衡投资组合的频率',
        reason: '月度调仓可以降低交易成本，提高净收益',
        isModified: false
      }
    ]
  }
])

const recommendedTemplates = ref<ConfigTemplate[]>([
  {
    id: 'template_1',
    name: '稳健价值策略',
    description: '适合保守投资者的价值投资配置',
    rating: 4.5,
    usageCount: 156,
    preview: {
      '算法': 'LightGBM',
      '选股数': '30股',
      '调仓': '月度',
      '风险': '保守'
    }
  },
  {
    id: 'template_2', 
    name: '成长动量策略',
    description: '追求高收益的成长股投资策略',
    rating: 4.2,
    usageCount: 89,
    preview: {
      '算法': 'XGBoost',
      '选股数': '20股',
      '调仓': '周度',
      '风险': '积极'
    }
  },
  {
    id: 'template_3',
    name: '量化对冲策略',
    description: '市场中性的量化对冲配置',
    rating: 4.7,
    usageCount: 203,
    preview: {
      '算法': 'LSTM',
      '选股数': '50股',
      '调仓': '日度',
      '风险': '中性'
    }
  }
])

const historyConfigs = ref<HistoryConfig[]>([
  {
    id: 'config_1',
    name: 'LightGBM_优化配置_v3',
    createdAt: new Date('2024-01-10'),
    performance: 18.5,
    sharpeRatio: 1.45,
    maxDrawdown: -8.2,
    winRate: 68.5
  },
  {
    id: 'config_2',
    name: 'XGBoost_月度调仓',
    createdAt: new Date('2024-01-05'),
    performance: 15.2,
    sharpeRatio: 1.32,
    maxDrawdown: -12.1,
    winRate: 64.2
  },
  {
    id: 'config_3',
    name: '多因子综合策略',
    createdAt: new Date('2023-12-28'),
    performance: 22.1,
    sharpeRatio: 1.68,
    maxDrawdown: -6.5,
    winRate: 71.8
  }
])

const marketEnvironment = ref<MarketEnvironment>({
  trend: '震荡上行',
  volatility: 65,
  liquidity: 4,
  recommendations: [
    {
      id: 'rec_1',
      text: '当前市场波动较大，建议降低仓位或增加止损设置',
      icon: 'WarningFilled',
      actionable: true
    },
    {
      id: 'rec_2',
      text: '流动性充裕，适合增加小盘股配置比例',
      icon: 'TrendUp',
      actionable: true
    },
    {
      id: 'rec_3',
      text: '建议关注新兴行业主题，如新能源、人工智能等',
      icon: 'TrendCharts',
      actionable: false
    }
  ]
})

const newTemplate = reactive({
  name: '',
  description: '',
  tags: '',
  isPublic: false
})

// 计算属性和方法
const getStyleTagType = (style: string) => {
  const typeMap: Record<string, string> = {
    '价值成长': 'success',
    '动量趋势': 'warning', 
    '量化对冲': 'info'
  }
  return typeMap[style] || 'primary'
}

const getRiskColor = (risk: number) => {
  if (risk < 30) return '#67c23a'
  if (risk < 70) return '#e6a23c'
  return '#f56c6c'
}

const getRiskLabel = (risk: number) => {
  if (risk < 30) return '保守'
  if (risk < 70) return '中等'
  return '激进'
}

const getPerformanceType = (performance: number) => {
  if (performance > 15) return 'success'
  if (performance > 5) return 'warning'
  return 'danger'
}

const getMarketTrendType = (trend: string) => {
  const typeMap: Record<string, string> = {
    '震荡上行': 'success',
    '震荡下行': 'warning',
    '强势上涨': 'success',
    '快速下跌': 'danger'
  }
  return typeMap[trend] || 'info'
}

const getVolatilityColor = (volatility: number) => {
  if (volatility < 30) return '#67c23a'
  if (volatility < 70) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN')
}

// 方法
const refreshPreferences = async () => {
  try {
    // 这里应该调用API刷新用户偏好分析
    ElMessage.success('偏好分析已更新')
  } catch {
    ElMessage.error('刷新失败')
  }
}

const updateRecommendations = () => {
  // 根据选择的场景更新推荐配置
  console.log('更新场景推荐:', selectedScenario.value)
}

const applyRecommendation = (param: Parameter) => {
  param.currentValue = param.recommendedValue
  param.isModified = true
  ElMessage.success(`已应用推荐值: ${param.name} = ${param.recommendedValue}`)
}

const selectTemplate = (template: ConfigTemplate) => {
  console.log('选择模板:', template)
}

const applyTemplate = async (template: ConfigTemplate) => {
  try {
    // 这里应该应用模板配置
    ElMessage.success(`已应用模板: ${template.name}`)
  } catch {
    ElMessage.error('应用模板失败')
  }
}

const previewTemplate = (template: ConfigTemplate) => {
  console.log('预览模板:', template)
}

const loadHistoryConfigs = () => {
  // 根据日期范围加载历史配置
  console.log('加载历史配置:', historyDateRange.value)
}

const reapplyConfig = async (config: HistoryConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新应用配置 "${config.name}" 吗？`,
      '确认应用',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success(`已重新应用配置: ${config.name}`)
  } catch {
    // 用户取消
  }
}

const compareWithCurrent = (config: HistoryConfig) => {
  console.log('对比配置:', config)
}

const analyzeMarketEnvironment = async () => {
  try {
    // 这里应该调用API分析市场环境
    ElMessage.success('市场环境分析已更新')
  } catch {
    ElMessage.error('分析失败')
  }
}

const applyMarketRecommendation = (recommendation: any) => {
  console.log('应用市场建议:', recommendation)
  ElMessage.success('已应用市场建议')
}

const createTemplate = async () => {
  if (!newTemplate.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }

  try {
    // 这里应该调用API创建模板
    ElMessage.success('模板创建成功')
    showTemplateDialog.value = false
    
    // 重置表单
    Object.assign(newTemplate, {
      name: '',
      description: '',
      tags: '',
      isPublic: false
    })
  } catch {
    ElMessage.error('创建模板失败')
  }
}

// 生命周期
onMounted(() => {
  // 初始化加载数据
  refreshPreferences()
  analyzeMarketEnvironment()
})
</script>

<style scoped lang="scss">
.smart-config-assistant {
  background: #f5f7fa;
  min-height: 100vh;
}

.assistant-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 20px;

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 16px;

    .assistant-icon {
      font-size: 32px;
      color: #409eff;
    }

    .header-text {
      flex: 1;

      h3 {
        margin: 0 0 4px 0;
        color: #303133;
        font-size: 20px;
      }

      p {
        margin: 0;
        color: #606266;
        font-size: 14px;
      }
    }
  }
}

.config-wizard {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;

  .el-icon {
    color: #409eff;
  }

  span {
    flex: 1;
    font-weight: 600;
  }
}

// 用户偏好卡片
.preferences-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;

  .preference-item {
    .preference-label {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }

    .preference-value {
      display: flex;
      align-items: center;
      gap: 8px;

      .risk-text {
        font-size: 12px;
        color: #909399;
      }

      .algo-tag {
        margin: 2px;
      }
    }
  }
}

// 推荐配置卡片
.recommendations-container {
  .recommendation-section {
    margin-bottom: 24px;

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;

      .el-icon {
        color: #409eff;
      }

      span {
        flex: 1;
        font-weight: 600;
      }
    }

    .params-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;

      .param-item {
        border: 1px solid #e4e7ed;
        border-radius: 6px;
        padding: 16px;
        background: white;
        transition: all 0.3s;

        &:hover {
          border-color: #409eff;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
        }

        &.param-modified {
          border-color: #67c23a;
          background: #f0f9ff;
        }

        .param-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;

          .param-name {
            font-weight: 600;
            color: #303133;
          }

          .param-help {
            color: #c0c4cc;
            cursor: help;
          }
        }

        .param-content {
          .param-recommendation {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .recommend-label {
              font-size: 12px;
              color: #909399;
            }

            .recommend-value {
              font-weight: 600;
              color: #409eff;
            }
          }

          .param-current {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .current-label {
              font-size: 12px;
              color: #909399;
            }

            .current-value {
              color: #606266;
            }
          }

          .param-reason {
            font-size: 12px;
            line-height: 1.4;
          }
        }
      }
    }
  }
}

// 模板卡片
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;

  .template-item {
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      border-color: #409eff;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
      transform: translateY(-2px);
    }

    .template-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;

      .template-info {
        flex: 1;

        h4 {
          margin: 0 0 4px 0;
          color: #303133;
        }
      }

      .template-meta {
        text-align: right;
        font-size: 12px;
      }
    }

    .template-preview {
      margin-bottom: 12px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 4px;

      .preview-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
        font-size: 12px;

        .preview-key {
          color: #909399;
        }

        .preview-value {
          color: #303133;
          font-weight: 500;
        }
      }
    }

    .template-actions {
      display: flex;
      gap: 8px;
    }
  }
}

// 历史配置卡片
.history-list {
  .history-item {
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 12px;
    background: white;

    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;

      .config-info {
        h4 {
          margin: 0 0 4px 0;
          color: #303133;
        }
      }
    }

    .config-metrics {
      display: flex;
      gap: 24px;
      margin-bottom: 12px;

      .metric-item {
        display: flex;
        flex-direction: column;
        align-items: center;

        .metric-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 4px;
        }

        .metric-value {
          font-weight: 600;
          color: #303133;
        }
      }
    }

    .config-actions {
      display: flex;
      gap: 8px;
    }
  }
}

// 市场环境卡片
.market-analysis {
  .market-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 24px;

    .market-indicator {
      text-align: center;

      .indicator-label {
        font-size: 14px;
        color: #606266;
        margin-bottom: 8px;
      }

      .indicator-value {
        display: flex;
        justify-content: center;
        align-items: center;
      }
    }
  }

  .market-recommendations {
    h4 {
      margin: 0 0 12px 0;
      color: #303133;
    }

    .recommendation-list {
      list-style: none;
      padding: 0;
      margin: 0;

      li {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .el-icon {
          color: #409eff;
        }

        span {
          flex: 1;
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }
}
</style>