<template>
  <div class="qlib-factor-analyzer">
    <!-- 因子分析头部 -->
    <el-card class="analyzer-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><DataAnalysis /></el-icon>
            <span>Qlib因子IC分析与有效性评估</span>
          </div>
          <div class="header-actions">
            <el-button @click="refreshAnalysis" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新分析
            </el-button>
            <el-button @click="exportAnalysis">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
            <el-button type="primary" @click="createNewAnalysis">
              <el-icon><Plus /></el-icon>
              新建分析
            </el-button>
          </div>
        </div>
      </template>

      <!-- 因子选择器 -->
      <div class="factor-selector">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="选择因子">
              <el-select 
                v-model="selectedFactors" 
                multiple
                placeholder="请选择要分析的因子"
                @change="loadFactorAnalysis"
              >
                <el-option-group 
                  v-for="group in factorGroups" 
                  :key="group.label" 
                  :label="group.label"
                >
                  <el-option
                    v-for="factor in group.factors"
                    :key="factor.name"
                    :label="factor.display_name"
                    :value="factor.name"
                  >
                    <div class="factor-option">
                      <span>{{ factor.display_name }}</span>
                      <el-tag size="small" :type="getFactorTagType(factor.category)">
                        {{ factor.category }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="timeRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="loadFactorAnalysis"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="股票池">
              <el-select v-model="selectedUniverse" @change="loadFactorAnalysis">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="中证1000" value="CSI1000" />
                <el-option label="全A股" value="ALL" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="前瞻天数">
              <el-input-number 
                v-model="forwardDays" 
                :min="1" 
                :max="30" 
                @change="loadFactorAnalysis"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- IC分析概览 -->
    <el-row :gutter="16" class="ic-overview">
      <el-col :span="6">
        <el-card class="metric-card ic-mean">
          <el-statistic 
            title="平均IC" 
            :value="icMetrics.meanIC" 
            :precision="4"
          />
          <div class="metric-trend">
            <el-icon :class="['trend-icon', icMetrics.meanIC >= 0 ? 'positive' : 'negative']">
              <component :is="icMetrics.meanIC >= 0 ? 'CaretTop' : 'CaretBottom'" />
            </el-icon>
            <span class="trend-text">{{ getICRating(icMetrics.meanIC) }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card ic-ir">
          <el-statistic 
            title="IC信息比率(IR)" 
            :value="icMetrics.informationRatio" 
            :precision="3"
          />
          <div class="metric-rating">
            <el-rate 
              v-model="irRating" 
              disabled 
              :max="5"
              :colors="['#ff6b6b', '#feca57', '#48dbfb', '#0be881', '#5f27cd']"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card ic-stability">
          <el-statistic 
            title="IC稳定性" 
            :value="icMetrics.stability" 
            suffix="%" 
            :precision="1"
          />
          <div class="stability-indicator">
            <el-progress 
              :percentage="icMetrics.stability"
              :color="getStabilityColor(icMetrics.stability)"
              :show-text="false"
              :stroke-width="8"
            />
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card ic-decay">
          <el-statistic 
            title="IC衰减周期" 
            :value="icMetrics.decayPeriod" 
            suffix="天"
          />
          <div class="decay-chart">
            <el-progress 
              type="circle" 
              :percentage="Math.min(icMetrics.decayPeriod / 20 * 100, 100)"
              :width="60"
              :stroke-width="6"
              :color="getDecayColor(icMetrics.decayPeriod)"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细分析图表 -->
    <el-row :gutter="16" class="analysis-charts">
      <!-- IC时序图 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>因子IC时序分析</span>
              <div class="chart-controls">
                <el-radio-group v-model="icChartType" size="small">
                  <el-radio-button label="daily">日频IC</el-radio-button>
                  <el-radio-button label="rolling">滚动IC</el-radio-button>
                  <el-radio-button label="cumulative">累积IC</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="chart-container" ref="icTimeSeriesRef">
            <div class="chart-placeholder">IC时序图表区域</div>
          </div>
        </el-card>
      </el-col>

      <!-- IC分布图 -->
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>IC分布统计</span>
          </template>
          <div class="chart-container" ref="icDistributionRef">
            <div class="chart-placeholder">IC分布直方图</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="analysis-charts">
      <!-- 因子分层分析 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>因子分层收益分析</span>
              <el-select v-model="layerAnalysisType" size="small" style="width: 120px">
                <el-option label="5分层" value="5" />
                <el-option label="10分层" value="10" />
                <el-option label="20分层" value="20" />
              </el-select>
            </div>
          </template>
          <div class="chart-container" ref="layerAnalysisRef">
            <div class="chart-placeholder">分层收益图表</div>
          </div>
        </el-card>
      </el-col>

      <!-- 因子衰减分析 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>因子预测能力衰减</span>
          </template>
          <div class="chart-container" ref="decayAnalysisRef">
            <div class="chart-placeholder">衰减分析图表</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 因子详细统计表 -->
    <el-card class="factor-stats-card">
      <template #header>
        <div class="stats-header">
          <span>因子统计详情</span>
          <div class="stats-controls">
            <el-button size="small" @click="sortFactors('ic')">按IC排序</el-button>
            <el-button size="small" @click="sortFactors('ir')">按IR排序</el-button>
            <el-button size="small" @click="sortFactors('stability')">按稳定性排序</el-button>
          </div>
        </div>
      </template>

      <el-table :data="factorStats" border>
        <el-table-column prop="factor_name" label="因子名称" width="200" fixed />
        <el-table-column prop="category" label="类别" width="100">
          <template #default="{ row }">
            <el-tag :type="getFactorTagType(row.category)" size="small">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mean_ic" label="平均IC" width="120">
          <template #default="{ row }">
            <span :class="[row.mean_ic >= 0 ? 'positive' : 'negative']">
              {{ row.mean_ic.toFixed(4) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="ic_std" label="IC标准差" width="120">
          <template #default="{ row }">
            {{ row.ic_std.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="information_ratio" label="IR" width="120">
          <template #default="{ row }">
            <span :class="[row.information_ratio >= 0 ? 'positive' : 'negative']">
              {{ row.information_ratio.toFixed(3) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="stability" label="稳定性" width="120">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.stability" 
              :color="getStabilityColor(row.stability)"
              :format="() => `${row.stability.toFixed(1)}%`"
            />
          </template>
        </el-table-column>
        <el-table-column prop="t_stat" label="T统计量" width="120">
          <template #default="{ row }">
            {{ row.t_stat.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="p_value" label="P值" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getPValueType(row.p_value)" 
              size="small"
            >
              {{ row.p_value.toFixed(3) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="turnover" label="换手率" width="120">
          <template #default="{ row }">
            {{ (row.turnover * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewFactorDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button size="small" @click="analyzeFactorCorrelation(row)">
              <el-icon><Connection /></el-icon>
              相关性
            </el-button>
            <el-button size="small" @click="backtestFactor(row)">
              <el-icon><TrendCharts /></el-icon>
              回测
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 因子相关性热力图 -->
    <el-card class="correlation-card" v-if="selectedFactors.length > 1">
      <template #header>
        <div class="correlation-header">
          <span>因子相关性分析</span>
          <el-select v-model="correlationMethod" size="small" style="width: 120px">
            <el-option label="皮尔逊" value="pearson" />
            <el-option label="斯皮尔曼" value="spearman" />
            <el-option label="肯德尔" value="kendall" />
          </el-select>
        </div>
      </template>
      <div class="correlation-heatmap" ref="correlationHeatmapRef">
        <div class="chart-placeholder">因子相关性热力图</div>
      </div>
    </el-card>

    <!-- 因子详情对话框 -->
    <el-dialog v-model="showFactorDetail" title="因子详细分析" width="80%">
      <div v-if="selectedFactorDetail" class="factor-detail">
        <el-tabs v-model="activeDetailTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions title="因子基本信息" :column="2" border>
              <el-descriptions-item label="因子名称">
                {{ selectedFactorDetail.factor_name }}
              </el-descriptions-item>
              <el-descriptions-item label="因子类别">
                {{ selectedFactorDetail.category }}
              </el-descriptions-item>
              <el-descriptions-item label="计算公式">
                <code>{{ selectedFactorDetail.formula || '未提供' }}</code>
              </el-descriptions-item>
              <el-descriptions-item label="数据频率">
                {{ selectedFactorDetail.frequency || '日频' }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ selectedFactorDetail.update_time || '实时' }}
              </el-descriptions-item>
              <el-descriptions-item label="覆盖范围">
                {{ selectedFactorDetail.coverage || '全市场' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>
          
          <el-tab-pane label="IC分析" name="ic">
            <div class="ic-detail-analysis">
              <div class="detail-chart" ref="detailICChartRef">
                <div class="chart-placeholder">详细IC分析图表</div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="分层分析" name="layer">
            <div class="layer-detail-analysis">
              <div class="detail-chart" ref="detailLayerChartRef">
                <div class="chart-placeholder">详细分层分析图表</div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="因子值分布" name="distribution">
            <div class="distribution-analysis">
              <div class="detail-chart" ref="factorDistributionRef">
                <div class="chart-placeholder">因子值分布图表</div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Refresh, Download, Plus, CaretTop, CaretBottom,
  View, Connection, TrendCharts
} from '@element-plus/icons-vue'

// 数据结构定义
interface Factor {
  name: string
  display_name: string
  category: string
  formula?: string
  frequency?: string
  update_time?: string
  coverage?: string
}

interface FactorGroup {
  label: string
  factors: Factor[]
}

interface ICMetrics {
  meanIC: number
  informationRatio: number
  stability: number
  decayPeriod: number
}

interface FactorStat {
  factor_name: string
  category: string
  mean_ic: number
  ic_std: number
  information_ratio: number
  stability: number
  t_stat: number
  p_value: number
  turnover: number
  formula?: string
  frequency?: string
  update_time?: string
  coverage?: string
}

// 响应式数据
const loading = ref(false)
const selectedFactors = ref<string[]>([])
const timeRange = ref(['2023-01-01', '2023-12-31'])
const selectedUniverse = ref('CSI300')
const forwardDays = ref(5)
const icChartType = ref('daily')
const layerAnalysisType = ref('5')
const correlationMethod = ref('pearson')
const showFactorDetail = ref(false)
const selectedFactorDetail = ref<FactorStat | null>(null)
const activeDetailTab = ref('basic')

const factorGroups = ref<FactorGroup[]>([
  {
    label: '价值因子',
    factors: [
      { name: 'pe_ratio', display_name: '市盈率', category: '价值' },
      { name: 'pb_ratio', display_name: '市净率', category: '价值' },
      { name: 'ps_ratio', display_name: '市销率', category: '价值' },
      { name: 'pcf_ratio', display_name: '市现率', category: '价值' }
    ]
  },
  {
    label: '成长因子', 
    factors: [
      { name: 'roe_growth', display_name: 'ROE增长率', category: '成长' },
      { name: 'revenue_growth', display_name: '营收增长率', category: '成长' },
      { name: 'profit_growth', display_name: '利润增长率', category: '成长' }
    ]
  },
  {
    label: '动量因子',
    factors: [
      { name: 'return_1m', display_name: '1月收益率', category: '动量' },
      { name: 'return_3m', display_name: '3月收益率', category: '动量' },
      { name: 'return_12m', display_name: '12月收益率', category: '动量' }
    ]
  },
  {
    label: '技术因子',
    factors: [
      { name: 'rsi', display_name: 'RSI', category: '技术' },
      { name: 'macd', display_name: 'MACD', category: '技术' },
      { name: 'bollinger', display_name: '布林带', category: '技术' }
    ]
  }
])

const icMetrics = reactive<ICMetrics>({
  meanIC: 0,
  informationRatio: 0,
  stability: 0,
  decayPeriod: 0
})

const factorStats = ref<FactorStat[]>([])

// 计算属性
const irRating = computed(() => {
  const ir = icMetrics.informationRatio
  if (ir >= 1.5) return 5
  if (ir >= 1.0) return 4
  if (ir >= 0.5) return 3
  if (ir >= 0.2) return 2
  return 1
})

// 方法
const loadFactorAnalysis = async () => {
  if (selectedFactors.value.length === 0) return

  loading.value = true

  try {
    const response = await fetch('/api/v1/qlib-factors/ic-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        factors: selectedFactors.value,
        start_time: timeRange.value[0],
        end_time: timeRange.value[1],
        universe: selectedUniverse.value,
        forward_days: forwardDays.value
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      updateAnalysisData(result.data)
      ElMessage.success('因子分析加载成功')
    } else {
      throw new Error(result.message || '加载因子分析失败')
    }
  } catch (error) {
    console.error('加载因子分析失败:', error)
    ElMessage.error('加载因子分析失败: ' + error.message)
    
    // 降级到示例数据
    generateSampleAnalysis()
  } finally {
    loading.value = false
  }
}

const generateSampleAnalysis = () => {
  // 生成示例分析数据
  icMetrics.meanIC = 0.0456
  icMetrics.informationRatio = 1.234
  icMetrics.stability = 68.5
  icMetrics.decayPeriod = 8

  factorStats.value = selectedFactors.value.map((factor, index) => ({
    factor_name: getFactorDisplayName(factor),
    category: getFactorCategory(factor),
    mean_ic: 0.03 + Math.random() * 0.04,
    ic_std: 0.1 + Math.random() * 0.05,
    information_ratio: 0.5 + Math.random() * 1.0,
    stability: 60 + Math.random() * 30,
    t_stat: Math.random() * 4 - 2,
    p_value: Math.random() * 0.1,
    turnover: 0.1 + Math.random() * 0.3
  }))
}

const updateAnalysisData = (data: any) => {
  // 更新IC指标
  if (data.ic_metrics) {
    Object.assign(icMetrics, data.ic_metrics)
  }

  // 更新因子统计
  if (data.factor_stats) {
    factorStats.value = data.factor_stats
  }
}

const getFactorDisplayName = (factorName: string): string => {
  for (const group of factorGroups.value) {
    const factor = group.factors.find(f => f.name === factorName)
    if (factor) return factor.display_name
  }
  return factorName
}

const getFactorCategory = (factorName: string): string => {
  for (const group of factorGroups.value) {
    const factor = group.factors.find(f => f.name === factorName)
    if (factor) return factor.category
  }
  return '未知'
}

const refreshAnalysis = () => {
  loadFactorAnalysis()
}

const exportAnalysis = () => {
  ElMessage.success('分析报告导出功能开发中')
}

const createNewAnalysis = () => {
  ElMessage.info('跳转到新建分析页面')
}

const getFactorTagType = (category: string) => {
  const types: Record<string, string> = {
    '价值': 'success',
    '成长': 'primary', 
    '动量': 'warning',
    '技术': 'info'
  }
  return types[category] || 'default'
}

const getICRating = (ic: number) => {
  if (Math.abs(ic) >= 0.05) return '优秀'
  if (Math.abs(ic) >= 0.03) return '良好'
  if (Math.abs(ic) >= 0.01) return '一般'
  return '较差'
}

const getStabilityColor = (stability: number) => {
  if (stability >= 80) return '#67c23a'
  if (stability >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getDecayColor = (days: number) => {
  if (days <= 5) return '#67c23a'
  if (days <= 10) return '#e6a23c'
  return '#f56c6c'
}

const getPValueType = (pValue: number) => {
  if (pValue <= 0.01) return 'success'
  if (pValue <= 0.05) return 'primary'
  if (pValue <= 0.1) return 'warning'
  return 'danger'
}

const sortFactors = (sortBy: string) => {
  factorStats.value.sort((a, b) => {
    switch (sortBy) {
      case 'ic':
        return Math.abs(b.mean_ic) - Math.abs(a.mean_ic)
      case 'ir':
        return Math.abs(b.information_ratio) - Math.abs(a.information_ratio)
      case 'stability':
        return b.stability - a.stability
      default:
        return 0
    }
  })
}

const viewFactorDetail = (factor: FactorStat) => {
  selectedFactorDetail.value = factor
  showFactorDetail.value = true
}

const analyzeFactorCorrelation = (factor: FactorStat) => {
  ElMessage.info(`分析 ${factor.factor_name} 的相关性`)
}

const backtestFactor = (factor: FactorStat) => {
  ElMessage.info(`回测 ${factor.factor_name} 因子`)
}

// 生命周期
onMounted(() => {
  // 默认选择一些因子进行分析
  selectedFactors.value = ['pe_ratio', 'return_1m']
  loadFactorAnalysis()
})
</script>

<style scoped>
.qlib-factor-analyzer {
  padding: 20px;
}

.analyzer-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.factor-selector {
  padding: 16px 0;
}

.factor-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.ic-overview {
  margin-bottom: 24px;
}

.metric-card {
  text-align: center;
  position: relative;
  overflow: hidden;
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.metric-trend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.positive {
  color: #67c23a;
}

.trend-icon.negative {
  color: #f56c6c;
}

.trend-text {
  color: #909399;
}

.metric-rating {
  margin-top: 8px;
}

.stability-indicator {
  margin-top: 12px;
}

.decay-chart {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.analysis-charts {
  margin-bottom: 24px;
}

.chart-card {
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.chart-placeholder {
  color: #999;
  font-size: 14px;
}

.factor-stats-card {
  margin-bottom: 24px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-controls {
  display: flex;
  gap: 8px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.correlation-card {
  margin-bottom: 24px;
}

.correlation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.correlation-heatmap {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

.factor-detail {
  padding: 16px 0;
}

.ic-detail-analysis,
.layer-detail-analysis,
.distribution-analysis {
  padding: 16px 0;
}

.detail-chart {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
}

@media (max-width: 768px) {
  .qlib-factor-analyzer {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .factor-selector .el-col {
    margin-bottom: 16px;
  }
  
  .ic-overview .el-col {
    margin-bottom: 16px;
  }
  
  .analysis-charts .el-col {
    margin-bottom: 16px;
  }
}
</style>