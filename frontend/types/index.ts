/**
 * CPG2PVG-AI 前端类型定义
 */

// 基础响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

// 指南相关类型
export interface Guideline {
  id: number;
  title: string;
  description?: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  file_hash: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  processed_content?: string;
  processing_metadata?: Record<string, any>;
  quality_score?: number;
  accuracy_score?: number;
  uploaded_by: string;
  processing_mode: 'slow' | 'fast';
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// 任务相关类型
export interface Task {
  id: string;
  task_id: string;
  task_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  guideline_id: number;
  input_data?: Record<string, any>;
  result_data?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  execution_time?: number;
  total_tokens_used: number;
  total_cost: number;
  quality_score?: number;
  accuracy_score?: number;
  retry_count: number;
  max_retries: number;
  priority: number;
  notify_on_completion: boolean;
  created_at: string;
  updated_at: string;
}

// 任务进度类型
export interface TaskProgress {
  id: number;
  task_id: string;
  step_name: string;
  status: 'running' | 'completed' | 'failed';
  progress_percentage: number;
  message?: string;
  metadata?: Record<string, any>;
  execution_time?: number;
  created_at: string;
  updated_at: string;
}

// 任务进度流更新类型
export interface TaskProgressUpdate {
  task_id: string;
  status: Task['status'];
  progress_percentage: number;
  current_step?: string;
  message?: string;
  recent_updates: TaskProgress[];
  estimated_completion?: string;
}

// 文件上传响应类型
export interface UploadResponse {
  task_id: string;
  status: string;
  message: string;
}

// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  is_premium: boolean;
  api_quota: number;
  api_usage: number;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

// 工作流步骤类型
export interface WorkflowStep {
  name: string;
  display_name: string;
  description: string;
  estimated_time: number; // 分钟
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
}

// Slow工作流步骤
export const SLOW_WORKFLOW_STEPS: WorkflowStep[] = [
  {
    name: 'document_parsing',
    display_name: '文档解析',
    description: '智能解析上传的医学指南文档',
    estimated_time: 2,
    status: 'pending',
    progress: 0,
  },
  {
    name: 'multimodal_processing',
    display_name: '多模态处理',
    description: '处理文本、表格、图表等不同类型内容',
    estimated_time: 3,
    status: 'pending',
    progress: 0,
  },
  {
    name: 'knowledge_graph_enhancement',
    display_name: '知识图谱增强',
    description: '使用医学知识图谱增强语义理解',
    estimated_time: 4,
    status: 'pending',
    progress: 0,
  },
  {
    name: 'agent_processing',
    display_name: '智能体处理',
    description: '多专业智能体协同处理医学内容',
    estimated_time: 8,
    status: 'pending',
    progress: 0,
  },
  {
    name: 'content_generation',
    display_name: '内容生成',
    description: '渐进式生成公众医学指南内容',
    estimated_time: 6,
    status: 'pending',
    progress: 0,
  },
  {
    name: 'quality_control',
    display_name: '质量控制',
    description: '多层质量验证和优化',
    estimated_time: 3,
    status: 'pending',
    progress: 0,
  },
];

// API错误类型
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// 分页类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 查询参数类型
export interface QueryParams {
  page?: number;
  size?: number;
  search?: string;
  sort?: string;
  order?: 'asc' | 'desc';
  status?: string;
  date_from?: string;
  date_to?: string;
}

// 仪表板统计类型
export interface DashboardStats {
  total_guidelines: number;
  processing_guidelines: number;
  completed_guidelines: number;
  failed_guidelines: number;
  total_tasks: number;
  running_tasks: number;
  average_processing_time: number;
  total_cost: number;
  quality_score_avg: number;
}

// 文件类型定义
export interface FileUploadOptions {
  maxSize: number; // bytes
  allowedTypes: string[];
  multiple?: boolean;
}

// 表格列配置类型
export interface TableColumn {
  key: string;
  title: string;
  dataIndex: string;
  width?: number;
  align?: 'left' | 'center' | 'right';
  sorter?: boolean;
  render?: (value: any, record: any) => React.ReactNode;
}