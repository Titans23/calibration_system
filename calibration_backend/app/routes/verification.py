# 验证相关 API 路由
from fastapi import APIRouter, HTTPException

from app.models import TargetPosition
from app.service import verification_service

router = APIRouter(prefix="/verification", tags=["验证"])


@router.get("/info")
async def get_calibration_info():
    """获取标定信息"""
    info = verification_service.get_calibration_info()
    return {
        "code": 200,
        "data": info
    }


@router.post("/reprojection")
async def verify_reprojection():
    """重投影验证"""
    result = verification_service.verify_reprojection()
    return {
        "code": 200,
        "message": "验证完成",
        "data": result
    }


@router.post("/target")
async def verify_target(position: TargetPosition):
    """目标点验证"""
    result = verification_service.verify_target(position)
    return {
        "code": 200,
        "message": "验证完成",
        "data": result
    }


@router.post("/move-to-target")
async def move_to_target(position: TargetPosition):
    """移动机械臂到目标位置"""
    result = verification_service.move_to_target(position)
    return {
        "code": 200,
        "message": f"已移动到目标位置 ({position.x}, {position.y}, {position.z})",
        "data": result
    }
