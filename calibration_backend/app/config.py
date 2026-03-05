# 配置加载模块
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

# 全局配置缓存
_config: Optional[Dict[str, Any]] = None


def get_config_path() -> Path:
    """获取配置文件路径

    优先查找项目根目录的 config.yaml
    """
    # 从当前文件向上查找项目根目录
    current = Path(__file__).resolve()
    # calibration_backend/app/config.py -> calibration_backend/app -> calibration_backend -> 项目根目录
    project_root = current.parent.parent.parent
    config_path = project_root / "config.yaml"

    if not config_path.exists():
        # 备用：直接在当前目录查找
        config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"

    return config_path


def load_config() -> Dict[str, Any]:
    """加载配置文件

    Returns:
        Dict[str, Any]: 配置字典
    """
    global _config

    if _config is not None:
        return _config

    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)

    return _config


def get_camera_config() -> Dict[str, Any]:
    """获取相机配置

    Returns:
        Dict[str, Any]: 相机配置字典
    """
    config = load_config()
    return config.get('camera', {})


def get_robot_config() -> Dict[str, Any]:
    """获取机器人配置

    Returns:
        Dict[str, Any]: 机器人配置字典
    """
    config = load_config()
    return config.get('robot', {})


def get_calibration_board_config() -> Dict[str, Any]:
    """获取标定板配置

    Returns:
        Dict[str, Any]: 标定板配置字典
    """
    config = load_config()
    return config.get('calibration_board', {})


def reload_config() -> Dict[str, Any]:
    """重新加载配置

    Returns:
        Dict[str, Any]: 新的配置字典
    """
    global _config
    _config = None
    return load_config()
