/**
 * 历史管理页面组件
 * History Management Page Component
 */

import React, { useState, useCallback, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Typography,
  Modal,
  Descriptions,
  Timeline,
  Avatar,
  Progress,
  message,
  Tooltip,
  Popconfirm,
  Badge,
  Empty
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  EyeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  HistoryOutlined,
  FileTextOutlined,
  CalendarOutlined,
  UserOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CopyOutlined,
  ShareAltOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { Guideline, Task, TaskStatus, User } from '@/types'
import { useGuideline } from '@/hooks/useGuideline'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const { Title, Text, Paragraph } = Typography
const { RangePicker } = DatePicker

interface HistoryPageProps {
  currentUser?: User
}

const HistoryPage: React.FC<HistoryPageProps> = ({ currentUser }) => {
  const [guidelines, setGuidelines] = useState<Guideline[]>([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    fileType: '',
    processingMode: '',
    dateRange: null,
    tags: [] as string[]
  })
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedGuideline, setSelectedGuideline] = useState<Guideline | null>(null)
  const [versionModalVisible, setVersionModalVisible] = useState(false)

  const { deleteGuideline, downloadPVG } = useGuideline({
    onSuccess: (msg) => message.success(msg),
    onError: (error) => message.error(error)
  })

  // 状态映射
  const statusMap = {
    uploaded: { text: '已上传', color: 'default', icon: <ClockCircleOutlined /> },
    parsing: { text: '解析中', color: 'processing', icon: <ClockCircleOutlined /> },
    processing: { text: '处理中', color: 'processing', icon: <ClockCircleOutlined /> },
    completed: { text: '已完成', color: 'success', icon: <CheckCircleOutlined /> },
    failed: { text: '失败', color: 'error', icon: <ExclamationCircleOutlined /> },
    archived: { text: '已归档', color: 'warning', icon: <HistoryOutlined /> }
  }

  const processingModeMap = {
    slow: { text: 'Slow模式', color: 'blue' },
    fast: { text: 'Fast模式', color: 'orange' },
    custom: { text: '自定义', color: 'purple' }
  }

  // 表格列定义
  const columns: ColumnsType<Guideline> = [
    {
      title: '指南信息',
      key: 'info',
      width: 300,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <Text ellipsis style={{ display: 'block' }}>
              {record.title}
            </Text>
          </div>
          <Space wrap>
            <Tag color={processingModeMap[record.processingMode as keyof typeof processingModeMap]?.color}>
              {processingModeMap[record.processingMode as keyof typeof processingModeMap]?.text}
            </Tag>
            {record.tags.map(tag => (
              <Tag key={tag} size="small">{tag}</Tag>
            ))}
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.author} · {record.publisher}
          </Text>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const config = statusMap[status as keyof typeof statusMap]
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      }
    },
    {
      title: '进度',
      key: 'progress',
      width: 120,
      render: (_, record) => (
        <Progress
          percent={Math.round(record.processingProgress)}
          size="small"
          status={record.status === 'completed' ? 'success' : record.status === 'failed' ? 'exception' : 'active'}
          format={(percent) => `${percent}%`}
        />
      )
    },
    {
      title: '文件信息',
      key: 'fileInfo',
      width: 150,
      render: (_, record) => (
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.originalFilename}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.fileType.toUpperCase()} · {(record.fileSize / 1024 / 1024).toFixed(1)}MB
          </Text>
        </div>
      )
    },
    {
      title: '处理时间',
      key: 'processingTime',
      width: 120,
      render: (_, record) => {
        if (!record.updatedAt) return '-'
        return (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(record.updatedAt).format('MM-DD HH:mm')}
          </Text>
        )
      }
    },
    {
      title: '访问量',
      key: 'stats',
      width: 100,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div style={{ textAlign: 'center' }}>
            <Text style={{ fontSize: 12 }}>
              👁 {record.viewCount}
            </Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text style={{ fontSize: 12 }}>
              ⬇ {record.downloadCount}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedGuideline(record)
                setDetailModalVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title="下载PVG">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              disabled={record.status !== 'completed'}
              onClick={() => downloadPVG(record.id)}
            />
          </Tooltip>
          <Tooltip title="版本历史">
            <Button
              type="text"
              icon={<HistoryOutlined />}
              onClick={() => {
                setSelectedGuideline(record)
                setVersionModalVisible(true)
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个指南吗？"
            onConfirm={() => deleteGuideline(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 获取指南列表
  const fetchGuidelines = useCallback(async (params = {}) => {
    setLoading(true)
    try {
      const searchParams = new URLSearchParams()

      if (params.page) searchParams.append('page', params.page.toString())
      if (params.pageSize) searchParams.append('pageSize', params.pageSize.toString())
      if (filters.search) searchParams.append('search', filters.search)
      if (filters.status) searchParams.append('status', filters.status)
      if (filters.fileType) searchParams.append('fileType', filters.fileType)
      if (filters.processingMode) searchParams.append('processingMode', filters.processingMode)
      if (filters.tags?.length) {
        filters.tags.forEach(tag => searchParams.append('tags', tag))
      }
      if (filters.dateRange) {
        searchParams.append('startDate', filters.dateRange[0])
        searchParams.append('endDate', filters.dateRange[1])
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/guidelines?${searchParams}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('获取指南列表失败')
      }

      const data = await response.json()

      if (data.success) {
        setGuidelines(data.data || [])
        setPagination({
          current: data.pagination?.current || 1,
          pageSize: data.pagination?.pageSize || 10,
          total: data.pagination?.total || 0
        })
      } else {
        throw new Error(data.message || '获取指南列表失败')
      }

    } catch (error) {
      console.error('Failed to fetch guidelines:', error)
      message.error('获取指南列表失败')
    } finally {
      setLoading(false)
    }
  }, [filters])

  // 处理搜索
  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchGuidelines({ page: 1, ...filters, search: value })
  }

  // 处理状态过滤
  const handleStatusFilter = (value: string) => {
    setFilters(prev => ({ ...prev, status: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchGuidelines({ page: 1, ...filters, status: value })
  }

  // 处理文件类型过滤
  const handleFileTypeFilter = (value: string) => {
    setFilters(prev => ({ ...prev, fileType: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchGuidelines({ page: 1, ...filters, fileType: value })
  }

  // 处理处理模式过滤
  const handleProcessingModeFilter = (value: string) => {
    setFilters(prev => ({ ...prev, processingMode: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchGuidelines({ page: 1, ...filters, processingMode: value })
  }

  // 处理日期范围过滤
  const handleDateRangeChange = (dates: any) => {
    setFilters(prev => ({
      ...prev,
      dateRange: dates ? [
        dates[0].format('YYYY-MM-DD'),
        dates[1].format('YYYY-MM-DD')
      ] : null
    }))
    setPagination(prev => ({ ...prev, current: 1 }))
    fetchGuidelines({ page: 1, ...filters, dateRange: dates })
  }

  // 处理分页
  const handleTableChange = (paginationConfig: any) => {
    setPagination(paginationConfig)
    fetchGuidelines({
      page: paginationConfig.current,
      pageSize: paginationConfig.pageSize
    })
  }

  // 复制内容到剪贴板
  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      message.success('复制成功')
    } catch (error) {
      message.error('复制失败')
    }
  }, [])

  // 统计数据
  const renderStatistics = useCallback(() => {
    const total = guidelines.length
    const completed = guidelines.filter(g => g.status === 'completed').length
    const processing = guidelines.filter(g => g.status === 'processing').length
    const failed = guidelines.filter(g => g.status === 'failed').length

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic title="总指南数" value={total} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="已完成"
              value={completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="处理中"
              value={processing}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="失败"
              value={failed}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>
    )
  }, [guidelines])

  // 渲染详情模态框内容
  const renderDetailModalContent = () => {
    if (!selectedGuideline) return null

    return (
      <>
        <Descriptions
          title="基本信息"
          column={2}
          bordered
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Descriptions.Item label="标题">{selectedGuideline.title}</Descriptions.Item>
          <Descriptions.Item label="作者">{selectedGuideline.author}</Descriptions.Item>
          <Descriptions.Item label="出版机构">{selectedGuideline.publisher}</Descriptions.Item>
          <Descriptions.Item label="出版年份">{selectedGuideline.publicationYear}</Descriptions.Item>
          <Descriptions.Item label="文件名">{selectedGuideline.originalFilename}</Descriptions.Item>
          <Descriptions.Item label="文件类型">{selectedGuideline.fileType}</Descriptions.Item>
          <Descriptions.Item label="文件大小">
            {(selectedGuideline.fileSize / 1024 / 1024).toFixed(2)} MB
          </Descriptions.Item>
          <Descriptions.Item label="处理模式">
            <Tag color={processingModeMap[selectedGuideline.processingMode as keyof typeof processingModeMap]?.color}>
              {processingModeMap[selectedGuideline.processingMode as keyof typeof processingModeMap]?.text}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[selectedGuideline.status as keyof typeof statusMap]?.color}>
              {statusMap[selectedGuideline.status as keyof typeof statusMap]?.text}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(selectedGuideline.createdAt).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(selectedGuideline.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="访问量">{selectedGuideline.viewCount}</Descriptions.Item>
          <Descriptions.Item label="下载量">{selectedGuideline.downloadCount}</Descriptions.Item>
          <Descriptions.Item label="描述">
            <Paragraph ellipsis={{ rows: 3 }}>
              {selectedGuideline.description || '暂无描述'}
            </Paragraph>
          </Descriptions.Item>
        </Descriptions>

        {selectedGuideline.tags && selectedGuideline.tags.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <Text strong>标签：</Text>
              <div style={{ marginTop: 8 }}>
                {selectedGuideline.tags.map(tag => (
                  <Tag key={tag} style={{ marginBottom: 4 }}>{tag}</Tag>
                ))}
              </div>
            </div>
          )}

        {selectedGuideline.pvgSummary && (
            <div style={{ marginBottom: 16 }}>
              <Text strong>PVG摘要：</Text>
              <Paragraph style={{ marginTop: 8 }}>
                {selectedGuideline.pvgSummary}
              </Paragraph>
            </div>
          )}
        </>
    )
  }

  // 渲染版本历史
  const renderVersionHistory = useCallback(() => {
    return (
      <Timeline>
        <TimelineItem>
          <TimelineItem dot={<CheckCircleOutlined color="green" />}>
            <div>
              <Text strong>当前版本</Text>
              <Text type="secondary">
                v{selectedGuideline?.version} · {dayjs(selectedGuideline?.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
              </Text>
              <div style={{ marginTop: 8 }}>
                <Button
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(window.location.href)}
                >
                  复制链接
                </Button>
              </div>
            </div>
          </TimelineItem>
        </Timeline>
      )
    )
  }, [selectedGuideline, copyToClipboard])

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <HistoryOutlined /> 历史管理
      </Title>
      <Paragraph>
        查看和管理所有已上传的医学指南及其处理结果，支持搜索、过滤和批量操作。
      </Paragraph>

      {renderStatistics()}

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} sm={8}>
            <Input.Search
              placeholder="搜索指南标题、作者或关键词"
              allowClear
              enterButton
              value={filters.search}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </Col>
          <Col xs={24} sm={4}>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: '100%' }}
              value={filters.status}
              onChange={handleStatusFilter}
              options={[
                { value: '', label: '全部状态' },
                { value: 'uploaded', label: '已上传' },
                { value: 'processing', label: '处理中' },
                {value: 'completed', label: '已完成' },
                { value: 'failed', label: '失败' },
                { value: 'archived', label: '已归档' }
              ]}
            />
          </Col>
          <Col xs={24} sm={4}>
            <Select
              placeholder="处理模式"
              allowClear
              style={{ width: '100%' }}
              value={filters.processingMode}
              onChange={handleProcessingModeFilter}
              options={[
                { value: '', label: '全部模式' },
                { value: 'slow', label: 'Slow模式' },
                { value: 'fast', label: 'Fast模式' },
                { value: 'custom', label: '自定义' }
              ]}
            />
          </Col>
          <Col xs={24} sm={8}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={handleDateRangeChange}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Text strong>
              共 {pagination.total} 条记录
            </Text>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchGuidelines()}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={guidelines}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
          onChange={handleTableChange}
          rowSelection={{
            selectedRowKeys,
            onChange: (selectedRowKeys) => {
              setSelectedRowKeys(selectedRowKeys)
            }
          }}
        />
      </Card>

      {/* 详情模态框 */}
      <Modal
        title="指南详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false)
          setSelectedGuideline(null)
        }}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {renderDetailModalContent()}
      </Modal>

      {/* 版本历史模态框 */}
      <Modal
        title="版本历史"
        open={versionModalVisible}
        onCancel={() => {
          setVersionModalVisible(false)
        }}
        width={600}
        footer={[
          <Button key="close" onClick={() => setVersionModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {renderVersionHistory()}
      </Modal>
    </div>
  )
}

export default HistoryPage