/**
 * WebSocket连接配置TypeScript类型定义
 * WebSocket Connection Configuration TypeScript Type Definitions
 *
 * 这个文件定义了WebSocket连接相关的类型，确保前后端一致性
 * This file defines WebSocket connection related types for frontend-backend consistency
 */

// ==================== 枚举类型 ====================

export type WebSocketMessageType =
  // 连接管理
  | 'connect'
  | 'disconnect'
  | 'heartbeat'
  | 'ping'
  | 'pong'

  // 认证相关
  | 'auth'
  | 'auth_response'

  // 任务相关
  | 'task_update'
  | 'task_progress'
  | 'task_status'
  | 'task_step'
  | 'task_completed'
  | 'task_failed'
  | 'task_cancelled'

  // 工作流相关
  | 'workflow_update'
  | 'workflow_phase'
  | 'workflow_node'
  | 'workflow_completed'
  | 'workflow_failed'

  // 系统相关
  | 'system_notification'
  | 'error'
  | 'warning'
  | 'info'

  // 文件相关
  | 'file_upload_progress'
  | 'file_processing'
  | 'file_completed'

export type WebSocketConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnecting'
  | 'disconnected'
  | 'reconnecting'
  | 'error'

export type WebSocketErrorCode =
  | 'CONNECTION_FAILED'
  | 'AUTHENTICATION_FAILED'
  | 'AUTHENTICATION_EXPIRED'
  | 'CONNECTION_TIMEOUT'
  | 'CONNECTION_LOST'
  | 'MAX_RECONNECT_ATTEMPTS_REACHED'
  | 'INVALID_MESSAGE_FORMAT'
  | 'UNSUPPORTED_MESSAGE_TYPE'
  | 'RATE_LIMIT_EXCEEDED'
  | 'SERVER_ERROR'
  | 'NETWORK_ERROR'

// ==================== 消息结构 ====================

export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType
  data?: T
  timestamp: number
  messageId: string
  requestId?: string
  error?: WebSocketError
}

export interface WebSocketError {
  code: WebSocketErrorCode
  message: string
  details?: Record<string, any>
}

// ==================== 具体消息类型 ====================

export interface AuthData {
  token: string
  refreshToken?: string
  userId?: string
}

export interface AuthResponseData {
  success: boolean
  userId?: string
  permissions?: string[]
  expiresIn?: number
  error?: string
}

export interface TaskUpdateData {
  taskId: string
  status: string
  progress?: number
  currentStep?: string
  completedSteps?: number
  totalSteps?: number
  error?: string
  result?: any
  metadata?: Record<string, any>
}

export interface TaskProgressData {
  taskId: string
  progress: number
  currentStep?: string
  stepProgress?: number
  estimatedTimeRemaining?: number
  message?: string
  data?: Record<string, any>
}

export interface WorkflowUpdateData {
  workflowId: string
  taskId?: string
  status: string
  currentPhase?: string
  currentNode?: string
  completedNodes: string[]
  progress: number
  estimatedCompletion?: number
  totalCost?: number
  tokensUsed?: number
  qualityScore?: number
  error?: string
  nodeResults?: Record<string, any>
}

export interface WorkflowNodeData {
  nodeId: string
  nodeName: string
  status: string
  progress: number
  startTime?: number
  endTime?: number
  duration?: number
  input?: any
  output?: any
  error?: string
  metadata?: Record<string, any>
}

export interface FileUploadProgressData {
  fileId: string
  fileName: string
  progress: number
  bytesUploaded: number
  totalBytes: number
  uploadSpeed?: number
  timeRemaining?: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
}

export interface FileProcessingData {
  fileId: string
  fileName: string
  status: 'parsing' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage?: string
  stages?: Array<{
    name: string
    status: string
    progress: number
    message?: string
  }>
  error?: string
  result?: any
}

export interface SystemNotificationData {
  title: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  persistent?: boolean
  actions?: Array<{
    label: string
    action: string
    type?: 'primary' | 'default' | 'danger'
  }>
  metadata?: Record<string, any>
}

export interface HeartbeatData {
  timestamp: number
  serverTime?: number
  latency?: number
  connectionId?: string
}

// ==================== 配置结构 ====================

export interface WebSocketConfig {
  // 连接配置
  url: string
  protocol?: 'ws' | 'wss'
  port?: number
  path?: string

  // 重连配置
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectInterval?: number
  reconnectBackoffFactor?: number
  maxReconnectInterval?: number

  // 心跳配置
  enableHeartbeat?: boolean
  heartbeatInterval?: number
  heartbeatTimeout?: number
  heartbeatRetryCount?: number

  // 消息配置
  messageTimeout?: number
  maxMessageSize?: number
  bufferSize?: number

  // 认证配置
  authRequired?: boolean
  authTimeout?: number
  tokenRefreshThreshold?: number

  // 性能配置
  compression?: boolean
  enableStatistics?: boolean
  connectionTimeout?: number

  // 调试配置
  debug?: boolean
  logMessages?: boolean
}

export interface ConnectionStatistics {
  // 连接统计
  totalConnections: number
  successfulConnections: number
  failedConnections: number
  reconnections: number
  currentConnections: number

  // 消息统计
  messagesSent: number
  messagesReceived: number
  bytesSent: number
  bytesReceived: number

  // 时间统计
  totalConnectionTime: number
  averageConnectionTime: number
  lastConnectionTime?: number
  lastMessageTime?: number

  // 错误统计
  connectionErrors: number
  messageErrors: number
  timeoutErrors: number
  authErrors: number
}

export interface ConnectionQuality {
  latency: number // 延迟 (毫秒)
  packetLoss: number // 丢包率 (百分比)
  jitter: number // 抖动 (毫秒)
  bandwidth: number // 带宽 (kbps)
  qualityScore: number // 质量评分 (0-100)
}

// ==================== 事件类型 ====================

export interface WebSocketEvent<T = any> {
  type: 'open' | 'close' | 'error' | 'message'
  data?: T
  timestamp: number
}

export interface WebSocketOpenEvent extends WebSocketEvent {
  type: 'open'
  data: {
    url: string
    protocol?: string
  }
}

export interface WebSocketCloseEvent extends WebSocketEvent {
  type: 'close'
  data: {
    code: number
    reason: string
    wasClean: boolean
  }
}

export interface WebSocketErrorEvent extends WebSocketEvent {
  type: 'error'
  data: {
    error: Error | WebSocketError
    code?: WebSocketErrorCode
  }
}

export interface WebSocketMessageEvent<T = any> extends WebSocketEvent<T> {
  type: 'message'
  data: {
    message: WebSocketMessage<T>
    rawMessage: MessageEvent
  }
}

// ==================== Hook 和组件类型 ====================

export interface UseWebSocketOptions<T = any> {
  config?: Partial<WebSocketConfig>
  onOpen?: (event: WebSocketOpenEvent) => void
  onClose?: (event: WebSocketCloseEvent) => void
  onError?: (event: WebSocketErrorEvent) => void
  onMessage?: (event: WebSocketMessageEvent<T>) => void
  onReconnect?: (attempt: number, maxAttempts: number) => void
  onHeartbeat?: (latency: number) => void
  onConnectionQualityChange?: (quality: ConnectionQuality) => void
  enableAutoReconnect?: boolean
  enableHeartbeat?: boolean
  enableStatistics?: boolean
  debug?: boolean
}

export interface UseWebSocketReturn<T = any> {
  // 连接状态
  status: WebSocketConnectionStatus
  isConnected: boolean
  isConnecting: boolean
  error: WebSocketError | null

  // 连接信息
  url: string
  connectionId?: string
  connectTime?: number
  lastMessageTime?: number

  // 统计信息
  statistics: ConnectionStatistics
  quality: ConnectionQuality

  // 操作方法
  connect: (url?: string, config?: Partial<WebSocketConfig>) => Promise<void>
  disconnect: () => void
  reconnect: () => Promise<void>
  send: <K = any>(message: WebSocketMessage<K>) => Promise<void>
  sendMessage: <K = any>(type: WebSocketMessageType, data?: K) => Promise<void>

  // 实用方法
  ping: () => Promise<number> // 返回延迟
  getConnectionInfo: () => any
  resetStatistics: () => void
}

// ==================== 任务流特定类型 ====================

export interface TaskStreamOptions extends UseWebSocketOptions {
  taskId?: string
  onProgress?: (progress: TaskProgressData) => void
  onStatusChange?: (status: string, taskId: string) => void
  onStepChange?: (step: string, taskId: string) => void
  onCompleted?: (result: any, taskId: string) => void
  onFailed?: (error: string, taskId: string) => void
  onCancelled?: (taskId: string) => void
  autoSubscribe?: boolean
}

export interface TaskStreamReturn extends UseWebSocketReturn {
  taskProgress: TaskProgressData | null
  subscribe: (taskId: string) => Promise<void>
  unsubscribe: (taskId: string) => Promise<void>
  subscribeToMultiple: (taskIds: string[]) => Promise<void>
  unsubscribeFromAll: () => Promise<void>
}

// ==================== 工作流流特定类型 ====================

export interface WorkflowStreamOptions extends UseWebSocketOptions {
  workflowId?: string
  onPhaseChange?: (phase: string, workflowId: string) => void
  onNodeUpdate?: (node: WorkflowNodeData, workflowId: string) => void
  onNodeCompleted?: (node: WorkflowNodeData, workflowId: string) => void
  onNodeFailed?: (node: WorkflowNodeData, workflowId: string) => void
  onWorkflowCompleted?: (result: any, workflowId: string) => void
  onWorkflowFailed?: (error: string, workflowId: string) => void
  autoSubscribe?: boolean
}

export interface WorkflowStreamReturn extends UseWebSocketReturn {
  workflowProgress: WorkflowUpdateData | null
  currentNode: WorkflowNodeData | null
  subscribe: (workflowId: string) => Promise<void>
  unsubscribe: (workflowId: string) => Promise<void>
  getNodeStatus: (nodeId: string) => WorkflowNodeData | null
}

// ==================== 类型守卫 ====================

export function isWebSocketMessage(obj: any): obj is WebSocketMessage {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.type === 'string' &&
    typeof obj.timestamp === 'number' &&
    typeof obj.messageId === 'string'
}

export function isAuthMessage(obj: WebSocketMessage): obj is WebSocketMessage<AuthData> {
  return obj.type === 'auth' && obj.data !== undefined
}

export function isTaskUpdateMessage(obj: WebSocketMessage): obj is WebSocketMessage<TaskUpdateData> {
  return obj.type === 'task_update' && obj.data !== undefined
}

export function isTaskProgressMessage(obj: WebSocketMessage): obj is WebSocketMessage<TaskProgressData> {
  return obj.type === 'task_progress' && obj.data !== undefined
}

export function isWorkflowUpdateMessage(obj: WebSocketMessage): obj is WebSocketMessage<WorkflowUpdateData> {
  return obj.type === 'workflow_update' && obj.data !== undefined
}

export function isErrorMessage(obj: WebSocketMessage): obj is WebSocketMessage<WebSocketError> {
  return obj.type === 'error' && obj.data !== undefined
}

export function isHeartbeatMessage(obj: WebSocketMessage): obj is WebSocketMessage<HeartbeatData> {
  return obj.type === 'heartbeat'
}

// ==================== 工厂函数 ====================

export function createWebSocketMessage<T = any>(
  type: WebSocketMessageType,
  data?: T,
  options?: Partial<Pick<WebSocketMessage<T>, 'requestId' | 'error'>>
): WebSocketMessage<T> {
  return {
    type,
    data,
    timestamp: Date.now(),
    messageId: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    requestId: options?.requestId,
    error: options?.error
  }
}

export function createAuthMessage(token: string, requestId?: string): WebSocketMessage<AuthData> {
  return createWebSocketMessage('auth', { token }, { requestId })
}

export function createHeartbeatMessage(requestId?: string): WebSocketMessage<HeartbeatData> {
  return createWebSocketMessage('heartbeat', { timestamp: Date.now() }, { requestId })
}

export function createTaskUpdateMessage(
  taskId: string,
  status: string,
  progress?: number,
  requestId?: string
): WebSocketMessage<TaskUpdateData> {
  return createWebSocketMessage('task_update', {
    taskId,
    status,
    progress
  }, { requestId })
}

export function createErrorMessage(
  code: WebSocketErrorCode,
  message: string,
  details?: Record<string, any>,
  requestId?: string
): WebSocketMessage<WebSocketError> {
  return createWebSocketMessage('error', {
    code,
    message,
    details
  }, { requestId })
}

// ==================== 默认配置 ====================

export const DEFAULT_WEBSOCKET_CONFIG: Required<WebSocketConfig> = {
  url: 'localhost:8000',
  protocol: 'ws',
  port: undefined,
  path: '/ws',
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectInterval: 3000,
  reconnectBackoffFactor: 1.5,
  maxReconnectInterval: 30000,
  enableHeartbeat: true,
  heartbeatInterval: 30000,
  heartbeatTimeout: 5000,
  heartbeatRetryCount: 3,
  messageTimeout: 10000,
  maxMessageSize: 1024 * 1024,
  bufferSize: 8192,
  authRequired: true,
  authTimeout: 5000,
  tokenRefreshThreshold: 300000,
  compression: true,
  enableStatistics: true,
  connectionTimeout: 10000,
  debug: false,
  logMessages: false
}