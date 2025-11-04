/**
 * 任务流监控Hook
 * Task Stream Monitoring Hook
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { TaskProgress, Task, TaskStatus, HookOptions } from '@/types'

interface UseTaskStreamOptions extends HookOptions {
  onProgress?: (progress: TaskProgress) => void
  onStatusChange?: (status: TaskStatus, taskId: string) => void
  onStepChange?: (step: string, taskId: string) => void
  onCompleted?: (result: any, taskId: string) => void
  onRetry?: (attempt: number, maxAttempts: number, taskId: string) => void
  autoReconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  enableHeartbeat?: boolean
  retryOnNetworkError?: boolean
}

interface UseTaskStreamReturn {
  progress: TaskProgress | null
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  reconnect: () => void
  disconnect: () => void
  task: Task | null
  reconnectAttempts: number
  lastHeartbeat: number
  connectionTime: number
}

// SSE事件类型定义
interface SSEEvent {
  type: 'progress' | 'status' | 'error' | 'completed' | 'step' | 'heartbeat'
  data: any
  timestamp: number
  taskId: string
}

export const useTaskStream = (taskId: string, options: UseTaskStreamOptions = {}): UseTaskStreamReturn => {
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [lastHeartbeat, setLastHeartbeat] = useState(0)
  const [connectionTime, setConnectionTime] = useState(0)

  // Refs for connection management
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const connectionStartTimeRef = useRef<number>(0)

  const {
    onProgress,
    onStatusChange,
    onStepChange,
    onCompleted,
    onRetry,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    enableHeartbeat = true,
    retryOnNetworkError = true
  } = options

  // Memoized options to prevent unnecessary reconnections
  const memoizedOptions = useMemo(() => ({
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeatInterval,
    enableHeartbeat,
    retryOnNetworkError
  }), [autoReconnect, reconnectInterval, maxReconnectAttempts, heartbeatInterval, enableHeartbeat, retryOnNetworkError])

  const handleHeartbeat = useCallback(() => {
    if (enableHeartbeat && isConnected) {
      setLastHeartbeat(Date.now())

      // 检查心跳超时
      if (heartbeatTimeoutRef.current) {
        clearTimeout(heartbeatTimeoutRef.current)
      }

      heartbeatTimeoutRef.current = setTimeout(() => {
        console.warn('Heartbeat timeout detected for task:', taskId)
        setError('Connection timeout - no heartbeat received')
        setIsConnected(false)

        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          onRetry?.(reconnectAttempts + 1, maxReconnectAttempts, taskId)
        }
      }, heartbeatInterval * 2) // 2倍心跳间隔作为超时
    }
  }, [enableHeartbeat, isConnected, heartbeatInterval, autoReconnect, reconnectAttempts, maxReconnectAttempts, taskId, onRetry])

  const handleEvent = useCallback((event: MessageEvent) => {
    try {
      const sseEvent: SSEEvent = JSON.parse(event.data)

      // 验证事件数据
      if (!sseEvent.type || !sseEvent.timestamp) {
        console.warn('Invalid SSE event format:', sseEvent)
        return
      }

      switch (sseEvent.type) {
        case 'progress':
          const progressData = sseEvent.data as TaskProgress
          if (progressData && typeof progressData.progress === 'number') {
            setProgress(progressData)
            onProgress?.(progressData)

            // 更新任务进度
            if (task && task.progress !== progressData.progress) {
              setTask(prev => prev ? { ...prev, progress: progressData.progress } : null)
            }
          }
          break

        case 'status':
          const statusData = sseEvent.data
          const newStatus = statusData.status as TaskStatus

          onStatusChange?.(newStatus, taskId)

          // 更新任务状态
          setTask(prev => {
            if (!prev) return null
            const updated = { ...prev, status: newStatus }

            if (statusData.errorMessage) {
              updated.errorMessage = statusData.errorMessage
            }

            // 设置时间戳
            if (newStatus === 'completed') {
              updated.endTime = new Date().toISOString()
              updated.progress = 100
            } else if (newStatus === 'running' && !prev.startTime) {
              updated.startTime = new Date().toISOString()
            }

            return updated
          })
          break

        case 'step':
          const stepData = sseEvent.data
          if (stepData.step) {
            onStepChange?.(stepData.step, taskId)
            setTask(prev => prev ? { ...prev, currentStep: stepData.step } : null)
          }
          break

        case 'heartbeat':
          handleHeartbeat()
          break

        case 'error':
          const errorData = sseEvent.data
          const errorMessage = errorData.error || errorData.message || 'Unknown error occurred'
          setError(errorMessage)
          onError?.(errorMessage)

          // 更新任务错误状态
          setTask(prev => prev ? {
            ...prev,
            status: 'failed',
            errorMessage,
            endTime: new Date().toISOString()
          } : null)
          break

        case 'completed':
          const completedData = sseEvent.data
          onCompleted?.(completedData.result, taskId)

          // 更新任务为完成状态
          setTask(prev => prev ? {
            ...prev,
            status: 'completed',
            progress: 100,
            endTime: completedData.timestamp || new Date().toISOString(),
            duration: completedData.duration,
            outputData: completedData.result
          } : null)
          break

        default:
          console.warn('Unknown SSE event type:', sseEvent.type)
      }
    } catch (err) {
      console.error('Error parsing SSE event:', err, event.data)
      const errorMessage = 'Failed to parse server event'
      setError(errorMessage)
      onError?.(errorMessage)
    }
  }, [taskId, onProgress, onStatusChange, onStepChange, onCompleted, onError, task, handleHeartbeat])

  const connect = useCallback(async () => {
    if (!taskId || isConnecting) return

    setIsConnecting(true)
    setError(null)
    connectionStartTimeRef.current = Date.now()

    // 清理之前的连接
    disconnect()

    try {
      // 验证网络连接
      if (!navigator.onLine) {
        throw new Error('No network connection available')
      }

      // 创建新的AbortController
      abortControllerRef.current = new AbortController()

      // 构建SSE URL
      const baseUrl = process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_API_URL || ''
      if (!baseUrl) {
        throw new Error('API URL not configured')
      }

      const sseUrl = `${baseUrl.replace(/\/$/, '')}/api/v1/tasks/${taskId}/stream`

      // 获取认证token
      const token = localStorage.getItem('accessToken')
      const separator = sseUrl.includes('?') ? '&' : '?'
      const urlWithToken = token ? `${sseUrl}${separator}token=${encodeURIComponent(token)}` : sseUrl

      // 创建EventSource连接
      const eventSource = new EventSource(urlWithToken)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        const connectionDuration = Date.now() - connectionStartTimeRef.current
        setConnectionTime(connectionDuration)
        setIsConnected(true)
        setIsConnecting(false)
        setReconnectAttempts(0)
        setLastHeartbeat(Date.now())
        console.log(`SSE connection established for task: ${taskId} (${connectionDuration}ms)`)

        // 启动心跳监听
        if (enableHeartbeat) {
          handleHeartbeat()
        }
      }

      eventSource.onmessage = handleEvent

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event)
        setIsConnected(false)
        setIsConnecting(false)

        const currentAttempts = reconnectAttempts

        if (eventSource.readyState === EventSource.CLOSED) {
          // 连接被关闭，尝试重连
          if (autoReconnect && currentAttempts < maxReconnectAttempts) {
            const nextAttempt = currentAttempts + 1
            setReconnectAttempts(nextAttempt)

            const delay = Math.min(reconnectInterval * Math.pow(2, currentAttempts), 30000) // 指数退避，最大30秒

            reconnectTimeoutRef.current = setTimeout(() => {
              console.log(`Attempting to reconnect ${nextAttempt}/${maxReconnectAttempts} in ${delay}ms`)
              onRetry?.(nextAttempt, maxReconnectAttempts, taskId)
              connect()
            }, delay)
          } else {
            const errorMsg = retryOnNetworkError ? 'Connection to server lost' : 'Max reconnection attempts reached'
            setError(errorMsg)
            onError?.(errorMsg)
          }
        }
      }

      // 获取初始任务信息
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/tasks/${taskId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          signal: abortControllerRef.current.signal
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        if (data.success && data.data) {
          setTask(data.data)
        } else {
          console.warn('Task not found or invalid response:', data)
        }
      } catch (fetchError) {
        if (fetchError.name !== 'AbortError') {
          console.error('Failed to fetch initial task info:', fetchError)
          // 不中断SSE连接，只记录错误
        }
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to server'
      console.error('Failed to create SSE connection:', err)
      setError(errorMessage)
      setIsConnected(false)
      setIsConnecting(false)
      onError?.(errorMessage)
    }
  }, [
    taskId,
    isConnecting,
    handleEvent,
    enableHeartbeat,
    autoReconnect,
    reconnectAttempts,
    maxReconnectAttempts,
    reconnectInterval,
    retryOnNetworkError,
    onError,
    onRetry,
    handleHeartbeat
  ])

  const disconnect = useCallback(() => {
    // 清理所有定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }

    // 关闭SSE连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    // 取消进行中的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    // 重置状态
    setIsConnected(false)
    setIsConnecting(false)
    setLastHeartbeat(0)
    setConnectionTime(0)

    console.log('SSE connection disconnected for task:', taskId)
  }, [taskId])

  const reconnect = useCallback(() => {
    disconnect()
    setReconnectAttempts(0)
    setError(null)
    connect()
  }, [disconnect, connect])

  // 初始连接
  useEffect(() => {
    if (taskId) {
      connect()
    }

    // 清理函数
    return disconnect
  }, [taskId, connect, disconnect])

  // 页面可见性变化时的处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏时断开连接以节省资源
        if (isConnected) {
          console.log('Page hidden, disconnecting SSE connection')
          disconnect()
        }
      } else if (taskId && !isConnected && !isConnecting) {
        // 页面显示且未连接时重新连接
        console.log('Page visible, reconnecting SSE connection')
        connect()
      }
    }

    const handleOnline = () => {
      // 网络恢复时尝试重连
      if (taskId && !isConnected && !isConnecting) {
        console.log('Network restored, reconnecting SSE connection')
        reconnect()
      }
    }

    const handleOffline = () => {
      // 网络断开时断开连接
      if (isConnected) {
        console.log('Network lost, disconnecting SSE connection')
        disconnect()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [taskId, isConnected, isConnecting, disconnect, connect, reconnect])

  // 心跳监控
  useEffect(() => {
    if (!enableHeartbeat || !isConnected) return

    const heartbeatCheck = setInterval(() => {
      const now = Date.now()
      const timeSinceLastHeartbeat = now - lastHeartbeat

      if (timeSinceLastHeartbeat > heartbeatInterval * 3) { // 3倍心跳间隔无响应
        console.warn('Heartbeat timeout, reconnecting...')
        setError('Connection timeout - no heartbeat received')
        setIsConnected(false)

        if (autoReconnect && reconnectAttempts < maxReconnectAttempts) {
          reconnect()
        }
      }
    }, heartbeatInterval)

    return () => clearInterval(heartbeatCheck)
  }, [enableHeartbeat, isConnected, lastHeartbeat, heartbeatInterval, autoReconnect, reconnectAttempts, maxReconnectAttempts, reconnect])

  return {
    progress,
    isConnected,
    isConnecting,
    error,
    reconnect,
    disconnect,
    task,
    reconnectAttempts,
    lastHeartbeat,
    connectionTime
  }
}

// 用于批量任务流的Hook (优化版本)
export const useBatchTaskStream = (taskIds: string[], options: UseTaskStreamOptions = {}) => {
  const [tasks, setTasks] = useState<Record<string, Task | null>>({})
  const [progresses, setProgresses] = useState<Record<string, TaskProgress | null>>({})
  const [connections, setConnections] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string | null>>({})
  const [overallStats, setOverallStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    runningTasks: 0,
    pendingTasks: 0
  })

  // 计算整体统计信息
  useEffect(() => {
    const taskValues = Object.values(tasks)
    const completedTasks = taskValues.filter(task => task?.status === 'completed').length
    const failedTasks = taskValues.filter(task => task?.status === 'failed').length
    const runningTasks = taskValues.filter(task => task?.status === 'running').length
    const pendingTasks = taskValues.filter(task => task?.status === 'pending').length

    setOverallStats({
      totalTasks: taskIds.length,
      completedTasks,
      failedTasks,
      runningTasks,
      pendingTasks
    })
  }, [tasks, taskIds.length])

  // 计算总体进度
  const totalProgress = useMemo(() => {
    const progressValues = Object.values(progresses)
    if (progressValues.length === 0) return 0

    const totalProgress = progressValues.reduce((acc, curr) => {
      return acc + (curr?.progress || 0)
    }, 0)

    return Math.round(totalProgress / progressValues.length)
  }, [progresses])

  // 计算总体连接状态
  const connectionStats = useMemo(() => {
    const connectionValues = Object.values(connections)
    const connectedCount = connectionValues.filter(Boolean).length
    const totalCount = connectionValues.length

    return {
      connected: connectedCount,
      total: totalCount,
      percentage: totalCount > 0 ? Math.round((connectedCount / totalCount) * 100) : 0
    }
  }, [connections])

  // 获取错误摘要
  const errorSummary = useMemo(() => {
    const errorEntries = Object.entries(errors)
    return errorEntries
      .filter(([_, error]) => error !== null)
      .map(([taskId, error]) => ({ taskId, error: error! }))
  }, [errors])

  // 检查是否全部完成
  const allCompleted = useMemo(() => {
    return overallStats.completedTasks === overallStats.totalTasks
  }, [overallStats])

  // 检查是否有错误
  const hasErrors = useMemo(() => {
    return overallStats.failedTasks > 0
  }, [overallStats])

  // 检查是否完成（包括成功和失败）
  const isComplete = useMemo(() => {
    return overallStats.completedTasks + overallStats.failedTasks === overallStats.totalTasks
  }, [overallStats])

  return {
    tasks,
    progresses,
    connections,
    errors,
    overallStats,
    totalProgress,
    connectionStats,
    errorSummary,
    allCompleted,
    hasErrors,
    isComplete
  }
}