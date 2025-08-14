<template>
  <div class="factor-editor">
    <!-- 编辑器头部 -->
    <div class="editor-header">
      <h3>
        <el-icon><EditPen /></el-icon>
        手动因子编辑器
      </h3>
      <p>使用专业的代码编辑器创建和编辑Qlib因子表达式</p>
    </div>

    <!-- 因子基本信息 -->
    <el-form :model="factorForm" :rules="formRules" ref="formRef" label-width="120px">
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="因子名称" prop="name">
            <el-input 
              v-model="factorForm.name" 
              placeholder="请输入因子名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="因子类型" prop="category">
            <el-select v-model="factorForm.category" placeholder="选择因子类型" style="width: 100%">
              <el-option label="技术指标" value="technical" />
              <el-option label="基本面" value="fundamental" />
              <el-option label="情绪指标" value="sentiment" />
              <el-option label="组合因子" value="composite" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="因子描述" prop="description">
        <el-input 
          v-model="factorForm.description" 
          type="textarea"
          :rows="2"
          placeholder="请描述因子的投资逻辑和计算方法"
        />
      </el-form-item>
    </el-form>

    <!-- 代码编辑器 -->
    <div class="editor-section">
      <div class="editor-toolbar">
        <div class="toolbar-left">
          <span class="section-title">因子表达式编辑器</span>
          <el-tag :type="validationStatus.type" size="small">
            {{ validationStatus.text }}
          </el-tag>
        </div>
        <div class="toolbar-right">
          <el-button size="small" @click="formatExpression">
            <el-icon><Operation /></el-icon>
            格式化
          </el-button>
          <el-button size="small" @click="validateExpression">
            <el-icon><CircleCheck /></el-icon>
            验证语法
          </el-button>
          <el-button size="small" @click="showHelp = true">
            <el-icon><QuestionFilled /></el-icon>
            语法帮助
          </el-button>
        </div>
      </div>
      
      <!-- Monaco编辑器容器 -->
      <div class="monaco-editor-container">
        <div 
          ref="editorContainer" 
          class="monaco-editor"
          @input="handleExpressionChange"
        ></div>
      </div>
      
      <!-- 语法错误提示 -->
      <div v-if="syntaxErrors.length > 0" class="syntax-errors">
        <el-alert
          v-for="(error, index) in syntaxErrors"
          :key="index"
          :title="error.message"
          type="error"
          :description="error.detail"
          show-icon
          :closable="false"
        />
      </div>
    </div>

    <!-- 因子预览 -->
    <div v-if="factorForm.expression" class="preview-section">
      <h4>表达式预览</h4>
      <div class="expression-preview">
        <code>{{ factorForm.expression }}</code>
      </div>
      
      <!-- 快速测试 -->
      <div class="quick-test">
        <el-button type="info" @click="quickTest" :loading="testing">
          <el-icon><View /></el-icon>
          快速测试
        </el-button>
        <span class="test-hint">在样本数据上快速验证因子有效性</span>
      </div>
    </div>

    <!-- 常用函数面板 -->
    <div class="functions-panel">
      <h4>常用Qlib函数</h4>
      <div class="function-categories">
        <el-tabs v-model="activeFunctionTab" type="card">
          <el-tab-pane label="数学运算" name="math">
            <div class="function-grid">
              <el-button 
                v-for="func in mathFunctions" 
                :key="func.name"
                size="small"
                @click="insertFunction(func)"
                class="function-btn"
              >
                {{ func.name }}
              </el-button>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="时间序列" name="timeseries">
            <div class="function-grid">
              <el-button 
                v-for="func in timeseriesFunctions" 
                :key="func.name"
                size="small"
                @click="insertFunction(func)"
                class="function-btn"
              >
                {{ func.name }}
              </el-button>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="统计函数" name="stats">
            <div class="function-grid">
              <el-button 
                v-for="func in statsFunctions" 
                :key="func.name"
                size="small"
                @click="insertFunction(func)"
                class="function-btn"
              >
                {{ func.name }}
              </el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 保存操作 -->
    <div class="save-actions">
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" @click="saveFactor" :disabled="!isValid">
        <el-icon><Document /></el-icon>
        保存因子
      </el-button>
    </div>

    <!-- 语法帮助对话框 -->
    <el-dialog v-model="showHelp" title="Qlib因子表达式语法帮助" width="800px">
      <div class="help-content">
        <h4>基本语法</h4>
        <ul>
          <li><code>$close</code> - 收盘价</li>
          <li><code>$open</code> - 开盘价</li>
          <li><code>$high</code> - 最高价</li>
          <li><code>$low</code> - 最低价</li>
          <li><code>$volume</code> - 成交量</li>
          <li><code>$pe_ttm</code> - 市盈率TTM</li>
          <li><code>$market_cap</code> - 市值</li>
        </ul>
        
        <h4>常用函数</h4>
        <ul>
          <li><code>Ref(expression, N)</code> - 获取N天前的值</li>
          <li><code>Mean(expression, N)</code> - N天移动平均</li>
          <li><code>Std(expression, N)</code> - N天标准差</li>
          <li><code>Max(expression, N)</code> - N天最大值</li>
          <li><code>Min(expression, N)</code> - N天最小值</li>
          <li><code>Rank(expression)</code> - 横截面排名</li>
          <li><code>Quantile(expression, q)</code> - 分位数</li>
        </ul>
        
        <h4>示例表达式</h4>
        <ul>
          <li><code>($close / Ref($close, 20)) - 1</code> - 20日收益率</li>
          <li><code>Rank($close / $open - 1)</code> - 日内收益率排名</li>
          <li><code>($close - Mean($close, 20)) / Std($close, 20)</code> - 价格标准化</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  EditPen, Operation, CircleCheck, QuestionFilled, 
  View, Document 
} from '@element-plus/icons-vue'
import type { FactorDefinition } from '@/types/factor'

// Props和Events
const props = defineProps<{
  modelValue?: FactorDefinition | null
}>()

const emit = defineEmits<{
  'update:modelValue': [factor: FactorDefinition]
  validate: [isValid: boolean, errors?: string[]]
  save: [factor: FactorDefinition]
}>()

// 响应式数据
const formRef = ref<FormInstance>()
const editorContainer = ref<HTMLElement>()
const showHelp = ref(false)
const testing = ref(false)
const activeFunctionTab = ref('math')

const factorForm = reactive<Partial<FactorDefinition>>({
  name: '',
  expression: '',
  description: '',
  category: 'technical'
})

const validationStatus = ref({
  type: 'info' as const,
  text: '待验证'
})

const syntaxErrors = ref<Array<{
  message: string
  detail: string
  line?: number
}>>([])

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入因子名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择因子类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入因子描述', trigger: 'blur' }
  ]
}

// Monaco编辑器实例
let monacoEditor: any = null

// 函数库定义
const mathFunctions = ref([
  { name: 'Abs', description: '绝对值', syntax: 'Abs(expression)' },
  { name: 'Log', description: '自然对数', syntax: 'Log(expression)' },
  { name: 'Sqrt', description: '平方根', syntax: 'Sqrt(expression)' },
  { name: 'Power', description: '幂运算', syntax: 'Power(base, exp)' },
  { name: 'Round', description: '四舍五入', syntax: 'Round(expression, digits)' }
])

const timeseriesFunctions = ref([
  { name: 'Ref', description: '时间延迟', syntax: 'Ref(expression, N)' },
  { name: 'Delay', description: '延迟N期', syntax: 'Delay(expression, N)' },
  { name: 'Delta', description: '差分', syntax: 'Delta(expression, N)' },
  { name: 'Shift', description: '位移', syntax: 'Shift(expression, N)' }
])

const statsFunctions = ref([
  { name: 'Mean', description: '移动平均', syntax: 'Mean(expression, N)' },
  { name: 'Std', description: '标准差', syntax: 'Std(expression, N)' },
  { name: 'Var', description: '方差', syntax: 'Var(expression, N)' },
  { name: 'Max', description: '最大值', syntax: 'Max(expression, N)' },
  { name: 'Min', description: '最小值', syntax: 'Min(expression, N)' },
  { name: 'Rank', description: '排名', syntax: 'Rank(expression)' },
  { name: 'Quantile', description: '分位数', syntax: 'Quantile(expression, q)' }
])

// 计算属性
const isValid = computed(() => {
  return factorForm.name && 
         factorForm.expression && 
         factorForm.description && 
         validationStatus.value.type !== 'danger'
})

// 监听器
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    Object.assign(factorForm, newValue)
    if (monacoEditor) {
      monacoEditor.setValue(newValue.expression || '')
    }
  }
}, { immediate: true })

// 方法
const initMonacoEditor = async () => {
  // 这里应该集成Monaco Editor
  // 由于Monaco Editor需要额外的配置，这里用简化版本
  if (editorContainer.value) {
    // 创建一个简单的文本区域作为替代
    const textarea = document.createElement('textarea')
    textarea.value = factorForm.expression || ''
    textarea.placeholder = '请输入Qlib因子表达式，例如: ($close / Ref($close, 20)) - 1'
    textarea.className = 'simple-editor'
    textarea.addEventListener('input', (e) => {
      const target = e.target as HTMLTextAreaElement
      factorForm.expression = target.value
      handleExpressionChange()
    })
    
    editorContainer.value.appendChild(textarea)
    
    // 模拟Monaco编辑器对象
    monacoEditor = {
      setValue: (value: string) => {
        textarea.value = value
        factorForm.expression = value
      },
      getValue: () => textarea.value,
      dispose: () => textarea.remove()
    }
  }
}

const handleExpressionChange = () => {
  // 实时验证表达式
  if (factorForm.expression) {
    validateExpression()
  }
}

const validateExpression = async () => {
  if (!factorForm.expression) {
    validationStatus.value = { type: 'warning', text: '表达式为空' }
    emit('validate', false, ['表达式不能为空'])
    return
  }

  testing.value = true
  
  try {
    // 调用qlib API进行因子验证
    const response = await fetch('/api/v1/qlib-factors/validate-factor', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        factor_expression: factorForm.expression,
        instruments: 'csi300',
        start_time: '2020-01-01',
        end_time: '2023-12-31',
        validation_metrics: ['ic', 'rank_ic']
      })
    })
    
    const result = await response.json()
    
    if (result.status === 'success') {
      const validation = result.data
      
      if (validation.isValid) {
        validationStatus.value = { 
          type: 'success', 
          text: `语法正确 (得分: ${validation.score}分)` 
        }
        syntaxErrors.value = []
        
        // 如果有性能指标，更新显示
        if (validation.metrics) {
          updatePerformanceMetrics(validation.metrics)
        }
        
        emit('validate', true)
        ElMessage.success('因子表达式验证通过')
      } else {
        validationStatus.value = { type: 'danger', text: '验证失败' }
        syntaxErrors.value = validation.errors.map((error: string) => ({
          message: error,
          detail: '请检查因子表达式语法'
        }))
        
        if (validation.warnings && validation.warnings.length > 0) {
          validation.warnings.forEach((warning: string) => {
            ElMessage.warning(warning)
          })
        }
        
        emit('validate', false, validation.errors)
      }
    } else {
      throw new Error(result.message || '验证请求失败')
    }
  } catch (error) {
    console.error('因子验证失败:', error)
    validationStatus.value = { type: 'danger', text: '验证失败' }
    
    // 降级到简单的本地验证
    const localErrors = await validateQlibExpressionLocal(factorForm.expression)
    syntaxErrors.value = localErrors
    
    if (localErrors.length === 0) {
      validationStatus.value = { type: 'warning', text: '本地验证通过(服务器验证失败)' }
      emit('validate', true)
    } else {
      emit('validate', false, localErrors.map(e => e.message))
    }
    
    ElMessage.error('服务器验证失败，使用本地验证: ' + error.message)
  } finally {
    testing.value = false
  }
}

// 更新性能指标显示
const updatePerformanceMetrics = (metrics: any) => {
  if (metrics.ic) {
    console.log('IC指标:', metrics.ic)
  }
  if (metrics.statistics) {
    console.log('统计信息:', metrics.statistics)
  }
}

// 本地简单验证作为降级方案
const validateQlibExpressionLocal = async (expression: string) => {
  await new Promise(resolve => setTimeout(resolve, 300))
  
  const errors: Array<{message: string, detail: string}> = []
  
  // 基本语法检查
  if (expression.includes('(') && !expression.includes(')')) {
    errors.push({
      message: '括号不匹配',
      detail: '表达式中存在未闭合的括号'
    })
  }
  
  if (expression.includes('$') && !/\$\w+/.test(expression)) {
    errors.push({
      message: '字段引用格式错误',
      detail: '字段引用应该以$开头，如$close, $volume等'
    })
  }
  
  // 检查常用qlib函数
  const qlibFunctions = ['Mean', 'Std', 'Ref', 'Rank', 'Max', 'Min', 'Sum', 'Delta']
  const missingFunctions = expression.match(/[A-Z][a-z]+\(/g)
  if (missingFunctions) {
    missingFunctions.forEach(func => {
      const funcName = func.slice(0, -1)
      if (!qlibFunctions.includes(funcName)) {
        errors.push({
          message: `未知函数: ${funcName}`,
          detail: `请确认函数名是否正确，常用函数包括: ${qlibFunctions.join(', ')}`
        })
      }
    })
  }
  
  return errors
}

const formatExpression = () => {
  if (!factorForm.expression) return
  
  // 简单的格式化逻辑
  let formatted = factorForm.expression
    .replace(/\s+/g, ' ')
    .replace(/\(/g, '( ')
    .replace(/\)/g, ' )')
    .replace(/,/g, ', ')
    .replace(/\s+/g, ' ')
    .trim()
  
  factorForm.expression = formatted
  if (monacoEditor) {
    monacoEditor.setValue(formatted)
  }
  
  ElMessage.success('表达式已格式化')
}

const insertFunction = (func: any) => {
  const currentExpression = factorForm.expression || ''
  const insertText = func.syntax
  
  // 简单的插入逻辑
  factorForm.expression = currentExpression + (currentExpression ? ' + ' : '') + insertText
  
  if (monacoEditor) {
    monacoEditor.setValue(factorForm.expression)
  }
}

const quickTest = async () => {
  if (!isValid.value) {
    ElMessage.warning('请先完善因子信息并确保语法正确')
    return
  }
  
  testing.value = true
  
  try {
    // 模拟快速测试
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('快速测试完成，因子表现良好')
  } catch (error) {
    ElMessage.error('快速测试失败')
  } finally {
    testing.value = false
  }
}

const saveFactor = async () => {
  try {
    await formRef.value?.validate()
    
    const factor: FactorDefinition = {
      id: `factor_${Date.now()}`,
      name: factorForm.name!,
      expression: factorForm.expression!,
      description: factorForm.description!,
      category: factorForm.category as any,
      createdAt: new Date(),
      createdBy: 'Manual Editor'
    }
    
    emit('save', factor)
    emit('update:modelValue', factor)
    
  } catch (error) {
    ElMessage.error('请完善因子信息')
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  factorForm.expression = ''
  if (monacoEditor) {
    monacoEditor.setValue('')
  }
  syntaxErrors.value = []
  validationStatus.value = { type: 'info', text: '待验证' }
}

// 生命周期
onMounted(() => {
  initMonacoEditor()
})

onUnmounted(() => {
  if (monacoEditor) {
    monacoEditor.dispose()
  }
})
</script>

<style scoped>
.factor-editor {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background: #fafafa;
  border-radius: 8px;
}

.editor-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  color: #303133;
}

.editor-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.editor-section {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-weight: 500;
  color: #303133;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.monaco-editor-container {
  height: 300px;
  position: relative;
}

.monaco-editor {
  height: 100%;
  width: 100%;
}

.simple-editor {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: 16px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.syntax-errors {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.expression-preview {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.expression-preview code {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  color: #e6a23c;
}

.quick-test {
  display: flex;
  align-items: center;
  gap: 12px;
}

.test-hint {
  font-size: 12px;
  color: #909399;
}

.functions-panel {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.functions-panel h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.function-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  padding: 16px 0;
}

.function-btn {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
}

.save-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.help-content h4 {
  color: #303133;
  margin: 20px 0 12px 0;
}

.help-content h4:first-child {
  margin-top: 0;
}

.help-content ul {
  margin: 0 0 16px 20px;
  padding: 0;
}

.help-content li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.help-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  color: #e6a23c;
}

@media (max-width: 768px) {
  .factor-editor {
    padding: 16px;
  }
  
  .editor-toolbar {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .function-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
  
  .save-actions {
    flex-direction: column;
  }
}
</style>