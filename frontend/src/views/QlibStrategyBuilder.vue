<template>
  <div class="qlib-strategy-builder">
    <div class="toolbar">
      <div class="toolbar-left">
        <h1 class="page-title">
          <el-icon><Setting /></el-icon>
          Qlib策略构建器
        </h1>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/qlib-dashboard' }">Qlib中心</el-breadcrumb-item>
          <el-breadcrumb-item>策略构建器</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button type="primary" @click="saveStrategy">
            <el-icon><DocumentAdd /></el-icon>
            保存策略
          </el-button>
          <el-button @click="previewStrategy">
            <el-icon><View /></el-icon>
            预览
          </el-button>
        </el-button-group>
      </div>
    </div>

    <div class="main-content">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="component-panel" shadow="never">
            <template #header>
              <span>策略组件</span>
            </template>
            <div class="component-list">
              <div class="component-group">
                <h4>数据源</h4>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'data-source')">
                  <el-icon><DataBoard /></el-icon>
                  <span>数据源</span>
                </div>
              </div>
              
              <div class="component-group">
                <h4>因子处理</h4>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'factor-processor')">
                  <el-icon><MagicStick /></el-icon>
                  <span>因子处理器</span>
                </div>
              </div>
              
              <div class="component-group">
                <h4>信号生成</h4>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'signal-generator')">
                  <el-icon><Cpu /></el-icon>
                  <span>信号生成器</span>
                </div>
              </div>
              
              <div class="component-group">
                <h4>组合构建</h4>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'portfolio-builder')">
                  <el-icon><PieChart /></el-icon>
                  <span>组合构建器</span>
                </div>
              </div>
              
              <div class="component-group">
                <h4>风险管理</h4>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'risk-manager')">
                  <el-icon><Warning /></el-icon>
                  <span>风险管理器</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="strategy-canvas" shadow="never">
            <template #header>
              <span>策略流程图</span>
            </template>
            <div class="canvas-area" @drop="onDrop" @dragover="onDragOver">
              <div v-if="strategyComponents.length === 0" class="empty-canvas">
                <el-icon size="64"><Box /></el-icon>
                <p>拖拽组件到这里开始构建策略</p>
              </div>
              <div v-else class="strategy-flow">
                <div 
                  v-for="(component, index) in strategyComponents" 
                  :key="index"
                  class="flow-component"
                  @click="selectComponent(component, index)"
                  :class="{ active: selectedComponentIndex === index }"
                >
                  <div class="component-content">
                    <el-icon>{{ getComponentIcon(component.type) }}</el-icon>
                    <span>{{ getComponentName(component.type) }}</span>
                  </div>
                  <el-button 
                    class="remove-btn" 
                    size="small" 
                    circle 
                    type="danger" 
                    @click.stop="removeComponent(index)"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="config-panel" shadow="never">
            <template #header>
              <span>组件配置</span>
            </template>
            <div v-if="selectedComponent" class="config-form">
              <h4>{{ getComponentName(selectedComponent.type) }}</h4>
              <el-form :model="selectedComponent.config" label-width="80px" size="small">
                <!-- 数据源配置 -->
                <template v-if="selectedComponent.type === 'data-source'">
                  <el-form-item label="数据集">
                    <el-select v-model="selectedComponent.config.dataset">
                      <el-option label="Alpha158" value="alpha158" />
                      <el-option label="Alpha360" value="alpha360" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="股票池">
                    <el-select v-model="selectedComponent.config.universe">
                      <el-option label="沪深300" value="CSI300" />
                      <el-option label="中证500" value="CSI500" />
                    </el-select>
                  </el-form-item>
                </template>
                
                <!-- 因子处理器配置 -->
                <template v-else-if="selectedComponent.type === 'factor-processor'">
                  <el-form-item label="处理方式">
                    <el-select v-model="selectedComponent.config.method">
                      <el-option label="标准化" value="standardize" />
                      <el-option label="中性化" value="neutralize" />
                      <el-option label="去极值" value="winsorize" />
                    </el-select>
                  </el-form-item>
                </template>
                
                <!-- 信号生成器配置 -->
                <template v-else-if="selectedComponent.type === 'signal-generator'">
                  <el-form-item label="模型类型">
                    <el-select v-model="selectedComponent.config.model_type">
                      <el-option label="LightGBM" value="lightgbm" />
                      <el-option label="XGBoost" value="xgboost" />
                      <el-option label="LSTM" value="lstm" />
                    </el-select>
                  </el-form-item>
                </template>
              </el-form>
            </div>
            <div v-else class="no-selection">
              <p>请选择一个组件进行配置</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting,
  DocumentAdd,
  View,
  DataBoard,
  MagicStick,
  Cpu,
  PieChart,
  Warning,
  Box,
  Close
} from '@element-plus/icons-vue'

interface StrategyComponent {
  type: string
  config: Record<string, any>
}

const strategyComponents = ref<StrategyComponent[]>([])
const selectedComponent = ref<StrategyComponent | null>(null)
const selectedComponentIndex = ref<number>(-1)
const draggedComponentType = ref<string>('')

const getComponentName = (type: string) => {
  const names: Record<string, string> = {
    'data-source': '数据源',
    'factor-processor': '因子处理器',
    'signal-generator': '信号生成器',
    'portfolio-builder': '组合构建器',
    'risk-manager': '风险管理器'
  }
  return names[type] || type
}

const getComponentIcon = (type: string) => {
  // 返回组件图标
  return 'Box'
}

const onDragStart = (event: DragEvent, componentType: string) => {
  draggedComponentType.value = componentType
  event.dataTransfer?.setData('text/plain', componentType)
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  const componentType = event.dataTransfer?.getData('text/plain')
  if (componentType) {
    const newComponent: StrategyComponent = {
      type: componentType,
      config: {}
    }
    strategyComponents.value.push(newComponent)
    ElMessage.success(`已添加${getComponentName(componentType)}`)
  }
}

const selectComponent = (component: StrategyComponent, index: number) => {
  selectedComponent.value = component
  selectedComponentIndex.value = index
}

const removeComponent = (index: number) => {
  strategyComponents.value.splice(index, 1)
  if (selectedComponentIndex.value === index) {
    selectedComponent.value = null
    selectedComponentIndex.value = -1
  }
  ElMessage.success('组件已删除')
}

const saveStrategy = () => {
  if (strategyComponents.value.length === 0) {
    ElMessage.warning('请先添加组件')
    return
  }
  ElMessage.success('策略已保存')
}

const previewStrategy = () => {
  if (strategyComponents.value.length === 0) {
    ElMessage.warning('请先添加组件')
    return
  }
  ElMessage.info('策略预览功能')
}
</script>

<style scoped lang="scss">
.qlib-strategy-builder {
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
    
    .component-panel {
      height: 600px;
      
      .component-list {
        .component-group {
          margin-bottom: 20px;
          
          h4 {
            margin: 0 0 12px 0;
            color: #409eff;
            font-size: 14px;
          }
          
          .component-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px;
            background: #f8f9fa;
            border: 1px solid #e4e7ed;
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: grab;
            transition: all 0.3s;
            
            &:hover {
              background: #e3f2fd;
              border-color: #409eff;
              transform: translateY(-2px);
            }
            
            &:active {
              cursor: grabbing;
            }
            
            span {
              font-size: 12px;
              color: #606266;
            }
          }
        }
      }
    }
    
    .strategy-canvas {
      height: 600px;
      
      .canvas-area {
        height: 520px;
        border: 2px dashed #e4e7ed;
        border-radius: 8px;
        position: relative;
        
        .empty-canvas {
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #909399;
          
          .el-icon {
            margin-bottom: 16px;
          }
        }
        
        .strategy-flow {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          
          .flow-component {
            background: white;
            border: 2px solid #e4e7ed;
            border-radius: 8px;
            padding: 16px;
            cursor: pointer;
            position: relative;
            transition: all 0.3s;
            
            &:hover {
              border-color: #409eff;
              box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
            }
            
            &.active {
              border-color: #409eff;
              box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
            }
            
            .component-content {
              display: flex;
              align-items: center;
              gap: 12px;
              
              span {
                font-weight: 500;
                color: #409eff;
              }
            }
            
            .remove-btn {
              position: absolute;
              top: -8px;
              right: -8px;
              width: 20px;
              height: 20px;
            }
          }
        }
      }
    }
    
    .config-panel {
      height: 600px;
      
      .config-form {
        h4 {
          margin: 0 0 16px 0;
          color: #409eff;
        }
      }
      
      .no-selection {
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #909399;
      }
    }
  }
}
</style>