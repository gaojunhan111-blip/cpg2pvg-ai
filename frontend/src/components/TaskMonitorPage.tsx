/**
 * 任务监控页面组件
 * Task Monitor Page Component
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Progress,
  Steps,
  Timeline,
  Tag,
  Button,
  Space,
  Row,
  Col,
  Statistic,
  Table,
  Alert,
  Typography,
  Descriptions,
  Spin,
  Empty,
  Tooltip,
  Badge,
  List,
  Avatar
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  StopOutlined,
  EyeOutlined,
  DownloadOutlined,
  HistoryOutlined
} from '@ant-design/icons'
import { useTaskStream, useBatchTaskStream } from '@/hooks/useTaskStream'
import { Task, TaskStatus, TaskProgress, ProcessingStep } from '@/types'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const { Title, Text, Paragraph } = Typography
const { Step } = Steps
const { TimelineItem } = Timeline
const { Countdown } = Statistic

interface TaskMonitorPageProps {
  taskId?: string
  onTaskComplete?: (task: Task) => void
}

const TaskMonitorPage: React.FC<TaskMonitorPageProps> = ({ taskId, onTaskComplete }) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())
  const [showDetails, setShowDetails] = useState(false)

  // 使用任务流监控Hook
  const {
    progress,
    isConnected,
    error,
    reconnect,
    task,
    disconnect
  } = useTaskStream(taskId!, {
    onProgress: (progressData) => {
      console.log('Task progress:', progressData)
    },
    onCompleted: (result) => {
      console.log('Task completed:', result)
      onTaskComplete?.(task!)
    },
    onError: (errorMsg) => {
      console.error('Task error:', errorMsg)
    },
    autoReconnect: true
  })

  // 状态映射
  const getStatusConfig = useCallback((status: TaskStatus) => {
    const configs = {
      [TaskStatus.PENDING]: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      [TaskStatus.QUEUED]: { color: 'processing', icon: <ClockCircleOutlined />, text: '排队中' },
      [TaskStatus.RUNNING]: { color: 'processing', icon: <PlayCircleOutlined />, text: '处理中' },
      [TaskStatus.COMPLETED]: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      [TaskStatus.FAILED]: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
      [TaskStatus.CANCELLED]: { color: 'warning', icon: <StopOutlined />, text: '已取消' },
      [TaskStatus.RETRYING]: { color: 'warning', icon: <ReloadOutlined />, text: '重试中' }
    }
    return configs[status] || { color: 'default', icon: <ClockCircleOutlined />, text: '未知' }
  }, [])

  // 格式化时间
  const formatDuration = useCallback((seconds?: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    if (hours > 0) {
      return `${hours}时${minutes}分${secs}秒`
    } else if (minutes > 0) {
      return `${minutes}分${secs}秒`
    } else {
      return `${secs}秒`
    }
  }, [])

  // 步骤配置
  const workflowSteps = [
    { title: '文档解析', key: 'document_parsing', icon: '📄' },
    { title: '结构分析', key: 'structure_analysis', icon: '🔍' },
    { title: '内容提取', key: 'content_extraction', icon: '📝' },
    { title: '知识图谱', key: 'knowledge_graph', icon: '🕸️' },
    { title: '智能代理', key: 'intelligent_agent', icon: '🤖' },
    { title: '渐进生成', key: 'progressive_generation', icon: '🔄' },
    { title: '成本优化', key: 'cost_optimization', icon: '💰' },
    { title: '质量控制', key: 'quality_control', icon: '✅' },
    { title: '可视化', key: 'visualization', icon: '📊' }
  ]

  // 获取当前步骤索引
  const getCurrentStepIndex = useCallback(() => {
    if (!task || !task.currentStep) return 0
    const stepIndex = workflowSteps.findIndex(step => step.key === task.currentStep)
    return Math.max(0, stepIndex)
  }, [task])

  // 切换步骤展开状态
  const toggleStepExpand = useCallback((stepIndex: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepIndex)) {
      newExpanded.delete(stepIndex)
    } else {
      newExpanded.add(stepIndex)
    }
    setExpandedSteps(newExpanded)
  }, [expandedSteps])

  // 渲染进度详情
  const renderProgressDetails = useCallback(() => {
    if (!progress) return null

    return (
      <Card title="进度详情" size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="当前步骤">{progress.stepName}</Descriptions.Item>
          <Descriptions.Item label="步骤序号">{progress.stepNumber + 1}/{task?.totalSteps}</Descriptions.Item>
          <Descriptions.Item label="总体进度">{progress.progress}%</Descriptions.Item>
          <Descriptions.Item label="状态">{progress.status}</Descriptions.Item>
          {progress.startTime && (
            <Descriptions.Item label="开始时间">
              {dayjs(progress.startTime).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
          {progress.endTime && (
            <Descriptions.Item label="结束时间">
              {dayjs(progress.endTime).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
          {progress.duration && (
            <Descriptions.Item label="耗时">{formatDuration(progress.duration)}</Descriptions.Item>
          )}
        </Descriptions>

        {progress.error && (
          <Alert
            message="错误信息"
            description={progress.error}
            type="error"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {progress.output && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>输出结果</Title>
            <pre style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 6,
              fontSize: 12,
              maxHeight: 200,
              overflow: 'auto'
            }}>
              {JSON.stringify(progress.output, null, 2)}
            </pre>
          </div>
        )}
      </Card>
    )
  }, [progress, task, formatDuration])

  // 渲染任务状态卡片
  const renderStatusCard = useCallback(() => {
    const statusConfig = getStatusConfig(task?.status || TaskStatus.PENDING)

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="任务状态"
              value={statusConfig.text}
              prefix={<span style={{ color: statusConfig.color === 'default' ? '#8c8c8c' : statusConfig.color }}>
                {statusConfig.icon}
              </span>}
              valueStyle={{ color: statusConfig.color }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="处理进度"
              value={progress?.progress || 0}
              suffix="%"
              prefix={<Progress
                type="circle"
                percent={progress?.progress || 0}
                width={60}
                size="small"
                status={task?.status === TaskStatus.FAILED ? 'exception' : 'active'}
              />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="连接状态"
              value={isConnected ? "已连接" : "未连接"}
              prefix={
                <span style={{ color: isConnected ? '#52c41a' : '#ff4d4f' }}>
                  {isConnected ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                </span>
              }
              valueStyle={{ color: isConnected ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>
    )
  }, [task, progress, isConnected, getStatusConfig])

  // 渲染工作流步骤
  const renderWorkflowSteps = useCallback(() => {
    const currentStep = getCurrentStepIndex()

    return (
      <Card title="处理流程" style={{ marginBottom: 16 }}>
        <Steps
          current={currentStep}
          status={task?.status === TaskStatus.FAILED ? 'error' : 'process'}
          direction="horizontal"
          size="small"
        >
          {workflowSteps.map((step, index) => (
            <Step
              key={step.key}
              title={step.title}
              icon={<span>{step.icon}</span>}
              description={
                expandedSteps.has(index) && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">
                      {step.key === task?.currentStep
                        ? `当前正在处理${step.title}`
                        : `${step.title}等待处理`
                      }
                    </Text>
                  </div>
                )
              }
            />
          ))}
        </Steps>

        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Button
            type="link"
            onClick={() => setExpandedSteps(
              expandedSteps.size > 0 ? new Set() : new Set(workflowSteps.map((_, index) => index))
            )}
          >
            {expandedSteps.size > 0 ? '收起详情' : '展开详情'}
          </Button>
        </div>
      </Card>
    )
  }, [task, getCurrentStepIndex, expandedSteps, workflowSteps])

  // 渲染时间线
  const renderTimeline = useCallback(() => {
    if (!task) return null

    const timelineItems = []

    // 添加创建时间
    timelineItems.push({
      dot: <ClockCircleOutlined />,
      color: 'blue',
      children: (
        <div>
          <Text strong>任务创建</Text>
          <br />
          <Text type="secondary">{dayjs(task.createdAt).format('YYYY-MM-DD HH:mm:ss')}</Text>
        </div>
      )
    })

    // 添加开始时间
    if (task.startTime) {
      timelineItems.push({
        dot: <PlayCircleOutlined />,
        color: 'green',
        children: (
          <div>
            <Text strong>开始处理</Text>
            <br />
            <Text type="secondary">{dayjs(task.startTime).format('YYYY-MM-DD HH:mm:ss')}</Text>
          </div>
        )
      })
    }

    // 添加当前进度
    if (task.status === TaskStatus.RUNNING && progress) {
      timelineItems.push({
        dot: <Spin size="small" />,
        color: 'blue',
        children: (
          <div>
            <Text strong>正在处理：{progress.stepName}</Text>
            <br />
            <Progress percent={progress.progress} size="small" style={{ width: 200 }} />
          </div>
        )
      })
    }

    // 添加完成或失败时间
    if (task.endTime) {
      const isSuccess = task.status === TaskStatus.COMPLETED
      timelineItems.push({
        dot: isSuccess ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />,
        color: isSuccess ? 'green' : 'red',
        children: (
          <div>
            <Text strong>{isSuccess ? '处理完成' : '处理失败'}</Text>
            <br />
            <Text type="secondary">{dayjs(task.endTime).format('YYYY-MM-DD HH:mm:ss')}</Text>
            {task.duration && (
              <>
                <br />
                <Text type="secondary">耗时：{formatDuration(task.duration)}</Text>
              </>
            )}
          </div>
        )
      })
    }

    return (
      <Card title="处理时间线" size="small">
        <Timeline items={timelineItems} />
      </Card>
    )
  }, [task, progress, formatDuration])

  // 渲染错误信息
  const renderErrorInfo = useCallback(() => {
    if (!error && !task?.errorMessage) return null

    return (
      <Alert
        message="连接错误"
        description={error || task?.errorMessage}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={reconnect}>
            重新连接
          </Button>
        }
        style={{ marginBottom: 16 }}
      />
    )
  }, [error, task?.errorMessage, reconnect])

  if (!taskId) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Empty
          description="请提供任务ID以监控处理进度"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <EyeOutlined /> 任务监控
        </Title>
        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => window.open(`/api/v1/tasks/${taskId}/download`, '_blank')}
          >
            下载结果
          </Button>
          <Button
            icon={<HistoryOutlined />}
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? '隐藏详情' : '显示详情'}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={reconnect}
            disabled={isConnected}
          >
            重新连接
          </Button>
        </Space>
      </div>

      {renderStatusCard()}
      {renderErrorInfo()}
      {renderWorkflowSteps()}

      <Row gutter={16}>
        <Col xs={24} lg={showDetails ? 12 : 24}>
          {renderTimeline()}
        </Col>
        <Col xs={24} lg={showDetails ? 12 : 24}>
          {showDetails && renderProgressDetails()}
        </Col>
      </Row>
    </div>
  )
}

export default TaskMonitorPage