/**
 * API版本控制TypeScript类型定义
 * API Version Control TypeScript Type Definitions
 *
 * 这个文件定义了API版本控制相关的类型，确保前后端一致性
 * This file defines API version control related types for frontend-backend consistency
 */

// ==================== 枚举类型 ====================

export type APIVersion = 'v1' | 'v2' | 'latest' | 'legacy'

export type APIStatus = 'active' | 'deprecated' | 'sunset' | 'beta' | 'alpha'

export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'

export type ResponseFormat = 'json' | 'xml' | 'yaml' | 'csv' | 'html' | 'plain'

// ==================== 接口定义 ====================

export interface APIParameter {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  required?: boolean
  default?: any
  description?: string
  example?: any
  validation?: {
    min?: number
    max?: number
    pattern?: string
    enum?: any[]
  }
}

export interface APIEndpoint {
  path: string
  method: HTTPMethod
  version: APIVersion
  description: string
  parameters?: APIParameter[]
  responses?: Record<string, any>
  deprecated?: boolean
  deprecatedSince?: APIVersion
  sunsetDate?: string
  alternatives?: string[]
  tags?: string[]
  security?: string[]
  rateLimit?: {
    requests: number
    window: number
  }
  cacheTTL?: number
}

export interface APIVersionInfo {
  version: APIVersion
  status: APIStatus
  releaseDate: string
  sunsetDate?: string
  deprecationDate?: string
  description: string
  changelog?: string[]
  breakingChanges?: string[]
  newFeatures?: string[]
  bugFixes?: string[]
  supportedFormats?: ResponseFormat[]
  basePath: string
}

export interface APIConfig {
  defaultVersion: APIVersion
  supportedVersions: APIVersion[]
  versionHeader: string
  formatHeader: string
  versionParam: string
  formatParam: string
  enableVersionNegotiation: boolean
  enableFormatNegotiation: boolean
  strictVersioning: boolean
  deprecatedVersionGracePeriod: number
}

// ==================== 请求和响应类型 ====================

export interface APIRequestOptions {
  version?: APIVersion
  format?: ResponseFormat
  headers?: Record<string, string>
  params?: Record<string, any>
  query?: Record<string, any>
  timeout?: number
  retries?: number
  cache?: boolean
  signal?: AbortSignal
}

export interface APIResponse<T = any> {
  data: T
  status: number
  statusText: string
  headers: Record<string, string>
  config: APIRequestOptions
  request: any
}

export interface APIError extends Error {
  config: APIRequestOptions
  code?: string
  request?: any
  response?: APIResponse
  isAxiosError?: boolean
}

// ==================== 客户端配置类型 ====================

export interface APIClientConfig {
  baseURL: string
  timeout: number
  version: APIVersion
  format: ResponseFormat
  headers: Record<string, string>
  retryConfig: {
    retries: number
    retryDelay: number
    retryCondition?: (error: APIError) => boolean
  }
  cacheConfig: {
    enabled: boolean
    ttl: number
    maxSize: number
  }
  interceptors: {
    request: Array<(config: APIRequestOptions) => APIRequestOptions>
    response: Array<(response: APIResponse) => APIResponse>
    error: Array<(error: APIError) => APIError>
  }
}

export interface APIEndpointDefinition {
  path: string
  method: HTTPMethod
  version: APIVersion
  description: string
  parameters?: APIParameter[]
  requestSchema?: any
  responseSchema?: any
  examples?: {
    request?: any
    response?: any
  }
  tags?: string[]
  deprecated?: boolean
  deprecationMessage?: string
}

// ==================== Hook 和组件类型 ====================

export interface UseAPIOptions<T = any> {
  config?: Partial<APIRequestOptions>
  onSuccess?: (data: T) => void
  onError?: (error: APIError) => void
  onRetry?: (attempt: number, maxRetries: number) => void
  cache?: boolean
  retryCount?: number
  retryDelay?: number
  immediate?: boolean
  refetchOnWindowFocus?: boolean
  refetchOnReconnect?: boolean
  staleTime?: number
  cacheTime?: number
}

export interface UseAPIReturn<T = any> {
  data: T | null
  loading: boolean
  error: APIError | null
  execute: (options?: Partial<APIRequestOptions>) => Promise<T>
  reset: () => void
  refetch: () => Promise<T>
  mutate: (data: T) => Promise<T>
  cancel: () => void
  lastUpdated: number | null
}

export interface UsePaginatedAPIOptions<T = any> extends UseAPIOptions<{
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}>> {
  initialPage?: number
  initialSize?: number
  pageSizeOptions?: number[]
}

export interface UsePaginatedAPIReturn<T = any> extends UseAPIReturn<{
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}> {
  pagination: {
    page: number
    size: number
    total: number
    pages: number
    hasNext: boolean
    hasPrev: boolean
  }
  setPage: (page: number) => void
  setSize: (size: number) => void
  nextPage: () => void
  prevPage: () => void
  goToPage: (page: number) => void
  refresh: () => Promise<void>
}

// ==================== 中间件类型 ====================

export interface APIMiddleware {
  name: string
  priority: number
  execute: (
    context: APIContext,
    next: () => Promise<APIResponse>
  ) => Promise<APIResponse>
}

export interface APIContext {
  request: APIRequestOptions
  response?: APIResponse
  error?: APIError
  metadata: Record<string, any>
}

// ==================== 版本协商类型 ====================

export interface VersionNegotiationResult {
  version: APIVersion
  format: ResponseFormat
  warnings: string[]
  deprecationWarning?: {
    version: APIVersion
    sunsetDate: string
    alternatives: string[]
  }
}

export interface NegotiationOptions {
  preferredVersion?: APIVersion
  preferredFormat?: ResponseFormat
  allowDeprecated?: boolean
  strictVersioning?: boolean
}

// ==================== 缓存类型 ====================

export interface CacheEntry<T = any> {
  key: string
  data: T
  timestamp: number
  ttl: number
  expiresAt: number
  hits: number
  lastAccessed: number
  metadata?: Record<string, any>
}

export interface CacheConfig {
  enabled: boolean
  maxSize: number
  defaultTTL: number
  strategy: 'lru' | 'fifo' | 'lfu'
  compression: boolean
  encryption: boolean
  persistence: boolean
  storageQuota: number
}

// ==================== 速率限制类型 ====================

export interface RateLimitInfo {
  limit: number
  remaining: number
  reset: number
  retryAfter?: number
  scope: string
}

export interface RateLimitConfig {
  enabled: boolean
  strategy: 'fixed' | 'sliding' | 'token_bucket'
  limits: Record<string, {
    requests: number
    window: number
    burst?: number
  }>
  headers: {
    limit: string
    remaining: string
    reset: string
    retryAfter: string
  }
}

// ==================== 监控和分析类型 ====================

export interface APIMetrics {
  requests: {
    total: number
    successful: number
    failed: number
    byStatus: Record<number, number>
    byMethod: Record<HTTPMethod, number>
    byVersion: Record<APIVersion, number>
    byEndpoint: Record<string, number>
  }
  responseTime: {
    average: number
    min: number
    max: number
    p50: number
    p95: number
    p99: number
  }
  errors: {
    total: number
    byType: Record<string, number>
    byCode: Record<string, number>
  }
  cache: {
    hits: number
    misses: number
    hitRate: number
    size: number
  }
}

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: APIVersion
  uptime: number
  checks: Array<{
    name: string
    status: 'pass' | 'fail' | 'warn'
    duration: number
    message?: string
  }>
  metrics?: APIMetrics
}

// ==================== 类型守卫 ====================

export function isAPIVersion(value: string): value is APIVersion {
  return ['v1', 'v2', 'latest', 'legacy'].includes(value)
}

export function isHTTPMethod(value: string): value is HTTPMethod {
  return ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'].includes(value)
}

export function isResponseFormat(value: string): value is ResponseFormat {
  return ['json', 'xml', 'yaml', 'csv', 'html', 'plain'].includes(value)
}

export function isAPIError(error: any): error is APIError {
  return error && error.isAxiosError === true
}

export function isSuccessResponse<T = any>(response: APIResponse<T>): response is APIResponse<T> {
  return response.status >= 200 && response.status < 300
}

export function isErrorResponse(response: APIResponse): response is APIResponse {
  return response.status >= 400
}

// ==================== 工厂函数 ====================

export function createAPIRequestOptions(
  overrides: Partial<APIRequestOptions> = {}
): APIRequestOptions {
  return {
    version: 'v1' as APIVersion,
    format: 'json' as ResponseFormat,
    headers: {},
    params: {},
    query: {},
    timeout: 30000,
    retries: 3,
    cache: true,
    ...overrides
  }
}

export function createAPIEndpoint(
  path: string,
  method: HTTPMethod,
  version: APIVersion,
  description: string,
  overrides: Partial<APIEndpoint> = {}
): APIEndpoint {
  return {
    path,
    method,
    version,
    description,
    parameters: [],
    responses: {},
    tags: [],
    alternatives: [],
    security: [],
    ...overrides
  }
}

export function createAPIError(
  message: string,
  config: APIRequestOptions,
  code?: string,
  response?: APIResponse
): APIError {
  const error = new Error(message) as APIError
  error.config = config
  error.code = code
  error.response = response
  error.isAxiosError = true
  return error
}

// ==================== 默认配置 ====================

export const DEFAULT_API_CONFIG: APIClientConfig = {
  baseURL: '',
  timeout: 30000,
  version: 'v1' as APIVersion,
  format: 'json' as ResponseFormat,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  retryConfig: {
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error) => {
      return !error.response || (error.response.status >= 500 && error.response.status < 600)
    }
  },
  cacheConfig: {
    enabled: true,
    ttl: 300000, // 5分钟
    maxSize: 100,
  },
  interceptors: {
    request: [],
    response: [],
    error: []
  }
}

export const DEFAULT_API_VERSIONS: Record<APIVersion, APIVersionInfo> = {
  v1: {
    version: 'v1',
    status: 'active',
    releaseDate: '2024-01-01T00:00:00Z',
    description: '第一版API，提供核心功能',
    supportedFormats: ['json', 'xml'],
    basePath: '/api/v1'
  },
  v2: {
    version: 'v2',
    status: 'beta',
    releaseDate: '2024-06-01T00:00:00Z',
    description: '第二版API，增强功能和性能',
    supportedFormats: ['json', 'xml', 'yaml'],
    basePath: '/api/v2'
  },
  latest: {
    version: 'latest',
    status: 'active',
    releaseDate: '2024-06-01T00:00:00Z',
    description: '最新稳定版API',
    supportedFormats: ['json'],
    basePath: '/api/latest'
  },
  legacy: {
    version: 'legacy',
    status: 'sunset',
    releaseDate: '2023-01-01T00:00:00Z',
    deprecationDate: '2024-01-01T00:00:00Z',
    sunsetDate: '2024-12-31T23:59:59Z',
    description: '旧版API，即将停止支持',
    supportedFormats: ['json'],
    basePath: '/api/legacy'
  }
}

export const CONTENT_TYPE_MAPPING: Record<ResponseFormat, string> = {
  json: 'application/json',
  xml: 'application/xml',
  yaml: 'application/x-yaml',
  csv: 'text/csv',
  html: 'text/html',
  plain: 'text/plain'
}