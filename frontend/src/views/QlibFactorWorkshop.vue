<template>
  <div class="qlib-factor-workshop">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">
          <el-icon><MagicStick /></el-icon>
          Qlib因子开发工作坊
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/qlib-dashboard' }">Qlib中心</el-breadcrumb-item>
          <el-breadcrumb-item>因子工作坊</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button type="primary" @click="showAIAssistant">
            <el-icon><ChatRound /></el-icon>
            AI助手
          </el-button>
          <el-button @click="refreshFactors" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 主要内容标签页 -->
    <div class="main-content">
      <el-tabs v-model="activeTab" type="card" class="workshop-tabs">
        <!-- 因子库管理 -->
        <el-tab-pane label="因子库" name="library">
          <el-card shadow="never">
            <template #header>
              <div class="tab-header">
                <span>因子库管理</span>
                <div class="header-actions">
                  <el-input
                    v-model="searchQuery"
                    placeholder="搜索因子"
                    style="width: 200px; margin-right: 12px;"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <el-button type="primary" @click="createNewFactor">
                    <el-icon><Plus /></el-icon>
                    新建因子
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 因子统计 -->
            <div class="factor-stats">
              <div class="stat-card">
                <div class="stat-value">{{ factorStats.total }}</div>
                <div class="stat-label">总因子数</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ factorStats.builtIn }}</div>
                <div class="stat-label">内置因子</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ factorStats.custom }}</div>
                <div class="stat-label">自定义因子</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ factorStats.validated }}</div>
                <div class="stat-label">已验证因子</div>
              </div>
            </div>

            <!-- 因子列表 -->
            <el-table
              :data="filteredFactorLibrary"
              :loading="loading"
              stripe
              @selection-change="handleFactorSelection"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="display_name" label="因子名称" width="200">
                <template #default="scope">
                  <div class="factor-name">
                    <span>{{ scope.row.display_name }}</span>
                    <el-tag v-if="!scope.row.is_built_in" type="success" size="small">自定义</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="expression" label="表达式" min-width="250">
                <template #default="scope">
                  <el-tooltip :content="scope.row.expression" placement="top">
                    <code class="factor-expression">{{ scope.row.expression }}</code>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="category" label="分类" width="100">
                <template #default="scope">
                  <el-tag :type="getCategoryType(scope.row.category)" size="small">
                    {{ scope.row.category }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="validation_status" label="验证状态" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.validation_status)" size="small">
                    {{ getStatusText(scope.row.validation_status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                  <el-button-group size="small">
                    <el-button type="primary" link @click="editFactor(scope.row)">编辑</el-button>
                    <el-button type="success" link @click="validateFactor(scope.row)">验证</el-button>
                    <el-button type="warning" link @click="analyzeFactor(scope.row)">分析</el-button>
                    <el-button v-if="!scope.row.is_built_in" type="danger" link @click="deleteFactor(scope.row)">删除</el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- AI因子生成 -->
        <el-tab-pane label="AI生成" name="ai-generate">
          <el-card shadow="never">
            <div class="ai-generator">
              <div class="input-section">
                <h3>描述您的投资逻辑</h3>
                <el-input
                  v-model="aiPrompt"
                  type="textarea"
                  :rows="4"
                  placeholder="例如：我想要一个动量因子，关注过去20天的价格趋势，能够识别上涨势头强劲的股票..."
                />
                <div class="ai-actions">
                  <el-button type="primary" @click="generateAIFactor" :loading="aiLoading">
                    <el-icon><MagicStick /></el-icon>
                    生成因子
                  </el-button>
                  <el-button @click="clearAIPrompt">清空</el-button>
                </div>
              </div>

              <div v-if="aiGeneratedFactor" class="result-section">
                <h3>AI生成的因子</h3>
                <div class="generated-factor">
                  <div class="factor-info">
                    <h4>{{ aiGeneratedFactor.display_name }}</h4>
                    <p>{{ aiGeneratedFactor.description }}</p>
                    <code>{{ aiGeneratedFactor.expression }}</code>
                  </div>
                  <div class="factor-actions">
                    <el-button type="success" @click="saveAIFactor">
                      <el-icon><Check /></el-icon>
                      保存到因子库
                    </el-button>
                    <el-button type="primary" @click="testAIFactor">
                      <el-icon><DataAnalysis /></el-icon>
                      测试因子
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- 因子测试 -->
        <el-tab-pane label="因子测试" name="testing">
          <el-card shadow="never">
            <div class="factor-testing">
              <el-form :model="testForm" label-width="100px" class="test-form">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="选择因子">
                      <el-select v-model="testForm.factorName" placeholder="选择要测试的因子">
                        <el-option
                          v-for="factor in filteredFactorLibrary"
                          :key="factor.name"
                          :label="factor.display_name"
                          :value="factor.name"
                        />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="股票池">
                      <el-select v-model="testForm.universe" placeholder="选择股票池">
                        <el-option label="沪深300" value="CSI300" />
                        <el-option label="中证500" value="CSI500" />
                        <el-option label="全市场" value="ALL" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="测试时间">
                      <el-date-picker
                        v-model="testForm.timeRange"
                        type="daterange"
                        range-separator="至"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        format="YYYY-MM-DD"
                        value-format="YYYY-MM-DD"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item>
                      <el-button type="primary" @click="runFactorTest" :loading="testLoading">
                        <el-icon><PlayArrowFilled /></el-icon>
                        开始测试
                      </el-button>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>

              <!-- 测试结果 -->
              <div v-if="testResults" class="test-results">
                <h3>测试结果</h3>
                <el-row :gutter="24">
                  <el-col :span="6">
                    <div class="result-metric">
                      <div class="metric-value">{{ formatNumber(testResults.ic_mean, 4) }}</div>
                      <div class="metric-label">平均IC</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="result-metric">
                      <div class="metric-value">{{ formatNumber(testResults.information_ratio, 4) }}</div>
                      <div class="metric-label">信息比率</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="result-metric">
                      <div class="metric-value">{{ formatNumber(testResults.stability, 2) }}%</div>
                      <div class="metric-label">稳定性</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="result-metric">
                      <div class="metric-value">{{ formatNumber(testResults.turnover, 4) }}</div>
                      <div class="metric-label">换手率</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- AI助手对话框 -->
    <el-dialog v-model="aiAssistantVisible" title="AI因子助手" width="60%" @close="closeAIAssistant">
      <div class="ai-assistant">
        <div class="chat-messages" ref="chatContainer">
          <div v-for="(message, index) in chatMessages" :key="index" class="chat-message" :class="message.role">
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <el-input
            v-model="chatInput"
            placeholder="请描述您想要的因子类型..."
            @keyup.enter="sendChatMessage"
          >
            <template #append>
              <el-button type="primary" @click="sendChatMessage" :loading="chatLoading">
                发送
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  ChatRound,
  Refresh,
  Search,
  Plus,
  Check,
  DataAnalysis,
  PlayArrowFilled
} from '@element-plus/icons-vue'

// Store
import { useQlibFactorsStore } from '@/stores/qlib-factors'

const router = useRouter()
const route = useRoute()
const qlibFactorsStore = useQlibFactorsStore()

// 响应式数据
const loading = ref(false)
const activeTab = ref('library')
const searchQuery = ref('')
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiGeneratedFactor = ref<any>(null)
const testLoading = ref(false)
const testResults = ref<any>(null)
const aiAssistantVisible = ref(false)
const chatMessages = ref<any[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatContainer = ref<HTMLElement>()
const selectedFactors = ref<any[]>([])

// 表单数据
const testForm = ref({
  factorName: '',
  universe: 'CSI300',
  timeRange: [] as string[]
})

// 计算属性
const filteredFactorLibrary = computed(() => qlibFactorsStore.filteredFactorLibrary)
const factorStats = computed(() => qlibFactorsStore.factorStats)

// 方法
const formatNumber = (num: number | null | undefined, decimals = 0) => {
  if (num === null || num === undefined || isNaN(num)) return 'N/A'
  return num.toLocaleString('zh-CN', { 
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals 
  })
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

const getCategoryType = (category: string) => {
  const types: Record<string, string> = {
    'price': 'primary',
    'volume': 'success',
    'technical': 'warning',
    'fundamental': 'info',
    'custom': 'danger'
  }
  return types[category] || ''
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'valid': 'success',
    'invalid': 'danger',
    'warning': 'warning',
    'pending': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'valid': '有效',
    'invalid': '无效',
    'warning': '警告',
    'pending': '待验证'
  }
  return texts[status] || '未知'
}

const refreshFactors = async () => {
  loading.value = true
  try {
    await qlibFactorsStore.loadFactorLibrary()
    ElMessage.success('因子库刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const createNewFactor = () => {
  // 跳转到因子编辑器
  activeTab.value = 'ai-generate'
}

const handleFactorSelection = (selection: any[]) => {
  selectedFactors.value = selection
}

const editFactor = (factor: any) => {
  ElMessage.info(`编辑因子: ${factor.display_name}`)
}

const validateFactor = async (factor: any) => {
  try {
    await qlibFactorsStore.validateFactor(factor.expression)
    ElMessage.success(`因子 ${factor.display_name} 验证完成`)
  } catch (error) {
    ElMessage.error('因子验证失败')
  }
}

const analyzeFactor = (factor: any) => {
  testForm.value.factorName = factor.name
  activeTab.value = 'testing'
  ElMessage.info(`准备分析因子: ${factor.display_name}`)
}

const deleteFactor = async (factor: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除因子"${factor.display_name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await qlibFactorsStore.deleteCustomFactor(factor.name)
    ElMessage.success('因子删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const generateAIFactor = async () => {
  if (!aiPrompt.value.trim()) {
    ElMessage.warning('请输入因子描述')
    return
  }

  aiLoading.value = true
  try {
    const factor = await qlibFactorsStore.aiGenerateFactor(aiPrompt.value)
    aiGeneratedFactor.value = factor
    ElMessage.success('AI因子生成成功')
  } catch (error) {
    ElMessage.error('AI因子生成失败')
  } finally {
    aiLoading.value = false
  }
}

const clearAIPrompt = () => {
  aiPrompt.value = ''
  aiGeneratedFactor.value = null
}

const saveAIFactor = async () => {
  if (!aiGeneratedFactor.value) return
  
  try {
    await qlibFactorsStore.createCustomFactor(aiGeneratedFactor.value)
    ElMessage.success('因子已保存到因子库')
    activeTab.value = 'library'
    aiGeneratedFactor.value = null
    aiPrompt.value = ''
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const testAIFactor = () => {
  if (!aiGeneratedFactor.value) return
  
  testForm.value.factorName = aiGeneratedFactor.value.name
  activeTab.value = 'testing'
}

const runFactorTest = async () => {
  if (!testForm.value.factorName) {
    ElMessage.warning('请选择要测试的因子')
    return
  }

  testLoading.value = true
  try {
    const results = await qlibFactorsStore.analyzeFactorIC([testForm.value.factorName])
    testResults.value = results[0]
    ElMessage.success('因子测试完成')
  } catch (error) {
    ElMessage.error('因子测试失败')
  } finally {
    testLoading.value = false
  }
}

const showAIAssistant = () => {
  aiAssistantVisible.value = true
  if (chatMessages.value.length === 0) {
    chatMessages.value.push({
      role: 'assistant',
      content: '您好！我是AI因子助手，可以帮您开发各种量化因子。请告诉我您想要什么类型的因子？',
      timestamp: Date.now()
    })
  }
}

const closeAIAssistant = () => {
  aiAssistantVisible.value = false
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim()) return

  const userMessage = {
    role: 'user',
    content: chatInput.value,
    timestamp: Date.now()
  }
  chatMessages.value.push(userMessage)

  const prompt = chatInput.value
  chatInput.value = ''
  chatLoading.value = true

  try {
    // 模拟AI回复
    setTimeout(() => {
      const aiReply = {
        role: 'assistant',
        content: `基于您的描述"${prompt}"，我建议创建一个自定义因子。让我为您生成相关的表达式...`,
        timestamp: Date.now()
      }
      chatMessages.value.push(aiReply)
      chatLoading.value = false
      
      // 滚动到底部
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }, 1000)
  } catch (error) {
    chatLoading.value = false
    ElMessage.error('AI助手响应失败')
  }
}

// 生命周期
onMounted(async () => {
  // 加载因子库
  await refreshFactors()
  
  // 处理URL参数
  const action = route.query.action as string
  const instrument = route.query.instrument as string
  
  if (action && instrument) {
    switch (action) {
      case 'analyze':
        activeTab.value = 'testing'
        break
      case 'add_factor':
      case 'create_factor':
        activeTab.value = 'ai-generate'
        if (instrument) {
          aiPrompt.value = `请为股票 ${instrument} 创建一个相关的分析因子`
        }
        break
    }
  }
  
  // 设置搜索
  if (route.query.search) {
    searchQuery.value = route.query.search as string
  }
})
</script>

<style scoped lang="scss">
.qlib-factor-workshop {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  
  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    
    .toolbar-left {
      .page-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 500;
      }
    }
  }
  
  .main-content {
    flex: 1;
    padding: 24px;
    overflow: hidden;
    
    .workshop-tabs {
      height: 100%;
      display: flex;
      flex-direction: column;
      
      .el-tabs__content {
        flex: 1;
        overflow: hidden;
        
        .el-tab-pane {
          height: 100%;
          overflow-y: auto;
        }
      }
      
      .tab-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        
        .header-actions {
          display: flex;
          align-items: center;
        }
      }
      
      .factor-stats {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
        
        .stat-card {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
          
          .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #409eff;
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
      
      .factor-name {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .factor-expression {
        background: #f5f7fa;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        color: #409eff;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: inline-block;
      }
    }
  }
  
  .ai-generator {
    .input-section {
      margin-bottom: 32px;
      
      h3 {
        margin: 0 0 16px 0;
        color: #409eff;
      }
      
      .ai-actions {
        margin-top: 16px;
        display: flex;
        gap: 12px;
      }
    }
    
    .result-section {
      h3 {
        margin: 0 0 16px 0;
        color: #67c23a;
      }
      
      .generated-factor {
        background: #f0f9ff;
        border: 1px solid #b3d8ff;
        border-radius: 8px;
        padding: 20px;
        
        .factor-info {
          margin-bottom: 20px;
          
          h4 {
            margin: 0 0 8px 0;
            color: #409eff;
          }
          
          p {
            margin: 0 0 12px 0;
            color: #606266;
          }
          
          code {
            background: #e1f3d8;
            color: #67c23a;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            display: block;
          }
        }
        
        .factor-actions {
          display: flex;
          gap: 12px;
        }
      }
    }
  }
  
  .factor-testing {
    .test-form {
      margin-bottom: 32px;
    }
    
    .test-results {
      background: #fafbfc;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 20px;
      
      h3 {
        margin: 0 0 20px 0;
        color: #409eff;
      }
      
      .result-metric {
        text-align: center;
        
        .metric-value {
          font-size: 28px;
          font-weight: 600;
          color: #67c23a;
          margin-bottom: 8px;
        }
        
        .metric-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
  
  .ai-assistant {
    height: 500px;
    display: flex;
    flex-direction: column;
    
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #fafbfc;
      border-radius: 8px;
      margin-bottom: 16px;
      
      .chat-message {
        margin-bottom: 16px;
        
        &.user {
          text-align: right;
          
          .message-content {
            background: #409eff;
            color: white;
            display: inline-block;
            padding: 12px 16px;
            border-radius: 16px 16px 4px 16px;
            max-width: 80%;
          }
        }
        
        &.assistant {
          text-align: left;
          
          .message-content {
            background: white;
            color: #606266;
            display: inline-block;
            padding: 12px 16px;
            border-radius: 16px 16px 16px 4px;
            max-width: 80%;
            border: 1px solid #e4e7ed;
          }
        }
        
        .message-text {
          margin-bottom: 4px;
        }
        
        .message-time {
          font-size: 11px;
          opacity: 0.7;
        }
      }
    }
  }
}
</style>