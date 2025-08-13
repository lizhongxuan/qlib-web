<template>
  <div class="result-interpretation-assistant">
    <div class="assistant-header">
      <h3>
        <el-icon><ChatDotRound /></el-icon>
        结果解读助手
      </h3>
      <el-button @click="toggleAssistant" :type="isActive ? 'danger' : 'primary'">
        {{ isActive ? '关闭助手' : '启动助手' }}
      </el-button>
    </div>

    <div v-if="isActive" class="assistant-content">
      <!-- AI解读面板 -->
      <el-card class="interpretation-panel">
        <template #header>
          <div class="panel-header">
            <h4>智能解读</h4>
            <el-tag type="success">AI驱动</el-tag>
          </div>
        </template>
        
        <div class="interpretation-content">
          <div class="ai-summary">
            <h5>策略表现总结</h5>
            <div class="summary-text">
              <p>{{ aiSummary.overview }}</p>
              <el-divider />
              <div class="key-points">
                <div v-for="point in aiSummary.keyPoints" :key="point.id" class="key-point">
                  <el-icon :style="{ color: point.color }">
                    <component :is="point.icon" />
                  </el-icon>
                  <span>{{ point.text }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="interpretation-tabs">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="优势分析" name="strengths">
                <div class="strengths-analysis">
                  <div v-for="strength in interpretations.strengths" :key="strength.id" class="strength-item">
                    <h6>{{ strength.title }}</h6>
                    <p>{{ strength.description }}</p>
                    <div class="metrics">
                      <el-tag v-for="metric in strength.metrics" :key="metric" size="small" type="success">
                        {{ metric }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="风险提示" name="risks">
                <div class="risks-analysis">
                  <div v-for="risk in interpretations.risks" :key="risk.id" class="risk-item">
                    <h6>{{ risk.title }}</h6>
                    <p>{{ risk.description }}</p>
                    <el-progress
                      :percentage="risk.severity"
                      :color="getRiskColor(risk.severity)"
                      :stroke-width="6"
                    />
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="改进建议" name="suggestions">
                <div class="suggestions-list">
                  <div v-for="suggestion in interpretations.suggestions" :key="suggestion.id" class="suggestion-item">
                    <div class="suggestion-header">
                      <h6>{{ suggestion.title }}</h6>
                      <el-tag :type="getPriorityType(suggestion.priority)">
                        {{ suggestion.priority }}
                      </el-tag>
                    </div>
                    <p>{{ suggestion.description }}</p>
                    <div class="suggestion-actions">
                      <el-button size="small" type="primary" @click="applySuggestion(suggestion)">
                        应用建议
                      </el-button>
                      <el-button size="small" @click="learnMore(suggestion)">
                        了解更多
                      </el-button>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </el-card>

      <!-- 交互式问答 -->
      <el-card class="qa-panel">
        <template #header>
          <h4>智能问答</h4>
        </template>
        
        <div class="qa-content">
          <div class="chat-messages" ref="chatMessages">
            <div v-for="message in chatMessages" :key="message.id" class="message-item">
              <div class="message" :class="message.type">
                <div class="message-avatar">
                  <el-icon v-if="message.type === 'user'">
                    <User />
                  </el-icon>
                  <el-icon v-else>
                    <ChatDotRound />
                  </el-icon>
                </div>
                <div class="message-content">
                  <div class="message-text">{{ message.content }}</div>
                  <div class="message-time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>
            </div>
            <div v-if="isThinking" class="message-item">
              <div class="message assistant">
                <div class="message-avatar">
                  <el-icon><ChatDotRound /></el-icon>
                </div>
                <div class="message-content">
                  <div class="thinking-indicator">
                    <span>AI正在分析...</span>
                    <el-icon class="is-loading"><Loading /></el-icon>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="quick-questions">
            <h5>常见问题</h5>
            <div class="question-buttons">
              <el-button
                v-for="question in quickQuestions"
                :key="question.id"
                size="small"
                @click="askQuestion(question.text)"
              >
                {{ question.text }}
              </el-button>
            </div>
          </div>

          <div class="chat-input">
            <el-input
              v-model="userQuestion"
              placeholder="请输入您的问题..."
              @keyup.enter="sendQuestion"
            >
              <template #append>
                <el-button @click="sendQuestion" :loading="isThinking">
                  发送
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound, User, Loading, SuccessFilled, WarningFilled, InfoFilled
} from '@element-plus/icons-vue'

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface QuickQuestion {
  id: string
  text: string
}

const isActive = ref(false)
const activeTab = ref('strengths')
const userQuestion = ref('')
const isThinking = ref(false)
const chatMessages = ref<ChatMessage[]>([])

const aiSummary = reactive({
  overview: '基于回测结果分析，该策略在风险调整后收益方面表现优秀，年化收益率达到18.5%，夏普比率1.45，最大回撤控制在8.2%以内。策略具有良好的稳定性和风险控制能力。',
  keyPoints: [
    { id: '1', text: '收益稳定性好，夏普比率超过1.4', icon: 'SuccessFilled', color: '#67c23a' },
    { id: '2', text: '风险控制有效，回撤控制在10%以内', icon: 'InfoFilled', color: '#409eff' },
    { id: '3', text: '需要注意持仓集中度风险', icon: 'WarningFilled', color: '#e6a23c' }
  ]
})

const interpretations = reactive({
  strengths: [
    {
      id: '1',
      title: '优秀的风险调整收益',
      description: '策略的夏普比率达到1.45，显著超过市场平均水平，表明在承担单位风险的情况下获得了较高的超额收益。',
      metrics: ['夏普比率: 1.45', '信息比率: 0.96', '年化收益: 18.5%']
    },
    {
      id: '2',
      title: '有效的回撤控制',
      description: '最大回撤控制在8.2%，远低于同类策略的平均水平，显示了良好的风险管理能力。',
      metrics: ['最大回撤: 8.2%', 'VaR(95%): 3.8%', '下行波动率: 12.1%']
    }
  ],
  risks: [
    {
      id: '1',
      title: '持仓集中度较高',
      description: '前十大持仓占比超过60%，存在集中度风险，市场波动时可能影响策略稳定性。',
      severity: 65
    },
    {
      id: '2',
      title: '行业暴露不均衡',
      description: '在某些行业的暴露过度集中，需要关注行业轮动风险。',
      severity: 45
    }
  ],
  suggestions: [
    {
      id: '1',
      title: '优化持仓分散化',
      description: '建议将前十大持仓占比控制在50%以内，增加持仓的分散化程度。',
      priority: '高优先级'
    },
    {
      id: '2',
      title: '增加行业中性约束',
      description: '考虑添加行业中性约束条件，减少行业轮动带来的风险。',
      priority: '中优先级'
    }
  ]
})

const quickQuestions = ref<QuickQuestion[]>([
  { id: '1', text: '这个策略的主要优势是什么？' },
  { id: '2', text: '有哪些风险需要注意？' },
  { id: '3', text: '如何进一步优化策略？' },
  { id: '4', text: '策略适合什么市场环境？' }
])

const toggleAssistant = () => {
  isActive.value = !isActive.value
  if (isActive.value) {
    // 初始化欢迎消息
    chatMessages.value = [{
      id: '1',
      type: 'assistant',
      content: '您好！我是结果解读助手，可以帮您分析策略表现、解答疑问。请问有什么想了解的吗？',
      timestamp: Date.now()
    }]
  }
}

const askQuestion = (question: string) => {
  userQuestion.value = question
  sendQuestion()
}

const sendQuestion = async () => {
  if (!userQuestion.value.trim() || isThinking.value) return

  // 添加用户消息
  const userMessage: ChatMessage = {
    id: Date.now().toString(),
    type: 'user',
    content: userQuestion.value,
    timestamp: Date.now()
  }
  chatMessages.value.push(userMessage)

  const question = userQuestion.value
  userQuestion.value = ''
  isThinking.value = true

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 模拟AI思考时间
  await new Promise(resolve => setTimeout(resolve, 1500))

  // 生成AI回答
  const aiResponse = generateAIResponse(question)
  const assistantMessage: ChatMessage = {
    id: (Date.now() + 1).toString(),
    type: 'assistant',
    content: aiResponse,
    timestamp: Date.now()
  }

  chatMessages.value.push(assistantMessage)
  isThinking.value = false

  await nextTick()
  scrollToBottom()
}

const generateAIResponse = (question: string): string => {
  const responses = {
    '优势': '该策略的主要优势包括：1）优秀的夏普比率1.45，显示良好的风险调整收益；2）稳定的年化收益18.5%；3）有效的回撤控制，最大回撤仅8.2%。这些指标表明策略具有良好的风险收益特征。',
    '风险': '主要风险包括：1）持仓集中度较高，前十大持仓超过60%；2）行业暴露不均衡，存在行业轮动风险；3）在极端市场条件下的表现还需要进一步验证。建议通过增加分散化来降低这些风险。',
    '优化': '优化建议：1）控制单一持仓权重，建议不超过5%；2）添加行业中性约束；3）考虑引入宏观对冲因子；4）定期重新平衡持仓；5）设置动态止损机制。',
    '市场环境': '该策略在震荡上涨的市场环境中表现最佳。在牛市中能够获得稳定超额收益，在震荡市中风险控制能力突出。但在极端熊市中需要额外的防御性措施。',
    '默认': '感谢您的问题！基于当前的回测结果，我建议您关注策略的风险收益特征。如果您有具体的指标或方面想了解，请告诉我，我可以提供更详细的分析。'
  }

  for (const [key, response] of Object.entries(responses)) {
    if (question.includes(key)) {
      return response
    }
  }
  
  return responses['默认']
}

const applySuggestion = (suggestion: any) => {
  ElMessage.success(`正在应用建议：${suggestion.title}`)
}

const learnMore = (suggestion: any) => {
  ElMessage.info(`查看详细说明：${suggestion.title}`)
}

const getRiskColor = (severity: number) => {
  if (severity >= 70) return '#f56c6c'
  if (severity >= 40) return '#e6a23c'
  return '#67c23a'
}

const getPriorityType = (priority: string) => {
  if (priority.includes('高')) return 'danger'
  if (priority.includes('中')) return 'warning'
  return 'info'
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

const scrollToBottom = () => {
  const chatContainer = document.querySelector('.chat-messages')
  if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight
  }
}
</script>

<style scoped lang="scss">
.result-interpretation-assistant {
  .assistant-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      color: var(--el-text-color-primary);
    }
  }

  .assistant-content {
    .interpretation-panel {
      margin-bottom: 24px;

      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .ai-summary {
        margin-bottom: 24px;

        .summary-text {
          padding: 16px;
          background-color: var(--el-color-info-light-9);
          border-radius: 8px;
          border-left: 4px solid var(--el-color-primary);

          .key-points {
            .key-point {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 8px;
              font-size: 14px;
            }
          }
        }
      }

      .strengths-analysis,
      .risks-analysis,
      .suggestions-list {
        .strength-item,
        .risk-item,
        .suggestion-item {
          margin-bottom: 16px;
          padding: 16px;
          border: 1px solid var(--el-border-color);
          border-radius: 8px;

          h6 {
            margin: 0 0 8px 0;
            color: var(--el-text-color-primary);
          }

          p {
            margin: 0 0 12px 0;
            color: var(--el-text-color-regular);
            line-height: 1.5;
          }
        }

        .suggestion-item {
          .suggestion-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }

          .suggestion-actions {
            display: flex;
            gap: 8px;
          }
        }
      }
    }

    .qa-panel {
      .qa-content {
        .chat-messages {
          height: 300px;
          overflow-y: auto;
          margin-bottom: 16px;
          padding: 12px;
          border: 1px solid var(--el-border-color);
          border-radius: 8px;
          background-color: var(--el-color-info-light-9);

          .message-item {
            margin-bottom: 16px;

            .message {
              display: flex;
              gap: 12px;

              &.user {
                flex-direction: row-reverse;

                .message-content {
                  text-align: right;
                }

                .message-text {
                  background-color: var(--el-color-primary);
                  color: white;
                }
              }

              &.assistant {
                .message-text {
                  background-color: white;
                  border: 1px solid var(--el-border-color);
                }
              }

              .message-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background-color: var(--el-color-primary-light-8);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
              }

              .message-content {
                flex: 1;
                max-width: 70%;

                .message-text {
                  padding: 12px 16px;
                  border-radius: 16px;
                  line-height: 1.5;
                  word-break: break-word;
                }

                .message-time {
                  font-size: 12px;
                  color: var(--el-text-color-placeholder);
                  margin-top: 4px;
                }

                .thinking-indicator {
                  display: flex;
                  align-items: center;
                  gap: 8px;
                  padding: 12px 16px;
                  background-color: white;
                  border: 1px solid var(--el-border-color);
                  border-radius: 16px;
                  color: var(--el-text-color-regular);
                }
              }
            }
          }
        }

        .quick-questions {
          margin-bottom: 16px;

          h5 {
            margin: 0 0 8px 0;
            color: var(--el-text-color-primary);
          }

          .question-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .result-interpretation-assistant {
    .assistant-header {
      flex-direction: column;
      gap: 16px;
      align-items: flex-start;
    }

    .qa-content {
      .chat-messages {
        height: 250px;
      }

      .quick-questions {
        .question-buttons {
          flex-direction: column;

          .el-button {
            width: 100%;
            justify-content: flex-start;
          }
        }
      }
    }
  }
}
</style>