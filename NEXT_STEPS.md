# 🚀 CPG2PVG-AI 云部署下一步操作指南

## 🎯 当前状态

✅ **部署准备已完成** - 所有配置文件和脚本已生成
✅ **Git仓库已就绪** - 代码已提交到本地仓库
✅ **云部署配置完成** - Vercel、Railway、Supabase配置已就绪

## 📋 立即执行步骤

### 第一步：创建GitHub仓库 (5分钟)

1. **访问GitHub**: [https://github.com](https://github.com)
2. **创建新仓库**:
   - 点击右上角 "+" → "New repository"
   - 仓库名称: `cpg2pvg-ai`
   - 描述: `CPG2PVG-AI - 临床医学指南转化为公众医学指南的智能系统`
   - 设为Public或Private (根据你的需要)
   - **不要**勾选 "Initialize this repository with README"
3. **创建仓库后，复制仓库地址**

### 第二步：连接Git到GitHub (2分钟)

在项目目录中执行以下命令：

```bash
# 替换YOUR_USERNAME为你的GitHub用户名
git remote add origin https://github.com/YOUR_USERNAME/cpg2pvg-ai.git

# 推送代码到GitHub
git push -u origin main
```

### 第三步：部署前端到Vercel (10分钟)

1. **访问Vercel**: [https://vercel.com](https://vercel.com)
2. **使用GitHub登录**
3. **导入项目**:
   - 点击 "New Project"
   - 选择 "Import Git Repository"
   - 选择你的 `cpg2pvg-ai` 仓库
   - 点击 "Import"
4. **配置项目**:
   - Framework: Next.js (自动检测)
   - Build Settings: 保持默认
5. **添加环境变量**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   NEXT_PUBLIC_ENVIRONMENT=production
   NEXT_PUBLIC_VERSION=1.0.0
   ```
6. **点击Deploy** - 等待部署完成

### 第四步：部署后端到Railway (15分钟)

1. **访问Railway**: [https://railway.app](https://railway.app)
2. **使用GitHub登录**
3. **创建新项目**:
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的 `cpg2pvg-ai` 仓库
   - 选择分支: `main`
4. **添加数据库服务**:
   - 点击 "Add Service"
   - 选择 "PostgreSQL"
   - 保持默认配置
5. **配置后端服务**:
   - Service名称: `backend-api`
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **添加环境变量**:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/database
   SECRET_KEY=your-secure-secret-key-here
   OPENAI_API_KEY=your-openai-api-key
   ENVIRONMENT=production
   ```
   **注意**: DATABASE_URL将在PostgreSQL服务创建后显示
7. **点击Deploy** - 等待部署完成

### 第五步：数据库初始化 (10分钟)

1. **在Railway中**:
   - 点击PostgreSQL服务
   - 选择 "Connect" 标签
   - 复制连接字符串
2. **运行数据库脚本**:
   - 使用任何PostgreSQL客户端
   - 连接到数据库
   - 执行 `scripts/cloud-deployment.sql` 脚本

### 第六步：配置Redis缓存 (可选，5分钟)

1. **注册Redis Cloud**: [https://redis.com/try-free](https://redis.com/try-free)
2. **创建免费数据库**
3. **获取连接字符串**
4. **在Railway后端添加环境变量**:
   ```env
   REDIS_URL=redis://user:password@host:port
   ```

## 🔧 配置详情

### 前端Vercel环境变量
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_VERSION=1.0.0
```

### 后端Railway环境变量
```env
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=your-secure-secret-key-here
OPENAI_API_KEY=your-openai-api-key
ENVIRONMENT=production
REDIS_URL=redis://user:password@host:port  # 可选
```

### 重要配置文件位置
- **前端配置**: `frontend/vercel.json`
- **后端配置**: `backend/railway.json`
- **数据库脚本**: `scripts/cloud-deployment.sql`
- **部署脚本**: `deploy.sh`

## 🎯 部署后验证

### 验证清单
- [ ] 前端页面可以正常访问
- [ ] 后端API健康检查通过
- [ ] 数据库连接正常
- [ ] 可以查看API文档
- [ ] 文件上传功能正常

### 访问地址
- **前端**: `https://your-app-name.vercel.app`
- **后端API**: `https://your-backend.railway.app`
- **API文档**: `https://your-backend.railway.app/docs`

## 🆘 常见问题解决

### 问题1: Vercel部署失败
**解决方案**: 检查package.json和next.config.js配置

### 问题2: Railway后端无法启动
**解决方案**: 检查环境变量配置，特别是DATABASE_URL

### 问题3: 数据库连接失败
**解决方案**: 确认数据库连接字符串格式正确

### 问题4: CORS错误
**解决方案**: 在后端配置中添加前端域名到CORS允许列表

## 📞 获取帮助

如果遇到问题，可以：
1. 查看部署日志
2. 检查环境变量配置
3. 参考详细文档：`CLOUD_DEPLOYMENT_GUIDE.md`
4. 联系云平台支持团队

## 🎉 部署成功标志

当你能够：
- ✅ 访问前端页面看到CPG2PVG-AI界面
- ✅ 访问 `/docs` 查看API文档
- ✅ 上传文件并看到处理状态更新
- ✅ 查看处理后的PVG结果

**恭喜！你的CPG2PVG-AI系统已经成功上线！** 🚀

---

**预计总时间**: 45-60分钟
**预计成本**: 免费额度内零成本，超出后$0-77/月

**立即开始部署，让你的医学指南转化系统上线运行！**