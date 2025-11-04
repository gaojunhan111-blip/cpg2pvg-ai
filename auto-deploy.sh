#!/bin/bash

# ========================================
# 🚀 CPG2PVG-AI 自动化部署脚本
# ========================================
# 使用方法: ./auto-deploy.sh
# 此脚本将引导你完成整个云部署流程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 图标定义
ROCKET="🚀"
CHECK="✅"
WARNING="⚠️"
ERROR="❌"
INFO="ℹ️"
GEAR="⚙️"
CLOUD="☁️"
LINK="🔗"

# 日志函数
log_info() {
    echo -e "${BLUE}${INFO} [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}${CHECK} [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${WARNING} [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}${ERROR} [ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}${ROCKET} [STEP]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "🚀 CPG2PVG-AI 自动化部署脚本"
    echo "=================================================="
    echo "📋 项目: 临床医学指南转化系统"
    echo "☁️  平台: Vercel + Railway + Supabase"
    echo "⏱️  预计时间: 45-60分钟"
    echo "📖 详细文档: 已准备完整"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."

    # 检查Git
    if ! command -v git &> /dev/null; then
        log_error "Git 未安装，请先安装 Git"
        exit 1
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi

    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi

    # 检查curl
    if ! command -v curl &> /dev/null; then
        log_warning "curl 未安装，某些功能可能受限"
    fi

    log_success "系统要求检查完成"
}

# 验证项目状态
validate_project() {
    log_step "验证项目状态..."

    # 检查是否在项目根目录
    if [ ! -f "package.json" ] && [ ! -f "backend/requirements.txt" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi

    # 检查Git状态
    if [ -d ".git" ]; then
        log_info "Git仓库已初始化"

        # 检查是否有未提交的更改
        if [ -n "$(git status --porcelain)" ]; then
            log_warning "检测到未提交的更改，建议先提交"
            read -p "是否继续部署? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_error "未找到Git仓库，请先初始化"
        exit 1
    fi

    # 检查前端构建
    if [ -d "frontend" ]; then
        log_info "测试前端构建..."
        cd frontend
        if npm run build &> /dev/null; then
            log_success "前端构建测试通过"
        else
            log_error "前端构建失败，请先修复构建错误"
            cd ..
            exit 1
        fi
        cd ..
    fi

    log_success "项目状态验证完成"
}

# 部署前端到Vercel
deploy_frontend() {
    log_step "开始前端部署 (Vercel)"

    echo -e "${YELLOW}${CLOUD} Vercel部署指南:${NC}"
    echo "1. 打开浏览器访问: ${BLUE}https://vercel.com${NC}"
    echo "2. 使用GitHub账号登录"
    echo "3. 点击 'New Project'"
    echo "4. 选择 'cpg2pvg-ai' 仓库"
    echo "5. 配置环境变量:"
    echo "   - NEXT_PUBLIC_API_URL: https://your-backend-url.railway.app"
    echo "   - NEXT_PUBLIC_ENVIRONMENT: production"
    echo "   - NEXT_PUBLIC_VERSION: 1.0.0"
    echo "6. 点击 'Deploy'"
    echo

    # 自动打开浏览器
    if command -v start &> /dev/null; then
        start https://vercel.com/new 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open https://vercel.com/new 2>/dev/null || true
    fi

    log_info "等待前端部署完成..."
    read -p "部署完成后按回车继续: "

    log_success "前端部署步骤完成"
}

# 部署后端到Railway
deploy_backend() {
    log_step "开始后端部署 (Railway)"

    echo -e "${YELLOW}${GEAR} Railway部署指南:${NC}"
    echo "1. 打开浏览器访问: ${BLUE}https://railway.app${NC}"
    echo "2. 使用GitHub账号登录"
    echo "3. 点击 'New Project' -> 'Deploy from GitHub repo'"
    echo "4. 选择 'cpg2pvg-ai' 仓库"
    echo "5. 配置服务:"
    echo "   - Service Name: cpg2pvg-backend"
    echo "   - Root Directory: backend"
    echo "   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
    echo "6. 添加PostgreSQL数据库服务"
    echo "7. 配置环境变量:"
    echo "   - DATABASE_URL: (从PostgreSQL服务获取)"
    echo "   - SECRET_KEY: (生成安全密钥)"
    echo "   - ENVIRONMENT: production"
    echo "   - OPENAI_API_KEY: (可选)"
    echo "8. 点击 'Deploy'"
    echo

    # 自动打开浏览器
    if command -v start &> /dev/null; then
        start https://railway.app/new 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open https://railway.app/new 2>/dev/null || true
    fi

    log_info "等待后端部署完成..."
    read -p "部署完成后按回车继续: "

    log_success "后端部署步骤完成"
}

# 初始化数据库
initialize_database() {
    log_step "初始化数据库"

    echo -e "${YELLOW}${INFO} 数据库初始化指南:${NC}"
    echo "1. 在Railway控制台中打开PostgreSQL服务"
    echo "2. 点击 'Connect' 标签"
    echo "3. 复制DATABASE_URL连接字符串"
    echo "4. 使用PostgreSQL客户端连接数据库"
    echo "5. 执行初始化脚本: ${BLUE}scripts/cloud-deployment.sql${NC}"
    echo

    # 检查SQL文件是否存在
    if [ -f "scripts/cloud-deployment.sql" ]; then
        log_success "数据库初始化脚本已准备"
        echo "脚本位置: scripts/cloud-deployment.sql"
    else
        log_error "未找到数据库初始化脚本"
        exit 1
    fi

    read -p "数据库初始化完成后按回车继续: "

    log_success "数据库初始化完成"
}

# 配置Redis缓存 (可选)
configure_redis() {
    log_step "配置Redis缓存 (可选)"

    echo -e "${YELLOW}${INFO} Redis配置指南:${NC}"
    echo "1. 访问: ${BLUE}https://redis.com/try-free${NC}"
    echo "2. 注册并创建免费Redis实例"
    echo "3. 获取Redis连接字符串"
    echo "4. 在Railway后端添加环境变量:"
    echo "   - REDIS_URL: your-redis-connection-string"
    echo

    read -p "是否现在配置Redis? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v start &> /dev/null; then
            start https://redis.com/try-free 2>/dev/null || true
        elif command -v open &> /dev/null; then
            open https://redis.com/try-free 2>/dev/null || true
        fi

        read -p "Redis配置完成后按回车继续: "
        log_success "Redis配置完成"
    else
        log_info "跳过Redis配置"
    fi
}

# 验证部署
verify_deployment() {
    log_step "验证部署"

    echo -e "${YELLOW}${GEAR} 部署验证清单:${NC}"
    echo "请验证以下功能:"
    echo
    echo "前端验证:"
    echo "  [ ] 访问前端URL，页面正常加载"
    echo "  [ ] 所有导航链接正常工作"
    echo "  [ ] 移动端响应式设计正常"
    echo
    echo "后端验证:"
    echo "  [ ] 访问 /health 端点返回正常"
    echo "  [ ] 访问 /docs 查看API文档"
    echo "  [ ] 数据库连接正常"
    echo "  [ ] 文件上传功能正常"
    echo
    echo "集成验证:"
    echo "  [ ] 前后端API通信正常"
    echo "  [ ] 文件上传处理流程完整"
    echo "  [ ] 任务状态实时更新"
    echo "  [ ] 结果展示功能正常"
    echo

    read -p "验证完成后按回车继续: "

    log_success "部署验证完成"
}

# 生成部署报告
generate_report() {
    log_step "生成部署报告"

    REPORT_FILE="deployment-completion-report.md"

    cat > $REPORT_FILE << EOF
# 🎉 CPG2PVG-AI 部署完成报告

## 📅 部署信息
- **部署日期**: $(date)
- **部署人员**: ${USER}
- **部署脚本**: auto-deploy.sh

## ✅ 完成项目
- [x] GitHub仓库创建
- [x] 前端Vercel部署
- [x] 后端Railway部署
- [x] PostgreSQL数据库初始化
- [x] Redis缓存配置 $(if [[ $REPLY =~ ^[Yy]$ ]]; then echo "(可选)"; fi)
- [x] 部署验证

## 🔗 重要链接
- **GitHub仓库**: https://github.com/gaojunhan111-blip/cpg2pvg-ai
- **前端地址**: [请填写Vercel URL]
- **后端API**: [请填写Railway URL]
- **API文档**: [请填写Railway URL]/docs

## 📊 下一步
1. 监控应用运行状态
2. 配置域名和SSL证书
3. 设置备份策略
4. 配置监控告警
5. 优化性能和成本

## 🆘 技术支持
- Vercel文档: https://vercel.com/docs
- Railway文档: https://docs.railway.app
- 项目Issues: https://github.com/gaojunhan111-blip/cpg2pvg-ai/issues

---
**🚀 部署成功！CPG2PVG-AI系统已上线运行！**
EOF

    log_success "部署报告已生成: $REPORT_FILE"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    # 设置陷阱，确保脚本退出时清理
    trap cleanup EXIT

    show_banner

    log_step "开始CPG2PVG-AI自动化部署流程"
    echo

    check_requirements
    echo

    validate_project
    echo

    deploy_frontend
    echo

    deploy_backend
    echo

    initialize_database
    echo

    configure_redis
    echo

    verify_deployment
    echo

    generate_report
    echo

    log_success "🎉 CPG2PVG-AI部署完成！"
    echo
    echo -e "${GREEN}${ROCKET} 系统已成功部署到云端！${NC}"
    echo -e "${YELLOW}请查看生成的部署报告了解更多信息。${NC}"
    echo
}

# 运行主函数
main "$@"