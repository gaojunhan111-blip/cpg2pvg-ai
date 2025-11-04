/**
 * 文件类型常量定义
 * File Type Constants Definition
 *
 * 这个文件定义了前后端共享的文件类型常量，确保一致性
 */

// 文件类型枚举
export const FILE_TYPES = {
  PDF: 'pdf',
  DOCX: 'docx',
  DOC: 'doc',
  TXT: 'txt',
  HTML: 'html',
  MARKDOWN: 'md'
} as const

// 文件扩展名映射
export const FILE_EXTENSIONS = {
  [FILE_TYPES.PDF]: ['.pdf'],
  [FILE_TYPES.DOCX]: ['.docx'],
  [FILE_TYPES.DOC]: ['.doc'],
  [FILE_TYPES.TXT]: ['.txt'],
  [FILE_TYPES.HTML]: ['.html', '.htm'],
  [FILE_TYPES.MARKDOWN]: ['.md', '.markdown']
} as const

// 允许的文件扩展名（后端和前端统一使用）
export const ALLOWED_FILE_EXTENSIONS = [
  ...FILE_EXTENSIONS[FILE_TYPES.PDF],
  ...FILE_EXTENSIONS[FILE_TYPES.DOCX],
  ...FILE_EXTENSIONS[FILE_TYPES.DOC],
  ...FILE_EXTENSIONS[FILE_TYPES.TXT],
  ...FILE_EXTENSIONS[FILE_TYPES.HTML],
  ...FILE_EXTENSIONS[FILE_TYPES.MARKDOWN]
] as const

// 允许的MIME类型
export const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/plain',
  'text/html',
  'text/markdown'
] as const

// MIME类型到文件类型的映射
export const MIME_TO_FILE_TYPE = {
  'application/pdf': FILE_TYPES.PDF,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FILE_TYPES.DOCX,
  'application/msword': FILE_TYPES.DOC,
  'text/plain': FILE_TYPES.TXT,
  'text/html': FILE_TYPES.HTML,
  'text/markdown': FILE_TYPES.MARKDOWN
} as const

// 文件类型显示名称
export const FILE_TYPE_NAMES = {
  [FILE_TYPES.PDF]: 'PDF文档',
  [FILE_TYPES.DOCX]: 'Word文档 (DOCX)',
  [FILE_TYPES.DOC]: 'Word文档 (DOC)',
  [FILE_TYPES.TXT]: '纯文本',
  [FILE_TYPES.HTML]: 'HTML网页',
  [FILE_TYPES.MARKDOWN]: 'Markdown文档'
} as const

// 文件类型图标映射
export const FILE_TYPE_ICONS = {
  [FILE_TYPES.PDF]: 'FilePdfOutlined',
  [FILE_TYPES.DOCX]: 'FileWordOutlined',
  [FILE_TYPES.DOC]: 'FileWordOutlined',
  [FILE_TYPES.TXT]: 'FileTextOutlined',
  [FILE_TYPES.HTML]: 'FileMarkdownOutlined',
  [FILE_TYPES.MARKDOWN]: 'FileMarkdownOutlined'
} as const

// 文件验证配置
export const FILE_VALIDATION = {
  MAX_SIZE: 50 * 1024 * 1024, // 50MB
  MAX_SIZE_MB: 50,
  MIN_SIZE: 1, // 1字节
  MAX_FILES: 10, // 单次上传最大文件数
  CHUNK_SIZE: 1024 * 1024, // 1MB
  MAX_CONCURRENT_UPLOADS: 3
  UPLOAD_TIMEOUT: 5 * 60 * 1000 // 5分钟
} as const

// 文件类型验证函数
export function validateFileType(filename: string, mimeType?: string): {
  valid: boolean
  fileType?: string
  error?: string
} {
  const fileExtension = filename.split('.').pop()?.toLowerCase()

  if (!fileExtension) {
    return { valid: false, error: '文件缺少扩展名' }
  }

  // 检查扩展名是否允许
  if (!ALLOWED_FILE_EXTENSIONS.includes(`.${fileExtension}`)) {
    return {
      valid: false,
      error: `不支持的文件类型，允许的类型: ${Array.from(new Set(ALLOWED_FILE_EXTENSIONS)).join(', ')}`
    }
  }

  // 如果有MIME类型，也要验证
  if (mimeType && !ALLOWED_MIME_TYPES.includes(mimeType)) {
    return {
      valid: false,
      error: `不支持的文件类型 (MIME: ${mimeType})`
    }
  }

  // 获取文件类型
  let fileType: string
  for (const [type, extensions] of Object.entries(FILE_EXTENSIONS)) {
    if (extensions.includes(`.${fileExtension}`)) {
      fileType = type
      break
    }
  }

  return { valid: true, fileType }
}

// 文件大小验证函数
export function validateFileSize(fileSize: number): {
  valid: boolean
  error?: string
} {
  if (fileSize < FILE_VALIDATION.MIN_SIZE) {
    return { valid: false, error: '文件大小不能为0' }
  }

  if (fileSize > FILE_VALIDATION.MAX_SIZE) {
    return {
      valid: false,
      error: `文件大小超过限制，最大 ${FILE_VALIDATION.MAX_SIZE_MB}MB`
    }
  }

  return { valid: true }
}

// 格式化文件大小显示
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 检查文件是否为图片类型（用于预览）
export function isImageFile(filename: string, mimeType?: string): boolean {
  const imageTypes = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
  const imageMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']

  const fileExtension = filename.split('.').pop()?.toLowerCase()

  return imageTypes.includes(`.${fileExtension}`) ||
         (mimeType && imageMimeTypes.includes(mimeType))
}

// 获取文件类型的显示信息
export function getFileInfo(filename: string, mimeType?: string) {
  const { valid, fileType, error } = validateFileType(filename, mimeType)

  if (!valid) {
    return { error, valid: false }
  }

  const fileSize = 0 // 这里应该传入实际文件大小
  const { valid: sizeValid } = validateFileSize(fileSize)

  return {
    valid: valid && sizeValid,
    fileType: fileType!,
    fileName: filename,
    displayName: FILE_TYPE_NAMES[fileType!],
    icon: FILE_TYPE_ICONS[fileType!],
    extensions: FILE_EXTENSIONS[fileType!],
    mimeTypes: Array.from(
      new Set(
        Object.entries(MIME_TO_FILE_TYPE)
          .filter(([_, type]) => type === fileType)
          .map(([mime]) => mime)
      )
    )
  }
}

// 导出类型定义
export type FileType = typeof FILE_TYPES[keyof typeof FILE_TYPES]
export type FileExtension = typeof ALLOWED_FILE_EXTENSIONS[number]