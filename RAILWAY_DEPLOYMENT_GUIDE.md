# 🚀 Railway后端部署指南

## 📋 部署准备状态

✅ **后端代码已准备** - FastAPI应用已配置
✅ **Docker配置已完成** - Dockerfile和railway.json已就绪
✅ **依赖已优化** - requirements.cloud.txt已创建
✅ **GitHub仓库已同步** - 最新代码已推送

## 🎯 立即部署步骤

### 第一步：访问Railway (2分钟)

1. **打开Railway官网**: [https://railway.app](https://railway.app)
2. **点击登录** → 选择 **Continue with GitHub**
3. **授权GitHub访问** → 选择你的GitHub账号
4. **进入控制台** → 点击 **New Project**

### 第二步：导入项目 (3分钟)

1. **选择部署方式**:
   - 点击 **Deploy from GitHub repo**
   - 在仓库列表中找到 `cpg2pvg-ai`
   - 选择分支: `main`

2. **配置服务**:
   - Service Name: `cpg2pvg-backend`
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 第三步：添加PostgreSQL数据库 (5分钟)

1. **在项目中添加服务**:
   - 点击 **+ New Service**
   - 选择 **Database**
   - 选择 **PostgreSQL**
   - 保持默认配置

2. **等待数据库创建**:
   - Railway会自动创建PostgreSQL实例
   - 获取数据库连接字符串

### 第四步：配置环境变量 (5分钟)

在后端服务的Environment Variables中添加：

```env
# 数据库配置 (从PostgreSQL服务获取)
DATABASE_URL=postgresql://user:password@host:5432/database

# 安全配置
SECRET_KEY=your-secure-secret-key-here-min-32-chars
ENVIRONMENT=production

# OpenAI配置 (可选)
OPENAI_API_KEY=your-openai-api-key

# Redis配置 (可选，稍后配置)
REDIS_URL=redis://user:password@host:port

# CORS配置
ALLOWED_ORIGINS=https://your-frontend-url.vercel.app
```

**重要**:
- `DATABASE_URL` 从PostgreSQL服务页面复制
- `SECRET_KEY` 生成一个安全的密钥
- `ALLOWED_ORIGINS` 先留空，前端部署后更新

### 第五步：开始部署 (2分钟)

1. **确认配置** → 检查所有设置
2. **点击Deploy** → 开始自动部署
3. **监控日志** → 观察构建和启动过程

## 📊 部署配置详情

### Railway配置文件
```
backend/railway.json
```

### Docker配置
```
backend/Dockerfile.railway
```

### Python依赖
```
backend/requirements.cloud.txt
```

### 健康检查
- 端点: `/health`
- 方法: GET
- 响应: `{"status": "healthy"}`

## 🎉 部署成功标志

部署成功后你会看到：

```
✅ Build completed successfully
✅ Service is running
🌐 URL: https://cpg2pvg-backend.up.railway.app
📚 API文档: https://cpg2pvg-backend.up.railway.app/docs
```

## 📱 验证部署

### 1. 健康检查
访问: `https://your-backend-url.up.railway.app/health`
预期响应:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. API文档检查
访问: `https://your-backend-url.up.railway.app/docs`
确认Swagger UI正常显示

### 3. 数据库连接测试
```bash
curl https://your-backend-url.up.railway.app/api/v1/health
```

## 🔄 数据库初始化

### 方法1: Railway控制台 (推荐)
1. 打开PostgreSQL服务
2. 点击 **Connect** 标签
3. 复制连接字符串
4. 使用任何PostgreSQL客户端连接
5. 执行 `scripts/cloud-deployment.sql`

### 方法2: Railway CLI
```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录Railway
railway login

# 连接到数据库
railway variables

# 执行SQL脚本
psql $DATABASE_URL -f scripts/cloud-deployment.sql
```

## 🔧 关键配置文件

### railway.json
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Dockerfile.railway
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.cloud.txt .
RUN pip install --no-cache-dir -r requirements.cloud.txt

COPY . .

EXPOSE $PORT

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

## 🆘 常见问题解决

### 问题1: 构建失败
**解决方案**:
- 检查requirements.cloud.txt中的依赖
- 确认Python版本兼容性
- 查看构建日志中的错误信息

### 问题2: 数据库连接失败
**解决方案**:
- 确认DATABASE_URL格式正确
- 检查数据库服务是否正在运行
- 验证数据库用户权限

### 问题3: API无法访问
**解决方案**:
- 检查健康检查端点
- 确认端口配置正确
- 查看应用日志中的错误

### 问题4: 环境变量未生效
**解决方案**:
- 重新部署服务
- 检查变量名称拼写
- 确认变量值格式正确

## 📊 成本预估

### PostgreSQL数据库
- **免费套餐**: 512MB存储，500小时/月
- **付费套餐**: $5/月起

### 后端服务
- **免费套餐**: 500小时/月，$5使用额度
- **付费套餐**: 按使用量计费

**预计月度成本**: $0-20 (免费额度内)

## 📈 监控和维护

### 日志查看
- Railway控制台 → Logs标签
- 实时查看应用日志
- 过滤错误和警告信息

### 性能监控
- 控制台 → Metrics标签
- CPU、内存、网络使用情况
- 数据库连接数和查询性能

### 自动重启
- 配置restartPolicyType: "ON_FAILURE"
- 应用崩溃时自动重启
- 健康检查失败时自动恢复

## 📞 技术支持

- **Railway文档**: [https://docs.railway.app](https://docs.railway.app)
- **FastAPI部署**: [https://fastapi.tiangolo.com/deployment](https://fastapi.tiangolo.com/deployment)
- **PostgreSQL帮助**: [https://www.postgresql.org/docs](https://www.postgresql.org/docs)

---

## 🚀 准备开始部署！

**点击这里开始部署**: [https://railway.app/new](https://railway.app/new)

**预计总时间**: 15-20分钟
**部署难度**: ⭐⭐⭐☆☆ (中等)

后端部署完成后，继续进行数据库初始化！ 🎯