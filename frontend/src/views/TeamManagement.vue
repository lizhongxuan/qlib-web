<template>
  <div class="team-management">
    <div class="page-header">
      <h1>团队管理</h1>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
          创建团队
        </el-button>
      </div>
    </div>

    <div class="content-wrapper">
      <!-- 我的团队 -->
      <el-card shadow="hover" class="team-card">
        <template #header>
          <div class="card-header">
            <span>我的团队</span>
            <el-badge :value="myTeams.length" class="badge" />
          </div>
        </template>

        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else-if="myTeams.length === 0" class="empty-state">
          <el-empty description="暂无团队">
            <el-button type="primary" @click="showCreateDialog = true">
              创建第一个团队
            </el-button>
          </el-empty>
        </div>

        <div v-else class="teams-grid">
          <div
            v-for="team in myTeams"
            :key="team.id"
            class="team-item"
            @click="viewTeamDetails(team)"
          >
            <div class="team-info">
              <h3>{{ team.name }}</h3>
              <p>{{ team.description || '暂无描述' }}</p>
              <div class="team-meta">
                <el-tag v-if="team.is_public" size="small" type="success">
                  公开团队
                </el-tag>
                <el-tag v-else size="small" type="info">
                  私有团队
                </el-tag>
                <span class="member-count">
                  {{ team.member_count || team.members?.length || 0 }} 名成员
                </span>
              </div>
            </div>
            
            <div class="team-actions">
              <el-dropdown @command="handleTeamAction($event, team)">
                <el-button text>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="view">查看详情</el-dropdown-item>
                    <el-dropdown-item v-if="isTeamOwner(team)" command="edit">
                      编辑团队
                    </el-dropdown-item>
                    <el-dropdown-item command="members">管理成员</el-dropdown-item>
                    <el-dropdown-item
                      v-if="isTeamOwner(team)"
                      command="delete"
                      divided
                    >
                      删除团队
                    </el-dropdown-item>
                    <el-dropdown-item v-else command="leave" divided>
                      退出团队
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 公开团队 -->
      <el-card shadow="hover" class="team-card">
        <template #header>
          <div class="card-header">
            <span>发现团队</span>
            <el-button text @click="refreshPublicTeams">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div v-if="publicTeamsLoading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else-if="publicTeams.length === 0" class="empty-state">
          <el-empty description="暂无公开团队" />
        </div>

        <div v-else class="teams-grid">
          <div
            v-for="team in publicTeams"
            :key="team.id"
            class="team-item"
          >
            <div class="team-info">
              <h3>{{ team.name }}</h3>
              <p>{{ team.description || '暂无描述' }}</p>
              <div class="team-meta">
                <el-avatar :size="24" :src="team.owner.avatar_url">
                  {{ team.owner.full_name.charAt(0) }}
                </el-avatar>
                <span class="owner-name">{{ team.owner.full_name }}</span>
                <span class="member-count">
                  {{ team.member_count || team.members?.length || 0 }} 名成员
                </span>
              </div>
            </div>
            
            <div class="team-actions">
              <el-button
                v-if="!isTeamMember(team)"
                type="primary"
                size="small"
                @click="joinTeam(team)"
              >
                申请加入
              </el-button>
              <el-button
                v-else
                size="small"
                disabled
              >
                已加入
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 创建团队对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建团队"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="团队名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入团队名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="团队描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入团队描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="团队类型">
          <el-radio-group v-model="createForm.is_public">
            <el-radio :label="false">私有团队</el-radio>
            <el-radio :label="true">公开团队</el-radio>
          </el-radio-group>
          <div class="form-tip">
            私有团队需要邀请才能加入，公开团队允许用户申请加入
          </div>
        </el-form-item>
        
        <el-form-item label="成员上限" prop="max_members">
          <el-input-number
            v-model="createForm.max_members"
            :min="2"
            :max="100"
            :step="1"
          />
          <div class="form-tip">
            设置团队的最大成员数量（包含团队所有者）
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="createLoading"
            @click="handleCreateTeam"
          >
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 团队详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedTeam?.name"
      width="800px"
    >
      <div v-if="selectedTeam" class="team-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="团队名称">
            {{ selectedTeam.name }}
          </el-descriptions-item>
          <el-descriptions-item label="团队类型">
            <el-tag v-if="selectedTeam.is_public" type="success">
              公开团队
            </el-tag>
            <el-tag v-else type="info">
              私有团队
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="团队所有者">
            <div class="owner-info">
              <el-avatar :size="24" :src="selectedTeam.owner?.avatar_url">
                {{ selectedTeam.owner?.full_name.charAt(0) }}
              </el-avatar>
              <span>{{ selectedTeam.owner?.full_name }}</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="成员数量">
            {{ selectedTeam.member_count || selectedTeam.members?.length || 0 }} / {{ selectedTeam.max_members }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(selectedTeam.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="团队描述" :span="2">
            {{ selectedTeam.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 团队成员列表 -->
        <div class="team-members">
          <h4>团队成员</h4>
          <div v-if="selectedTeam.members && selectedTeam.members.length > 0" class="members-list">
            <div
              v-for="member in selectedTeam.members"
              :key="member.id"
              class="member-item"
            >
              <el-avatar :size="32" :src="member.avatar_url">
                {{ member.full_name.charAt(0) }}
              </el-avatar>
              <div class="member-info">
                <div class="member-name">
                  {{ member.full_name }}
                  <el-tag v-if="member.id === selectedTeam.owner_id" size="small" type="warning">
                    所有者
                  </el-tag>
                </div>
                <div class="member-meta">
                  @{{ member.username }}
                  <span v-if="member.company"> · {{ member.company }}</span>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无成员信息" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, MoreFilled, Refresh } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { Team, TeamCreate } from '@/types/auth'
import { api } from '@/api'

const authStore = useAuthStore()
const createFormRef = ref<InstanceType<typeof ElForm>>()

const loading = ref(false)
const publicTeamsLoading = ref(false)
const createLoading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)

const myTeams = ref<Team[]>([])
const publicTeams = ref<Team[]>([])
const selectedTeam = ref<Team | null>(null)

const createForm = reactive<TeamCreate>({
  name: '',
  description: '',
  is_public: false,
  max_members: 10
})

const createRules = {
  name: [
    { required: true, message: '请输入团队名称', trigger: 'blur' },
    { min: 2, max: 100, message: '团队名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  max_members: [
    { required: true, message: '请设置成员上限', trigger: 'blur' },
    { type: 'number', min: 2, max: 100, message: '成员数量在 2 到 100 之间', trigger: 'blur' }
  ]
}

// 计算属性
const isTeamOwner = (team: Team) => {
  return team.owner_id === authStore.user?.id
}

const isTeamMember = (team: Team) => {
  if (!authStore.user) return false
  return team.members?.some(member => member.id === authStore.user?.id) || false
}

// 方法
const loadMyTeams = async () => {
  loading.value = true
  try {
    const response = await api.get('/users/teams')
    myTeams.value = response.data.data || []
  } catch (error: any) {
    ElMessage.error('加载团队列表失败')
  } finally {
    loading.value = false
  }
}

const loadPublicTeams = async () => {
  publicTeamsLoading.value = true
  try {
    // TODO: 实现公开团队列表API
    await new Promise(resolve => setTimeout(resolve, 1000))
    publicTeams.value = []
  } catch (error: any) {
    ElMessage.error('加载公开团队失败')
  } finally {
    publicTeamsLoading.value = false
  }
}

const refreshPublicTeams = () => {
  loadPublicTeams()
}

const handleCreateTeam = async () => {
  if (!createFormRef.value) return
  
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  createLoading.value = true
  
  try {
    const response = await api.post('/users/teams', createForm)
    ElMessage.success('团队创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    Object.assign(createForm, {
      name: '',
      description: '',
      is_public: false,
      max_members: 10
    })
    
    // 刷新团队列表
    loadMyTeams()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

const viewTeamDetails = async (team: Team) => {
  try {
    const response = await api.get(`/users/teams/${team.id}`)
    selectedTeam.value = response.data.data
    showDetailDialog.value = true
  } catch (error: any) {
    ElMessage.error('获取团队详情失败')
  }
}

const handleTeamAction = async (command: string, team: Team) => {
  switch (command) {
    case 'view':
      viewTeamDetails(team)
      break
    case 'edit':
      // TODO: 实现编辑团队功能
      ElMessage.info('编辑功能开发中')
      break
    case 'members':
      // TODO: 实现成员管理功能
      ElMessage.info('成员管理功能开发中')
      break
    case 'delete':
      await handleDeleteTeam(team)
      break
    case 'leave':
      await handleLeaveTeam(team)
      break
  }
}

const handleDeleteTeam = async (team: Team) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除团队"${team.name}"吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await api.delete(`/users/teams/${team.id}`)
    ElMessage.success('团队删除成功')
    loadMyTeams()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleLeaveTeam = async (team: Team) => {
  try {
    await ElMessageBox.confirm(
      `确定要退出团队"${team.name}"吗？`,
      '确认退出',
      {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/users/teams/${team.id}/members/${authStore.user?.id}`)
    ElMessage.success('已退出团队')
    loadMyTeams()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('退出失败')
    }
  }
}

const joinTeam = async (team: Team) => {
  try {
    await api.post(`/users/teams/${team.id}/members/${authStore.user?.id}`)
    ElMessage.success('申请已提交')
    // 刷新列表
    loadMyTeams()
    loadPublicTeams()
  } catch (error: any) {
    ElMessage.error('申请失败')
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadMyTeams()
  loadPublicTeams()
})
</script>

<style scoped>
.team-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.team-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badge {
  margin-left: 8px;
}

.loading-container {
  padding: 20px;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.team-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.team-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.team-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.team-info p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.team-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.team-actions {
  position: absolute;
  top: 16px;
  right: 16px;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-name {
  font-size: 14px;
}

.member-count {
  font-size: 12px;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.team-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.team-members {
  margin-top: 20px;
}

.team-members h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  background: #f5f7fa;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
</style>