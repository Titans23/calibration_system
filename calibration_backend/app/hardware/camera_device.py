# 相机设备抽象基类
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

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
        self._frame_count = 0
        # 预生成的噪声图像
        self._noise = None
        # 预生成的棋盘格模板
        self._chessboard = None

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
        """返回模拟的动态黑白相间图像"""
        if self._connected and self._grabbing:
            self._frame_count += 1

            width, height = 640, 480
            square_size = 40

            # 每60帧（约2秒）随机改变方向，使运动更连贯
            if self._frame_count % 60 == 0:
                self._direction = np.random.choice(['left', 'right', 'up', 'down'])

            # 懒加载预生成资源
            if self._chessboard is None:
                # 预生成棋盘格
                x = np.arange(width)
                y = np.arange(height)
                xx, yy = np.meshgrid(x, y)
                self._chessboard = ((((xx // square_size) + (yy // square_size)) % 2) * 255).astype(np.uint8)
                self._direction = 'right'
                self._offset_x = 0
                self._offset_y = 0

            # 使用累加偏移实现平滑移动
            if self._direction == 'right':
                self._offset_x = (self._offset_x + 2) % width
            elif self._direction == 'left':
                self._offset_x = (self._offset_x - 2) % width
            elif self._direction == 'up':
                self._offset_y = (self._offset_y - 2) % height
            elif self._direction == 'down':
                self._offset_y = (self._offset_y + 2) % height

            # 使用 scipy ndimage 进行更平滑的平移
            from scipy import ndimage
            rolled = ndimage.shift(self._chessboard, [self._offset_y, self._offset_x], mode='wrap')
            rolled = rolled.astype(np.uint8)

            # 添加噪声
            if self._noise is None or self._frame_count % 30 == 0:
                self._noise = np.random.randint(-10, 10, (height, width), dtype=np.int16)

            image = np.clip(rolled.astype(np.int16) + self._noise, 0, 255).astype(np.uint8)

            # 转换为3通道
            image = np.stack([image, image, image], axis=2)

            return image
        return None

    def get_frame_base64(self) -> Optional[str]:
        """返回模拟的Base64图像"""
        import base64
        import cv2
        frame = self.get_frame()
        if frame is not None:
            # 使用较低质量编码以提高速度
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return base64.b64encode(buffer).decode('utf-8')
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
