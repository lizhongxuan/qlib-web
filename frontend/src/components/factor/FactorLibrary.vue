<template>
  <div class="factor-library">
    <!-- 库头部操作 -->
    <div class="library-header">
      <div class="header-left">
        <h3>
          <el-icon><Collection /></el-icon>
          因子库管理
        </h3>
        <el-tag type="info">共 {{ factors.length }} 个因子</el-tag>
      </div>
      
      <div class="header-actions">
        <el-input
          v-model="searchText"
          placeholder="搜索因子名称或表达式..."
          class="search-input"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="categoryFilter" placeholder="筛选类型" clearable>
          <el-option label="全部类型" value="" />
          <el-option label="技术指标" value="technical" />
          <el-option label="基本面" value="fundamental" />
          <el-option label="情绪指标" value="sentiment" />
          <el-option label="组合因子" value="composite" />
        </el-select>
        
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建因子
        </el-button>
      </div>
    </div>

    <!-- 因子列表 -->
    <div class="factors-grid">
      <div 
        v-for="factor in filteredFactors" 
        :key="factor.id"
        class="factor-card"
        :class="{ selected: selectedFactors.includes(factor.id) }"
        @click="toggleFactorSelection(factor.id)"
      >
        <div class="factor-card-header">
          <div class="factor-info">
            <h4 class="factor-name">{{ factor.name }}</h4>
            <el-tag 
              :type="getCategoryTagType(factor.category)" 
              size="small"
            >
              {{ getCategoryName(factor.category) }}
            </el-tag>
          </div>
          
          <div class="factor-actions">
            <el-dropdown @command="handleFactorAction">
              <el-button type="text" size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`edit_${factor.id}`">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-dropdown-item>
                  <el-dropdown-item :command="`test_${factor.id}`">
                    <el-icon><View /></el-icon>
                    测试
                  </el-dropdown-item>
                  <el-dropdown-item :command="`copy_${factor.id}`">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-dropdown-item>
                  <el-dropdown-item :command="`export_${factor.id}`">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-dropdown-item>
                  <el-dropdown-item :command="`delete_${factor.id}`" divided>
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <div class="factor-expression">
          <code>{{ factor.expression }}</code>
        </div>
        
        <div class="factor-description">
          {{ factor.description }}
        </div>
        
        <div v-if="factor.performance" class="factor-metrics">
          <div class="metric">
            <span class="metric-label">IC值:</span>
            <span class="metric-value">{{ factor.performance.ic?.toFixed(3) }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">IR值:</span>
            <span class="metric-value">{{ factor.performance.ir?.toFixed(3) }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">胜率:</span>
            <span class="metric-value">{{ factor.performance.winRate?.toFixed(1) }}%</span>
          </div>
        </div>
        
        <div class="factor-footer">
          <div class="factor-meta">
            <span class="created-by">{{ factor.createdBy }}</span>
            <span class="created-at">{{ formatDate(factor.createdAt) }}</span>
          </div>
          
          <div class="factor-status">
            <el-tag 
              :type="getStatusTagType(factor.status)" 
              size="small"
            >
              {{ getStatusText(factor.status) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedFactors.length > 0" class="batch-actions">
      <div class="batch-info">
        已选择 {{ selectedFactors.length }} 个因子
      </div>
      <div class="batch-buttons">
        <el-button @click="batchTest">
          <el-icon><View /></el-icon>
          批量测试
        </el-button>
        <el-button @click="batchExport">
          <el-icon><Download /></el-icon>
          批量导出
        </el-button>
        <el-button @click="useSelectedFactors" type="primary">
          <el-icon><Right /></el-icon>
          使用选中因子
        </el-button>
        <el-button @click="clearSelection">
          清除选择
        </el-button>
      </div>
    </div>

    <!-- 创建因子对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建因子" width="600px">
      <FactorEditor 
        @save="handleFactorSaved"
        @cancel="showCreateDialog = false"
      />
    </el-dialog>

    <!-- 因子测试对话框 -->
    <el-dialog v-model="showTestDialog" title="因子测试" width="800px">
      <FactorValidation 
        :factor="testingFactor"
        @close="showTestDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Collection, Search, Plus, MoreFilled, Edit, View, 
  CopyDocument, Download, Delete, Right
} from '@element-plus/icons-vue'
import FactorEditor from './FactorEditor.vue'
import FactorValidation from './FactorValidation.vue'
import type { FactorDefinition } from '@/types/factor'

// 事件定义
const emit = defineEmits<{
  editFactor: [factor: FactorDefinition]
  testFactor: [factor: FactorDefinition]
  useFactor: [factors: FactorDefinition[]]
}>()

// 响应式数据
const searchText = ref('')
const categoryFilter = ref('')
const selectedFactors = ref<string[]>([])
const showCreateDialog = ref(false)
const showTestDialog = ref(false)
const testingFactor = ref<FactorDefinition | null>(null)

const factors = ref<FactorDefinition[]>([
  {
    id: 'momentum_20d',
    name: '20日动量因子',
    expression: '($close / Ref($close, 20)) - 1',
    description: '计算过去20个交易日的累计收益率，用于捕捉价格动量效应',
    category: 'technical',
    status: 'active',
    performance: {
      ic: 0.045,
      ir: 1.25,
      winRate: 58.7
    },
    createdBy: 'AI Assistant',
    createdAt: new Date('2024-08-01')
  },
  {
    id: 'pe_inverse',
    name: '市盈率倒数因子',
    expression: '1 / $pe_ttm',
    description: '市盈率的倒数，数值越大表示估值越便宜',
    category: 'fundamental',
    status: 'active',
    performance: {
      ic: 0.062,
      ir: 0.95,
      winRate: 55.2
    },
    createdBy: 'Manual Editor',
    createdAt: new Date('2024-07-28')
  },
  {
    id: 'volume_strength',
    name: '成交量相对强度',
    expression: '$volume / Mean($volume, 20)',
    description: '当日成交量与过去20日平均成交量的比值',
    category: 'technical',
    status: 'testing',
    performance: {
      ic: 0.028,
      ir: 1.15,
      winRate: 52.1
    },
    createdBy: 'AI Assistant',
    createdAt: new Date('2024-08-05')
  },
  {
    id: 'rsi_factor',
    name: 'RSI技术指标',
    expression: 'RSI($close, 14)',
    description: '相对强弱指数，衡量股价超买超卖程度',
    category: 'technical',
    status: 'deprecated',
    performance: {
      ic: 0.015,
      ir: 0.85,
      winRate: 48.3
    },
    createdBy: 'Manual Editor',
    createdAt: new Date('2024-07-15')
  }
])

// 计算属性
const filteredFactors = computed(() => {
  let filtered = factors.value

  // 文本搜索
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(factor =>
      factor.name.toLowerCase().includes(search) ||
      factor.expression.toLowerCase().includes(search) ||
      factor.description.toLowerCase().includes(search)
    )
  }

  // 类型筛选
  if (categoryFilter.value) {
    filtered = filtered.filter(factor => factor.category === categoryFilter.value)
  }

  return filtered.sort((a, b) => {
    // 按状态和创建时间排序
    if (a.status === 'active' && b.status !== 'active') return -1
    if (b.status === 'active' && a.status !== 'active') return 1
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  })
})

// 方法
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    technical: '技术指标',
    fundamental: '基本面',
    sentiment: '情绪指标',
    composite: '组合因子',
    other: '其他'
  }
  return names[category] || category
}

const getCategoryTagType = (category: string) => {
  const types: Record<string, string> = {
    technical: 'primary',
    fundamental: 'success',
    sentiment: 'warning',
    composite: 'info',
    other: 'default'
  }
  return types[category] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    active: '活跃',
    testing: '测试中',
    deprecated: '已废弃',
    draft: '草稿'
  }
  return texts[status] || status
}

const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    active: 'success',
    testing: 'warning',
    deprecated: 'danger',
    draft: 'info'
  }
  return types[status] || 'default'
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const toggleFactorSelection = (factorId: string) => {
  const index = selectedFactors.value.indexOf(factorId)
  if (index > -1) {
    selectedFactors.value.splice(index, 1)
  } else {
    selectedFactors.value.push(factorId)
  }
}

const handleFactorAction = (command: string) => {
  const [action, factorId] = command.split('_')
  const factor = factors.value.find(f => f.id === factorId)
  
  if (!factor) return

  switch (action) {
    case 'edit':
      emit('editFactor', factor)
      break
    case 'test':
      testingFactor.value = factor
      showTestDialog.value = true
      break
    case 'copy':
      copyFactor(factor)
      break
    case 'export':
      exportFactor(factor)
      break
    case 'delete':
      deleteFactor(factor)
      break
  }
}

const copyFactor = (factor: FactorDefinition) => {
  navigator.clipboard.writeText(factor.expression)
  ElMessage.success('因子表达式已复制到剪贴板')
}

const exportFactor = (factor: FactorDefinition) => {
  const data = JSON.stringify(factor, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${factor.name}.json`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('因子已导出')
}

const deleteFactor = async (factor: FactorDefinition) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除因子 "${factor.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = factors.value.findIndex(f => f.id === factor.id)
    if (index > -1) {
      factors.value.splice(index, 1)
      ElMessage.success('因子已删除')
    }
  } catch {
    // 用户取消删除
  }
}

const batchTest = () => {
  const selectedFactorObjects = factors.value.filter(f => 
    selectedFactors.value.includes(f.id)
  )
  
  ElMessage.info(`开始批量测试 ${selectedFactorObjects.length} 个因子`)
  // 这里可以实现批量测试逻辑
}

const batchExport = () => {
  const selectedFactorObjects = factors.value.filter(f => 
    selectedFactors.value.includes(f.id)
  )
  
  const data = JSON.stringify(selectedFactorObjects, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `factors_batch_export.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success(`已导出 ${selectedFactorObjects.length} 个因子`)
}

const useSelectedFactors = () => {
  const selectedFactorObjects = factors.value.filter(f => 
    selectedFactors.value.includes(f.id)
  )
  
  emit('useFactor', selectedFactorObjects)
  ElMessage.success(`已选择 ${selectedFactorObjects.length} 个因子用于后续操作`)
}

const clearSelection = () => {
  selectedFactors.value = []
}

const handleFactorSaved = (factor: FactorDefinition) => {
  factors.value.unshift(factor)
  showCreateDialog.value = false
  ElMessage.success('因子创建成功')
}

// 生命周期
onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.factor-library {
  padding: 24px;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.factors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.factor-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.factor-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.factor-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.factor-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.factor-info {
  flex: 1;
}

.factor-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.factor-expression {
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.factor-expression code {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  color: #e6a23c;
  word-break: break-all;
}

.factor-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
}

.factor-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.metric {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-weight: 500;
  color: #303133;
}

.factor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.factor-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.created-by {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.created-at {
  font-size: 12px;
  color: #909399;
}

.batch-actions {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 1000;
}

.batch-info {
  font-weight: 500;
  color: #303133;
}

.batch-buttons {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .factor-library {
    padding: 16px;
  }
  
  .library-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .search-input {
    width: 100%;
  }
  
  .factors-grid {
    grid-template-columns: 1fr;
  }
  
  .factor-metrics {
    grid-template-columns: 1fr;
  }
  
  .batch-actions {
    flex-direction: column;
    width: calc(100% - 32px);
    left: 16px;
    transform: none;
  }
  
  .batch-buttons {
    width: 100%;
    justify-content: space-around;
  }
}
</style>