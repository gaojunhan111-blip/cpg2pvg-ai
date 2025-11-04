/**
 * 核心类型定义
 * Core Type Definitions
 */

// ==================== 导入共享响应类型 ====================
export type {
  ResponseStatus,
  ErrorCode,
  BaseResponse,
  SuccessResponse,
  ErrorResponse,
  ValidationErrorResponse,
  PaginatedResponse,
  TaskResponse,
  FileUploadResponse,
  AuthResponse,
  GuidelineListResponse,
  UserInfo,
  TaskInfo,
  FileInfo,
  GuidelineInfo,
  ErrorInfo,
  PaginationInfo,
  isSuccessResponse,
  isErrorResponse,
  getErrorMessage,
  getErrorDetails,
  getStatusCode,
  isPaginatedResponse,
  isTaskResponse,
  isFileUploadResponse,
  isValidationErrorResponse
} from '../../../shared/constants/response-types'

// ==================== 通用类型 ====================

// 保留向后兼容的分页参数
export interface PaginationParams {
  page?: number
  pageSize?: number
  total?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// ==================== 用户相关类型 ====================

export type UserRole = 'admin' | 'doctor' | 'professional' | 'user'
export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended'

export interface User {
  id: string
  username: string
  email: string
  name?: string
  role: UserRole
  status: UserStatus
  createdAt: string
  lastLoginAt?: string
  isActive: boolean
  avatar?: string
  organization?: string
  department?: string
  apiQuota: number
  apiUsage: number
  storageQuota: number
  storageUsed: number
  settings?: UserSettings
}

export interface UserSettings {
  language: 'zh' | 'en'
  theme: 'light' | 'dark' | 'auto'
  notifications: boolean
  emailNotifications: boolean
  defaultProcessingMode: 'slow' | 'fast'
  autoSave: boolean
}

export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
  name?: string
  role?: UserRole
  organization?: string
  department?: string
}

export interface AuthResponse {
  accessToken: string
  refreshToken: string
  expiresIn: number
  tokenType: string
  userInfo: User
}

// ==================== 文件相关类型 ====================
// 导入共享常量
export {
  FILE_TYPES,
  FILE_EXTENSIONS,
  ALLOWED_FILE_EXTENSIONS,
  ALLOWED_MIME_TYPES,
  MIME_TO_FILE_TYPE,
  FILE_TYPE_NAMES,
  FILE_TYPE_ICONS,
  FILE_VALIDATION,
  validateFileType,
  validateFileSize,
  formatFileSize,
  isImageFile,
  getFileInfo
} from '../../../shared/constants/file-types'

// 从共享常量导出FileType类型
export type FileType = typeof FILE_TYPES[keyof typeof FILE_TYPES]

// ==================== 指南相关类型 ====================
export type GuidelineStatus = 'uploaded' | 'parsing' | 'processing' | 'completed' | 'failed' | 'archived'
export type ProcessingMode = 'slow' | 'fast' | 'custom'
export type Priority = 'low' | 'normal' | 'high' | 'urgent'

export interface Guideline {
  id: string
  title: string
  description?: string
  author?: string
  publisher?: string
  publicationYear?: number
  isbn?: string
  doi?: string
  originalFilename: string
  filePath: string
  fileSize: number
  fileType: FileType
  fileHash: string
  mimeType?: string
  status: GuidelineStatus
  processingMode: ProcessingMode
  priority: Priority
  processingProgress: number
  currentStep?: string
  errorMessage?: string
  processedContent?: string
  pvgSummary?: string
  processingMetadata?: Record<string, unknown>
  createdAt: string
  updatedAt: string
  userId?: string
  isPublic: boolean
  tags: string[]
  version: string
  parentGuidelineId?: string
  viewCount: number
  downloadCount: number
  shareCount: number
  rating?: number
  reviewCount: number
  lastAccessedAt?: string
  estimatedReadTime?: number // 分钟
  difficultyLevel?: 'basic' | 'intermediate' | 'advanced'
  targetAudience?: string[]
  medicalSpecialties?: string[]
  collaborators?: string[] // 协作者用户ID列表
}

export interface GuidelineCreateRequest {
  title: string
  description?: string
  author?: string
  publisher?: string
  publicationYear?: number
  isbn?: string
  doi?: string
  processingMode: ProcessingMode
  priority: Priority
  isPublic: boolean
  tags: string[]
  targetAudience?: string[]
  medicalSpecialties?: string[]
}

export interface GuidelineUpdateRequest extends Partial<GuidelineCreateRequest> {
  version?: string
  status?: GuidelineStatus
}

export type ContentFormat = 'html' | 'markdown' | 'plain_text' | 'json' | 'pdf'
export type ValidationStatus = 'generated' | 'validated' | 'approved' | 'rejected' | 'pending_review'
export type QualityIssueType = 'content' | 'style' | 'accuracy' | 'safety' | 'clarity' | 'completeness'
export type Severity = 'low' | 'medium' | 'high' | 'critical'

export interface ProcessingResult {
  id: string
  guidelineId: string
  pvgContent: string
  pvgSummary?: string
  pvgTitle?: string
  contentFormat: ContentFormat
  contentLength: number
  wordCount: number
  estimatedReadTime: number // 分钟
  // 质量评分 (0-100)
  qualityScores: {
    overall?: number
    accuracy?: number
    readability?: number
    completeness?: number
    medicalSafety?: number
    patientFriendly?: number
  }
  processingMetrics: {
    processingTime?: number // 秒
    tokenUsage: number
    cost: number // USD
    efficiency?: number
  }
  contentMetadata: {
    sourceLanguage: string
    targetLanguage: string
    targetAudience?: string[]
    sectionsCount?: number
    hasImages: boolean
    hasTables: boolean
    hasReferences: boolean
    hasDisclaimer: boolean
    hasGlossary: boolean
  }
  medicalMetadata: {
    medicalSpecialties?: string[]
    complexityLevel?: 'basic' | 'intermediate' | 'advanced'
    evidenceLevel?: string
    riskLevel?: string
    targetConditions?: string[]
    ageGroups?: string[]
  }
  processingInfo: {
    processingSteps?: ProcessingStep[]
    stepDurations?: Record<string, number>
    stepQualityScores?: Record<string, number>
    llmModelsUsed?: string[]
    processingParameters?: Record<string, unknown>
    modelConfigs?: Record<string, unknown>
  }
  validation: {
    status: ValidationStatus
    validationDetails?: Record<string, unknown>
    qualityIssues?: QualityIssue[]
    improvementSuggestions?: string[]
    reviewedBy?: string
    reviewNotes?: string
  }
  versioning: {
    version: string
    iterationCount: number
    previousResultId?: string
  }
  publishing: {
    isPublished: boolean
    publishedAt?: string
  }
  analytics: {
    viewCount: number
    downloadCount: number
    shareCount: number
    userRating?: number
    userFeedback?: string
    averageReadTime?: number
    bounceRate?: number
  }
  categorization: {
    tags?: string[]
    keywords?: string[]
  }
  timestamps: {
    createdAt: string
    updatedAt: string
    lastAccessedAt?: string
  }
}

export interface QualityIssue {
  id: string
  type: QualityIssueType
  severity: Severity
  message: string
  suggestion?: string
  location?: {
    line?: number
    section?: string
    paragraph?: number
    character?: number
  }
  autoFixable: boolean
  confidence: number // 0-1
  category?: string
  ruleId?: string
  createdAt: string
}

// ==================== 任务相关类型 ====================

export type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying' | 'paused'
export type TaskType =
  | 'document_parsing'
  | 'multimodal_processing'
  | 'knowledge_graph'
  | 'agent_processing'
  | 'content_generation'
  | 'quality_control'
  | 'full_processing'
  | 'fast_processing'
  | 'validation'
  | 'publishing'

export interface Task {
  id: string
  taskId: string
  taskType: TaskType
  name: string
  description?: string
  status: TaskStatus
  priority: Priority
  progress: number
  currentStep?: string
  totalSteps: number
  completedSteps: number
  guidelineId: string
  userId?: string
  inputData?: Record<string, unknown>
  resultData?: Record<string, unknown>
  outputData?: Record<string, unknown>
  errorMessage?: string
  errorDetails?: Record<string, unknown>
  timings: {
    startTime?: string
    endTime?: string
    duration?: number
    estimatedDuration?: number
    pausedDuration?: number
  }
  retry: {
    count: number
    maxRetries: number
    lastRetryAt?: string
  }
  resource: {
    cpuUsage?: number
    memoryUsage?: number
    diskUsage?: number
  }
  metadata?: {
    tags?: string[]
    category?: string
    source?: string
    [key: string]: unknown
  }
  createdAt: string
  updatedAt: string
  startedAt?: string
  completedAt?: string
}

export interface TaskProgress {
  id: string
  taskId: string
  stepName: string
  stepNumber: number
  status: TaskStatus
  progress: number
  message?: string
  data?: Record<string, unknown>
  timings: {
    startTime?: string
    endTime?: string
    duration?: number
    estimatedTimeRemaining?: number
  }
  output?: Record<string, unknown>
  error?: string
  metadata?: Record<string, unknown>
  createdAt: string
  updatedAt: string
  subSteps?: {
    name: string
    progress: number
    status: TaskStatus
    message?: string
  }[]
}

export interface ProcessingStep {
  id: string
  name: string
  type: TaskType
  description: string
  status: TaskStatus
  progress: number
  startTime?: string
  endTime?: string
  duration?: number
  input?: Record<string, unknown>
  output?: Record<string, unknown>
  error?: string
  metadata?: Record<string, unknown>
  dependencies?: string[] // 依赖的其他步骤
  parallel?: boolean // 是否可并行执行
  retryable?: boolean // 是否可重试
  maxRetries?: number
}

// 任务创建和更新请求
export interface TaskCreateRequest {
  taskType: TaskType
  name: string
  description?: string
  priority: Priority
  guidelineId: string
  inputData?: Record<string, unknown>
  tags?: string[]
  scheduledAt?: string // 定时执行
}

export interface TaskUpdateRequest extends Partial<TaskCreateRequest> {
  status?: TaskStatus
  progress?: number
  errorMessage?: string
  outputData?: Record<string, unknown>
}

// ==================== 工作流相关类型 ====================

export interface WorkflowExecution {
  id: string
  name: string
  description?: string
  workflowType: 'slow' | 'fast' | 'custom'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  currentStep?: string
  totalSteps: number
  completedSteps: number
  guidelineId?: number
  userId?: string
  inputConfig: Record<string, any>
  outputConfig?: Record<string, any>
  steps: WorkflowStep[]
  startTime?: string
  endTime?: string
  duration?: number
  errorMessage?: string
  metadata?: Record<string, any>
  createdAt: string
  updatedAt: string
}

export interface WorkflowStep {
  id: string
  name: string
  type: string
  status: TaskStatus
  progress: number
  startTime?: string
  endTime?: string
  duration?: number
  input?: Record<string, any>
  output?: Record<string, any>
  error?: string
  metadata?: Record<string, any>
}

// ==================== 文件相关类型 ====================

export interface FileInfo {
  id: string
  originalFilename: string
  filename: string // 存储的文件名
  filePath: string
  fileSize: number
  fileType: FileType
  fileHash: string
  mimeType: string
  checksum?: string // 校验和
  userId?: string
  metadata?: {
    width?: number // 图片宽度
    height?: number // 图片高度
    pages?: number // 文档页数
    encoding?: string // 文件编码
    compression?: string // 压缩格式
    [key: string]: unknown
  }
  security: {
    virusScanned: boolean
    virusScanResult?: string
    quarantine: boolean
  }
  timestamps: {
    uploadTime: string
    lastAccessTime?: string
    expirationTime?: string
  }
  access: {
    isPublic: boolean
    downloadCount: number
    shareToken?: string
    shareExpiresAt?: string
  }
}

export interface FileUploadRequest {
  file: File
  filename?: string
  isPublic?: boolean
  tags?: string[]
  category?: string
  metadata?: Record<string, unknown>
  generateThumbnail?: boolean
  extractText?: boolean
  virusScan?: boolean
}

export interface FileUploadResponse {
  fileInfo: FileInfo
  uploadUrl?: string // 预签名上传URL
  thumbnailUrl?: string // 缩略图URL
  extractedText?: string // 提取的文本
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
}

export interface FileListResponse {
  files: FileInfo[]
  totalCount: number
  totalSize: number
  pagination: {
    current: number
    pageSize: number
    totalPages: number
  }
}

export interface StorageStats {
  usage: {
    totalFiles: number
    totalSize: number
    usedQuota: number
    quotaPercentage: number
  }
  breakdown: {
    fileTypes: Record<string, { count: number; size: number }>
    categories: Record<string, { count: number; size: number }>
    timeDistribution: Record<string, number> // 按时间分布
  }
  quota: {
    quotaTotal: number
    quotaUsed: number
    quotaRemaining: number
    renewalDate?: string
  }
}

export interface FileSearchFilters {
  search?: string
  fileType?: FileType[]
  tags?: string[]
  category?: string
  userId?: string
  dateRange?: [string, string]
  sizeRange?: [number, number]
  isPublic?: boolean
  hasThumbnail?: boolean
}

// ==================== 可视化相关类型 ====================

export interface VisualizationConfig {
  chartType: 'bar' | 'line' | 'pie' | 'scatter' | 'network' | 'tree' | 'sankey'
  title: string
  width: number
  height: number
  showLegend?: boolean
  showGrid?: boolean
  colors?: string[]
  [key: string]: any
}

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    borderWidth?: number
  }[]
}

// ==================== API请求类型 ====================

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
  requestId?: string
  path?: string
  method?: string
  statusCode?: number
}

export interface UploadOptions {
  chunkSize?: number
  maxRetries?: number
  timeout?: number
  concurrent?: number
  onProgress?: (progress: number, loaded: number, total: number) => void
  onError?: (error: Error, attempt: number) => void
  onSuccess?: (response: FileUploadResponse) => void
  onChunkComplete?: (chunkIndex: number, totalChunks: number) => void
  validateChecksum?: boolean
  compress?: boolean
}

// ==================== UI状态类型 ====================

export type LoadingState = {
  loading: boolean
  error?: string | null
  loadingText?: string
}

export interface AsyncState<T = any> extends LoadingState {
  data?: T
  lastUpdated?: string
}

export interface PaginationState {
  current: number
  pageSize: number
  total: number
  hasNext: boolean
  hasPrev: boolean
}

export interface SortState {
  field?: string
  order?: 'asc' | 'desc'
}

export interface FilterState {
  search?: string
  status?: string[]
  dateRange?: [string, string]
  tags?: string[]
  [key: string]: unknown
}

export interface TableColumn<T = any> {
  key: string
  title: string
  dataIndex?: string
  width?: number | string
  minWidth?: number
  maxWidth?: number
  fixed?: 'left' | 'right'
  sorter?: boolean | ((a: T, b: T) => number)
  filterable?: boolean
  resizable?: boolean
  ellipsis?: boolean
  align?: 'left' | 'center' | 'right'
  render?: (value: any, record: T, index: number) => React.ReactNode
  filterDropdown?: React.ReactNode
  filterIcon?: React.ReactNode
  onFilter?: (value: any, record: T) => boolean
  onHeaderCell?: (column: any) => any
}

// ==================== 主题相关类型 ====================

export interface ThemeConfig {
  primaryColor: string
  borderRadius: number
  colorBgBase: string
  colorTextBase: string
  fontSize: number
  fontFamily: string
}

export interface ThemeState {
  mode: 'light' | 'dark' | 'auto'
  config: ThemeConfig
  customCSS?: string
}

// ==================== 通知类型 ====================

export type NotificationType = 'success' | 'info' | 'warning' | 'error'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string
  duration?: number
  timestamp: string
  read: boolean
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  actions?: Array<{
    label: string
    action: () => void
    type?: 'primary' | 'default' | 'danger'
  }>
  metadata?: Record<string, unknown>
}

export interface NotificationState {
  notifications: NotificationItem[]
  unreadCount: number
  settings: {
    enabled: boolean
    desktop: boolean
    sound: boolean
    position: 'topRight' | 'topLeft' | 'bottomRight' | 'bottomLeft'
  }
}

// ==================== Hook 相关类型 ====================

export interface HookOptions<T = any> {
  onSuccess?: (data: T) => void
  onError?: (error: Error | string) => void
  onSettled?: () => void
  retry?: number
  retryDelay?: number
  refetchOnWindowFocus?: boolean
  refetchOnReconnect?: boolean
  staleTime?: number
  cacheTime?: number
}

// ==================== 实用类型 ====================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type ID = string | number
export type Timestamp = string | number | Date

export interface SelectOption<T = any> {
  label: string
  value: T
  disabled?: boolean
  description?: string
  icon?: React.ReactNode
}

export interface TreeNode<T = any> {
  key: string
  title: string
  data: T
  children?: TreeNode<T>[]
  expanded?: boolean
  selected?: boolean
  disabled?: boolean
  loading?: boolean
}

// ==================== 事件类型 ====================

export interface AppEvent {
  type: string
  payload?: any
  timestamp: number
  source?: string
}

export interface EventHandler<T = any> {
  (event: AppEvent & { payload: T }): void
  once?: boolean
}

// ==================== 性能监控类型 ====================

export interface PerformanceMetric {
  name: string
  value: number
  unit: string
  timestamp: number
  tags?: Record<string, string>
}

export interface PagePerformance {
  loadTime: number
  domContentLoaded: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  cumulativeLayoutShift: number
  firstInputDelay: number
}

// ==================== 缓存类型 ====================

export interface CacheEntry<T = any> {
  data: T
  timestamp: number
  expiresAt?: number
  ttl?: number
  hits: number
  lastAccessed: number
}

export interface CacheConfig {
  maxSize?: number
  defaultTtl?: number
  strategy?: 'lru' | 'fifo' | 'lfu'
  compression?: boolean
  encryption?: boolean
}