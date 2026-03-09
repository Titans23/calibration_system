# 标定业务逻辑服务
import logging
import os
import ast
import cv2
import base64
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import numpy as np

from app.models import (
    DeviceStatus, CalibrationResult, CalibrationConfig,
    CalibrationData, RobotPose
)
from app.algorithm.hand_eye_calibrator import HandEyeCalibrator
from app.hardware.camera_device import CameraDevice, MockCameraDevice, RealCameraDevice,DobotCameraDevice
from app.hardware.robot_device import RobotDevice, RobotPose as RobotPoseClass, MockRobotDevice,UR5eRobotDevice
from app.config import get_robot_config,get_camera_config

# 配置日志
logger = logging.getLogger(__name__)

# 数据文件路径
DATA_DIR = Path(__file__).parent.parent / "data"
ORIGIN_DATA_FILE = DATA_DIR / "origin_data.txt"
IMG_DIR = DATA_DIR / "img"
CALIB_RESULT_DIR = DATA_DIR / "calib_result"

# 确保目录存在
CALIB_RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 设备实例（单例模式）
_camera_device: Optional[CameraDevice] = None
_robot_device: Optional[RobotDevice] = None


def get_camera_device() -> CameraDevice:
    """获取相机设备实例（单例）"""
    global _camera_device
    if _camera_device is None:
        camera_type = get_camera_config().get("type")
        if camera_type == "mock":
            _camera_device = MockCameraDevice()  # 实际项目中替换为真实相机类
        elif camera_type == "real":
            _camera_device = RealCameraDevice()  # 实际项目中替换为真实相机类
        elif camera_type == "dobot":
            _camera_device = DobotCameraDevice()  # 实际项目中替换为 Dobot 相机类
        else:
            raise ValueError(f"不支持的相机类型: {camera_type}")
    return _camera_device


def get_robot_device() -> RobotDevice:
    """获取机器人设备实例（单例）"""
    global _robot_device
    if _robot_device is None:
        robot_type = get_robot_config().get("type")
        if robot_type == "mock":
            _robot_device = MockRobotDevice()  # 实际项目中替换为真实机器人类
        elif robot_type == "ur5e":
            _robot_device = UR5eRobotDevice()  # 实际项目中替换为 UR5e 机器人类
        else:
            raise ValueError(f"不支持的机器人类型: {robot_type}")
    return _robot_device

def load_origin_data() -> List[Dict[str, Any]]:
    """从 origin_data.txt 加载标定数据

    Returns:
        包含图片路径和机械臂位姿的列表
    """
    data_list = []
    if not ORIGIN_DATA_FILE.exists():
        logger.warning(f"数据文件不存在: {ORIGIN_DATA_FILE}")
        return data_list

    with open(ORIGIN_DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 格式: filename.jpg,[x, y, z, rx, ry, rz]
            parts = line.split(",", 1)
            if len(parts) == 2:
                filename = parts[0].strip()
                pose_str = parts[1].strip()
                try:
                    pose = ast.literal_eval(pose_str)
                    # 完整的图片路径
                    image_path = str(IMG_DIR / filename)
                    data_list.append({
                        "image_path": image_path,
                        "robot_pose": pose  # [x, y, z, rx, ry, rz]
                    })
                except Exception as e:
                    logger.warning(f"解析数据行失败: {line}, error: {e}")

    logger.info(f"从 origin_data.txt 加载了 {len(data_list)} 条数据")
    return data_list

# 内存存储（后续可替换为数据库）
_calibration_data: List[Dict[str, Any]] = []
_calibration_result: Optional[Dict[str, Any]] = None
_calibration_config: Optional[Dict[str, Any]] = None
_device_status: DeviceStatus = DeviceStatus()


# ========== 设备状态相关 ==========

def get_device_status() -> DeviceStatus:
    """获取设备状态"""
    return _device_status


def check_devices() -> DeviceStatus:
    """检查设备连接状态"""
    global _device_status
    logging.info("检查设备连接状态...")

    # 获取设备实例
    camera = get_camera_device()
    robot = get_robot_device()

    # 连接相机
    camera_connected = camera.connect()
    if camera_connected:
        camera.start_grabbing()

    # 连接机器人
    robot_connected = robot.connect()

    # 检查标定板（通过相机检测）
    board_detected = False
    if camera_connected:
        frame = camera.get_frame()
        if frame is not None:
            board_width = _calibration_config.get("board_width", 10) if _calibration_config else 10
            board_height = _calibration_config.get("board_height", 7) if _calibration_config else 7
            detected, _ = camera.detect_calibration_board(frame, board_width, board_height)
            board_detected = detected

    _device_status = DeviceStatus(
        camera=camera_connected,
        robot=robot_connected,
        board=board_detected
    )
    logging.info(f"设备状态: camera={_device_status.camera}, robot={_device_status.robot}, board={_device_status.board}")
    return _device_status


# ========== 标定流程相关 ==========

def start_calibration(config: CalibrationConfig) -> Dict[str, Any]:
    """开始标定

    Args:
        config: 标定配置

    Returns:
        标定启动结果
    """
    global _calibration_data, _calibration_result,_calibration_config
    _calibration_data = []
    _calibration_result = None
    _calibration_config = config.model_dump()
    logger.info(f"开始标定, 配置: board={_calibration_config.get('board_width')}x{_calibration_config.get('board_height')}, square_size={_calibration_config.get('square_size')}m")

    return {
        "config": _calibration_config,
        "capture_count": 0
    }


def capture_calibration_data(data: CalibrationData) -> Dict[str, Any]:
    """采集标定数据

    Args:
        data: 标定数据

    Returns:
        采集结果
    """
    global _calibration_data

    if len(_calibration_data) >= 20:
        logger.warning("已达到最大采集数量 20")
        raise ValueError("已达到最大采集数量")

    # 获取设备
    camera = get_camera_device()
    robot = get_robot_device()

    # 获取当前机械臂位姿（如果前端没有提供，则从机器人获取）
    if data.robot_pose is not None:
        robot_pose = data.robot_pose.model_dump()
    else:
        current_pose = robot.get_current_pose()
        if current_pose:
            robot_pose = current_pose.to_dict()
        else:
            raise ValueError("无法获取机械臂位姿")

    # 捕获图像
    frame = camera.get_frame()
    if frame is None:
        raise ValueError("无法获取相机图像")

    # 检测标定板角点
    board_width = _calibration_config.get("board_width", 10) if _calibration_config else 10
    board_height = _calibration_config.get("board_height", 7) if _calibration_config else 7

    detected, corners = camera.detect_calibration_board(frame, board_width, board_height)

    if not detected:
        raise ValueError("未检测到标定板")

    corners_count = len(corners) if corners is not None else 0

    # 保存图像
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"calib_{timestamp_str}_{len(_calibration_data) + 1}.jpg"
    image_path = str(IMG_DIR / filename)
    os.makedirs(IMG_DIR, exist_ok=True)
    camera.save_image(frame, image_path)

    capture = {
        "index": len(_calibration_data) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "position": f"X:{robot_pose.get('x', 0):.1f} Y:{robot_pose.get('y', 0):.1f} Z:{robot_pose.get('z', 0):.1f} R:{robot_pose.get('rx', 0):.1f}",
        "corners": corners_count,
        "robot_pose": robot_pose,
        "image_corners": corners.tolist() if corners is not None else [],
        "image_path": image_path
    }

    _calibration_data.append(capture)
    logger.info(f"采集第 {capture['index']} 组数据, 角点数: {corners_count}, 累计: {len(_calibration_data)}/12")

    return capture


def get_calibration_data() -> Dict[str, Any]:
    """获取已采集的标定数据

    Returns:
        标定数据列表
    """
    return {
        "captures": _calibration_data,
        "count": len(_calibration_data)
    }


def calculate_calibration() -> Dict[str, Any]:
    """计算手眼矩阵

    Returns:
        标定结果
    """
    global _calibration_result

    if len(_calibration_data) < 3:
        logger.warning(f"数据不足，当前: {len(_calibration_data)}, 需要: 3")
        raise ValueError("数据不足，需要至少3组数据")

    logger.info(f"开始计算标定, 数据组数: {len(_calibration_data)}")

    # 获取标定配置
    board_width = _calibration_config.get("board_width", 10) if _calibration_config else 10
    board_height = _calibration_config.get("board_height", 7) if _calibration_config else 7
    square_size = _calibration_config.get("square_size", 0.020) if _calibration_config else 0.020

    # 尝试使用真实手眼标定算法
    try:
        # 提取图像路径和机械臂位姿
        image_paths = []
        robot_poses = []

        for capture in _calibration_data:
            # 检查是否有图像路径
            if "image_path" in capture and capture["image_path"]:
                image_paths.append(capture["image_path"])
                robot_poses.append([
                    capture["robot_pose"]["x"],
                    capture["robot_pose"]["y"],
                    capture["robot_pose"]["z"],
                    capture["robot_pose"]["rx"],
                    capture["robot_pose"]["ry"],
                    capture["robot_pose"]["rz"]
                ])

        if len(image_paths) >= 3:
            logger.info(f"使用真实算法计算, 有效图像数: {len(image_paths)}")
            # 使用真实手眼标定算法
            calibrator = HandEyeCalibrator(
                corner_long=board_width,
                corner_short=board_height,
                corner_size=square_size
            )

            result = calibrator.calibrate(
                image_paths=image_paths,
                robot_poses=robot_poses,
                method="PARK"
            )

            _calibration_result = {
                "method": result["method"],
                "data_count": result["data_count"],
                "reprojection_error": round(result["reprojection_error"], 4),
                "calibration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "success": True,
                "hand_eye_matrix": result["hand_eye_matrix"],
                "camera_matrix": result.get("camera_matrix"),
                "camera_reprojection_error": result.get("camera_reprojection_error"),
                "distortion_coeffs": result.get("distortion_coeffs")
            }
            logger.info(f"标定成功! 重投影误差: {_calibration_result['reprojection_error']}mm")
        else:
            # 没有图像路径，使用模拟计算
            raise ValueError("无图像路径，使用模拟计算")

    except Exception as e:
        # 降级为使用 origin_data.txt 数据进行计算
        logger.warning(f"手眼标定失败: {e}, 尝试使用 origin_data.txt 数据")

        # 从文件加载数据
        origin_data = load_origin_data()

        if len(origin_data) >= 3:
            # 使用真实算法计算
            calibrator = HandEyeCalibrator(
                corner_long=board_width,
                corner_short=board_height,
                corner_size=square_size
            )

            image_paths = [d["image_path"] for d in origin_data]
            robot_poses = origin_data[0]["robot_pose"]  # 这里简化处理

            try:
                result = calibrator.calibrate(
                    image_paths=image_paths,
                    robot_poses=[d["robot_pose"] for d in origin_data],
                    method="PARK"
                )
                _calibration_result = {
                    "method": result["method"],
                    "data_count": result["data_count"],
                    "reprojection_error": round(result["reprojection_error"], 4),
                    "calibration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "success": True,
                    "hand_eye_matrix": result["hand_eye_matrix"],
                    "camera_matrix": result.get("camera_matrix"),
                    "camera_reprojection_error": result.get("camera_reprojection_error"),
                    "distortion_coeffs": result.get("distortion_coeffs")
                }
                logger.info(f"使用 origin_data.txt 标定成功! 重投影误差: {_calibration_result['reprojection_error']}mm")
            except Exception as calc_error:
                raise ValueError(f"使用 origin_data.txt 计算失败: {calc_error}")
        else:
            raise ValueError(f"origin_data.txt 数据不足: {len(origin_data)}")

    # 保存标定结果到文件
    if _calibration_result:
        _save_calibration_result(_calibration_result)

    return _calibration_result


def _save_calibration_result(result: Dict[str, Any]) -> bool:
    """保存标定结果到文件

    Args:
        result: 标定结果字典

    Returns:
        是否保存成功
    """
    try:
        import json
        from datetime import datetime

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 转换 numpy 数组为列表（JSON 不支持 numpy 数组）
        def to_list(val):
            """安全转换为列表"""
            if val is None:
                return None
            if isinstance(val, np.ndarray):
                return val.tolist()
            # 已经是列表或其他类型，直接返回
            return val

        # ========== 1. 保存手眼标定结果 ==========
        hand_eye_data = {
            "method": result.get("method"),
            "data_count": result.get("data_count"),
            "reprojection_error": result.get("reprojection_error"),
            "calibration_time": result.get("calibration_time"),
            "success": result.get("success"),
            "hand_eye_matrix": to_list(result.get("hand_eye_matrix"))
        }

        hand_eye_file = CALIB_RESULT_DIR / f"hand_eye_{timestamp}.json"
        with open(hand_eye_file, 'w', encoding='utf-8') as f:
            json.dump(hand_eye_data, f, indent=2, ensure_ascii=False)
        logger.info(f"手眼标定结果已保存到: {hand_eye_file}")

        # 保存最新手眼标定结果
        hand_eye_latest = CALIB_RESULT_DIR / "hand_eye_latest.json"
        with open(hand_eye_latest, 'w', encoding='utf-8') as f:
            json.dump(hand_eye_data, f, indent=2, ensure_ascii=False)

        # ========== 2. 保存相机标定结果 ==========
        camera_calib_data = {
            "calibration_time": result.get("calibration_time"),
            "success": result.get("success"),
            "camera_matrix": to_list(result.get("camera_matrix")),
            "distortion_coeffs": to_list(result.get("distortion_coeffs")),
            "camera_reprojection_error": result.get("camera_reprojection_error")
        }

        camera_calib_file = CALIB_RESULT_DIR / f"camera_calib_{timestamp}.json"
        with open(camera_calib_file, 'w', encoding='utf-8') as f:
            json.dump(camera_calib_data, f, indent=2, ensure_ascii=False)
        logger.info(f"相机标定结果已保存到: {camera_calib_file}")

        # 保存最新相机标定结果
        camera_calib_latest = CALIB_RESULT_DIR / "camera_calib_latest.json"
        with open(camera_calib_latest, 'w', encoding='utf-8') as f:
            json.dump(camera_calib_data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        logger.error(f"保存标定结果失败: {e}")
        return False


def get_calibration_result() -> Optional[Dict[str, Any]]:
    """获取标定结果

    Returns:
        标定结果，如果不存在则返回 None
    """
    return _calibration_result


def clear_calibration_data() -> None:
    """清空标定数据"""
    global _calibration_data, _calibration_result
    logger.info("清空标定数据")
    _calibration_data = []
    _calibration_result = None


def is_calibration_completed() -> bool:
    """检查标定是否完成

    Returns:
        是否已完成标定
    """
    return _calibration_result is not None


# ========== 相机实时预览相关 ==========

def get_camera_frame() -> Optional[str]:
    """获取当前相机帧（Base64编码）

    Returns:
        Base64编码的图像字符串，失败返回 None
    """
    camera = get_camera_device()
    if camera.is_connected():
        return camera.get_frame_base64()
    return None


def start_camera_stream() -> bool:
    """启动相机采集

    Returns:
        是否成功启动
    """
    camera = get_camera_device()
    if not camera.is_connected():
        camera.connect()
    return camera.start_grabbing()


def stop_camera_stream() -> bool:
    """停止相机采集

    Returns:
        是否成功停止
    """
    camera = get_camera_device()
    return camera.stop_grabbing()
