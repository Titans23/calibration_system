# 标定相关 API 路由
from fastapi import APIRouter, HTTPException
import logging
from app.models import (
    CalibrationConfig, CalibrationData
)
from app.service import calibration_service

router = APIRouter(prefix="/calibration", tags=["标定"])

logger = logging.getLogger(__name__)
@router.get("/status")
async def get_status():
    """获取设备状态"""
    status = calibration_service.get_device_status()
    return {
        "code": 200,
        "data": status.model_dump()
    }


@router.post("/check-devices")
async def check_devices():
    """检查设备连接状态"""
    status = calibration_service.check_devices()
    return {
        "code": 200,
        "message": "设备检查完成",
        "data": status.model_dump()
    }


@router.post("/start")
async def start_calibration(config: CalibrationConfig):
    """开始标定"""
    result = calibration_service.start_calibration(config)

    return {
        "code": 200,
        "message": "标定已启动",
        "data": result
    }


@router.post("/capture")
async def capture_data(data: CalibrationData):
    """采集标定数据"""
    capture = calibration_service.capture_calibration_data(data)
    return {
        "code": 200,
        "message": f"已采集第 {capture['index']} 组数据",
        "data": capture
    }


@router.get("/data")
async def get_calibration_data():
    """获取已采集的标定数据"""
    data = calibration_service.get_calibration_data()
    return {
        "code": 200,
        "data": data
    }


@router.post("/calculate")
async def calculate_calibration():
    """计算手眼矩阵"""
    result = calibration_service.calculate_calibration()
    return {
        "code": 200,
        "message": "标定计算完成",
        "data": result
    }


@router.get("/result")
async def get_calibration_result():
    """获取标定结果"""
    result = calibration_service.get_calibration_result()
    if result is None:
        raise HTTPException(status_code=404, detail="暂无标定结果")

    return {
        "code": 200,
        "data": result
    }


@router.post("/clear")
async def clear_calibration_data():
    """清空标定数据"""
    calibration_service.clear_calibration_data()

    return {
        "code": 200,
        "message": "已清空所有数据"
    }

@router.post("/move_by_keyword")
async def move_robot_by_keyword(data: dict):
    """移动机械臂到指定位姿

    Args:
        data: 请求体，包含 keyword 字段

    Request Body:
        {"keyword": "px"}
    """
    keyword = data.get("keyword")
    if not keyword:
        raise ValueError("缺少 keyword 参数")

    pose = calibration_service.move_robot_by_keyword(keyword)
    return {
        "code": 200,
        "message": "机械臂移动完成",
        "data": pose.to_dict_mm()  
    }


@router.get("/robot_pose")
async def get_robot_pose():
    """获取机械臂当前位姿"""
    robot = calibration_service.get_robot_device()
    robot.connect()
    pose = robot.get_current_pose()
    return {
        "code": 200,
        "data": pose.to_dict_mm()
    }