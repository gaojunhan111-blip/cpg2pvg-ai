"""
FastAPI应用简单入口 - Railway部署
Simple FastAPI Entry Point for Railway Deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建FastAPI应用实例
app = FastAPI(
    title="CPG2PVG-AI API",
    description="Clinical Practice Guidelines to Public Guidelines AI System",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CPG2PVG-AI API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "cpg2pvg-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)