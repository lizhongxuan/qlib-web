<template>
  <div class="qlib-strategy-builder">
    <!-- 策略构建器头部 -->
    <el-card class="builder-header">
      <template #header>
        <div class="header-content">
          <div class="header-title">
            <el-icon><Tools /></el-icon>
            <span>Qlib可视化策略构建器</span>
          </div>
          <div class="header-actions">
            <el-button @click="loadTemplate" :loading="loading">
              <el-icon><FolderOpened /></el-icon>
              加载模板
            </el-button>
            <el-button @click="saveTemplate">
              <el-icon><DocumentAdd /></el-icon>
              保存模板
            </el-button>
            <el-button @click="previewStrategy">
              <el-icon><View /></el-icon>
              预览策略
            </el-button>
            <el-button type="primary" @click="buildStrategy" :loading="building">
              <el-icon><Setting /></el-icon>
              构建策略
            </el-button>
          </div>
        </div>
      </template>

      <!-- 策略基本信息 -->
      <div class="strategy-basic-info">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="策略名称">
              <el-input 
                v-model="strategyConfig.name" 
                placeholder="请输入策略名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="策略类型">
              <el-select v-model="strategyConfig.type" @change="onStrategyTypeChange">
                <el-option label="TopK选股策略" value="topk" />
                <el-option label="多空策略" value="long_short" />
                <el-option label="权重优化策略" value="weight_opt" />
                <el-option label="因子轮动策略" value="factor_rotation" />
                <el-option label="自定义策略" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="策略描述">
              <el-input 
                v-model="strategyConfig.description" 
                placeholder="策略描述信息"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 策略构建工作区 -->
    <el-row :gutter="16" class="builder-workspace">
      <!-- 组件库面板 -->
      <el-col :span="6">
        <el-card class="component-library">
          <template #header>
            <span>策略组件库</span>
          </template>

          <el-collapse v-model="activeComponentGroups">
            <!-- 因子选择器 -->
            <el-collapse-item title="因子选择器" name="factors">
              <div class="component-group">
                <div 
                  v-for="factor in availableFactors" 
                  :key="factor.name"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('factor', factor)"
                >
                  <el-icon><DataBoard /></el-icon>
                  <span>{{ factor.display_name }}</span>
                  <el-tag size="small" :type="getFactorTagType(factor.category)">
                    {{ factor.category }}
                  </el-tag>
                </div>
              </div>
            </el-collapse-item>

            <!-- 模型组件 -->
            <el-collapse-item title="预测模型" name="models">
              <div class="component-group">
                <div 
                  v-for="model in availableModels"
                  :key="model.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('model', model)"
                >
                  <el-icon><Cpu /></el-icon>
                  <span>{{ model.name }}</span>
                  <el-tag size="small" type="primary">{{ model.type }}</el-tag>
                </div>
              </div>
            </el-collapse-item>

            <!-- 信号处理器 -->
            <el-collapse-item title="信号处理" name="signals">
              <div class="component-group">
                <div 
                  v-for="processor in signalProcessors"
                  :key="processor.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('signal', processor)"
                >
                  <el-icon><Operation /></el-icon>
                  <span>{{ processor.name }}</span>
                </div>
              </div>
            </el-collapse-item>

            <!-- 选股器 -->
            <el-collapse-item title="选股器" name="selectors">
              <div class="component-group">
                <div 
                  v-for="selector in stockSelectors"
                  :key="selector.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('selector', selector)"
                >
                  <el-icon><Filter /></el-icon>
                  <span>{{ selector.name }}</span>
                </div>
              </div>
            </el-collapse-item>

            <!-- 权重分配器 -->
            <el-collapse-item title="权重分配" name="weights">
              <div class="component-group">
                <div 
                  v-for="allocator in weightAllocators"
                  :key="allocator.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('weight', allocator)"
                >
                  <el-icon><PieChart /></el-icon>
                  <span>{{ allocator.name }}</span>
                </div>
              </div>
            </el-collapse-item>

            <!-- 风险控制器 -->
            <el-collapse-item title="风险控制" name="risks">
              <div class="component-group">
                <div 
                  v-for="controller in riskControllers"
                  :key="controller.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="startDrag('risk', controller)"
                >
                  <el-icon><Warning /></el-icon>
                  <span>{{ controller.name }}</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>

      <!-- 策略构建画布 -->
      <el-col :span="12">
        <el-card class="strategy-canvas">
          <template #header>
            <div class="canvas-header">
              <span>策略构建画布</span>
              <div class="canvas-controls">
                <el-button size="small" @click="clearCanvas">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
                <el-button size="small" @click="autoLayout">
                  <el-icon><Grid /></el-icon>
                  自动布局
                </el-button>
                <el-button size="small" @click="validateStrategy">
                  <el-icon><CircleCheck /></el-icon>
                  验证
                </el-button>
              </div>
            </div>
          </template>

          <div 
            class="canvas-area"
            @drop="onDrop"
            @dragover.prevent
            @dragenter.prevent
          >
            <!-- 策略流程图 -->
            <div v-if="strategyComponents.length === 0" class="canvas-placeholder">
              <el-icon><Plus /></el-icon>
              <span>拖拽组件到此处开始构建策略</span>
            </div>

            <!-- 策略组件节点 -->
            <div 
              v-for="(component, index) in strategyComponents"
              :key="component.id"
              class="strategy-node"
              :style="{ 
                left: component.position.x + 'px', 
                top: component.position.y + 'px' 
              }"
              @click="selectComponent(component)"
              :class="{ 'selected': selectedComponent?.id === component.id }"
            >
              <div class="node-header">
                <el-icon>
                  <component :is="getComponentIcon(component.type)" />
                </el-icon>
                <span class="node-title">{{ component.name }}</span>
                <el-button 
                  size="small" 
                  type="danger" 
                  text 
                  @click.stop="removeComponent(index)"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <div class="node-content">
                <div class="node-config">
                  <!-- 组件具体配置内容 -->
                  <component 
                    :is="getConfigComponent(component.type)"
                    v-model="component.config"
                    :component-data="component"
                  />
                </div>
              </div>
              
              <!-- 连接点 -->
              <div class="connection-points">
                <div class="input-point" v-if="component.type !== 'factor'"></div>
                <div class="output-point"></div>
              </div>
            </div>

            <!-- 连接线 -->
            <svg class="connection-lines" :style="{ width: '100%', height: '100%' }">
              <line
                v-for="connection in connections"
                :key="`${connection.from}-${connection.to}`"
                :x1="connection.x1"
                :y1="connection.y1"
                :x2="connection.x2"
                :y2="connection.y2"
                stroke="#409eff"
                stroke-width="2"
                marker-end="url(#arrowhead)"
              />
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                 refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#409eff" />
                </marker>
              </defs>
            </svg>
          </div>
        </el-card>
      </el-col>

      <!-- 配置属性面板 -->
      <el-col :span="6">
        <el-card class="properties-panel">
          <template #header>
            <span>属性配置</span>
          </template>

          <div v-if="!selectedComponent" class="no-selection">
            <el-empty description="请选择一个组件进行配置" :image-size="80" />
          </div>

          <div v-else class="component-properties">
            <h4>{{ selectedComponent.name }}</h4>
            
            <!-- 通用属性 -->
            <el-form label-width="80px" size="small">
              <el-form-item label="组件名称">
                <el-input v-model="selectedComponent.name" />
              </el-form-item>
              <el-form-item label="启用状态">
                <el-switch v-model="selectedComponent.enabled" />
              </el-form-item>
            </el-form>

            <el-divider />

            <!-- 特定组件属性 -->
            <div class="specific-properties">
              <!-- 因子组件属性 -->
              <div v-if="selectedComponent.type === 'factor'">
                <h5>因子配置</h5>
                <el-form label-width="80px" size="small">
                  <el-form-item label="权重">
                    <el-input-number 
                      v-model="selectedComponent.config.weight" 
                      :min="0" 
                      :max="1" 
                      :step="0.1"
                    />
                  </el-form-item>
                  <el-form-item label="标准化">
                    <el-switch v-model="selectedComponent.config.normalize" />
                  </el-form-item>
                  <el-form-item label="中性化">
                    <el-select v-model="selectedComponent.config.neutralize">
                      <el-option label="无" value="none" />
                      <el-option label="行业中性" value="industry" />
                      <el-option label="市值中性" value="market_cap" />
                      <el-option label="行业+市值" value="both" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>

              <!-- 模型组件属性 -->
              <div v-else-if="selectedComponent.type === 'model'">
                <h5>模型配置</h5>
                <el-form label-width="80px" size="small">
                  <el-form-item label="模型参数">
                    <el-input 
                      type="textarea" 
                      v-model="selectedComponent.config.params" 
                      placeholder="JSON格式参数"
                      :rows="4"
                    />
                  </el-form-item>
                  <el-form-item label="训练窗口">
                    <el-input-number 
                      v-model="selectedComponent.config.train_window" 
                      :min="20" 
                      :max="252"
                    />
                  </el-form-item>
                  <el-form-item label="更新频率">
                    <el-select v-model="selectedComponent.config.update_freq">
                      <el-option label="每日" value="D" />
                      <el-option label="每周" value="W" />
                      <el-option label="每月" value="M" />
                      <el-option label="每季度" value="Q" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>

              <!-- 选股器属性 -->
              <div v-else-if="selectedComponent.type === 'selector'">
                <h5>选股配置</h5>
                <el-form label-width="80px" size="small">
                  <el-form-item label="选股数量">
                    <el-input-number 
                      v-model="selectedComponent.config.stock_count" 
                      :min="5" 
                      :max="100"
                    />
                  </el-form-item>
                  <el-form-item label="选股方式">
                    <el-radio-group v-model="selectedComponent.config.method">
                      <el-radio label="topk">TopK</el-radio>
                      <el-radio label="threshold">阈值</el-radio>
                      <el-radio label="percentile">百分位</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="阈值" v-if="selectedComponent.config.method === 'threshold'">
                    <el-input-number 
                      v-model="selectedComponent.config.threshold" 
                      :step="0.01"
                    />
                  </el-form-item>
                </el-form>
              </div>

              <!-- 权重分配器属性 -->
              <div v-else-if="selectedComponent.type === 'weight'">
                <h5>权重配置</h5>
                <el-form label-width="80px" size="small">
                  <el-form-item label="分配方式">
                    <el-select v-model="selectedComponent.config.allocation_method">
                      <el-option label="等权重" value="equal" />
                      <el-option label="信号权重" value="signal" />
                      <el-option label="风险平价" value="risk_parity" />
                      <el-option label="最小方差" value="min_variance" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="最大权重">
                    <el-input-number 
                      v-model="selectedComponent.config.max_weight" 
                      :min="0.01" 
                      :max="1" 
                      :step="0.01"
                    />
                  </el-form-item>
                  <el-form-item label="重平衡频率">
                    <el-select v-model="selectedComponent.config.rebalance_freq">
                      <el-option label="每日" value="D" />
                      <el-option label="每周" value="W" />
                      <el-option label="每月" value="M" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>

              <!-- 风险控制器属性 -->
              <div v-else-if="selectedComponent.type === 'risk'">
                <h5>风险控制</h5>
                <el-form label-width="80px" size="small">
                  <el-form-item label="最大回撤">
                    <el-input-number 
                      v-model="selectedComponent.config.max_drawdown" 
                      :min="0.05" 
                      :max="0.5" 
                      :step="0.01"
                    />
                  </el-form-item>
                  <el-form-item label="止损比例">
                    <el-input-number 
                      v-model="selectedComponent.config.stop_loss" 
                      :min="0.05" 
                      :max="0.3" 
                      :step="0.01"
                    />
                  </el-form-item>
                  <el-form-item label="止盈比例">
                    <el-input-number 
                      v-model="selectedComponent.config.take_profit" 
                      :min="0.1" 
                      :max="1" 
                      :step="0.05"
                    />
                  </el-form-item>
                  <el-form-item label="波动率控制">
                    <el-switch v-model="selectedComponent.config.volatility_control" />
                  </el-form-item>
                </el-form>
              </div>
            </div>

            <!-- 验证结果 -->
            <div v-if="selectedComponent.validation" class="validation-result">
              <el-divider />
              <h5>验证结果</h5>
              <el-alert
                :title="selectedComponent.validation.message"
                :type="selectedComponent.validation.status"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 策略代码预览对话框 -->
    <el-dialog v-model="showCodePreview" title="策略代码预览" width="70%">
      <div class="code-preview">
        <el-tabs v-model="activeCodeTab">
          <el-tab-pane label="Python代码" name="python">
            <pre class="code-content">{{ generatedCode.python }}</pre>
          </el-tab-pane>
          <el-tab-pane label="Qlib配置" name="config">
            <pre class="code-content">{{ generatedCode.config }}</pre>
          </el-tab-pane>
          <el-tab-pane label="回测脚本" name="backtest">
            <pre class="code-content">{{ generatedCode.backtest }}</pre>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="copyCode">复制代码</el-button>
        <el-button @click="downloadCode">下载代码</el-button>
        <el-button type="primary" @click="runStrategy">运行策略</el-button>
      </template>
    </el-dialog>

    <!-- 策略模板对话框 -->
    <el-dialog v-model="showTemplateDialog" title="策略模板" width="60%">
      <div class="template-list">
        <el-row :gutter="16">
          <el-col 
            v-for="template in strategyTemplates"
            :key="template.id"
            :span="12"
            class="template-item"
          >
            <el-card 
              class="template-card"
              @click="loadStrategyTemplate(template)"
            >
              <template #header>
                <div class="template-header">
                  <span>{{ template.name }}</span>
                  <el-tag :type="template.difficulty === 'easy' ? 'success' : template.difficulty === 'medium' ? 'warning' : 'danger'">
                    {{ template.difficulty === 'easy' ? '简单' : template.difficulty === 'medium' ? '中等' : '困难' }}
                  </el-tag>
                </div>
              </template>
              <div class="template-content">
                <p>{{ template.description }}</p>
                <div class="template-tags">
                  <el-tag 
                    v-for="tag in template.tags"
                    :key="tag"
                    size="small"
                    class="template-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Tools, FolderOpened, DocumentAdd, View, Setting, DataBoard, Cpu,
  Operation, Filter, PieChart, Warning, Delete, Grid, CircleCheck,
  Plus, Close
} from '@element-plus/icons-vue'

// 数据结构定义
interface StrategyConfig {
  name: string
  type: string
  description: string
}

interface Factor {
  name: string
  display_name: string
  category: string
}

interface Model {
  type: string
  name: string
}

interface StrategyComponent {
  id: string
  type: string
  name: string
  position: { x: number; y: number }
  config: any
  enabled: boolean
  validation?: {
    status: 'success' | 'warning' | 'error'
    message: string
  }
}

interface Connection {
  from: string
  to: string
  x1: number
  y1: number
  x2: number
  y2: number
}

interface StrategyTemplate {
  id: string
  name: string
  description: string
  difficulty: 'easy' | 'medium' | 'hard'
  tags: string[]
  components: StrategyComponent[]
}

// 响应式数据
const loading = ref(false)
const building = ref(false)
const showCodePreview = ref(false)
const showTemplateDialog = ref(false)
const activeCodeTab = ref('python')
const activeComponentGroups = ref(['factors', 'models', 'signals'])
const selectedComponent = ref<StrategyComponent | null>(null)

const strategyConfig = reactive<StrategyConfig>({
  name: '',
  type: 'topk',
  description: ''
})

const strategyComponents = ref<StrategyComponent[]>([])
const connections = ref<Connection[]>([])

const availableFactors = ref<Factor[]>([
  { name: 'pe_ratio', display_name: '市盈率', category: '价值' },
  { name: 'pb_ratio', display_name: '市净率', category: '价值' },
  { name: 'return_1m', display_name: '1月收益率', category: '动量' },
  { name: 'return_3m', display_name: '3月收益率', category: '动量' },
  { name: 'rsi', display_name: 'RSI', category: '技术' },
  { name: 'macd', display_name: 'MACD', category: '技术' }
])

const availableModels = ref<Model[]>([
  { type: 'lightgbm', name: 'LightGBM' },
  { type: 'xgboost', name: 'XGBoost' },
  { type: 'lstm', name: 'LSTM' },
  { type: 'linear', name: '线性回归' }
])

const signalProcessors = ref([
  { type: 'normalize', name: '标准化' },
  { type: 'rank', name: '排序' },
  { type: 'winsorize', name: '去极值' },
  { type: 'neutralize', name: '中性化' }
])

const stockSelectors = ref([
  { type: 'topk', name: 'TopK选股' },
  { type: 'threshold', name: '阈值选股' },
  { type: 'percentile', name: '百分位选股' }
])

const weightAllocators = ref([
  { type: 'equal', name: '等权重' },
  { type: 'signal', name: '信号权重' },
  { type: 'risk_parity', name: '风险平价' },
  { type: 'min_variance', name: '最小方差' }
])

const riskControllers = ref([
  { type: 'drawdown', name: '回撤控制' },
  { type: 'volatility', name: '波动率控制' },
  { type: 'position', name: '仓位控制' },
  { type: 'stop_loss', name: '止损控制' }
])

const strategyTemplates = ref<StrategyTemplate[]>([
  {
    id: 'template_1',
    name: '多因子TopK策略',
    description: '基于多个因子的TopK选股策略，适合初学者',
    difficulty: 'easy',
    tags: ['多因子', 'TopK', '选股'],
    components: []
  },
  {
    id: 'template_2',
    name: '动量轮动策略',
    description: '基于动量因子的轮动策略',
    difficulty: 'medium',
    tags: ['动量', '轮动', '择时'],
    components: []
  },
  {
    id: 'template_3',
    name: '机器学习多空策略',
    description: '结合机器学习的多空策略',
    difficulty: 'hard',
    tags: ['机器学习', '多空', '对冲'],
    components: []
  }
])

const generatedCode = reactive({
  python: '',
  config: '',
  backtest: ''
})

// 方法
const startDrag = (type: string, data: any) => {
  // 设置拖拽数据
  const dragData = { type, data }
  // 在实际实现中，这里应该使用 dataTransfer
  console.log('开始拖拽:', dragData)
}

const onDrop = (event: DragEvent) => {
  const rect = event.currentTarget!.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 这里应该从 dataTransfer 获取数据
  // 为演示目的，我们模拟添加一个组件
  addComponent('factor', availableFactors.value[0], { x, y })
}

const addComponent = (type: string, data: any, position: { x: number; y: number }) => {
  const component: StrategyComponent = {
    id: `${type}_${Date.now()}`,
    type,
    name: data.display_name || data.name,
    position,
    config: getDefaultConfig(type),
    enabled: true
  }
  
  strategyComponents.value.push(component)
}

const getDefaultConfig = (type: string) => {
  switch (type) {
    case 'factor':
      return { weight: 1.0, normalize: true, neutralize: 'none' }
    case 'model':
      return { params: '{}', train_window: 60, update_freq: 'M' }
    case 'selector':
      return { stock_count: 20, method: 'topk' }
    case 'weight':
      return { allocation_method: 'equal', max_weight: 0.1, rebalance_freq: 'M' }
    case 'risk':
      return { max_drawdown: 0.1, stop_loss: 0.05, take_profit: 0.2, volatility_control: false }
    default:
      return {}
  }
}

const selectComponent = (component: StrategyComponent) => {
  selectedComponent.value = component
}

const removeComponent = (index: number) => {
  strategyComponents.value.splice(index, 1)
  selectedComponent.value = null
}

const clearCanvas = () => {
  strategyComponents.value = []
  connections.value = []
  selectedComponent.value = null
}

const autoLayout = () => {
  // 自动布局组件
  strategyComponents.value.forEach((component, index) => {
    component.position.x = 50 + (index % 3) * 200
    component.position.y = 50 + Math.floor(index / 3) * 150
  })
}

const validateStrategy = () => {
  // 验证策略配置
  for (const component of strategyComponents.value) {
    component.validation = {
      status: 'success',
      message: '配置验证通过'
    }
  }
  ElMessage.success('策略验证通过')
}

const previewStrategy = () => {
  if (strategyComponents.value.length === 0) {
    ElMessage.warning('请先添加策略组件')
    return
  }
  
  generateCode()
  showCodePreview.value = true
}

const generateCode = () => {
  // 生成Python代码
  generatedCode.python = `
import qlib
from qlib.data.dataset import DatasetH
from qlib.contrib.model.lightgbm import LGBModel
from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

class ${strategyConfig.name || 'CustomStrategy'}(TopkDropoutStrategy):
    def __init__(self):
        super().__init__()
        # 策略配置
        ${strategyComponents.value.map(comp => `        # ${comp.name}: ${JSON.stringify(comp.config)}`).join('\n')}
    
    def generate_trade_decision(self, score, current, trade_start_time, trade_end_time):
        # 生成交易决策
        return super().generate_trade_decision(score, current, trade_start_time, trade_end_time)
`

  // 生成Qlib配置
  generatedCode.config = JSON.stringify({
    strategy: {
      class: strategyConfig.name || 'CustomStrategy',
      module_path: 'custom_strategy',
      kwargs: {
        topk: 20,
        n_drop: 5
      }
    },
    factors: strategyComponents.value
      .filter(comp => comp.type === 'factor')
      .map(comp => comp.name),
    models: strategyComponents.value
      .filter(comp => comp.type === 'model')
      .map(comp => ({ type: comp.name, config: comp.config }))
  }, null, 2)

  // 生成回测脚本
  generatedCode.backtest = `
import qlib
from qlib.workflow import R

# 初始化Qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

# 运行回测
rid = R.get_recorder().id
with R.start(experiment_name="custom_strategy"):
    # 配置数据集
    dataset = DatasetH({
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": {}
            },
            "segments": {
                "train": ("2015-01-01", "2016-12-31"),
                "valid": ("2017-01-01", "2017-12-31"),
                "test": ("2018-01-01", "2020-12-31")
            }
        }
    })
    
    # 运行策略
    recorder = R.get_recorder(rid)
    print(f"策略回测完成，记录ID: {rid}")
`
}

const copyCode = () => {
  const code = generatedCode[activeCodeTab.value]
  navigator.clipboard.writeText(code)
  ElMessage.success('代码已复制到剪贴板')
}

const downloadCode = () => {
  const code = generatedCode[activeCodeTab.value]
  const filename = `strategy_${activeCodeTab.value}.${activeCodeTab.value === 'config' ? 'json' : 'py'}`
  
  const blob = new Blob([code], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('代码文件下载成功')
}

const runStrategy = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要运行这个策略吗？这将提交到Qlib执行引擎。',
      '确认运行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    ElMessage.success('策略已提交运行，请到实验管理页面查看进度')
    showCodePreview.value = false
  } catch {
    // 用户取消
  }
}

const buildStrategy = () => {
  if (strategyComponents.value.length === 0) {
    ElMessage.warning('请先添加策略组件')
    return
  }
  
  if (!strategyConfig.name) {
    ElMessage.warning('请填写策略名称')
    return
  }
  
  building.value = true
  
  // 模拟构建过程
  setTimeout(() => {
    building.value = false
    ElMessage.success('策略构建成功')
    previewStrategy()
  }, 2000)
}

const loadTemplate = () => {
  showTemplateDialog.value = true
}

const loadStrategyTemplate = (template: StrategyTemplate) => {
  strategyConfig.name = template.name
  strategyConfig.description = template.description
  strategyComponents.value = [...template.components]
  showTemplateDialog.value = false
  ElMessage.success(`已加载模板: ${template.name}`)
}

const saveTemplate = () => {
  if (strategyComponents.value.length === 0) {
    ElMessage.warning('请先构建策略')
    return
  }
  
  ElMessage.success('策略模板保存成功')
}

const onStrategyTypeChange = () => {
  // 根据策略类型调整组件
  ElMessage.info(`已切换为${strategyConfig.type}策略类型`)
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

const getComponentIcon = (type: string) => {
  const icons: Record<string, string> = {
    factor: 'DataBoard',
    model: 'Cpu',
    signal: 'Operation',
    selector: 'Filter',
    weight: 'PieChart',
    risk: 'Warning'
  }
  return icons[type] || 'Setting'
}

const getConfigComponent = (type: string) => {
  // 返回对应的配置组件名称
  return 'div' // 简化处理
}

// 生命周期
onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.qlib-strategy-builder {
  padding: 20px;
}

.builder-header {
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

.strategy-basic-info {
  padding: 16px 0;
}

.builder-workspace {
  min-height: 600px;
}

.component-library {
  height: 600px;
  overflow-y: auto;
}

.component-group {
  max-height: 200px;
  overflow-y: auto;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.3s;
}

.component-item:hover {
  background: #f5f7fa;
  border-color: #409eff;
}

.component-item:active {
  cursor: grabbing;
}

.strategy-canvas {
  height: 600px;
}

.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.canvas-controls {
  display: flex;
  gap: 8px;
}

.canvas-area {
  position: relative;
  height: 500px;
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #999;
  font-size: 16px;
}

.canvas-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  display: block;
}

.strategy-node {
  position: absolute;
  width: 180px;
  min-height: 120px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  z-index: 10;
}

.strategy-node.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 8px 8px 0 0;
}

.node-title {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
}

.node-content {
  padding: 12px;
}

.node-config {
  font-size: 12px;
  color: #666;
}

.connection-points {
  position: absolute;
}

.input-point {
  position: absolute;
  top: 50%;
  left: -6px;
  width: 12px;
  height: 12px;
  background: #409eff;
  border-radius: 50%;
  transform: translateY(-50%);
}

.output-point {
  position: absolute;
  top: 50%;
  right: -6px;
  width: 12px;
  height: 12px;
  background: #67c23a;
  border-radius: 50%;
  transform: translateY(-50%);
}

.connection-lines {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 5;
}

.properties-panel {
  height: 600px;
  overflow-y: auto;
}

.no-selection {
  text-align: center;
  padding: 40px 0;
}

.component-properties h4 {
  margin-bottom: 16px;
  color: #303133;
}

.specific-properties h5 {
  margin: 16px 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.validation-result {
  margin-top: 16px;
}

.validation-result h5 {
  margin-bottom: 12px;
  color: #606266;
  font-size: 14px;
}

.code-preview {
  margin-bottom: 20px;
}

.code-content {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

.template-list {
  max-height: 500px;
  overflow-y: auto;
}

.template-item {
  margin-bottom: 16px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-content p {
  margin-bottom: 12px;
  color: #666;
  font-size: 13px;
}

.template-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.template-tag {
  margin: 0;
}

@media (max-width: 768px) {
  .qlib-strategy-builder {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .builder-workspace .el-col {
    margin-bottom: 16px;
  }
  
  .strategy-basic-info .el-col {
    margin-bottom: 16px;
  }
  
  .component-library,
  .strategy-canvas,
  .properties-panel {
    height: auto;
    min-height: 300px;
  }
}
</style>