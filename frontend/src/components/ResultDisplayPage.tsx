/**
 * 结果展示页面组件
 * Result Display Page Component
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tag,
  Descriptions,
  Table,
  Tabs,
  Progress,
  Alert,
  Statistic,
  Timeline,
  List,
  Avatar,
  Tooltip,
  Switch,
  Divider,
  Image,
  Spin
} from 'antd'
import {
  DownloadOutlined,
  EyeOutlined,
  FileTextOutlined,
  StarOutlined,
  ShareAltOutlined,
  HistoryOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  EditOutlined,
  CopyOutlined,
  PrinterOutlined,
  FullscreenOutlined,
  SettingOutlined
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import remarkGfm from 'remark-gfm'
import { Prism as PrismTheme } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import { useGuideline } from '@/hooks/useGuideline'
import { ProcessingResult, QualityIssue, User } from '@/types'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface ResultDisplayPageProps {
  guidelineId: string
  onEdit?: (guideline: any) => void
}

const ResultDisplayPage: React.FC<ResultDisplayPageProps> = ({ guidelineId, onEdit }) => {
  const [activeTab, setActiveTab] = useState('content')
  const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview')
  const [fullscreen, setFullscreen] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const {
    currentGuideline,
    processingResult,
    loading,
    downloadPVG
  } = useGuideline({
    onSuccess: (msg) => {
      console.log('Guideline loaded:', msg)
    },
    onError: (error) => {
      console.error('Failed to load guideline:', error)
    }
  })

  useEffect(() => {
    if (guidelineId) {
      // 这里需要实现获取单个指南的函数
      // fetchGuideline(guidelineId)
    }
  }, [guidelineId])

  // 渲染质量评分
  const renderQualityScores = useCallback(() => {
    if (!processingResult) return null

    const scores = [
      { label: '总体质量', value: processingResult.overallQualityScore, max: 100 },
      { label: '准确性', value: processingResult.accuracyScore, max: 100 },
      { label: '可读性', value: processingResult.readabilityScore, max: 100 },
      { label: '完整性', value: processingResult.completenessScore, max: 100 },
      { label: '医学安全性', value: processingResult.medicalSafetyScore, max: 100 },
      { label: '患者友好度', value: processingResult.patientFriendlyScore, max: 100 }
    ]

    return (
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {scores.map((score, index) => (
          <Col xs={12} sm={8} md={4} key={index}>
            <Card size="small">
              <Statistic
                title={score.label}
                value={score.value || 0}
                suffix="/ 100"
                precision={1}
                valueStyle={{
                  color: score.value! >= 80 ? '#3f8600' : score.value! >= 60 ? '#fa8c16' : '#ff4d4f'
                }}
                prefix={<Progress percent={score.value || 0} size="small" />}
              />
            </Card>
          </Col>
        ))}
      </Row>
    )
  }, [processingResult])

  // 渲染质量评估详情
  const renderQualityAssessment = useCallback(() => {
    if (!processingResult?.qualityIssues) return null

    const getSeverityColor = (severity: string) => {
      const colors = {
        'low': '#52c41a',
        'medium': '#fa8c16',
        'high': '#ff4d4f',
        'critical': '#722ed1'
      }
      return colors[severity] || '#d9d9d9'
    }

    return (
      <Card title="质量评估详情" style={{ marginBottom: 16 }}>
        <List
          dataSource={processingResult.qualityIssues}
          renderItem={(issue: QualityIssue, index) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Avatar
                    style={{ backgroundColor: getSeverityColor(issue.severity) }}
                    icon={<InfoCircleOutlined />}
                  />
                }
                title={
                  <Space>
                    <Tag color={getSeverityColor(issue.severity)}>
                      {issue.type.toUpperCase()}
                    </Tag>
                    <Text strong>{issue.message}</Text>
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary">{issue.suggestion}</Text>
                    {issue.location && (
                      <div style={{ marginTop: 4 }}>
                        <Text code>
                          {issue.location.line ? `行 ${issue.location.line}` : ''}
                          {issue.location.section && ` - ${issue.location.section}`}
                        </Text>
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    )
  }, [processingResult])

  // 渲染统计信息
  const renderStatistics = useCallback(() => {
    if (!processingResult) return null

    const stats = [
      { title: '字符数', value: processingResult.contentLength.toLocaleString() },
      { title: '词数', value: processingResult.wordCount.toLocaleString() },
      { title: '章节数', value: processingResult.sectionsCount || 0 },
      { title: '处理时间', value: `${(processingResult.processingTime || 0).toFixed(2)}秒` },
      { title: 'Token使用', value: processingResult.tokenUsage.toLocaleString() },
      { title: '处理成本', value: `$${(processingResult.cost || 0).toFixed(4)}` }
    ]

    return (
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {stats.map((stat, index) => (
          <Col xs={12} sm={8} md={4} key={index}>
            <Card size="small">
              <Statistic title={stat.title} value={stat.value} />
            </Card>
          </Col>
        ))}
      </Row>
    )
  }, [processingResult])

  // 渲染处理步骤信息
  const renderProcessingSteps = useCallback(() => {
    if (!processingResult?.processingSteps) return null

    return (
      <Card title="处理步骤" style={{ marginBottom: 16 }}>
        <Timeline>
          {processingResult.processingSteps.map((step, index) => (
            <TimelineItem
              key={index}
              color={step.status === 'completed' ? 'green' : step.status === 'failed' ? 'red' : 'blue'}
              dot={
                <Progress
                  type="circle"
                  percent={step.progress}
                  size="small"
                  status={step.status === 'completed' ? 'success' : step.status === 'failed' ? 'exception' : 'active'}
                />
              }
            >
              <div>
                <Text strong>{step.name}</Text>
                <br />
                <Text type="secondary">{step.description}</Text>
                {step.duration && (
                  <Text type="secondary">耗时：{step.duration.toFixed(2)}秒</Text>
                )}
                {step.error && (
                  <Alert
                    message={step.error}
                    type="error"
                    size="small"
                    style={{ marginTop: 8 }}
                  />
                )}
              </div>
            </TimelineItem>
          ))}
        </Timeline>
      </Card>
    )
  }, [processingResult])

  // 渲染内容
  const renderContent = useCallback(() => {
    if (!processingResult?.pvgContent && !currentGuideline?.processedContent) {
      return (
        <Empty
          description="暂无处理结果"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )
    }

    const content = processingResult?.pvgContent || currentGuideline?.processedContent || ''

    return (
      <Card
        title="处理结果"
        extra={[
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowSettings(!showSettings)}
          >
            设置
          </Button>,
          <Button
            icon={<FullscreenOutlined />}
            onClick={() => setFullscreen(!fullscreen)}
          >
            {fullscreen ? '退出全屏' : '全屏'}
          </Button>,
          <Button
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(content)
            }}
          >
            复制
          </Button>
        ]
        style={{ marginBottom: 16 }}
      >
        <div style={fullscreen ? { minHeight: '100vh' } : {}}>
          {viewMode === 'preview' ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              className="markdown-content"
              style={{
                padding: '24px',
                backgroundColor: '#fff',
                borderRadius: 8,
                minHeight: 400
              }}
            >
              {content}
            </ReactMarkdown>
          ) : (
            <SyntaxHighlighter
              language="markdown"
              style={PrismTheme}
              showLineNumbers
              customStyle={{
                backgroundColor: '#f6f8fa',
                borderRadius: 8,
                padding: 16,
                minHeight: 400
              }}
            >
              {content}
            </SyntaxHighlighter>
          )}
        </div>
      </Card>
    )
  }, [processingResult, currentGuideline, viewMode, fullscreen, showSettings])

  // 渲染基础信息
  const renderBasicInfo = useCallback(() => {
    return (
      <Card title="指南信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="标题">{currentGuideline?.title}</Descriptions.Item>
          <Descriptions.Item label="作者">{currentGuideline?.author || '-'}</Descriptions.Item>
          <Descriptions.Item label="出版机构">{currentGuideline?.publisher || '-'}</Descriptions.Item>
          <Descriptions.Item label="出版年份">{currentGuideline?.publicationYear || '-'}</Descriptions.Item>
          <Descriptions.Item label="处理模式">{currentGuideline?.processingMode}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {currentGuideline?.createdAt ? dayjs(currentGuideline.createdAt).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="处理时间">
            {currentGuideline?.updatedAt ? dayjs(currentGuideline.updatedAt).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="版本">{currentGuideline?.version}</Descriptions.Item>
          <Descriptions.Item label="标签">
            <Space wrap>
              {currentGuideline?.tags?.map(tag => (
                <Tag key={tag}>{tag}</Tag>
              )) || <Text type="secondary">无</Text>}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    )
  }, [currentGuideline])

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <FileTextOutlined /> 处理结果
        </Title>
        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => downloadPVG(guidelineId)}
            disabled={!processingResult && !currentGuideline?.processedContent}
          >
            下载PVG
          </Button>
          <Button
            icon={<EditOutlined />}
            onClick={() => onEdit?.(currentGuideline)}
          >
            编辑
          </Button>
        </Space>
      </div>

      {currentGuideline?.status === 'processing' ? (
        <Alert
          message="处理中"
          description="指南正在处理中，请稍后查看结果"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      ) : currentGuideline?.status === 'failed' ? (
        <Alert
          message="处理失败"
          description={currentGuideline.errorMessage || '处理过程中出现错误，请重试或联系管理员'}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      ) : null}

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="内容展示" key="content">
          {renderContent()}
        </TabPane>
        <TabPane tab="质量评估" key="quality">
          {renderQualityScores()}
          {renderQualityAssessment()}
        </TabPane>
        <TabPane tab="统计信息" key="statistics">
          {renderStatistics()}
        </TabPane>
        <TabPane tab="处理步骤" key="steps">
          {renderProcessingSteps()}
        </TabPane>
        <TabPane tab="基本信息" key="info">
          {renderBasicInfo()}
        </TabPane>
      </Tabs>
    </div>
  )
}

export default ResultDisplayPage