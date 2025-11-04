"""
FastAPI应用简单入口 - Railway部署备用入口
Simple FastAPI Entry Point for Railway Deployment
"""

# 从主应用模块导入FastAPI实例
from app.main import app

# Railway会自动检测这个文件
__all__ = ["app"]