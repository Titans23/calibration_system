# 相机设备抽象基类
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, Dict
import numpy as np
import logging
import cv2

from app.config import get_camera_config

logger = logging.getLogger(__name__)

class CameraDevice(ABC):
    """相机设备抽象基类，定义相机操作的标准接口"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化相机

        Args:
            config: 相机配置字典，如果为 None 则从 config.yaml 加载
        """
        # 加载配置
        if config is None:
            config = get_camera_config()

        self._connected = False
        self._grabbing = False
        self._exposure = config.get('exposure', 10000.0)
        self._gain = config.get('gain', 1.0)
        self._width = config.get('width', 640)
        self._height = config.get('height', 480)
        self._jpeg_quality = config.get('jpeg_quality', 70)
        self._frame_count = 0

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

    def is_connected(self) -> bool:
        return self._connected

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


    def set_exposure(self, value: float) -> bool:
        self._exposure = value
        return True

    def set_gain(self, value: float) -> bool:
        self._gain = value
        return True

    def get_frame_base64(self) -> Optional[str]:
        """返回模拟的Base64图像"""
        import base64
        import cv2
        frame = self.get_frame()
        if frame is not None:
            # 使用配置的 JPEG 质量编码
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality])
            return base64.b64encode(buffer).decode('utf-8')
        return None

    def detect_calibration_board(self, image: np.ndarray, board_width: int, board_height: int) -> Tuple[bool, Optional[np.ndarray]]:
        """检测标定板

        Args:
            image: 输入图像
            board_width: 棋盘格内角点宽度
            board_height: 棋盘格内角点高度

        Returns:
            (是否成功, 角点数据) - 角点数据shape为(N, 1, 2)
        """
        if image is None or image.size == 0:
            return False, None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(
            gray,
            (board_width, board_height),
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        if ret:
            # 亚像素精度优化
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        return ret, corners

    def save_image(self, image: np.ndarray, filepath: str) -> bool:
        """保存图像"""
        import cv2
        try:
            cv2.imwrite(filepath, image)
            return True
        except Exception:
            return False


class MockCameraDevice(CameraDevice):
    """模拟相机设备，用于测试和开发"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化模拟相机

        Args:
            config: 相机配置字典，如果为 None 则从 config.yaml 加载
        """
        super().__init__(config)

        # 预生成的噪声图像
        self._noise = None
        # 预生成的棋盘格模板
        self._chessboard = None

        logger.info(f"MockCameraDevice 初始化: exposure={self._exposure}, gain={self._gain}, resolution={self._width}x{self._height}")

    def connect(self) -> bool:
        """模拟连接相机"""
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """模拟断开相机"""
        self._connected = False
        self._grabbing = False
        return True

    def start_grabbing(self) -> bool:
        if self._connected:
            self._grabbing = True
            return True
        return False

    def stop_grabbing(self) -> bool:
        self._grabbing = False
        return True
    
    # 用于测试将detect_calibration_board重写为模拟检测功能，返回固定的角点数据
    def detect_calibration_board(self, image: np.ndarray, board_width: int, board_height: int) -> Tuple[bool, Optional[np.ndarray]]:
        """模拟检测标定板

        Args:
            image: 输入图像
            board_width: 棋盘格内角点宽度
            board_height: 棋盘格内角点高度

        Returns:
            (是否成功, 角点数据) - 角点数据shape为(N, 1, 2)
        """
        if image is None or image.size == 0:
            return False, None

        # 返回模拟的角点数据，shape必须为(N, 1, 2)以匹配OpenCV格式
        corners = np.zeros((board_width * board_height, 1, 2))
        for i in range(board_height):
            for j in range(board_width):
                corners[i * board_width + j] = [[j * 20 + 10, i * 20 + 10]]
        return True, corners

    def get_frame(self) -> Optional[np.ndarray]:
        """返回模拟的动态黑白相间图像"""
        if self._connected and self._grabbing:
            self._frame_count += 1

            width = self._width
            height = self._height
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
        
class RealCameraDevice(CameraDevice):
    """真实相机设备，使用 OpenCV 进行操作"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # 图片列表用于测试角点检测
        img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'img')
        self._img_files = sorted([os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith('.jpg')])
        self._img_index = 0
        logger.info(f"RealCameraDevice 初始化: exposure={self._exposure}, gain={self._gain}, resolution={self._width}x{self._height}, test_images={len(self._img_files)}")
    def connect(self) -> bool:
        """模拟连接相机"""
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """模拟断开相机"""
        self._connected = False
        self._grabbing = False
        return True

    def start_grabbing(self) -> bool:
        if self._connected:
            self._grabbing = True
            return True
        return False

    def stop_grabbing(self) -> bool:
        self._grabbing = False
        return True
    
    def get_frame(self) -> Optional[np.ndarray]:
        """每2秒轮流播放测试图片"""
        if self._connected and self._grabbing and self._img_files:
            self._frame_count += 1
            # 每30帧（约1秒，假设30fps）切换一次图片
            if self._frame_count % 5 == 0:
                self._img_index = (self._img_index + 1) % len(self._img_files)
                # logger.info(f"切换到第 {self._img_index + 1}/{len(self._img_files)} 张图片: {os.path.basename(self._img_files[self._img_index])}")

            img_path = self._img_files[self._img_index]
            image = cv2.imread(img_path)
            if image is not None:
                # 压缩图像到配置的分辨率
                image = cv2.resize(image, (self._width, self._height), interpolation=cv2.INTER_AREA)
            return image
        return None