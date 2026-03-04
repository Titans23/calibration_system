# 相机设备抽象基类
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
import numpy as np


class CameraDevice(ABC):
    """相机设备抽象基类，定义相机操作的标准接口"""

    @abstractmethod
    def connect(self) -> bool:
        """连接相机

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """断开相机连接

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查相机是否已连接

        Returns:
            bool: 相机是否已连接
        """
        pass

    @abstractmethod
    def start_grabbing(self) -> bool:
        """开始采集图像

        Returns:
            bool: 是否成功开始采集
        """
        pass

    @abstractmethod
    def stop_grabbing(self) -> bool:
        """停止采集图像

        Returns:
            bool: 是否成功停止采集
        """
        pass

    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """获取当前帧图像

        Returns:
            Optional[np.ndarray]: 图像数组，失败返回 None
        """
        pass

    @abstractmethod
    def get_frame_base64(self) -> Optional[str]:
        """获取当前帧的 Base64 编码图像

        Returns:
            Optional[str]: Base64 编码的图像字符串，失败返回 None
        """
        pass

    @abstractmethod
    def set_exposure(self, value: float) -> bool:
        """设置曝光时间

        Args:
            value: 曝光时间（微秒）

        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    def set_gain(self, value: float) -> bool:
        """设置增益

        Args:
            value: 增益值

        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    def detect_calibration_board(self, image: np.ndarray, board_width: int, board_height: int) -> Tuple[bool, Any]:
        """检测标定板角点

        Args:
            image: 输入图像
            board_width: 标定板角点列数
            board_height: 标定板角点行数

        Returns:
            Tuple[bool, Any]: (是否检测成功, 角点坐标或None)
        """
        pass

    @abstractmethod
    def save_image(self, image: np.ndarray, filepath: str) -> bool:
        """保存图像到文件

        Args:
            image: 要保存的图像
            filepath: 保存路径

        Returns:
            bool: 保存是否成功
        """
        pass


class MockCameraDevice(CameraDevice):
    """模拟相机设备，用于测试和开发"""

    def __init__(self):
        self._connected = False
        self._grabbing = False
        self._exposure = 10000.0
        self._gain = 1.0

    def connect(self) -> bool:
        """模拟连接相机"""
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """模拟断开相机"""
        self._connected = False
        self._grabbing = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def start_grabbing(self) -> bool:
        if self._connected:
            self._grabbing = True
            return True
        return False

    def stop_grabbing(self) -> bool:
        self._grabbing = False
        return True

    def get_frame(self) -> Optional[np.ndarray]:
        """返回模拟的空白图像"""
        if self._connected and self._grabbing:
            # 返回一个640x480的黑色图像
            return np.zeros((480, 640, 3), dtype=np.uint8)
        return None

    def get_frame_base64(self) -> Optional[str]:
        """返回模拟的Base64图像"""
        import base64
        frame = self.get_frame()
        if frame is not None:
            # 简单处理，实际项目中需要正确编码
            return base64.b64encode(frame.tobytes()).decode('utf-8')
        return None

    def set_exposure(self, value: float) -> bool:
        self._exposure = value
        return True

    def set_gain(self, value: float) -> bool:
        self._gain = value
        return True

    def detect_calibration_board(self, image: np.ndarray, board_width: int, board_height: int) -> Tuple[bool, Any]:
        """模拟检测标定板"""
        # 返回模拟的角点数据
        corners = np.zeros((board_width * board_height, 2))
        for i in range(board_height):
            for j in range(board_width):
                corners[i * board_width + j] = [j * 20 + 10, i * 20 + 10]
        return True, corners

    def save_image(self, image: np.ndarray, filepath: str) -> bool:
        """保存图像"""
        import cv2
        try:
            cv2.imwrite(filepath, image)
            return True
        except Exception:
            return False
