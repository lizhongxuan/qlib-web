<template>
  <div class="template-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>实验模板管理</h2>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建模板
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-input
              v-model="searchForm.keyword"
              placeholder="搜索模板名称、描述或作者"
              clearable
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select v-model="searchForm.category" placeholder="选择分类" clearable @change="handleSearch">
              <el-option label="预设模板" value="preset" />
              <el-option label="用户自定义" value="user" />
              <el-option label="共享模板" value="shared" />
              <el-option label="推荐模板" value="featured" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="searchForm.sortBy" placeholder="排序方式" @change="handleSearch">
              <el-option label="创建时间" value="created_at" />
              <el-option label="使用次数" value="usage_count" />
              <el-option label="评分" value="rating" />
              <el-option label="名称" value="name" />
            </el-select>
          </el-col>
          <el-col :span="2">
            <el-button @click="resetSearch">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 推荐模板 -->
      <div class="featured-section" v-if="featuredTemplates.length > 0">
        <h3>推荐模板</h3>
        <el-row :gutter="16">
          <el-col :span="6" v-for="template in featuredTemplates" :key="template.id">
            <el-card shadow="hover" class="template-card featured">
              <div class="template-header">
                <h4>{{ template.name }}</h4>
                <el-tag type="warning" size="small">推荐</el-tag>
              </div>
              <p class="template-description">{{ template.description }}</p>
              <div class="template-meta">
                <span><el-icon><User /></el-icon>{{ template.author }}</span>
                <span><el-icon><View /></el-icon>{{ template.usage_count }}</span>
                <span><el-icon><Star /></el-icon>{{ calculateRating(template) }}</span>
              </div>
              <div class="template-actions">
                <el-button size="small" @click="useTemplate(template)">使用</el-button>
                <el-button size="small" @click="viewTemplate(template)">查看</el-button>
                <el-button size="small" @click="cloneTemplate(template)">克隆</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 模板列表 -->
      <div class="template-list">
        <el-table :data="templates" v-loading="loading">
          <el-table-column prop="name" label="模板名称" min-width="200">
            <template #default="scope">
              <div class="template-name-cell">
                <strong>{{ scope.row.name }}</strong>
                <div class="template-tags">
                  <el-tag
                    v-for="tag in scope.row.tags"
                    :key="tag"
                    size="small"
                    style="margin-right: 4px;"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="scope">
              <el-tag :type="getCategoryType(scope.row.category)">
                {{ getCategoryName(scope.row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column label="统计信息" width="150">
            <template #default="scope">
              <div class="template-stats">
                <div><el-icon><View /></el-icon>{{ scope.row.usage_count }}</div>
                <div><el-icon><Star /></el-icon>{{ calculateRating(scope.row) }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="scope">
              <el-button size="small" @click="useTemplate(scope.row)">使用</el-button>
              <el-button size="small" @click="viewTemplate(scope.row)">查看</el-button>
              <el-dropdown>
                <el-button size="small">
                  更多<el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="cloneTemplate(scope.row)">克隆</el-dropdown-item>
                    <el-dropdown-item @click="rateTemplate(scope.row)">评分</el-dropdown-item>
                    <el-dropdown-item v-if="scope.row.category === 'user'" @click="editTemplate(scope.row)">编辑</el-dropdown-item>
                    <el-dropdown-item v-if="scope.row.category === 'user'" @click="deleteTemplate(scope.row)" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTemplate ? '编辑模板' : '创建模板'"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <el-form :model="templateForm" :rules="templateRules" ref="templateFormRef" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="templateForm.name" placeholder="输入模板名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="templateForm.category" placeholder="选择分类" style="width: 100%">
                <el-option label="用户自定义" value="user" />
                <el-option label="共享模板" value="shared" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述" prop="description">
          <el-input v-model="templateForm.description" type="textarea" :rows="3" placeholder="输入模板描述" />
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-tag
            v-for="tag in templateForm.tags"
            :key="tag"
            closable
            @close="removeTag(tag)"
            style="margin-right: 8px;"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="showTagInput"
            ref="tagInputRef"
            v-model="newTag"
            size="small"
            style="width: 100px;"
            @keyup.enter="addTag"
            @blur="addTag"
          />
          <el-button v-else size="small" @click="showNewTagInput">+ 添加标签</el-button>
        </el-form-item>
        <!-- 这里可以添加更多配置选项 -->
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 模板详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="模板详情" width="70%">
      <div v-if="selectedTemplate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ selectedTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ selectedTemplate.author }}</el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag :type="getCategoryType(selectedTemplate.category)">
              {{ getCategoryName(selectedTemplate.category) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">{{ selectedTemplate.version }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ selectedTemplate.usage_count }}</el-descriptions-item>
          <el-descriptions-item label="评分">{{ calculateRating(selectedTemplate) }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ formatDate(selectedTemplate.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedTemplate.description }}</el-descriptions-item>
        </el-descriptions>
        
        <div style="margin-top: 16px;">
          <h4>标签</h4>
          <el-tag v-for="tag in selectedTemplate.tags" :key="tag" style="margin-right: 8px;">
            {{ tag }}
          </el-tag>
        </div>
        
        <div style="margin-top: 16px;">
          <h4>配置预览</h4>
          <el-code :code="JSON.stringify(selectedTemplate.config, null, 2)" language="json" />
        </div>
      </div>
    </el-dialog>

    <!-- 评分对话框 -->
    <el-dialog v-model="showRatingDialog" title="为模板评分" width="400px">
      <div style="text-align: center; padding: 20px;">
        <h4>{{ ratingTemplate?.name }}</h4>
        <el-rate v-model="rating" size="large" />
        <div style="margin-top: 16px;">
          <el-button @click="showRatingDialog = false">取消</el-button>
          <el-button type="primary" @click="submitRating">提交评分</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, User, View, Star, ArrowDown } from '@element-plus/icons-vue'

interface Template {
  id: string
  name: string
  description: string
  category: string
  author: string
  version: string
  tags: string[]
  usage_count: number
  rating: number
  rating_count: number
  is_public: boolean
  is_featured: boolean
  created_at: string
  config: any
}

const templates = ref<Template[]>([])
const featuredTemplates = ref<Template[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showRatingDialog = ref(false)
const selectedTemplate = ref<Template | null>(null)
const ratingTemplate = ref<Template | null>(null)
const editingTemplate = ref<Template | null>(null)
const rating = ref(0)

const searchForm = reactive({
  keyword: '',
  category: '',
  sortBy: 'created_at'
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const templateForm = reactive({
  name: '',
  description: '',
  category: 'user',
  tags: [] as string[],
  config: {}
})

const templateRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ]
}

const templateFormRef = ref()
const showTagInput = ref(false)
const newTag = ref('')
const tagInputRef = ref()

// 加载模板列表
const loadTemplates = async () => {
  loading.value = true
  try {
    // 这里调用API
    const response = await fetch('/api/v1/templates?' + new URLSearchParams({
      keyword: searchForm.keyword,
      category: searchForm.category,
      sort_by: searchForm.sortBy,
      page: pagination.page.toString(),
      page_size: pagination.pageSize.toString()
    }))
    const data = await response.json()
    
    if (data.success) {
      templates.value = data.data.items
      pagination.total = data.data.total
    }
  } catch (error) {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

// 加载推荐模板
const loadFeaturedTemplates = async () => {
  try {
    const response = await fetch('/api/v1/templates/featured?limit=4')
    const data = await response.json()
    
    if (data.success) {
      featuredTemplates.value = data.data
    }
  } catch (error) {
    console.error('加载推荐模板失败:', error)
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadTemplates()
}

// 重置搜索
const resetSearch = () => {
  Object.assign(searchForm, {
    keyword: '',
    category: '',
    sortBy: 'created_at'
  })
  handleSearch()
}

// 分页处理
const handleSizeChange = () => {
  loadTemplates()
}

const handleCurrentChange = () => {
  loadTemplates()
}

// 使用模板
const useTemplate = (template: Template) => {
  ElMessage.success(`使用模板：${template.name}`)
  // 这里可以跳转到新建实验页面，并填充模板配置
}

// 查看模板详情
const viewTemplate = (template: Template) => {
  selectedTemplate.value = template
  showDetailDialog.value = true
}

// 克隆模板
const cloneTemplate = async (template: Template) => {
  try {
    const { value: newName } = await ElMessageBox.prompt('请输入新模板名称', '克隆模板', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: `${template.name} - 副本`
    })
    
    const response = await fetch(`/api/v1/templates/${template.id}/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName })
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('模板克隆成功')
      loadTemplates()
    } else {
      ElMessage.error('模板克隆失败')
    }
  } catch (error) {
    // 用户取消
  }
}

// 评分模板
const rateTemplate = (template: Template) => {
  ratingTemplate.value = template
  rating.value = 0
  showRatingDialog.value = true
}

// 提交评分
const submitRating = async () => {
  if (!ratingTemplate.value || rating.value === 0) {
    ElMessage.warning('请选择评分')
    return
  }
  
  try {
    const response = await fetch(`/api/v1/templates/${ratingTemplate.value.id}/rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating: rating.value })
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('评分成功')
      showRatingDialog.value = false
      loadTemplates()
    }
  } catch (error) {
    ElMessage.error('评分失败')
  }
}

// 编辑模板
const editTemplate = (template: Template) => {
  editingTemplate.value = template
  Object.assign(templateForm, {
    name: template.name,
    description: template.description,
    category: template.category,
    tags: [...template.tags],
    config: template.config
  })
  showCreateDialog.value = true
}

// 删除模板
const deleteTemplate = async (template: Template) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模板吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch(`/api/v1/templates/${template.id}`, {
      method: 'DELETE'
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('模板删除成功')
      loadTemplates()
    }
  } catch (error) {
    // 用户取消
  }
}

// 保存模板
const saveTemplate = async () => {
  try {
    await templateFormRef.value.validate()
    
    const method = editingTemplate.value ? 'PUT' : 'POST'
    const url = editingTemplate.value 
      ? `/api/v1/templates/${editingTemplate.value.id}`
      : '/api/v1/templates'
    
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(templateForm)
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success(editingTemplate.value ? '模板更新成功' : '模板创建成功')
      showCreateDialog.value = false
      loadTemplates()
    }
  } catch (error) {
    ElMessage.error('保存模板失败')
  }
}

// 关闭对话框
const handleCloseDialog = () => {
  templateFormRef.value?.resetFields()
  editingTemplate.value = null
  showCreateDialog.value = false
}

// 标签管理
const showNewTagInput = () => {
  showTagInput.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const addTag = () => {
  if (newTag.value.trim() && !templateForm.tags.includes(newTag.value.trim())) {
    templateForm.tags.push(newTag.value.trim())
  }
  newTag.value = ''
  showTagInput.value = false
}

const removeTag = (tag: string) => {
  const index = templateForm.tags.indexOf(tag)
  if (index > -1) {
    templateForm.tags.splice(index, 1)
  }
}

// 工具函数
const getCategoryType = (category: string) => {
  const types: Record<string, string> = {
    preset: 'info',
    user: 'success',
    shared: 'warning',
    featured: 'danger'
  }
  return types[category] || 'info'
}

const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    preset: '预设',
    user: '自定义',
    shared: '共享',
    featured: '推荐'
  }
  return names[category] || category
}

const calculateRating = (template: Template) => {
  if (template.rating_count === 0) return '暂无'
  return (template.rating / template.rating_count).toFixed(1)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadTemplates()
  loadFeaturedTemplates()
})
</script>

<style scoped>
.template-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.filter-section {
  margin-bottom: 20px;
}

.featured-section {
  margin-bottom: 30px;
}

.template-card {
  height: 200px;
  cursor: pointer;
}

.template-card.featured {
  border: 2px solid #f56c6c;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.template-header h4 {
  margin: 0;
}

.template-description {
  color: #666;
  font-size: 12px;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.template-meta span {
  display: flex;
  align-items: center;
  gap: 2px;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.template-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.template-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.template-stats div {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>