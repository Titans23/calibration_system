"""
手眼标定平台 - 后端服务
基于 FastAPI 构建
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时配置日志（uvicorn reload 时也会执行）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("app.service").setLevel(logging.INFO)
    logging.info("应用启动")
    yield
    logging.info("应用关闭")

from app.routes import calibration, verification

app = FastAPI(
    title="手眼标定平台 API",
    description="提供手眼标定、验证等功能的 RESTful API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（添加 /api 前缀）
app.include_router(calibration.router, prefix="/api")
app.include_router(verification.router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用手眼标定平台 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # 直接运行，不用 reload
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
