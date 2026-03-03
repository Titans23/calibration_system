# 验证业务逻辑服务
from typing import Dict, Any
import random
import math

from app.models import (
    VerificationResult, TargetPosition
)
import app.service.calibration_service


# ========== 标定信息相关 ==========

def get_calibration_info() -> Dict[str, Any]:
    """获取标定信息

    Returns:
        标定信息
    """
    result = app.service.calibration_service.get_calibration_result()

    if result is None:
        return {
            "time": "未完成标定",
            "data_count": 0,
            "error": "N/A",
            "method": "N/A"
        }

    return {
        "time": result.get("calibration_time", ""),
        "data_count": result.get("data_count", 0),
        "error": f"{result.get('reprojection_error', 0)} mm",
        "method": result.get("method", "Tsai-Lenz")
    }


# ========== 重投影验证 ==========

def verify_reprojection() -> Dict[str, Any]:
    """重投影验证

    Returns:
        验证结果
    """
    calibration_result = app.service.calibration_service.get_calibration_result()

    if calibration_result is None:
        raise ValueError("请先完成标定")

    data_count = calibration_result.get("data_count", 12)

    # TODO: 实现实际的重投影误差计算逻辑
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
        "result": result.model_dump(),
        "error_data": error_list
    }


# ========== 目标点验证 ==========

def verify_target(position: TargetPosition) -> Dict[str, Any]:
    """目标点验证

    Args:
        position: 目标位置

    Returns:
        验证结果
    """
    calibration_result = app.service.calibration_service.get_calibration_result()

    if calibration_result is None:
        raise ValueError("请先完成标定")

    # TODO: 实现实际的目标点验证逻辑
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
        "pass": is_passed,
        "position_compare": position_compare,
        "max_error": max_diff
    }


# ========== 移动到目标位置 ==========

def move_to_target(position: TargetPosition) -> Dict[str, Any]:
    """移动机械臂到目标位置

    Args:
        position: 目标位置

    Returns:
        移动结果
    """
    # TODO: 实现实际的机械臂运动逻辑
    # 实际项目中会控制调用机械臂 SDK
    return {
        "target": position.model_dump(),
        "moved": True
    }
