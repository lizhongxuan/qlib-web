<template>
  <div class="qlib-model-lab">
    <div class="toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">
          <el-icon><Cpu /></el-icon>
          Qlib模型实验室
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/qlib-dashboard' }">Qlib中心</el-breadcrumb-item>
          <el-breadcrumb-item>模型实验室</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button type="primary" @click="createNewModel">
            <el-icon><Plus /></el-icon>
            新建模型
          </el-button>
          <el-button @click="refreshModels" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </el-button-group>
      </div>
    </div>

    <div class="main-content">
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="模型注册表" name="registry">
          <el-card shadow="never">
            <el-table :data="modelRegistry" :loading="loading" stripe>
              <el-table-column prop="name" label="模型名称" width="200" />
              <el-table-column prop="model_type" label="模型类型" width="120" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="150" />
              <el-table-column label="操作" fixed="right">
                <template #default="scope">
                  <el-button-group size="small">
                    <el-button type="primary" link @click="trainModel(scope.row)">训练</el-button>
                    <el-button type="success" link @click="viewModel(scope.row)">查看</el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
        
        <el-tab-pane label="训练任务" name="training">
          <el-card shadow="never">
            <div class="training-dashboard">
              <div class="stats-row">
                <div class="stat-card">
                  <div class="stat-value">{{ modelStats.total }}</div>
                  <div class="stat-label">总模型数</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ modelStats.training }}</div>
                  <div class="stat-label">训练中</div>
                </div>
                <div class="stat-card">
                  <div class="stat-value">{{ modelStats.trained }}</div>
                  <div class="stat-label">已完成</div>
                </div>
              </div>
              
              <div class="active-tasks">
                <h3>活跃训练任务</h3>
                <div v-if="activeTrainingTasks.length === 0" class="no-tasks">
                  <p>暂无活跃训练任务</p>
                </div>
                <div v-else class="tasks-list">
                  <div v-for="task in activeTrainingTasks" :key="task.task_id" class="task-item">
                    <div class="task-info">
                      <h4>{{ task.name }}</h4>
                      <p>进度: {{ task.progress }}%</p>
                    </div>
                    <el-progress :percentage="task.progress" />
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Plus, Refresh } from '@element-plus/icons-vue'
import { useQlibModelsStore } from '@/stores/qlib-models'

const qlibModelsStore = useQlibModelsStore()
const loading = ref(false)
const activeTab = ref('registry')

const modelRegistry = computed(() => qlibModelsStore.modelRegistry)
const modelStats = computed(() => qlibModelsStore.modelStats)
const activeTrainingTasks = computed(() => qlibModelsStore.activeTrainingTasks)

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'trained': 'success',
    'training': 'warning',
    'failed': 'danger',
    'registered': 'info'
  }
  return types[status] || 'info'
}

const createNewModel = () => {
  ElMessage.info('创建新模型功能')
}

const refreshModels = async () => {
  loading.value = true
  try {
    await qlibModelsStore.loadModelRegistry()
    ElMessage.success('模型刷新成功')
  } finally {
    loading.value = false
  }
}

const trainModel = async (model: any) => {
  try {
    await qlibModelsStore.trainModel(model.model_id)
    ElMessage.success('训练任务已启动')
    activeTab.value = 'training'
  } catch (error) {
    ElMessage.error('启动训练失败')
  }
}

const viewModel = (model: any) => {
  ElMessage.info(`查看模型: ${model.name}`)
}

onMounted(() => {
  refreshModels()
})
</script>

<style scoped lang="scss">
.qlib-model-lab {
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
    
    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 500;
    }
  }
  
  .main-content {
    flex: 1;
    padding: 24px;
    
    .stats-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
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
        }
        
        .stat-label {
          font-size: 12px;
          color: #909399;
        }
      }
    }
    
    .active-tasks {
      h3 {
        color: #409eff;
        margin-bottom: 16px;
      }
      
      .no-tasks {
        text-align: center;
        color: #909399;
        padding: 40px;
      }
      
      .tasks-list {
        .task-item {
          background: white;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 12px;
          border: 1px solid #e4e7ed;
          
          .task-info {
            margin-bottom: 12px;
            
            h4 {
              margin: 0 0 4px 0;
              color: #409eff;
            }
            
            p {
              margin: 0;
              color: #909399;
              font-size: 12px;
            }
          }
        }
      }
    }
  }
}
</style>