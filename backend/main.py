"""
FastAPI应用入口文件 - Railway部署
Railway FastAPI Application Entry Point
"""

from app.main import app

# Railway会自动从这个文件启动应用
# 直接导入app实例即可

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)