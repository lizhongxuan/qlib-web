<template>
  <div class="intelligent-report-generator">
    <div class="generator-header">
      <h3>智能报告生成</h3>
      <el-button-group>
        <el-button type="primary" @click="generateReport" :loading="isGenerating">
          生成报告
        </el-button>
        <el-button @click="saveTemplate">保存模板</el-button>
        <el-button @click="exportReport">导出报告</el-button>
      </el-button-group>
    </div>

    <el-row :gutter="24">
      <!-- 左侧配置面板 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <h4>报告配置</h4>
          </template>

          <el-form :model="reportConfig" label-width="80px">
            <el-form-item label="报告类型">
              <el-select v-model="reportConfig.type" style="width: 100%">
                <el-option label="策略分析报告" value="strategy" />
                <el-option label="投资组合报告" value="portfolio" />
                <el-option label="风险评估报告" value="risk" />
                <el-option label="市场研究报告" value="market" />
                <el-option label="因子分析报告" value="factor" />
              </el-select>
            </el-form-item>

            <el-form-item label="数据源">
              <el-checkbox-group v-model="reportConfig.dataSources">
                <el-checkbox label="backtest">回测结果</el-checkbox>
                <el-checkbox label="market">市场数据</el-checkbox>
                <el-checkbox label="factors">因子数据</el-checkbox>
                <el-checkbox label="performance">业绩数据</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="时间范围">
              <el-date-picker
                v-model="reportConfig.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="报告深度">
              <el-radio-group v-model="reportConfig.depth">
                <el-radio label="summary">摘要</el-radio>
                <el-radio label="detailed">详细</el-radio>
                <el-radio label="comprehensive">全面</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="包含模块">
              <el-checkbox-group v-model="reportConfig.modules">
                <el-checkbox label="executive_summary">执行摘要</el-checkbox>
                <el-checkbox label="performance_analysis">业绩分析</el-checkbox>
                <el-checkbox label="risk_analysis">风险分析</el-checkbox>
                <el-checkbox label="attribution_analysis">归因分析</el-checkbox>
                <el-checkbox label="market_analysis">市场分析</el-checkbox>
                <el-checkbox label="recommendations">投资建议</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="AI解读">
              <el-switch v-model="reportConfig.aiInsights" />
              <span class="form-help">启用AI智能解读和建议</span>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 模板库 -->
        <el-card class="template-library">
          <template #header>
            <h4>报告模板</h4>
          </template>
          <div class="template-list">
            <div
              v-for="template in reportTemplates"
              :key="template.id"
              class="template-item"
              @click="applyTemplate(template)"
            >
              <div class="template-info">
                <h5>{{ template.name }}</h5>
                <p>{{ template.description }}</p>
              </div>
              <el-button size="small">应用</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧报告预览 -->
      <el-col :span="16">
        <el-card class="report-preview">
          <template #header>
            <div class="preview-header">
              <h4>报告预览</h4>
              <div class="preview-controls">
                <el-button-group>
                  <el-button
                    :type="previewMode === 'structure' ? 'primary' : ''"
                    @click="previewMode = 'structure'"
                  >
                    结构视图
                  </el-button>
                  <el-button
                    :type="previewMode === 'content' ? 'primary' : ''"
                    @click="previewMode = 'content'"
                  >
                    内容预览
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>

          <!-- 结构视图 -->
          <div v-if="previewMode === 'structure'" class="structure-view">
            <div class="report-outline">
              <h5>报告大纲</h5>
              <el-tree
                :data="reportStructure"
                :props="{ label: 'title', children: 'children' }"
                default-expand-all
                class="outline-tree"
              >
                <template #default="{ data }">
                  <div class="outline-node">
                    <span>{{ data.title }}</span>
                    <el-tag v-if="data.status" :type="data.status === 'generated' ? 'success' : 'info'" size="small">
                      {{ data.status === 'generated' ? '已生成' : '待生成' }}
                    </el-tag>
                  </div>
                </template>
              </el-tree>
            </div>
          </div>

          <!-- 内容预览 -->
          <div v-if="previewMode === 'content'" class="content-preview">
            <div v-if="!generatedReport" class="empty-preview">
              <el-empty description="点击生成报告开始创建智能分析报告" />
            </div>
            
            <div v-else class="report-content">
              <!-- 报告标题 -->
              <div class="report-header">
                <h2>{{ generatedReport.title }}</h2>
                <div class="report-meta">
                  <span>生成时间: {{ generatedReport.generatedAt }}</span>
                  <span>报告类型: {{ getReportTypeName(generatedReport.type) }}</span>
                  <span>AI置信度: {{ generatedReport.confidence }}%</span>
                </div>
              </div>

              <!-- 执行摘要 -->
              <div v-if="generatedReport.executiveSummary" class="report-section">
                <h3>执行摘要</h3>
                <div class="summary-content">
                  <el-alert
                    :title="generatedReport.executiveSummary.title"
                    :type="generatedReport.executiveSummary.type"
                    :description="generatedReport.executiveSummary.content"
                    show-icon
                  />
                  
                  <div class="key-findings">
                    <h4>关键发现</h4>
                    <ul>
                      <li v-for="(finding, index) in generatedReport.executiveSummary.keyFindings" :key="index">
                        {{ finding }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <!-- 业绩分析 -->
              <div v-if="generatedReport.performanceAnalysis" class="report-section">
                <h3>业绩分析</h3>
                <div class="performance-metrics">
                  <el-row :gutter="16">
                    <el-col :span="6" v-for="metric in generatedReport.performanceAnalysis.metrics" :key="metric.name">
                      <el-statistic
                        :title="metric.name"
                        :value="metric.value"
                        :suffix="metric.suffix"
                        :precision="metric.precision"
                      />
                    </el-col>
                  </el-row>
                </div>
                
                <div class="performance-charts">
                  <div ref="performanceChart" class="chart-container"></div>
                </div>
                
                <div class="ai-interpretation">
                  <h4>AI智能解读</h4>
                  <el-card shadow="never">
                    <p>{{ generatedReport.performanceAnalysis.aiInsight }}</p>
                  </el-card>
                </div>
              </div>

              <!-- 风险分析 -->
              <div v-if="generatedReport.riskAnalysis" class="report-section">
                <h3>风险分析</h3>
                <div class="risk-metrics">
                  <el-descriptions :column="3" border>
                    <el-descriptions-item
                      v-for="risk in generatedReport.riskAnalysis.metrics"
                      :key="risk.name"
                      :label="risk.name"
                    >
                      <el-tag :type="getRiskTagType(risk.level)">{{ risk.value }}</el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
                
                <div class="risk-breakdown">
                  <h4>风险分解</h4>
                  <el-table :data="generatedReport.riskAnalysis.breakdown" style="width: 100%">
                    <el-table-column prop="factor" label="风险因子" />
                    <el-table-column prop="contribution" label="贡献度" />
                    <el-table-column prop="trend" label="趋势">
                      <template #default="{ row }">
                        <el-tag :type="row.trend === 'up' ? 'danger' : 'success'" size="small">
                          {{ row.trend === 'up' ? '上升' : '下降' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>

              <!-- 投资建议 -->
              <div v-if="generatedReport.recommendations" class="report-section">
                <h3>投资建议</h3>
                <div class="recommendations-list">
                  <div
                    v-for="(rec, index) in generatedReport.recommendations"
                    :key="index"
                    class="recommendation-card"
                  >
                    <el-card shadow="hover">
                      <div class="rec-header">
                        <h4>{{ rec.title }}</h4>
                        <el-tag :type="rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'info'">
                          {{ rec.priority }}优先级
                        </el-tag>
                      </div>
                      <p class="rec-description">{{ rec.description }}</p>
                      <div class="rec-details">
                        <div class="rec-metric">
                          <span class="label">预期影响:</span>
                          <span class="value">{{ rec.expectedImpact }}</span>
                        </div>
                        <div class="rec-metric">
                          <span class="label">实施难度:</span>
                          <span class="value">{{ rec.difficulty }}</span>
                        </div>
                      </div>
                    </el-card>
                  </div>
                </div>
              </div>

              <!-- 图表解读 -->
              <div v-if="generatedReport.chartInsights" class="report-section">
                <h3>图表智能解读</h3>
                <div class="chart-insights">
                  <div
                    v-for="(insight, index) in generatedReport.chartInsights"
                    :key="index"
                    class="insight-item"
                  >
                    <div class="insight-header">
                      <h4>{{ insight.chartTitle }}</h4>
                      <el-tag size="small">{{ insight.type }}</el-tag>
                    </div>
                    <div class="insight-content">
                      <p><strong>关键洞察:</strong> {{ insight.keyInsight }}</p>
                      <p><strong>数据特征:</strong> {{ insight.dataPattern }}</p>
                      <p><strong>投资含义:</strong> {{ insight.investmentImplication }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 生成进度对话框 -->
    <el-dialog v-model="showProgressDialog" title="报告生成进度" width="500px" :close-on-click-modal="false">
      <div class="generation-progress">
        <div class="progress-info">
          <h4>{{ currentTask }}</h4>
          <el-progress :percentage="overallProgress" :stroke-width="8" />
        </div>
        
        <div class="task-list">
          <div
            v-for="task in generationTasks"
            :key="task.id"
            class="task-item"
            :class="{ active: task.status === 'processing', completed: task.status === 'completed' }"
          >
            <el-icon v-if="task.status === 'completed'" class="task-icon success">
              <Check />
            </el-icon>
            <el-icon v-else-if="task.status === 'processing'" class="task-icon processing">
              <Loading />
            </el-icon>
            <el-icon v-else class="task-icon pending">
              <Clock />
            </el-icon>
            <span>{{ task.name }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Loading, Clock } from '@element-plus/icons-vue'

interface ReportConfig {
  type: string
  dataSources: string[]
  dateRange: [Date, Date] | null
  depth: string
  modules: string[]
  aiInsights: boolean
}

const isGenerating = ref(false)
const previewMode = ref('structure')
const showProgressDialog = ref(false)
const overallProgress = ref(0)
const currentTask = ref('')

const reportConfig = reactive<ReportConfig>({
  type: 'strategy',
  dataSources: ['backtest', 'market'],
  dateRange: null,
  depth: 'detailed',
  modules: ['executive_summary', 'performance_analysis', 'risk_analysis', 'recommendations'],
  aiInsights: true
})

const reportTemplates = ref([
  {
    id: '1',
    name: '标准策略报告',
    description: '包含业绩、风险、归因分析的标准模板'
  },
  {
    id: '2',
    name: '简要分析报告',
    description: '适合快速决策的简化报告模板'
  },
  {
    id: '3',
    name: '全面研究报告',
    description: '详尽的研究分析报告模板'
  }
])

const reportStructure = ref([
  {
    title: '执行摘要',
    status: 'pending',
    children: [
      { title: '关键发现', status: 'pending' },
      { title: '主要建议', status: 'pending' }
    ]
  },
  {
    title: '业绩分析',
    status: 'pending',
    children: [
      { title: '收益指标', status: 'pending' },
      { title: '基准对比', status: 'pending' },
      { title: 'AI智能解读', status: 'pending' }
    ]
  },
  {
    title: '风险分析',
    status: 'pending',
    children: [
      { title: '风险指标', status: 'pending' },
      { title: '风险分解', status: 'pending' },
      { title: '压力测试', status: 'pending' }
    ]
  },
  {
    title: '投资建议',
    status: 'pending',
    children: [
      { title: '优化建议', status: 'pending' },
      { title: '风险提示', status: 'pending' }
    ]
  }
])

const generationTasks = ref([
  { id: 1, name: '数据收集与预处理', status: 'pending' },
  { id: 2, name: '业绩指标计算', status: 'pending' },
  { id: 3, name: '风险指标计算', status: 'pending' },
  { id: 4, name: 'AI分析与解读', status: 'pending' },
  { id: 5, name: '图表生成', status: 'pending' },
  { id: 6, name: '报告整合', status: 'pending' }
])

const generatedReport = ref(null as any)

const generateReport = async () => {
  isGenerating.value = true
  showProgressDialog.value = true
  overallProgress.value = 0
  
  // 重置任务状态
  generationTasks.value.forEach(task => task.status = 'pending')
  
  // 模拟报告生成过程
  for (let i = 0; i < generationTasks.value.length; i++) {
    const task = generationTasks.value[i]
    task.status = 'processing'
    currentTask.value = task.name
    
    // 模拟任务执行时间
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))
    
    task.status = 'completed'
    overallProgress.value = ((i + 1) / generationTasks.value.length) * 100
  }
  
  // 生成模拟报告数据
  generatedReport.value = {
    title: `${getReportTypeName(reportConfig.type)}报告`,
    type: reportConfig.type,
    generatedAt: new Date().toLocaleString('zh-CN'),
    confidence: 92,
    executiveSummary: {
      title: '策略表现优异',
      type: 'success',
      content: '基于AI分析，当前策略在回测期间表现出色，年化收益率达到15.8%，夏普比率1.42，最大回撤控制在8.5%以内。',
      keyFindings: [
        '策略在牛市和震荡市中表现稳定',
        '下行风险控制良好，回撤恢复能力强',
        '选股能力突出，alpha贡献显著',
        '建议适度增加仓位配置'
      ]
    },
    performanceAnalysis: {
      metrics: [
        { name: '年化收益率', value: 15.8, suffix: '%', precision: 1 },
        { name: '夏普比率', value: 1.42, suffix: '', precision: 2 },
        { name: '最大回撤', value: -8.5, suffix: '%', precision: 1 },
        { name: '胜率', value: 68.3, suffix: '%', precision: 1 }
      ],
      aiInsight: 'AI分析显示，该策略具有良好的风险调整后收益，在同类策略中排名前15%。收益主要来源于选股能力，择时贡献相对较小。建议继续关注因子有效性和市场环境变化。'
    },
    riskAnalysis: {
      metrics: [
        { name: '波动率', value: '12.3%', level: 'medium' },
        { name: 'VaR(95%)', value: '2.1%', level: 'low' },
        { name: '下行风险', value: '8.9%', level: 'low' }
      ],
      breakdown: [
        { factor: '市场风险', contribution: '65%', trend: 'stable' },
        { factor: '行业风险', contribution: '25%', trend: 'down' },
        { factor: '个股风险', contribution: '10%', trend: 'up' }
      ]
    },
    recommendations: [
      {
        title: '适度增加仓位',
        description: '基于当前策略表现和市场环境，建议将仓位从70%提升至85%',
        priority: 'medium',
        expectedImpact: '增加8-12%收益',
        difficulty: '简单'
      },
      {
        title: '优化因子权重',
        description: '质量因子表现突出，建议适当提高其权重配置',
        priority: 'high',
        expectedImpact: '提升2-3%年化收益',
        difficulty: '中等'
      }
    ],
    chartInsights: [
      {
        chartTitle: '净值走势图',
        type: '趋势分析',
        keyInsight: '策略净值呈稳定上升趋势，波动性控制良好',
        dataPattern: '上升趋势明确，回撤时间短，恢复速度快',
        investmentImplication: '适合风险偏好中等的投资者长期持有'
      },
      {
        chartTitle: '收益分布图',
        type: '分布分析',
        keyInsight: '日收益分布近似正态，极端损失概率低',
        dataPattern: '收益分布集中，尾部风险较小',
        investmentImplication: '策略稳定性高，适合作为核心配置'
      }
    ]
  }
  
  // 更新报告结构状态
  updateReportStructure()
  
  showProgressDialog.value = false
  isGenerating.value = false
  previewMode.value = 'content'
  
  ElMessage.success('智能报告生成完成')
}

const updateReportStructure = () => {
  const updateStatus = (nodes: any[]) => {
    nodes.forEach(node => {
      node.status = 'generated'
      if (node.children) {
        updateStatus(node.children)
      }
    })
  }
  updateStatus(reportStructure.value)
}

const getReportTypeName = (type: string) => {
  const names: Record<string, string> = {
    strategy: '策略分析',
    portfolio: '投资组合',
    risk: '风险评估',
    market: '市场研究',
    factor: '因子分析'
  }
  return names[type] || type
}

const getRiskTagType = (level: string) => {
  const types: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return types[level] || 'info'
}

const applyTemplate = (template: any) => {
  ElMessage.success(`已应用模板: ${template.name}`)
  // 这里应用模板配置
}

const saveTemplate = () => {
  ElMessage.success('模板已保存')
}

const exportReport = () => {
  if (!generatedReport.value) {
    ElMessage.warning('请先生成报告')
    return
  }
  ElMessage.success('报告导出成功')
}
</script>

<style scoped lang="scss">
.intelligent-report-generator {
  .generator-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .form-help {
    margin-left: 8px;
    color: var(--el-text-color-placeholder);
    font-size: 12px;
  }

  .template-library {
    margin-top: 16px;

    .template-list {
      .template-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border: 1px solid var(--el-border-color);
        border-radius: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          border-color: var(--el-color-primary);
          background-color: var(--el-color-primary-light-9);
        }

        .template-info {
          flex: 1;

          h5 {
            margin: 0 0 4px 0;
          }

          p {
            margin: 0;
            font-size: 12px;
            color: var(--el-text-color-regular);
          }
        }
      }
    }
  }

  .report-preview {
    min-height: 800px;

    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .structure-view {
      .outline-tree {
        .outline-node {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }
      }
    }

    .content-preview {
      .empty-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 400px;
      }

      .report-content {
        .report-header {
          text-align: center;
          margin-bottom: 32px;
          padding-bottom: 16px;
          border-bottom: 2px solid var(--el-border-color);

          h2 {
            margin: 0 0 16px 0;
            color: var(--el-text-color-primary);
          }

          .report-meta {
            display: flex;
            justify-content: center;
            gap: 24px;
            color: var(--el-text-color-regular);
            font-size: 14px;
          }
        }

        .report-section {
          margin-bottom: 32px;

          h3 {
            color: var(--el-text-color-primary);
            border-bottom: 1px solid var(--el-border-color);
            padding-bottom: 8px;
            margin-bottom: 16px;
          }

          h4 {
            color: var(--el-text-color-primary);
            margin: 16px 0 8px 0;
          }

          .summary-content {
            .key-findings {
              margin-top: 16px;

              ul {
                padding-left: 20px;

                li {
                  margin-bottom: 8px;
                  line-height: 1.6;
                }
              }
            }
          }

          .performance-metrics {
            margin-bottom: 24px;
          }

          .chart-container {
            height: 300px;
            background: var(--el-color-info-light-9);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--el-text-color-placeholder);
            margin: 16px 0;
          }

          .ai-interpretation {
            margin-top: 16px;
          }

          .risk-metrics {
            margin-bottom: 24px;
          }

          .risk-breakdown {
            margin-top: 16px;
          }

          .recommendations-list {
            .recommendation-card {
              margin-bottom: 16px;

              .rec-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;

                h4 {
                  margin: 0;
                }
              }

              .rec-description {
                color: var(--el-text-color-regular);
                margin-bottom: 12px;
              }

              .rec-details {
                display: flex;
                gap: 24px;

                .rec-metric {
                  display: flex;
                  gap: 8px;

                  .label {
                    color: var(--el-text-color-placeholder);
                  }

                  .value {
                    font-weight: 500;
                    color: var(--el-text-color-primary);
                  }
                }
              }
            }
          }

          .chart-insights {
            .insight-item {
              margin-bottom: 16px;
              padding: 16px;
              border: 1px solid var(--el-border-color);
              border-radius: 8px;

              .insight-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;

                h4 {
                  margin: 0;
                }
              }

              .insight-content {
                p {
                  margin-bottom: 8px;
                  line-height: 1.6;

                  strong {
                    color: var(--el-text-color-primary);
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  .generation-progress {
    .progress-info {
      text-align: center;
      margin-bottom: 24px;

      h4 {
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }
    }

    .task-list {
      .task-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;

        &.active {
          color: var(--el-color-primary);
          font-weight: 500;
        }

        &.completed {
          color: var(--el-color-success);
        }

        .task-icon {
          &.success {
            color: var(--el-color-success);
          }

          &.processing {
            color: var(--el-color-primary);
          }

          &.pending {
            color: var(--el-text-color-placeholder);
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .intelligent-report-generator {
    .el-col {
      margin-bottom: 16px;
    }

    .report-header .report-meta {
      flex-direction: column;
      gap: 8px;
    }

    .rec-details {
      flex-direction: column !important;
      gap: 8px !important;
    }
  }
}
</style>