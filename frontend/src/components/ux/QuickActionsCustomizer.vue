<template>
  <div class="quick-actions-customizer">
    <div class="customizer-header">
      <h3>快捷操作定制</h3>
      <el-button type="primary" @click="saveCustomActions">保存配置</el-button>
    </div>

    <div class="customizer-content">
      <!-- 当前快捷操作 -->
      <el-card class="current-actions">
        <template #header>
          <h4>当前快捷操作</h4>
        </template>
        <div class="actions-list">
          <div
            v-for="(action, index) in customActions"
            :key="action.id"
            class="action-item"
          >
            <div class="action-info">
              <el-icon><component :is="action.icon" /></el-icon>
              <div>
                <h5>{{ action.name }}</h5>
                <p>{{ action.description }}</p>
              </div>
            </div>
            <div class="action-controls">
              <el-button size="small" @click="editAction(action)">编辑</el-button>
              <el-button size="small" @click="removeAction(index)">移除</el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 可用操作 -->
      <el-card class="available-actions">
        <template #header>
          <h4>可添加操作</h4>
        </template>
        <div class="actions-grid">
          <div
            v-for="action in availableActions"
            :key="action.id"
            class="action-card"
            @click="addAction(action)"
          >
            <el-icon><component :is="action.icon" /></el-icon>
            <span>{{ action.name }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑快捷操作" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" />
        </el-form-item>
        <el-form-item label="快捷键">
          <el-input v-model="editForm.shortcut" placeholder="如: Ctrl+B" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

interface QuickAction {
  id: string
  name: string
  description: string
  icon: string
  shortcut?: string
  action: string
}

const showEditDialog = ref(false)
const editingIndex = ref(-1)

const customActions = ref<QuickAction[]>([
  {
    id: '1',
    name: '新建策略',
    description: '快速创建新的投资策略',
    icon: 'Plus',
    shortcut: 'Ctrl+N',
    action: 'create_strategy'
  },
  {
    id: '2',
    name: '快速回测',
    description: '使用默认参数进行回测',
    icon: 'VideoPlay',
    shortcut: 'Ctrl+R',
    action: 'quick_backtest'
  }
])

const availableActions = ref<QuickAction[]>([
  {
    id: 'export',
    name: '导出结果',
    description: '导出当前结果',
    icon: 'Download',
    action: 'export_results'
  },
  {
    id: 'refresh',
    name: '刷新数据',
    description: '刷新页面数据',
    icon: 'Refresh',
    action: 'refresh_data'
  },
  {
    id: 'settings',
    name: '系统设置',
    description: '打开系统设置',
    icon: 'Setting',
    action: 'open_settings'
  }
])

const editForm = reactive({
  name: '',
  description: '',
  shortcut: ''
})

const addAction = (action: QuickAction) => {
  const newAction = { ...action, id: Date.now().toString() }
  customActions.value.push(newAction)
  ElMessage.success('快捷操作已添加')
}

const removeAction = (index: number) => {
  customActions.value.splice(index, 1)
  ElMessage.success('快捷操作已移除')
}

const editAction = (action: QuickAction) => {
  editingIndex.value = customActions.value.findIndex(a => a.id === action.id)
  editForm.name = action.name
  editForm.description = action.description
  editForm.shortcut = action.shortcut || ''
  showEditDialog.value = true
}

const saveEdit = () => {
  if (editingIndex.value >= 0) {
    const action = customActions.value[editingIndex.value]
    action.name = editForm.name
    action.description = editForm.description
    action.shortcut = editForm.shortcut
    
    showEditDialog.value = false
    ElMessage.success('快捷操作已更新')
  }
}

const saveCustomActions = () => {
  localStorage.setItem('custom_quick_actions', JSON.stringify(customActions.value))
  ElMessage.success('配置已保存')
}
</script>

<style scoped lang="scss">
.quick-actions-customizer {
  .customizer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .customizer-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;

    .current-actions {
      .actions-list {
        .action-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border: 1px solid var(--el-border-color);
          border-radius: 8px;
          margin-bottom: 8px;

          .action-info {
            display: flex;
            align-items: center;
            gap: 12px;

            h5 {
              margin: 0 0 4px 0;
            }

            p {
              margin: 0;
              color: var(--el-text-color-regular);
              font-size: 12px;
            }
          }

          .action-controls {
            display: flex;
            gap: 8px;
          }
        }
      }
    }

    .available-actions {
      .actions-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;

        .action-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          border: 2px dashed var(--el-border-color);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s;

          &:hover {
            border-color: var(--el-color-primary);
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .quick-actions-customizer {
    .customizer-content {
      grid-template-columns: 1fr;
    }
  }
}
</style>