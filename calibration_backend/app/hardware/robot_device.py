# 机器人设备抽象基类
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging
import time
import numpy as np
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface

from app.config import get_robot_config

logger = logging.getLogger(__name__)


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
    
    def to_dict_mm(self) -> Dict[str, float]:
        """转换为字典，单位为 mm"""
        return {
            "x": self.x * 1000,
            "y": self.y * 1000,
            "z": self.z * 1000,
            "rx": self.rx,
            "ry": self.ry,
            "rz": self.rz
        }
    def to_list_mm(self) -> List[float]:
        """转换为列表 [x, y, z, rx, ry, rz]，单位为 mm"""
        return [self.x * 1000, self.y * 1000, self.z * 1000, self.rx, self.ry, self.rz]

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

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化模拟机器人

        Args:
            config: 机器人配置字典，如果为 None 则从 config.yaml 加载
        """
        # 加载配置
        if config is None:
            config = get_robot_config()
        self.config = config
        self._connected = False
        self._host = config.get('ip')
        self._port = config.get('port')
        self._default_speed = config.get('default_speed')
        self._current_pose = RobotPose(x=100, y=0, z=200, rx=0, ry=0, rz=0)

    @abstractmethod
    def connect(self, host: str = None, port: int = None) -> bool:
        """连接机器人

        Args:
            host: 机器人IP地址，如果为 None 则使用配置中的IP
            port: 机器人端口，如果为 None 则使用配置中的端口

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


class MockRobotDevice(RobotDevice):
    """模拟机器人设备，用于测试和开发"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        logger.info(f"MockRobotDevice 初始化: ip={self._host}, port={self._port}, default_speed={self._default_speed}")
        
    def connect(self, host: str = None, port: int = None) -> bool:
        """模拟连接机器人

        Args:
            host: 机器人IP，如果为 None 则使用配置中的IP
            port: 机器人端口，如果为 None 则使用配置中的端口
        """
        if self._connected:
            return True
        self._host = host if host is not None else self._host
        self._port = port if port is not None else self._port
        self._connected = True
        self._current_pose = RobotPose(x=0.2, y=0, z=0.2, rx=0, ry=0, rz=0)
        logger.info(f"MockRobot 连接: {self._host}:{self._port}")
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

    def move_to(self, pose: RobotPose, speed: float = 0.1) -> bool:
        if self._connected:
            self._current_pose = pose
            return True
        return False


class UR5eRobotDevice(RobotDevice):
    """UR5e 机械臂设备实现"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        logger.info(f"UR5eRobotDevice 初始化: ip={self._host}, port={self._port}, default_speed={self._default_speed}")

    def connect(self, host: str = None, port: int = None) -> bool:
        """模拟连接机器人

        Args:
            host: 机器人IP，如果为 None 则使用配置中的IP
            port: 机器人端口，如果为 None 则使用配置中的端口
        """
        if self._connected:
            return True
        self._host = host if host is not None else self._host
        cnt = 0
        max_retry = 5
        delay = 5
        while True:
            try:
                logger.info("[connect_rtde] 正在连接机器人...")
                self.rtde_c = RTDEControlInterface(self._host)
                self.rtde_r = RTDEReceiveInterface(self._host)
                logger.info("[connect_rtde] ✅ 连接成功")
                self._connected = True
                logger.info(f"UR5eRobotDevice 连接: {self._host}:{self._port}")
                return True
            except Exception as e:
                logger.info(f"[connect_rtde] ❌ 连接失败: {e}")
                if max_retry and cnt >= max_retry:
                    raise RuntimeError("达到最大重试次数，仍无法连接机器人") from e
                cnt += 1
                logger.info(f"[connect_rtde] {delay}s 后重试...")
                time.sleep(delay)


    def disconnect(self) -> bool:
        """断开机器人"""
        self._connected = False
        self.rtde_c.stopScript()
        return True

    def is_connected(self) -> bool:
        return self._connected

    def get_current_pose(self) -> Optional[RobotPose]:
        if self._connected:
            self._current_pose = RobotPose.from_list(self.rtde_r.getActualTCPPose())  # 得到的单位为m
            return self._current_pose
        return None

    def move_to(self, pose: RobotPose, speed: float = 0.01) -> bool:
        if self._connected:
            self._current_pose = pose
            self.rtde_c.moveL(pose.to_list(), speed=0.2, acceleration=0.2)
            return True
        return False