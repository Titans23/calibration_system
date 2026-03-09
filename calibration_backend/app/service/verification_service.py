# 验证业务逻辑服务
import logging
from typing import Dict, Any
import random
import math

from app.models import (
    VerificationResult, TargetPosition
)
import app.service.calibration_service

# 配置日志
logger = logging.getLogger(__name__)


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



def detect_target_point() -> Dict[str, Any]:
    """仅检测标定板角点位置，不移动机械臂

    步骤：
    1. 拍摄标定板图像
    2. 检测标定板角点，计算左上角角点在相机坐标系下的3D位置
    3. 使用手眼矩阵转换为机械臂基座坐标
    4. 返回目标坐标供用户确认移动

    Returns:
        检测结果，包含目标坐标和当前机械臂姿态信息
    """
    import app.service.calibration_service as calib_service

    # 检查标定结果
    calibration_result = calib_service.get_calibration_result()
    if calibration_result is None:
        raise ValueError("请先完成标定")

    # 获取标定配置
    calib_config = calib_service._calibration_config
    board_width = calib_config.get("board_width", 10) if calib_config else 10
    board_height = calib_config.get("board_height", 7) if calib_config else 7
    square_size = calib_config.get("square_size", 0.020) if calib_config else 0.020

    # 获取当前机械臂位姿
    robot = calib_service.get_robot_device()
    robot.connect()
    current_pose = robot.get_current_pose()

    if current_pose is None:
        raise ValueError("无法获取机械臂当前位姿")

    pose_dict = current_pose.to_dict()

    # 检查当前姿态：建议RX、RY接近0（末端与基座X、Y轴对齐）
    rx = pose_dict.get("rx", 0)
    ry = pose_dict.get("ry", 0)
    rz = pose_dict.get("rz", 0)

    # 判断姿态是否对齐（容差 ±5度）
    tolerance = 5.0
    is_aligned = abs(rx) <= tolerance and abs(ry) <= tolerance

    alignment_tip = ""
    if not is_aligned:
        alignment_tip = f"当前姿态: RX={rx:.1f}°, RY={ry:.1f}°。建议先将机械臂末端调整为RX≈0°, RY≈0°（与基座X、Y轴对齐）后再进行检测，以获得更准确的结果。"

    # 计算角点在机械臂基座坐标系下的3D位置
    corner_base = calib_service.calculate_corner_base(
        board_width=board_width,
        board_height=board_height,
        square_size=square_size
    )

    return {
        "detected": True,
        "corner_base": corner_base,
        "current_pose": {
            "x": round(pose_dict.get("x", 0), 2),
            "y": round(pose_dict.get("y", 0), 2),
            "z": round(pose_dict.get("z", 0), 2),
            "rx": round(rx, 2),
            "ry": round(ry, 2),
            "rz": round(rz, 2)
        },
        "is_aligned": is_aligned,
        "alignment_tip": alignment_tip,
        "target_pose": {
            "x": round(corner_base.get("x", 0), 2),
            "y": round(corner_base.get("y", 0), 2),
            "z": round(corner_base.get("z", 0), 2),
            "rx": 0,
            "ry": 0,
            "rz": rz  # 保持当前的Rz
        }
    }
