<!--
虚拟滚动表格组件
用于优化大数据量表格的性能，只渲染可见区域的行
-->
<template>
  <div class="virtual-scroll-table" ref="containerRef">
    <!-- 表头 -->
    <div class="table-header" :style="{ width: `${totalWidth}px` }">
      <div
        v-for="(column, index) in columns"
        :key="index"
        class="table-header-cell"
        :style="{ 
          width: `${column.width || defaultColumnWidth}px`,
          left: `${getColumnLeft(index)}px`
        }"
      >
        {{ column.title }}
      </div>
    </div>

    <!-- 滚动容器 -->
    <div
      class="table-scroll-container"
      :style="{ height: `${containerHeight}px` }"
      @scroll="handleScroll"
      ref="scrollRef"
    >
      <!-- 虚拟占位空间 -->
      <div
        class="virtual-spacer"
        :style="{ 
          height: `${totalHeight}px`,
          width: `${totalWidth}px`
        }"
      >
        <!-- 可见行 -->
        <div
          class="virtual-viewport"
          :style="{
            transform: `translateY(${startOffset}px)`,
            width: `${totalWidth}px`
          }"
        >
          <div
            v-for="(item, rowIndex) in visibleItems"
            :key="getRowKey ? getRowKey(item, startIndex + rowIndex) : startIndex + rowIndex"
            class="table-row"
            :class="{ 'table-row-even': (startIndex + rowIndex) % 2 === 0 }"
            :style="{ height: `${itemHeight}px` }"
            @click="handleRowClick(item, startIndex + rowIndex)"
          >
            <div
              v-for="(column, cellIndex) in columns"
              :key="cellIndex"
              class="table-cell"
              :style="{
                width: `${column.width || defaultColumnWidth}px`,
                left: `${getColumnLeft(cellIndex)}px`
              }"
            >
              <slot
                v-if="column.slot"
                :name="column.slot"
                :row="item"
                :column="column"
                :index="startIndex + rowIndex"
              >
                {{ getCellValue(item, column.key) }}
              </slot>
              <span v-else>
                {{ getCellValue(item, column.key) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="table-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载中...</span>
    </div>

    <!-- 空数据提示 -->
    <div v-if="!loading && data.length === 0" class="table-empty">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'

interface Column {
  key: string
  title: string
  width?: number
  slot?: string
  fixed?: 'left' | 'right'
}

interface Props {
  data: any[]
  columns: Column[]
  itemHeight?: number
  containerHeight?: number
  bufferSize?: number
  loading?: boolean
  getRowKey?: (item: any, index: number) => string | number
}

const props = withDefaults(defineProps<Props>(), {
  itemHeight: 50,
  containerHeight: 400,
  bufferSize: 5,
  loading: false
})

const emit = defineEmits<{
  rowClick: [row: any, index: number]
  scroll: [scrollTop: number, scrollLeft: number]
}>()

// 引用
const containerRef = ref<HTMLElement>()
const scrollRef = ref<HTMLElement>()

// 滚动状态
const scrollTop = ref(0)
const scrollLeft = ref(0)

// 默认列宽
const defaultColumnWidth = 120

// 计算总高度
const totalHeight = computed(() => props.data.length * props.itemHeight)

// 计算总宽度
const totalWidth = computed(() => {
  return props.columns.reduce((total, column) => {
    return total + (column.width || defaultColumnWidth)
  }, 0)
})

// 计算可见项目数量
const visibleCount = computed(() => {
  return Math.ceil(props.containerHeight / props.itemHeight) + props.bufferSize * 2
})

// 计算开始索引
const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - props.bufferSize)
})

// 计算结束索引
const endIndex = computed(() => {
  return Math.min(props.data.length - 1, startIndex.value + visibleCount.value)
})

// 计算可见项目
const visibleItems = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value + 1)
})

// 计算开始偏移量
const startOffset = computed(() => {
  return startIndex.value * props.itemHeight
})

// 获取列的左偏移量
const getColumnLeft = (columnIndex: number): number => {
  let left = 0
  for (let i = 0; i < columnIndex; i++) {
    left += props.columns[i].width || defaultColumnWidth
  }
  return left
}

// 获取单元格值
const getCellValue = (item: any, key: string): any => {
  return key.split('.').reduce((obj, k) => obj?.[k], item)
}

// 处理滚动事件
const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  scrollLeft.value = target.scrollLeft
  
  emit('scroll', scrollTop.value, scrollLeft.value)
}

// 处理行点击事件
const handleRowClick = (item: any, index: number) => {
  emit('rowClick', item, index)
}

// 滚动到指定索引
const scrollToIndex = (index: number) => {
  if (scrollRef.value) {
    const targetScrollTop = index * props.itemHeight
    scrollRef.value.scrollTop = targetScrollTop
  }
}

// 滚动到顶部
const scrollToTop = () => {
  scrollToIndex(0)
}

// 滚动到底部
const scrollToBottom = () => {
  scrollToIndex(props.data.length - 1)
}

// 监听数据变化，重置滚动位置
watch(() => props.data.length, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollTop.value = scrollRef.value.scrollTop
    }
  })
})

// 暴露方法
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom
})

onMounted(() => {
  // 初始化时同步滚动位置
  if (scrollRef.value) {
    scrollTop.value = scrollRef.value.scrollTop
  }
})
</script>

<style lang="scss" scoped>
.virtual-scroll-table {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  overflow: hidden;

  .table-header {
    position: relative;
    height: 44px;
    background-color: var(--el-bg-color-page);
    border-bottom: 1px solid var(--el-border-color);
    font-weight: 600;
    font-size: 14px;

    .table-header-cell {
      position: absolute;
      top: 0;
      height: 44px;
      display: flex;
      align-items: center;
      padding: 0 12px;
      border-right: 1px solid var(--el-border-color);
      color: var(--el-text-color-primary);
      background-color: var(--el-bg-color-page);

      &:last-child {
        border-right: none;
      }
    }
  }

  .table-scroll-container {
    position: relative;
    overflow: auto;
    
    .virtual-spacer {
      position: relative;
    }

    .virtual-viewport {
      position: absolute;
      top: 0;
      left: 0;
      
      .table-row {
        position: relative;
        border-bottom: 1px solid var(--el-border-color-lighter);
        transition: background-color 0.2s;

        &:hover {
          background-color: var(--el-bg-color-page);
        }

        &.table-row-even {
          background-color: var(--el-fill-color-blank);
        }

        .table-cell {
          position: absolute;
          top: 0;
          height: 100%;
          display: flex;
          align-items: center;
          padding: 0 12px;
          border-right: 1px solid var(--el-border-color-lighter);
          color: var(--el-text-color-regular);
          font-size: 14px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;

          &:last-child {
            border-right: none;
          }
        }
      }
    }
  }

  .table-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--el-text-color-secondary);
    font-size: 14px;
  }

  .table-empty {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100%;
  }
}

// 暗黑主题适配
.dark {
  .virtual-scroll-table {
    .table-header {
      background-color: var(--el-bg-color-overlay);
    }
    
    .table-row {
      &.table-row-even {
        background-color: var(--el-fill-color-darker);
      }
    }
  }
}
</style>