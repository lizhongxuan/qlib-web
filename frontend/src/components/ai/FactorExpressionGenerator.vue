<template>
  <div class="factor-generator">
    <!-- 生成器头部 -->
    <div class="generator-header">
      <el-icon class="header-icon"><MagicStick /></el-icon>
      <div class="header-text">
        <h3>因子表达式生成器</h3>
        <p>通过可视化配置或自然语言描述生成量化因子表达式</p>
      </div>
    </div>

    <!-- 生成方式选择 -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- 可视化生成 -->
      <el-tab-pane label="可视化生成" name="visual">
        <div class="visual-generator">
          <!-- 因子类型选择 -->
          <el-card class="config-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Category /></el-icon>
                <span>因子类型</span>
              </div>
            </template>

            <div class="factor-types">
              <div 
                v-for="type in factorTypes" 
                :key="type.value"
                class="factor-type-item"
                :class="{ active: selectedFactorType === type.value }"
                @click="selectFactorType(type.value)"
              >
                <el-icon><component :is="type.icon" /></el-icon>
                <div class="type-content">
                  <h4>{{ type.label }}</h4>
                  <p>{{ type.description }}</p>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 数据源配置 -->
          <el-card class="config-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Database /></el-icon>
                <span>数据源配置</span>
              </div>
            </template>

            <div class="data-config">
              <div class="config-row">
                <label>主要数据</label>
                <el-select 
                  v-model="dataConfig.primaryData" 
                  multiple 
                  placeholder="选择主要数据字段"
                  @change="updateExpression"
                >
                  <el-option 
                    v-for="field in dataFields" 
                    :key="field.value"
                    :label="field.label" 
                    :value="field.value"
                  >
                    <span style="float: left">{{ field.label }}</span>
                    <span style="float: right; color: #8492a6; font-size: 13px">{{ field.value }}</span>
                  </el-option>
                </el-select>
              </div>

              <div class="config-row">
                <label>辅助数据</label>
                <el-select 
                  v-model="dataConfig.auxiliaryData" 
                  multiple 
                  placeholder="选择辅助数据字段"
                  @change="updateExpression"
                >
                  <el-option 
                    v-for="field in auxiliaryFields" 
                    :key="field.value"
                    :label="field.label" 
                    :value="field.value"
                  />
                </el-select>
              </div>

              <div class="config-row">
                <label>时间窗口</label>
                <div class="time-config">
                  <el-input-number 
                    v-model="dataConfig.timeWindow" 
                    :min="1" 
                    :max="252" 
                    @change="updateExpression"
                  />
                  <el-select v-model="dataConfig.timeUnit" @change="updateExpression">
                    <el-option label="天" value="day" />
                    <el-option label="周" value="week" />
                    <el-option label="月" value="month" />
                  </el-select>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 计算配置 -->
          <el-card class="config-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Calculator /></el-icon>
                <span>计算配置</span>
              </div>
            </template>

            <div class="calculation-config">
              <div class="config-section">
                <h4>基础运算</h4>
                <div class="operation-buttons">
                  <el-button 
                    v-for="op in basicOperations" 
                    :key="op.value"
                    size="small"
                    @click="addOperation(op.value)"
                    :title="op.description"
                  >
                    {{ op.label }}
                  </el-button>
                </div>
              </div>

              <div class="config-section">
                <h4>时序函数</h4>
                <div class="function-buttons">
                  <el-button 
                    v-for="func in timeSeriesFunctions" 
                    :key="func.value"
                    size="small"
                    type="primary"
                    plain
                    @click="addFunction(func.value)"
                    :title="func.description"
                  >
                    {{ func.label }}
                  </el-button>
                </div>
              </div>

              <div class="config-section">
                <h4>统计函数</h4>
                <div class="function-buttons">
                  <el-button 
                    v-for="func in statisticalFunctions" 
                    :key="func.value"
                    size="small"
                    type="success"
                    plain
                    @click="addFunction(func.value)"
                    :title="func.description"
                  >
                    {{ func.label }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 表达式构建区 -->
          <el-card class="expression-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><EditPen /></el-icon>
                <span>表达式构建</span>
                <div class="header-actions">
                  <el-button size="small" @click="clearExpression">清空</el-button>
                  <el-button size="small" type="primary" @click="validateExpression">验证</el-button>
                </div>
              </div>
            </template>

            <div class="expression-builder">
              <!-- 表达式编辑器 -->
              <div class="expression-editor">
                <el-input 
                  v-model="generatedExpression"
                  type="textarea"
                  :rows="4"
                  placeholder="在此构建因子表达式，或使用上方配置自动生成..."
                  @input="handleExpressionChange"
                />
                
                <!-- 语法提示 -->
                <div v-if="syntaxErrors.length > 0" class="syntax-errors">
                  <div v-for="error in syntaxErrors" :key="error" class="error-item">
                    <el-icon><WarningFilled /></el-icon>
                    <span>{{ error }}</span>
                  </div>
                </div>

                <!-- 语法建议 -->
                <div v-if="syntaxSuggestions.length > 0" class="syntax-suggestions">
                  <div class="suggestions-header">语法建议：</div>
                  <div class="suggestions-list">
                    <el-tag 
                      v-for="suggestion in syntaxSuggestions" 
                      :key="suggestion"
                      size="small"
                      type="info"
                      class="suggestion-tag"
                      @click="applySuggestion(suggestion)"
                    >
                      {{ suggestion }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- 表达式预览 -->
              <div class="expression-preview">
                <div class="preview-header">
                  <span>表达式预览</span>
                  <el-switch 
                    v-model="showFormatted"
                    active-text="格式化显示"
                    size="small"
                  />
                </div>
                <div class="preview-content">
                  <code v-if="showFormatted" class="formatted-expression">
                    {{ formatExpression(generatedExpression) }}
                  </code>
                  <code v-else class="raw-expression">
                    {{ generatedExpression || '暂无表达式' }}
                  </code>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 自然语言生成 -->
      <el-tab-pane label="自然语言生成" name="natural">
        <div class="natural-generator">
          <el-card class="input-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><ChatDotRound /></el-icon>
                <span>描述您的投资想法</span>
              </div>
            </template>

            <div class="natural-input">
              <el-input 
                v-model="naturalLanguageInput"
                type="textarea"
                :rows="6"
                placeholder="请用自然语言描述您想要的因子，例如：&#10;- 我想要一个反映股票动量的因子，关注最近20天的价格变化&#10;- 创建一个基于成交量的因子，识别异常放量的股票&#10;- 设计一个价值因子，结合市盈率和市净率指标&#10;- 生成一个技术指标因子，使用RSI和MACD"
                @input="handleNaturalInputChange"
              />

              <div class="input-actions">
                <div class="quick-templates">
                  <span class="templates-label">快速模板：</span>
                  <el-button 
                    v-for="template in naturalTemplates" 
                    :key="template.label"
                    size="small" 
                    type="primary" 
                    link
                    @click="fillNaturalTemplate(template.content)"
                  >
                    {{ template.label }}
                  </el-button>
                </div>
                
                <el-button 
                  type="primary" 
                  @click="generateFromNatural"
                  :loading="isGenerating"
                  :disabled="!naturalLanguageInput.trim()"
                >
                  <el-icon><MagicStick /></el-icon>
                  生成因子表达式
                </el-button>
              </div>
            </div>
          </el-card>

          <!-- 生成结果 -->
          <el-card v-if="naturalGenerationResult" class="result-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><Trophy /></el-icon>
                <span>生成结果</span>
                <el-rate v-model="resultRating" size="small" />
              </div>
            </template>

            <div class="generation-result">
              <div class="result-expression">
                <div class="expression-label">生成的表达式：</div>
                <code class="expression-code">{{ naturalGenerationResult.expression }}</code>
                <el-button 
                  size="small" 
                  @click="copyExpression(naturalGenerationResult.expression)"
                >
                  复制
                </el-button>
              </div>

              <div class="result-explanation">
                <div class="explanation-label">表达式解释：</div>
                <p class="explanation-text">{{ naturalGenerationResult.explanation }}</p>
              </div>

              <div class="result-suggestions">
                <div class="suggestions-label">优化建议：</div>
                <ul class="suggestions-list">
                  <li v-for="suggestion in naturalGenerationResult.suggestions" :key="suggestion">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>

              <div class="result-actions">
                <el-button type="success" @click="acceptGeneration">
                  <el-icon><Check /></el-icon>
                  接受此表达式
                </el-button>
                <el-button @click="refineGeneration">
                  <el-icon><Refresh /></el-icon>
                  优化表达式
                </el-button>
                <el-button @click="regenerate">
                  <el-icon><MagicStick /></el-icon>
                  重新生成
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 模板库 -->
      <el-tab-pane label="模板库" name="templates">
        <div class="template-library">
          <!-- 模板分类 -->
          <div class="template-categories">
            <el-button 
              v-for="category in templateCategories" 
              :key="category.value"
              :type="selectedCategory === category.value ? 'primary' : 'default'"
              @click="selectCategory(category.value)"
            >
              {{ category.label }} ({{ category.count }})
            </el-button>
          </div>

          <!-- 模板列表 -->
          <div class="templates-grid">
            <div 
              v-for="template in filteredTemplates" 
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-header">
                <h4>{{ template.name }}</h4>
                <div class="template-meta">
                  <el-tag :type="getTemplateTypeColor(template.type)" size="small">
                    {{ template.type }}
                  </el-tag>
                  <el-rate v-model="template.rating" disabled size="small" />
                </div>
              </div>

              <div class="template-description">
                <p>{{ template.description }}</p>
              </div>

              <div class="template-expression">
                <code>{{ template.expression }}</code>
              </div>

              <div class="template-stats">
                <div class="stat-item">
                  <span class="stat-label">使用次数</span>
                  <span class="stat-value">{{ template.usageCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">平均IC</span>
                  <span class="stat-value">{{ template.avgIC }}</span>
                </div>
              </div>

              <div class="template-actions">
                <el-button size="small" type="primary" @click.stop="useTemplate(template)">
                  使用模板
                </el-button>
                <el-button size="small" @click.stop="previewTemplate(template)">
                  预览效果
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 生成结果面板 -->
    <div v-if="finalExpression" class="result-panel">
      <el-card shadow="always">
        <template #header>
          <div class="result-header">
            <el-icon><Trophy /></el-icon>
            <span>生成完成</span>
            <div class="result-actions">
              <el-button size="small" @click="saveToLibrary">保存到因子库</el-button>
              <el-button size="small" type="primary" @click="useForTraining">用于模型训练</el-button>
            </div>
          </div>
        </template>

        <div class="final-result">
          <div class="expression-display">
            <label>最终表达式：</label>
            <code class="final-expression">{{ finalExpression }}</code>
          </div>
          
          <div class="expression-info">
            <div class="info-item">
              <span class="info-label">因子类型：</span>
              <span class="info-value">{{ expressionInfo.type }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">复杂度：</span>
              <span class="info-value">{{ expressionInfo.complexity }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">预期有效性：</span>
              <el-progress 
                :percentage="expressionInfo.effectiveness" 
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick,
  Category,
  Database,
  Calculator,
  EditPen,
  WarningFilled,
  ChatDotRound,
  Trophy,
  Check,
  Refresh,
  TrendCharts,
  DataAnalysis,
  Histogram,
  Timer
} from '@element-plus/icons-vue'

// 接口定义
interface FactorType {
  value: string
  label: string
  description: string
  icon: string
}

interface DataField {
  value: string
  label: string
  type: 'price' | 'volume' | 'fundamental' | 'technical'
}

interface Operation {
  value: string
  label: string
  description: string
}

interface NaturalTemplate {
  label: string
  content: string
}

interface GenerationResult {
  expression: string
  explanation: string
  suggestions: string[]
}

interface FactorTemplate {
  id: string
  name: string
  type: string
  description: string
  expression: string
  rating: number
  usageCount: number
  avgIC: number
}

// 响应式数据
const activeTab = ref('visual')
const selectedFactorType = ref('')
const showFormatted = ref(true)
const naturalLanguageInput = ref('')
const isGenerating = ref(false)
const naturalGenerationResult = ref<GenerationResult | null>(null)
const resultRating = ref(0)
const selectedCategory = ref('all')
const generatedExpression = ref('')
const finalExpression = ref('')
const syntaxErrors = ref<string[]>([])
const syntaxSuggestions = ref<string[]>([])

// 数据配置
const dataConfig = reactive({
  primaryData: [] as string[],
  auxiliaryData: [] as string[],
  timeWindow: 20,
  timeUnit: 'day'
})

// 表达式信息
const expressionInfo = reactive({
  type: '',
  complexity: '',
  effectiveness: 0
})

// 因子类型
const factorTypes: FactorType[] = [
  {
    value: 'momentum',
    label: '动量因子',
    description: '捕捉股票价格趋势和惯性效应',
    icon: 'TrendCharts'
  },
  {
    value: 'value',
    label: '价值因子',
    description: '基于基本面指标识别被低估股票',
    icon: 'DataAnalysis'
  },
  {
    value: 'quality',
    label: '质量因子',
    description: '评估公司的盈利能力和财务健康度',
    icon: 'Trophy'
  },
  {
    value: 'volatility',
    label: '波动率因子',
    description: '度量股票价格的波动特征',
    icon: 'Histogram'
  },
  {
    value: 'technical',
    label: '技术指标',
    description: '基于技术分析的经典指标',
    icon: 'Timer'
  }
]

// 数据字段
const dataFields: DataField[] = [
  { value: '$close', label: '收盘价', type: 'price' },
  { value: '$open', label: '开盘价', type: 'price' },
  { value: '$high', label: '最高价', type: 'price' },
  { value: '$low', label: '最低价', type: 'price' },
  { value: '$volume', label: '成交量', type: 'volume' },
  { value: '$amount', label: '成交额', type: 'volume' }
]

const auxiliaryFields: DataField[] = [
  { value: '$pe_ratio', label: '市盈率', type: 'fundamental' },
  { value: '$pb_ratio', label: '市净率', type: 'fundamental' },
  { value: '$roe', label: '净资产收益率', type: 'fundamental' },
  { value: '$roa', label: '总资产回报率', type: 'fundamental' }
]

// 基础运算
const basicOperations: Operation[] = [
  { value: '+', label: '+', description: '加法' },
  { value: '-', label: '-', description: '减法' },
  { value: '*', label: '×', description: '乘法' },
  { value: '/', label: '÷', description: '除法' },
  { value: '()', label: '( )', description: '括号' }
]

// 时序函数
const timeSeriesFunctions: Operation[] = [
  { value: 'MA', label: 'MA', description: '移动平均' },
  { value: 'Ref', label: 'Ref', description: '引用历史值' },
  { value: 'Delay', label: 'Delay', description: '延迟函数' },
  { value: 'Delta', label: 'Delta', description: '差分函数' },
  { value: 'Ts_Rank', label: 'Ts_Rank', description: '时序排序' }
]

// 统计函数
const statisticalFunctions: Operation[] = [
  { value: 'STD', label: 'STD', description: '标准差' },
  { value: 'MAX', label: 'MAX', description: '最大值' },
  { value: 'MIN', label: 'MIN', description: '最小值' },
  { value: 'CORR', label: 'CORR', description: '相关系数' },
  { value: 'Rank', label: 'Rank', description: '排序函数' }
]

// 自然语言模板
const naturalTemplates: NaturalTemplate[] = [
  {
    label: '动量因子',
    content: '我想要一个反映股票动量的因子，关注最近20天的价格趋势'
  },
  {
    label: '价值因子',
    content: '创建一个价值投资因子，基于市盈率和市净率指标'
  },
  {
    label: '成交量因子',
    content: '设计一个基于成交量异动的因子，识别资金流入的股票'
  },
  {
    label: '技术指标',
    content: '生成一个技术指标因子，结合RSI和MACD等经典指标'
  }
]

// 模板分类
const templateCategories = [
  { value: 'all', label: '全部', count: 24 },
  { value: 'momentum', label: '动量', count: 8 },
  { value: 'value', label: '价值', count: 6 },
  { value: 'quality', label: '质量', count: 5 },
  { value: 'technical', label: '技术', count: 5 }
]

// 因子模板
const factorTemplates: FactorTemplate[] = [
  {
    id: 'template_1',
    name: '20日动量因子',
    type: 'momentum',
    description: '基于20日价格变化的动量因子',
    expression: '($close / Ref($close, 20)) - 1',
    rating: 4.5,
    usageCount: 156,
    avgIC: 0.068
  },
  {
    id: 'template_2',
    name: 'PE-PB综合价值因子',
    type: 'value',
    description: '结合市盈率和市净率的价值因子',
    expression: '1 / ($pe_ratio * $pb_ratio)',
    rating: 4.2,
    usageCount: 89,
    avgIC: 0.055
  },
  {
    id: 'template_3',
    name: 'ROE质量因子',
    type: 'quality',
    description: '基于净资产收益率的质量因子',
    expression: '$roe / STD($roe, 8)',
    rating: 4.0,
    usageCount: 234,
    avgIC: 0.042
  }
]

// 计算属性
const filteredTemplates = computed(() => {
  if (selectedCategory.value === 'all') {
    return factorTemplates
  }
  return factorTemplates.filter(template => template.type === selectedCategory.value)
})

// 方法
const handleTabChange = (tab: string) => {
  console.log('切换到标签页:', tab)
}

const selectFactorType = (type: string) => {
  selectedFactorType.value = type
  updateExpression()
}

const updateExpression = () => {
  // 根据配置自动生成表达式
  if (!selectedFactorType.value || dataConfig.primaryData.length === 0) {
    return
  }

  let expression = ''
  const primaryField = dataConfig.primaryData[0]
  const timeWindow = dataConfig.timeWindow

  switch (selectedFactorType.value) {
    case 'momentum':
      expression = `(${primaryField} / Ref(${primaryField}, ${timeWindow})) - 1`
      break
    case 'value':
      if (dataConfig.auxiliaryData.includes('$pe_ratio')) {
        expression = `1 / $pe_ratio`
      }
      break
    case 'volatility':
      expression = `STD(${primaryField}, ${timeWindow})`
      break
    default:
      expression = primaryField
  }

  generatedExpression.value = expression
}

const addOperation = (operation: string) => {
  const cursor = generatedExpression.value.length
  generatedExpression.value += operation
}

const addFunction = (func: string) => {
  const cursor = generatedExpression.value.length
  generatedExpression.value += `${func}()`
}

const clearExpression = () => {
  generatedExpression.value = ''
  syntaxErrors.value = []
  syntaxSuggestions.value = []
}

const validateExpression = () => {
  syntaxErrors.value = []
  syntaxSuggestions.value = []

  if (!generatedExpression.value.trim()) {
    syntaxErrors.value.push('表达式不能为空')
    return
  }

  // 简单的语法检查
  const expr = generatedExpression.value
  
  // 检查括号匹配
  const openCount = (expr.match(/\(/g) || []).length
  const closeCount = (expr.match(/\)/g) || []).length
  if (openCount !== closeCount) {
    syntaxErrors.value.push('括号不匹配')
  }

  // 检查函数调用
  const funcMatches = expr.match(/\w+\(/g)
  if (funcMatches) {
    const validFunctions = ['MA', 'STD', 'MAX', 'MIN', 'Ref', 'Delay', 'Rank', 'CORR']
    funcMatches.forEach(match => {
      const funcName = match.replace('(', '')
      if (!validFunctions.includes(funcName)) {
        syntaxErrors.value.push(`未识别的函数: ${funcName}`)
      }
    })
  }

  // 生成建议
  if (syntaxErrors.value.length === 0) {
    if (!expr.includes('$')) {
      syntaxSuggestions.value.push('建议使用数据字段（如$close）')
    }
    if (!expr.match(/\d+/)) {
      syntaxSuggestions.value.push('考虑添加数值参数')
    }
  }

  if (syntaxErrors.value.length === 0) {
    ElMessage.success('表达式语法正确')
  }
}

const handleExpressionChange = () => {
  // 实时检查语法
  syntaxErrors.value = []
  syntaxSuggestions.value = []
}

const formatExpression = (expr: string) => {
  // 简单的表达式格式化
  return expr
    .replace(/\(/g, '(\n  ')
    .replace(/\)/g, '\n)')
    .replace(/,/g, ',\n  ')
}

const applySuggestion = (suggestion: string) => {
  console.log('应用建议:', suggestion)
}

const handleNaturalInputChange = () => {
  // 处理自然语言输入变化
}

const fillNaturalTemplate = (content: string) => {
  naturalLanguageInput.value = content
}

const generateFromNatural = async () => {
  if (!naturalLanguageInput.value.trim()) {
    ElMessage.warning('请输入描述内容')
    return
  }

  isGenerating.value = true
  
  try {
    // 模拟AI生成过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const input = naturalLanguageInput.value.toLowerCase()
    let result: GenerationResult

    if (input.includes('动量') || input.includes('趋势')) {
      result = {
        expression: '($close / Ref($close, 20)) - 1',
        explanation: '这个表达式计算当前价格相对于20天前价格的变化率，用于捕捉股票的短期动量特征',
        suggestions: [
          '可以调整时间窗口（如10天、30天）来适应不同的投资周期',
          '建议结合成交量指标来验证动量的可靠性',
          '考虑对结果进行行业中性化处理'
        ]
      }
    } else if (input.includes('价值') || input.includes('市盈率') || input.includes('市净率')) {
      result = {
        expression: '1 / ($pe_ratio * $pb_ratio)',
        explanation: '这个表达式结合了市盈率和市净率，数值越大表示股票的价值投资吸引力越高',
        suggestions: [
          '可以添加财务质量指标（如ROE）来提高因子质量',
          '建议对极端值进行winsorize处理',
          '考虑按行业分组来提高因子的区分度'
        ]
      }
    } else {
      result = {
        expression: 'Rank(($close / MA($close, 20) - 1) + (1 / $pe_ratio))',
        explanation: '这是一个综合因子，结合了动量和价值两个维度，通过排序函数标准化',
        suggestions: [
          '可以调整动量和价值的权重比例',
          '建议添加更多维度如质量、成长性指标',
          '考虑使用机器学习方法自动优化权重'
        ]
      }
    }

    naturalGenerationResult.value = result
    resultRating.value = 4
    
  } catch (error) {
    ElMessage.error('生成失败，请稍后重试')
  } finally {
    isGenerating.value = false
  }
}

const copyExpression = async (expression: string) => {
  try {
    await navigator.clipboard.writeText(expression)
    ElMessage.success('表达式已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const acceptGeneration = () => {
  if (naturalGenerationResult.value) {
    finalExpression.value = naturalGenerationResult.value.expression
    expressionInfo.type = '动量因子'
    expressionInfo.complexity = '中等'
    expressionInfo.effectiveness = 75
    ElMessage.success('已接受生成的表达式')
  }
}

const refineGeneration = () => {
  console.log('优化表达式')
}

const regenerate = () => {
  generateFromNatural()
}

const selectCategory = (category: string) => {
  selectedCategory.value = category
}

const selectTemplate = (template: FactorTemplate) => {
  console.log('选择模板:', template)
}

const getTemplateTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    momentum: 'success',
    value: 'warning',
    quality: 'info',
    technical: 'danger'
  }
  return colorMap[type] || 'primary'
}

const useTemplate = (template: FactorTemplate) => {
  generatedExpression.value = template.expression
  finalExpression.value = template.expression
  expressionInfo.type = template.type
  expressionInfo.complexity = '模板'
  expressionInfo.effectiveness = Math.round(template.avgIC * 1000)
  ElMessage.success(`已应用模板: ${template.name}`)
}

const previewTemplate = (template: FactorTemplate) => {
  console.log('预览模板:', template)
}

const saveToLibrary = () => {
  if (finalExpression.value) {
    ElMessage.success('因子已保存到因子库')
  }
}

const useForTraining = () => {
  if (finalExpression.value) {
    ElMessage.success('因子已添加到训练配置')
  }
}

// 生命周期
onMounted(() => {
  // 初始化
})
</script>

<style scoped lang="scss">
.factor-generator {
  background: #f5f7fa;
  min-height: 100vh;
}

.generator-header {
  background: white;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 16px;

  .header-icon {
    font-size: 32px;
    color: #409eff;
  }

  .header-text {
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

.el-tabs {
  background: white;
  margin: 20px;
  border-radius: 8px;
  padding: 20px;
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

  .header-actions {
    display: flex;
    gap: 8px;
  }
}

// 可视化生成器
.visual-generator {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-card {
  .factor-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;

    .factor-type-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      border: 2px solid #e4e7ed;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        border-color: #409eff;
        background: #f0f9ff;
      }

      &.active {
        border-color: #409eff;
        background: #f0f9ff;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
      }

      .el-icon {
        font-size: 24px;
        color: #409eff;
      }

      .type-content {
        h4 {
          margin: 0 0 4px 0;
          color: #303133;
        }

        p {
          margin: 0;
          font-size: 12px;
          color: #606266;
        }
      }
    }
  }

  .data-config {
    .config-row {
      display: flex;
      align-items: center;
      margin-bottom: 16px;

      label {
        width: 100px;
        font-weight: 600;
        color: #303133;
      }

      .el-select {
        flex: 1;
      }

      .time-config {
        display: flex;
        gap: 8px;
        flex: 1;

        .el-input-number {
          width: 120px;
        }

        .el-select {
          width: 80px;
        }
      }
    }
  }

  .calculation-config {
    .config-section {
      margin-bottom: 20px;

      h4 {
        margin: 0 0 12px 0;
        color: #303133;
        font-size: 14px;
      }

      .operation-buttons,
      .function-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .el-button {
          min-width: 60px;
        }
      }
    }
  }
}

.expression-card {
  .expression-builder {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;

    .expression-editor {
      .syntax-errors {
        margin-top: 12px;

        .error-item {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #f56c6c;
          font-size: 12px;
          margin-bottom: 4px;

          .el-icon {
            font-size: 14px;
          }
        }
      }

      .syntax-suggestions {
        margin-top: 12px;

        .suggestions-header {
          font-size: 12px;
          color: #909399;
          margin-bottom: 6px;
        }

        .suggestions-list {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;

          .suggestion-tag {
            cursor: pointer;
          }
        }
      }
    }

    .expression-preview {
      .preview-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;

        span {
          font-weight: 600;
          color: #303133;
        }
      }

      .preview-content {
        .formatted-expression,
        .raw-expression {
          display: block;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 4px;
          border: 1px solid #e4e7ed;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 13px;
          line-height: 1.6;
          white-space: pre-wrap;
          word-break: break-all;
        }
      }
    }
  }
}

// 自然语言生成器
.natural-generator {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-card {
  .natural-input {
    .input-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 16px;

      .quick-templates {
        display: flex;
        align-items: center;
        gap: 8px;

        .templates-label {
          font-size: 14px;
          color: #606266;
        }
      }
    }
  }
}

.result-card {
  .generation-result {
    .result-expression {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;

      .expression-label {
        font-weight: 600;
        color: #303133;
      }

      .expression-code {
        flex: 1;
        padding: 8px 12px;
        background: #f8f9fa;
        border-radius: 4px;
        font-family: monospace;
        border: 1px solid #e4e7ed;
      }
    }

    .result-explanation {
      margin-bottom: 16px;

      .explanation-label {
        font-weight: 600;
        color: #303133;
        margin-bottom: 6px;
      }

      .explanation-text {
        color: #606266;
        line-height: 1.6;
      }
    }

    .result-suggestions {
      margin-bottom: 20px;

      .suggestions-label {
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
      }

      .suggestions-list {
        color: #606266;
        line-height: 1.6;
        padding-left: 20px;

        li {
          margin-bottom: 4px;
        }
      }
    }

    .result-actions {
      display: flex;
      gap: 12px;
    }
  }
}

// 模板库
.template-library {
  .template-categories {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }

  .templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;

    .template-card {
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

        h4 {
          margin: 0;
          color: #303133;
        }

        .template-meta {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
        }
      }

      .template-description {
        margin-bottom: 12px;

        p {
          margin: 0;
          font-size: 14px;
          color: #606266;
          line-height: 1.4;
        }
      }

      .template-expression {
        margin-bottom: 12px;
        padding: 8px;
        background: #f8f9fa;
        border-radius: 4px;

        code {
          font-family: monospace;
          font-size: 12px;
          color: #409eff;
        }
      }

      .template-stats {
        display: flex;
        justify-content: space-between;
        margin-bottom: 12px;

        .stat-item {
          text-align: center;

          .stat-label {
            display: block;
            font-size: 12px;
            color: #909399;
            margin-bottom: 2px;
          }

          .stat-value {
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .template-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}

// 结果面板
.result-panel {
  margin: 20px;

  .result-header {
    display: flex;
    align-items: center;
    gap: 8px;

    .el-icon {
      color: #67c23a;
    }

    span {
      flex: 1;
      font-weight: 600;
    }

    .result-actions {
      display: flex;
      gap: 8px;
    }
  }

  .final-result {
    .expression-display {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;

      label {
        font-weight: 600;
        color: #303133;
      }

      .final-expression {
        flex: 1;
        padding: 12px;
        background: #f0f9ff;
        border: 1px solid #409eff;
        border-radius: 6px;
        font-family: monospace;
        color: #409eff;
        font-weight: 600;
      }
    }

    .expression-info {
      display: flex;
      gap: 24px;

      .info-item {
        display: flex;
        align-items: center;
        gap: 8px;

        .info-label {
          font-size: 14px;
          color: #606266;
        }

        .info-value {
          font-weight: 600;
          color: #303133;
        }

        .el-progress {
          width: 100px;
        }
      }
    }
  }
}
</style>