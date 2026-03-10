# 机械臂相关 API 路由
from fastapi import APIRouter, HTTPException
import logging

from app.service import calibration_service

router = APIRouter(prefix="/robot", tags=["机械臂"])

logger = logging.getLogger(__name__)


@router.get("/pose")
async def get_robot_pose():
    """获取机械臂当前位姿"""
    try:
        robot = calibration_service.get_robot_device()
        robot.connect()
        pose = robot.get_current_pose()

        if pose is None:
            raise HTTPException(status_code=400, detail="无法获取机械臂位姿")

        return {
            "code": 200,
            "data": pose.to_dict()
        }
    except Exception as e:
        logger.error(f"获取机械臂位姿失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/move")
async def move_robot(pose: dict):
    """移动机械臂到指定位姿

    Args:
        pose: 目标位姿 {x, y, z, rx, ry, rz}
    """
    try:
        from app.models import RobotPose

        robot = calibration_service.get_robot_device()
        robot.connect()

        # 构建目标位姿
        target_pose = RobotPose(
            x=pose.get("x", 0),
            y=pose.get("y", 0),
            z=pose.get("z", 0),
            rx=pose.get("rx", 0),
            ry=pose.get("ry", 0),
            rz=pose.get("rz", 0)
        )

        robot.move_to(target_pose)

        return {
            "code": 200,
            "message": "移动成功",
            "data": target_pose.model_dump()
        }
    except Exception as e:
        logger.error(f"机械臂移动失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
