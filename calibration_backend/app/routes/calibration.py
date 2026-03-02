# 标定相关 API 路由
from fastapi import APIRouter, HTTPException
from datetime import datetime
import random

from app.models import (
    DeviceStatus, CalibrationResult, CaptureData,
    CalibrationConfig, CalibrationData, RobotPose
)

router = APIRouter(prefix="/calibration", tags=["标定"])

# 内存存储（生产环境应使用数据库）
_calibration_data = []
_calibration_result = None
_device_status = DeviceStatus()


@router.get("/status")
async def get_status():
    """获取设备状态"""
    return {
        "code": 200,
        "data": _device_status.model_dump()
    }


@router.post("/check-devices")
async def check_devices():
    """检查设备连接状态"""
    global _device_status
    # 模拟设备检查
    _device_status = DeviceStatus(camera=True, robot=True, board=True)
    return {
        "code": 200,
        "message": "设备检查完成",
        "data": _device_status.model_dump()
    }


@router.post("/start")
async def start_calibration(config: CalibrationConfig):
    """开始标定"""
    global _calibration_data, _calibration_result
    _calibration_data = []
    _calibration_result = None

    return {
        "code": 200,
        "message": "标定已启动",
        "data": {
            "config": config.model_dump(),
            "capture_count": 0
        }
    }


@router.post("/capture")
async def capture_data(data: CalibrationData):
    """采集标定数据"""
    global _calibration_data

    if len(_calibration_data) >= 20:
        raise HTTPException(status_code=400, message="已达到最大采集数量")

    # 模拟图像处理
    corners_count = random.randint(50, 54)

    capture = {
        "index": len(_calibration_data) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "position": f"X:{data.robot_pose.x:.1f} Y:{data.robot_pose.y:.1f} Z:{data.robot_pose.z:.1f} R:{data.robot_pose.rx:.1f}",
        "corners": corners_count,
        "robot_pose": data.robot_pose.model_dump(),
        "image_corners": data.image_corners
    }

    _calibration_data.append(capture)

    return {
        "code": 200,
        "message": f"已采集第 {len(_calibration_data)} 组数据",
        "data": capture
    }


@router.get("/data")
async def get_calibration_data():
    """获取已采集的标定数据"""
    return {
        "code": 200,
        "data": {
            "captures": _calibration_data,
            "count": len(_calibration_data)
        }
    }


@router.post("/calculate")
async def calculate_calibration():
    """计算手眼矩阵"""
    global _calibration_result

    if len(_calibration_data) < 3:
        raise HTTPException(status_code=400, message="数据不足，需要至少3组数据")

    # 模拟计算过程
    # 实际项目中这里会调用 OpenCV 或其他标定算法

    reprojection_error = random.uniform(0.005, 0.05)

    _calibration_result = {
        "method": "Tsai-Lenz",
        "data_count": len(_calibration_data),
        "reprojection_error": round(reprojection_error, 4),
        "calibration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        # 手眼矩阵 (4x4)
        "hand_eye_matrix": [
            [1.0, 0.0, 0.0, 100.0],
            [0.0, 1.0, 0.0, 200.0],
            [0.0, 0.0, 1.0, 300.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
    }

    return {
        "code": 200,
        "message": "标定计算完成",
        "data": _calibration_result
    }


@router.get("/result")
async def get_calibration_result():
    """获取标定结果"""
    if _calibration_result is None:
        raise HTTPException(status_code=404, message="暂无标定结果")

    return {
        "code": 200,
        "data": _calibration_result
    }


@router.post("/clear")
async def clear_calibration_data():
    """清空标定数据"""
    global _calibration_data, _calibration_result
    _calibration_data = []
    _calibration_result = None

    return {
        "code": 200,
        "message": "已清空所有数据"
    }
