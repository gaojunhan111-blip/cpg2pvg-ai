# CPG2PVG-AI 系统部署指南

## 系统概述

CPG2PVG-AI是一个完整的医学指南转化系统，包含：
- Slow工作流编排器（9个处理节点）
- Celery异步任务队列
- FastAPI REST API
- 用户认证和授权
- 实时进度推送
- 文件管理和存储
- 完整的错误处理和重试机制

## 系统架构

```
Frontend (Web UI)
       ↓
FastAPI Application
       ↓
    Celery Queue
       ↓
Redis (Message Broker + Cache)
       ↓
PostgreSQL (Database)
       ↓
File Storage
```

## 部署要求

### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+) 或 Windows 10+
- **Python**: 3.9+
- **内存**: 最低8GB，推荐16GB+
- **存储**: 最低50GB，推荐100GB+
- **CPU**: 最低4核，推荐8核+

### 依赖服务
- **PostgreSQL**: 12+
- **Redis**: 6+
- **Nginx** (可选，用于反向代理)

## 安装步骤

### 1. 环境准备

```bash
# 克隆代码
git clone <repository-url>
cd cpg2pvg-ai/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/cpg2pvg_ai
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# 文件存储配置
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
TEMP_DIR=./temp
BACKUP_DIR=./backups
MAX_FILE_SIZE=104857600  # 100MB

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 外部服务配置
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 3. 数据库初始化

```bash
# 创建数据库
createdb cpg2pvg_ai

# 运行数据库迁移
alembic upgrade head

# 创建初始用户（可选）
python scripts/create_initial_user.py
```

### 4. 启动服务

#### 方式1：直接启动（开发环境）

```bash
# 启动FastAPI应用
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动Celery Worker（新终端）
celery -A app.core.celery_app.celery_app worker --loglevel=info

# 启动Celery Beat（调度器，新终端）
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

#### 方式2：使用Docker（推荐生产环境）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/cpg2pvg_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=cpg2pvg_ai
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A app.core.celery_app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/cpg2pvg_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs

  beat:
    build: .
    command: celery -A app.core.celery_app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/cpg2pvg_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

启动Docker：

```bash
docker-compose up -d
```

#### 方式3：使用Supervisor（生产环境）

创建 `supervisor.conf`：

```ini
[program:cpg2pvg_api]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/path/to/cpg2pvg-ai/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cpg2pvg/api.log

[program:cpg2pvg_worker]
command=celery -A app.core.celery_app.celery_app worker --loglevel=info
directory=/path/to/cpg2pvg-ai/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cpg2pvg/worker.log

[program:cpg2pvg_beat]
command=celery -A app.core.celery_app.celery_app beat --loglevel=info
directory=/path/to/cpg2pvg-ai/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/cpg2pvg/beat.log
```

启动Supervisor：

```bash
supervisorctl start all
```

## API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新Token
- `GET /api/v1/auth/me` - 获取当前用户信息

### 工作流相关
- `POST /api/v1/workflow/upload` - 上传并处理指南（Slow工作流）
- `GET /api/v1/workflow/{task_id}/status` - 获取工作流状态
- `GET /api/v1/workflow/{task_id}/stream` - 实时进度推送
- `GET /api/v1/workflow/{guideline_id}/pvg/download` - 下载PVG文档
- `POST /api/v1/workflow/batch` - 批量处理
- `DELETE /api/v1/workflow/{task_id}` - 取消工作流

### 文件管理
- `GET /api/v1/files/download/{path}` - 下载文件
- `GET /api/v1/files/stats` - 存储统计

### 系统监控
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/stats` - 系统统计

## 配置说明

### 工作流配置

工作流可以通过以下参数配置：

```python
# 处理模式
processing_mode: "slow" | "fast" | "thorough"

# 功能开关
enable_visualization: bool
enable_caching: bool
enable_cost_optimization: bool
enable_quality_control: bool

# 性能配置
max_concurrent_nodes: int = 5
timeout_per_node: int = 600  # 10分钟
total_timeout: int = 7200    # 2小时
```

### 重试配置

系统内置了智能重试机制：

```python
# 工作流重试配置
WORKFLOW_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=120.0,
    backoff_factor=1.5,
    jitter=True
)
```

## 监控和日志

### 日志文件
- `app.log` - 应用主日志
- `celery.log` - Celery任务日志
- `access.log` - API访问日志

### 监控指标
- 任务执行时间
- 成功/失败率
- 系统资源使用
- API响应时间

### 告警配置
系统支持多种告警方式：
- 邮件告警
- 日志记录
- 外部监控系统集成

## 性能优化

### 数据库优化
- 为常用查询字段添加索引
- 定期清理过期数据
- 使用连接池

### 缓存策略
- Redis缓存任务状态
- 内存缓存文件元数据
- 分层缓存提升响应速度

### 异步处理
- 使用Celery处理耗时任务
- 并发控制避免资源过载
- 智能重试提高成功率

## 故障排除

### 常见问题

1. **任务卡住不动**
   - 检查Celery worker状态
   - 查看Redis连接
   - 检查任务队列

2. **文件上传失败**
   - 检查存储空间
   - 验证文件权限
   - 确认文件类型支持

3. **数据库连接错误**
   - 检查数据库服务状态
   - 验证连接配置
   - 检查网络连接

4. **内存使用过高**
   - 调整并发数量
   - 优化数据处理逻辑
   - 增加系统内存

### 调试模式

启用调试模式获取详细日志：

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 安全考虑

1. **API安全**
   - JWT Token认证
   - 角色权限控制
   - 请求频率限制

2. **文件安全**
   - 文件类型验证
   - 大小限制
   - 路径遍历防护

3. **数据安全**
   - 数据库连接加密
   - 敏感信息脱敏
   - 定期数据备份

## 备份策略

1. **数据库备份**
   - 每日全量备份
   - 增量备份
   - 异地备份存储

2. **文件备份**
   - 自动备份重要文件
   - 版本控制
   - 定期清理旧备份

## 扩展性

系统设计支持水平扩展：

1. **API服务扩展**
   - 负载均衡
   - 多实例部署

2. **任务队列扩展**
   - 多Worker节点
   - 队列分片

3. **存储扩展**
   - 分布式文件存储
   - CDN加速

## 维护建议

1. **定期维护**
   - 清理临时文件
   - 优化数据库
   - 更新依赖

2. **监控告警**
   - 系统健康监控
   - 性能指标监控
   - 异常告警

3. **安全审计**
   - 定期安全检查
   - 日志审计
   - 权限审查