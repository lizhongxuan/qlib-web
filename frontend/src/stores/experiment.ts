import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { experimentApi } from '@/api/experiment'
import type { ExperimentConfig, ExperimentStatus, ExperimentDetail } from '@/types/experiment'

export const useExperimentStore = defineStore('experiment', () => {
  // 状态
  const experimentList = ref<ExperimentStatus[]>([])
  const currentExperiment = ref<ExperimentDetail | null>(null)
  const loading = ref(false)
  
  // 配置选项缓存
  const configOptions = reactive({
    stockPools: [] as string[],
    models: [] as string[],
    strategies: [] as string[],
    modelParams: {} as Record<string, any>
  })

  // Actions
  const fetchExperimentList = async () => {
    loading.value = true
    try {
      const response = await experimentApi.getExperiments()
      if (response.data.success && response.data.data) {
        experimentList.value = response.data.data.items || response.data.data
      } else {
        console.error('获取实验列表失败:', response.data.message)
        experimentList.value = []
      }
    } catch (error) {
      console.error('获取实验列表失败:', error)
      experimentList.value = []
    } finally {
      loading.value = false
    }
  }

  const createExperiment = async (config: ExperimentConfig) => {
    loading.value = true
    try {
      const response = await experimentApi.createExperiment(config)
      if (response.data.success && response.data.data) {
        return { success: true, id: response.data.data.id }
      } else {
        console.error('创建实验失败:', response.data.message)
        return { success: false, message: response.data.message }
      }
    } catch (error) {
      console.error('创建实验失败:', error)
      return { success: false, message: '创建实验失败' }
    } finally {
      loading.value = false
    }
  }

  const fetchExperimentDetail = async (id: string) => {
    loading.value = true
    try {
      const response = await experimentApi.getExperimentDetail(id)
      if (response.data.success && response.data.data) {
        currentExperiment.value = response.data.data
      } else {
        console.error('获取实验详情失败:', response.data.message)
        currentExperiment.value = null
      }
    } catch (error) {
      console.error('获取实验详情失败:', error)
      currentExperiment.value = null
    } finally {
      loading.value = false
    }
  }

  const deleteExperiment = async (id: string) => {
    loading.value = true
    try {
      const response = await experimentApi.deleteExperiment(id)
      if (response.data.success) {
        // 从列表中移除
        const index = experimentList.value.findIndex(exp => exp.id === id)
        if (index > -1) {
          experimentList.value.splice(index, 1)
        }
        return { success: true }
      } else {
        console.error('删除实验失败:', response.data.message)
        return { success: false, message: response.data.message }
      }
    } catch (error) {
      console.error('删除实验失败:', error)
      return { success: false, message: '删除实验失败' }
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    experimentList,
    currentExperiment,
    loading,
    configOptions,
    
    // Actions
    fetchExperimentList,
    createExperiment,
    fetchExperimentDetail,
    deleteExperiment
  }
})