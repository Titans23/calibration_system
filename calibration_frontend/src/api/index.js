import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code === 200 || res.success) {
      return res.data
    } else {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  error => {
    const message = error.response?.data?.message || error.message || '网络错误，请稍后重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 封装 API 请求
const api = {
  // ===== 标定相关 =====

  // 获取设备状态
  getCalibrationStatus: () => {
    return request.get('/calibration/status')
  },

  // 检查设备连接
  checkDevices: () => {
    return request.post('/calibration/check-devices')
  },

  // 开始标定
  startCalibration: () => {
    return request.post('/calibration/start')
  },

  // 采集数据
  captureData: (data) => {
    return request.post('/calibration/capture', data)
  },

  // 获取已采集数据
  getCalibrationData: () => {
    return request.get('/calibration/data')
  },

  // 计算手眼矩阵
  calculateCalibration: () => {
    return request.post('/calibration/calculate')
  },

  // 获取标定结果
  getCalibrationResult: () => {
    return request.get('/calibration/result')
  },

  // 清空标定数据
  clearCalibrationData: () => {
    return request.post('/calibration/clear')
  },

  // 机械臂移动关键词
  moveRobotByKeyword: (keyword) => {
    return request.post('/calibration/move_by_keyword', {
      keyword: keyword
    })
  },

  // 获取机械臂当前位姿
  getRobotPose: () => {
    return request.get('/calibration/robot_pose')
  },

  // 移动机械臂到指定位姿
  moveRobot: (pose) => {
    return request.post('/robot/move', pose)
  },

  // ===== 验证相关 =====

  // 获取标定信息
  getVerificationInfo: () => {
    return request.get('/verification/info')
  },

  // 重投影验证
  verifyReprojection: () => {
    return request.post('/verification/reprojection')
  },

  // 目标点验证
  verifyTarget: (position) => {
    return request.post('/verification/target', position)
  },

  // 检测目标点（自动计算3D坐标）
  detectTarget: () => {
    return request.post('/verification/detect-target')
  },

}

export default api
