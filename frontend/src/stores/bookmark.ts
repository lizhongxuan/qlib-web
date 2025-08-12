import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Bookmark {
  id: string
  path: string
  title: string
  icon?: string
  params?: Record<string, any>
  query?: Record<string, any>
  createdAt: number
  lastVisited?: number
  tags?: string[]
  category?: string
}

interface BookmarkCategory {
  id: string
  name: string
  icon?: string
  color?: string
  bookmarks: Bookmark[]
}

export const useBookmarkStore = defineStore('bookmark', () => {
  // 状态
  const bookmarks = ref<Bookmark[]>([])
  const categories = ref<BookmarkCategory[]>([
    {
      id: 'favorites',
      name: '收藏夹',
      icon: 'Star',
      color: '#f56c6c',
      bookmarks: []
    },
    {
      id: 'development',
      name: '开发相关',
      icon: 'MagicStick',
      color: '#409eff',
      bookmarks: []
    },
    {
      id: 'analysis',
      name: '分析页面',
      icon: 'DataAnalysis',
      color: '#67c23a',
      bookmarks: []
    }
  ])

  // 计算属性
  const isBookmarked = computed(() => (path: string) => {
    return bookmarks.value.some(bookmark => bookmark.path === path)
  })

  const getBookmarksByCategory = computed(() => (categoryId: string) => {
    return bookmarks.value.filter(bookmark => bookmark.category === categoryId)
  })

  const recentBookmarks = computed(() => {
    return bookmarks.value
      .filter(bookmark => bookmark.lastVisited)
      .sort((a, b) => (b.lastVisited || 0) - (a.lastVisited || 0))
      .slice(0, 5)
  })

  const bookmarksByPath = computed(() => {
    const map: Record<string, Bookmark> = {}
    bookmarks.value.forEach(bookmark => {
      map[bookmark.path] = bookmark
    })
    return map
  })

  // 动作
  const addBookmark = (bookmarkData: Omit<Bookmark, 'id' | 'createdAt'>) => {
    const bookmark: Bookmark = {
      ...bookmarkData,
      id: `bookmark-${Date.now()}`,
      createdAt: Date.now(),
      category: bookmarkData.category || 'favorites'
    }
    
    bookmarks.value.push(bookmark)
    
    // 更新分类
    updateCategoryBookmarks()
    
    // 保存到本地存储
    saveBookmarksToStorage()
  }

  const removeBookmark = (path: string) => {
    const index = bookmarks.value.findIndex(bookmark => bookmark.path === path)
    if (index > -1) {
      bookmarks.value.splice(index, 1)
      updateCategoryBookmarks()
      saveBookmarksToStorage()
    }
  }

  const updateBookmark = (id: string, updates: Partial<Bookmark>) => {
    const bookmark = bookmarks.value.find(b => b.id === id)
    if (bookmark) {
      Object.assign(bookmark, updates)
      updateCategoryBookmarks()
      saveBookmarksToStorage()
    }
  }

  const recordBookmarkVisit = (path: string) => {
    const bookmark = bookmarks.value.find(b => b.path === path)
    if (bookmark) {
      bookmark.lastVisited = Date.now()
      saveBookmarksToStorage()
    }
  }

  const moveBookmarkToCategory = (bookmarkId: string, categoryId: string) => {
    const bookmark = bookmarks.value.find(b => b.id === bookmarkId)
    if (bookmark) {
      bookmark.category = categoryId
      updateCategoryBookmarks()
      saveBookmarksToStorage()
    }
  }

  const addBookmarkTag = (bookmarkId: string, tag: string) => {
    const bookmark = bookmarks.value.find(b => b.id === bookmarkId)
    if (bookmark) {
      if (!bookmark.tags) {
        bookmark.tags = []
      }
      if (!bookmark.tags.includes(tag)) {
        bookmark.tags.push(tag)
        saveBookmarksToStorage()
      }
    }
  }

  const removeBookmarkTag = (bookmarkId: string, tag: string) => {
    const bookmark = bookmarks.value.find(b => b.id === bookmarkId)
    if (bookmark && bookmark.tags) {
      const index = bookmark.tags.indexOf(tag)
      if (index > -1) {
        bookmark.tags.splice(index, 1)
        saveBookmarksToStorage()
      }
    }
  }

  const searchBookmarks = (query: string) => {
    if (!query.trim()) return bookmarks.value
    
    const searchTerm = query.toLowerCase()
    return bookmarks.value.filter(bookmark => {
      return bookmark.title.toLowerCase().includes(searchTerm) ||
             bookmark.path.toLowerCase().includes(searchTerm) ||
             (bookmark.tags && bookmark.tags.some(tag => 
               tag.toLowerCase().includes(searchTerm)
             ))
    })
  }

  const createCategory = (name: string, icon?: string, color?: string) => {
    const category: BookmarkCategory = {
      id: `category-${Date.now()}`,
      name,
      icon,
      color,
      bookmarks: []
    }
    
    categories.value.push(category)
    saveBookmarksToStorage()
    return category
  }

  const deleteCategory = (categoryId: string) => {
    // 将该分类下的书签移到默认分类
    bookmarks.value.forEach(bookmark => {
      if (bookmark.category === categoryId) {
        bookmark.category = 'favorites'
      }
    })
    
    // 删除分类
    const index = categories.value.findIndex(c => c.id === categoryId)
    if (index > -1) {
      categories.value.splice(index, 1)
    }
    
    updateCategoryBookmarks()
    saveBookmarksToStorage()
  }

  const exportBookmarks = () => {
    const exportData = {
      bookmarks: bookmarks.value,
      categories: categories.value,
      exportedAt: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `qlib-bookmarks-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    
    URL.revokeObjectURL(url)
  }

  const importBookmarks = (data: any) => {
    try {
      if (data.bookmarks && Array.isArray(data.bookmarks)) {
        bookmarks.value = [...bookmarks.value, ...data.bookmarks]
      }
      
      if (data.categories && Array.isArray(data.categories)) {
        // 合并分类，避免重复
        data.categories.forEach((importedCategory: BookmarkCategory) => {
          const existingCategory = categories.value.find(c => c.name === importedCategory.name)
          if (!existingCategory) {
            categories.value.push(importedCategory)
          }
        })
      }
      
      updateCategoryBookmarks()
      saveBookmarksToStorage()
      return true
    } catch (error) {
      console.error('导入书签失败:', error)
      return false
    }
  }

  // 辅助函数
  const updateCategoryBookmarks = () => {
    categories.value.forEach(category => {
      category.bookmarks = bookmarks.value.filter(
        bookmark => bookmark.category === category.id
      )
    })
  }

  const saveBookmarksToStorage = () => {
    try {
      const data = {
        bookmarks: bookmarks.value,
        categories: categories.value
      }
      localStorage.setItem('qlib-bookmarks', JSON.stringify(data))
    } catch (error) {
      console.error('保存书签失败:', error)
    }
  }

  const loadBookmarksFromStorage = () => {
    try {
      const stored = localStorage.getItem('qlib-bookmarks')
      if (stored) {
        const data = JSON.parse(stored)
        if (data.bookmarks) {
          bookmarks.value = data.bookmarks
        }
        if (data.categories) {
          categories.value = data.categories
        }
        updateCategoryBookmarks()
      }
    } catch (error) {
      console.error('加载书签失败:', error)
    }
  }

  // 初始化
  const initialize = () => {
    loadBookmarksFromStorage()
    
    // 添加一些默认书签（如果没有的话）
    if (bookmarks.value.length === 0) {
      addBookmark({
        path: '/dashboard',
        title: '仪表盘',
        icon: 'Odometer',
        category: 'favorites'
      })
      
      addBookmark({
        path: '/factors',
        title: '因子开发',
        icon: 'MagicStick',
        category: 'development'
      })
    }
  }

  return {
    // 状态
    bookmarks,
    categories,
    
    // 计算属性
    isBookmarked,
    getBookmarksByCategory,
    recentBookmarks,
    bookmarksByPath,
    
    // 动作
    addBookmark,
    removeBookmark,
    updateBookmark,
    recordBookmarkVisit,
    moveBookmarkToCategory,
    addBookmarkTag,
    removeBookmarkTag,
    searchBookmarks,
    createCategory,
    deleteCategory,
    exportBookmarks,
    importBookmarks,
    initialize
  }
})