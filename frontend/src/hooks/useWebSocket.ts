/**
 * 优化的WebSocket Hook
 * Optimized WebSocket Hook

这个Hook提供了完整的WebSocket连接管理，包括重连、心跳、统计等功能
This hook provides complete WebSocket connection management including reconnection, heartbeat, statistics, etc.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import {
  WebSocketMessage,
  WebSocketConfig,
  WebSocketConnectionStatus,
  WebSocketErrorCode,
  ConnectionStatistics,
  ConnectionQuality,
  UseWebSocketOptions,
  UseWebSocketReturn,
  WebSocketEvent,
  WebSocketOpenEvent,
  WebSocketCloseEvent,
  WebSocketErrorEvent,
  WebSocketMessageEvent,
  DEFAULT_WEBSOCKET_CONFIG,
  createWebSocketMessage,
  createHeartbeatMessage,
  createErrorMessage,
  isWebSocketMessage
} from '../../../shared/constants/websocket-types'

export const useWebSocket = <T = any>(
  url?: string,
  options: UseWebSocketOptions<T> = {}
): UseWebSocketReturn<T> => {
  // 合并配置
  const config = useMemo(() => ({
    ...DEFAULT_WEBSOCKET_CONFIG,
    url: url || options.config?.url || DEFAULT_WEBSOCKET_CONFIG.url,
    ...options.config
  }), [url, options.config])

  // 状态管理
  const [status, setStatus] = useState<WebSocketConnectionStatus>('disconnected')
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<WebSocketError | null>(null)
  const [connectionId, setConnectionId] = useState<string>()
  const [connectTime, setConnectTime] = useState<number>()
  const [lastMessageTime, setLastMessageTime] = useState<number>()

  // 统计信息
  const [statistics, setStatistics] = useState<ConnectionStatistics>({
    totalConnections: 0,
    successfulConnections: 0,
    failedConnections: 0,
    reconnections: 0,
    currentConnections: 0,
    messagesSent: 0,
    messagesReceived: 0,
    bytesSent: 0,
    bytesReceived: 0,
    totalConnectionTime: 0,
    averageConnectionTime: 0,
    connectionErrors: 0,
    messageErrors: 0,
    timeoutErrors: 0,
    authErrors: 0
  })

  const [quality, setQuality] = useState<ConnectionQuality>({
    latency: 0,
    packetLoss: 0,
    jitter: 0,
    bandwidth: 0,
    qualityScore: 100
  })

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const messageQueueRef = useRef<WebSocketMessage[]>([])
  const pendingMessagesRef = useRef<Map<string, {
    message: WebSocketMessage
    resolve: (value: void) => void
    reject: (reason: any) => void
    timeout: NodeJS.Timeout
  }>>(new Map())
  const connectionStartTimeRef = useRef<number>(0)
  const lastHeartbeatTimeRef = useRef<number>(0)
  const latencyMeasurementsRef = useRef<number[]>([])
  const reconnectAttemptsRef = useRef<number>(0)
  const abortControllerRef = useRef<AbortController | null>(null)

  // 提取选项
  const {
    onOpen,
    onClose,
    onError,
    onMessage,
    onReconnect,
    onHeartbeat,
    onConnectionQualityChange,
    enableAutoReconnect = true,
    enableHeartbeat = true,
    enableStatistics = true,
    debug = false
  } = options

  // 调试日志
  const log = useCallback((level: 'info' | 'warn' | 'error', message: string, data?: any) => {
    if (debug || config.debug) {
      const timestamp = new Date().toISOString()
      console[level](`[WebSocket ${timestamp}] ${message}`, data)
    }
  }, [debug, config.debug])

  // 更新连接质量
  const updateQuality = useCallback((latency: number) => {
    latencyMeasurementsRef.current.push(latency)

    // 只保留最近10次测量
    if (latencyMeasurementsRef.current.length > 10) {
      latencyMeasurementsRef.current.shift()
    }

    // 计算平均延迟
    const avgLatency = latencyMeasurementsRef.current.reduce((sum, l) => sum + l, 0) / latencyMeasurementsRef.current.length

    // 计算抖动
    const jitter = latencyMeasurementsRef.current.length > 1
      ? Math.sqrt(
          latencyMeasurementsRef.current.reduce((sum, l) => {
            return sum + Math.pow(l - avgLatency, 2)
          }, 0) / (latencyMeasurementsRef.current.length - 1)
        )
      : 0

    // 更新质量指标
    const newQuality: ConnectionQuality = {
      latency: avgLatency,
      packetLoss: 0, // 需要实现丢包率检测
      jitter,
      bandwidth: 0, // 需要实现带宽检测
      qualityScore: Math.max(0, 100 - avgLatency / 10 - jitter / 5)
    }

    setQuality(newQuality)
    onConnectionQualityChange?.(newQuality)
  }, [onConnectionQualityChange])

  // 处理心跳
  const handleHeartbeat = useCallback(async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    try {
      const startTime = Date.now()
      const pingMessage = createHeartbeatMessage()

      wsRef.current.send(JSON.stringify(pingMessage))

      // 等待pong响应
      return new Promise<void>((resolve) => {
        pingTimeoutRef.current = setTimeout(() => {
          const latency = Date.now() - startTime
          updateQuality(latency)
          setLastHeartbeatTime(Date.now())
          onHeartbeat?.(latency)
          resolve()
        }, config.heartbeatTimeout)
      })

    } catch (err) {
      log('warn', 'Heartbeat failed', err)
      setError({
        code: 'CONNECTION_TIMEOUT',
        message: 'Heartbeat failed',
        details: { error: err }
      })
    }
  }, [config.heartbeatTimeout, log, updateQuality, onHeartbeat])

  // 启动心跳
  const startHeartbeat = useCallback(() => {
    if (!enableHeartbeat) return

    heartbeatIntervalRef.current = setInterval(() => {
      handleHeartbeat()
    }, config.heartbeatInterval)

    log('info', 'Heartbeat started', { interval: config.heartbeatInterval })
  }, [enableHeartbeat, config.heartbeatInterval, handleHeartbeat, log])

  // 停止心跳
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }
    if (pingTimeoutRef.current) {
      clearTimeout(pingTimeoutRef.current)
      pingTimeoutRef.current = null
    }
    log('info', 'Heartbeat stopped')
  }, [log])

  // 更新统计信息
  const updateStatistics = useCallback((updateFn: (stats: ConnectionStatistics) => void) => {
    if (!enableStatistics) return

    setStatistics(prev => {
      const newStats = { ...prev }
      updateFn(newStats)
      return newStats
    })
  }, [enableStatistics])

  // 处理连接打开
  const handleOpen = useCallback((event: Event) => {
    const connectionDuration = Date.now() - connectionStartTimeRef.current
    setConnectionId(`${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
    setConnectTime(Date.now())
    setStatus('connected')
    setIsConnected(true)
    setIsConnecting(false)
    setError(null)
    reconnectAttemptsRef.current = 0

    // 更新统计
    updateStatistics(stats => {
      stats.successfulConnections++
      stats.totalConnections++
      stats.currentConnections++
      stats.totalConnectionTime += connectionDuration
      stats.averageConnectionTime = stats.totalConnectionTime / stats.totalConnections
    })

    // 处理消息队列
    if (messageQueueRef.current.length > 0) {
      messageQueueRef.current.forEach(message => {
        try {
          wsRef.current?.send(JSON.stringify(message))
        } catch (err) {
          log('warn', 'Failed to send queued message', err)
        }
      })
      messageQueueRef.current = []
    }

    // 启动心跳
    startHeartbeat()

    log('info', 'WebSocket connected', {
      url: config.url,
      connectionId,
      duration: connectionDuration
    })

    onOpen?.({
      type: 'open',
      timestamp: Date.now(),
      data: {
        url: config.url,
        protocol: wsRef.current?.protocol
      }
    } as WebSocketOpenEvent)
  }, [connectionStartTimeRef, connectionId, config.url, log, onOpen, startHeartbeat, updateStatistics])

  // 处理连接关闭
  const handleClose = useCallback((event: CloseEvent) => {
    const connectionDuration = Date.now() - connectionStartTimeRef.current
    setStatus('disconnected')
    setIsConnected(false)
    setIsConnecting(false)

    // 更新统计
    updateStatistics(stats => {
      stats.currentConnections--
      stats.totalConnectionTime += connectionDuration
      stats.averageConnectionTime = stats.totalConnectionTime / Math.max(1, stats.totalConnections)
    })

    // 停止心跳
    stopHeartbeat()

    log('info', 'WebSocket disconnected', {
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean
    })

    onClose?.({
      type: 'close',
      timestamp: Date.now(),
      data: {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      }
    } as WebSocketCloseEvent)

    // 自动重连
    if (enableAutoReconnect && !event.wasClean && reconnectAttemptsRef.current < config.maxReconnectAttempts) {
      handleReconnect()
    }
  }, [connectionStartTimeRef, config.maxReconnectAttempts, enableAutoReconnect, log, onClose, stopHeartbeat, updateStatistics])

  // 处理连接错误
  const handleError = useCallback((event: Event) => {
    setStatus('error')
    setIsConnecting(false)
    setIsConnected(false)

    const wsError = {
      code: 'CONNECTION_FAILED' as WebSocketErrorCode,
      message: 'WebSocket connection failed',
      details: { error: event }
    }

    setError(wsError)

    // 更新统计
    updateStatistics(stats => {
      stats.connectionErrors++
    })

    log('error', 'WebSocket error', event)

    onError?.({
      type: 'error',
      timestamp: Date.now(),
      data: {
        error: new Error('WebSocket connection failed'),
        code: 'CONNECTION_FAILED'
      }
    } as WebSocketErrorEvent)
  }, [log, onError, updateStatistics])

  // 处理消息接收
  const handleMessage = useCallback((event: MessageEvent) => {
    setLastMessageTime(Date.now())

    try {
      const message = JSON.parse(event.data) as WebSocketMessage

      // 验证消息格式
      if (!isWebSocketMessage(message)) {
        log('warn', 'Invalid message format', message)
        return
      }

      // 更新统计
      updateStatistics(stats => {
        stats.messagesReceived++
        stats.bytesReceived += event.data.length
      })

      // 处理心跳响应
      if (message.type === 'pong') {
        const latency = Date.now() - lastHeartbeatTimeRef.current
        updateQuality(latency)
        onHeartbeat?.(latency)
        return
      }

      // 处理待处理消息
      if (message.requestId && pendingMessagesRef.current.has(message.requestId)) {
        const pending = pendingMessagesRef.current.get(message.requestId)!
        clearTimeout(pending.timeout)
        pendingMessagesRef.current.delete(message.requestId)

        if (message.error) {
          pending.reject(new Error(message.error.message))
        } else {
          pending.resolve()
        }
        return
      }

      log('info', 'Message received', message)

      onMessage?.({
        type: 'message',
        timestamp: Date.now(),
        data: {
          message,
          rawMessage: event
        }
      } as WebSocketMessageEvent)

    } catch (err) {
      log('error', 'Failed to parse message', err)

      // 更新统计
      updateStatistics(stats => {
        stats.messageErrors++
      })
    }
  }, [lastHeartbeatTimeRef, log, onMessage, onHeartbeat, updateQuality, updateStatistics])

  // 处理重连
  const handleReconnect = useCallback(() => {
    reconnectAttemptsRef.current++
    const delay = Math.min(
      config.reconnectInterval * Math.pow(config.reconnectBackoffFactor, reconnectAttemptsRef.current - 1),
      config.maxReconnectInterval
    )

    setStatus('reconnecting')

    log('info', 'Scheduling reconnect', {
      attempt: reconnectAttemptsRef.current,
      maxAttempts: config.maxReconnectAttempts,
      delay
    })

    onReconnect?.(reconnectAttemptsRef.current, config.maxReconnectAttempts)

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, delay)
  }, [config, log, onReconnect])

  // 连接WebSocket
  const connect = useCallback(async (newUrl?: string, newConfig?: Partial<WebSocketConfig>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      log('warn', 'WebSocket already connected')
      return
    }

    if (isConnecting) {
      log('warn', 'WebSocket connection in progress')
      return
    }

    const targetUrl = newUrl || config.url
    const finalConfig = { ...config, ...newConfig }

    // 构建WebSocket URL
    const wsUrl = `${finalConfig.protocol}://${targetUrl}${finalConfig.path}`

    setIsConnecting(true)
    setStatus('connecting')
    connectionStartTimeRef.current = Date.now()

    // 创建AbortController
    abortControllerRef.current = new AbortController()

    try {
      log('info', 'Connecting to WebSocket', { url: wsUrl })

      wsRef.current = new WebSocket(wsUrl)

      // 设置事件监听器
      wsRef.current.onopen = handleOpen
      wsRef.current.onclose = handleClose
      wsRef.current.onerror = handleError
      wsRef.current.onmessage = handleMessage

      // 连接超时
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          wsRef.current.close()
          setError({
            code: 'CONNECTION_TIMEOUT',
            message: 'Connection timeout',
            details: { timeout: finalConfig.connectionTimeout }
          })
        }
      }, finalConfig.connectionTimeout)

    } catch (err) {
      setIsConnecting(false)
      setStatus('error')
      setError({
        code: 'CONNECTION_FAILED',
        message: 'Failed to create WebSocket connection',
        details: { error: err }
      })

      updateStatistics(stats => {
        stats.failedConnections++
      })

      log('error', 'Failed to connect', err)
    }
  }, [config, isConnecting, handleOpen, handleClose, handleError, handleMessage, log, updateStatistics])

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    stopHeartbeat()

    if (wsRef.current) {
      wsRef.current.close(1000, 'Disconnected by user')
      wsRef.current = null
    }

    setStatus('disconnected')
    setIsConnected(false)
    setIsConnecting(false)
    setError(null)

    log('info', 'WebSocket disconnected by user')
  }, [stopHeartbeat, log])

  // 重连
  const reconnect = useCallback(async () => {
    disconnect()
    reconnectAttemptsRef.current = 0
    await connect()
  }, [disconnect, connect])

  // 发送消息
  const send = useCallback(async <K = any>(message: WebSocketMessage<K>): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        // 如果未连接，加入队列
        if (config.autoReconnect) {
          messageQueueRef.current.push(message)
          reject(new Error('WebSocket not connected - message queued'))
        } else {
          reject(new Error('WebSocket not connected'))
        }
        return
      }

      try {
        const messageData = JSON.stringify(message)
        wsRef.current.send(messageData)

        // 更新统计
        updateStatistics(stats => {
          stats.messagesSent++
          stats.bytesSent += messageData.length
        })

        log('info', 'Message sent', message)

        // 如果需要响应，设置超时
        if (message.requestId) {
          const timeout = setTimeout(() => {
            if (pendingMessagesRef.current.has(message.requestId!)) {
              pendingMessagesRef.current.delete(message.requestId!)
              reject(new Error('Message timeout'))
            }
          }, config.messageTimeout)

          pendingMessagesRef.current.set(message.requestId, {
            message,
            resolve,
            reject,
            timeout
          })
        } else {
          resolve()
        }

      } catch (err) {
        updateStatistics(stats => {
          stats.messageErrors++
        })

        log('error', 'Failed to send message', err)
        reject(err)
      }
    })
  }, [config, log, updateStatistics])

  // 发送简单消息
  const sendMessage = useCallback(async <K = any>(
    type: WebSocketMessageType,
    data?: K,
    requestId?: string
  ): Promise<void> => {
    const message = createWebSocketMessage(type, data, { requestId })
    return send(message)
  }, [send])

  // Ping
  const ping = useCallback(async (): Promise<number> => {
    const startTime = Date.now()
    await sendMessage('ping')
    return Date.now() - startTime
  }, [sendMessage])

  // 获取连接信息
  const getConnectionInfo = useCallback(() => ({
    url: config.url,
    status,
    connectionId,
    connectTime,
    lastMessageTime,
    statistics,
    quality,
    reconnectAttempts: reconnectAttemptsRef.current
  }), [config.url, status, connectionId, connectTime, lastMessageTime, statistics, quality])

  // 重置统计信息
  const resetStatistics = useCallback(() => {
    setStatistics({
      totalConnections: 0,
      successfulConnections: 0,
      failedConnections: 0,
      reconnections: 0,
      currentConnections: 0,
      messagesSent: 0,
      messagesReceived: 0,
      bytesSent: 0,
      bytesReceived: 0,
      totalConnectionTime: 0,
      averageConnectionTime: 0,
      connectionErrors: 0,
      messageErrors: 0,
      timeoutErrors: 0,
      authErrors: 0
    })

    latencyMeasurementsRef.current = []
    reconnectAttemptsRef.current = 0

    log('info', 'Statistics reset')
  }, [log])

  // 初始化连接
  useEffect(() => {
    if (url) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [url]) // 只在url变化时重新连接

  // 清理函数
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [])

  return {
    status,
    isConnected,
    isConnecting,
    error,
    url: config.url,
    connectionId,
    connectTime,
    lastMessageTime,
    statistics,
    quality,
    connect,
    disconnect,
    reconnect,
    send,
    sendMessage,
    ping,
    getConnectionInfo,
    resetStatistics
  }
}