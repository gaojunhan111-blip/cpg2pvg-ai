# CPG2PVG-AI Backend System

CPG2PVG-AI (Clinical Practice Guidelines to Patient Versioned Guidelines using AI) 是一个智能系统，用于将临床医学指南转化为公众可理解的患者版本指南。

## [BUILD] 系统架构

### 核心组件
- **FastAPI**: 高性能异步Web框架
- **PostgreSQL**: 主数据库，使用SQLAlchemy 2.0 ORM
- **Redis**: 缓存和会话存储
- **Celery**: 分布式任务队列
- **MinIO**: 对象存储服务
- **Docker**: 容器化部署

### 工作流架构
- **Slow工作流**: 9节点渐进式处理架构
  1. 知识图谱语义理解
  2. 分层智能体系统
  3. 渐进式内容生成
  4. 智能缓存和记忆系统
  5. 成本优化策略
  6. 质量控制验证系统
  7. 性能监控和自适应调整

### AI/LLM集成
- **OpenAI**: GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 (Sonnet, Haiku, Opus)
- **Azure OpenAI**: 企业级AI服务
- **本地模型**: 支持私有部署

## [START] 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (可选)

### 1. 克隆项目
```bash
git clone <repository-url>
cd cpg2pvg-ai/backend
```

### 2. 设置环境变量
创建 `.env` 文件：
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://cpg2pvg_user:password@localhost:5432/cpg2pvg

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-super-secret-key-change-in-production-environment

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=cpg2pvg-docs

# LLM配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# 环境配置
ENVIRONMENT=development
DEBUG=true
```

### 3. 自动化设置
运行完整系统设置脚本：
```bash
python scripts/setup_complete_system.py
```

或分步骤设置：
```bash
# 设置数据库
python scripts/setup_database.py

# 设置文件存储
python scripts/setup_file_storage.py

# 设置LLM提供商
python scripts/setup_llm_providers.py

# 设置安全系统
python scripts/setup_security.py

# 设置日志系统
python scripts/setup_logging.py
```

### 4. 启动服务

#### 使用Docker Compose（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 手动启动
```bash
# 启动主应用
python -m app.main

# 启动Celery Worker
celery -A app.core.celery worker --loglevel=info

# 启动Celery Beat（定时任务）
celery -A app.core.celery beat --loglevel=info

# 启动Flower（Celery监控）
celery -A app.core.celery flower
```

## [LIST] API文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## [HEALTH] 主要功能

### 1. 用户管理
- 用户注册和登录
- JWT身份认证
- API密钥管理
- 角色权限控制

### 2. 指南管理
- 指南文件上传（PDF、DOCX等）
- 指南内容解析和处理
- 多版本管理
- 元数据管理

### 3. 工作流处理
- Slow工作流处理
- 任务状态跟踪
- 进度监控
- 结果质量控制

### 4. LLM集成
- 多提供商支持
- 模型选择和配置
- 成本监控和优化
- 请求限流

### 5. 文件存储
- MinIO对象存储
- 文件上传下载
- 预签名URL
- 存储配额管理

## [CONFIG] 配置说明

### 应用配置
主要配置在 `app/core/config.py` 中：

```python
# 基础配置
PROJECT_NAME = "CPG2PVG-AI"
VERSION = "0.1.0"
DEBUG = False

# 数据库配置
DATABASE_URL = "postgresql+asyncpg://..."
DATABASE_POOL_SIZE = 10

# Redis配置
REDIS_URL = "redis://localhost:6379/0"

# 安全配置
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7天

# LLM配置
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"
HIGH_QUALITY_MODEL = "gpt-4"
MAX_TOKENS_PER_REQUEST = 4000
```

### 日志配置
支持结构化日志和JSON格式：
```python
# 日志级别
LOG_LEVEL = "INFO"

# 日志文件
LOG_FILE_PATH = "/var/log/cpg2pvg/app.log"

# JSON格式
LOG_JSON_FORMAT = True

# 结构化日志
LOG_STRUCTURED = True
```

## [SECURITY] 安全特性

### 身份认证
- JWT访问令牌
- 刷新令牌机制
- API密钥认证
- 多因素认证支持

### 权限控制
- 基于角色的访问控制（RBAC）
- 资源级权限管理
- API限流
- CORS配置

### 安全头
- HSTS
- CSP
- XSS保护
- 点击劫持防护

## [METRICS] 监控和日志

### 性能监控
- Prometheus指标
- 响应时间监控
- 资源使用监控
- 错误率追踪

### 日志系统
- 结构化日志
- 多级别日志
- 日志轮转
- 集中化日志收集

### 审计日志
- 用户操作记录
- API访问日志
- 安全事件日志
- 合规性审计

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py

# 生成覆盖率报告
pytest --cov=app tests/

# 运行性能测试
pytest tests/performance/
```

### 测试类型
- 单元测试
- 集成测试
- API测试
- 性能测试

## [PACKAGE] 部署

### 生产环境要求
- Docker 20.10+
- Kubernetes 1.20+
- Helm 3.0+
- 监控系统（Prometheus + Grafana）

### 部署方式
1. **Docker部署**：推荐用于单机部署
2. **Kubernetes部署**：推荐用于生产环境
3. **云服务部署**：支持AWS、Azure、GCP

### 环境变量
生产环境必须配置的安全变量：
- `SECRET_KEY`: 强随机密钥
- `DATABASE_URL`: 生产数据库URL
- `REDIS_URL`: Redis连接URL
- `ENVIRONMENT=production`

## 🛠️ 开发

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 代码规范
- Black：代码格式化
- isort：导入排序
- flake8：代码检查
- mypy：类型检查

### 数据库迁移
```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📚 文档

详细文档：
- [API文档](docs/api.md)
- [架构文档](docs/architecture.md)
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)

## 🤝 贡献

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)

## 🆘 支持

- **问题报告**：[GitHub Issues](https://github.com/your-org/cpg2pvg-ai/issues)
- **功能请求**：[GitHub Discussions](https://github.com/your-org/cpg2pvg-ai/discussions)
- **安全问题**：security@your-org.com

## 🏆 致谢

感谢所有为这个项目做出贡献的开发者和研究人员。

---

**CPG2PVG-AI** - 让医学指南更易理解，让患者更好地管理健康。