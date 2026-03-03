# 数据模型定义
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DeviceStatus(BaseModel):
    """设备状态"""
    camera: bool = False
    robot: bool = False
    board: bool = False


class CaptureData(BaseModel):
    """采集数据"""
    index: int
    timestamp: str
    position: str
    corners: int


class CalibrationResult(BaseModel):
    """标定结果"""
    method: str = "Tsai-Lenz"
    data_count: int = 0
    reprojection_error: float = 0.0
    calibration_time: str = ""
    success: bool = True


class VerificationResult(BaseModel):
    """验证结果"""
    is_passed: bool = True
    avg_error: float = 0.0
    max_error: float = 0.0
    std_dev: float = 0.0
    point_count: int = 0


class ErrorData(BaseModel):
    """误差数据"""
    index: int
    error: float
    status: str


class PositionCompare(BaseModel):
    """坐标对比"""
    axis: str
    target: float
    actual: float
    diff: float


class TargetPosition(BaseModel):
    """目标位置"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0


class RobotPose(BaseModel):
    """机械臂末端位姿"""
    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float


class CalibrationData(BaseModel):
    """标定数据组"""
    robot_pose: RobotPose
    image_corners: List[List[float]]
    timestamp: Optional[str] = None


class CalibrationConfig(BaseModel):
    """标定配置"""
    board_type: str = "chessboard"
    board_width: int = 9
    board_height: int = 6
    square_size: float = 25.0  # mm
    capture_count: int = 12
