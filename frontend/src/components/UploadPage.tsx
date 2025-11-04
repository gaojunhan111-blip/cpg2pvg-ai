/**
 * 指南上传页面组件 (优化版本)
 * Guideline Upload Page Component (Optimized Version)
 */

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import {
  Card,
  Upload,
  Button,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Tag,
  Space,
  Typography,
  Alert,
  Steps,
  Row,
  Col,
  Divider,
  message,
  Progress,
  Tabs,
  List,
  Descriptions,
  Tooltip,
  Modal,
  Spin,
  Empty,
  Image,
  Affix,
  BackTop,
  FloatButton,
  Tour,
  Badge,
  Timeline,
  Collapse
} from 'antd'
import {
  InboxOutlined,
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  DeleteOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  StarOutlined,
  HistoryOutlined,
  ShareAltOutlined,
  DragOutlined,
  FolderOpenOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileTextOutlined as FileTxtOutlined,
  FileMarkdownOutlined
} from '@ant-design/icons'
import type { UploadProps, UploadFile, RcFile } from 'antd/es/upload'
import { useGuideline } from '@/hooks/useGuideline'
import { useFileUpload } from '@/hooks/useFileUpload'
import { Guideline, TaskStatus, FileType } from '@/types'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps
const { Dragger } = Upload
const { TabPane } = Tabs
const { TextArea } = Input
const { Panel } = Collapse

interface UploadPageProps {
  onSuccess?: (guideline: Guideline, task?: any) => void
  preselectedFile?: File
  mode?: 'simple' | 'advanced'
}

interface FilePreview {
  id: string
  file: RcFile
  preview?: string
  metadata: {
    size: number
    type: string
    lastModified: number
    name: string
  }
  status: 'pending' | 'uploading' | 'completed' | 'error'
  progress?: number
  error?: string
}

const UploadPage: React.FC<UploadPageProps> = ({
  onSuccess,
  preselectedFile,
  mode = 'advanced'
}) => {
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [filePreviews, setFilePreviews] = useState<FilePreview[]>([])
  const [processingMode, setProcessingMode] = useState<'slow' | 'fast'>('slow')
  const [isPublic, setIsPublic] = useState(false)
  const [tags, setTags] = useState<string[]>([])
  const [inputTag, setInputTag] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const [showPreview, setShowPreview] = useState(false)
  const [showTour, setShowTour] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<FilePreview[]>([])
  const [showAdvanced, setShowAdvanced] = useState(mode === 'advanced')

  // Refs
  const dropZoneRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 检查是否为首次访问
  const [isFirstVisit, setIsFirstVisit] = useState(() => {
    return !localStorage.getItem('uploadPageVisited')
  })

  // 使用hooks with optimized options
  const {
    upload,
    uploading,
    progress,
    error,
    queue,
    pause,
    resume,
    cancel,
    retry
  } = useFileUpload({
    onSuccess: (response) => {
      message.success('文件上传成功!')
      handleStartProcessing(response.fileId)
      // 更新文件预览状态
      setFilePreviews(prev => prev.map(fp =>
        fp.status === 'uploading' ? { ...fp, status: 'completed', progress: 100 } : fp
      ))
    },
    onError: (error) => {
      message.error(`上传失败: ${error.message}`)
      setFilePreviews(prev => prev.map(fp =>
        fp.status === 'uploading' ? { ...fp, status: 'error', error: error.message } : fp
      ))
    },
    onProgress: (progressData) => {
      setFilePreviews(prev => prev.map(fp =>
        fp.status === 'uploading' ? { ...fp, progress: progressData.percentage } : fp
      ))
    },
    maxConcurrentChunks: 3,
    enableResume: true,
    queueLimit: 5
  })

  const { startProcessing, task } = useGuideline({
    onSuccess: (msg) => message.success(msg),
    onError: (error) => message.error(error),
    cacheEnabled: true,
    optimisticUpdates: true
  })

  // 处理预选文件
  useEffect(() => {
    if (preselectedFile) {
      handleAddFile(preselectedFile)
    }
  }, [preselectedFile])

  // 首次访问引导
  useEffect(() => {
    if (isFirstVisit) {
      setTimeout(() => setShowTour(true), 1000)
      localStorage.setItem('uploadPageVisited', 'true')
    }
  }, [isFirstVisit])

  // 获取文件图标
  const getFileIcon = useCallback((fileType: string) => {
    if (fileType.includes('pdf')) return <FilePdfOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
    if (fileType.includes('word') || fileType.includes('docx')) return <FileWordOutlined style={{ fontSize: 48, color: '#1890ff' }} />
    if (fileType.includes('markdown')) return <FileMarkdownOutlined style={{ fontSize: 48, color: '#52c41a' }} />
    return <FileTxtOutlined style={{ fontSize: 48, color: '#8c8c8c' }} />
  }, [])

  // 生成文件预览
  const generateFilePreview = useCallback(async (file: RcFile): Promise<string | undefined> => {
    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file)
    }
    return undefined
  }, [])

  // 添加文件
  const handleAddFile = useCallback(async (file: RcFile) => {
    const preview = await generateFilePreview(file)
    const filePreview: FilePreview = {
      id: `${file.name}-${Date.now()}`,
      file,
      preview,
      metadata: {
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        name: file.name
      },
      status: 'pending'
    }

    setFilePreviews(prev => [...prev, filePreview])
    setFileList([{
      uid: filePreview.id,
      name: file.name,
      status: 'done',
      originFileObj: file
    }])
  }, [generateFilePreview])

  // 移除文件
  const handleRemoveFile = useCallback((fileId: string) => {
    setFilePreviews(prev => prev.filter(fp => fp.id !== fileId))
    setFileList(prev => prev.filter(f => f.uid !== fileId))
  }, [])

  // 格式化文件大小
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }, [])

  // 验证文件
  const validateFile = useCallback((file: RcFile): { valid: boolean; error?: string } => {
    const maxSize = 100 * 1024 * 1024 // 100MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'text/markdown',
      'text/html'
    ]

    if (file.size > maxSize) {
      return { valid: false, error: '文件大小不能超过100MB' }
    }

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|docx?|txt|md|html)$/i)) {
      return { valid: false, error: '不支持的文件类型，请上传PDF、Word文档或文本文件' }
    }

    return { valid: true }
  }, [])

  // 处理拖拽
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    files.forEach(file => {
      const validation = validateFile(file)
      if (validation.valid) {
        handleAddFile(file)
      } else {
        message.error(validation.error)
      }
    })
  }, [validateFile, handleAddFile])

  // 处理文件选择
  const handleFileChange: UploadProps['onChange'] = ({ fileList: newFileList }) => {
    setFileList(newFileList.slice(-1)) // 只保留最新的一个文件
  }

  // 处理文件上传前的验证
  const beforeUpload = (file: File) => {
    const maxSize = 100 * 1024 * 1024 // 100MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'text/markdown',
      'text/html'
    ]

    if (file.size > maxSize) {
      message.error('文件大小不能超过100MB!')
      return false
    }

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|docx?|txt|md|html)$/i)) {
      message.error('只支持PDF、Word文档、TXT、Markdown和HTML文件!')
      return false
    }

    return false // 阻止自动上传，我们使用自定义上传
  }

  // 开始处理指南
  const handleStartProcessing = useCallback(async (fileId: string) => {
    try {
      const values = await form.validateFields()

      const formData = new FormData()
      formData.append('fileId', fileId)
      formData.append('title', values.title)
      formData.append('description', values.description || '')
      formData.append('author', values.author || '')
      formData.append('publisher', values.publisher || '')
      formData.append('publicationYear', values.publicationYear?.toString() || '')
      formData.append('tags', JSON.stringify(tags))
      formData.append('processingMode', processingMode)
      formData.append('priority', values.priority?.toString() || '0')
      formData.append('isPublic', isPublic.toString())

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/workflow/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        message.success('指南上传成功，开始处理...')
        onSuccess?.(data.data.guideline, data.data.task)
      } else {
        message.error(data.message || '上传失败')
      }

    } catch (error) {
      console.error('Upload error:', error)
      message.error('上传失败，请重试')
    }
  }, [form, tags, processingMode, isPublic, onSuccess])

  // 自定义上传
  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请先选择文件!')
      return
    }

    const file = fileList[0].originFileObj as File
    if (!file) {
      message.error('无效的文件!')
      return
    }

    try {
      // 首先上传文件
      const uploadResponse = await upload(file)

      // 然后开始处理
      await handleStartProcessing(uploadResponse.fileId)

    } catch (error) {
      console.error('Upload error:', error)
      message.error('上传失败，请重试')
    }
  }

  // 标签处理
  const handleTagAdd = () => {
    if (inputTag && tags.indexOf(inputTag) === -1) {
      setTags([...tags, inputTag])
    }
    setInputTag('')
  }

  const handleTagRemove = (removedTag: string) => {
    setTags(tags.filter(tag => tag !== removedTag))
  }

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.docx,.doc,.txt,.md,.html',
    beforeUpload,
    onChange: handleFileChange,
    fileList
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <FileTextOutlined /> 上传医学指南
      </Title>
      <Paragraph>
        上传临床医学指南文件，系统将自动将其转换为患者友好的可视化指南（PVG）。
      </Paragraph>

      <Row gutter={24}>
        <Col xs={24} lg={16}>
          {/* 文件上传区域 */}
          <Card title="选择文件" style={{ marginBottom: 24 }}>
            <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                点击或拖拽文件到此区域上传
              </p>
              <p className="ant-upload-hint">
                支持PDF、Word文档、TXT、Markdown和HTML文件，最大100MB
              </p>
            </Dragger>

            {error && (
              <Alert
                message="上传错误"
                description={error}
                type="error"
                showIcon
                closable
                style={{ marginBottom: 16 }}
              />
            )}

            {uploading && progress && (
              <div style={{ marginBottom: 16 }}>
                <Text>上传进度: {progress.percentage}%</Text>
                <Progress
                  percent={progress.percentage}
                  status={progress.percentage === 100 ? 'success' : 'active'}
                  style={{ marginTop: 8 }}
                />
                {progress.speed > 0 && (
                  <Text type="secondary">
                    速度: {(progress.speed / 1024).toFixed(2)} KB/s
                    {progress.timeRemaining > 0 &&
                      ` - 剩余时间: ${Math.round(progress.timeRemaining)}秒`
                    }
                  </Text>
                )}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={handleUpload}
                  loading={uploading}
                  disabled={fileList.length === 0}
                >
                  上传并处理
                </Button>
                <Button onClick={() => setFileList([])}>
                  清空文件
                </Button>
              </Space>
            </div>
          </Card>

          {/* 配置表单 */}
          <Card title="处理配置" style={{ marginBottom: 24 }}>
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                priority: 0,
                isPublic: false
              }}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="指南标题"
                    name="title"
                    rules={[{ required: true, message: '请输入指南标题' }]}
                  >
                    <Input placeholder="请输入指南标题" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item label="作者" name="author">
                    <Input placeholder="请输入作者姓名" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item label="出版机构" name="publisher">
                    <Input placeholder="请输入出版机构" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item label="出版年份" name="publicationYear">
                    <InputNumber
                      placeholder="请输入出版年份"
                      min={1900}
                      max={new Date().getFullYear()}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="描述" name="description">
                <TextArea
                  rows={3}
                  placeholder="请输入指南描述（可选）"
                  maxLength={500}
                  showCount
                />
              </Form.Item>

              <Row gutter={16}>
                <Col xs={24} sm={8}>
                  <Form.Item label="处理模式">
                    <Select
                      value={processingMode}
                      onChange={setProcessingMode}
                      options={[
                        { value: 'slow', label: 'Slow模式（完整9节点）', description: '完整、高质量的转换处理' },
                        { value: 'fast', label: 'Fast模式（快速处理）', description: '快速、基础的转换处理' }
                      ]}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item label="优先级" name="priority">
                    <Select
                      options={[
                        { value: 0, label: '普通' },
                        { value: 1, label: '较高' },
                        { value: 2, label: '高' },
                        { value: 3, label= '紧急' }
                      ]}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={8}>
                  <Form.Item label="公开访问">
                    <Switch
                      checked={isPublic}
                      onChange={setIsPublic}
                      checkedChildren="公开"
                      unCheckedChildren="私有"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="标签">
                <Space wrap>
                  {tags.map((tag, index) => (
                    <Tag
                      key={index}
                      closable
                      onClose={() => handleTagRemove(tag)}
                    >
                      {tag}
                    </Tag>
                  ))}
                  <Input
                    style={{ width: 120 }}
                    placeholder="添加标签"
                    value={inputTag}
                    onChange={e => setInputTag(e.target.value)}
                    onPressEnter={handleTagAdd}
                    onBlur={handleTagAdd}
                  />
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* 处理信息 */}
          {processingMode === 'slow' && (
            <Card title="Slow模式 - 9节点处理流程" style={{ marginBottom: 24 }}>
              <Alert
                message="完整的转换处理流程"
                description="Slow模式包含9个处理节点，提供完整、高质量的指南转换"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Steps
                direction="vertical"
                size="small"
                current={task ? -1 : 0}
              >
                <Step
                  title="文档解析"
                  description="解析文档结构，提取关键信息"
                  icon={<FileTextOutlined />}
                />
                <Step
                  title="结构分析"
                  description="分析文档层次结构和章节关系"
                />
                <Step
                  title="内容提取"
                  description="提取文本、表格、图片等多元内容"
                />
                <Step
                  title="知识图谱"
                  description="构建医学知识图谱和概念关系"
                />
                <Step
                  title="智能代理"
                  description="多AI代理协同处理和分析"
                />
                <Step
                  title="渐进生成"
                  description="迭代优化生成患者友好内容"
                />
                <Step
                  title="成本优化"
                  description="智能控制和优化处理成本"
                />
                <Step
                  title="质量控制"
                  description="多维度质量评估和验证"
                />
                <Step
                  title="可视化"
                  description="生成图表、流程图等可视化内容"
                />
              </Steps>
            </Card>
          )}

          {processingMode === 'fast' && (
            <Card title="Fast模式 - 快速处理流程" style={{ marginBottom: 24 }}>
              <Alert
                message="快速转换处理"
                description="Fast模式提供基础的指南转换，处理速度快，适合预览和简单转换"
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Steps
                direction="vertical"
                size="small"
                current={task ? -1 : 0}
              >
                <Step title="文档解析" description="快速解析文档内容" />
                <Step title="内容提取" description="提取主要文本内容" />
                <Step title="基础转换" description="转换为患者友好格式" />
              </Steps>
            </Card>
          )}
        </Col>

        <Col xs={24} lg={8}>
          {/* 右侧信息面板 */}
          <Card title="支持格式" size="small" style={{ marginBottom: 16 }}>
            <List
              size="small"
              dataSource={[
                { title: 'PDF文档', desc: '推荐格式，支持所有版本' },
                { title: 'Word文档', desc: '支持.docx和.doc格式' },
                { title: 'Markdown', desc: '轻量级标记语言格式' },
                { title: 'HTML', desc: '网页格式文档' },
                { title: '纯文本', desc: '基础文本格式' }
              ]}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<FileTextOutlined />}
                    title={item.title}
                    description={item.desc}
                  />
                </List.Item>
              )}
            />
          </Card>

          <Card title="处理要求" size="small" style={{ marginBottom: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="文件大小">最大 100MB</Descriptions.Item>
              <Descriptions.Item label="页数限制">建议 500 页以内</Descriptions.Item>
              <Descriptions.Item label="语言支持">中文、英文</Descriptions.Item>
              <Descriptions.Item label="处理时间">
                {processingMode === 'slow' ? '5-15分钟' : '1-3分钟'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="注意事项" size="small">
            <Alert
              message="隐私保护"
              description="上传的文档仅用于处理，不会被存储或分享。处理完成后将自动删除原始文件。"
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
            />
            <Divider style={{ margin: '12px 0' }} />
            <Alert
              message="质量保证"
              description="所有处理结果都经过严格的质量验证，确保医学内容的准确性和安全性。"
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default UploadPage