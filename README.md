# CPG2PVG-AI

将临床医学指南(CPG)转化为公众医学指南(PVG)的智能系统

## 项目概述

CPG2PVG-AI是一个基于多智能体协作的医疗AI系统，旨在将专业的临床医学指南转化为通俗易懂的公众医学指南。系统采用Slow工作流架构，包含9个核心技术节点，确保转化结果的准确性、可读性和完整性。

### 核心特性

- **智能文档解析**: 支持PDF、DOCX等多种格式的医学指南文档
- **多模态处理**: 并行处理文本、表格、图表等不同类型内容
- **知识图谱增强**: 集成医学知识图谱提升语义理解
- **分层智能体系统**: 多专业智能体协同处理不同医学领域内容
- **渐进式内容生成**: 关键内容优先生成，支持流式输出
- **智能缓存系统**: 基于语义相似性的缓存机制
- **成本优化策略**: 根据任务复杂度选择最优模型
- **多层质量控制**: 医学准确性、可读性、一致性全面验证
- **性能监控**: 实时监控和自适应优化

## 技术架构

### 后端技术栈
- **Web框架**: FastAPI 0.104.1
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0
- **缓存**: Redis 7
- **任务队列**: Celery 5.3
- **文件存储**: MinIO
- **AI模型**: OpenAI GPT-4/3.5, Anthropic Claude
- **医学NLP**: spaCy + scispaCy

### 前端技术栈
- **框架**: Next.js 14 + TypeScript
- **UI库**: Ant Design 5
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **图表**: Recharts
- **实时通信**: Server-Sent Events

### 部署架构
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (可选)

## Slow工作流架构

系统采用Slow工作流模式，完整保留9个技术节点：

1. **智能文档解析层** (HierarchicalMedicalParser)
   - 基于医学文档结构的智能解析
   - 自适应分块策略
   - 多格式文档支持

2. **多模态内容处理管道** (MultiModalProcessor)
   - 并行处理不同模态内容
   - 表格、图表智能提取
   - 内容整合与优化

3. **基于知识图谱的语义理解** (MedicalKnowledgeGraph)
   - 医学实体识别与链接
   - 临床关系推理
   - 上下文构建

4. **分层智能体系统** (IntelligentAgentOrchestrator)
   - 诊断、治疗、预防等专业智能体
   - 并行处理与协调
   - 结果整合

5. **渐进式内容生成** (ProgressiveContentGenerator)
   - 关键内容优先生成
   - 流式输出支持
   - 质量分级处理

6. **智能缓存和记忆系统** (MedicalContentCache)
   - 语义相似性缓存
   - 处理模式记忆
   - 自适应缓存策略

7. **成本优化策略** (AdaptiveCostOptimizer)
   - 模型智能选择
   - Token使用优化
   - 批量处理策略

8. **质量控制和验证系统** (MultiLayerQualityController)
   - 医学准确性检查
   - 可读性评估
   - 一致性验证

9. **性能监控和自适应调整** (PerformanceMonitor)
   - 实时性能监控
   - 参数自动优化
   - 异常检测与告警

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (本地开发)
- Python 3.11+ (本地开发)

### 🚀 使用Docker Compose一键启动

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd cpg2pvg-ai
   ```

2. **一键启动所有服务**
   ```bash
   make docker-up
   # 或者
   docker-compose up -d
   ```

3. **等待服务启动完成**（约1-2分钟）
   ```bash
   # 查看服务状态
   docker-compose ps
   ```

4. **访问应用**
   - 🎯 前端界面: http://localhost:3000
   - 🔧 后端API: http://localhost:8000
   - 📚 API文档: http://localhost:8000/docs
   - 📊 Celery监控: http://localhost:5555
   - 💾 MinIO控制台: http://localhost:9001 (minioadmin/minioadmin)

### 🛠️ 本地开发模式

#### 后端开发
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动数据库服务
docker-compose up -d postgres redis minio

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 启动Celery Worker
```bash
cd backend

# 启动Celery Worker
celery -A celery_worker.celery_app worker --loglevel=info

# 启动Celery Beat (定时任务)
celery -A celery_worker.celery_app beat --loglevel=info

# 启动Flower监控
celery -A celery_worker.celery_app flower --port=5555
```

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### Celery Worker

```bash
cd backend

# 启动Celery Worker
celery -A celery_worker.celery_app worker --loglevel=info

# 启动Celery Beat (定时任务)
celery -A celery_worker.celery_app beat --loglevel=info

# 启动Flower监控
celery -A celery_worker.celery_app flower --port=5555
```

## API文档

### 主要端点

- `POST /api/v1/guidelines/upload` - 上传医学指南
- `GET /api/v1/guidelines` - 获取指南列表
- `GET /api/v1/guidelines/{id}` - 获取指南详情
- `GET /api/v1/tasks/{task_id}/stream` - 任务进度流(SSE)
- `GET /api/v1/tasks/{task_id}` - 获取任务状态

详细API文档请访问: http://localhost:8000/docs

## 配置说明

### 环境变量配置

#### 后端配置 (backend/.env)

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cpg2pvg

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# AI模型
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
```

#### 前端配置 (frontend/.env)

```env
# API地址
NEXT_PUBLIC_API_URL=http://localhost:8000

# 应用配置
NEXT_PUBLIC_APP_NAME=CPG2PVG-AI
```

## 开发指南

### 项目结构

```
cpg2pvg-ai/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── api/            # API路由
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
├── frontend/               # Next.js前端
│   ├── app/                # App Router
│   ├── components/         # 组件
│   ├── lib/                # 工具库
│   ├── stores/             # 状态管理
│   └── types/              # TypeScript类型
├── celery_worker/          # Celery任务处理
│   ├── tasks/              # 任务定义
│   ├── workflows/          # 工作流处理
│   └── utils/              # 工具函数
├── docker/                 # Docker配置
├── docs/                   # 项目文档
└── scripts/                # 部署脚本
```

### 代码规范

- **Python**: 遵循PEP 8，使用Black格式化，isort排序
- **TypeScript**: 遵循ESLint规则，使用Prettier格式化
- **Git**: 使用Conventional Commits规范

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 部署

### 生产环境部署

1. **配置生产环境变量**
2. **使用生产配置启动**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
3. **配置Nginx反向代理**
4. **设置SSL证书**
5. **配置监控告警**

### Kubernetes部署

```bash
# 应用Kubernetes配置
kubectl apply -f k8s/
```

## 监控

### 健康检查

- 后端: `GET /health`
- 数据库: PostgreSQL连接检查
- Redis: `ping`命令
- Celery: Flower监控界面

### 性能监控

- **Prometheus**: 指标收集
- **Grafana**: 可视化面板
- **Sentry**: 错误追踪
- **日志聚合**: ELK Stack

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认网络连通性

2. **Celery任务不执行**
   - 检查Redis连接
   - 验证Worker状态
   - 查看任务日志

3. **文件上传失败**
   - 检查MinIO服务
   - 验证存储配置
   - 确认文件大小限制

### 日志查看

```bash
# 查看各服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系我们

- 项目主页: https://github.com/cpg2pvg/cpg2pvg-ai
- 问题反馈: https://github.com/cpg2pvg/cpg2pvg-ai/issues
- 邮箱: team@cpg2pvg.ai

## 致谢

感谢所有为CPG2PVG-AI项目做出贡献的开发者和研究人员。