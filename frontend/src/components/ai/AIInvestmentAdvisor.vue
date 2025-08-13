<template>
  <div class="ai-investment-advisor">
    <div class="advisor-header">
      <h3>AI投资顾问</h3>
      <el-switch v-model="isActive" active-text="启用" inactive-text="关闭" />
    </div>

    <el-tabs v-model="activeTab" class="advisor-tabs">
      <!-- 投资建议生成器 -->
      <el-tab-pane label="投资建议" name="recommendations">
        <el-card>
          <template #header>
            <div class="card-header">
              <h4>投资建议生成器</h4>
              <el-button type="primary" @click="generateRecommendations" :loading="isGenerating">
                生成建议
              </el-button>
            </div>
          </template>

          <!-- 投资偏好配置 -->
          <el-row :gutter="16" class="preference-config">
            <el-col :span="6">
              <el-card shadow="never">
                <h5>风险偏好</h5>
                <el-slider
                  v-model="preferences.riskTolerance"
                  :min="1"
                  :max="10"
                  :step="1"
                  show-stops
                  show-input
                />
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never">
                <h5>投资期限</h5>
                <el-select v-model="preferences.timeHorizon" style="width: 100%">
                  <el-option label="短期(1-6月)" value="short" />
                  <el-option label="中期(6月-2年)" value="medium" />
                  <el-option label="长期(2年以上)" value="long" />
                </el-select>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never">
                <h5>资金规模</h5>
                <el-input
                  v-model="preferences.capitalSize"
                  placeholder="万元"
                  suffix-icon="el-icon-money"
                />
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="never">
                <h5>投资风格</h5>
                <el-select v-model="preferences.investmentStyle" style="width: 100%">
                  <el-option label="价值投资" value="value" />
                  <el-option label="成长投资" value="growth" />
                  <el-option label="量化策略" value="quantitative" />
                  <el-option label="混合策略" value="balanced" />
                </el-select>
              </el-card>
            </el-col>
          </el-row>

          <!-- AI生成的投资建议 -->
          <div v-if="recommendations.length > 0" class="recommendations-list">
            <h5>AI投资建议</h5>
            <div
              v-for="(rec, index) in recommendations"
              :key="index"
              class="recommendation-item"
            >
              <div class="recommendation-header">
                <el-tag :type="getRecommendationType(rec.type)" size="small">
                  {{ rec.type }}
                </el-tag>
                <span class="confidence">置信度: {{ rec.confidence }}%</span>
              </div>
              <h6>{{ rec.title }}</h6>
              <p class="description">{{ rec.description }}</p>
              <div class="recommendation-details">
                <div class="detail-item" v-if="rec.expectedReturn">
                  <span class="label">预期收益:</span>
                  <span class="value">{{ rec.expectedReturn }}%</span>
                </div>
                <div class="detail-item" v-if="rec.riskLevel">
                  <span class="label">风险等级:</span>
                  <span class="value">{{ rec.riskLevel }}</span>
                </div>
                <div class="detail-item" v-if="rec.timeFrame">
                  <span class="label">建议持有期:</span>
                  <span class="value">{{ rec.timeFrame }}</span>
                </div>
              </div>
              <div class="recommendation-actions">
                <el-button size="small" @click="viewDetails(rec)">查看详情</el-button>
                <el-button size="small" type="primary" @click="applyRecommendation(rec)">
                  应用建议
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 市场分析助手 -->
      <el-tab-pane label="市场分析" name="market">
        <el-card>
          <template #header>
            <div class="card-header">
              <h4>市场分析助手</h4>
              <el-button type="primary" @click="analyzeMarket" :loading="isAnalyzing">
                分析市场
              </el-button>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col :span="12">
              <div class="market-overview">
                <h5>市场概况</h5>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="大盘指数">
                    <el-tag :type="marketData.indexTrend === 'up' ? 'success' : 'danger'">
                      {{ marketData.indexValue }} ({{ marketData.indexChange }}%)
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="市场情绪">{{ marketData.sentiment }}</el-descriptions-item>
                  <el-descriptions-item label="成交量">{{ marketData.volume }}</el-descriptions-item>
                  <el-descriptions-item label="涨跌比">{{ marketData.advanceDeclineRatio }}</el-descriptions-item>
                </el-descriptions>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="sector-analysis">
                <h5>行业分析</h5>
                <div class="sector-list">
                  <div
                    v-for="sector in sectorAnalysis"
                    :key="sector.name"
                    class="sector-item"
                  >
                    <div class="sector-info">
                      <span class="sector-name">{{ sector.name }}</span>
                      <el-tag :type="sector.trend === 'up' ? 'success' : 'danger'" size="small">
                        {{ sector.change }}%
                      </el-tag>
                    </div>
                    <el-progress
                      :percentage="Math.abs(sector.change) * 10"
                      :color="sector.trend === 'up' ? '#67c23a' : '#f56c6c'"
                      :stroke-width="4"
                    />
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- AI市场解读 -->
          <div v-if="marketAnalysis" class="market-analysis">
            <h5>AI市场解读</h5>
            <el-alert :title="marketAnalysis.title" :type="marketAnalysis.type" show-icon>
              <p>{{ marketAnalysis.summary }}</p>
            </el-alert>
            <div class="analysis-details">
              <el-collapse v-model="activeAnalysis">
                <el-collapse-item title="技术分析" name="technical">
                  <p>{{ marketAnalysis.technical }}</p>
                </el-collapse-item>
                <el-collapse-item title="基本面分析" name="fundamental">
                  <p>{{ marketAnalysis.fundamental }}</p>
                </el-collapse-item>
                <el-collapse-item title="资金流向分析" name="flow">
                  <p>{{ marketAnalysis.flow }}</p>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 风险评估顾问 -->
      <el-tab-pane label="风险评估" name="risk">
        <el-card>
          <template #header>
            <div class="card-header">
              <h4>风险评估顾问</h4>
              <el-button type="primary" @click="assessRisk" :loading="isAssessing">
                风险评估
              </el-button>
            </div>
          </template>

          <div class="risk-assessment">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-card shadow="never">
                  <el-statistic title="投资组合风险等级" :value="riskAssessment.portfolioRisk">
                    <template #suffix>/10</template>
                  </el-statistic>
                  <el-progress
                    :percentage="riskAssessment.portfolioRisk * 10"
                    :color="getRiskColor(riskAssessment.portfolioRisk)"
                  />
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never">
                  <el-statistic title="预期最大回撤" :value="riskAssessment.maxDrawdown" suffix="%" />
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never">
                  <el-statistic title="夏普比率" :value="riskAssessment.sharpeRatio" :precision="2" />
                </el-card>
              </el-col>
            </el-row>

            <!-- 风险详细分析 -->
            <div class="risk-details">
              <h5>风险分析报告</h5>
              <el-table :data="riskFactors" style="width: 100%">
                <el-table-column prop="factor" label="风险因子" />
                <el-table-column prop="level" label="风险等级">
                  <template #default="{ row }">
                    <el-tag :type="getRiskTagType(row.level)">{{ row.level }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="impact" label="影响程度" />
                <el-table-column prop="suggestion" label="应对建议" />
              </el-table>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 策略优化建议 -->
      <el-tab-pane label="策略优化" name="optimization">
        <el-card>
          <template #header>
            <div class="card-header">
              <h4>策略优化建议</h4>
              <el-button type="primary" @click="optimizeStrategy" :loading="isOptimizing">
                生成优化建议
              </el-button>
            </div>
          </template>

          <div v-if="optimizationSuggestions.length > 0" class="optimization-suggestions">
            <div
              v-for="(suggestion, index) in optimizationSuggestions"
              :key="index"
              class="suggestion-item"
            >
              <el-card shadow="hover">
                <div class="suggestion-header">
                  <h6>{{ suggestion.title }}</h6>
                  <el-tag :type="suggestion.priority === 'high' ? 'danger' : suggestion.priority === 'medium' ? 'warning' : 'info'">
                    {{ suggestion.priority }}优先级
                  </el-tag>
                </div>
                <p class="suggestion-description">{{ suggestion.description }}</p>
                <div class="suggestion-metrics">
                  <div class="metric-item">
                    <span class="metric-label">预期改进:</span>
                    <span class="metric-value">{{ suggestion.expectedImprovement }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">实施难度:</span>
                    <span class="metric-value">{{ suggestion.difficulty }}</span>
                  </div>
                </div>
                <div class="suggestion-actions">
                  <el-button size="small" @click="viewOptimizationDetails(suggestion)">
                    详细方案
                  </el-button>
                  <el-button size="small" type="primary" @click="applySuggestion(suggestion)">
                    应用优化
                  </el-button>
                </div>
              </el-card>
            </div>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 实时市场解读 -->
      <el-tab-pane label="实时解读" name="realtime">
        <el-card>
          <template #header>
            <div class="card-header">
              <h4>实时市场解读</h4>
              <el-switch v-model="realtimeEnabled" active-text="开启" inactive-text="关闭" />
            </div>
          </template>

          <div class="realtime-feed">
            <div
              v-for="(item, index) in realtimeFeed"
              :key="index"
              class="feed-item"
            >
              <div class="feed-header">
                <span class="feed-time">{{ item.time }}</span>
                <el-tag :type="getNewsType(item.type)" size="small">{{ item.type }}</el-tag>
              </div>
              <h6 class="feed-title">{{ item.title }}</h6>
              <p class="feed-content">{{ item.content }}</p>
              <div class="feed-actions">
                <el-button size="small" @click="viewFullNews(item)">查看详情</el-button>
                <el-button size="small" type="primary" @click="addToWatchlist(item)">
                  加入关注
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

interface InvestmentPreferences {
  riskTolerance: number
  timeHorizon: string
  capitalSize: string
  investmentStyle: string
}

interface Recommendation {
  type: string
  title: string
  description: string
  confidence: number
  expectedReturn?: number
  riskLevel?: string
  timeFrame?: string
}

const isActive = ref(true)
const activeTab = ref('recommendations')
const isGenerating = ref(false)
const isAnalyzing = ref(false)
const isAssessing = ref(false)
const isOptimizing = ref(false)
const realtimeEnabled = ref(false)
const activeAnalysis = ref(['technical'])

const preferences = reactive<InvestmentPreferences>({
  riskTolerance: 5,
  timeHorizon: 'medium',
  capitalSize: '100',
  investmentStyle: 'balanced'
})

const recommendations = ref<Recommendation[]>([])

const marketData = reactive({
  indexValue: '3245.68',
  indexChange: '+1.23',
  indexTrend: 'up',
  sentiment: '乐观',
  volume: '2350亿',
  advanceDeclineRatio: '3:2'
})

const sectorAnalysis = ref([
  { name: '科技', change: 2.3, trend: 'up' },
  { name: '金融', change: -0.8, trend: 'down' },
  { name: '医药', change: 1.5, trend: 'up' },
  { name: '消费', change: 0.2, trend: 'up' },
  { name: '新能源', change: -1.2, trend: 'down' }
])

const marketAnalysis = ref({
  title: '市场整体偏强',
  type: 'success',
  summary: '当前市场呈现震荡上行态势，科技股领涨，资金流入明显。建议适度增加科技板块配置。',
  technical: '从技术角度看，大盘突破短期均线压力，成交量放大，多头趋势明确。但需关注3300点附近阻力。',
  fundamental: '基本面支撑较强，企业盈利改善，政策环境友好。关注三季报业绩兑现情况。',
  flow: '北上资金连续流入，机构资金偏向成长股。建议关注资金集中流入的板块和个股。'
})

const riskAssessment = reactive({
  portfolioRisk: 6.8,
  maxDrawdown: 15.2,
  sharpeRatio: 1.35
})

const riskFactors = ref([
  {
    factor: '市场风险',
    level: '中',
    impact: '影响整体收益',
    suggestion: '分散投资，关注宏观政策'
  },
  {
    factor: '行业集中风险',
    level: '高',
    impact: '单一行业占比过高',
    suggestion: '适当分散行业配置'
  },
  {
    factor: '流动性风险',
    level: '低',
    impact: '资金充裕',
    suggestion: '维持当前配置'
  }
])

const optimizationSuggestions = ref([
  {
    title: '优化资产配置比例',
    description: '建议增加债券类资产配置，降低整体波动率',
    priority: 'high',
    expectedImprovement: 8.5,
    difficulty: '简单'
  },
  {
    title: '调整调仓频率',
    description: '当前调仓过于频繁，建议降低交易频率减少成本',
    priority: 'medium',
    expectedImprovement: 3.2,
    difficulty: '中等'
  }
])

const realtimeFeed = ref([
  {
    time: '09:30',
    type: '重要资讯',
    title: '央行降准传言刺激市场',
    content: 'AI解读：该消息对银行股和地产股形成利好，建议关注相关板块机会。'
  },
  {
    time: '10:15',
    type: '技术分析',
    title: '沪指突破重要压力位',
    content: 'AI解读：成交量配合良好，短期有望继续上行，建议适度加仓。'
  }
])

const generateRecommendations = async () => {
  isGenerating.value = true
  
  // 模拟AI生成投资建议
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  recommendations.value = [
    {
      type: '买入建议',
      title: '科技龙头股配置机会',
      description: '基于当前市场环境和您的风险偏好，建议增加科技板块配置',
      confidence: 85,
      expectedReturn: 12.5,
      riskLevel: '中等',
      timeFrame: '3-6个月'
    },
    {
      type: '卖出建议',
      title: '高估值金融股减持',
      description: '部分银行股估值偏高，建议适度减仓',
      confidence: 72,
      expectedReturn: -2.8,
      riskLevel: '低',
      timeFrame: '1个月'
    },
    {
      type: '持有建议',
      title: '优质消费股长期持有',
      description: '消费板块基本面稳健，建议长期持有',
      confidence: 90,
      expectedReturn: 8.3,
      riskLevel: '低',
      timeFrame: '12个月'
    }
  ]
  
  isGenerating.value = false
  ElMessage.success('投资建议生成完成')
}

const analyzeMarket = async () => {
  isAnalyzing.value = true
  
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // 更新市场数据
  ElMessage.success('市场分析完成')
  isAnalyzing.value = false
}

const assessRisk = async () => {
  isAssessing.value = true
  
  await new Promise(resolve => setTimeout(resolve, 1800))
  
  ElMessage.success('风险评估完成')
  isAssessing.value = false
}

const optimizeStrategy = async () => {
  isOptimizing.value = true
  
  await new Promise(resolve => setTimeout(resolve, 2200))
  
  ElMessage.success('策略优化建议生成完成')
  isOptimizing.value = false
}

const getRecommendationType = (type: string) => {
  const types: Record<string, string> = {
    '买入建议': 'success',
    '卖出建议': 'warning',
    '持有建议': 'info'
  }
  return types[type] || 'info'
}

const getRiskColor = (risk: number) => {
  if (risk <= 3) return '#67c23a'
  if (risk <= 6) return '#e6a23c'
  return '#f56c6c'
}

const getRiskTagType = (level: string) => {
  const types: Record<string, string> = {
    '低': 'success',
    '中': 'warning',
    '高': 'danger'
  }
  return types[level] || 'info'
}

const getNewsType = (type: string) => {
  const types: Record<string, string> = {
    '重要资讯': 'danger',
    '技术分析': 'warning',
    '基本面分析': 'info'
  }
  return types[type] || 'info'
}

const viewDetails = (rec: Recommendation) => {
  ElMessage.info(`查看建议详情: ${rec.title}`)
}

const applyRecommendation = (rec: Recommendation) => {
  ElMessage.success(`应用投资建议: ${rec.title}`)
}

const viewOptimizationDetails = (suggestion: any) => {
  ElMessage.info(`查看优化详情: ${suggestion.title}`)
}

const applySuggestion = (suggestion: any) => {
  ElMessage.success(`应用优化建议: ${suggestion.title}`)
}

const viewFullNews = (item: any) => {
  ElMessage.info(`查看新闻详情: ${item.title}`)
}

const addToWatchlist = (item: any) => {
  ElMessage.success(`已加入关注列表: ${item.title}`)
}

// 实时数据更新
let realtimeInterval: NodeJS.Timeout | null = null

const startRealtimeUpdate = () => {
  if (realtimeInterval) return
  
  realtimeInterval = setInterval(() => {
    if (realtimeEnabled.value) {
      // 模拟新的实时数据
      const newItem = {
        time: new Date().toLocaleTimeString('zh-CN', { 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        type: ['重要资讯', '技术分析', '基本面分析'][Math.floor(Math.random() * 3)],
        title: '市场动态更新',
        content: 'AI实时解读市场变化和投资机会'
      }
      
      realtimeFeed.value.unshift(newItem)
      if (realtimeFeed.value.length > 10) {
        realtimeFeed.value = realtimeFeed.value.slice(0, 10)
      }
    }
  }, 30000) // 30秒更新一次
}

const stopRealtimeUpdate = () => {
  if (realtimeInterval) {
    clearInterval(realtimeInterval)
    realtimeInterval = null
  }
}

onMounted(() => {
  startRealtimeUpdate()
})

onUnmounted(() => {
  stopRealtimeUpdate()
})
</script>

<style scoped lang="scss">
.ai-investment-advisor {
  .advisor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .preference-config {
    margin-bottom: 24px;
    
    h5 {
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }
  }

  .recommendations-list {
    margin-top: 24px;

    .recommendation-item {
      padding: 16px;
      border: 1px solid var(--el-border-color);
      border-radius: 8px;
      margin-bottom: 12px;

      .recommendation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .confidence {
          font-size: 12px;
          color: var(--el-text-color-regular);
        }
      }

      h6 {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }

      .description {
        color: var(--el-text-color-regular);
        margin-bottom: 12px;
      }

      .recommendation-details {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 4px;

          .label {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
          }

          .value {
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
        }
      }

      .recommendation-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .market-overview,
  .sector-analysis {
    margin-bottom: 16px;

    h5 {
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }
  }

  .sector-list {
    .sector-item {
      margin-bottom: 12px;

      .sector-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;

        .sector-name {
          font-weight: 500;
        }
      }
    }
  }

  .market-analysis {
    margin-top: 24px;

    h5 {
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }

    .analysis-details {
      margin-top: 16px;
    }
  }

  .risk-assessment {
    .risk-details {
      margin-top: 24px;

      h5 {
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }
    }
  }

  .optimization-suggestions {
    .suggestion-item {
      margin-bottom: 16px;

      .suggestion-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        h6 {
          margin: 0;
        }
      }

      .suggestion-description {
        color: var(--el-text-color-regular);
        margin-bottom: 12px;
      }

      .suggestion-metrics {
        display: flex;
        gap: 24px;
        margin-bottom: 12px;

        .metric-item {
          display: flex;
          gap: 8px;

          .metric-label {
            color: var(--el-text-color-placeholder);
          }

          .metric-value {
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
        }
      }

      .suggestion-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .realtime-feed {
    max-height: 600px;
    overflow-y: auto;

    .feed-item {
      padding: 12px;
      border-bottom: 1px solid var(--el-border-color-light);

      &:last-child {
        border-bottom: none;
      }

      .feed-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .feed-time {
          font-size: 12px;
          color: var(--el-text-color-placeholder);
        }
      }

      .feed-title {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
      }

      .feed-content {
        color: var(--el-text-color-regular);
        margin-bottom: 8px;
        font-size: 14px;
      }

      .feed-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}

@media (max-width: 768px) {
  .ai-investment-advisor {
    .preference-config {
      .el-col {
        margin-bottom: 16px;
      }
    }

    .recommendation-details {
      flex-direction: column !important;
      gap: 8px !important;
    }

    .suggestion-metrics {
      flex-direction: column !important;
      gap: 8px !important;
    }
  }
}
</style>