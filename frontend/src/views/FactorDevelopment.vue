<template>
  <div class="factor-development-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Calculator /></el-icon>
        因子开发中心
      </h1>
      <p class="page-subtitle">使用AI助手或手动创建量化投资因子表达式</p>
    </div>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" type="card" class="factor-tabs">
      <el-tab-pane label="AI因子助手" name="ai-assistant">
        <AIFactorAssistant 
          @factor-generated="handleFactorGenerated"
          @save-to-library="handleSaveToLibrary"
        />
      </el-tab-pane>
      
      <el-tab-pane label="手动编辑" name="manual-editor">
        <FactorEditor 
          v-model="currentFactor"
          @validate="handleFactorValidation"
          @save="handleSaveFactor"
        />
      </el-tab-pane>
      
      <el-tab-pane label="因子库" name="factor-library">
        <FactorLibrary 
          @edit-factor="handleEditFactor"
          @test-factor="handleTestFactor"
          @use-factor="handleUseFactor"
        />
      </el-tab-pane>
      
      <el-tab-pane label="因子测试" name="factor-testing">
        <FactorValidation 
          :factor="testingFactor"
          @test-complete="handleTestComplete"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 因子预览面板 -->
    <el-drawer
      v-model="showPreview"
      title="因子效果预览"
      direction="rtl"
      size="600px"
    >
      <FactorPreview 
        :factor="previewFactor"
        @close="showPreview = false"
      />
    </el-drawer>

    <!-- 快速操作工具栏 -->
    <div class="quick-actions">
      <el-button 
        type="primary" 
        @click="startTrainingWithFactors"
        :disabled="selectedFactors.length === 0"
      >
        <el-icon><Cpu /></el-icon>
        使用选中因子开始训练 ({{ selectedFactors.length }})
      </el-button>
      
      <el-button 
        type="success" 
        @click="exportFactors"
        :disabled="selectedFactors.length === 0"
      >
        <el-icon><Download /></el-icon>
        导出因子库
      </el-button>
      
      <el-button 
        type="info" 
        @click="importFactors"
      >
        <el-icon><Upload /></el-icon>
        导入因子配置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calculator, Cpu, Download, Upload } from '@element-plus/icons-vue'

// 导入子组件
import AIFactorAssistant from '@/components/factor/AIFactorAssistant.vue'
import FactorEditor from '@/components/factor/FactorEditor.vue'
import FactorLibrary from '@/components/factor/FactorLibrary.vue'
import FactorValidation from '@/components/factor/FactorValidation.vue'
import FactorPreview from '@/components/factor/FactorPreview.vue'

// 导入类型定义
import type { FactorDefinition } from '@/types/factor'

const router = useRouter()

// 响应式数据
const activeTab = ref('ai-assistant')
const showPreview = ref(false)
const currentFactor = ref<FactorDefinition | null>(null)
const previewFactor = ref<FactorDefinition | null>(null)
const testingFactor = ref<FactorDefinition | null>(null)
const selectedFactors = ref<FactorDefinition[]>([])

// 事件处理函数
const handleFactorGenerated = (factor: FactorDefinition) => {
  currentFactor.value = factor
  previewFactor.value = factor
  showPreview.value = true
  ElMessage.success('AI成功生成因子表达式')
}

const handleSaveToLibrary = (factor: FactorDefinition) => {
  // 保存到因子库的逻辑
  ElMessage.success('因子已保存到因子库')
  // 切换到因子库标签页
  activeTab.value = 'factor-library'
}

const handleFactorValidation = (isValid: boolean, errors?: string[]) => {
  if (isValid) {
    ElMessage.success('因子表达式验证通过')
  } else {
    ElMessage.error(`因子表达式验证失败: ${errors?.join(', ')}`)
  }
}

const handleSaveFactor = (factor: FactorDefinition) => {
  // 保存因子的逻辑
  ElMessage.success('因子保存成功')
}

const handleEditFactor = (factor: FactorDefinition) => {
  currentFactor.value = factor
  activeTab.value = 'manual-editor'
}

const handleTestFactor = (factor: FactorDefinition) => {
  testingFactor.value = factor
  activeTab.value = 'factor-testing'
}

const handleUseFactor = (factors: FactorDefinition[]) => {
  selectedFactors.value = factors
}

const handleTestComplete = (result: any) => {
  ElMessage.success('因子测试完成')
  // 可以显示测试结果
}

const startTrainingWithFactors = () => {
  // 跳转到训练页面，传递选中的因子
  router.push({
    path: '/training',
    query: {
      factors: selectedFactors.value.map(f => f.id).join(',')
    }
  })
}

const exportFactors = () => {
  // 导出因子库的逻辑
  ElMessage.success('因子库导出成功')
}

const importFactors = () => {
  // 导入因子配置的逻辑
  ElMessage.info('请选择要导入的因子文件')
}

// 生命周期
onMounted(() => {
  // 初始化页面数据
})
</script>

<style scoped>
.factor-development-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

.factor-tabs {
  margin-bottom: 24px;
}

.factor-tabs :deep(.el-tabs__content) {
  min-height: 600px;
}

.quick-actions {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
}

@media (max-width: 768px) {
  .factor-development-container {
    padding: 16px;
  }
  
  .quick-actions {
    position: relative;
    bottom: auto;
    right: auto;
    margin-top: 24px;
    flex-direction: column;
  }
}
</style>