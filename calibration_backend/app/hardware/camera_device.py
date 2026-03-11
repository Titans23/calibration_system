# 相机设备抽象基类
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, Dict
import numpy as np
import logging
import cv2
from ctypes import cast, POINTER, c_ubyte, byref, sizeof, memset

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
        if self._connected:
            logger.info("RealCameraDevice 已连接，跳过重复连接")
            return True
        self._connected = True
        logger.info("RealCameraDevice 连接成功")
        return True

    def disconnect(self) -> bool:
        """模拟断开相机"""
        self._connected = False
        self._grabbing = False
        self.stop_grabbing()
        return True

    def start_grabbing(self) -> bool:
        if self._connected:
            # 如果已经在采集，直接返回成功
            if self._grabbing:
                logger.info("RealCameraDevice 已在采集中，跳过重复启动")
                return True
            self._grabbing = True
            logger.info("RealCameraDevice 开始采集")
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
            # if image is not None:
            #     # 压缩图像到配置的分辨率
            #     image = cv2.resize(image, (self._width, self._height), interpolation=cv2.INTER_AREA)
            return image
        return None

class DobotCameraDevice(CameraDevice):
    """越疆相机设备"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化越疆相机

        Args:
            config: 相机配置字典，如果为 None 则从 config.yaml 加载
        """
        super().__init__(config)

        # 越疆相机SDK相关
        self._cam = None
        self._stOutFrame = None

        # 导入越疆相机SDK
        try:
            from MvImport.MvCameraControl_class import MvCamera, MV_CC_DEVICE_INFO_LIST
            logger.info("越疆相机SDK导入成功")
        except ImportError as e:
            logger.error(f"越疆相机SDK导入失败: {e}")
            raise ImportError("请确保已正确安装越疆相机SDK (MvImport)")

        logger.info(f"DobotCameraDevice 初始化: exposure={self._exposure}, gain={self._gain}, resolution={self._width}x{self._height}")

    def connect(self) -> bool:
        """连接越疆相机

        Returns:
            bool: 连接是否成功
        """
        try:
            # 如果已经连接，直接返回成功
            if self._connected and self._cam is not None:
                logger.info("越疆相机已连接，跳过重复连接")
                return True

            from MvImport.MvCameraControl_class import (
                MvCamera, MV_CC_DEVICE_INFO_LIST, MV_CC_DEVICE_INFO,
                MV_GIGE_DEVICE, MV_USB_DEVICE, MV_ACCESS_Exclusive
            )

            # 搜索设备
            deviceList = MV_CC_DEVICE_INFO_LIST()
            ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)

            if ret != 0 or deviceList.nDeviceNum == 0:
                logger.error(f"未找到相机! 错误码: [0x{ret:x}]")
                return False

            logger.info(f"成功找到 {deviceList.nDeviceNum} 个设备，正在连接...")

            # 初始化相机对象
            self._cam = MvCamera()
            stDeviceInfo = cast(deviceList.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
            ret = self._cam.MV_CC_CreateHandle(stDeviceInfo)
            if ret != 0:
                logger.error(f"创建设备句柄失败! [0x{ret:x}]")
                return False

            # 打开设备
            ret = self._cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                logger.error(f"打开设备失败! [0x{ret:x}]")
                return False

            # 初始化相机参数
            self._init_camera_params()

            self._connected = True
            logger.info("越疆相机已成功连接")
            return True

        except Exception as e:
            logger.error(f"连接越疆相机失败: {e}")
            return False

    def _init_camera_params(self) -> bool:
        """初始化相机参数

        Returns:
            bool: 是否成功
        """
        try:
            # 设置为连续取流模式
            ret = self._cam.MV_CC_SetEnumValue("TriggerMode", 0)
            if ret != 0:
                logger.warning(f"设置触发模式失败! [0x{ret:x}]")

            # 关闭自动曝光，使用手动模式
            ret = self._cam.MV_CC_SetEnumValue("ExposureAuto", 0)
            if ret != 0:
                logger.warning(f"关闭自动曝光失败! [0x{ret:x}]")

            # 设置曝光时间
            if self._exposure is not None:
                ret = self._cam.MV_CC_SetFloatValue("ExposureTime", float(self._exposure))
                if ret != 0:
                    logger.warning(f"设置曝光时间失败! [0x{ret:x}]")

            # 设置增益
            if self._gain is not None:
                ret = self._cam.MV_CC_SetFloatValue("Gain", float(self._gain))
                if ret != 0:
                    logger.warning(f"设置增益失败! [0x{ret:x}]")

            logger.info("越疆相机参数初始化完成")
            return True

        except Exception as e:
            logger.error(f"初始化相机参数失败: {e}")
            return False

    def disconnect(self) -> bool:
        """断开越疆相机连接

        Returns:
            bool: 断开是否成功
        """
        try:
            if not self._connected or self._cam is None:
                return True

            # 如果正在采集，先停止
            if self._grabbing:
                self.stop_grabbing()

            # 关闭设备
            ret = self._cam.MV_CC_CloseDevice()
            if ret != 0:
                logger.error(f"关闭设备失败! [0x{ret:x}]")
                return False

            # 销毁句柄
            ret = self._cam.MV_CC_DestroyHandle()
            if ret != 0:
                logger.error(f"销毁句柄失败! [0x{ret:x}]")
                return False

            self._connected = False
            self._cam = None
            logger.info("越疆相机已安全关闭")
            return True

        except Exception as e:
            logger.error(f"断开越疆相机失败: {e}")
            return False

    def start_grabbing(self) -> bool:
        """开始采集图像

        Returns:
            bool: 是否成功开始采集
        """
        try:
            if not self._connected or self._cam is None:
                logger.error("相机未连接，无法开始采集")
                return False

            # 如果已经在采集，直接返回成功
            if self._grabbing:
                logger.info("越疆相机已在采集中，跳过重复启动")
                return True

            # 开始取流
            ret = self._cam.MV_CC_StartGrabbing()
            if ret != 0:
                logger.error(f"开始取流失败! [0x{ret:x}]")
                return False

            # 初始化帧结构
            from MvImport.MvCameraControl_class import MV_FRAME_OUT
            self._stOutFrame = MV_FRAME_OUT()
            memset(byref(self._stOutFrame), 0, sizeof(self._stOutFrame))

            self._grabbing = True
            logger.info("越疆相机开始采集")
            return True

        except Exception as e:
            logger.error(f"开始采集失败: {e}")
            return False

    def stop_grabbing(self) -> bool:
        """停止采集图像

        Returns:
            bool: 是否成功停止采集
        """
        try:
            if not self._grabbing or self._cam is None:
                return True

            ret = self._cam.MV_CC_StopGrabbing()
            if ret != 0:
                logger.error(f"停止取流失败! [0x{ret:x}]")
                return False

            self._grabbing = False
            self._stOutFrame = None
            logger.info("越疆相机停止采集")
            return True

        except Exception as e:
            logger.error(f"停止采集失败: {e}")
            return False

    def get_frame(self) -> Optional[np.ndarray]:
        """获取当前帧图像

        Returns:
            Optional[np.ndarray]: 图像数组，失败返回 None
        """
        try:
            if not self._grabbing or self._cam is None or self._stOutFrame is None:
                return None

            # 获取一帧图像
            ret = self._cam.MV_CC_GetImageBuffer(self._stOutFrame, 1000)
            if ret != 0:
                return None

            try:
                # 获取图像参数
                nHeight = self._stOutFrame.stFrameInfo.nHeight
                nWidth = self._stOutFrame.stFrameInfo.nWidth
                nFrameLen = self._stOutFrame.stFrameInfo.nFrameLen

                # 从内存指针读取数据
                pData = cast(self._stOutFrame.pBufAddr, POINTER(c_ubyte * nFrameLen)).contents
                img_data = np.frombuffer(pData, dtype=np.uint8)

                # 根据数据大小判断图像格式并重构图像
                if nFrameLen == nHeight * nWidth * 3:
                    # RGB 格式 (3 通道) - 转换为BGR供OpenCV使用
                    img = img_data.reshape((nHeight, nWidth, 3))
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                elif nFrameLen == nHeight * nWidth:
                    # 灰度或 Bayer 格式
                    img = img_data.reshape((nHeight, nWidth))
                    # 转换为3通道
                    img = np.stack([img, img, img], axis=2)
                else:
                    # 其他格式
                    logger.warning(f"未知图像格式: {nFrameLen} bytes for {nWidth}x{nHeight}")
                    img = None

                return img.copy() if img is not None else None

            finally:
                # 释放缓存
                self._cam.MV_CC_FreeImageBuffer(self._stOutFrame)

        except Exception as e:
            logger.error(f"获取图像帧失败: {e}")
            return None

    def set_exposure(self, value: float) -> bool:
        """设置曝光时间

        Args:
            value: 曝光时间（微秒）

        Returns:
            bool: 是否成功
        """
        try:
            if self._cam is None or not self._connected:
                return False

            ret = self._cam.MV_CC_SetFloatValue("ExposureTime", float(value))
            if ret != 0:
                logger.error(f"设置曝光时间失败! [0x{ret:x}]")
                return False

            self._exposure = value
            logger.info(f"曝光时间已设置为: {value} 微秒")
            return True

        except Exception as e:
            logger.error(f"设置曝光时间失败: {e}")
            return False

    def set_gain(self, value: float) -> bool:
        """设置增益

        Args:
            value: 增益值（dB）

        Returns:
            bool: 是否成功
        """
        try:
            if self._cam is None or not self._connected:
                return False

            ret = self._cam.MV_CC_SetFloatValue("Gain", float(value))
            if ret != 0:
                logger.error(f"设置增益失败! [0x{ret:x}]")
                return False

            self._gain = value
            logger.info(f"增益已设置为: {value} dB")
            return True

        except Exception as e:
            logger.error(f"设置增益失败: {e}")
            return False

    def __del__(self):
        """析构函数，确保资源被释放"""
        if self._connected:
            self.disconnect()
