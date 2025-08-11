<template>
  <div class="notification-center">
    <!-- 通知触发按钮 -->
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
      <el-button 
        type="text" 
        size="large" 
        @click="togglePanel"
        :class="{ active: showPanel }"
      >
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>

    <!-- 通知面板 -->
    <div v-if="showPanel" class="notification-panel" v-click-outside="closePanel">
      <div class="panel-header">
        <h3>通知中心</h3>
        <div class="header-actions">
          <el-button 
            type="text" 
            size="small" 
            @click="markAllAsRead"
            :disabled="unreadCount === 0"
          >
            全部已读
          </el-button>
          <el-button 
            type="text" 
            size="small" 
            @click="showSettings = true"
          >
            设置
          </el-button>
        </div>
      </div>

      <div class="panel-tabs">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="全部" name="all">
            <div class="notification-list">
              <div 
                v-for="notification in filteredNotifications" 
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.read, [notification.type]: true }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-icon">
                  <el-icon>
                    <SuccessFilled v-if="notification.type === 'success'" />
                    <InfoFilled v-else-if="notification.type === 'info'" />
                    <WarningFilled v-else-if="notification.type === 'warning'" />
                    <CircleCloseFilled v-else-if="notification.type === 'error'" />
                    <Bell v-else />
                  </el-icon>
                </div>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
                </div>
                <div class="notification-actions">
                  <el-button 
                    v-if="!notification.read" 
                    type="text" 
                    size="small"
                    @click.stop="markAsRead(notification.id)"
                  >
                    标记已读
                  </el-button>
                  <el-button 
                    type="text" 
                    size="small"
                    @click.stop="deleteNotification(notification.id)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              
              <div v-if="filteredNotifications.length === 0" class="empty-state">
                <el-icon><Bell /></el-icon>
                <p>暂无通知</p>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="实验" name="experiment">
            <div class="notification-list">
              <div 
                v-for="notification in experimentNotifications" 
                :key="notification.id"
                class="notification-item experiment-notification"
                :class="{ unread: !notification.read }"
              >
                <div class="experiment-info">
                  <div class="experiment-name">{{ notification.data?.experiment_name }}</div>
                  <div class="status-update">
                    状态: {{ getStatusText(notification.data?.status) }}
                    <el-progress 
                      v-if="notification.data?.progress !== undefined"
                      :percentage="notification.data.progress"
                      :show-text="false"
                      size="small"
                      style="margin-left: 8px; width: 80px;"
                    />
                  </div>
                  <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
                </div>
                <div class="notification-actions">
                  <el-button 
                    type="primary" 
                    size="small"
                    @click="viewExperiment(notification.data?.experiment_id)"
                  >
                    查看实验
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="系统" name="system">
            <div class="notification-list">
              <div 
                v-for="notification in systemNotifications" 
                :key="notification.id"
                class="notification-item system-notification"
                :class="{ unread: !notification.read, [notification.type]: true }"
              >
                <div class="notification-icon">
                  <el-icon>
                    <Monitor v-if="notification.data?.category === 'resource'" />
                    <Setting v-else-if="notification.data?.category === 'config'" />
                    <WarningFilled v-else-if="notification.type === 'warning'" />
                    <InfoFilled v-else />
                  </el-icon>
                </div>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 通知设置对话框 -->
    <el-dialog v-model="showSettings" title="通知设置" width="500px">
      <el-form :model="notificationSettings" label-width="120px">
        <el-form-item label="桌面通知">
          <el-switch 
            v-model="notificationSettings.desktop" 
            @change="toggleDesktopNotifications"
          />
          <div class="setting-desc">允许浏览器发送桌面通知</div>
        </el-form-item>
        
        <el-form-item label="声音提醒">
          <el-switch v-model="notificationSettings.sound" />
          <div class="setting-desc">新通知时播放提示音</div>
        </el-form-item>
        
        <el-form-item label="实验完成通知">
          <el-switch v-model="notificationSettings.experimentComplete" />
          <div class="setting-desc">实验运行完成时发送通知</div>
        </el-form-item>
        
        <el-form-item label="实验失败通知">
          <el-switch v-model="notificationSettings.experimentFailed" />
          <div class="setting-desc">实验运行失败时发送通知</div>
        </el-form-item>
        
        <el-form-item label="系统维护通知">
          <el-switch v-model="notificationSettings.systemMaintenance" />
          <div class="setting-desc">系统维护和更新通知</div>
        </el-form-item>
        
        <el-form-item label="资源监控通知">
          <el-switch v-model="notificationSettings.resourceMonitoring" />
          <div class="setting-desc">系统资源使用异常通知</div>
        </el-form-item>
        
        <el-form-item label="邮件通知">
          <el-switch v-model="notificationSettings.email" />
          <div class="setting-desc">重要通知同时发送邮件</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>

    <!-- 浮动通知组件 -->
    <div class="floating-notifications">
      <transition-group name="notification" tag="div">
        <div 
          v-for="notification in floatingNotifications" 
          :key="notification.id"
          class="floating-notification"
          :class="[notification.type]"
        >
          <div class="floating-icon">
            <el-icon>
              <SuccessFilled v-if="notification.type === 'success'" />
              <InfoFilled v-else-if="notification.type === 'info'" />
              <WarningFilled v-else-if="notification.type === 'warning'" />
              <CircleCloseFilled v-else-if="notification.type === 'error'" />
            </el-icon>
          </div>
          <div class="floating-content">
            <div class="floating-title">{{ notification.title }}</div>
            <div class="floating-message">{{ notification.message }}</div>
          </div>
          <el-button 
            type="text" 
            size="small"
            @click="removeFloatingNotification(notification.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  SuccessFilled,
  InfoFilled,
  WarningFilled,
  CircleCloseFilled,
  Monitor,
  Setting,
  Close
} from '@element-plus/icons-vue'
import { useWebSocket } from '@/utils/websocket'

interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  category: 'experiment' | 'system' | 'general'
  timestamp: string
  read: boolean
  data?: any
}

const router = useRouter()
const { subscribe, unsubscribe } = useWebSocket()

// 响应式数据
const showPanel = ref(false)
const showSettings = ref(false)
const activeTab = ref('all')
const notifications = ref<Notification[]>([])
const floatingNotifications = ref<Notification[]>([])

const notificationSettings = reactive({
  desktop: false,
  sound: true,
  experimentComplete: true,
  experimentFailed: true,
  systemMaintenance: true,
  resourceMonitoring: true,
  email: false
})

// 计算属性
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length
})

const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') return notifications.value
  return notifications.value.filter(n => n.category === activeTab.value)
})

const experimentNotifications = computed(() => {
  return notifications.value.filter(n => n.category === 'experiment')
})

const systemNotifications = computed(() => {
  return notifications.value.filter(n => n.category === 'system')
})

// 方法
const togglePanel = () => {
  showPanel.value = !showPanel.value
}

const closePanel = () => {
  showPanel.value = false
}

const handleTabChange = (tabName: string) => {
  activeTab.value = tabName
}

const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
  const newNotification: Notification = {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    read: false,
    ...notification
  }
  
  notifications.value.unshift(newNotification)
  
  // 检查是否需要显示浮动通知
  if (shouldShowFloatingNotification(newNotification)) {
    showFloatingNotification(newNotification)
  }
  
  // 播放声音
  if (notificationSettings.sound) {
    playNotificationSound()
  }
  
  // 发送桌面通知
  if (notificationSettings.desktop) {
    sendDesktopNotification(newNotification)
  }
}

const shouldShowFloatingNotification = (notification: Notification): boolean => {
  const { category, type } = notification
  
  if (category === 'experiment' && type === 'success' && notificationSettings.experimentComplete) {
    return true
  }
  if (category === 'experiment' && type === 'error' && notificationSettings.experimentFailed) {
    return true
  }
  if (category === 'system' && notificationSettings.systemMaintenance) {
    return true
  }
  
  return false
}

const showFloatingNotification = (notification: Notification) => {
  floatingNotifications.value.push(notification)
  
  // 自动移除浮动通知
  setTimeout(() => {
    removeFloatingNotification(notification.id)
  }, 5000)
}

const removeFloatingNotification = (id: string) => {
  const index = floatingNotifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    floatingNotifications.value.splice(index, 1)
  }
}

const markAsRead = (id: string) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
  }
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
}

const deleteNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

const handleNotificationClick = (notification: Notification) => {
  if (!notification.read) {
    markAsRead(notification.id)
  }
  
  // 根据通知类型执行相应操作
  if (notification.category === 'experiment' && notification.data?.experiment_id) {
    viewExperiment(notification.data.experiment_id)
  }
}

const viewExperiment = (experimentId: string) => {
  router.push(`/experiments/${experimentId}`)
  showPanel.value = false
}

const toggleDesktopNotifications = async () => {
  if (notificationSettings.desktop) {
    // 请求桌面通知权限
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        notificationSettings.desktop = false
        ElMessage.warning('桌面通知权限被拒绝')
      }
    } else {
      notificationSettings.desktop = false
      ElMessage.warning('浏览器不支持桌面通知')
    }
  }
}

const sendDesktopNotification = (notification: Notification) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    const desktopNotification = new Notification(notification.title, {
      body: notification.message,
      icon: '/favicon.ico',
      tag: notification.id
    })
    
    desktopNotification.onclick = () => {
      window.focus()
      handleNotificationClick(notification)
      desktopNotification.close()
    }
    
    // 自动关闭
    setTimeout(() => {
      desktopNotification.close()
    }, 5000)
  }
}

const playNotificationSound = () => {
  // 创建音频上下文播放提示音
  try {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    oscillator.frequency.value = 800
    oscillator.type = 'sine'
    
    gainNode.gain.setValueAtTime(0, audioContext.currentTime)
    gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.1)
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.3)
    
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.3)
  } catch (error) {
    console.warn('播放通知声音失败:', error)
  }
}

const saveSettings = () => {
  // 保存设置到本地存储
  localStorage.setItem('notificationSettings', JSON.stringify(notificationSettings))
  showSettings.value = false
  ElMessage.success('通知设置已保存')
}

const loadSettings = () => {
  const saved = localStorage.getItem('notificationSettings')
  if (saved) {
    Object.assign(notificationSettings, JSON.parse(saved))
  }
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString()
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '已失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// WebSocket 消息处理
const handleExperimentUpdate = (message: any) => {
  const { experiment_id, status, experiment_name, progress } = message.data
  
  let notificationType: 'info' | 'success' | 'warning' | 'error' = 'info'
  let title = ''
  let messageText = ''
  
  switch (status) {
    case 'completed':
      notificationType = 'success'
      title = '实验完成'
      messageText = `实验 "${experiment_name}" 已成功完成`
      break
    case 'failed':
      notificationType = 'error'
      title = '实验失败'
      messageText = `实验 "${experiment_name}" 运行失败`
      break
    case 'running':
      notificationType = 'info'
      title = '实验进度更新'
      messageText = `实验 "${experiment_name}" 进度: ${progress}%`
      break
  }
  
  if (title) {
    addNotification({
      title,
      message: messageText,
      type: notificationType,
      category: 'experiment',
      data: { experiment_id, experiment_name, status, progress }
    })
  }
}

const handleSystemNotification = (message: any) => {
  addNotification({
    title: message.data.title,
    message: message.data.message,
    type: message.data.type,
    category: 'system',
    data: message.data
  })
}

// 生命周期
onMounted(() => {
  loadSettings()
  
  // 订阅WebSocket消息
  subscribe('experiments', handleExperimentUpdate)
  subscribe('system', handleSystemNotification)
  
  // 模拟一些初始通知
  setTimeout(() => {
    addNotification({
      title: '欢迎使用',
      message: '欢迎使用Qlib-Web量化平台！',
      type: 'info',
      category: 'general'
    })
  }, 1000)
})

onUnmounted(() => {
  // 取消订阅
  unsubscribe('experiments', handleExperimentUpdate)
  unsubscribe('system', handleSystemNotification)
})

// 暴露方法给外部组件使用
defineExpose({
  addNotification
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-badge {
  .el-button {
    font-size: 16px;
    color: #666;
    transition: color 0.3s;
  }
  
  .el-button:hover,
  .el-button.active {
    color: #409eff;
  }
}

.notification-panel {
  position: absolute;
  top: 100%;
  right: 0;
  width: 400px;
  max-height: 500px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 2000;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.panel-tabs {
  max-height: 400px;
  overflow-y: auto;
}

.notification-list {
  padding: 8px 0;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background-color 0.3s;
  border-left: 3px solid transparent;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #f0f9ff;
  border-left-color: #409eff;
}

.notification-item.success {
  border-left-color: #67c23a;
}

.notification-item.warning {
  border-left-color: #e6a23c;
}

.notification-item.error {
  border-left-color: #f56c6c;
}

.notification-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  margin-bottom: 4px;
  word-break: break-word;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.notification-actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.experiment-notification {
  border-left-color: #409eff;
}

.experiment-info {
  flex: 1;
}

.experiment-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.status-update {
  display: flex;
  align-items: center;
  font-size: 13px;
  margin-bottom: 4px;
}

.system-notification.warning {
  border-left-color: #e6a23c;
}

.system-notification.error {
  border-left-color: #f56c6c;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-state .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.setting-desc {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.floating-notifications {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.floating-notification {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-left: 4px solid #409eff;
  max-width: 350px;
}

.floating-notification.success {
  border-left-color: #67c23a;
}

.floating-notification.warning {
  border-left-color: #e6a23c;
}

.floating-notification.error {
  border-left-color: #f56c6c;
}

.floating-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.floating-content {
  flex: 1;
}

.floating-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.floating-message {
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}

/* 动画效果 */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>