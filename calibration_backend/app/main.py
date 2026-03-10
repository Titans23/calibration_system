"""
手眼标定平台 - 后端服务
基于 FastAPI 构建
"""
import logging
import sys
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

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

# 全局变量
_streaming = False
_websocket = None
_frame_count = 0
_last_fps_time = time.time()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时视频流"""
    global _streaming, _websocket, _frame_count, _last_fps_time
    await websocket.accept()
    _websocket = websocket
    _streaming = True
    _frame_count = 0
    _last_fps_time = time.time()

    logger.info("WebSocket 客户端连接")

    # 启动相机采集
    from app.service import calibration_service
    calibration_service.start_camera_stream()
    logger.info("相机已启动")

    try:
        while _streaming:
            try:
                frame_base64 = calibration_service.get_camera_frame()
                if frame_base64:
                    _frame_count += 1
                    # 每秒计算一次帧率
                    current_time = time.time()
                    if current_time - _last_fps_time >= 1.0:
                        fps = _frame_count / (current_time - _last_fps_time)
                        _frame_count = 0
                        _last_fps_time = current_time
                        # 发送帧率和图像
                        await websocket.send_text(f"{{\"type\":\"fps\",\"value\":{fps:.1f}}}")
                        await websocket.send_text(f"data:image/jpeg;base64,{frame_base64}")
                    else:
                        await websocket.send_text(f"data:image/jpeg;base64,{frame_base64}")
                import asyncio
                await asyncio.sleep(0.033)  # 约30fps
            except Exception as e:
                logger.error(f"发送帧失败: {e}")
                break
    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开")
    finally:
        _streaming = False
        _websocket = None
        calibration_service.stop_camera_stream()


def stop_streaming():
    """停止流"""
    global _streaming
    _streaming = False


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


# 全局异常处理器 - 捕获 ValueError 并返回给前端
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """处理 ValueError 异常，返回错误信息给前端"""
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": str(exc),
            "success": False
        }
    )


# 全局异常处理器 - 捕获 HTTPException 并返回统一格式
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTPException 异常，返回统一格式的错误信息"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "success": False
        }
    )

# 注册 WebSocket 路由
@app.websocket("/ws/camera")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)


# 注册路由（添加 /api 前缀）
from app.routes import calibration, verification, robot
app.include_router(calibration.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(robot.router, prefix="/api")


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
    stop_streaming()
    logging.info("应用关闭")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
