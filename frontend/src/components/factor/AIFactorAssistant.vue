<template>
  <div class="ai-factor-assistant">
    <!-- AI对话界面 -->
    <div class="chat-container">
      <div class="chat-header">
        <h3>
          <el-icon><Robot /></el-icon>
          AI因子助手
        </h3>
        <p>用自然语言描述您的投资想法，AI将帮您生成专业的量化因子表达式</p>
      </div>

      <!-- 对话历史 -->
      <div class="chat-history" ref="chatHistoryRef">
        <div 
          v-for="(message, index) in chatHistory" 
          :key="index"
          :class="['message', message.type]"
        >
          <div class="message-avatar">
            <el-icon v-if="message.type === 'user'">
              <User />
            </el-icon>
            <el-icon v-else>
              <Robot />
            </el-icon>
          </div>
          
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            
            <!-- AI生成的因子信息 -->
            <div v-if="message.factor" class="factor-result">
              <el-card class="factor-card">
                <template #header>
                  <div class="factor-header">
                    <span>🧮 生成的因子表达式</span>
                    <el-button 
                      type="primary" 
                      size="small"
                      @click="previewFactor(message.factor)"
                    >
                      预览效果
                    </el-button>
                  </div>
                </template>
                
                <div class="factor-info">
                  <div class="factor-expression">
                    <strong>表达式：</strong>
                    <code>{{ message.factor.expression }}</code>
                  </div>
                  
                  <div class="factor-description">
                    <strong>说明：</strong>
                    {{ message.factor.description }}
                  </div>
                  
                  <div class="factor-metrics" v-if="message.factor.expectedPerformance">
                    <strong>预期表现：</strong>
                    <div class="metrics-grid">
                      <div class="metric">
                        <span class="metric-label">年化超额收益：</span>
                        <span class="metric-value positive">
                          +{{ message.factor.expectedPerformance.annualReturn }}%
                        </span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">信息比率：</span>
                        <span class="metric-value">
                          {{ message.factor.expectedPerformance.informationRatio }}
                        </span>
                      </div>
                      <div class="metric">
                        <span class="metric-label">胜率：</span>
                        <span class="metric-value">
                          {{ message.factor.expectedPerformance.winRate }}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="factor-actions">
                    <el-button 
                      type="success" 
                      size="small"
                      @click="saveFactor(message.factor)"
                    >
                      <el-icon><Check /></el-icon>
                      满意，保存
                    </el-button>
                    <el-button 
                      size="small"
                      @click="improveFactor(message.factor)"
                    >
                      <el-icon><Edit /></el-icon>
                      优化建议
                    </el-button>
                    <el-button 
                      size="small"
                      @click="regenerateFactor(message.text)"
                    >
                      <el-icon><Refresh /></el-icon>
                      重新生成
                    </el-button>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
        
        <!-- 加载指示器 -->
        <div v-if="isLoading" class="message ai">
          <div class="message-avatar">
            <el-icon><Robot /></el-icon>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="请描述您的投资想法，例如：我觉得最近20天涨幅大的股票还会继续涨"
          @keydown.ctrl.enter="sendMessage"
        />
        <div class="input-actions">
          <el-button 
            type="primary" 
            @click="sendMessage"
            :loading="isLoading"
            :disabled="!userInput.trim()"
          >
            <el-icon><Position /></el-icon>
            发送 (Ctrl+Enter)
          </el-button>
        </div>
      </div>
    </div>

    <!-- 快速示例 -->
    <div class="quick-examples">
      <h4>💡 投资想法示例：</h4>
      <div class="example-tags">
        <el-tag 
          v-for="example in examples" 
          :key="example"
          class="example-tag"
          @click="useExample(example)"
        >
          {{ example }}
        </el-tag>
      </div>
    </div>

    <!-- AI建议面板 -->
    <div v-if="aiSuggestions.length > 0" class="ai-suggestions">
      <h4>🔍 AI优化建议：</h4>
      <div class="suggestions-list">
        <el-card 
          v-for="(suggestion, index) in aiSuggestions" 
          :key="index"
          class="suggestion-card"
          @click="applySuggestion(suggestion)"
        >
          <div class="suggestion-content">
            <div class="suggestion-title">{{ suggestion.title }}</div>
            <div class="suggestion-desc">{{ suggestion.description }}</div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Robot, User, Check, Edit, Refresh, Position } from '@element-plus/icons-vue'
import type { FactorDefinition } from '@/types/factor'

// 事件定义
const emit = defineEmits<{
  factorGenerated: [factor: FactorDefinition]
  saveToLibrary: [factor: FactorDefinition]
}>()

// 响应式数据
const userInput = ref('')
const isLoading = ref(false)
const chatHistoryRef = ref<HTMLElement>()

interface ChatMessage {
  type: 'user' | 'ai'
  text: string
  timestamp: Date
  factor?: FactorDefinition
}

const chatHistory = ref<ChatMessage[]>([
  {
    type: 'ai',
    text: '👋 您好！我是AI因子助手。请用自然语言描述您的投资想法，我会为您生成专业的量化因子表达式。',
    timestamp: new Date()
  }
])

const examples = ref([
  '最近涨得快的股票还会继续涨',
  '便宜的股票有投资价值',
  '成交量突然放大的股票值得关注',
  '盈利增长稳定的公司更可靠',
  '技术分析中的RSI指标有用',
  '高股息收益率的股票适合长期持有'
])

const aiSuggestions = ref<Array<{
  title: string
  description: string
  factor: FactorDefinition
}>>([])

// 方法
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return
  
  const userMessage: ChatMessage = {
    type: 'user',
    text: userInput.value,
    timestamp: new Date()
  }
  
  chatHistory.value.push(userMessage)
  const inputText = userInput.value
  userInput.value = ''
  isLoading.value = true
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  try {
    // 调用AI API生成因子
    const factor = await generateFactorFromText(inputText)
    
    const aiMessage: ChatMessage = {
      type: 'ai',
      text: `我理解了您的投资想法！为您生成了一个${factor.name}。`,
      timestamp: new Date(),
      factor
    }
    
    chatHistory.value.push(aiMessage)
    emit('factorGenerated', factor)
    
    // 生成优化建议
    await generateOptimizationSuggestions(factor)
    
  } catch (error) {
    const errorMessage: ChatMessage = {
      type: 'ai',
      text: '抱歉，生成因子时出现错误。请尝试用更具体的语言描述您的投资想法。',
      timestamp: new Date()
    }
    chatHistory.value.push(errorMessage)
    ElMessage.error('AI生成因子失败，请重试')
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const generateFactorFromText = async (text: string): Promise<FactorDefinition> => {
  // 模拟AI API调用
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  // 根据输入文本生成不同的因子
  let factor: FactorDefinition
  
  if (text.includes('涨') || text.includes('动量') || text.includes('趋势')) {
    factor = {
      id: `momentum_${Date.now()}`,
      name: '20日价格动量因子',
      expression: '($close / Ref($close, 20)) - 1',
      description: '计算过去20个交易日的累计收益率，用于捕捉价格动量效应',
      category: 'technical',
      expectedPerformance: {
        annualReturn: 12.3,
        informationRatio: 1.25,
        winRate: 58.7
      },
      createdAt: new Date(),
      createdBy: 'AI Assistant'
    }
  } else if (text.includes('便宜') || text.includes('估值') || text.includes('价值')) {
    factor = {
      id: `value_${Date.now()}`,
      name: '市盈率倒数因子',
      expression: '1 / $pe_ttm',
      description: '市盈率的倒数，数值越大表示估值越便宜，价值投资潜力越大',
      category: 'fundamental',
      expectedPerformance: {
        annualReturn: 8.5,
        informationRatio: 0.95,
        winRate: 55.2
      },
      createdAt: new Date(),
      createdBy: 'AI Assistant'
    }
  } else if (text.includes('成交量') || text.includes('量')) {
    factor = {
      id: `volume_${Date.now()}`,
      name: '成交量相对强度因子',
      expression: '$volume / Mean($volume, 20)',
      description: '当日成交量与过去20日平均成交量的比值，用于识别异常交易活跃度',
      category: 'technical',
      expectedPerformance: {
        annualReturn: 9.8,
        informationRatio: 1.15,
        winRate: 52.1
      },
      createdAt: new Date(),
      createdBy: 'AI Assistant'
    }
  } else {
    // 默认生成一个综合因子
    factor = {
      id: `composite_${Date.now()}`,
      name: '综合质量因子',
      expression: '($roe + $roa) / 2 * (1 / $pe_ttm)',
      description: '结合盈利能力和估值水平的综合因子',
      category: 'composite',
      expectedPerformance: {
        annualReturn: 15.2,
        informationRatio: 1.45,
        winRate: 61.3
      },
      createdAt: new Date(),
      createdBy: 'AI Assistant'
    }
  }
  
  return factor
}

const generateOptimizationSuggestions = async (factor: FactorDefinition) => {
  // 模拟生成优化建议
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  aiSuggestions.value = [
    {
      title: '行业中性化处理',
      description: '对因子进行行业中性化处理，减少行业偏差影响',
      factor: {
        ...factor,
        expression: `demean(${factor.expression}, industry)`
      }
    },
    {
      title: '添加市值调整',
      description: '结合市值因子，提高因子稳定性',
      factor: {
        ...factor,
        expression: `${factor.expression} - 0.2 * log($market_cap)`
      }
    }
  ]
}

const useExample = (example: string) => {
  userInput.value = example
}

const previewFactor = (factor: FactorDefinition) => {
  emit('factorGenerated', factor)
}

const saveFactor = (factor: FactorDefinition) => {
  emit('saveToLibrary', factor)
  ElMessage.success('因子已保存到因子库')
}

const improveFactor = (factor: FactorDefinition) => {
  userInput.value = `请帮我优化这个因子：${factor.expression}`
}

const regenerateFactor = (originalText: string) => {
  userInput.value = originalText
  sendMessage()
}

const applySuggestion = (suggestion: any) => {
  emit('factorGenerated', suggestion.factor)
  ElMessage.success(`已应用建议：${suggestion.title}`)
}

const scrollToBottom = () => {
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.ai-factor-assistant {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 24px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.chat-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 18px;
}

.chat-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.chat-history {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  max-height: 500px;
  background: #fafafa;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #409eff;
  color: white;
}

.message.ai .message-avatar {
  background: #67c23a;
  color: white;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 12px;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.factor-result {
  margin-top: 12px;
}

.factor-card {
  border-radius: 8px;
}

.factor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.factor-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-expression code {
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  display: block;
  margin-top: 4px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #606266;
}

.metric-value {
  font-weight: 600;
  font-size: 14px;
}

.metric-value.positive {
  color: #67c23a;
}

.factor-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.input-actions {
  margin-top: 12px;
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.quick-examples {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.quick-examples h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.example-tag:hover {
  background: #409eff;
  color: white;
}

.ai-suggestions {
  margin-top: 16px;
}

.ai-suggestions h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.suggestions-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.suggestion-card {
  cursor: pointer;
  transition: all 0.3s;
}

.suggestion-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.suggestion-content {
  padding: 4px;
}

.suggestion-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.suggestion-desc {
  font-size: 12px;
  color: #606266;
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .factor-actions {
    flex-direction: column;
  }
  
  .suggestions-list {
    grid-template-columns: 1fr;
  }
}
</style>