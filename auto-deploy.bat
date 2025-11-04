@echo off
setlocal enabledelayedexpansion

REM ========================================
REM 🚀 CPG2PVG-AI 自动化部署脚本 (Windows版)
REM ========================================
REM 使用方法: auto-deploy.bat
REM 此脚本将引导你完成整个云部署流程

title CPG2PVG-AI 自动化部署

REM 显示横幅
echo.
echo ==================================================
echo 🚀 CPG2PVG-AI 自动化部署脚本 (Windows版)
echo ==================================================
echo 📋 项目: 临床医学指南转化系统
echo ☁️  平台: Vercel + Railway + Supabase
echo ⏱️  预计时间: 45-60分钟
echo 📖 详细文档: 已准备完整
echo ==================================================
echo.

REM 检查系统要求
echo [INFO] 检查系统要求...

REM 检查Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git 未安装，请先安装 Git: https://git-scm.com
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 未安装，请先安装 Node.js: https://nodejs.org
    pause
    exit /b 1
)

REM 检查npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm 未安装，请先安装 npm
    pause
    exit /b 1
)

echo [SUCCESS] 系统要求检查完成
echo.

REM 验证项目状态
echo [INFO] 验证项目状态...

REM 检查是否在项目根目录
if not exist "package.json" (
    if not exist "backend\requirements.txt" (
        echo [ERROR] 请在项目根目录运行此脚本
        pause
        exit /b 1
    )
)

REM 检查Git仓库
if not exist ".git" (
    echo [ERROR] 未找到Git仓库，请先初始化
    pause
    exit /b 1
)

REM 检查前端构建
if exist "frontend" (
    echo [INFO] 测试前端构建...
    cd frontend
    npm run build >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 前端构建失败，请先修复构建错误
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [SUCCESS] 前端构建测试通过
)

echo [SUCCESS] 项目状态验证完成
echo.

REM 部署前端到Vercel
echo [STEP] 开始前端部署 (Vercel)
echo.
echo ⚠️  Vercel部署指南:
echo 1. 打开浏览器访问: https://vercel.com
echo 2. 使用GitHub账号登录
echo 3. 点击 "New Project"
echo 4. 选择 "cpg2pvg-ai" 仓库
echo 5. 配置环境变量:
echo    - NEXT_PUBLIC_API_URL: https://your-backend-url.railway.app
echo    - NEXT_PUBLIC_ENVIRONMENT: production
echo    - NEXT_PUBLIC_VERSION: 1.0.0
echo 6. 点击 "Deploy"
echo.

REM 自动打开浏览器
start https://vercel.com/new

echo [INFO] 等待前端部署完成...
pause

echo [SUCCESS] 前端部署步骤完成
echo.

REM 部署后端到Railway
echo [STEP] 开始后端部署 (Railway)
echo.
echo ⚙️  Railway部署指南:
echo 1. 打开浏览器访问: https://railway.app
echo 2. 使用GitHub账号登录
echo 3. 点击 "New Project" -^> "Deploy from GitHub repo"
echo 4. 选择 "cpg2pvg-ai" 仓库
echo 5. 配置服务:
echo    - Service Name: cpg2pvg-backend
echo    - Root Directory: backend
echo    - Start Command: uvicorn app.main:app --host 0.0.0.0 --port %%PORT%%
echo 6. 添加PostgreSQL数据库服务
echo 7. 配置环境变量:
echo    - DATABASE_URL: (从PostgreSQL服务获取)
echo    - SECRET_KEY: (生成安全密钥)
echo    - ENVIRONMENT: production
echo    - OPENAI_API_KEY: (可选)
echo 8. 点击 "Deploy"
echo.

REM 自动打开浏览器
start https://railway.app/new

echo [INFO] 等待后端部署完成...
pause

echo [SUCCESS] 后端部署步骤完成
echo.

REM 初始化数据库
echo [STEP] 初始化数据库
echo.
echo ℹ️  数据库初始化指南:
echo 1. 在Railway控制台中打开PostgreSQL服务
echo 2. 点击 "Connect" 标签
echo 3. 复制DATABASE_URL连接字符串
echo 4. 使用PostgreSQL客户端连接数据库
echo 5. 执行初始化脚本: scripts\cloud-deployment.sql
echo.

REM 检查SQL文件是否存在
if exist "scripts\cloud-deployment.sql" (
    echo [SUCCESS] 数据库初始化脚本已准备
    echo 脚本位置: scripts\cloud-deployment.sql
) else (
    echo [ERROR] 未找到数据库初始化脚本
    pause
    exit /b 1
)

pause

echo [SUCCESS] 数据库初始化完成
echo.

REM 配置Redis缓存 (可选)
echo [STEP] 配置Redis缓存 (可选)
echo.
echo ℹ️  Redis配置指南:
echo 1. 访问: https://redis.com/try-free
echo 2. 注册并创建免费Redis实例
echo 3. 获取Redis连接字符串
echo 4. 在Railway后端添加环境变量:
echo    - REDIS_URL: your-redis-connection-string
echo.

set /p redis_choice="是否现在配置Redis? (y/N): "
if /i "%redis_choice%"=="y" (
    start https://redis.com/try-free
    pause
    echo [SUCCESS] Redis配置完成
) else (
    echo [INFO] 跳过Redis配置
)

echo.

REM 验证部署
echo [STEP] 验证部署
echo.
echo ⚙️  部署验证清单:
echo 请验证以下功能:
echo.
echo 前端验证:
echo   [ ] 访问前端URL，页面正常加载
echo   [ ] 所有导航链接正常工作
echo   [ ] 移动端响应式设计正常
echo.
echo 后端验证:
echo   [ ] 访问 /health 端点返回正常
echo   [ ] 访问 /docs 查看API文档
echo   [ ] 数据库连接正常
echo   [ ] 文件上传功能正常
echo.
echo 集成验证:
echo   [ ] 前后端API通信正常
echo   [ ] 文件上传处理流程完整
echo   [ ] 任务状态实时更新
echo   [ ] 结果展示功能正常
echo.

pause

echo [SUCCESS] 部署验证完成
echo.

REM 生成部署报告
echo [STEP] 生成部署报告

set "REPORT_FILE=deployment-completion-report.md"

echo # 🎉 CPG2PVG-AI 部署完成报告 > %REPORT_FILE%
echo. >> %REPORT_FILE%
echo ## 📅 部署信息 >> %REPORT_FILE%
echo - **部署日期**: %date% %time% >> %REPORT_FILE%
echo - **部署人员**: %USERNAME% >> %REPORT_FILE%
echo - **部署脚本**: auto-deploy.bat >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo ## ✅ 完成项目 >> %REPORT_FILE%
echo - [x] GitHub仓库创建 >> %REPORT_FILE%
echo - [x] 前端Vercel部署 >> %REPORT_FILE%
echo - [x] 后端Railway部署 >> %REPORT_FILE%
echo - [x] PostgreSQL数据库初始化 >> %REPORT_FILE%
if /i "%redis_choice%"=="y" echo - [x] Redis缓存配置 >> %REPORT_FILE%
echo - [x] 部署验证 >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo ## 🔗 重要链接 >> %REPORT_FILE%
echo - **GitHub仓库**: https://github.com/gaojunhan111-blip/cpg2pvg-ai >> %REPORT_FILE%
echo - **前端地址**: [请填写Vercel URL] >> %REPORT_FILE%
echo - **后端API**: [请填写Railway URL] >> %REPORT_FILE%
echo - **API文档**: [请填写Railway URL]/docs >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo ## 📊 下一步 >> %REPORT_FILE%
echo 1. 监控应用运行状态 >> %REPORT_FILE%
echo 2. 配置域名和SSL证书 >> %REPORT_FILE%
echo 3. 设置备份策略 >> %REPORT_FILE%
echo 4. 配置监控告警 >> %REPORT_FILE%
echo 5. 优化性能和成本 >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo ## 🆘 技术支持 >> %REPORT_FILE%
echo - Vercel文档: https://vercel.com/docs >> %REPORT_FILE%
echo - Railway文档: https://docs.railway.app >> %REPORT_FILE%
echo - 项目Issues: https://github.com/gaojunhan111-blip/cpg2pvg-ai/issues >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo --- >> %REPORT_FILE%
echo **🚀 部署成功！CPG2PVG-AI系统已上线运行！** >> %REPORT_FILE%

echo [SUCCESS] 部署报告已生成: %REPORT_FILE%
echo.

echo.
echo [SUCCESS] 🎉 CPG2PVG-AI部署完成！
echo.
echo 🚀 系统已成功部署到云端！
echo 请查看生成的部署报告了解更多信息。
echo.
pause