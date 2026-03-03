# 手眼标定平台 - 后端

基于 FastAPI 构建的手眼标定后端服务，提供标定数据采集、计算和验证等功能。

## 技术栈

- FastAPI 0.109+
- Uvicorn 0.27+
- Pydantic 2.12+
- NumPy 1.26+
- OpenCV-Python 4.9+

## 项目结构

```
calibration_backend/
├── requirements.txt          # 依赖包
├── README.md                 # 说明文档
└── app/
    ├── __init__.py          # 模块初始化
    ├── main.py              # 应用入口
    ├── models/              # 数据模型
    │   └── __init__.py
    └── routes/              # API 路由
        ├── calibration.py   # 标定相关 API
        ├── verification.py  # 验证相关 API
        └── __init__.py
```

## 安装与运行

### 1. 创建虚拟环境（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 方式一：直接运行
python -m app.main

# 方式二：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口说明

### 标定接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/calibration/status` | 获取设备状态 |
| POST | `/api/calibration/check-devices` | 检查设备连接 |
| POST | `/api/calibration/start` | 开始标定 |
| POST | `/api/calibration/capture` | 采集标定数据 |
| GET | `/api/calibration/data` | 获取已采集数据 |
| POST | `/api/calibration/calculate` | 计算手眼矩阵 |
| GET | `/api/calibration/result` | 获取标定结果 |
| POST | `/api/calibration/clear` | 清空标定数据 |

### 验证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/verification/info` | 获取标定信息 |
| POST | `/api/verification/reprojection` | 重投影验证 |
| POST | `/api/verification/target` | 目标点验证 |
| POST | `/api/verification/move-to-target` | 移动到目标点 |

## 数据模型

### CalibrationData
```python
{
    "robot_pose": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rx": 0.0,
        "ry": 0.0,
        "rz": 0.0
    },
    "image_corners": [[x, y], ...]
}
```

### CalibrationResult
```python
{
    "method": "Tsai-Lenz",
    "data_count": 12,
    "reprojection_error": 0.012,
    "calibration_time": "2024-01-15 14:30:00",
    "success": True,
    "hand_eye_matrix": [[4x4 matrix]]
}
```

## 配置说明

### 标定配置 (CalibrationConfig)
- `board_type`: 标定板类型 (默认: chessboard)
- `board_width`: 标定板宽度角点数 (默认: 9)
- `board_height`: 标定板高度角点数 (默认: 6)
- `square_size`: 方格尺寸 mm (默认: 25.0)
- `capture_count`: 建议采集数量 (默认: 12)

## 开发说明

### 添加新的路由

1. 在 `app/routes/` 下创建新的路由文件
2. 在 `app/main.py` 中注册路由

示例：
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["新功能"])

@router.get("/example")
async def example():
    return {"message": "示例"}

# 在 main.py 中
app.include_router(router)
```

### 添加新的数据模型

在 `app/models/__init__.py` 中定义 Pydantic 模型：

```python
class NewModel(BaseModel):
    field1: str
    field2: int = 0
```

## 注意事项

1. 当前版本使用内存存储数据，生产环境建议使用数据库
2. 标定计算部分为模拟实现，实际使用时需接入 OpenCV 或其他标定算法
3. 机械臂控制接口为模拟实现，需要根据实际机械臂 SDK 进行适配
