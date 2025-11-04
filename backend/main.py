"""
FastAPI应用入口 - Railway部署简化版
Simplified FastAPI Entry Point for Railway Deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建FastAPI应用实例
app = FastAPI(
    title="CPG2PVG-AI API",
    description="Clinical Practice Guidelines to Public Guidelines AI System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CPG2PVG-AI API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "service": "cpg2pvg-backend"
    }

@app.get("/api/v1/health")
async def api_health():
    """API健康检查"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "cpg2pvg-ai-backend"
    }

# 如果需要导入完整的应用，可以取消注释下面的代码
# try:
#     from app.main import app as full_app
#     # 复制完整应用的路由到简化应用
#     app.include_router(full_app.router, prefix="/api/v1")
# except ImportError as e:
#     print(f"Warning: Could not import full application: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)