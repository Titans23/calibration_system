# 手眼标定平台

一个基于 Vue3 + FastAPI 的手眼标定可视化引导平台，帮助普通用户轻松完成工业机器人手眼标定操作。

## 项目概述

手眼标定是工业机器人视觉引导应用中的关键步骤，本平台通过可视化的步骤引导，让非专业人员也能顺利完成手眼标定操作。平台包含学习示例、标定执行和结果验证三大核心功能。

## 技术栈

### 前端
- Vue 3.4+
- Vite 5.0+
- Element Plus 2.5+
- Vue Router 4.2+
- Axios 1.6+

### 后端
- FastAPI 0.109+
- Uvicorn 0.27+
- Pydantic 2.12+
- Python 3.12+

## 项目结构

```
calibration_system/
├── README.md                    # 项目说明文档
├── config.yaml                  # 配置文件
├── calibration_frontend/        # 前端项目
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js              # 入口文件
│       ├── App.vue             # 根组件
│       ├── router/             # 路由配置
│       ├── api/                # API 接口封装
│       ├── styles/             # 全局样式
│       └── views/              # 页面组件
│           ├── LearningPage.vue        # 学习示例
│           ├── CalibrationPage.vue     # 标定引导
│           └── VerificationPage.vue    # 标定验证
└── calibration_backend/        # 后端项目
    ├── requirements.txt
    ├── README.md
    └── app/
        ├── __init__.py
        ├── main.py             # 应用入口
        ├── models/             # 数据模型
        └── routes/             # API 路由
            ├── calibration.py  # 标定接口
            └── verification.py # 验证接口
```

## 功能介绍

### 1. 学习示例
- 观看手眼标定流程演示视频/动画
- 了解标定的四个基本步骤
- 逐步引导学习，图文并茂

### 2. 标定引导
- **设备检查**：自动检测相机、机械臂、标定板连接状态
- **数据采集**：引导用户移动机械臂，采集多组标定数据
- **自动计算**：自动计算手眼变换矩阵
- **结果展示**：展示标定结果和重投影误差

### 3. 标定验证
- **重投影验证**：通过重投影误差评估标定精度
- **目标点验证**：移动机械臂到指定位置，验证标定准确度
- **误差分析**：详细展示误差分布和各项指标

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.8+
- Git

### 安装与运行

#### 1. 克隆项目

```bash
cd calibration_system
```

#### 2. 启动后端服务

```bash
cd calibration_backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m app.main
```

后端服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

#### 3. 启动前端服务

```bash
cd calibration_frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：http://localhost:3000

#### 4. 生产构建

```bash
# 前端构建
cd calibration_frontend
npm run build

# 构建产物将生成在 dist/ 目录
```

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

## 配置说明

### 标定参数

在 `CalibrationPage` 组件中可以配置以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| board_type | chessboard | 标定板类型 |
| board_width | 9 | 标定板宽度角点数 |
| board_height | 6 | 标定板高度角点数 |
| square_size | 25.0 | 方格尺寸 (mm) |
| capture_count | 12 | 建议采集数量 |

### 前端代理配置

在 `vite.config.js` 中可以修改代理配置：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // 后端地址
    changeOrigin: true
  }
}
```

## 页面预览

### 学习示例页面
- 包含标定流程视频演示
- 四个步骤的详细说明
- 上一步/下一步切换按钮

### 标定引导页面
- 步骤条显示当前进度
- 设备状态卡片（相机、机械臂、标定板）
- 实时预览区域和采集控制
- 数据表格展示已采集信息

### 标定验证页面
- 两种验证方式选择
- 目标点坐标输入
- 误差分布表格
- 验证结果展示

## 注意事项

1. **首次使用**：建议先观看学习示例，了解完整流程
2. **设备连接**：确保相机和机械臂正确连接后再进行标定
3. **数据采集**：建议采集 12 组以上数据以获得更好的标定精度
4. **验证环节**：标定完成后务必进行验证，确保精度满足要求

## 扩展开发

### 添加新的页面

1. 在 `src/views/` 下创建新的 Vue 组件
2. 在 `src/router/index.js` 中添加路由配置

### 添加新的 API

1. 在 `calibration_backend/app/routes/` 下创建新的路由文件
2. 在 `calibration_backend/app/main.py` 中注册路由

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！
