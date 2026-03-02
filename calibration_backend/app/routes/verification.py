# 验证相关 API 路由
from fastapi import APIRouter, HTTPException
from datetime import datetime
import random
import math

from app.models import (
    VerificationResult, TargetPosition,
    ErrorData, PositionCompare
)
from app.routes.calibration import _calibration_result, _calibration_data

router = APIRouter(prefix="/verification", tags=["验证"])


@router.get("/info")
async def get_calibration_info():
    """获取标定信息"""
    if _calibration_result is None:
        # 返回默认信息
        return {
            "code": 200,
            "data": {
                "time": "未完成标定",
                "data_count": 0,
                "error": "N/A",
                "method": "N/A"
            }
        }

    return {
        "code": 200,
        "data": {
            "time": _calibration_result.get("calibration_time", ""),
            "data_count": _calibration_result.get("data_count", 0),
            "error": f"{_calibration_result.get('reprojection_error', 0)} mm",
            "method": _calibration_result.get("method", "Tsai-Lenz")
        }
    }


@router.post("/reprojection")
async def verify_reprojection():
    """重投影验证"""
    if _calibration_result is None:
        raise HTTPException(status_code=400, message="请先完成标定")

    data_count = _calibration_result.get("data_count", 12)

    # 生成模拟误差数据
    error_list = []
    for i in range(data_count):
        error = random.uniform(0.01, 0.8)
        error_list.append({
            "index": i + 1,
            "error": round(error, 3),
            "status": "合格" if error < 0.5 else "偏高"
        })

    errors = [e["error"] for e in error_list]
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    std_dev = math.sqrt(sum((e - avg_error) ** 2 for e in errors) / len(errors))

    result = VerificationResult(
        is_passed=avg_error < 0.5,
        avg_error=round(avg_error, 3),
        max_error=round(max_error, 3),
        std_dev=round(std_dev, 3),
        point_count=data_count
    )

    return {
        "code": 200,
        "message": "验证完成",
        "data": {
            "result": result.model_dump(),
            "error_data": error_list
        }
    }


@router.post("/target")
async def verify_target(position: TargetPosition):
    """目标点验证"""
    if _calibration_result is None:
        raise HTTPException(status_code=400, message="请先完成标定")

    # 模拟目标点验证
    # 实际项目中会根据手眼矩阵计算理论位置并与实际位置对比

    # 生成带误差的实际位置
    position_compare = [
        {
            "axis": "X",
            "target": position.x,
            "actual": round(position.x + random.uniform(-0.3, 0.3), 2),
            "diff": round(random.uniform(0.1, 0.4), 2)
        },
        {
            "axis": "Y",
            "target": position.y,
            "actual": round(position.y + random.uniform(-0.3, 0.3), 2),
            "diff": round(random.uniform(0.1, 0.4), 2)
        },
        {
            "axis": "Z",
            "target": position.z,
            "actual": round(position.z + random.uniform(-0.3, 0.3), 2),
            "diff": round(random.uniform(0.1, 0.4), 2)
        },
        {
            "axis": "RX",
            "target": position.rx,
            "actual": round(position.rx + random.uniform(-0.5, 0.5), 2),
            "diff": round(random.uniform(0.2, 0.5), 2)
        }
    ]

    max_diff = max(p["diff"] for p in position_compare)
    is_passed = max_diff < 1.0

    return {
        "code": 200,
        "message": "验证完成",
        "data": {
            "pass": is_passed,
            "position_compare": position_compare,
            "max_error": max_diff
        }
    }


@router.post("/move-to-target")
async def move_to_target(position: TargetPosition):
    """移动机械臂到目标位置"""
    # 模拟机械臂运动
    # 实际项目中会调用机械臂 SDK

    return {
        "code": 200,
        "message": f"已移动到目标位置 ({position.x}, {position.y}, {position.z})",
        "data": {
            "target": position.model_dump(),
            "moved": True
        }
    }
