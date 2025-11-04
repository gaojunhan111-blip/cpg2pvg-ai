#!/bin/bash

# CPG2PVG-AI 云部署自动化脚本
# 使用方法: ./deploy.sh

set -e

echo "🚀 CPG2PVG-AI 云部署开始..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的工具
check_requirements() {
    log_info "检查部署要求..."

    if ! command -v git &> /dev/null; then
        log_error "Git 未安装，请先安装 Git"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi

    log_success "部署要求检查完成"
}

# 准备代码仓库
prepare_repository() {
    log_info "准备代码仓库..."

    # 检查是否在git仓库中
    if [ ! -d ".git" ]; then
        log_info "初始化Git仓库..."
        git init
        git add .
        git commit -m "Initial commit: CPG2PVG-AI project"
    fi

    # 检查是否有远程仓库
    if ! git remote get-url origin &> /dev/null; then
        log_warning "未找到远程仓库，请手动创建GitHub仓库并添加远程地址"
        echo "请执行以下命令："
        echo "1. 在GitHub创建新仓库 'cpg2pvg-ai'"
        echo "2. 运行: git remote add origin https://github.com/YOUR_USERNAME/cpg2pvg-ai.git"
        echo "3. 运行: git push -u origin main"
        read -p "按回车键继续..."
    else
        log_info "推送代码到远程仓库..."
        git add .
        git commit -m "Prepare for cloud deployment"
        git push origin main
    fi

    log_success "代码仓库准备完成"
}

# 准备前端部署
prepare_frontend() {
    log_info "准备前端部署..."

    cd frontend

    # 安装依赖
    log_info "安装前端依赖..."
    npm install

    # 构建测试
    log_info "测试前端构建..."
    npm run build || log_warning "前端构建失败，但将继续部署"

    cd ..
    log_success "前端部署准备完成"
}

# 准备后端部署
prepare_backend() {
    log_info "准备后端部署..."

    cd backend

    # 创建简化的requirements文件用于云部署
    log_info "创建云部署requirements文件..."
    cat > requirements.cloud.txt << EOF
# Core web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1

# Redis and caching
redis==5.0.1

# Celery task queue
celery==5.3.4

# Authentication and security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
PyJWT==2.8.0

# Configuration
pydantic==2.5.0
pydantic-settings==2.1.0

# File processing
PyPDF2==3.0.1
python-docx==1.1.0

# AI/ML integration
openai==1.3.7
tiktoken==0.5.2

# HTTP client
httpx==0.25.2

# Utilities
python-dotenv==1.0.0
tenacity==8.2.3
EOF

    cd ..
    log_success "后端部署准备完成"
}

# 生成部署指南
generate_deployment_guide() {
    log_info "生成部署指南..."

    cat > DEPLOYMENT_INSTRUCTIONS.md << EOF
# CPG2PVG-AI 云部署说明

## 🌟 部署概览

项目已准备完成，现在可以按照以下步骤进行云部署：

## 📋 部署清单

### ✅ 1. 前端部署 (Vercel)
1. 访问 [vercel.com](https://vercel.com)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择 'cpg2pvg-ai' 仓库
5. 配置框架：Next.js
6. 设置环境变量：
   - NEXT_PUBLIC_API_URL: https://your-backend-url.railway.app
   - NEXT_PUBLIC_ENVIRONMENT: production
7. 点击 "Deploy"

### ✅ 2. 后端部署 (Railway)
1. 访问 [railway.app](https://railway.app)
2. 使用GitHub账号登录
3. 点击 "New Project" -> "Deploy from GitHub repo"
4. 选择 'cpg2pvg-ai' 仓库
5. 添加PostgreSQL数据库服务
6. 配置环境变量：
   - DATABASE_URL: (从Railway数据库获取)
   - SECRET_KEY: your-secret-key-here
   - OPENAI_API_KEY: your-openai-api-key
   - ENVIRONMENT: production
7. 点击 "Deploy"

### ✅ 3. 数据库初始化
1. 在Railway数据库中运行以下脚本：
   - 文件位置: \`scripts/cloud-deployment.sql\`
2. 或连接到数据库执行初始化

### ✅ 4. 配置Redis (可选)
1. 注册 [Redis Cloud](https://redis.com/try-free)
2. 创建免费数据库
3. 获取连接字符串
4. 在Railway后端添加环境变量：
   - REDIS_URL: your-redis-connection-string

## 🔗 重要链接

部署完成后，你将获得：
- 前端地址: https://your-app.vercel.app
- 后端API: https://your-backend.railway.app
- API文档: https://your-backend.railway.app/docs
- 数据库管理: Railway控制台

## 🎯 验证部署

1. 访问前端地址，确认页面正常加载
2. 访问API文档，确认后端正常
3. 测试文件上传功能
4. 检查数据库连接

## 🆘 故障排除

如遇问题：
1. 检查环境变量配置
2. 查看部署日志
3. 确认数据库连接
4. 验证API密钥

详细故障排除指南请参考 \`CLOUD_DEPLOYMENT_GUIDE.md\`
EOF

    log_success "部署指南已生成"
}

# 主函数
main() {
    echo "🌟 CPG2PVG-AI 云部署自动化脚本"
    echo "================================="

    check_requirements
    prepare_repository
    prepare_frontend
    prepare_backend
    generate_deployment_guide

    echo ""
    log_success "🎉 云部署准备完成！"
    echo ""
    echo "📋 下一步操作："
    echo "1. 查看生成的 DEPLOYMENT_INSTRUCTIONS.md"
    echo "2. 按照指南在Vercel和Railway上部署"
    echo "3. 配置环境变量和数据库"
    echo "4. 验证部署是否成功"
    echo ""
    echo "📚 详细文档："
    echo "- CLOUD_DEPLOYMENT_GUIDE.md (完整部署指南)"
    echo "- DEPLOYMENT_INSTRUCTIONS.md (快速部署说明)"
    echo ""
}

# 运行主函数
main "$@"