<template>
  <div class="workflow-preferences">
    <div class="preferences-header">
      <h3>工作流偏好设置</h3>
      <el-button type="primary" @click="savePreferences" :loading="isSaving">
        保存设置
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="preferences-tabs">
      <!-- 工作流配置 -->
      <el-tab-pane label="工作流配置" name="workflow">
        <el-card>
          <template #header>
            <h4>默认工作流程</h4>
          </template>
          
          <el-form :model="preferences.workflow" label-width="120px">
            <el-form-item label="起始页面">
              <el-select v-model="preferences.workflow.startPage">
                <el-option label="仪表盘" value="dashboard" />
                <el-option label="因子开发" value="factors" />
                <el-option label="策略回测" value="backtest" />
                <el-option label="结果分析" value="results" />
              </el-select>
            </el-form-item>

            <el-form-item label="自动保存">
              <el-switch v-model="preferences.workflow.autoSave" />
              <span class="form-help">自动保存配置和进度</span>
            </el-form-item>

            <el-form-item label="智能建议">
              <el-switch v-model="preferences.workflow.smartSuggestions" />
              <span class="form-help">显示智能操作建议</span>
            </el-form-item>

            <el-form-item label="进度跟踪">
              <el-switch v-model="preferences.workflow.progressTracking" />
              <span class="form-help">跟踪和显示工作流进度</span>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card>
          <template #header>
            <h4>快速操作</h4>
          </template>
          
          <el-form :model="preferences.quickActions" label-width="120px">
            <el-form-item label="启用快捷键">
              <el-switch v-model="preferences.quickActions.enabled" />
            </el-form-item>

            <el-form-item label="一键回测">
              <el-switch v-model="preferences.quickActions.oneClickBacktest" />
            </el-form-item>

            <el-form-item label="快速导出">
              <el-switch v-model="preferences.quickActions.quickExport" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 界面偏好 -->
      <el-tab-pane label="界面偏好" name="interface">
        <el-card>
          <template #header>
            <h4>外观设置</h4>
          </template>
          
          <el-form :model="preferences.interface" label-width="120px">
            <el-form-item label="主题">
              <el-radio-group v-model="preferences.interface.theme">
                <el-radio label="light">浅色主题</el-radio>
                <el-radio label="dark">深色主题</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="紧凑模式">
              <el-switch v-model="preferences.interface.compact" />
            </el-form-item>

            <el-form-item label="显示网格">
              <el-switch v-model="preferences.interface.showGrid" />
            </el-form-item>

            <el-form-item label="动画效果">
              <el-switch v-model="preferences.interface.animations" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 数据偏好 -->
      <el-tab-pane label="数据偏好" name="data">
        <el-card>
          <template #header>
            <h4>默认参数</h4>
          </template>
          
          <el-form :model="preferences.data" label-width="120px">
            <el-form-item label="股票池">
              <el-select v-model="preferences.data.defaultUniverse">
                <el-option label="沪深300" value="CSI300" />
                <el-option label="中证500" value="CSI500" />
                <el-option label="创业板" value="CHINEXT" />
              </el-select>
            </el-form-item>

            <el-form-item label="回测期间">
              <el-select v-model="preferences.data.defaultPeriod">
                <el-option label="最近1年" value="1y" />
                <el-option label="最近2年" value="2y" />
                <el-option label="最近3年" value="3y" />
              </el-select>
            </el-form-item>

            <el-form-item label="风险偏好">
              <el-slider
                v-model="preferences.data.riskTolerance"
                :min="1"
                :max="10"
                :step="1"
                show-stops
                show-input
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知偏好 -->
      <el-tab-pane label="通知偏好" name="notifications">
        <el-card>
          <template #header>
            <h4>通知设置</h4>
          </template>
          
          <el-form :model="preferences.notifications" label-width="120px">
            <el-form-item label="任务完成">
              <el-switch v-model="preferences.notifications.taskCompletion" />
            </el-form-item>

            <el-form-item label="错误提醒">
              <el-switch v-model="preferences.notifications.errorAlerts" />
            </el-form-item>

            <el-form-item label="性能警告">
              <el-switch v-model="preferences.notifications.performanceWarnings" />
            </el-form-item>

            <el-form-item label="市场提醒">
              <el-switch v-model="preferences.notifications.marketAlerts" />
            </el-form-item>

            <el-form-item label="通知方式">
              <el-checkbox-group v-model="preferences.notifications.methods">
                <el-checkbox label="browser">浏览器通知</el-checkbox>
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="sms">短信通知</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 预设模板 -->
    <el-card class="templates-card">
      <template #header>
        <h4>预设模板</h4>
      </template>
      
      <div class="template-grid">
        <div
          v-for="template in presetTemplates"
          :key="template.id"
          class="template-item"
          @click="applyTemplate(template)"
        >
          <div class="template-icon">
            <el-icon><component :is="template.icon" /></el-icon>
          </div>
          <h5>{{ template.name }}</h5>
          <p>{{ template.description }}</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

interface PreferencesData {
  workflow: {
    startPage: string
    autoSave: boolean
    smartSuggestions: boolean
    progressTracking: boolean
  }
  quickActions: {
    enabled: boolean
    oneClickBacktest: boolean
    quickExport: boolean
  }
  interface: {
    theme: string
    compact: boolean
    showGrid: boolean
    animations: boolean
  }
  data: {
    defaultUniverse: string
    defaultPeriod: string
    riskTolerance: number
  }
  notifications: {
    taskCompletion: boolean
    errorAlerts: boolean
    performanceWarnings: boolean
    marketAlerts: boolean
    methods: string[]
  }
}

const activeTab = ref('workflow')
const isSaving = ref(false)

const preferences = reactive<PreferencesData>({
  workflow: {
    startPage: 'dashboard',
    autoSave: true,
    smartSuggestions: true,
    progressTracking: true
  },
  quickActions: {
    enabled: true,
    oneClickBacktest: false,
    quickExport: true
  },
  interface: {
    theme: 'light',
    compact: false,
    showGrid: true,
    animations: true
  },
  data: {
    defaultUniverse: 'CSI300',
    defaultPeriod: '2y',
    riskTolerance: 5
  },
  notifications: {
    taskCompletion: true,
    errorAlerts: true,
    performanceWarnings: true,
    marketAlerts: false,
    methods: ['browser']
  }
})

const presetTemplates = ref([
  {
    id: 'beginner',
    name: '新手模式',
    description: '适合初学者的简化工作流',
    icon: 'User'
  },
  {
    id: 'professional',
    name: '专业模式',
    description: '适合专业用户的完整功能',
    icon: 'Medal'
  },
  {
    id: 'research',
    name: '研究模式',
    description: '适合研究分析的配置',
    icon: 'DataBoard'
  }
])

const savePreferences = async () => {
  isSaving.value = true
  
  // 模拟保存过程
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 保存到本地存储
  localStorage.setItem('workflow_preferences', JSON.stringify(preferences))
  
  isSaving.value = false
  ElMessage.success('偏好设置已保存')
}

const applyTemplate = (template: any) => {
  ElMessage.success(`已应用${template.name}模板`)
  // 这里应用相应的模板配置
}
</script>

<style scoped lang="scss">
.workflow-preferences {
  .preferences-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .form-help {
    margin-left: 8px;
    color: var(--el-text-color-placeholder);
    font-size: 12px;
  }

  .templates-card {
    margin-top: 24px;

    .template-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;

      .template-item {
        text-align: center;
        padding: 20px;
        border: 2px solid var(--el-border-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
          border-color: var(--el-color-primary);
          background-color: var(--el-color-primary-light-9);
        }

        .template-icon {
          font-size: 32px;
          color: var(--el-color-primary);
          margin-bottom: 12px;
        }

        h5 {
          margin: 0 0 8px 0;
        }

        p {
          margin: 0;
          color: var(--el-text-color-regular);
          font-size: 14px;
        }
      }
    }
  }
}
</style>