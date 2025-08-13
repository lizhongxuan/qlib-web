<template>
  <div class="batch-experiment-manager">
    <div class="manager-header">
      <h3>批量实验管理</h3>
      <el-button type="primary" @click="createBatchExperiment">新建批量实验</el-button>
    </div>

    <el-card>
      <el-table :data="batchExperiments" style="width: 100%">
        <el-table-column prop="name" label="实验组名称" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="experiments" label="实验数量" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">查看</el-button>
            <el-button size="small" type="danger" @click="stopBatch(row)">停止</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建批量实验对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建批量实验" width="600px">
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="实验组名称">
          <el-input v-model="batchForm.name" />
        </el-form-item>
        <el-form-item label="参数扫描">
          <el-checkbox-group v-model="batchForm.parameters">
            <el-checkbox label="learning_rate">学习率</el-checkbox>
            <el-checkbox label="n_estimators">树的数量</el-checkbox>
            <el-checkbox label="max_depth">最大深度</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="并行数量">
          <el-input-number v-model="batchForm.parallel" :min="1" :max="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="startBatch">开始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const showCreateDialog = ref(false)

const batchExperiments = ref([
  { id: '1', name: '参数扫描实验组1', status: '运行中', progress: 75, experiments: 24 },
  { id: '2', name: '模型对比实验组', status: '已完成', progress: 100, experiments: 12 },
  { id: '3', name: '因子测试组', status: '等待中', progress: 0, experiments: 36 }
])

const batchForm = reactive({
  name: '',
  parameters: [],
  parallel: 3
})

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    '运行中': 'warning',
    '已完成': 'success',
    '等待中': 'info',
    '已停止': 'danger'
  }
  return types[status] || 'info'
}

const createBatchExperiment = () => {
  showCreateDialog.value = true
}

const startBatch = () => {
  showCreateDialog.value = false
  ElMessage.success('批量实验已启动')
}

const viewDetails = (row: any) => {
  ElMessage.info(`查看实验组 ${row.name} 详情`)
}

const stopBatch = (row: any) => {
  ElMessage.warning(`停止实验组 ${row.name}`)
}
</script>

<style scoped lang="scss">
.batch-experiment-manager {
  .manager-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }
}
</style>