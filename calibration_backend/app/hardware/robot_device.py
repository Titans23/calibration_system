# 机器人设备抽象基类
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import numpy as np


class RobotPose:
    """机器人位姿数据类"""

    def __init__(self, x: float = 0, y: float = 0, z: float = 0,
                 rx: float = 0, ry: float = 0, rz: float = 0):
        self.x = x
        self.y = y
        self.z = z
        self.rx = rx
        self.ry = ry
        self.rz = rz

    def to_list(self) -> List[float]:
        """转换为列表 [x, y, z, rx, ry, rz]"""
        return [self.x, self.y, self.z, self.rx, self.ry, self.rz]

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "rx": self.rx,
            "ry": self.ry,
            "rz": self.rz
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'RobotPose':
        """从字典创建"""
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            z=data.get("z", 0),
            rx=data.get("rx", 0),
            ry=data.get("ry", 0),
            rz=data.get("rz", 0)
        )

    @classmethod
    def from_list(cls, data: List[float]) -> 'RobotPose':
        """从列表创建 [x, y, z, rx, ry, rz]"""
        if len(data) >= 6:
            return cls(
                x=data[0], y=data[1], z=data[2],
                rx=data[3], ry=data[4], rz=data[5]
            )
        return cls()


class RobotDevice(ABC):
    """机器人设备抽象基类，定义机械臂操作的标准接口"""

    @abstractmethod
    def connect(self, host: str = "192.168.1.100", port: int = 8080) -> bool:
        """连接机器人

        Args:
            host: 机器人IP地址
            port: 机器人端口

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """断开机器人连接

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查机器人是否已连接

        Returns:
            bool: 机器人是否已连接
        """
        pass

    @abstractmethod
    def get_current_pose(self) -> Optional[RobotPose]:
        """获取当前末端位姿

        Returns:
            Optional[RobotPose]: 当前位姿，失败返回 None
        """
        pass

    @abstractmethod
    def move_to(self, pose: RobotPose, speed: float = 100.0) -> bool:
        """移动到目标位姿

        Args:
            pose: 目标位姿
            speed: 移动速度 (0-100)

        Returns:
            bool: 移动是否成功
        """
        pass

    @abstractmethod
    def move_relative(self, dx: float, dy: float, dz: float,
                     drx: float = 0, dry: float = 0, drz: float = 0,
                     speed: float = 100.0) -> bool:
        """相对移动

        Args:
            dx, dy, dz: 位置增量
            drx, dry, drz: 姿态增量
            speed: 移动速度 (0-100)

        Returns:
            bool: 移动是否成功
        """
        pass

    @abstractmethod
    def get_joint_positions(self) -> Optional[List[float]]:
        """获取关节角度

        Returns:
            Optional[List[float]]: 关节角度列表 [J1, J2, J3, J4, J5, J6]
        """
        pass

    @abstractmethod
    def emergency_stop(self) -> bool:
        """紧急停止

        Returns:
            bool: 是否成功停止
        """
        pass

    @abstractmethod
    def clear_error(self) -> bool:
        """清除错误状态

        Returns:
            bool: 是否成功清除
        """
        pass


class MockRobotDevice(RobotDevice):
    """模拟机器人设备，用于测试和开发"""

    def __init__(self):
        self._connected = False
        self._host = ""
        self._port = 0
        self._current_pose = RobotPose(x=100, y=0, z=200, rx=0, ry=0, rz=0)
        self._joint_positions = [0, -45, 90, 0, 45, 0]  # 角度

    def connect(self, host: str = "192.168.1.100", port: int = 8080) -> bool:
        """模拟连接机器人"""
        self._host = host
        self._port = port
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """模拟断开机器人"""
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def get_current_pose(self) -> Optional[RobotPose]:
        if self._connected:
            return self._current_pose
        return None

    def move_to(self, pose: RobotPose, speed: float = 100.0) -> bool:
        if self._connected:
            self._current_pose = pose
            return True
        return False

    def move_relative(self, dx: float, dy: float, dz: float,
                     drx: float = 0, dry: float = 0, drz: float = 0,
                     speed: float = 100.0) -> bool:
        if self._connected:
            self._current_pose.x += dx
            self._current_pose.y += dy
            self._current_pose.z += dz
            self._current_pose.rx += drx
            self._current_pose.ry += dry
            self._current_pose.rz += drz
            return True
        return False

    def get_joint_positions(self) -> Optional[List[float]]:
        if self._connected:
            return self._joint_positions
        return None

    def emergency_stop(self) -> bool:
        return True

    def clear_error(self) -> bool:
        return True
