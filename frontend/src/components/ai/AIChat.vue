<template>
  <div class="ai-chat-container">
    <!-- 聊天窗口 -->
    <div class="chat-window" ref="chatWindow">
      <div class="chat-header">
        <el-icon><Robot /></el-icon>
        <span class="title">AI因子助手</span>
        <div class="chat-status">
          <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'" size="small">
            {{ connectionStatus === 'connected' ? '在线' : '离线' }}
          </el-tag>
        </div>
      </div>
      
      <div class="chat-messages" ref="messagesContainer">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="ai-avatar">
            <el-icon><Robot /></el-icon>
          </div>
          <div class="welcome-content">
            <h3>👋 欢迎使用AI因子助手</h3>
            <p>我可以帮助您：</p>
            <ul>
              <li>🧮 根据投资逻辑生成因子表达式</li>
              <li>📊 解读因子的投资含义</li>
              <li>🔍 预测因子效果和适用场景</li>
              <li>💡 提供因子优化建议</li>
            </ul>
            <div class="quick-actions">
              <span class="quick-action-label">快速开始：</span>
              <el-button 
                v-for="suggestion in quickSuggestions" 
                :key="suggestion"
                size="small" 
                type="primary" 
                link
                @click="sendMessage(suggestion)"
              >
                {{ suggestion }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 聊天消息列表 -->
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'"><User /></el-icon>
            <el-icon v-else><Robot /></el-icon>
          </div>
          
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            
            <!-- 因子表达式展示 -->
            <div v-if="message.factorExpression" class="factor-expression">
              <div class="expression-header">
                <el-icon><MagicStick /></el-icon>
                <span>生成的因子表达式</span>
              </div>
              <div class="expression-code">
                <code>{{ message.factorExpression.expression }}</code>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="copyExpression(message.factorExpression.expression)"
                >
                  复制
                </el-button>
              </div>
              <div class="expression-description">
                {{ message.factorExpression.description }}
              </div>
              <div class="expression-actions">
                <el-button 
                  size="small" 
                  @click="previewFactor(message.factorExpression)"
                >
                  <el-icon><View /></el-icon>
                  预览效果
                </el-button>
                <el-button 
                  size="small" 
                  type="success"
                  @click="saveFactor(message.factorExpression)"
                >
                  <el-icon><Plus /></el-icon>
                  保存到因子库
                </el-button>
                <el-button 
                  size="small" 
                  type="primary"
                  @click="useForTraining(message.factorExpression)"
                >
                  <el-icon><Right /></el-icon>
                  直接用于训练
                </el-button>
              </div>
            </div>

            <!-- 投资逻辑解读 -->
            <div v-if="message.investmentLogic" class="investment-logic">
              <div class="logic-header">
                <el-icon><TrendCharts /></el-icon>
                <span>投资逻辑解读</span>
              </div>
              <div class="logic-content">
                <div class="logic-section">
                  <h4>核心理念</h4>
                  <p>{{ message.investmentLogic.concept }}</p>
                </div>
                <div class="logic-section">
                  <h4>适用场景</h4>
                  <el-tag 
                    v-for="scenario in message.investmentLogic.scenarios" 
                    :key="scenario" 
                    size="small"
                    class="scenario-tag"
                  >
                    {{ scenario }}
                  </el-tag>
                </div>
                <div class="logic-section">
                  <h4>预期效果</h4>
                  <p>{{ message.investmentLogic.expectedEffect }}</p>
                </div>
              </div>
            </div>

            <!-- 因子效果预测 -->
            <div v-if="message.factorPrediction" class="factor-prediction">
              <div class="prediction-header">
                <el-icon><DataAnalysis /></el-icon>
                <span>因子效果预测</span>
              </div>
              <div class="prediction-metrics">
                <div class="metric-item">
                  <span class="metric-label">预期IC</span>
                  <span class="metric-value">{{ message.factorPrediction.expectedIC }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">预期ICIR</span>
                  <span class="metric-value">{{ message.factorPrediction.expectedICIR }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">置信度</span>
                  <el-progress 
                    :percentage="message.factorPrediction.confidence" 
                    :show-text="false"
                    :stroke-width="8"
                  />
                  <span class="confidence-text">{{ message.factorPrediction.confidence }}%</span>
                </div>
              </div>
              <div class="prediction-notes">
                <p><strong>注意：</strong>{{ message.factorPrediction.notes }}</p>
              </div>
            </div>
            
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="isTyping" class="typing-indicator">
          <div class="message-avatar">
            <el-icon><Robot /></el-icon>
          </div>
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-toolbar">
        <el-button 
          v-for="template in inputTemplates" 
          :key="template.label"
          size="small" 
          type="primary" 
          link
          @click="fillTemplate(template.content)"
        >
          {{ template.label }}
        </el-button>
      </div>
      
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="描述您的投资想法，比如：我想要一个反映股票动量的因子..."
          @keydown.ctrl.enter="sendMessage()"
          :disabled="isLoading"
        />
        <div class="input-actions">
          <el-button 
            type="primary" 
            @click="sendMessage()"
            :loading="isLoading"
            :disabled="!inputMessage.trim()"
          >
            <el-icon><Position /></el-icon>
            发送
          </el-button>
          <el-button @click="clearChat()">
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
      </div>
    </div>

    <!-- 因子预览对话框 -->
    <el-dialog 
      v-model="previewDialogVisible" 
      title="因子效果预览" 
      width="80%"
      :before-close="closePreviewDialog"
    >
      <div v-if="previewFactor" class="factor-preview">
        <div class="preview-header">
          <h3>{{ previewFactorData?.name }}</h3>
          <code class="expression">{{ previewFactorData?.expression }}</code>
        </div>
        
        <el-tabs v-model="previewTab">
          <el-tab-pane label="历史回测" name="backtest">
            <div class="backtest-chart">
              <!-- 这里应该集成图表组件显示回测结果 -->
              <div class="chart-placeholder">
                <el-icon><TrendCharts /></el-icon>
                <p>历史回测图表</p>
                <p class="chart-description">展示因子在历史数据上的表现</p>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="统计指标" name="statistics">
            <div class="statistics-grid">
              <div class="stat-card">
                <div class="stat-label">信息系数 (IC)</div>
                <div class="stat-value">0.068</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">信息比率 (ICIR)</div>
                <div class="stat-value">1.24</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">年化收益</div>
                <div class="stat-value">12.5%</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">最大回撤</div>
                <div class="stat-value">-8.2%</div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="分布分析" name="distribution">
            <div class="distribution-chart">
              <div class="chart-placeholder">
                <el-icon><Histogram /></el-icon>
                <p>因子值分布图</p>
                <p class="chart-description">展示因子值在不同股票上的分布情况</p>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <el-button @click="closePreviewDialog()">关闭</el-button>
        <el-button type="success" @click="saveFactor(previewFactorData)">
          保存到因子库
        </el-button>
        <el-button type="primary" @click="useForTraining(previewFactorData)">
          直接用于训练
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Robot,
  User,
  MagicStick,
  View,
  Plus,
  Right,
  TrendCharts,
  DataAnalysis,
  Position,
  Delete,
  Histogram
} from '@element-plus/icons-vue'

// 接口定义
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  factorExpression?: {
    expression: string
    description: string
    name: string
    confidence: number
  }
  investmentLogic?: {
    concept: string
    scenarios: string[]
    expectedEffect: string
  }
  factorPrediction?: {
    expectedIC: string
    expectedICIR: string
    confidence: number
    notes: string
  }
}

// 响应式数据
const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const isTyping = ref(false)
const connectionStatus = ref<'connected' | 'disconnected'>('connected')
const chatWindow = ref<HTMLElement>()
const messagesContainer = ref<HTMLElement>()

// 预览相关
const previewDialogVisible = ref(false)
const previewFactorData = ref<any>(null)
const previewTab = ref('backtest')

// 快速建议
const quickSuggestions = [
  '生成一个动量因子',
  '创建价值投资因子',
  '设计反转策略因子'
]

// 输入模板
const inputTemplates = [
  { label: '动量因子', content: '我需要一个反映股票价格动量的因子，关注最近20天的价格趋势' },
  { label: '价值因子', content: '帮我设计一个价值投资因子，基于市盈率和市净率指标' },
  { label: '成交量因子', content: '创建一个基于成交量异动的因子，捕捉资金关注度变化' },
  { label: '技术指标', content: '生成一个技术分析因子，结合RSI和MACD等经典指标' }
]

// 方法
const sendMessage = async (message?: string) => {
  const text = message || inputMessage.value.trim()
  if (!text) return

  // 添加用户消息
  const userMessage: ChatMessage = {
    role: 'user',
    content: text,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  
  // 清空输入
  if (!message) {
    inputMessage.value = ''
  }
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 显示正在输入
  isTyping.value = true
  isLoading.value = true
  
  try {
    // 模拟AI响应
    await simulateAIResponse(text)
  } catch (error) {
    ElMessage.error('AI响应出错，请稍后重试')
  } finally {
    isTyping.value = false
    isLoading.value = false
  }
}

const simulateAIResponse = async (userInput: string) => {
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  const lowerInput = userInput.toLowerCase()
  let response: ChatMessage
  
  if (lowerInput.includes('动量') || lowerInput.includes('趋势')) {
    response = {
      role: 'assistant',
      content: '我为您生成了一个20日动量因子，该因子通过比较当前价格与20天前价格来捕捉股票的动量特征。',
      timestamp: new Date(),
      factorExpression: {
        expression: '($close / Ref($close, 20)) - 1',
        description: '计算当前收盘价相对于20天前收盘价的变化率，反映股票的短期动量',
        name: '20日动量因子',
        confidence: 85
      },
      investmentLogic: {
        concept: '动量效应认为表现强势的股票往往会继续强势，表现弱势的股票往往会继续弱势',
        scenarios: ['牛市行情', '趋势明确', '流动性充裕'],
        expectedEffect: '在趋势行情中能够有效捕捉超额收益，但在震荡市中可能出现频繁止损'
      },
      factorPrediction: {
        expectedIC: '0.065 ~ 0.085',
        expectedICIR: '1.2 ~ 1.6',
        confidence: 75,
        notes: '该预测基于历史数据分析，实际效果可能因市场环境变化而有所差异'
      }
    }
  } else if (lowerInput.includes('价值') || lowerInput.includes('市盈率') || lowerInput.includes('市净率')) {
    response = {
      role: 'assistant',
      content: '为您设计了一个综合价值因子，结合市盈率和市净率指标来评估股票的价值投资吸引力。',
      timestamp: new Date(),
      factorExpression: {
        expression: '1 / ($pe_ratio * $pb_ratio)',
        description: '市盈率和市净率的倒数乘积，数值越大表示估值越便宜',
        name: '综合价值因子',
        confidence: 90
      },
      investmentLogic: {
        concept: '价值投资理念认为市场会低估优质公司，这些股票具有均值回归的潜力',
        scenarios: ['熊市底部', '市场恐慌', '价值回归'],
        expectedEffect: '长期持有能够获得稳定的超额收益，但可能需要较长的持有期才能实现'
      },
      factorPrediction: {
        expectedIC: '0.045 ~ 0.065',
        expectedICIR: '0.8 ~ 1.2',
        confidence: 80,
        notes: '价值因子通常在市场底部表现更好，需要结合市场周期进行分析'
      }
    }
  } else if (lowerInput.includes('成交量')) {
    response = {
      role: 'assistant',
      content: '创建了一个成交量异动因子，通过比较当前成交量与历史平均水平来识别资金关注度的变化。',
      timestamp: new Date(),
      factorExpression: {
        expression: '($volume / MA($volume, 20)) - 1',
        description: '当前成交量相对于20日平均成交量的偏离程度',
        name: '成交量异动因子',
        confidence: 70
      },
      investmentLogic: {
        concept: '成交量异动往往预示着股价的重要变化，大资金的进出会留下明显的成交量痕迹',
        scenarios: ['重大事件', '政策利好', '业绩公告'],
        expectedEffect: '能够捕捉短期的价格波动机会，但需要及时止盈止损'
      },
      factorPrediction: {
        expectedIC: '0.035 ~ 0.055',
        expectedICIR: '0.6 ~ 1.0',
        confidence: 65,
        notes: '成交量因子的有效性存在一定的时间衰减，建议结合其他因子使用'
      }
    }
  } else {
    response = {
      role: 'assistant',
      content: '我理解您的需求，让我为您生成一个通用的多因子组合。这个因子结合了动量、价值和质量等多个维度。',
      timestamp: new Date(),
      factorExpression: {
        expression: 'Rank(($close / Ref($close, 20)) - 1) + Rank(1 / $pe_ratio) + Rank($roe)',
        description: '综合动量、价值和质量三个维度的排序因子',
        name: '多因子综合评分',
        confidence: 78
      },
      investmentLogic: {
        concept: '多因子模型通过结合不同类型的因子来提高选股的稳健性和有效性',
        scenarios: ['各种市场环境', '长期投资', '风险分散'],
        expectedEffect: '相比单一因子更加稳定，能够在不同市场环境下保持一定的有效性'
      },
      factorPrediction: {
        expectedIC: '0.055 ~ 0.075',
        expectedICIR: '1.0 ~ 1.4',
        confidence: 82,
        notes: '多因子组合的效果通常更加稳定，但需要定期调整各因子的权重'
      }
    }
  }
  
  messages.value.push(response)
  await nextTick()
  scrollToBottom()
}

const formatMessage = (content: string) => {
  // 简单的文本格式化，可以扩展支持更多格式
  return content.replace(/\n/g, '<br>')
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const copyExpression = async (expression: string) => {
  try {
    await navigator.clipboard.writeText(expression)
    ElMessage.success('因子表达式已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const previewFactor = (factorData: any) => {
  previewFactorData.value = factorData
  previewDialogVisible.value = true
}

const closePreviewDialog = () => {
  previewDialogVisible.value = false
  previewFactorData.value = null
  previewTab.value = 'backtest'
}

const saveFactor = async (factorData: any) => {
  try {
    // 这里应该调用API保存因子到库
    ElMessage.success(`因子 "${factorData.name}" 已保存到因子库`)
    closePreviewDialog()
  } catch {
    ElMessage.error('保存因子失败')
  }
}

const useForTraining = async (factorData: any) => {
  try {
    // 这里应该跳转到模型训练页面并传递因子信息
    ElMessage.success(`因子 "${factorData.name}" 已添加到训练配置`)
    closePreviewDialog()
  } catch {
    ElMessage.error('添加到训练失败')
  }
}

const fillTemplate = (template: string) => {
  inputMessage.value = template
}

const clearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有聊天记录吗？',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    messages.value = []
  } catch {
    // 用户取消
  }
}

// 生命周期
onMounted(() => {
  // 初始化连接状态检查
  // 这里可以添加与AI服务的连接检查逻辑
})
</script>

<style scoped lang="scss">
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .el-icon {
    font-size: 20px;
    color: #409eff;
    margin-right: 8px;
  }

  .title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    flex: 1;
  }

  .chat-status {
    margin-left: auto;
  }
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.welcome-message {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24px;

  .ai-avatar {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #409eff, #67c23a);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    flex-shrink: 0;

    .el-icon {
      color: white;
      font-size: 20px;
    }
  }

  .welcome-content {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    max-width: 80%;

    h3 {
      margin: 0 0 12px 0;
      color: #303133;
      font-size: 18px;
    }

    p {
      margin: 8px 0;
      color: #606266;
    }

    ul {
      margin: 12px 0;
      padding-left: 20px;
      color: #606266;

      li {
        margin: 6px 0;
      }
    }

    .quick-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #e4e7ed;

      .quick-action-label {
        color: #909399;
        font-size: 14px;
        margin-right: 12px;
      }

      .el-button {
        margin: 4px;
      }
    }
  }
}

.message {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24px;

  &.user-message {
    flex-direction: row-reverse;

    .message-content {
      background: #409eff;
      color: white;
      margin-left: 60px;
      margin-right: 12px;
    }

    .message-avatar {
      margin-left: 12px;
      margin-right: 0;
    }
  }

  &.ai-message {
    .message-content {
      background: white;
      margin-right: 60px;
      margin-left: 12px;
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;

  .el-icon {
    font-size: 18px;
  }

  .user-message & {
    background: #409eff;
    color: white;
  }

  .ai-message & {
    background: linear-gradient(135deg, #409eff, #67c23a);
    color: white;
  }
}

.message-content {
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 70%;
  word-wrap: break-word;
}

.message-text {
  margin-bottom: 8px;
  line-height: 1.6;
}

.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;

  .ai-message & {
    color: #c0c4cc;
  }
}

.factor-expression {
  margin-top: 16px;
  padding: 16px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;

  .expression-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-weight: 600;
    color: #1890ff;

    .el-icon {
      margin-right: 6px;
    }
  }

  .expression-code {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;

    code {
      flex: 1;
      background: #fff;
      padding: 8px 12px;
      border-radius: 4px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 14px;
      border: 1px solid #d9d9d9;
    }
  }

  .expression-description {
    color: #666;
    font-size: 14px;
    margin-bottom: 12px;
  }

  .expression-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;

    .el-button {
      font-size: 12px;
    }
  }
}

.investment-logic {
  margin-top: 16px;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;

  .logic-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-weight: 600;
    color: #52c41a;

    .el-icon {
      margin-right: 6px;
    }
  }

  .logic-content {
    .logic-section {
      margin-bottom: 12px;

      h4 {
        margin: 0 0 6px 0;
        font-size: 14px;
        color: #262626;
      }

      p {
        margin: 0;
        color: #595959;
        font-size: 14px;
        line-height: 1.5;
      }

      .scenario-tag {
        margin: 2px 4px 2px 0;
      }
    }
  }
}

.factor-prediction {
  margin-top: 16px;
  padding: 16px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;

  .prediction-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-weight: 600;
    color: #fa8c16;

    .el-icon {
      margin-right: 6px;
    }
  }

  .prediction-metrics {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    flex-wrap: wrap;

    .metric-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 80px;

      .metric-label {
        font-size: 12px;
        color: #8c8c8c;
        margin-bottom: 4px;
      }

      .metric-value {
        font-size: 14px;
        font-weight: 600;
        color: #262626;
      }

      .el-progress {
        width: 60px;
        margin: 4px 0;
      }

      .confidence-text {
        font-size: 12px;
        color: #8c8c8c;
      }
    }
  }

  .prediction-notes {
    font-size: 12px;
    color: #8c8c8c;
    font-style: italic;
  }
}

.typing-indicator {
  display: flex;
  align-items: center;
  margin-bottom: 24px;

  .message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #409eff, #67c23a);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;

    .el-icon {
      color: white;
      font-size: 18px;
    }
  }

  .typing-dots {
    display: flex;
    align-items: center;
    gap: 4px;
    background: white;
    padding: 12px 16px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    span {
      width: 6px;
      height: 6px;
      background: #c0c4cc;
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out;

      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
      &:nth-child(3) { animation-delay: 0s; }
    }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input-area {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 20px;
}

.input-toolbar {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;

  .el-button {
    margin-right: 8px;
    margin-bottom: 4px;
  }
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;

  .el-textarea {
    flex: 1;
  }

  .input-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

// 预览对话框样式
.factor-preview {
  .preview-header {
    margin-bottom: 20px;
    text-align: center;

    h3 {
      margin: 0 0 8px 0;
      color: #303133;
    }

    .expression {
      background: #f5f7fa;
      padding: 8px 16px;
      border-radius: 4px;
      font-family: monospace;
      color: #606266;
    }
  }

  .chart-placeholder {
    height: 300px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fafafa;
    border: 2px dashed #d9d9d9;
    border-radius: 8px;
    color: #8c8c8c;

    .el-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    p {
      margin: 4px 0;
      font-size: 14px;
    }

    .chart-description {
      font-size: 12px;
      color: #bfbfbf;
    }
  }

  .statistics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;

    .stat-card {
      background: #fafafa;
      padding: 20px;
      border-radius: 8px;
      text-align: center;

      .stat-label {
        font-size: 14px;
        color: #8c8c8c;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #262626;
      }
    }
  }
}
</style>