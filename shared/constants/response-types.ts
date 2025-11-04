/**
 * 统一响应格式TypeScript类型定义
 * Unified Response Format TypeScript Type Definitions
 *
 * 这个文件定义了前后端共享的响应格式类型，确保一致性
 * This file defines shared response format types for frontend-backend consistency
 */

// ==================== 基础响应类型 ====================

export type ResponseStatus = 'success' | 'error' | 'partial' | 'pending'

export type ErrorCode =
  // 通用错误 (1000-1999)
  | 'UNKNOWN_ERROR'
  | 'INVALID_REQUEST'
  | 'VALIDATION_ERROR'
  | 'MISSING_PARAMETER'
  | 'INVALID_PARAMETER'
  | 'INVALID_FORMAT'
  | 'RATE_LIMIT_EXCEEDED'

  // 认证错误 (2000-2999)
  | 'UNAUTHORIZED'
  | 'AUTHENTICATION_FAILED'
  | 'TOKEN_EXPIRED'
  | 'TOKEN_INVALID'
  | 'FORBIDDEN'
  | 'INSUFFICIENT_PERMISSIONS'

  // 业务逻辑错误 (3000-3999)
  | 'RESOURCE_NOT_FOUND'
  | 'RESOURCE_ALREADY_EXISTS'
  | 'OPERATION_NOT_ALLOWED'
  | 'INVALID_STATE'
  | 'DUPLICATE_OPERATION'

  // 文件处理错误 (4000-4999)
  | 'FILE_NOT_FOUND'
  | 'FILE_TOO_LARGE'
  | 'UNSUPPORTED_FILE_TYPE'
  | 'FILE_UPLOAD_FAILED'
  | 'FILE_PROCESSING_FAILED'
  | 'CORRUPTED_FILE'

  // 系统错误 (5000-5999)
  | 'INTERNAL_SERVER_ERROR'
  | 'DATABASE_ERROR'
  | 'EXTERNAL_SERVICE_ERROR'
  | 'NETWORK_ERROR'
  | 'TIMEOUT_ERROR'
  | 'SERVICE_UNAVAILABLE'

  // 任务处理错误 (6000-6999)
  | 'TASK_NOT_FOUND'
  | 'TASK_FAILED'
  | 'TASK_CANCELLED'
  | 'TASK_TIMEOUT'
  | 'PROCESSING_ERROR'

export interface ErrorInfo {
  code: ErrorCode
  message: string
  details?: Record<string, any>
  cause?: string
}

export interface BaseResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: ErrorInfo
  timestamp: string
  requestId?: string
  statusCode?: number
}

export interface SuccessResponse<T = any> extends BaseResponse<T> {
  success: true
  data: T
  error?: never
}

export interface ErrorResponse extends BaseResponse {
  success: false
  data?: never
  error: ErrorInfo
}

export interface ValidationErrorInfo extends ErrorInfo {
  field: string
  value?: string
}

export interface ValidationErrorResponse extends ErrorResponse {
  error: ValidationErrorInfo
}

// ==================== 分页响应类型 ====================

export interface PaginationInfo {
  current: number
  pageSize: number
  total: number
  totalPages: number
  hasNext?: boolean
  hasPrev?: boolean
}

export interface PaginatedResponse<T = any> extends SuccessResponse<T[]> {
  pagination: PaginationInfo
}

// ==================== 任务响应类型 ====================

export interface TaskInfo {
  taskId: string
  status: string
  progress?: number
  estimatedTime?: number
  startTime?: string
  endTime?: string
  duration?: number
  errorMessage?: string
  result?: any
}

export interface TaskResponse extends SuccessResponse<TaskInfo> {
  data: TaskInfo
}

// ==================== 文件上传响应类型 ====================

export interface FileInfo {
  id: string
  originalFilename: string
  filename: string
  filePath: string
  fileSize: number
  fileType: string
  fileHash: string
  mimeType: string
  uploadTime: string
  status?: 'uploading' | 'completed' | 'failed'
  thumbnailUrl?: string
  downloadUrl?: string
}

export interface FileUploadResponse extends SuccessResponse<FileInfo> {
  data: FileInfo
}

// ==================== 具体业务响应类型 ====================

export interface UserInfo {
  id: string
  username: string
  email: string
  name?: string
  role: string
  status: string
  createdAt: string
  lastLoginAt?: string
  avatar?: string
  organization?: string
  department?: string
}

export interface AuthResponse extends SuccessResponse<{
  accessToken: string
  refreshToken: string
  expiresIn: number
  tokenType: string
  userInfo: UserInfo
}> {
  data: {
    accessToken: string
    refreshToken: string
    expiresIn: number
    tokenType: string
    userInfo: UserInfo
  }
}

export interface GuidelineInfo {
  id: string
  title: string
  description?: string
  originalFilename: string
  filePath: string
  fileSize: number
  fileType: string
  fileHash: string
  status: string
  processingMode: string
  progress: number
  createdAt: string
  updatedAt: string
  userId?: string
  isPublic: boolean
  tags: string[]
  version: string
  viewCount: number
  downloadCount: number
  shareCount: number
}

export interface GuidelineListResponse extends PaginatedResponse<GuidelineInfo[]> {
  data: GuidelineInfo[]
}

// ==================== 响应工具函数 ====================

/**
 * 检查响应是否成功
 */
export function isSuccessResponse<T = any>(response: BaseResponse<T>): response is SuccessResponse<T> {
  return response.success === true
}

/**
 * 检查响应是否为错误
 */
export function isErrorResponse(response: BaseResponse): response is ErrorResponse {
  return response.success === false
}

/**
 * 获取错误消息
 */
export function getErrorMessage(response: ErrorResponse): string {
  return response.error?.message || response.message || '未知错误'
}

/**
 * 获取错误详情
 */
export function getErrorDetails(response: ErrorResponse): Record<string, any> {
  return response.error?.details || {}
}

/**
 * 获取HTTP状态码
 */
export function getStatusCode(response: BaseResponse): number {
  return response.statusCode || (response.success ? 200 : 400)
}

// ==================== 响应类型守卫 ====================

/**
 * 检查是否为分页响应
 */
export function isPaginatedResponse<T = any>(response: BaseResponse): response is PaginatedResponse<T> {
  return isSuccessResponse(response) && 'pagination' in response
}

/**
 * 检查是否为任务响应
 */
export function isTaskResponse(response: BaseResponse): response is TaskResponse {
  return isSuccessResponse(response) &&
         response.data &&
         typeof response.data === 'object' &&
         'taskId' in response.data
}

/**
 * 检查是否为文件上传响应
 */
export function isFileUploadResponse(response: BaseResponse): response is FileUploadResponse {
  return isSuccessResponse(response) &&
         response.data &&
         typeof response.data === 'object' &&
         'filePath' in response.data &&
         'fileHash' in response.data
}

/**
 * 检查是否为验证错误响应
 */
export function isValidationErrorResponse(response: ErrorResponse): response is ValidationErrorResponse {
  return response.error &&
         'field' in response.error &&
         response.error.code === 'VALIDATION_ERROR'
}

// ==================== API响应包装器类型 ====================

export interface ApiResponse<T = any> {
  response: BaseResponse<T>
  status: number
  headers: Record<string, string>
  config?: any
}

export interface ApiError extends ApiResponse {
  response: ErrorResponse
}

export interface ApiSuccess<T = any> extends ApiResponse<T> {
  response: SuccessResponse<T>
}

// ==================== 请求/响应拦截器类型 ====================

export interface RequestInterceptor {
  onRequest?(config: any): any
  onRequestError?(error: any): any
}

export interface ResponseInterceptor {
  onResponse?(response: any): any
  onResponseError?(error: any): any
}

// ==================== WebSocket响应类型 ====================

export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp: string
  messageId?: string
  requestId?: string
}

export interface WebSocketError extends WebSocketMessage<ErrorInfo> {
  type: 'error'
  data: ErrorInfo
}

export interface WebSocketTaskUpdate extends WebSocketMessage<TaskInfo> {
  type: 'task_update'
  data: TaskInfo
}

export interface WebSocketNotification extends WebSocketMessage<{
  title: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
  persistent?: boolean
}> {
  type: 'notification'
}