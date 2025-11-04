/**
 * 文件上传Hook (优化版本)
 * File Upload Hook (Optimized Version)
 */

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { message } from 'antd'
import { FileUploadResponse, UploadOptions, HookOptions, ALLOWED_MIME_TYPES, ALLOWED_FILE_EXTENSIONS, validateFileType } from '@/types'

interface UploadProgress {
  loaded: number
  total: number
  percentage: number
  speed: number
  timeRemaining: number
  chunkIndex?: number
  totalChunks?: number
  pausedTime?: number
}

interface UploadChunkInfo {
  index: number
  start: number
  end: number
  size: number
  status: 'pending' | 'uploading' | 'completed' | 'failed'
  retryCount: number
  uploadedAt?: number
  checksum?: string
}

interface UploadResumeInfo {
  uploadId: string
  fileName: string
  fileSize: number
  fileType: string
  totalChunks: number
  completedChunks: number[]
  chunkSize: number
  createdAt: number
}

interface UseFileUploadOptions extends HookOptions {
  onProgress?: (progress: UploadProgress) => void
  onSuccess?: (response: FileUploadResponse) => void
  onError?: (error: Error) => void
  onUploadStart?: (fileName: string, fileSize: number) => void
  onUploadEnd?: (fileName: string, response: FileUploadResponse) => void
  onChunkComplete?: (chunkIndex: number, totalChunks: number) => void
  onQueueUpdate?: (queue: UploadQueueItem[]) => void
  chunkSize?: number
  maxRetries?: number
  timeout?: number
  maxConcurrentChunks?: number
  enableResume?: boolean
  enableChecksum?: boolean
  enableCompression?: boolean
  retryDelay?: number
  queueLimit?: number
}

interface UploadQueueItem {
  id: string
  file: File
  status: 'queued' | 'uploading' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress: UploadProgress
  error?: string
  uploadId?: string
  startTime?: number
  endTime?: number
  chunks?: UploadChunkInfo[]
  resumeInfo?: UploadResumeInfo
}

interface UseFileUploadReturn {
  upload: (file: File, options?: UploadOptions) => Promise<FileUploadResponse>
  uploadFiles: (files: File[], options?: UploadOptions) => Promise<FileUploadResponse[]>
  uploading: boolean
  progress: UploadProgress | null
  error: string | null
  queue: UploadQueueItem[]
  pause: (uploadId?: string) => void
  resume: (uploadId?: string) => void
  cancel: (uploadId?: string) => void
  retry: (uploadId?: string) => void
  reset: () => void
  clearQueue: () => void
  getStats: () => UploadStats
}

interface UploadStats {
  totalUploads: number
  completedUploads: number
  failedUploads: number
  totalSize: number
  uploadedSize: number
  averageSpeed: number
  totalDuration: number
}

const DEFAULT_CHUNK_SIZE = 1024 * 1024 // 1MB
const MAX_RETRIES = 3
const TIMEOUT = 30000 // 30 seconds
const MAX_CONCURRENT_CHUNKS = 3
const QUEUE_LIMIT = 10

export const useFileUpload = (options: UseFileUploadOptions = {}): UseFileUploadReturn => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<UploadProgress | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [queue, setQueue] = useState<UploadQueueItem[]>([])

  const abortControllerRef = useRef<AbortController | null>(null)
  const progressRef = useRef<number>(0)
  const speedRef = useRef<number[]>([])
  const uploadStatsRef = useRef<UploadStats>({
    totalUploads: 0,
    completedUploads: 0,
    failedUploads: 0,
    totalSize: 0,
    uploadedSize: 0,
    averageSpeed: 0,
    totalDuration: 0
  })

  const {
    onProgress,
    onSuccess,
    onError,
    onUploadStart,
    onUploadEnd,
    onChunkComplete,
    onQueueUpdate,
    chunkSize = DEFAULT_CHUNK_SIZE,
    maxRetries = MAX_RETRIES,
    timeout = TIMEOUT,
    maxConcurrentChunks = MAX_CONCURRENT_CHUNKS,
    enableResume = true,
    enableChecksum = false,
    enableCompression = false,
    retryDelay = 1000,
    queueLimit = QUEUE_LIMIT
  } = options

  // 从localStorage恢复上传队列
  useEffect(() => {
    if (enableResume) {
      try {
        const savedQueue = localStorage.getItem('uploadQueue')
        if (savedQueue) {
          const parsedQueue: UploadQueueItem[] = JSON.parse(savedQueue)
          setQueue(parsedQueue.filter(item => item.status === 'paused' || item.status === 'failed'))
        }
      } catch (error) {
        console.warn('Failed to restore upload queue:', error)
      }
    }
  }, [enableResume])

  // 保存上传队列到localStorage
  const saveQueueToStorage = useCallback((queueItems: UploadQueueItem[]) => {
    if (enableResume) {
      try {
        const activeQueue = queueItems.filter(item =>
          item.status === 'paused' || item.status === 'failed' || item.status === 'queued'
        )
        localStorage.setItem('uploadQueue', JSON.stringify(activeQueue))
      } catch (error) {
        console.warn('Failed to save upload queue:', error)
      }
    }
  }, [enableResume])

  // 生成文件校验和
  const generateChecksum = useCallback(async (file: File): Promise<string> => {
    if (!enableChecksum) return ''

    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const buffer = e.target?.result as ArrayBuffer
        const hashBuffer = crypto.subtle.digest('SHA-256', buffer)
        hashBuffer.then((hashArray) => {
          const hashString = Array.from(new Uint8Array(hashArray))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('')
          resolve(hashString)
        })
      }
      reader.readAsArrayBuffer(file)
    })
  }, [enableChecksum])

  const calculateProgress = useCallback((
    loaded: number,
    total: number,
    chunkIndex?: number,
    totalChunks?: number,
    pausedTime?: number
  ): UploadProgress => {
    const percentage = total > 0 ? Math.round((loaded / total) * 100) : 0
    const currentTime = Date.now()

    // 计算上传速度 (bytes/second) - 使用滑动窗口
    const speedDataPoint = { loaded, time: currentTime }
    speedRef.current.push(speedDataPoint)

    // 只保留最近10个数据点用于平滑速度计算
    if (speedRef.current.length > 10) {
      speedRef.current.shift()
    }

    let speed = 0
    if (speedRef.current.length >= 2) {
      const recent = speedRef.current[speedRef.current.length - 1]
      const previous = speedRef.current[0]
      const timeDiff = (recent.time - previous.time) / 1000 // seconds
      if (timeDiff > 0) {
        const loadedDiff = recent.loaded - previous.loaded
        speed = loadedDiff / timeDiff
      }
    }

    // 计算剩余时间
    let timeRemaining = 0
    if (speed > 0) {
      const remainingBytes = Math.max(0, total - loaded)
      timeRemaining = remainingBytes / speed
    }

    return {
      loaded,
      total,
      percentage,
      speed: Math.round(speed),
      timeRemaining: Math.round(timeRemaining),
      chunkIndex,
      totalChunks,
      pausedTime
    }
  }, [])

  const uploadChunk = useCallback(async (
    chunk: Blob,
    chunkIndex: number,
    totalChunks: number,
    fileName: string,
    fileSize: number,
    uploadId: string,
    retryCount = 0
  ): Promise<void> => {
    const formData = new FormData()
    formData.append('chunk', chunk)
    formData.append('chunkIndex', chunkIndex.toString())
    formData.append('totalChunks', totalChunks.toString())
    formData.append('fileName', fileName)
    formData.append('fileSize', fileSize.toString())
    formData.append('uploadId', uploadId)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/files/upload-chunk`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: formData,
        signal: abortControllerRef.current?.signal,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      if (!result.success) {
        throw new Error(result.message || 'Upload failed')
      }

      return result.data

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Upload cancelled')
      }

      if (retryCount < maxRetries) {
        console.warn(`Chunk ${chunkIndex} upload failed, retrying... (${retryCount + 1}/${maxRetries})`)
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount))) // Exponential backoff
        return uploadChunk(chunk, chunkIndex, totalChunks, fileName, fileSize, uploadId, retryCount + 1)
      }

      throw error
    }
  }, [maxRetries])

  const uploadFileInChunks = useCallback(async (
    file: File,
    uploadId: string
  ): Promise<FileUploadResponse> => {
    const fileSize = file.size
    const fileName = file.name
    const totalChunks = Math.ceil(fileSize / chunkSize)

    onUploadStart?.(fileName)
    setUploading(true)
    setError(null)
    progressRef.current = 0
    speedRef.current = []

    try {
      // 初始化上传
      const initResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/files/upload-init`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileName,
          fileSize,
          fileType: file.type,
          totalChunks,
          uploadId
        }),
        signal: abortControllerRef.current?.signal,
      })

      if (!initResponse.ok) {
        throw new Error(`Failed to initialize upload: ${initResponse.statusText}`)
      }

      const initResult = await initResponse.json()
      if (!initResult.success) {
        throw new Error(initResult.message || 'Failed to initialize upload')
      }

      // 分块上传
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error('Upload cancelled')
        }

        const start = chunkIndex * chunkSize
        const end = Math.min(start + chunkSize, fileSize)
        const chunk = file.slice(start, end)

        await uploadChunk(chunk, chunkIndex, totalChunks, fileName, fileSize, uploadId)

        // 更新进度
        progressRef.current = (chunkIndex + 1) * chunkSize
        const uploadProgress = calculateProgress(progressRef.current, fileSize)
        setProgress(uploadProgress)
        onProgress?.(uploadProgress)
      }

      // 完成上传
      const completeResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/files/upload-complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileName,
          fileSize,
          uploadId
        }),
        signal: abortControllerRef.current?.signal,
      })

      if (!completeResponse.ok) {
        throw new Error(`Failed to complete upload: ${completeResponse.statusText}`)
      }

      const completeResult = await completeResponse.json()
      if (!completeResult.success) {
        throw new Error(completeResult.message || 'Failed to complete upload')
      }

      onUploadEnd?.(fileName)
      return completeResult.data

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed')
      onError?.(error instanceof Error ? error : new Error('Upload failed'))
      throw error
    } finally {
      setUploading(false)
    }
  }, [chunkSize, uploadChunk, calculateProgress, onProgress, onUploadStart, onUploadEnd, onError])

  const uploadSimple = useCallback(async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    onUploadStart?.(file.name)
    setUploading(true)
    setError(null)

    try {
      const xhr = new XMLHttpRequest()

      // 进度监听
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const uploadProgress = calculateProgress(event.loaded, event.total)
          setProgress(uploadProgress)
          onProgress?.(uploadProgress)
        }
      })

      // 创建Promise来包装XMLHttpRequest
      return new Promise<FileUploadResponse>((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status === 200) {
            try {
              const result = JSON.parse(xhr.responseText)
              if (result.success) {
                onUploadEnd?.(file.name)
                onSuccess?.(result.data)
                resolve(result.data)
              } else {
                throw new Error(result.message || 'Upload failed')
              }
            } catch (error) {
              reject(new Error('Invalid response format'))
            }
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`))
          }
        }

        xhr.onerror = () => {
          reject(new Error('Network error'))
        }

        xhr.ontimeout = () => {
          reject(new Error('Upload timeout'))
        }

        xhr.timeout = timeout

        xhr.open('POST', `${process.env.NEXT_PUBLIC_API_URL}/api/v1/files/upload`)
        xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('accessToken')}`)
        xhr.send(formData)

        // 设置取消处理
        if (abortControllerRef.current) {
          abortControllerRef.current.signal.addEventListener('abort', () => {
            xhr.abort()
            reject(new Error('Upload cancelled'))
          })
        }
      })

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed')
      onError?.(error instanceof Error ? error : new Error('Upload failed'))
      setUploading(false)
      throw error
    }
  }, [calculateProgress, timeout, onProgress, onUploadStart, onUploadEnd, onSuccess, onError])

  const upload = useCallback(async (file: File, options: UploadOptions = {}): Promise<FileUploadResponse> => {
    // 重置状态
    setError(null)
    setProgress(null)
    abortControllerRef.current = new AbortController()

    try {
      // 验证文件
      if (!file) {
        throw new Error('No file provided')
      }

      const maxSize = options.maxSize || 100 * 1024 * 1024 // 100MB
      if (file.size > maxSize) {
        throw new Error(`File size exceeds limit: ${maxSize / 1024 / 1024}MB`)
      }

      // 使用共享常量验证文件类型
      const validation = validateFileType(file.name, file.type)
      if (!validation.valid) {
        throw new Error(validation.error || 'Unsupported file type')
      }

      // 根据文件大小选择上传方式
      if (file.size > chunkSize) {
        const uploadId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        return await uploadFileInChunks(file, uploadId)
      } else {
        return await uploadSimple(file)
      }

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed')
      setUploading(false)
      throw error
    }
  }, [uploadSimple, uploadFileInChunks, chunkSize])

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setUploading(false)
    setProgress(null)
    setError('Upload cancelled')
  }, [])

  const reset = useCallback(() => {
    setUploading(false)
    setProgress(null)
    setError(null)
    abortControllerRef.current = null
    progressRef.current = 0
    speedRef.current = []
  }, [])

  return {
    upload,
    uploading,
    progress,
    error,
    reset,
    cancel
  }
}

// 用于批量文件上传的Hook
export const useBatchFileUpload = (options: UseFileUploadOptions = {}) => {
  const [uploads, setUploads] = useState<Record<string, {
    progress: number
    status: 'pending' | 'uploading' | 'completed' | 'error'
    error?: string
  }>>({})

  const [overallProgress, setOverallProgress] = useState(0)

  const uploadFiles = useCallback(async (files: File[]) => {
    const uploadPromises = files.map(async (file, index) => {
      const fileId = `${file.name}-${index}`

      setUploads(prev => ({
        ...prev,
        [fileId]: { progress: 0, status: 'uploading' }
      }))

      try {
        const { upload } = useFileUpload({
          ...options,
          onProgress: (progress) => {
            setUploads(prev => ({
              ...prev,
              [fileId]: { ...prev[fileId], progress: progress.percentage }
            }))
          }
        })

        const result = await upload(file)

        setUploads(prev => ({
          ...prev,
          [fileId]: { progress: 100, status: 'completed' }
        }))

        return result

      } catch (error) {
        setUploads(prev => ({
          ...prev,
          [fileId]: {
            progress: 0,
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed'
          }
        }))

        throw error
      }
    })

    const results = await Promise.allSettled(uploadPromises)

    // 计算总体进度
    const completed = Object.values(uploads).filter(u => u.status === 'completed').length
    setOverallProgress(Math.round((completed / files.length) * 100))

    return results
  }, [options])

  const reset = useCallback(() => {
    setUploads({})
    setOverallProgress(0)
  }, [])

  return {
    uploads,
    overallProgress,
    uploadFiles,
    reset
  }
}