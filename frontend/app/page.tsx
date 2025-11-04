'use client'

import { Card, Row, Col, Button, Typography, Space } from 'antd'
import { FileTextOutlined, CloudUploadOutlined, BarChartOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

export default function HomePage() {
  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <Title level={1}>CPG2PVG-AI</Title>
          <Paragraph style={{ fontSize: '18px', color: '#666' }}>
            临床医学指南转化为公众医学指南的智能系统
          </Paragraph>
          <Paragraph>
            基于Slow工作流和多智能体协作的医学指南转化平台
          </Paragraph>
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', height: '200px' }}
              bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
            >
              <CloudUploadOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
              <Title level={4}>上传指南</Title>
              <Paragraph>上传临床医学指南文档，支持PDF、DOCX等格式</Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', height: '200px' }}
              bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
            >
              <FileTextOutlined style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }} />
              <Title level={4}>智能转化</Title>
              <Paragraph>使用AI技术将专业指南转化为公众易懂的内容</Paragraph>
            </Card>
          </Col>

          <Col xs={24} sm={8}>
            <Card
              hoverable
              style={{ textAlign: 'center', height: '200px' }}
              bodyStyle={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}
            >
              <BarChartOutlined style={{ fontSize: '48px', color: '#faad14', marginBottom: '16px' }} />
              <Title level={4}>结果分析</Title>
              <Paragraph>查看转化结果和质量分析报告</Paragraph>
            </Card>
          </Col>
        </Row>

        <div style={{ textAlign: 'center', marginTop: '48px' }}>
          <Space size="large">
            <Button type="primary" size="large" icon={<CloudUploadOutlined />}>
              开始上传
            </Button>
            <Button size="large" icon={<BarChartOutlined />}>
              查看演示
            </Button>
          </Space>
        </div>
      </div>
    </div>
  )
}