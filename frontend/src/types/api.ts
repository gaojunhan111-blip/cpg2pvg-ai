/**
 * API响应类型定义
 * API Response Type Definitions
 */

import { BaseResponse, PaginatedResponse, User, AuthResponse, Guideline, Task, FileUploadResponse, FileListResponse, StorageStats } from './index'

// ==================== 认证API ====================

export interface LoginApiResponse extends BaseResponse<AuthResponse> {}

export interface RegisterApiResponse extends BaseResponse<User> {}

export interface RefreshTokenApiResponse extends BaseResponse<AuthResponse> {}

export interface GetCurrentUserApiResponse extends BaseResponse<User> {}

export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
}

export interface ChangePasswordApiResponse extends BaseResponse<{ message: string }> {}

export interface ResetPasswordRequestResponse extends BaseResponse<{ message: string }> {}

// ==================== 用户API ====================

export interface GetUsersParams {
  page?: number
  pageSize?: number
  search?: string
  role?: string
  status?: string
}

export interface GetUsersApiResponse extends PaginatedResponse<User> {}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  fullName?: string
  role: 'admin' | 'professional' | 'user'
}

export interface CreateUserApiResponse extends BaseResponse<User> {}

export interface UpdateUserRequest {
  username?: string
  email?: string
  fullName?: string
  role?: 'admin' | 'professional' | 'user'
  status?: 'active' | 'inactive' | 'pending'
}

export interface UpdateUserApiResponse extends BaseResponse<User> {}

export interface DeleteUserApiResponse extends BaseResponse<{ message: string }> {}

// ==================== 指南API ====================

export interface GetGuidelinesParams {
  page?: number
  pageSize?: number
  search?: string
  status?: string
  fileType?: string
  processingMode?: string
  tags?: string[]
  dateRange?: [string, string]
}

export interface GetGuidelinesApiResponse extends PaginatedResponse<Guideline> {}

export interface UploadGuidelineRequest {
  file: File
  title: string
  description?: string
  author?: string
  publisher?: string
  publicationYear?: number
  tags?: string[]
  processingMode?: 'slow' | 'fast' | 'custom'
  priority?: number
  isPublic?: boolean
}

export interface UploadGuidelineApiResponse extends BaseResponse<{
  guidelineId: string
  taskId: string
  message: string
}> {}

export interface GetGuidelineApiResponse extends BaseResponse<Guideline> {}

export interface UpdateGuidelineRequest {
  title?: string
  description?: string
  author?: string
  publisher?: string
  publicationYear?: number
  tags?: string[]
  isPublic?: boolean
}

export interface UpdateGuidelineApiResponse extends BaseResponse<Guideline> {}

export interface DeleteGuidelineApiResponse extends BaseResponse<{ message: string }> {}

// ==================== 任务API ====================

export interface GetTasksParams {
  page?: number
  pageSize?: number
  search?: string
  status?: string
  taskType?: string
  priority?: string
  dateRange?: [string, string]
  guidelineId?: number
}

export interface GetTasksApiResponse extends PaginatedResponse<Task> {}

export interface GetTaskApiResponse extends BaseResponse<Task> {}

export interface CancelTaskApiResponse extends BaseResponse<{ message: string }> {}

export interface RetryTaskApiResponse extends BaseResponse<Task> {}

// ==================== 工作流API ====================

export interface ExecuteWorkflowRequest {
  guidelineId: string
  workflowType: 'slow' | 'fast' | 'custom'
  config?: Record<string, any>
}

export interface ExecuteWorkflowApiResponse extends BaseResponse<{
  executionId: string
  taskId: string
  message: string
}> {}

export interface GetWorkflowStatusParams {
  executionId: string
}

export interface GetWorkflowStatusApiResponse extends BaseResponse<{
  executionId: string
  status: string
  progress: number
  currentStep?: string
  steps: Array<{
    name: string
    status: string
    progress: number
    startTime?: string
    endTime?: string
    duration?: number
  }>
  startTime?: string
  endTime?: string
  duration?: number
}> {}

export interface GetWorkflowStatisticsApiResponse extends BaseResponse<{
  totalExecutions: number
  successfulExecutions: number
  failedExecutions: number
  averageExecutionTime: number
  executionsByType: Record<string, number>
  executionsByStatus: Record<string, number>
}> {}

// ==================== 文件API ====================

export interface UploadFileRequest {
  file: File
  folder?: string
}

export interface UploadFileApiResponse extends BaseResponse<FileUploadResponse> {}

export interface DownloadFileParams {
  filePath: string
}

export interface ListFilesParams {
  path?: string
}

export interface ListFilesApiResponse extends BaseResponse<FileListResponse> {}

export interface DeleteFileParams {
  filePath: string
}

export interface DeleteFileApiResponse extends BaseResponse<{ message: string }> {}

export interface GetStorageStatsApiResponse extends BaseResponse<StorageStats> {}

// ==================== 健康检查API ====================

export interface HealthCheckApiResponse extends BaseResponse<{
  status: string
  service: string
  version: string
  timestamp: number
  dependencies: {
    database: 'healthy' | 'unhealthy'
    redis: 'healthy' | 'unhealthy'
    celery: 'healthy' | 'unhealthy'
  }
}> {}

export interface DetailedHealthCheckApiResponse extends BaseResponse<{
  status: string
  service: string
  version: string
  timestamp: number
  uptime: number
  system: {
    cpu: number
    memory: number
    disk: number
  }
  database: {
    status: 'healthy' | 'unhealthy'
    responseTime: number
    connectionCount: number
  }
  redis: {
    status: 'healthy' | 'unhealthy'
    responseTime: number
    memoryUsage: number
  }
  celery: {
    status: 'healthy' | 'unhealthy'
    activeWorkers: number
    pendingTasks: number
    activeTasks: number
  }
}> {}

// ==================== SSE事件类型 ====================

export interface TaskProgressEvent {
  type: 'progress'
  data: {
    taskId: string
    progress: number
    currentStep?: string
    message?: string
    timestamp: string
  }
}

export interface TaskStatusEvent {
  type: 'status'
  data: {
    taskId: string
    status: string
    message?: string
    timestamp: string
  }
}

export interface TaskErrorEvent {
  type: 'error'
  data: {
    taskId: string
    error: string
    details?: any
    timestamp: string
  }
}

export interface TaskCompletedEvent {
  type: 'completed'
  data: {
    taskId: string
    result: any
    duration: number
    timestamp: string
  }
}

export type SSEEvent = TaskProgressEvent | TaskStatusEvent | TaskErrorEvent | TaskCompletedEvent