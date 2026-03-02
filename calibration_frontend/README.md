# 手眼标定平台 - 前端

基于 Vue3 + Vite + Element Plus 开发的手眼标定可视化引导平台。

## 技术栈

- Vue 3.4+
- Vite 5.0+
- Element Plus 2.5+
- Vue Router 4.2+
- Axios 1.6+

## 项目结构

```
calibration_frontend/
├── index.html          # 入口 HTML
├── package.json        # 项目配置
├── vite.config.js      # Vite 配置
└── src/
    ├── main.js         # 入口 JS
    ├── App.vue         # 根组件
    ├── router/         # 路由配置
    │   └── index.js
    ├── api/            # API 请求封装
    │   └── index.js
    ├── styles/         # 全局样式
    │   └── main.css
    └── views/          # 页面组件
        ├── LearningPage.vue      # 学习示例
        ├── CalibrationPage.vue  # 标定引导
        └── VerificationPage.vue # 标定验证
```

## 安装与运行

### 1. 安装依赖

```bash
cd calibration_frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 功能说明

### 学习示例
- 观看手眼标定流程演示
- 了解标定的4个基本步骤
- 逐步引导学习

### 开始标定
- 设备连接检查
- 数据采集引导
- 自动计算手眼矩阵

### 标定验证
- 重投影验证
- 目标点验证
- 误差分析展示

## 样式规范

- 主色: #1890ff
- 辅助色: #f5222d
- 背景色: #f5f5f5
- 文字色: #333333
- 字体: 微软雅黑 / Inter
- 导航栏高度: 60px
- 侧边栏宽度: 200px
