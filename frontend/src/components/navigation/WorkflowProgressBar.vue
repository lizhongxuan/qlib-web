<template>
  <div class="workflow-progress-bar">
    <div class="progress-container">
      <div class="progress-steps">
        <div
          v-for="(step, index) in workflowSteps"
          :key="step.key"
          :class="['progress-step', getStepClass(index)]"
          @click="handleStepClick(step, index)"
        >
          <div class="step-icon">
            <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
            <el-icon v-else-if="step.status === 'current'"><Loading /></el-icon>
            <el-icon v-else :class="step.icon">
              <component :is="step.icon" />
            </el-icon>
          </div>
          <div class="step-info">
            <div class="step-title">{{ step.title }}</div>
            <div v-if="step.subtitle" class="step-subtitle">{{ step.subtitle }}</div>
          </div>
        </div>
        
        <!-- 连接线 -->
        <div
          v-for="index in workflowSteps.length - 1"
          :key="`connector-${index}`"
          :class="['step-connector', getConnectorClass(index)]"
        />
      </div>
      
      <div class="progress-info">
        <div class="progress-text">
          <span>{{ currentStepTitle }}</span>
          <span class="progress-percentage">{{ progressPercentage }}%</span>
        </div>
        <el-progress 
          :percentage="progressPercentage" 
          :show-text="false" 
          :stroke-width="4"
          :color="progressColor"
        />
      </div>
    </div>
    
    <div class="workflow-actions">
      <el-button 
        v-if="canGoBack"
        size="small" 
        @click="goToPreviousStep"
      >
        <el-icon><ArrowLeft /></el-icon>
        上一步
      </el-button>
      
      <el-button 
        v-if="canGoNext"
        type="primary" 
        size="small" 
        @click="goToNextStep"
        :disabled="!currentStepCompleted"
      >
        下一步
        <el-icon><ArrowRight /></el-icon>
      </el-button>
      
      <el-button 
        v-if="showSkipOption"
        size="small" 
        text
        @click="skipCurrentStep"
      >
        跳过
      </el-button>
      
      <el-button 
        size="small" 
        text
        @click="hideWorkflowProgress"
      >
        <el-icon><Close /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { ElMessage } from 'element-plus'
import {
  Check, Loading, ArrowLeft, ArrowRight, Close,
  MagicStick, Cpu, TrendCharts, DataAnalysis, Upload
} from '@element-plus/icons-vue'

const router = useRouter()
const workflowStore = useWorkflowStore()

// 计算属性
const workflowSteps = computed(() => workflowStore.workflowSteps)
const currentStepIndex = computed(() => workflowStore.currentStepIndex)
const currentStepTitle = computed(() => workflowStore.currentStep?.title || '')
const progressPercentage = computed(() => workflowStore.progressPercentage)
const currentStepCompleted = computed(() => workflowStore.isCurrentStepCompleted)
const canGoBack = computed(() => currentStepIndex.value > 0)
const canGoNext = computed(() => currentStepIndex.value < workflowSteps.value.length - 1)
const showSkipOption = computed(() => workflowStore.currentStep?.skippable || false)

const progressColor = computed(() => {
  if (progressPercentage.value < 30) return '#e6a23c'
  if (progressPercentage.value < 70) return '#409eff'
  return '#67c23a'
})

// 方法
const getStepClass = (index: number) => {
  const step = workflowSteps.value[index]
  const classes = []
  
  if (step.status === 'completed') classes.push('completed')
  if (step.status === 'current') classes.push('current')
  if (step.status === 'pending') classes.push('pending')
  if (step.status === 'skipped') classes.push('skipped')
  if (step.optional) classes.push('optional')
  
  return classes
}

const getConnectorClass = (index: number) => {
  const currentStep = workflowSteps.value[index]
  const nextStep = workflowSteps.value[index + 1]
  
  if (currentStep.status === 'completed' && nextStep.status !== 'pending') {
    return 'completed'
  }
  if (currentStep.status === 'current') {
    return 'current'
  }
  return 'pending'
}

const handleStepClick = (step: any, index: number) => {
  if (step.status === 'completed' || step.clickable) {
    workflowStore.jumpToStep(index)
    if (step.route) {
      router.push(step.route)
    }
  }
}

const goToPreviousStep = () => {
  const prevStep = workflowStore.goToPreviousStep()
  if (prevStep && prevStep.route) {
    router.push(prevStep.route)
  }
}

const goToNextStep = () => {
  if (!currentStepCompleted.value) {
    ElMessage.warning('请完成当前步骤后再继续')
    return
  }
  
  const nextStep = workflowStore.goToNextStep()
  if (nextStep && nextStep.route) {
    router.push(nextStep.route)
  }
}

const skipCurrentStep = () => {
  workflowStore.skipCurrentStep()
  goToNextStep()
}

const hideWorkflowProgress = () => {
  workflowStore.hideWorkflowProgress()
}
</script>

<style scoped>
.workflow-progress-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #f0f8ff 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 1px solid #d4e4fd;
  margin-left: 24px;
  min-width: 600px;
}

.progress-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-steps {
  display: flex;
  align-items: center;
  position: relative;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  background: #fff;
  border: 1px solid #e4e7ed;
  z-index: 2;
}

.progress-step:hover {
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateY(-1px);
}

.progress-step.completed {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: #fff;
  border-color: #67c23a;
}

.progress-step.current {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: #fff;
  border-color: #409eff;
  box-shadow: 0 0 12px rgba(64, 158, 255, 0.3);
}

.progress-step.pending {
  background: #f5f7fa;
  color: #909399;
  cursor: default;
}

.progress-step.skipped {
  background: #f0f0f0;
  color: #c0c4cc;
  opacity: 0.6;
}

.progress-step.optional::after {
  content: '可选';
  position: absolute;
  top: -8px;
  right: -8px;
  background: #e6a23c;
  color: #fff;
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 3px;
}

.step-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.step-info {
  display: flex;
  flex-direction: column;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2;
}

.step-subtitle {
  font-size: 12px;
  opacity: 0.8;
  line-height: 1.2;
}

.step-connector {
  height: 2px;
  width: 32px;
  background: #e4e7ed;
  position: absolute;
  z-index: 1;
  transition: all 0.3s ease;
}

.step-connector.completed {
  background: #67c23a;
}

.step-connector.current {
  background: linear-gradient(to right, #409eff, #e4e7ed);
}

/* 动态计算连接线位置 */
.step-connector:nth-of-type(2) {
  left: calc(var(--step-width) - 16px);
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #606266;
}

.progress-percentage {
  font-weight: 600;
  color: #409eff;
}

.workflow-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 1000px) {
  .workflow-progress-bar {
    min-width: 400px;
    padding: 8px 16px;
  }
  
  .step-info {
    display: none;
  }
  
  .step-connector {
    width: 20px;
  }
  
  .progress-step {
    padding: 6px;
  }
}

@media (max-width: 768px) {
  .workflow-progress-bar {
    flex-direction: column;
    gap: 12px;
    min-width: unset;
    width: 100%;
  }
  
  .progress-steps {
    justify-content: center;
  }
  
  .workflow-actions {
    justify-content: center;
  }
}
</style>