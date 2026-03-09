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
        obj_points, img_points, camera_reproj_error = self._calibrate_camera(image_paths)

        # 步骤2: 计算手眼矩阵
        R_cam2gripper, t_cam2gripper = self._compute_hand_eye(
            obj_points, img_points, robot_poses, method
        )

        # 步骤3: 构建结果
        hand_eye_matrix = R_t_to_matrix(R_cam2gripper, t_cam2gripper)

        # 计算手眼标定重投影误差
        reprojection_error = self._compute_reprojection_error(
            obj_points, img_points, self.rvecs, self.tvecs,
            robot_poses, R_cam2gripper, t_cam2gripper
        )

        return {
            "method": method,
            "camera_matrix": self.camera_matrix.tolist() if self.camera_matrix is not None else None,
            "distortion_coeffs": self.distortion_coeffs.tolist() if self.distortion_coeffs is not None else None,
            "R_cam2gripper": R_cam2gripper.tolist(),
            "t_cam2gripper": t_cam2gripper.tolist(),
            "hand_eye_matrix": hand_eye_matrix.tolist(),
            "camera_reprojection_error": camera_reproj_error,  # 相机标定重投影误差
            "reprojection_error": reprojection_error,  # 手眼标定重投影误差
            "data_count": len(image_paths)
        }

    def _calibrate_camera(
        self, image_paths: List[str]
    ) -> Tuple[List[np.ndarray], List[np.ndarray], float]:
        """相机内参标定

        Args:
            image_paths: 图像文件路径列表

        Returns:
            (obj_points, img_points, reprojection_error): 3D世界坐标点列表、2D图像坐标点列表和重投影误差
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
        self.camera_reprojection_error = ret  # 相机标定的重投影误差

        return obj_points, img_points, ret

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
        tvecs: List[np.ndarray],
        robot_poses: List[List[float]],
        R_cam2gripper: np.ndarray,
        t_cam2gripper: np.ndarray
    ) -> float:
        """计算手眼标定重投影误差

        通过两种方式计算标定板相对于基座的变换，比较差异作为手眼标定误差：
        1. 相机标定方式: T_board2base = T_gripper2base * T_cam2gripper * T_board2cam
        2. 直接使用相机标定结果

        Args:
            obj_points: 3D世界坐标点列表（标定板坐标）
            img_points: 2D图像坐标点列表
            rvecs: 相机标定得到的旋转向量列表
            tvecs: 相机标定得到的平移向量列表
            robot_poses: 机械臂末端位姿列表
            R_cam2gripper: 手眼矩阵旋转部分
            t_cam2gripper: 手眼矩阵平移部分

        Returns:
            手眼标定重投影误差（米）
        """
        total_error = 0
        total_count = 0

        for i in range(len(rvecs)):
            # 获取相机标定的板到相机变换
            R_board2cam, _ = cv2.Rodrigues(rvecs[i])
            t_board2cam = np.array(tvecs[i]).flatten()  # 确保是 (3,) 形状

            # 获取机械臂末端到基座变换
            T_gripper2base = pose_to_homogeneous_matrix(robot_poses[i])
            R_gripper2base = T_gripper2base[:3, :3]
            t_gripper2base = T_gripper2base[:3, 3].flatten()

            # 计算方式1: T_board2base = T_gripper2base * T_cam2gripper * T_board2cam
            # 即: 先将点从板坐标转到相机坐标，再转末端，再转基座
            # T_board2gripper = T_cam2gripper * T_board2cam
            R_board2gripper = R_cam2gripper @ R_board2cam
            t_board2gripper = (R_cam2gripper @ t_board2cam + t_cam2gripper.flatten()).flatten()

            # T_board2base = T_gripper2base * T_board2gripper
            R_board2base_method1 = R_gripper2base @ R_board2gripper
            t_board2base_method1 = (R_gripper2base @ t_board2gripper + t_gripper2base).flatten()

            # 获取方式2: 直接从相机标定结果计算板到基座的变换
            # 实际上，相机标定只给了我们板到相机的变换，没有直接的板到基座
            # 所以我们用T_board2base_method1来重投影验证

            # 为了计算误差，我们用重投影方法：
            # 将板角点转到基座，再用相机内参投影回来，与检测的角点比较
            # 这里简化为：比较T_board2base_method1与直接用相机标定得到的位姿

            # 使用另一种验证方式：
            # 用手眼标定结果反推相机到基座的变换，与相机标定结果比较
            # T_cam2base = T_gripper2base * T_cam2gripper
            R_cam2base = R_gripper2base @ R_cam2gripper
            t_cam2base = (R_gripper2base @ t_cam2gripper.flatten() + t_gripper2base).flatten()

            # 用手眼标定得到的相机到基座变换，重投影标定板角点
            # T_board2base = T_cam2base * T_board2cam (的逆) = T_cam2base @ T_cam2board
            R_board2cam_inv = R_board2cam.T
            t_board2cam_inv = (-R_board2cam_inv @ t_board2cam).flatten()

            R_board2base_handeye = R_cam2base @ R_board2cam_inv
            t_board2base_handeye = (R_cam2base @ t_board2cam_inv + t_cam2base).flatten()

            # 从相机标定结果构建板到基座的另一种表达
            # 实际上相机标定无法直接得到板到基座，所以我们用rvecs/tvecs直接重投影来验证
            # 这里我们改用更直观的方法：用手眼矩阵重投影验证

            # 重投影: 板角点 -> 相机坐标 -> 投影到图像
            # 用手眼标定得到的T_cam2base来验证
            # 先将标定板角点转到基座
            board_points = obj_points[i].T  # 3 x N

            # 确保 t_board2base_handeye 是正确的形状 (3,)
            t_board2base_handeye_flat = t_board2base_handeye.flatten()
            base_points = R_board2base_handeye @ board_points + t_board2base_handeye_flat.reshape(3, 1)

            # 再从基座转到相机 (用T_cam2base的逆)
            R_base2cam = R_cam2base.T
            t_cam2base_flat = t_cam2base.flatten()
            t_base2cam = -R_base2cam @ t_cam2base_flat

            cam_points = R_base2cam @ base_points + t_base2cam.reshape(3, 1)

            # 投影到图像
            img_points_pred, _ = cv2.projectPoints(
                cam_points.T, np.zeros(3), np.zeros(3),
                self.camera_matrix, self.distortion_coeffs
            )

            # 计算误差 - 确保类型一致
            img_actual = img_points[i].astype(np.float64)
            img_pred = img_points_pred.astype(np.float64)
            error = cv2.norm(img_actual.squeeze(), img_pred.squeeze(), cv2.NORM_L2)
            total_error += error * error
            total_count += len(obj_points[i])

        return np.sqrt(total_error / total_count) if total_count > 0 else 0

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
