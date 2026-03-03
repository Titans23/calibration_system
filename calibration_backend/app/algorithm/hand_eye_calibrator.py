# coding=utf-8
"""
手眼标定算法类 - 眼在手外
使用采集到的图片信息和机械臂位姿信息计算相机坐标系相对于机械臂基座标的旋转矩阵和平移向量
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from app.algorithm.util import (
    R_t_to_matrix, pose_to_homogeneous_matrix, inverse_transformation_matrix
)


class HandEyeCalibrator:
    """手眼标定器类 - 眼在手外模式"""

    def __init__(self, corner_long: int = 10, corner_short: int = 7, corner_size: float = 0.020):
        """初始化手眼标定器

        Args:
            corner_long: 标定板长边角点数量
            corner_short: 标定板短边角点数量
            corner_size: 标定板方格真实尺寸（米）
        """
        self.corner_long = corner_long
        self.corner_short = corner_short
        self.corner_size = corner_size

        # 标定结果
        self.camera_matrix: Optional[np.ndarray] = None
        self.distortion_coeffs: Optional[np.ndarray] = None
        self.rvecs: Optional[List[np.ndarray]] = None
        self.tvecs: Optional[List[np.ndarray]] = None
        self.R_cam2gripper: Optional[np.ndarray] = None
        self.t_cam2gripper: Optional[np.ndarray] = None
        self.method: str = ""

    def calibrate(
        self,
        image_paths: List[str],
        robot_poses: List[List[float]],
        method: str = "PARK"
    ) -> Dict[str, Any]:
        """执行手眼标定

        Args:
            image_paths: 图像文件路径列表
            robot_poses: 机械臂末端位姿列表 [[x, y, z, rx, ry, rz], ...]
            method: 标定方法，可选 "TSAI", "PARK", "HORAUD", "DANIILidis", "NEGAR"

        Returns:
            标定结果字典
        """
        if len(image_paths) != len(robot_poses):
            raise ValueError("图像数量与机械臂位姿数量不匹配")

        if len(image_paths) < 3:
            raise ValueError("数据不足，需要至少3组数据进行标定")

        # 步骤1: 相机内参标定
        obj_points, img_points = self._calibrate_camera(image_paths)

        # 步骤2: 计算手眼矩阵
        R_cam2gripper, t_cam2gripper = self._compute_hand_eye(
            obj_points, img_points, robot_poses, method
        )

        # 步骤3: 构建结果
        hand_eye_matrix = R_t_to_matrix(R_cam2gripper, t_cam2gripper)

        # 计算重投影误差
        reprojection_error = self._compute_reprojection_error(
            obj_points, img_points, self.rvecs, self.tvecs
        )

        return {
            "method": method,
            "camera_matrix": self.camera_matrix.tolist() if self.camera_matrix is not None else None,
            "distortion_coeffs": self.distortion_coeffs.tolist() if self.distortion_coeffs is not None else None,
            "R_cam2gripper": R_cam2gripper.tolist(),
            "t_cam2gripper": t_cam2gripper.tolist(),
            "hand_eye_matrix": hand_eye_matrix.tolist(),
            "reprojection_error": reprojection_error,
            "data_count": len(image_paths)
        }

    def _calibrate_camera(
        self, image_paths: List[str]
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """相机内参标定

        Args:
            image_paths: 图像文件路径列表

        Returns:
            (obj_points, img_points): 3D世界坐标点列表和2D图像坐标点列表
        """
        # 创建标定板角点3D坐标
        objp = np.zeros(
            (self.corner_long * self.corner_short, 3),
            dtype=np.float32
        )
        objp[:, :2] = np.mgrid[
            0:self.corner_long, 0:self.corner_short
        ].T.reshape(-1, 2)
        objp = self.corner_size * objp

        obj_points = []
        img_points = []
        valid_indices = []

        # 亚像素角点检测参数
        criteria = (
            cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS,
            30,
            0.001
        )

        for i, img_path in enumerate(image_paths):
            img = cv2.imread(img_path)
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            size = gray.shape[::-1]

            # 检测棋盘格角点
            ret, corners = cv2.findChessboardCorners(
                gray,
                (self.corner_long, self.corner_short),
                None
            )

            if ret:
                obj_points.append(objp)
                # 亚像素角点优化
                corners2 = cv2.cornerSubPix(
                    gray, corners, (5, 5), (-1, -1), criteria
                )
                img_points.append(corners2 if corners2 is not None else corners)
                valid_indices.append(i)

        if len(img_points) < 3:
            raise ValueError("有效图像数量不足，需要至少3张")

        # 相机标定
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, size, None, None
        )

        if not ret:
            raise ValueError("相机标定失败")

        self.camera_matrix = mtx
        self.distortion_coeffs = dist
        self.rvecs = rvecs
        self.tvecs = tvecs

        return obj_points, img_points

    def _compute_hand_eye(
        self,
        obj_points: List[np.ndarray],
        img_points: List[np.ndarray],
        robot_poses: List[List[float]],
        method: str = "PARK"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """计算手眼矩阵

        Args:
            obj_points: 3D世界坐标点列表
            img_points: 2D图像坐标点列表
            robot_poses: 机械臂末端位姿列表
            method: 标定方法

        Returns:
            (R_cam2gripper, t_cam2gripper): 旋转矩阵和平移向量
        """
        # 获取相机在标定板坐标系下的位姿
        R_cam2board = []
        t_cam2board = []

        for rvec, tvec in zip(self.rvecs, self.tvecs):
            R, _ = cv2.Rodrigues(rvec)
            R_cam2board.append(R)
            t_cam2board.append(tvec)

        # 将机械臂末端位姿转换为齐次变换矩阵，并求逆
        R_gripper2base = []
        t_gripper2base = []

        for pose in robot_poses:
            T_gripper2base = pose_to_homogeneous_matrix(pose)
            T_base2gripper = inverse_transformation_matrix(T_gripper2base)
            R_gripper2base.append(T_base2gripper[:3, :3])
            t_gripper2base.append(T_base2gripper[:3, 3])

        # 选择标定方法
        method_map = {
            "TSAI": cv2.CALIB_HAND_EYE_TSAI,
            "PARK": cv2.CALIB_HAND_EYE_PARK,
            "HORAUD": cv2.CALIB_HAND_EYE_HORAUD
        }

        if method not in method_map:
            method = "PARK"

        cv2_method = method_map.get(method, cv2.CALIB_HAND_EYE_PARK)
        self.method = method

        # 调用 OpenCV 手眼标定
        R_cam2gripper, t_cam2gripper = cv2.calibrateHandEye(
            R_gripper2base,
            t_gripper2base,
            R_cam2board,
            t_cam2board,
            method=cv2_method
        )

        self.R_cam2gripper = R_cam2gripper
        self.t_cam2gripper = t_cam2gripper

        return R_cam2gripper, t_cam2gripper

    def _compute_reprojection_error(
        self,
        obj_points: List[np.ndarray],
        img_points: List[np.ndarray],
        rvecs: List[np.ndarray],
        tvecs: List[np.ndarray]
    ) -> float:
        """计算重投影误差

        Args:
            obj_points: 3D世界坐标点列表
            img_points: 2D图像坐标点列表
            rvecs: 旋转向量列表
            tvecs: 平移向量列表

        Returns:
            平均重投影误差
        """
        total_error = 0
        total_points = 0

        for i in range(len(obj_points)):
            # 重投影
            imgpoints2, _ = cv2.projectPoints(
                obj_points[i], rvecs[i], tvecs[i],
                self.camera_matrix, self.distortion_coeffs
            )
            error = cv2.norm(img_points[i], imgpoints2, cv2.NORM_L2)
            total_error += error * error
            total_points += len(obj_points[i])

        return np.sqrt(total_error / total_points) if total_points > 0 else 0

    def get_calibration_result(self) -> Optional[Dict[str, Any]]:
        """获取标定结果

        Returns:
            标定结果字典，如果未标定则返回 None
        """
        if self.R_cam2gripper is None or self.t_cam2gripper is None:
            return None

        hand_eye_matrix = R_t_to_matrix(self.R_cam2gripper, self.t_cam2gripper)

        return {
            "method": self.method,
            "camera_matrix": self.camera_matrix.tolist(),
            "distortion_coeffs": self.distortion_coeffs.tolist(),
            "R_cam2gripper": self.R_cam2gripper.tolist(),
            "t_cam2gripper": self.t_cam2gripper.tolist(),
            "hand_eye_matrix": hand_eye_matrix.tolist()
        }
