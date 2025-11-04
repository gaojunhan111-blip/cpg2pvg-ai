# CPG2PVG-AI 云部署完整指南

## 🌟 部署架构概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel        │    │   Railway       │    │   Supabase      │
│   (前端)         │    │   (后端API)      │    │   (数据库)       │
│   Next.js       │◄──►│   FastAPI       │◄──►│   PostgreSQL    │
│   静态托管        │    │   容器化部署      │    │   实时数据库       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cloud   │
                       │   (缓存/队列)     │
                       │   内存缓存        │
                       └─────────────────┘
```

## 📋 部署清单

### ✅ 前端部署 - Vercel (推荐)

**优势:**
- 🚀 零配置部署
- 🌍 全球CDN加速
- 🔄 自动HTTPS
- 📊 内置分析工具
- 💰 免费额度充足

**部署步骤:**
1. 连接GitHub仓库到Vercel
2. 配置环境变量
3. 自动部署完成

### ✅ 后端部署 - Railway (推荐)

**优势:**
- 🐳 Docker容器支持
- 🚀 快速部署
- 📊 监控面板
- 💰 按使用付费
- 🔄 自动扩展

**替代方案:**
- Render.com
- Fly.io
- Heroku (付费)

### ✅ 数据库服务 - Supabase (推荐)

**优势:**
- 🆓 免费套餐
- 🔄 实时同步
- 🔐 内置认证
- 📊 RESTful API
- 🌍 全球边缘网络

**替代方案:**
- PlanetScale (MySQL)
- Neon (PostgreSQL)
- Railway (PostgreSQL)

### ✅ 缓存服务 - Redis Cloud

**优势:**
- ⚡ 毫秒级响应
- 🔧 管理控制台
- 📊 监控指标
- 🛡️ 高可用性

## 🛠️ 详细部署配置

### 1. 前端 Vercel 配置

#### package.json 脚本
```json
{
  "scripts": {
    "vercel-build": "npm run build",
    "build": "next build",
    "start": "next start"
  }
}
```

#### vercel.json 配置
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["hkg1", "sin1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url",
    "NEXT_PUBLIC_ENVIRONMENT": "production"
  }
}
```

#### 环境变量设置
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_VERSION=1.0.0
```

### 2. 后端 Railway 配置

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### railway.json 配置
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

#### 环境变量设置
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:6379
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
ENVIRONMENT=production
```

### 3. 数据库 Supabase 配置

#### 数据库表结构
```sql
-- 指南表
CREATE TABLE guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    file_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guideline_id UUID REFERENCES guidelines(id),
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 部署执行步骤

### 第一步：准备代码仓库

1. **推送代码到GitHub**
```bash
git add .
git commit -m "Ready for cloud deployment"
git push origin main
```

### 第二步：部署前端到Vercel

1. **访问 [vercel.com](https://vercel.com)**
2. **使用GitHub登录**
3. **导入项目仓库**
4. **配置框架：Next.js**
5. **设置环境变量**
6. **点击Deploy**

### 第三步：部署后端到Railway

1. **访问 [railway.app](https://railway.app)**
2. **使用GitHub登录**
3. **新建项目**
4. **选择数据库服务**
5. **配置后端服务**
6. **设置环境变量**
7. **点击Deploy**

### 第四步：配置数据库

1. **在Supabase创建项目**
2. **获取数据库连接字符串**
3. **运行数据库迁移**
4. **设置Row Level Security**

### 第五步：配置Redis

1. **注册Redis Cloud**
2. **创建免费数据库**
3. **获取连接字符串**
4. **更新后端环境变量**

## 📊 成本估算 (月度)

| 服务 | 免费额度 | 预估费用 |
|------|---------|---------|
| Vercel | 100GB带宽 | $0-20 |
| Railway | 500小时 | $0-25 |
| Supabase | 500MB数据 | $0-25 |
| Redis Cloud | 30MB内存 | $0-7 |
| **总计** | | **$0-77/月** |

## 🔧 监控和维护

### 日志监控
- **Vercel**: 内置函数日志
- **Railway**: 实时日志查看器
- **Supabase**: 数据库查询日志
- **Redis**: 性能监控面板

### 备份策略
- **数据库**: Supabase自动备份
- **代码**: Git版本控制
- **配置**: 环境变量管理

### 性能优化
- **前端**: Vercel Edge Network
- **后端**: Railway自动扩展
- **数据库**: 连接池优化
- **缓存**: Redis缓存策略

## 🎯 部署后验证清单

### 前端验证
- [ ] 页面正常加载
- [ ] 路由导航正常
- [ ] API连接成功
- [ ] 移动端适配
- [ ] 性能指标达标

### 后端验证
- [ ] API响应正常
- [ ] 数据库连接成功
- [ ] 缓存服务正常
- [ ] 文件上传功能
- [ ] 错误处理机制

### 集成验证
- [ ] 前后端通信正常
- [ ] 用户注册登录
- [ ] 文件上传处理
- [ ] 任务状态更新
- [ ] 实时通知功能

## 🆘 故障排除

### 常见问题
1. **CORS错误**: 配置正确的允许域名
2. **数据库连接失败**: 检查连接字符串
3. **环境变量未生效**: 重新部署服务
4. **内存不足**: 升级服务套餐

### 联系支持
- **Vercel**: support@vercel.com
- **Railway**: support@railway.app
- **Supabase**: support@supabase.io

---

**🎉 按照此指南，你可以在2小时内完成整个系统的云部署！**