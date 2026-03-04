"""
手眼标定平台 - 后端服务
基于 FastAPI 构建
"""
import logging
import sys
import asyncio
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Socket.IO 相关
import socketio as python_socketio
from socketio import ASGIApp

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("app.service").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# 创建 Socket.IO 服务器
sio = python_socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
asgi_app = ASGIApp(sio)

# 全局变量
_streaming = False
_streaming_thread = None
_stop_streaming = threading.Event()


@sio.on("connect")
async def connect(sid, environ):
    """客户端连接"""
    logger.info(f"客户端连接: {sid}")
    await sio.emit("connected", {"sid": sid}, room=sid)


@sio.on("disconnect")
async def disconnect(sid):
    """客户端断开"""
    logger.info(f"客户端断开: {sid}")


@sio.on("start_stream")
async def start_stream(sid, data):
    """开始相机流"""
    global _streaming, _streaming_thread
    logger.info(f"客户端请求开始流: {sid}")

    from app.service import calibration_service
    calibration_service.start_camera_stream()
    _streaming = True
    _stop_streaming.clear()

    # 启动后台发送线程
    _streaming_thread = threading.Thread(target=_send_camera_frames, daemon=True)
    _streaming_thread.start()

    await sio.emit("stream_started", {"status": "success"}, room=sid)
    return {"status": "success"}


@sio.on("stop_stream")
async def stop_stream(sid, data):
    """停止相机流"""
    global _streaming
    logger.info(f"客户端请求停止流: {sid}")

    _streaming = False
    _stop_streaming.set()

    from app.service import calibration_service
    calibration_service.stop_camera_stream()

    await sio.emit("stream_stopped", {"status": "success"}, room=sid)
    return {"status": "success"}


def _send_camera_frames():
    """后台线程：定时发送相机帧"""
    while _streaming and not _stop_streaming.is_set():
        try:
            from app.service import calibration_service
            frame_base64 = calibration_service.get_camera_frame()
            if frame_base64:
                # 使用 sync_to_async 来在异步上下文中发送
                asyncio.run(sio.emit("camera_frame", {"image": f"data:image/jpeg;base64,{frame_base64}"}))
        except Exception as e:
            logger.error(f"发送相机帧失败: {e}")
        import time
        time.sleep(0.033)  # 约30fps


# FastAPI 应用
app = FastAPI(
    title="手眼标定平台 API",
    description="提供手眼标定、验证等功能的 RESTful API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 Socket.IO ASGI 应用
app.mount("/socket.io", asgi_app)

# 注册路由（添加 /api 前缀）
from app.routes import calibration, verification
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


@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logging.info("应用启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    global _streaming
    _streaming = False
    _stop_streaming.set()
    logging.info("应用关闭")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
