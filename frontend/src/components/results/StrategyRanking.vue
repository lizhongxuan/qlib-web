<template>
  <div class="strategy-ranking">
    <!-- 排行榜头部控制 -->
    <div class="ranking-header">
      <div class="header-info">
        <h3 class="ranking-title">
          <el-icon><Trophy /></el-icon>
          策略性能排行榜
        </h3>
        <p class="ranking-subtitle">基于多维度指标的策略综合评分排名</p>
      </div>
      
      <div class="ranking-controls">
        <el-select v-model="sortBy" @change="handleSortChange" style="width: 150px; margin-right: 12px;">
          <el-option label="综合评分" value="score" />
          <el-option label="年化收益" value="return" />
          <el-option label="夏普比率" value="sharpe" />
          <el-option label="最大回撤" value="drawdown" />
          <el-option label="信息比率" value="information" />
        </el-select>
        
        <el-select v-model="timeRange" @change="handleTimeRangeChange" style="width: 120px; margin-right: 12px;">
          <el-option label="全部" value="all" />
          <el-option label="1年内" value="1y" />
          <el-option label="6个月" value="6m" />
          <el-option label="3个月" value="3m" />
        </el-select>
        
        <el-button @click="refreshRanking" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="ranking-stats">
      <div class="stat-item">
        <div class="stat-value">{{ strategies.length }}</div>
        <div class="stat-label">总策略数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value positive">{{ excellentCount }}</div>
        <div class="stat-label">优秀策略</div>
      </div>
      <div class="stat-item">
        <div class="stat-value info">{{ goodCount }}</div>
        <div class="stat-label">良好策略</div>
      </div>
      <div class="stat-item">
        <div class="stat-value warning">{{ averageCount }}</div>
        <div class="stat-label">一般策略</div>
      </div>
    </div>

    <!-- 排行榜表格 -->
    <el-card class="ranking-table-card">
      <el-table 
        :data="sortedStrategies" 
        v-loading="loading"
        row-key="id"
        class="ranking-table"
        @row-click="handleRowClick"
      >
        <!-- 排名列 -->
        <el-table-column label="排名" width="80" align="center">
          <template #default="{ $index }">
            <div class="rank-badge" :class="getRankClass($index)">
              <el-icon v-if="$index < 3" :class="getMedalIcon($index)"></el-icon>
              <span v-else>{{ $index + 1 }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 策略信息列 -->
        <el-table-column label="策略名称" min-width="200">
          <template #default="{ row }">
            <div class="strategy-info">
              <div class="strategy-name">
                {{ row.name }}
                <el-tag v-if="row.isNew" type="success" size="small">新</el-tag>
                <el-tag v-if="row.isHot" type="danger" size="small">热</el-tag>
              </div>
              <div class="strategy-meta">
                <span class="strategy-type">{{ row.type }}</span>
                <span class="strategy-date">{{ formatDate(row.createDate) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 综合评分列 -->
        <el-table-column label="综合评分" width="120" align="center" sortable>
          <template #default="{ row }">
            <div class="score-display">
              <div class="score-value" :class="getScoreClass(row.score)">
                {{ row.score.toFixed(1) }}
              </div>
              <el-rate 
                v-model="row.scoreStars" 
                disabled 
                show-score 
                text-color="#ff9900" 
                score-template="{value}"
                size="small"
              />
            </div>
          </template>
        </el-table-column>

        <!-- 年化收益列 -->
        <el-table-column label="年化收益" width="100" align="center" sortable prop="annualReturn">
          <template #default="{ row }">
            <span class="metric-value" :class="row.annualReturn >= 0 ? 'positive' : 'negative'">
              {{ formatPercent(row.annualReturn) }}
            </span>
          </template>
        </el-table-column>

        <!-- 夏普比率列 -->
        <el-table-column label="夏普比率" width="100" align="center" sortable prop="sharpeRatio">
          <template #default="{ row }">
            <span class="metric-value" :class="getSharpeClass(row.sharpeRatio)">
              {{ row.sharpeRatio.toFixed(2) }}
            </span>
          </template>
        </el-table-column>

        <!-- 最大回撤列 -->
        <el-table-column label="最大回撤" width="100" align="center" sortable prop="maxDrawdown">
          <template #default="{ row }">
            <span class="metric-value negative">
              {{ formatPercent(row.maxDrawdown) }}
            </span>
          </template>
        </el-table-column>

        <!-- 胜率列 -->
        <el-table-column label="胜率" width="100" align="center" sortable prop="winRate">
          <template #default="{ row }">
            <span class="metric-value" :class="getWinRateClass(row.winRate)">
              {{ formatPercent(row.winRate / 100) }}
            </span>
          </template>
        </el-table-column>

        <!-- 信息比率列 -->
        <el-table-column label="信息比率" width="100" align="center" sortable prop="informationRatio">
          <template #default="{ row }">
            <span class="metric-value" :class="getInformationRatioClass(row.informationRatio)">
              {{ row.informationRatio.toFixed(2) }}
            </span>
          </template>
        </el-table-column>

        <!-- 状态列 -->
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="small" type="primary" @click.stop="viewDetail(row)">
                详情
              </el-button>
              <el-button size="small" type="success" @click.stop="deployStrategy(row)" :disabled="row.status !== 'completed'">
                部署
              </el-button>
              <el-button size="small" @click.stop="compareStrategy(row)">
                对比
              </el-button>
              <el-dropdown @command="handleCommand" trigger="click">
                <el-button size="small" type="info">
                  更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="`clone-${row.id}`">克隆策略</el-dropdown-item>
                    <el-dropdown-item :command="`export-${row.id}`">导出数据</el-dropdown-item>
                    <el-dropdown-item :command="`share-${row.id}`">分享策略</el-dropdown-item>
                    <el-dropdown-item :command="`delete-${row.id}`" divided>删除策略</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分页 -->
    <div class="ranking-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalStrategies"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 策略详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="策略详细信息"
      direction="rtl"
      size="50%"
    >
      <div v-if="selectedStrategy" class="strategy-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="策略名称">{{ selectedStrategy.name }}</el-descriptions-item>
          <el-descriptions-item label="策略类型">{{ selectedStrategy.type }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedStrategy.createDate) }}</el-descriptions-item>
          <el-descriptions-item label="最后更新">{{ formatDate(selectedStrategy.updateDate) }}</el-descriptions-item>
          <el-descriptions-item label="股票池">{{ selectedStrategy.universe }}</el-descriptions-item>
          <el-descriptions-item label="调仓频率">{{ selectedStrategy.rebalanceFreq }}</el-descriptions-item>
          <el-descriptions-item label="回测开始">{{ selectedStrategy.backtest.startDate }}</el-descriptions-item>
          <el-descriptions-item label="回测结束">{{ selectedStrategy.backtest.endDate }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>性能指标</el-divider>
        
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-title">年化收益率</div>
            <div class="metric-value large positive">{{ formatPercent(selectedStrategy.annualReturn) }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-title">夏普比率</div>
            <div class="metric-value large">{{ selectedStrategy.sharpeRatio.toFixed(2) }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-title">最大回撤</div>
            <div class="metric-value large negative">{{ formatPercent(selectedStrategy.maxDrawdown) }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-title">胜率</div>
            <div class="metric-value large">{{ formatPercent(selectedStrategy.winRate / 100) }}</div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Trophy, Refresh, ArrowDown, 
  Star, Medal, FirstPlace, SecondPlace, ThirdPlace 
} from '@element-plus/icons-vue'

// 接口定义
interface Strategy {
  id: string
  name: string
  type: string
  createDate: string
  updateDate: string
  universe: string
  rebalanceFreq: string
  score: number
  scoreStars: number
  annualReturn: number
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  informationRatio: number
  status: 'running' | 'completed' | 'failed' | 'paused'
  isNew: boolean
  isHot: boolean
  backtest: {
    startDate: string
    endDate: string
  }
}

// 响应式数据
const loading = ref(false)
const sortBy = ref('score')
const timeRange = ref('all')
const currentPage = ref(1)
const pageSize = ref(20)
const detailDrawerVisible = ref(false)
const selectedStrategy = ref<Strategy | null>(null)

// 模拟策略数据
const strategies = ref<Strategy[]>([
  {
    id: 'strategy_1',
    name: 'LightGBM多因子策略v3.2',
    type: '机器学习策略',
    createDate: '2023-12-01',
    updateDate: '2023-12-15',
    universe: '沪深300',
    rebalanceFreq: '月频',
    score: 9.2,
    scoreStars: 5,
    annualReturn: 0.285,
    sharpeRatio: 1.45,
    maxDrawdown: -0.082,
    winRate: 62.5,
    informationRatio: 0.85,
    status: 'completed',
    isNew: false,
    isHot: true,
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    }
  },
  {
    id: 'strategy_2', 
    name: 'XGBoost量化选股v2.8',
    type: '机器学习策略',
    createDate: '2023-11-15',
    updateDate: '2023-12-10',
    universe: '中证500',
    rebalanceFreq: '周频',
    score: 8.7,
    scoreStars: 4,
    annualReturn: 0.231,
    sharpeRatio: 1.28,
    maxDrawdown: -0.095,
    winRate: 58.3,
    informationRatio: 0.72,
    status: 'completed',
    isNew: true,
    isHot: false,
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    }
  },
  {
    id: 'strategy_3',
    name: 'LSTM深度学习策略v1.5',
    type: '深度学习策略', 
    createDate: '2023-10-20',
    updateDate: '2023-12-08',
    universe: '全市场',
    rebalanceFreq: '日频',
    score: 8.3,
    scoreStars: 4,
    annualReturn: 0.198,
    sharpeRatio: 1.15,
    maxDrawdown: -0.125,
    winRate: 55.7,
    informationRatio: 0.68,
    status: 'running',
    isNew: false,
    isHot: false,
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    }
  },
  {
    id: 'strategy_4',
    name: '多空对冲策略v2.1',
    type: '对冲策略',
    createDate: '2023-09-12',
    updateDate: '2023-11-25',
    universe: '沪深300',
    rebalanceFreq: '日频',
    score: 7.8,
    scoreStars: 4,
    annualReturn: 0.156,
    sharpeRatio: 1.02,
    maxDrawdown: -0.065,
    winRate: 52.8,
    informationRatio: 0.58,
    status: 'completed',
    isNew: false,
    isHot: false,
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    }
  },
  {
    id: 'strategy_5',
    name: '动量反转混合策略v1.8',
    type: '技术策略',
    createDate: '2023-08-28',
    updateDate: '2023-11-20',
    universe: '中证1000',
    rebalanceFreq: '月频',
    score: 7.3,
    scoreStars: 3,
    annualReturn: 0.142,
    sharpeRatio: 0.95,
    maxDrawdown: -0.108,
    winRate: 49.6,
    informationRatio: 0.51,
    status: 'completed',
    isNew: false,
    isHot: false,
    backtest: {
      startDate: '2022-01-01',
      endDate: '2023-12-31'
    }
  }
])

// 计算属性
const sortedStrategies = computed(() => {
  let sorted = [...strategies.value]
  
  // 根据选择的排序字段排序
  switch (sortBy.value) {
    case 'score':
      sorted.sort((a, b) => b.score - a.score)
      break
    case 'return':
      sorted.sort((a, b) => b.annualReturn - a.annualReturn)
      break
    case 'sharpe':
      sorted.sort((a, b) => b.sharpeRatio - a.sharpeRatio)
      break
    case 'drawdown':
      sorted.sort((a, b) => a.maxDrawdown - b.maxDrawdown) // 回撤越小越好
      break
    case 'information':
      sorted.sort((a, b) => b.informationRatio - a.informationRatio)
      break
  }
  
  return sorted
})

const totalStrategies = computed(() => strategies.value.length)

const excellentCount = computed(() => 
  strategies.value.filter(s => s.score >= 8.5).length
)

const goodCount = computed(() => 
  strategies.value.filter(s => s.score >= 7.0 && s.score < 8.5).length
)

const averageCount = computed(() => 
  strategies.value.filter(s => s.score < 7.0).length
)

// 方法
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getRankClass = (index: number) => {
  if (index === 0) return 'rank-first'
  if (index === 1) return 'rank-second' 
  if (index === 2) return 'rank-third'
  return 'rank-normal'
}

const getMedalIcon = (index: number) => {
  if (index === 0) return FirstPlace
  if (index === 1) return SecondPlace
  if (index === 2) return ThirdPlace
  return Star
}

const getScoreClass = (score: number) => {
  if (score >= 9.0) return 'score-excellent'
  if (score >= 8.0) return 'score-good'
  if (score >= 7.0) return 'score-average'
  return 'score-poor'
}

const getSharpeClass = (sharpe: number) => {
  if (sharpe >= 1.5) return 'positive'
  if (sharpe >= 1.0) return 'info'
  return 'warning'
}

const getWinRateClass = (winRate: number) => {
  if (winRate >= 60) return 'positive'
  if (winRate >= 50) return 'info'
  return 'warning'
}

const getInformationRatioClass = (ir: number) => {
  if (ir >= 0.8) return 'positive'
  if (ir >= 0.5) return 'info'
  return 'warning'
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'primary'
    case 'failed': return 'danger'
    case 'paused': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '运行中'
    case 'failed': return '失败'
    case 'paused': return '暂停'
    default: return '未知'
  }
}

const handleSortChange = () => {
  ElMessage.info(`按${sortBy.value}排序`)
}

const handleTimeRangeChange = () => {
  ElMessage.info(`时间范围已切换为${timeRange.value}`)
}

const refreshRanking = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('排行榜已刷新')
  }, 1000)
}

const handleRowClick = (row: Strategy) => {
  selectedStrategy.value = row
  detailDrawerVisible.value = true
}

const viewDetail = (row: Strategy) => {
  selectedStrategy.value = row
  detailDrawerVisible.value = true
}

const deployStrategy = (row: Strategy) => {
  ElMessage.success(`开始部署策略: ${row.name}`)
}

const compareStrategy = (row: Strategy) => {
  ElMessage.info(`添加策略 ${row.name} 到对比列表`)
}

const handleCommand = (command: string) => {
  const [action, id] = command.split('-')
  const strategy = strategies.value.find(s => s.id === id)
  
  if (!strategy) return
  
  switch (action) {
    case 'clone':
      ElMessage.success(`克隆策略: ${strategy.name}`)
      break
    case 'export':
      ElMessage.success(`导出策略: ${strategy.name}`)
      break
    case 'share':
      ElMessage.success(`分享策略: ${strategy.name}`)
      break
    case 'delete':
      ElMessageBox.confirm(
        `确定要删除策略 "${strategy.name}" 吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(() => {
        ElMessage.success('删除成功')
      }).catch(() => {
        ElMessage.info('已取消删除')
      })
      break
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 暴露给父组件的方法
defineExpose({
  refreshRanking,
  getTopStrategies: () => sortedStrategies.value.slice(0, 10)
})

onMounted(() => {
  // 初始化加载数据
})
</script>

<style scoped>
.strategy-ranking {
  width: 100%;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 0 8px;
}

.header-info {
  flex: 1;
}

.ranking-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.ranking-subtitle {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.ranking-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ranking-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-value.positive {
  color: #67c23a;
}

.stat-value.info {
  color: #409eff;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.ranking-table-card {
  margin-bottom: 24px;
}

.ranking-table {
  width: 100%;
}

.rank-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  margin: 0 auto;
}

.rank-badge.rank-first {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  color: #d48806;
}

.rank-badge.rank-second {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #595959;
}

.rank-badge.rank-third {
  background: linear-gradient(135deg, #cd7f32, #daa520);
  color: #8b4513;
}

.rank-badge.rank-normal {
  background: #f5f7fa;
  color: #909399;
}

.strategy-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strategy-name {
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.score-value {
  font-size: 18px;
  font-weight: 600;
}

.score-value.score-excellent {
  color: #67c23a;
}

.score-value.score-good {
  color: #409eff;
}

.score-value.score-average {
  color: #e6a23c;
}

.score-value.score-poor {
  color: #f56c6c;
}

.metric-value {
  font-weight: 600;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-value.info {
  color: #409eff;
}

.metric-value.warning {
  color: #e6a23c;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.ranking-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.strategy-detail {
  padding: 0 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.metric-card {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.metric-value.large {
  font-size: 20px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .ranking-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .ranking-controls {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .ranking-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>