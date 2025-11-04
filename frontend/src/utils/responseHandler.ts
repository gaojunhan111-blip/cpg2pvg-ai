/**
 * 统一响应处理工具
 * Unified Response Handler Utility

这个工具处理API响应，确保前端能正确处理统一的响应格式
This utility handles API responses, ensuring the frontend can correctly process unified response formats
 */

import {
  BaseResponse,
  SuccessResponse,
  ErrorResponse,
  ValidationErrorResponse,
  ErrorCode,
  isSuccessResponse,
  isErrorResponse,
  getErrorMessage,
  getErrorDetails,
  getStatusCode,
  isValidationErrorResponse
} from '@/types'

// 错误消息映射
const ERROR_MESSAGES: Record<ErrorCode, string> = {
  // 通用错误
  UNKNOWN_ERROR: '未知错误',
  INVALID_REQUEST: '请求格式错误',
  VALIDATION_ERROR: '数据验证失败',
  MISSING_PARAMETER: '缺少必要参数',
  INVALID_PARAMETER: '参数值无效',
  INVALID_FORMAT: '数据格式错误',
  RATE_LIMIT_EXCEEDED: '请求过于频繁，请稍后重试',

  // 认证错误
  UNAUTHORIZED: '未授权访问',
  AUTHENTICATION_FAILED: '身份验证失败',
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  TOKEN_INVALID: '令牌无效',
  FORBIDDEN: '权限不足',
  INSUFFICIENT_PERMISSIONS: '权限不足',

  // 业务逻辑错误
  RESOURCE_NOT_FOUND: '资源不存在',
  RESOURCE_ALREADY_EXISTS: '资源已存在',
  OPERATION_NOT_ALLOWED: '操作不被允许',
  INVALID_STATE: '状态无效',
  DUPLICATE_OPERATION: '重复操作',

  // 文件处理错误
  FILE_NOT_FOUND: '文件不存在',
  FILE_TOO_LARGE: '文件过大',
  UNSUPPORTED_FILE_TYPE: '不支持的文件类型',
  FILE_UPLOAD_FAILED: '文件上传失败',
  FILE_PROCESSING_FAILED: '文件处理失败',
  CORRUPTED_FILE: '文件损坏',

  // 系统错误
  INTERNAL_SERVER_ERROR: '服务器内部错误',
  DATABASE_ERROR: '数据库错误',
  EXTERNAL_SERVICE_ERROR: '外部服务错误',
  NETWORK_ERROR: '网络错误',
  TIMEOUT_ERROR: '请求超时',
  SERVICE_UNAVAILABLE: '服务不可用',

  // 任务处理错误
  TASK_NOT_FOUND: '任务不存在',
  TASK_FAILED: '任务执行失败',
  TASK_CANCELLED: '任务已取消',
  TASK_TIMEOUT: '任务执行超时',
  PROCESSING_ERROR: '处理过程出错'
}

// 错误级别定义
export enum ErrorLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

// 错误级别映射
const ERROR_LEVELS: Record<ErrorCode, ErrorLevel> = {
  UNKNOWN_ERROR: ErrorLevel.ERROR,
  INVALID_REQUEST: ErrorLevel.WARNING,
  VALIDATION_ERROR: ErrorLevel.WARNING,
  MISSING_PARAMETER: ErrorLevel.WARNING,
  INVALID_PARAMETER: ErrorLevel.WARNING,
  INVALID_FORMAT: ErrorLevel.WARNING,
  RATE_LIMIT_EXCEEDED: ErrorLevel.WARNING,

  UNAUTHORIZED: ErrorLevel.ERROR,
  AUTHENTICATION_FAILED: ErrorLevel.ERROR,
  TOKEN_EXPIRED: ErrorLevel.ERROR,
  TOKEN_INVALID: ErrorLevel.ERROR,
  FORBIDDEN: ErrorLevel.ERROR,
  INSUFFICIENT_PERMISSIONS: ErrorLevel.ERROR,

  RESOURCE_NOT_FOUND: ErrorLevel.WARNING,
  RESOURCE_ALREADY_EXISTS: ErrorLevel.WARNING,
  OPERATION_NOT_ALLOWED: ErrorLevel.WARNING,
  INVALID_STATE: ErrorLevel.WARNING,
  DUPLICATE_OPERATION: ErrorLevel.WARNING,

  FILE_NOT_FOUND: ErrorLevel.WARNING,
  FILE_TOO_LARGE: ErrorLevel.WARNING,
  UNSUPPORTED_FILE_TYPE: ErrorLevel.WARNING,
  FILE_UPLOAD_FAILED: ErrorLevel.ERROR,
  FILE_PROCESSING_FAILED: ErrorLevel.ERROR,
  CORRUPTED_FILE: ErrorLevel.ERROR,

  INTERNAL_SERVER_ERROR: ErrorLevel.CRITICAL,
  DATABASE_ERROR: ErrorLevel.CRITICAL,
  EXTERNAL_SERVICE_ERROR: ErrorLevel.ERROR,
  NETWORK_ERROR: ErrorLevel.ERROR,
  TIMEOUT_ERROR: ErrorLevel.ERROR,
  SERVICE_UNAVAILABLE: ErrorLevel.CRITICAL,

  TASK_NOT_FOUND: ErrorLevel.WARNING,
  TASK_FAILED: ErrorLevel.ERROR,
  TASK_CANCELLED: ErrorLevel.INFO,
  TASK_TIMEOUT: ErrorLevel.ERROR,
  PROCESSING_ERROR: ErrorLevel.ERROR
}

export interface ResponseHandlerOptions {
  showErrorNotification?: boolean
  autoRetry?: boolean
  retryCount?: number
  retryDelay?: number
  onValidationError?: (field: string, message: string) => void
  onAuthError?: () => void
  onNetworkError?: () => void
  onServerError?: () => void
  customErrorHandlers?: Record<ErrorCode, (error: ErrorResponse) => void>
}

export class ResponseHandler {
  private options: ResponseHandlerOptions

  constructor(options: ResponseHandlerOptions = {}) {
    this.options = {
      showErrorNotification: true,
      autoRetry: false,
      retryCount: 3,
      retryDelay: 1000,
      ...options
    }
  }

  /**
   * 处理API响应
   */
  async handleResponse<T = any>(
    response: BaseResponse<T>
  ): Promise<T> {
    // 如果是成功响应，直接返回数据
    if (isSuccessResponse(response)) {
      return response.data
    }

    // 如果是错误响应，处理错误
    if (isErrorResponse(response)) {
      await this.handleError(response)
      throw new Error(this.getDisplayMessage(response))
    }

    // 未知响应格式
    throw new Error('Invalid response format')
  }

  /**
   * 处理错误响应
   */
  async handleError(error: ErrorResponse): Promise<void> {
    const errorCode = error.error?.code as ErrorCode
    const message = this.getDisplayMessage(error)

    // 调用自定义错误处理器
    if (errorCode && this.options.customErrorHandlers?.[errorCode]) {
      this.options.customErrorHandlers[errorCode](error)
    }

    // 验证错误处理
    if (isValidationErrorResponse(error)) {
      await this.handleValidationError(error)
      return
    }

    // 认证错误处理
    if (this.isAuthError(errorCode)) {
      await this.handleAuthError(error)
      return
    }

    // 网络错误处理
    if (this.isNetworkError(errorCode)) {
      await this.handleNetworkError(error)
      return
    }

    // 服务器错误处理
    if (this.isServerError(errorCode)) {
      await this.handleServerError(error)
      return
    }

    // 默认错误处理
    await this.handleDefaultError(error, message)
  }

  /**
   * 处理验证错误
   */
  private async handleValidationError(error: ValidationErrorResponse): Promise<void> {
    const field = error.error.field
    const message = error.error.message

    if (this.options.onValidationError) {
      this.options.onValidationError(field, message)
    }

    // 显示错误通知
    if (this.options.showErrorNotification) {
      await this.showNotification(ErrorLevel.WARNING, message)
    }
  }

  /**
   * 处理认证错误
   */
  private async handleAuthError(error: ErrorResponse): Promise<void> {
    if (this.options.onAuthError) {
      this.options.onAuthError()
    } else {
      // 默认处理：重定向到登录页
      this.redirectToLogin()
    }

    if (this.options.showErrorNotification) {
      await this.showNotification(ErrorLevel.ERROR, '请重新登录')
    }
  }

  /**
   * 处理网络错误
   */
  private async handleNetworkError(error: ErrorResponse): Promise<void> {
    if (this.options.onNetworkError) {
      this.options.onNetworkError()
    }

    if (this.options.showErrorNotification) {
      await this.showNotification(ErrorLevel.ERROR, '网络连接异常，请检查网络设置')
    }
  }

  /**
   * 处理服务器错误
   */
  private async handleServerError(error: ErrorResponse): Promise<void> {
    if (this.options.onServerError) {
      this.options.onServerError()
    }

    const message = this.getDisplayMessage(error)
    if (this.options.showErrorNotification) {
      await this.showNotification(ErrorLevel.CRITICAL, message)
    }
  }

  /**
   * 默认错误处理
   */
  private async handleDefaultError(error: ErrorResponse, message: string): Promise<void> {
    if (this.options.showErrorNotification) {
      const level = this.getErrorLevel(error.error?.code as ErrorCode)
      await this.showNotification(level, message)
    }
  }

  /**
   * 获取显示消息
   */
  private getDisplayMessage(error: ErrorResponse): string {
    const errorCode = error.error?.code as ErrorCode

    // 优先使用自定义消息映射
    if (errorCode && ERROR_MESSAGES[errorCode]) {
      return ERROR_MESSAGES[errorCode]
    }

    // 使用响应中的消息
    return getErrorMessage(error)
  }

  /**
   * 获取错误级别
   */
  private getErrorLevel(errorCode?: ErrorCode): ErrorLevel {
    if (!errorCode) {
      return ErrorLevel.ERROR
    }

    return ERROR_LEVELS[errorCode] || ErrorLevel.ERROR
  }

  /**
   * 判断是否为认证错误
   */
  private isAuthError(errorCode?: ErrorCode): boolean {
    if (!errorCode) return false

    const authErrors = [
      ErrorCode.UNAUTHORIZED,
      ErrorCode.AUTHENTICATION_FAILED,
      ErrorCode.TOKEN_EXPIRED,
      ErrorCode.TOKEN_INVALID,
      ErrorCode.FORBIDDEN,
      ErrorCode.INSUFFICIENT_PERMISSIONS
    ]

    return authErrors.includes(errorCode)
  }

  /**
   * 判断是否为网络错误
   */
  private isNetworkError(errorCode?: ErrorCode): boolean {
    if (!errorCode) return false

    const networkErrors = [
      ErrorCode.NETWORK_ERROR,
      ErrorCode.TIMEOUT_ERROR,
      ErrorCode.SERVICE_UNAVAILABLE,
      ErrorCode.EXTERNAL_SERVICE_ERROR
    ]

    return networkErrors.includes(errorCode)
  }

  /**
   * 判断是否为服务器错误
   */
  private isServerError(errorCode?: ErrorCode): boolean {
    if (!errorCode) return false

    const serverErrors = [
      ErrorCode.INTERNAL_SERVER_ERROR,
      ErrorCode.DATABASE_ERROR,
      ErrorCode.SERVICE_UNAVAILABLE
    ]

    return serverErrors.includes(errorCode)
  }

  /**
   * 显示通知
   */
  private async showNotification(level: ErrorLevel, message: string): Promise<void> {
    // 这里可以集成你的通知组件，比如 Ant Design 的 message
    switch (level) {
      case ErrorLevel.INFO:
        // message.info(message)
        console.info(`[INFO] ${message}`)
        break
      case ErrorLevel.WARNING:
        // message.warning(message)
        console.warn(`[WARNING] ${message}`)
        break
      case ErrorLevel.ERROR:
        // message.error(message)
        console.error(`[ERROR] ${message}`)
        break
      case ErrorLevel.CRITICAL:
        // message.error(message)
        console.error(`[CRITICAL] ${message}`)
        break
    }
  }

  /**
   * 重定向到登录页
   */
  private redirectToLogin(): void {
    // 实现重定向逻辑
    window.location.href = '/login'
  }

  /**
   * 带重试的请求处理
   */
  async handleWithRetry<T = any>(
    requestFn: () => Promise<BaseResponse<T>>,
    options: Partial<ResponseHandlerOptions> = {}
  ): Promise<T> {
    const mergedOptions = { ...this.options, ...options }
    let lastError: Error | null = null

    for (let attempt = 1; attempt <= (mergedOptions.retryCount || 1); attempt++) {
      try {
        const response = await requestFn()
        return await this.handleResponse(response)
      } catch (error) {
        lastError = error as Error

        // 如果是最后一次尝试或错误不可重试，直接抛出
        if (attempt >= (mergedOptions.retryCount || 1) || !this.isRetryableError(error)) {
          break
        }

        // 等待后重试
        if (mergedOptions.retryDelay) {
          await new Promise(resolve => setTimeout(resolve, mergedOptions.retryDelay))
        }
      }
    }

    throw lastError
  }

  /**
   * 判断错误是否可重试
   */
  private isRetryableError(error: Error): boolean {
    const errorStr = error.message.toLowerCase()

    // 可重试的错误类型
    const retryablePatterns = [
      'network error',
      'timeout',
      'connection refused',
      'service unavailable',
      'rate limit',
      'too many requests'
    ]

    return retryablePatterns.some(pattern => errorStr.includes(pattern))
  }
}

// 创建默认实例
export const defaultResponseHandler = new ResponseHandler({
  showErrorNotification: true,
  autoRetry: true,
  retryCount: 3,
  retryDelay: 1000
})

// 便捷函数
export const handleResponse = <T = any>(response: BaseResponse<T>): Promise<T> => {
  return defaultResponseHandler.handleResponse(response)
}

export const handleError = async (error: ErrorResponse): Promise<void> => {
  await defaultResponseHandler.handleError(error)
}

export const handleWithRetry = async <T = any>(
  requestFn: () => Promise<BaseResponse<T>>,
  options?: Partial<ResponseHandlerOptions>
): Promise<T> => {
  return defaultResponseHandler.handleWithRetry(requestFn, options)
}

// React Hook 集成
export const useResponseHandler = (options: ResponseHandlerOptions = {}) => {
  const handler = new ResponseHandler(options)

  return {
    handleResponse: handler.handleResponse.bind(handler),
    handleError: handler.handleError.bind(handler),
    handleWithRetry: handler.handleWithRetry.bind(handler)
  }
}