import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface WorkflowStep {
  key: string
  title: string
  subtitle?: string
  icon: string
  route?: string
  status: 'pending' | 'current' | 'completed' | 'skipped'
  optional?: boolean
  skippable?: boolean
  clickable?: boolean
  dependencies?: string[]
  completionCriteria?: () => boolean
}

export const useWorkflowStore = defineStore('workflow', () => {
  // 状态
  const currentStepIndex = ref(0)
  const workflowType = ref<'full' | 'quick' | 'custom'>('full')
  const workflowSteps = ref<WorkflowStep[]>([])
  const stepCompletionData = ref<Record<string, any>>({})
  const workflowStartTime = ref(0)
  const isWorkflowActive = ref(false)

  // 默认工作流配置
  const defaultWorkflowSteps: WorkflowStep[] = [
    {
      key: 'factor-development',
      title: '因子开发',
      subtitle: '创建量化因子',
      icon: 'MagicStick',
      route: '/factors',
      status: 'current',
      clickable: true,
      completionCriteria: () => checkFactorDevelopmentComplete()
    },
    {
      key: 'model-training',
      title: '模型训练',
      subtitle: '训练预测模型',
      icon: 'Cpu',
      route: '/training',
      status: 'pending',
      dependencies: ['factor-development'],
      completionCriteria: () => checkModelTrainingComplete()
    },
    {
      key: 'strategy-backtest',
      title: '策略回测',
      subtitle: '测试策略表现',
      icon: 'TrendCharts',
      route: '/backtest',
      status: 'pending',
      dependencies: ['model-training'],
      completionCriteria: () => checkBacktestComplete()
    },
    {
      key: 'results-analysis',
      title: '结果分析',
      subtitle: '分析策略效果',
      icon: 'DataAnalysis',
      route: '/results',
      status: 'pending',
      dependencies: ['strategy-backtest'],
      optional: true,
      skippable: true,
      completionCriteria: () => checkResultsAnalysisComplete()
    },
    {
      key: 'strategy-deployment',
      title: '策略部署',
      subtitle: '上线交易策略',
      icon: 'Upload',
      route: '/deployment',
      status: 'pending',
      dependencies: ['strategy-backtest'],
      completionCriteria: () => checkDeploymentComplete()
    }
  ]

  // 计算属性
  const currentStep = computed(() => {
    return workflowSteps.value[currentStepIndex.value]
  })

  const progressPercentage = computed(() => {
    if (workflowSteps.value.length === 0) return 0
    
    const completedSteps = workflowSteps.value.filter(
      step => step.status === 'completed' || step.status === 'skipped'
    ).length
    
    return Math.round((completedSteps / workflowSteps.value.length) * 100)
  })

  const isCurrentStepCompleted = computed(() => {
    const step = currentStep.value
    if (!step) return false
    
    return step.completionCriteria ? step.completionCriteria() : true
  })

  const nextAvailableStep = computed(() => {
    return workflowSteps.value.find(step => step.status === 'pending' && canActivateStep(step))
  })

  const workflowDuration = computed(() => {
    if (!workflowStartTime.value) return 0
    return Date.now() - workflowStartTime.value
  })

  // 动作
  const initializeWorkflow = (type: 'full' | 'quick' | 'custom' = 'full') => {
    workflowType.value = type
    workflowSteps.value = [...defaultWorkflowSteps]
    
    // 根据类型调整工作流
    if (type === 'quick') {
      // 快速工作流跳过可选步骤
      workflowSteps.value = workflowSteps.value.filter(step => !step.optional)
    } else if (type === 'custom') {
      // 自定义工作流允许用户选择步骤
      // 这里可以添加自定义逻辑
    }
    
    // 设置第一步为当前步骤
    if (workflowSteps.value.length > 0) {
      workflowSteps.value[0].status = 'current'
      currentStepIndex.value = 0
    }
    
    workflowStartTime.value = Date.now()
    isWorkflowActive.value = true
  }

  const goToNextStep = (): WorkflowStep | null => {
    const currentStepObj = currentStep.value
    if (!currentStepObj) return null
    
    // 标记当前步骤为完成
    if (isCurrentStepCompleted.value) {
      currentStepObj.status = 'completed'
      recordStepCompletion(currentStepObj.key)
    }
    
    // 查找下一个可用步骤
    const nextStep = findNextAvailableStep()
    if (nextStep) {
      const nextIndex = workflowSteps.value.findIndex(step => step.key === nextStep.key)
      if (nextIndex > -1) {
        currentStepIndex.value = nextIndex
        nextStep.status = 'current'
        return nextStep
      }
    }
    
    return null
  }

  const goToPreviousStep = (): WorkflowStep | null => {
    if (currentStepIndex.value > 0) {
      // 标记当前步骤为待处理
      const currentStepObj = currentStep.value
      if (currentStepObj) {
        currentStepObj.status = 'pending'
      }
      
      // 回到上一步
      currentStepIndex.value--
      const prevStep = currentStep.value
      if (prevStep) {
        prevStep.status = 'current'
        return prevStep
      }
    }
    
    return null
  }

  const jumpToStep = (stepIndex: number): WorkflowStep | null => {
    if (stepIndex >= 0 && stepIndex < workflowSteps.value.length) {
      const targetStep = workflowSteps.value[stepIndex]
      
      // 检查是否可以跳转到该步骤
      if (targetStep.clickable && canActivateStep(targetStep)) {
        // 更新当前步骤状态
        const currentStepObj = currentStep.value
        if (currentStepObj && currentStepObj.key !== targetStep.key) {
          if (isCurrentStepCompleted.value) {
            currentStepObj.status = 'completed'
          } else {
            currentStepObj.status = 'pending'
          }
        }
        
        // 激活目标步骤
        currentStepIndex.value = stepIndex
        targetStep.status = 'current'
        return targetStep
      }
    }
    
    return null
  }

  const skipCurrentStep = () => {
    const currentStepObj = currentStep.value
    if (currentStepObj && currentStepObj.skippable) {
      currentStepObj.status = 'skipped'
      recordStepSkipped(currentStepObj.key)
    }
  }

  const completeCurrentStep = (data?: any) => {
    const currentStepObj = currentStep.value
    if (currentStepObj) {
      currentStepObj.status = 'completed'
      recordStepCompletion(currentStepObj.key, data)
    }
  }

  const resetWorkflow = () => {
    currentStepIndex.value = 0
    workflowSteps.value.forEach(step => {
      step.status = step.key === workflowSteps.value[0]?.key ? 'current' : 'pending'
    })
    stepCompletionData.value = {}
    workflowStartTime.value = Date.now()
  }

  const hideWorkflowProgress = () => {
    isWorkflowActive.value = false
  }

  const showWorkflowProgress = () => {
    isWorkflowActive.value = true
  }

  const updateStepStatus = (stepKey: string, status: WorkflowStep['status']) => {
    const step = workflowSteps.value.find(s => s.key === stepKey)
    if (step) {
      step.status = status
    }
  }

  // 辅助函数
  const canActivateStep = (step: WorkflowStep): boolean => {
    if (!step.dependencies || step.dependencies.length === 0) return true
    
    return step.dependencies.every(depKey => {
      const depStep = workflowSteps.value.find(s => s.key === depKey)
      return depStep && (depStep.status === 'completed' || depStep.status === 'skipped')
    })
  }

  const findNextAvailableStep = (): WorkflowStep | null => {
    for (let i = currentStepIndex.value + 1; i < workflowSteps.value.length; i++) {
      const step = workflowSteps.value[i]
      if (canActivateStep(step)) {
        return step
      }
    }
    return null
  }

  const recordStepCompletion = (stepKey: string, data?: any) => {
    stepCompletionData.value[stepKey] = {
      completedAt: Date.now(),
      data
    }
  }

  const recordStepSkipped = (stepKey: string) => {
    stepCompletionData.value[stepKey] = {
      skippedAt: Date.now()
    }
  }

  // 步骤完成检查函数
  const checkFactorDevelopmentComplete = (): boolean => {
    // 检查是否有已创建的因子
    return stepCompletionData.value['factor-development']?.data?.factorCount > 0
  }

  const checkModelTrainingComplete = (): boolean => {
    // 检查是否有已训练的模型
    return stepCompletionData.value['model-training']?.data?.modelTrained === true
  }

  const checkBacktestComplete = (): boolean => {
    // 检查是否完成回测
    return stepCompletionData.value['strategy-backtest']?.data?.backtestCompleted === true
  }

  const checkResultsAnalysisComplete = (): boolean => {
    // 结果分析是可选的，总是返回true
    return true
  }

  const checkDeploymentComplete = (): boolean => {
    // 检查是否完成部署
    return stepCompletionData.value['strategy-deployment']?.data?.deployed === true
  }

  // 获取工作流建议
  const getWorkflowSuggestions = () => {
    const suggestions = []
    const currentStepObj = currentStep.value
    
    if (currentStepObj) {
      switch (currentStepObj.key) {
        case 'factor-development':
          suggestions.push('建议先使用AI助手生成基础因子，然后手动调优')
          break
        case 'model-training':
          suggestions.push('选择合适的算法和参数，建议从LightGBM开始')
          break
        case 'strategy-backtest':
          suggestions.push('设置合理的回测时间范围，注意交易成本设置')
          break
        case 'results-analysis':
          suggestions.push('重点关注夏普比率和最大回撤指标')
          break
        case 'strategy-deployment':
          suggestions.push('建议先进行模拟交易验证')
          break
      }
    }
    
    return suggestions
  }

  return {
    // 状态
    currentStepIndex,
    workflowType,
    workflowSteps,
    stepCompletionData,
    isWorkflowActive,
    
    // 计算属性
    currentStep,
    progressPercentage,
    isCurrentStepCompleted,
    nextAvailableStep,
    workflowDuration,
    
    // 动作
    initializeWorkflow,
    goToNextStep,
    goToPreviousStep,
    jumpToStep,
    skipCurrentStep,
    completeCurrentStep,
    resetWorkflow,
    hideWorkflowProgress,
    showWorkflowProgress,
    updateStepStatus,
    getWorkflowSuggestions
  }
})