<template>
  <div class="qlib-correlation-matrix">
    <div class="chart-header">
      <div class="header-left">
        <h3 class="chart-title">
          <el-icon><Grid /></el-icon>
          相关性矩阵分析
        </h3>
        <p class="chart-subtitle">基于Qlib因子和资产的相关性热力图分析</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button 
            :type="matrixType === 'factor' ? 'primary' : ''" 
            @click="matrixType = 'factor'"
            size="small"
          >
            因子相关性
          </el-button>
          <el-button 
            :type="matrixType === 'asset' ? 'primary' : ''" 
            @click="matrixType = 'asset'"
            size="small"
          >
            资产相关性
          </el-button>
          <el-button 
            :type="matrixType === 'cross' ? 'primary' : ''" 
            @click="matrixType = 'cross'"
            size="small"
          >
            因子-资产交叉
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <el-select v-model="correlationMethod" size="small" style="width: 120px" @change="updateMatrix">
          <el-option label="Pearson" value="pearson" />
          <el-option label="Spearman" value="spearman" />
          <el-option label="Kendall" value="kendall" />
        </el-select>
        <el-divider direction="vertical" />
        <el-select v-model="timeWindow" size="small" style="width: 120px" @change="updateMatrix">
          <el-option label="最近1个月" value="1M" />
          <el-option label="最近3个月" value="3M" />
          <el-option label="最近6个月" value="6M" />
          <el-option label="最近1年" value="1Y" />
        </el-select>
        <el-divider direction="vertical" />
        <el-dropdown @command="handleExport">
          <el-button size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出PNG</el-dropdown-item>
              <el-dropdown-item command="csv">导出CSV</el-dropdown-item>
              <el-dropdown-item command="excel">导出Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="chart-controls">
      <div class="selector-group">
        <div class="factor-selector" v-if="matrixType === 'factor' || matrixType === 'cross'">
          <el-select 
            v-model="selectedFactors" 
            multiple 
            filterable 
            placeholder="选择因子"
            style="width: 300px"
            @change="updateMatrix"
          >
            <el-option
              v-for="factor in availableFactors"
              :key="factor.id"
              :label="factor.name"
              :value="factor.id"
            >
              <span class="factor-option">
                <span class="factor-name">{{ factor.name }}</span>
                <span class="factor-category">{{ factor.category }}</span>
              </span>
            </el-option>
          </el-select>
        </div>
        
        <div class="asset-selector" v-if="matrixType === 'asset' || matrixType === 'cross'">
          <el-select 
            v-model="selectedAssets" 
            multiple 
            filterable 
            placeholder="选择资产"
            style="width: 300px"
            @change="updateMatrix"
          >
            <el-option
              v-for="asset in availableAssets"
              :key="asset.symbol"
              :label="asset.name"
              :value="asset.symbol"
            >
              <span class="asset-option">
                <span class="asset-name">{{ asset.name }}</span>
                <span class="asset-symbol">{{ asset.symbol }}</span>
              </span>
            </el-option>
          </el-select>
        </div>
      </div>
      
      <div class="matrix-options">
        <el-checkbox v-model="showColorScale" @change="updateMatrix">显示色标</el-checkbox>
        <el-checkbox v-model="showNumbers" @change="updateMatrix">显示数值</el-checkbox>
        <el-checkbox v-model="clusterMode" @change="updateMatrix">聚类排序</el-checkbox>
        <el-slider
          v-model="correlationThreshold"
          :min="0"
          :max="1"
          :step="0.05"
          :format-tooltip="formatThreshold"
          style="width: 150px; margin-left: 20px"
          @change="updateMatrix"
        />
        <span class="threshold-label">阈值: {{ correlationThreshold.toFixed(2) }}</span>
      </div>
    </div>

    <div class="chart-container">
      <div 
        ref="matrixContainer" 
        class="correlation-matrix"
        v-loading="loading"
        element-loading-text="正在计算相关性矩阵..."
      ></div>
      
      <div class="matrix-stats" v-if="matrixStats">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">平均相关性</div>
            <div class="stat-value">{{ matrixStats.avgCorrelation.toFixed(3) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最大相关性</div>
            <div class="stat-value positive">{{ matrixStats.maxCorrelation.toFixed(3) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最小相关性</div>
            <div class="stat-value negative">{{ matrixStats.minCorrelation.toFixed(3) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">高相关对数</div>
            <div class="stat-value">{{ matrixStats.highCorrelationPairs }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="correlation-analysis" v-if="correlationInsights.length > 0">
      <el-collapse v-model="activeAnalysis">
        <el-collapse-item title="相关性详细分析" name="detail">
          <div class="correlation-table">
            <el-table :data="correlationPairs" size="small" max-height="300">
              <el-table-column prop="pair" label="资产/因子对" width="200" />
              <el-table-column prop="correlation" label="相关系数" width="120" sortable>
                <template #default="scope">
                  <span :class="getCorrelationClass(scope.row.correlation)">
                    {{ scope.row.correlation.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="pValue" label="P值" width="100" sortable />
              <el-table-column prop="significance" label="显著性" width="100">
                <template #default="scope">
                  <el-tag :type="getSignificanceType(scope.row.pValue)" size="small">
                    {{ getSignificanceLevel(scope.row.pValue) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="interpretation" label="解释" min-width="200" />
            </el-table>
          </div>
        </el-collapse-item>
        
        <el-collapse-item title="AI相关性洞察" name="insights">
          <div class="ai-insights">
            <div class="insight-item" v-for="insight in correlationInsights" :key="insight.type">
              <div class="insight-header">
                <el-icon class="insight-icon"><Cpu /></el-icon>
                <span class="insight-title">{{ insight.title }}</span>
                <el-tag :type="getInsightType(insight.confidence)" size="small">
                  置信度: {{ (insight.confidence * 100).toFixed(0) }}%
                </el-tag>
              </div>
              <div class="insight-content">{{ insight.content }}</div>
              <div class="insight-suggestions" v-if="insight.suggestions">
                <div class="suggestions-title">投资建议:</div>
                <ul class="suggestions-list">
                  <li v-for="suggestion in insight.suggestions" :key="suggestion">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Grid, ArrowDown, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useQlibFactorsStore } from '@/stores/qlib-factors'

interface FactorInfo {
  id: string
  name: string
  category: string
  expression: string
}

interface AssetInfo {
  symbol: string
  name: string
  sector: string
  market: string
}

interface CorrelationPair {
  pair: string
  correlation: number
  pValue: number
  significance: string
  interpretation: string
}

interface MatrixStats {
  avgCorrelation: number
  maxCorrelation: number
  minCorrelation: number
  highCorrelationPairs: number
}

interface AIInsight {
  type: string
  title: string
  content: string
  confidence: number
  suggestions?: string[]
}

// 响应式数据
const loading = ref(false)
const matrixContainer = ref<HTMLElement>()
const chart = ref<echarts.ECharts>()

// 矩阵控制
const matrixType = ref<'factor' | 'asset' | 'cross'>('factor')
const correlationMethod = ref('pearson')
const timeWindow = ref('3M')
const showColorScale = ref(true)
const showNumbers = ref(true)
const clusterMode = ref(false)
const correlationThreshold = ref(0.3)

// 选择器数据
const selectedFactors = ref<string[]>([])
const selectedAssets = ref<string[]>([])

// 数据源
const availableFactors = ref<FactorInfo[]>([
  { id: 'momentum_20', name: '20日动量', category: '动量', expression: '($close / Ref($close, 20)) - 1' },
  { id: 'rsi_14', name: 'RSI指标', category: '技术', expression: 'RSI($close, 14)' },
  { id: 'pe_ratio', name: '市盈率', category: '估值', expression: '$pe_ttm' },
  { id: 'volume_ratio', name: '成交量比', category: '成交量', expression: '$volume / Mean($volume, 20)' },
  { id: 'volatility_20', name: '20日波动率', category: '风险', expression: 'Std(Log($close / Ref($close, 1)), 20)' },
  { id: 'ema_12', name: '12日EMA', category: '趋势', expression: 'EMA($close, 12)' }
])

const availableAssets = ref<AssetInfo[]>([
  { symbol: '000001.SZ', name: '平安银行', sector: '金融', market: 'SZ' },
  { symbol: '000002.SZ', name: '万科A', sector: '房地产', market: 'SZ' },
  { symbol: '000858.SZ', name: '五粮液', sector: '食品饮料', market: 'SZ' },
  { symbol: '600036.SH', name: '招商银行', sector: '金融', market: 'SH' },
  { symbol: '600519.SH', name: '贵州茅台', sector: '食品饮料', market: 'SH' },
  { symbol: '600887.SH', name: '伊利股份', sector: '食品饮料', market: 'SH' }
])

// 分析数据
const matrixStats = ref<MatrixStats>()
const correlationPairs = ref<CorrelationPair[]>([])
const correlationInsights = ref<AIInsight[]>([])
const activeAnalysis = ref(['detail'])

// Store
const qlibFactorsStore = useQlibFactorsStore()

// 计算属性
const matrixData = computed(() => {
  if (matrixType.value === 'factor') {
    return generateFactorCorrelationMatrix()
  } else if (matrixType.value === 'asset') {
    return generateAssetCorrelationMatrix()
  } else {
    return generateCrossCorrelationMatrix()
  }
})

// 方法
const initMatrix = async () => {
  if (!matrixContainer.value) return
  
  chart.value = echarts.init(matrixContainer.value)
  
  const option = {
    title: {
      text: '相关性矩阵',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        if (params.data) {
          return `
            <div style="text-align: center;">
              <div style="font-weight: bold; margin-bottom: 5px;">
                ${params.data[3]} & ${params.data[4]}
              </div>
              <div>相关系数: <span style="color: ${getCorrelationColor(params.data[2])}; font-weight: bold;">
                ${params.data[2].toFixed(4)}
              </span></div>
            </div>
          `
        }
        return ''
      }
    },
    animation: false,
    grid: {
      height: '70%',
      top: '10%',
      left: '20%'
    },
    xAxis: {
      type: 'category',
      data: [],
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'category',
      data: [],
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
                '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      },
      show: showColorScale.value
    },
    series: [{
      name: '相关性',
      type: 'heatmap',
      data: [],
      label: {
        show: showNumbers.value,
        formatter: '{c}'
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  chart.value.setOption(option)
}

const updateMatrix = async () => {
  if (!chart.value) return
  
  loading.value = true
  
  try {
    const data = await generateMatrixData()
    
    chart.value.setOption({
      xAxis: {
        data: data.xLabels
      },
      yAxis: {
        data: data.yLabels
      },
      visualMap: {
        show: showColorScale.value
      },
      series: [{
        data: data.matrixData,
        label: {
          show: showNumbers.value
        }
      }]
    })
    
    // 计算统计信息
    calculateMatrixStats(data.matrixData)
    
    // 生成相关性对分析
    generateCorrelationPairs(data)
    
    // 生成AI洞察
    generateCorrelationInsights()
    
  } catch (error) {
    console.error('更新相关性矩阵失败:', error)
    ElMessage.error('更新相关性矩阵失败')
  } finally {
    loading.value = false
  }
}

const generateMatrixData = async () => {
  const labels = getLabelsForMatrixType()
  const size = labels.length
  const matrixData: any[] = []
  
  // 模拟相关性计算
  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      let correlation: number
      
      if (i === j) {
        correlation = 1.0 // 自相关
      } else {
        // 生成模拟相关性数据
        correlation = generateMockCorrelation(labels[i], labels[j])
        
        // 应用阈值过滤
        if (Math.abs(correlation) < correlationThreshold.value) {
          correlation = correlation * 0.3 // 降低低相关性值
        }
      }
      
      matrixData.push([j, i, correlation, labels[j], labels[i]])
    }
  }
  
  return {
    xLabels: labels,
    yLabels: labels,
    matrixData: matrixData
  }
}

const getLabelsForMatrixType = (): string[] => {
  if (matrixType.value === 'factor') {
    return selectedFactors.value.map(id => {
      const factor = availableFactors.value.find(f => f.id === id)
      return factor?.name || id
    })
  } else if (matrixType.value === 'asset') {
    return selectedAssets.value.map(symbol => {
      const asset = availableAssets.value.find(a => a.symbol === symbol)
      return asset?.name || symbol
    })
  } else {
    // 交叉相关性：因子 vs 资产
    const factorLabels = selectedFactors.value.map(id => {
      const factor = availableFactors.value.find(f => f.id === id)
      return `F:${factor?.name || id}`
    })
    const assetLabels = selectedAssets.value.map(symbol => {
      const asset = availableAssets.value.find(a => a.symbol === symbol)
      return `A:${asset?.name || symbol}`
    })
    return [...factorLabels, ...assetLabels]
  }
}

const generateMockCorrelation = (label1: string, label2: string): number => {
  // 基于标签生成确定性的模拟相关性
  const hash = (str: string) => {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // 转换为32位整数
    }
    return hash
  }
  
  const combined = label1 + label2
  const hashValue = Math.abs(hash(combined))
  
  // 生成-1到1之间的相关性值
  let correlation = (hashValue % 2000) / 1000 - 1
  
  // 根据类型调整相关性强度
  if (matrixType.value === 'factor') {
    // 同类因子通常有更高的相关性
    if (isSameCategory(label1, label2)) {
      correlation = Math.abs(correlation) * 0.7 + 0.3
    } else {
      correlation = correlation * 0.5
    }
  } else if (matrixType.value === 'asset') {
    // 同行业资产通常有更高的相关性
    if (isSameSector(label1, label2)) {
      correlation = Math.abs(correlation) * 0.6 + 0.4
    } else {
      correlation = correlation * 0.4
    }
  }
  
  return Math.max(-1, Math.min(1, correlation))
}

const isSameCategory = (label1: string, label2: string): boolean => {
  const factor1 = availableFactors.value.find(f => f.name === label1)
  const factor2 = availableFactors.value.find(f => f.name === label2)
  return factor1?.category === factor2?.category
}

const isSameSector = (label1: string, label2: string): boolean => {
  const asset1 = availableAssets.value.find(a => a.name === label1)
  const asset2 = availableAssets.value.find(a => a.name === label2)
  return asset1?.sector === asset2?.sector
}

const calculateMatrixStats = (matrixData: any[]) => {
  const correlations = matrixData
    .filter(item => item[0] !== item[1]) // 排除自相关
    .map(item => item[2])
  
  const avgCorrelation = correlations.reduce((sum, val) => sum + Math.abs(val), 0) / correlations.length
  const maxCorrelation = Math.max(...correlations)
  const minCorrelation = Math.min(...correlations)
  const highCorrelationPairs = correlations.filter(val => Math.abs(val) > 0.7).length
  
  matrixStats.value = {
    avgCorrelation,
    maxCorrelation,
    minCorrelation,
    highCorrelationPairs
  }
}

const generateCorrelationPairs = (data: any) => {
  const pairs: CorrelationPair[] = []
  
  for (const item of data.matrixData) {
    if (item[0] !== item[1] && Math.abs(item[2]) > correlationThreshold.value) {
      const correlation = item[2]
      const pValue = Math.random() * 0.1 // 模拟p值
      
      pairs.push({
        pair: `${item[4]} - ${item[3]}`,
        correlation: correlation,
        pValue: pValue,
        significance: getSignificanceLevel(pValue),
        interpretation: getCorrelationInterpretation(correlation)
      })
    }
  }
  
  // 按相关性绝对值排序
  pairs.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
  
  correlationPairs.value = pairs.slice(0, 20) // 只显示前20个
}

const generateCorrelationInsights = () => {
  const insights: AIInsight[] = []
  
  if (matrixStats.value) {
    // 整体相关性分析
    if (matrixStats.value.avgCorrelation > 0.5) {
      insights.push({
        type: 'high_correlation',
        title: '高相关性警告',
        content: `检测到平均相关性较高(${matrixStats.value.avgCorrelation.toFixed(3)})，表明选择的因子/资产之间存在较强的共线性，可能影响分散化效果。`,
        confidence: 0.85,
        suggestions: [
          '考虑选择来自不同类别的因子以降低相关性',
          '在构建投资组合时适当降低高相关资产的权重',
          '使用主成分分析等降维技术处理多重共线性'
        ]
      })
    }
    
    // 低相关性机会
    if (matrixStats.value.minCorrelation < -0.3) {
      insights.push({
        type: 'negative_correlation',
        title: '负相关性机会',
        content: `发现存在较强负相关关系(最低${matrixStats.value.minCorrelation.toFixed(3)})，这为构建对冲策略提供了机会。`,
        confidence: 0.78,
        suggestions: [
          '利用负相关资产构建市场中性策略',
          '在风险管理中使用负相关因子进行对冲',
          '考虑配对交易策略的可能性'
        ]
      })
    }
    
    // 聚类分析洞察
    if (matrixType.value === 'factor') {
      insights.push({
        type: 'factor_clustering',
        title: '因子聚类分析',
        content: '基于相关性分析，建议将因子分为几个不同的类群，每个类群代表不同的市场特征和风险因素。',
        confidence: 0.72,
        suggestions: [
          '在每个类群中选择代表性因子以提高效率',
          '根据市场环境轮换不同类群的因子',
          '使用类群间的低相关性构建多因子模型'
        ]
      })
    }
  }
  
  correlationInsights.value = insights
}

const getCorrelationInterpretation = (correlation: number): string => {
  const abs = Math.abs(correlation)
  if (abs > 0.8) return correlation > 0 ? '极强正相关' : '极强负相关'
  if (abs > 0.6) return correlation > 0 ? '强正相关' : '强负相关'
  if (abs > 0.4) return correlation > 0 ? '中等正相关' : '中等负相关'
  if (abs > 0.2) return correlation > 0 ? '弱正相关' : '弱负相关'
  return '几乎无相关'
}

const getSignificanceLevel = (pValue: number): string => {
  if (pValue < 0.01) return '极显著'
  if (pValue < 0.05) return '显著'
  if (pValue < 0.1) return '边际显著'
  return '不显著'
}

const getCorrelationColor = (correlation: number): string => {
  if (correlation > 0.6) return '#d73027'
  if (correlation > 0.3) return '#f46d43'
  if (correlation > -0.3) return '#ffffcc'
  if (correlation > -0.6) return '#74add1'
  return '#313695'
}

const getCorrelationClass = (correlation: number): string => {
  const abs = Math.abs(correlation)
  if (abs > 0.7) return 'high-correlation'
  if (abs > 0.4) return 'medium-correlation'
  return 'low-correlation'
}

const getSignificanceType = (pValue: number): string => {
  if (pValue < 0.01) return 'success'
  if (pValue < 0.05) return 'primary'
  if (pValue < 0.1) return 'warning'
  return 'info'
}

const getInsightType = (confidence: number): string => {
  if (confidence > 0.8) return 'success'
  if (confidence > 0.6) return 'warning'
  return 'info'
}

const formatThreshold = (value: number): string => {
  return `${value.toFixed(2)}`
}

const handleExport = (command: string) => {
  switch (command) {
    case 'png':
      if (chart.value) {
        const url = chart.value.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#fff'
        })
        const link = document.createElement('a')
        link.download = `correlation-matrix-${Date.now()}.png`
        link.href = url
        link.click()
      }
      break
    case 'csv':
    case 'excel':
      ElMessage.info('导出功能开发中...')
      break
  }
}

// 生成各类型矩阵的辅助方法
const generateFactorCorrelationMatrix = () => {
  // 实现因子相关性矩阵生成逻辑
  return {}
}

const generateAssetCorrelationMatrix = () => {
  // 实现资产相关性矩阵生成逻辑
  return {}
}

const generateCrossCorrelationMatrix = () => {
  // 实现交叉相关性矩阵生成逻辑
  return {}
}

// 监听器
watch([matrixType, correlationMethod, timeWindow, showColorScale, showNumbers, clusterMode], () => {
  if ((matrixType.value === 'factor' && selectedFactors.value.length > 1) ||
      (matrixType.value === 'asset' && selectedAssets.value.length > 1) ||
      (matrixType.value === 'cross' && selectedFactors.value.length > 0 && selectedAssets.value.length > 0)) {
    updateMatrix()
  }
}, { deep: true })

// 生命周期
onMounted(async () => {
  await nextTick()
  await initMatrix()
  
  // 默认选择一些因子和资产
  selectedFactors.value = availableFactors.value.slice(0, 4).map(f => f.id)
  selectedAssets.value = availableAssets.value.slice(0, 4).map(a => a.symbol)
  await updateMatrix()
})

// 暴露给模板的方法
defineExpose({
  updateMatrix,
  exportMatrix: () => handleExport('png')
})
</script>

<style lang="scss" scoped>
.qlib-correlation-matrix {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  .chart-title {
    margin: 0;
    font-size: 18px;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: #409eff;
    }
  }
  
  .chart-subtitle {
    margin: 5px 0 0 0;
    color: #666;
    font-size: 13px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  flex-wrap: wrap;
  gap: 20px;
}

.selector-group {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.factor-option,
.asset-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.factor-name,
.asset-name {
  font-weight: 500;
}

.factor-category,
.asset-symbol {
  font-size: 12px;
  color: #666;
  margin-left: 10px;
}

.matrix-options {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.threshold-label {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.chart-container {
  position: relative;
}

.correlation-matrix {
  width: 100%;
  height: 600px;
}

.matrix-stats {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.stat-item {
  text-align: center;
  
  .stat-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 4px;
  }
  
  .stat-value {
    font-size: 16px;
    font-weight: bold;
    
    &.positive {
      color: #67c23a;
    }
    
    &.negative {
      color: #f56c6c;
    }
  }
}

.correlation-analysis {
  margin-top: 20px;
}

.correlation-table {
  :deep(.el-table) {
    font-size: 12px;
  }
  
  .high-correlation {
    color: #f56c6c;
    font-weight: bold;
  }
  
  .medium-correlation {
    color: #e6a23c;
    font-weight: 500;
  }
  
  .low-correlation {
    color: #999;
  }
}

.ai-insights {
  .insight-item {
    margin-bottom: 20px;
    padding: 15px;
    background: linear-gradient(135deg, #f6f8ff 0%, #e8f4f8 100%);
    border-left: 4px solid #409eff;
    border-radius: 6px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .insight-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    
    .insight-icon {
      color: #409eff;
    }
    
    .insight-title {
      font-weight: bold;
      color: #2c3e50;
    }
  }
  
  .insight-content {
    color: #555;
    line-height: 1.5;
    margin-bottom: 10px;
  }
  
  .suggestions-title {
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 5px;
  }
  
  .suggestions-list {
    margin: 0;
    padding-left: 20px;
    
    li {
      color: #555;
      margin: 3px 0;
    }
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .header-right {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .selector-group {
    flex-direction: column;
    width: 100%;
    
    .el-select {
      width: 100% !important;
    }
  }
  
  .matrix-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    
    .el-slider {
      width: 100% !important;
    }
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .correlation-matrix {
    height: 400px;
  }
}
</style>