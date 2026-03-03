#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import numpy as np
from scipy.spatial.transform import Rotation as pyR
import cv2

def R_t_to_matrix(R, t):
    """将旋转矩阵R和平移向量t转换为4x4齐次变换矩阵T"""
    if not np.allclose(np.dot(R.T, R), np.eye(3), atol=1e-6):
        raise ValueError("R is not a valid rotation matrix")
    T = np.identity(4, dtype=np.float64)
    T[:3, :3] = R
    T[:3, 3] = t.flatten()
    return T

def rotation_matrix_to_rotvec_angles(R):
    """将3x3旋转矩阵转换为旋转向量（rx, ry, rz）- 适配scipy.Rotation"""
    vec = cv2.Rodrigues(R)[0]  
    return vec.flatten()

def homogeneous_matrix_to_pose(H):
    """将4x4 SE3齐次矩阵转换为TCP坐标（x,y,z,rx,ry,rz）"""
    # 1. 提取平移向量（SE3矩阵的第4列前3个元素）
    x = H[0, 3]
    y = H[1, 3]
    z = H[2, 3]
    
    # 2. 提取旋转矩阵（SE3矩阵的左上3x3子矩阵）
    R = H[:3, :3]
    
    # 3. 将旋转矩阵转换为旋转向量
    rx, ry, rz = rotation_matrix_to_rotvec_angles(R)
    
    # 4. 返回TCP坐标（与原pose格式一致）
    return np.array([x, y, z, rx, ry, rz])

def rotvec_angles_to_rotation_matrix(rx, ry, rz):
    rotation = pyR.from_rotvec([rx, ry, rz])
    return rotation.as_matrix()


def pose_to_homogeneous_matrix(pose):
    x, y, z, rx, ry, rz = pose
    R = rotvec_angles_to_rotation_matrix(rx, ry, rz)
    t = np.array([x, y, z]).reshape(3, 1)
    H = np.eye(4)
    H[:3, :3] = R
    H[:3, 3] = t[:, 0]
    return H


def inverse_transformation_matrix(T):
    R = T[:3, :3]
    t = T[:3, 3]
    # 计算旋转矩阵的逆矩阵
    R_inv = R.T
    # 计算平移向量的逆矩阵
    t_inv = -np.dot(R_inv, t)
    # 构建逆变换矩阵
    T_inv = np.identity(4)
    T_inv[:3, :3] = R_inv
    T_inv[:3, 3] = t_inv
    return T_inv

if __name__ == '__main__':
    pose = np.array([-0.34197907531530347, -0.40991643678033707, 0.5820960974460481, 0.5134278600995639, 3.026726355192581, 0.4132661041519518])
    H = pose_to_homogeneous_matrix(pose)
    print("Homogeneous Matrix:\n", H)
    recovered_pose = homogeneous_matrix_to_pose(H)
    print("Recovered Pose:\n", recovered_pose)