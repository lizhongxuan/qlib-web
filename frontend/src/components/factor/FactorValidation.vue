<template>
  <div class="factor-validation">
    <!-- 测试头部 -->
    <div class="validation-header">
      <h3>
        <el-icon><TestTube /></el-icon>
        因子测试验证
      </h3>
      <p v-if="factor">正在测试因子: <strong>{{ factor.name }}</strong></p>
    </div>

    <!-- 测试配置 -->
    <el-card class="test-config-card">
      <template #header>
        <span>测试配置</span>
      </template>
      
      <el-form :model="testConfig" label-width="120px" size="default">
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="测试时间段">
              <el-date-picker
                v-model="testConfig.dateRange"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="股票池">
              <el-select v-model="testConfig.stockPool" style="width: 100%">
                <el-option label="沪深300" value="HS300" />
                <el-option label="中证500" value="ZZ500" />
                <el-option label="中证1000" value="ZZ1000" />
                <el-option label="全A股" value="ALL" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="更新频率">
              <el-select v-model="testConfig.frequency" style="width: 100%">
                <el-option label="日频" value="daily" />
                <el-option label="周频" value="weekly" />
                <el-option label="月频" value="monthly" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="基准指数">
              <el-select v-model="testConfig.benchmark" style="width: 100%">
                <el-option label="沪深300指数" value="000300.SH" />
                <el-option label="中证500指数" value="000905.SH" />
                <el-option label="创业板指数" value="399006.SZ" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="分组数量">
              <el-input-number 
                v-model="testConfig.groups" 
                :min="3" 
                :max="20" 
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <div class="test-actions">
        <el-button 
          type="primary" 
          @click="startTest"
          :loading="testing"
          :disabled="!factor"
        >
          <el-icon><CaretRight /></el-icon>
          开始测试
        </el-button>
        
        <el-button @click="stopTest" :disabled="!testing">
          <el-icon><VideoPause /></el-icon>
          停止测试
        </el-button>
        
        <el-button @click="exportResults" :disabled="!testResults">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
      </div>
    </el-card>

    <!-- 测试进度 -->
    <div v-if="testing" class="test-progress">
      <el-card>
        <template #header>
          <span>测试进度</span>
        </template>
        
        <div class="progress-info">
          <el-progress 
            :percentage="testProgress.percentage" 
            :status="testProgress.status"
            :stroke-width="8"
          />
          <div class="progress-details">
            <span>{{ testProgress.currentStep }}</span>
            <span class="progress-time">预计剩余: {{ testProgress.estimatedTime }}</span>
          </div>
        </div>
        
        <div class="progress-logs">
          <el-scrollbar height="200px">
            <div 
              v-for="(log, index) in testLogs" 
              :key="index"
              class="log-item"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span :class="['log-level', log.level]">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </el-scrollbar>
        </div>
      </el-card>
    </div>

    <!-- 测试结果 -->
    <div v-if="testResults" class="test-results">
      <!-- 核心指标 -->
      <el-card class="metrics-card">
        <template #header>
          <span>核心指标</span>
        </template>
        
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-label">信息系数 (IC)</div>
            <div class="metric-value" :class="getICClass(testResults.ic)">
              {{ testResults.ic?.toFixed(4) }}
            </div>
            <div class="metric-desc">平均值，标准差: {{ testResults.icStd?.toFixed(4) }}</div>
          </div>
          
          <div class="metric-item">
            <div class="metric-label">信息比率 (IR)</div>
            <div class="metric-value" :class="getIRClass(testResults.ir)">
              {{ testResults.ir?.toFixed(4) }}
            </div>
            <div class="metric-desc">IC均值/IC标准差</div>
          </div>
          
          <div class="metric-item">
            <div class="metric-label">Rank IC</div>
            <div class="metric-value">{{ testResults.rankIC?.toFixed(4) }}</div>
            <div class="metric-desc">排序相关系数</div>
          </div>
          
          <div class="metric-item">
            <div class="metric-label">胜率</div>
            <div class="metric-value">{{ testResults.winRate?.toFixed(1) }}%</div>
            <div class="metric-desc">IC > 0 的比例</div>
          </div>
          
          <div class="metric-item">
            <div class="metric-label">年化收益</div>
            <div class="metric-value positive">+{{ testResults.annualReturn?.toFixed(2) }}%</div>
            <div class="metric-desc">多空组合年化收益</div>
          </div>
          
          <div class="metric-item">
            <div class="metric-label">最大回撤</div>
            <div class="metric-value negative">{{ testResults.maxDrawdown?.toFixed(2) }}%</div>
            <div class="metric-desc">历史最大回撤</div>
          </div>
        </div>
      </el-card>

      <!-- 分组回测结果 -->
      <el-card class="group-results-card">
        <template #header>
          <span>分组回测结果</span>
        </template>
        
        <el-table :data="testResults.groupResults" stripe>
          <el-table-column prop="group" label="分组" width="80" />
          <el-table-column prop="annualReturn" label="年化收益率" width="120">
            <template #default="{ row }">
              <span :class="row.annualReturn > 0 ? 'positive' : 'negative'">
                {{ row.annualReturn?.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="volatility" label="波动率" width="100">
            <template #default="{ row }">
              {{ row.volatility?.toFixed(2) }}%
            </template>
          </el-table-column>
          <el-table-column prop="sharpe" label="夏普比率" width="100">
            <template #default="{ row }">
              {{ row.sharpe?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="maxDrawdown" label="最大回撤" width="100">
            <template #default="{ row }">
              <span class="negative">{{ row.maxDrawdown?.toFixed(2) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="avgWeight" label="平均权重" width="100">
            <template #default="{ row }">
              {{ row.avgWeight?.toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 图表展示 -->
      <el-card class="charts-card">
        <template #header>
          <span>可视化分析</span>
        </template>
        
        <el-tabs v-model="activeChartTab">
          <el-tab-pane label="IC时序图" name="ic-timeseries">
            <div class="chart-container">
              <canvas ref="icChartRef" height="300"></canvas>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="分组收益" name="group-returns">
            <div class="chart-container">
              <canvas ref="groupChartRef" height="300"></canvas>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="累计收益" name="cumulative-returns">
            <div class="chart-container">
              <canvas ref="cumulativeChartRef" height="300"></canvas>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 总结与建议 -->
      <el-card class="summary-card">
        <template #header>
          <span>测试总结与建议</span>
        </template>
        
        <div class="summary-content">
          <div class="summary-section">
            <h4>因子质量评价</h4>
            <el-tag :type="getQualityTagType(testResults.quality)" size="large">
              {{ getQualityText(testResults.quality) }}
            </el-tag>
            <p>{{ getQualityDescription(testResults.quality) }}</p>
          </div>
          
          <div class="summary-section">
            <h4>优化建议</h4>
            <ul class="suggestions-list">
              <li v-for="suggestion in testResults.suggestions" :key="suggestion">
                {{ suggestion }}
              </li>
            </ul>
          </div>
          
          <div class="summary-section">
            <h4>适用场景</h4>
            <div class="scenarios">
              <el-tag 
                v-for="scenario in testResults.applicableScenarios" 
                :key="scenario" 
                type="info" 
                class="scenario-tag"
              >
                {{ scenario }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TestTube, CaretRight, VideoPause, Download
} from '@element-plus/icons-vue'
import type { FactorDefinition } from '@/types/factor'

// Props
const props = defineProps<{
  factor?: FactorDefinition | null
}>()

// 事件定义
const emit = defineEmits<{
  testComplete: [result: any]
  close: []
}>()

// 响应式数据
const testing = ref(false)
const activeChartTab = ref('ic-timeseries')

const testConfig = reactive({
  dateRange: ['2020-01-01', '2023-12-31'] as [string, string],
  stockPool: 'HS300',
  frequency: 'daily',
  benchmark: '000300.SH',
  groups: 10
})

const testProgress = ref({
  percentage: 0,
  status: 'normal' as const,
  currentStep: '准备开始测试...',
  estimatedTime: '--'
})

const testLogs = ref<Array<{
  timestamp: Date
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
}>>([])

const testResults = ref<any>(null)

// 图表引用
const icChartRef = ref<HTMLCanvasElement>()
const groupChartRef = ref<HTMLCanvasElement>()
const cumulativeChartRef = ref<HTMLCanvasElement>()

// 方法
const startTest = async () => {
  if (!props.factor) {
    ElMessage.warning('请先选择要测试的因子')
    return
  }

  testing.value = true
  testResults.value = null
  testLogs.value = []
  testProgress.value = {
    percentage: 0,
    status: 'normal',
    currentStep: '初始化测试环境...',
    estimatedTime: '预计5分钟'
  }

  try {
    await simulateFactorTest()
    ElMessage.success('因子测试完成')
    emit('testComplete', testResults.value)
  } catch (error) {
    ElMessage.error('因子测试失败')
    testProgress.value.status = 'exception'
  } finally {
    testing.value = false
  }
}

const simulateFactorTest = async () => {
  const steps = [
    { step: '加载历史数据...', duration: 1000, progress: 20 },
    { step: '计算因子值...', duration: 1500, progress: 40 },
    { step: '执行分组回测...', duration: 2000, progress: 60 },
    { step: '计算performance指标...', duration: 1000, progress: 80 },
    { step: '生成测试报告...', duration: 500, progress: 100 }
  ]

  for (const [index, { step, duration, progress }] of steps.entries()) {
    testProgress.value.currentStep = step
    testProgress.value.percentage = progress
    testProgress.value.estimatedTime = `预计剩余 ${steps.length - index - 1} 分钟`

    addLog('info', step)
    await new Promise(resolve => setTimeout(resolve, duration))
  }

  // 模拟测试结果
  testResults.value = {
    ic: 0.042,
    icStd: 0.156,
    ir: 0.269,
    rankIC: 0.038,
    winRate: 54.2,
    annualReturn: 8.5,
    maxDrawdown: -12.3,
    quality: 'good',
    groupResults: [
      { group: 'G1', annualReturn: 15.2, volatility: 18.5, sharpe: 0.82, maxDrawdown: -15.2, avgWeight: 10.0 },
      { group: 'G2', annualReturn: 12.8, volatility: 16.8, sharpe: 0.76, maxDrawdown: -13.5, avgWeight: 10.0 },
      { group: 'G3', annualReturn: 10.5, volatility: 15.9, sharpe: 0.66, maxDrawdown: -12.8, avgWeight: 10.0 },
      { group: 'G4', annualReturn: 8.2, volatility: 15.2, sharpe: 0.54, maxDrawdown: -11.9, avgWeight: 10.0 },
      { group: 'G5', annualReturn: 6.8, volatility: 14.8, sharpe: 0.46, maxDrawdown: -11.2, avgWeight: 10.0 }
    ],
    suggestions: [
      '因子IC值较为稳定，建议在组合中使用',
      '可以考虑与基本面因子结合，提高稳定性',
      '建议定期重新训练，保持因子有效性'
    ],
    applicableScenarios: ['中长期选股', '多因子模型', '量化组合']
  }

  addLog('success', '测试完成！因子表现良好')
}

const stopTest = () => {
  testing.value = false
  testProgress.value.currentStep = '测试已停止'
  addLog('warning', '测试被用户手动停止')
}

const exportResults = () => {
  if (!testResults.value) return

  const data = {
    factor: props.factor,
    testConfig: testConfig,
    results: testResults.value,
    timestamp: new Date()
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `factor_test_${props.factor?.name}_${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)

  ElMessage.success('测试结果已导出')
}

const addLog = (level: 'info' | 'warning' | 'error' | 'success', message: string) => {
  testLogs.value.push({
    timestamp: new Date(),
    level,
    message
  })
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN')
}

const getICClass = (ic: number) => {
  if (ic > 0.05) return 'excellent'
  if (ic > 0.03) return 'good'
  if (ic > 0.01) return 'fair'
  return 'poor'
}

const getIRClass = (ir: number) => {
  if (ir > 0.5) return 'excellent'
  if (ir > 0.3) return 'good'
  if (ir > 0.1) return 'fair'
  return 'poor'
}

const getQualityTagType = (quality: string) => {
  const types: Record<string, string> = {
    excellent: 'success',
    good: 'primary',
    fair: 'warning',
    poor: 'danger'
  }
  return types[quality] || 'info'
}

const getQualityText = (quality: string) => {
  const texts: Record<string, string> = {
    excellent: '优秀',
    good: '良好',
    fair: '一般',
    poor: '较差'
  }
  return texts[quality] || quality
}

const getQualityDescription = (quality: string) => {
  const descriptions: Record<string, string> = {
    excellent: '因子表现优秀，具有很强的预测能力，建议重点使用',
    good: '因子表现良好，可以作为主要因子使用',
    fair: '因子表现一般，可以作为辅助因子使用',
    poor: '因子表现较差，不建议使用或需要进一步优化'
  }
  return descriptions[quality] || ''
}

// 监听器
watch(() => props.factor, (newFactor) => {
  if (newFactor) {
    // 重置测试状态
    testResults.value = null
    testProgress.value.percentage = 0
  }
})

// 生命周期
onMounted(() => {
  // 初始化图表
})
</script>

<style scoped>
.factor-validation {
  padding: 24px;
}

.validation-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  color: #303133;
}

.validation-header p {
  margin: 0;
  color: #606266;
}

.test-config-card {
  margin: 24px 0;
}

.test-actions {
  margin-top: 16px;
  text-align: center;
}

.test-progress {
  margin: 24px 0;
}

.progress-info {
  margin-bottom: 16px;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.progress-time {
  color: #909399;
}

.progress-logs {
  margin-top: 16px;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 4px 0;
  font-size: 12px;
  font-family: 'Monaco', 'Consolas', monospace;
}

.log-time {
  color: #909399;
  min-width: 80px;
}

.log-level {
  min-width: 60px;
  font-weight: 500;
}

.log-level.info { color: #409eff; }
.log-level.success { color: #67c23a; }
.log-level.warning { color: #e6a23c; }
.log-level.error { color: #f56c6c; }

.log-message {
  color: #303133;
}

.test-results {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.metric-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.metric-value.excellent { color: #67c23a; }
.metric-value.good { color: #409eff; }
.metric-value.fair { color: #e6a23c; }
.metric-value.poor { color: #f56c6c; }
.metric-value.positive { color: #67c23a; }
.metric-value.negative { color: #f56c6c; }

.metric-desc {
  font-size: 11px;
  color: #909399;
}

.chart-container {
  height: 300px;
  padding: 16px 0;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.suggestions-list {
  margin: 0;
  padding-left: 20px;
}

.suggestions-list li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.scenarios {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scenario-tag {
  margin-bottom: 4px;
}

.positive { color: #67c23a; }
.negative { color: #f56c6c; }

@media (max-width: 768px) {
  .factor-validation {
    padding: 16px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  }
  
  .metric-item {
    padding: 12px;
  }
  
  .test-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}
</style>