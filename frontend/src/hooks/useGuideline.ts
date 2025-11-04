/**
 * 指南管理Hook (优化版本)
 * Guideline Management Hook (Optimized Version)
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { message } from 'antd'
import {
  Guideline,
  Task,
  TaskStatus,
  BaseResponse,
  PaginatedResponse,
  PaginationParams,
  ProcessingResult,
  HookOptions,
  CacheEntry,
  CacheConfig
} from '@/types'

interface UseGuidelineOptions extends HookOptions {
  autoFetch?: boolean
  cacheEnabled?: boolean
  cacheTTL?: number
  optimisticUpdates?: boolean
  retryFailed?: boolean
  maxRetries?: number
  retryDelay?: number
  onSuccess?: (message: string) => void
  onError?: (error: string) => void
  onCacheHit?: (key: string) => void
  onCacheMiss?: (key: string) => void
}

interface UseGuidelineReturn {
  // 数据
  guidelines: Guideline[]
  currentGuideline: Guideline | null
  processingResult: ProcessingResult | null
  task: Task | null
  favorites: string[] // 收藏的指南ID

  // 状态
  loading: boolean
  error: string | null
  pagination: {
    current: number
    pageSize: number
    total: number
  }

  // 缓存状态
  cacheStats: {
    hits: number
    misses: number
    size: number
  }

  // 操作方法
  fetchGuidelines: (params?: PaginationParams & { search?: string; status?: string; tags?: string[] }) => Promise<void>
  fetchGuideline: (id: string, forceRefresh?: boolean) => Promise<void>
  uploadGuideline: (data: FormData) => Promise<Guideline>
  updateGuideline: (id: string, data: Partial<Guideline>) => Promise<Guideline>
  deleteGuideline: (id: string) => Promise<void>
  duplicateGuideline: (id: string) => Promise<Guideline>
  startProcessing: (id: string, mode?: 'slow' | 'fast') => Promise<Task>
  pauseProcessing: (id: string) => Promise<void>
  resumeProcessing: (id: string) => Promise<void>
  cancelProcessing: (id: string) => Promise<void>
  downloadPVG: (id: string, format?: 'pdf' | 'markdown' | 'html') => Promise<void>
  toggleFavorite: (id: string) => void
  bulkDelete: (ids: string[]) => Promise<void>
  bulkUpdate: (ids: string[], data: Partial<Guideline>) => Promise<Guideline[]>

  // 缓存方法
  clearCache: () => void
  preloadCache: (ids: string[]) => Promise<void>
  invalidateCache: (pattern?: string) => void

  // 工具方法
  refresh: () => Promise<void>
  reset: () => void
  search: (query: string, options?: { debounceMs?: number }) => void
  exportData: (format: 'json' | 'csv' | 'excel') => Promise<void>
}

const DEFAULT_PAGINATION = {
  current: 1,
  pageSize: 10,
  total: 0
}

const DEFAULT_CACHE_CONFIG: CacheConfig = {
  maxSize: 100,
  defaultTTL: 5 * 60 * 1000, // 5分钟
  strategy: 'lru'
}

// 简单的内存缓存实现
class MemoryCache<T> {
  private cache = new Map<string, CacheEntry<T>>()
  private config: CacheConfig

  constructor(config: CacheConfig = DEFAULT_CACHE_CONFIG) {
    this.config = config
  }

  set(key: string, data: T, ttl?: number): void {
    const now = Date.now()
    const entry: CacheEntry<T> = {
      data,
      timestamp: now,
      expiresAt: ttl ? now + ttl : now + this.config.defaultTTL!,
      ttl: ttl || this.config.defaultTTL,
      hits: 0,
      lastAccessed: now
    }

    // LRU策略：如果缓存满了，删除最久未访问的条目
    if (this.cache.size >= this.config.maxSize!) {
      const oldestKey = this.getOldestKey()
      if (oldestKey) {
        this.cache.delete(oldestKey)
      }
    }

    this.cache.set(key, entry)
  }

  get(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    const now = Date.now()
    if (entry.expiresAt && now > entry.expiresAt) {
      this.cache.delete(key)
      return null
    }

    entry.hits++
    entry.lastAccessed = now
    return entry.data
  }

  has(key: string): boolean {
    return this.get(key) !== null
  }

  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }

  getStats(): { hits: number; misses: number; size: number } {
    let hits = 0
    for (const entry of this.cache.values()) {
      hits += entry.hits
    }
    return {
      hits,
      misses: 0, // 需要在使用时跟踪misses
      size: this.cache.size
    }
  }

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.clear()
      return
    }

    const regex = new RegExp(pattern)
    for (const [key] of this.cache.entries()) {
      if (regex.test(key)) {
        this.cache.delete(key)
      }
    }
  }

  private getOldestKey(): string | null {
    let oldestKey: string | null = null
    let oldestTime = Date.now()

    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed
        oldestKey = key
      }
    }

    return oldestKey
  }
}

export const useGuideline = (options: UseGuidelineOptions = {}): UseGuidelineReturn => {
  const [guidelines, setGuidelines] = useState<Guideline[]>([])
  const [currentGuideline, setCurrentGuideline] = useState<Guideline | null>(null)
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [favorites, setFavorites] = useState<string[]>([])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState(DEFAULT_PAGINATION)
  const [cacheStats, setCacheStats] = useState({ hits: 0, misses: 0, size: 0 })

  // 缓存和请求管理
  const cacheRef = useRef<MemoryCache<any>>(new MemoryCache())
  const abortControllerRef = useRef<AbortController | null>(null)
  const pendingRequestsRef = useRef<Map<string, Promise<any>>>(new Map())
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const {
    autoFetch = true,
    cacheEnabled = true,
    cacheTTL = 5 * 60 * 1000, // 5分钟
    optimisticUpdates = true,
    retryFailed = true,
    maxRetries = 3,
    retryDelay = 1000,
    onSuccess,
    onError,
    onCacheHit,
    onCacheMiss,
    staleTime = 30 * 1000, // 30秒
    cacheTime = 5 * 60 * 1000 // 5分钟
  } = options

  // 初始化缓存
  useEffect(() => {
    if (cacheEnabled) {
      cacheRef.current = new MemoryCache({
        maxSize: 100,
        defaultTTL: cacheTTL
      })
    }
  }, [cacheEnabled, cacheTTL])

  // 加载收藏列表
  useEffect(() => {
    try {
      const savedFavorites = localStorage.getItem('favoriteGuidelines')
      if (savedFavorites) {
        setFavorites(JSON.parse(savedFavorites))
      }
    } catch (error) {
      console.warn('Failed to load favorites:', error)
    }
  }, [])

  // 保存收藏列表
  const saveFavorites = useCallback((favoritesList: string[]) => {
    try {
      localStorage.setItem('favoriteGuidelines', JSON.stringify(favoritesList))
    } catch (error) {
      console.warn('Failed to save favorites:', error)
    }
  }, [])

  // 获取认证token
  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('accessToken')
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }, [])

  // 构建查询参数
  const buildQueryParams = useCallback((params: GetGuidelinesParams = {}) => {
    const searchParams = new URLSearchParams()

    if (params.page) searchParams.append('page', params.page.toString())
    if (params.pageSize) searchParams.append('pageSize', params.pageSize.toString())
    if (params.search) searchParams.append('search', params.search)
    if (params.status) searchParams.append('status', params.status)
    if (params.fileType) searchParams.append('fileType', params.fileType)
    if (params.processingMode) searchParams.append('processingMode', params.processingMode)
    if (params.tags?.length) {
      params.tags.forEach(tag => searchParams.append('tags', tag))
    }
    if (params.dateRange) {
      searchParams.append('startDate', params.dateRange[0])
      searchParams.append('endDate', params.dateRange[1])
    }

    return searchParams.toString()
  }, [])

  // 处理API错误
  const handleApiError = useCallback((error: any) => {
    const errorMessage = error?.response?.data?.message || error?.message || '请求失败'
    setError(errorMessage)
    onError?.(errorMessage)
    console.error('API Error:', error)
    return errorMessage
  }, [onError])

  // 获取指南列表
  const fetchGuidelines = useCallback(async (params: GetGuidelinesParams = {}) => {
    setLoading(true)
    setError(null)

    try {
      const queryParams = buildQueryParams({
        page: params.page || pagination.current,
        pageSize: params.pageSize || pagination.pageSize,
        ...params
      })

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines?${queryParams}`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: PaginatedResponse<Guideline> = await response.json()

      if (data.success) {
        setGuidelines(data.data || [])
        setPagination(data.pagination || DEFAULT_PAGINATION)
      } else {
        throw new Error(data.message || '获取指南列表失败')
      }

    } catch (error) {
      handleApiError(error)
    } finally {
      setLoading(false)
    }
  }, [pagination, buildQueryParams, getAuthHeaders, handleApiError])

  // 获取单个指南
  const fetchGuideline = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${id}`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: BaseResponse<Guideline> = await response.json()

      if (data.success) {
        setCurrentGuideline(data.data)

        // 如果有处理结果，也获取处理结果
        if (data.data?.status === 'completed') {
          await fetchProcessingResult(id)
        }
      } else {
        throw new Error(data.message || '获取指南详情失败')
      }

    } catch (error) {
      handleApiError(error)
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders, handleApiError])

  // 获取处理结果
  const fetchProcessingResult = useCallback(async (guidelineId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${guidelineId}/processing-result`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: BaseResponse<ProcessingResult> = await response.json()

      if (data.success) {
        setProcessingResult(data.data)
      }

    } catch (error) {
      console.error('Failed to fetch processing result:', error)
    }
  }, [getAuthHeaders])

  // 上传指南
  const uploadGuideline = useCallback(async (formData: FormData): Promise<Guideline> => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/upload`,
        {
          method: 'POST',
          headers: {
            ...getAuthHeaders()
          },
          body: formData
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: BaseResponse<Guideline> = await response.json()

      if (data.success) {
        const guideline = data.data!
        setGuidelines(prev => [guideline, ...prev])
        onSuccess?.('指南上传成功')
        return guideline
      } else {
        throw new Error(data.message || '上传失败')
      }

    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders, handleApiError, onSuccess])

  // 更新指南
  const updateGuideline = useCallback(async (id: string, data: Partial<Guideline>): Promise<Guideline> => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify(data)
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const responseData: BaseResponse<Guideline> = await response.json()

      if (responseData.success) {
        const updatedGuideline = responseData.data!

        // 更新列表中的指南
        setGuidelines(prev =>
          prev.map(g => g.id === updatedGuideline.id ? updatedGuideline : g)
        )

        // 更新当前指南
        if (currentGuideline?.id === updatedGuideline.id) {
          setCurrentGuideline(updatedGuideline)
        }

        onSuccess?.('指南更新成功')
        return updatedGuideline
      } else {
        throw new Error(responseData.message || '更新失败')
      }

    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [currentGuideline, getAuthHeaders, handleApiError, onSuccess])

  // 删除指南
  const deleteGuideline = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${id}`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: BaseResponse = await response.json()

      if (data.success) {
        setGuidelines(prev => prev.filter(g => g.id !== id))
        if (currentGuideline?.id === id) {
          setCurrentGuideline(null)
        }
        onSuccess?.('指南删除成功')
      } else {
        throw new Error(data.message || '删除失败')
      }

    } catch (error) {
      handleApiError(error)
    } finally {
      setLoading(false)
    }
  }, [currentGuideline, getAuthHeaders, handleApiError, onSuccess])

  // 开始处理指南
  const startProcessing = useCallback(async (id: string, mode: 'slow' | 'fast' = 'slow'): Promise<Task> => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${id}/process`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({ processingMode: mode })
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: BaseResponse<Task> = await response.json()

      if (data.success) {
        const task = data.data!
        setTask(task)

        // 更新指南状态
        if (currentGuideline?.id === id) {
          setCurrentGuideline(prev => prev ? {
            ...prev,
            status: 'processing'
          } : null)
        }

        onSuccess?.('开始处理指南')
        return task
      } else {
        throw new Error(data.message || '处理启动失败')
      }

    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [currentGuideline, getAuthHeaders, handleApiError, onSuccess])

  // 下载PVG
  const downloadPVG = useCallback(async (id: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/${id}/pvg/download`,
        {
          headers: {
            ...getAuthHeaders()
          }
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // 创建下载链接
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // 从响应头获取文件名
      const contentDisposition = response.headers.get('content-disposition')
      let fileName = `pvg-${id}.pdf`
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (fileNameMatch?.[1]) {
          fileName = fileNameMatch[1].replace(/['"]/g, '')
        }
      }

      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      onSuccess?.('PVG下载成功')

    } catch (error) {
      handleApiError(error)
    }
  }, [getAuthHeaders, handleApiError, onSuccess])

  // 刷新数据
  const refresh = useCallback(async () => {
    await fetchGuidelines()
  }, [fetchGuidelines])

  // 重置状态
  const reset = useCallback(() => {
    setGuidelines([])
    setCurrentGuideline(null)
    setProcessingResult(null)
    setTask(null)
    setLoading(false)
    setError(null)
    setPagination(DEFAULT_PAGINATION)
  }, [])

  // 自动加载
  useEffect(() => {
    if (autoFetch) {
      fetchGuidelines()
    }
  }, [autoFetch, fetchGuidelines])

  return {
    // 数据
    guidelines,
    currentGuideline,
    processingResult,
    task,

    // 状态
    loading,
    error,
    pagination,

    // 操作方法
    fetchGuidelines,
    fetchGuideline,
    uploadGuideline,
    updateGuideline,
    deleteGuideline,
    startProcessing,
    downloadPVG,

    // 工具方法
    refresh,
    reset
  }
}

// 用于指南统计的Hook
export const useGuidelineStats = () => {
  const [stats, setStats] = useState({
    total: 0,
    uploaded: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    thisWeek: 0,
    thisMonth: 0
  })
  const [loading, setLoading] = useState(false)

  const fetchStats = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('accessToken')
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines/stats`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setStats(data.data)
        }
      }
    } catch (error) {
      console.error('Failed to fetch guideline stats:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, loading, refresh: fetchStats }
}