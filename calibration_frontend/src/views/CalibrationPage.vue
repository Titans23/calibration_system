<template>
  <div class="calibration-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>开始标定</h2>
      <p class="text-secondary">按照以下步骤完成手眼标定</p>
    </div>

    <!-- 标定进度 -->
    <div class="content-card">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="准备" description="检查设备连接" />
        <el-step title="采集" description="采集标定数据" />
        <el-step title="计算" description="计算手眼矩阵" />
        <el-step title="完成" description="标定完成" />
      </el-steps>

      <!-- 步骤1: 准备阶段 -->
      <div v-show="currentStep === 0" class="step-section">
        <div class="instruction-box">
          <h4>准备阶段</h4>
          <p>请确保以下设备已正确连接并准备就绪，点击检查设备后可进行数据采集</p>
        </div>

        <!-- 相机预览 + 机械臂控制 - 步骤1显示 -->
        <div class="preview-section">
          <div class="preview-left">
            <CameraPreview
              ref="cameraPreviewRef1"
              placeholder-text="相机实时预览"
            />
          </div>
          <div class="preview-right">
            <RobotControl :step="10" :rot-step="5" />
          </div>
        </div>

        <div class="device-list">
          <div class="device-item">
            <div class="device-icon">
              <el-icon :size="32"><Camera /></el-icon>
            </div>
            <div class="device-info">
              <h4>工业相机</h4>
              <p class="text-secondary">用于拍摄标定板图像</p>
            </div>
            <div class="device-status">
              <el-tag :type="deviceStatus.camera ? 'success' : 'danger'">
                {{ deviceStatus.camera ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </div>

          <div class="device-item">
            <div class="device-icon">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="device-info">
              <h4>机械臂</h4>
              <p class="text-secondary">提供末端位姿数据</p>
            </div>
            <div class="device-status">
              <el-tag :type="deviceStatus.robot ? 'success' : 'danger'">
                {{ deviceStatus.robot ? '已连接' : '未连接' }}
              </el-tag>
            </div>
          </div>

          <div class="device-item">
            <div class="device-icon">
              <el-icon :size="32"><Picture /></el-icon>
            </div>
            <div class="device-info">
              <h4>标定板</h4>
              <p class="text-secondary">hxw 角点标定板</p>
            </div>
            <div class="device-status">
              <el-tag :type="deviceStatus.board ? 'success' : 'warning'">
                {{ deviceStatus.board ? '已识别' : '待放置' }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="action-buttons">
          <el-button type="primary" size="large" @click="checkDevices" :loading="checking">
            <el-icon><Refresh /></el-icon>
            检查设备
          </el-button>
          <el-button type="primary" size="large" @click="startCalibration" :disabled="!allDevicesReady">
            <el-icon><ArrowRight /></el-icon>
            开始标定
          </el-button>
        </div>
      </div>

      <!-- 步骤2: 数据采集阶段 -->
      <div v-show="currentStep === 1" class="step-section">
        <div class="instruction-box">
          <h4>数据采集</h4>
          <p>移动机械臂到不同位置（x,y,z,rx,ry,rz均需要移动），点击"采集数据"按钮获取标定数据</p>
        </div>

        <!-- 实时预览 + 机械臂控制 -->
        <div class="preview-section">
          <div class="preview-left">
            <CameraPreview
              ref="cameraPreviewRef2"
              placeholder-text="相机实时预览"
            />
          </div>

          <div class="preview-right">
            <RobotControl :step="10" :rot-step="5" />
          </div>
        </div>

        <!-- 采集信息（独立显示） -->
        <div class="capture-info">
          <div class="progress-info">
            <span>已采集: </span>
            <el-tag type="primary">{{ capturedCount }} / {{ requiredCount }}</el-tag>
          </div>
          <div class="progress-bar-container">
            <el-progress
              :percentage="captureProgress"
              :stroke-width="10"
              :show-text="false"
            />
          </div>
          <p class="text-secondary">建议采集 {{ requiredCount }} 组数据以获得最佳精度</p>
        </div>

        <!-- 采集控制 -->
        <div class="capture-controls">
          <el-button type="primary" size="large" @click="captureData" :loading="capturing" :disabled="capturedCount >= requiredCount">
            <el-icon><Camera /></el-icon>
            {{ capturedCount >= requiredCount ? '已采集完成' : '采集数据' }}
          </el-button>
          <el-button size="large" @click="clearData" :disabled="capturedCount === 0">
            <el-icon><Delete /></el-icon>
            清空数据
          </el-button>
        </div>

        <!-- 采集的数据列表 -->
        <div v-if="capturedData.length > 0" class="captured-list">
          <h4>已采集数据</h4>
          <el-table :data="capturedData" style="width: 100%" max-height="200">
            <el-table-column prop="index" label="序号" width="80" />
            <el-table-column prop="timestamp" label="时间" width="180" />
            <el-table-column prop="position" label="机械臂位置" />
            <el-table-column prop="corners" label="检测角点" width="100" />
          </el-table>
        </div>

        <div class="action-buttons">
          <el-button size="large" @click="backToStep1">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <el-button type="primary" size="large" @click="calculateCalibration" :disabled="capturedCount < 3">
            <el-icon><ArrowRight /></el-icon>
            开始计算
          </el-button>
        </div>
      </div>

      <!-- 步骤3: 计算阶段 -->
      <div v-show="currentStep === 2" class="step-section">
        <div class="instruction-box">
          <h4>正在计算</h4>
          <p>系统正在计算手眼标定矩阵，请稍候...</p>
        </div>

        <div class="calculating-section">
          <el-icon class="loading-icon" :size="64"><Loading /></el-icon>
          <p>计算中...</p>
        </div>

        <div class="calc-steps">
          <el-progress :percentage="calcProgress" :stroke-width="15" />
          <div class="calc-status">
            <span v-if="calcProgress < 30">正在识别标定板角点...</span>
            <span v-else-if="calcProgress < 60">正在计算相机内参...</span>
            <span v-else-if="calcProgress < 90">正在求解手眼矩阵...</span>
            <span v-else>计算完成！</span>
          </div>
        </div>
      </div>

      <!-- 步骤4: 完成阶段 -->
      <div v-show="currentStep === 3" class="step-section">
        <div class="result-box" v-if="calibrationSuccess">
          <el-icon :size="48" color="#52c41a"><CircleCheck /></el-icon>
          <h3>标定完成！</h3>
          <p>手眼标定已成功完成，结果已保存</p>
        </div>

        <div class="result-box error" v-else>
          <el-icon :size="48" color="#f5222d"><CircleClose /></el-icon>
          <h3>标定失败</h3>
          <p>{{ errorMessage }}</p>
        </div>

        <!-- 标定结果详情 -->
        <div class="result-details" v-if="calibrationSuccess">
          <h4>标定结果</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="标定方法">{{ calibrationResult.method }}</el-descriptions-item>
            <el-descriptions-item label="数据组数">{{ calibrationResult.data_count }}</el-descriptions-item>
            <!-- <el-descriptions-item label="重投影误差">{{ calibrationResult.reprojection_error }} mm</el-descriptions-item> -->
            <el-descriptions-item label="标定时间">{{ calibrationResult.calibration_time }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="action-buttons">
          <el-button size="large" @click="retryCalibration">
            <el-icon><Refresh /></el-icon>
            重新标定
          </el-button>
          <el-button type="primary" size="large" @click="goToVerification">
            <el-icon><ArrowRight /></el-icon>
            验证结果
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import RobotControl from '../components/RobotControl.vue'
import CameraPreview from '../components/CameraPreview.vue'
import {
  Camera, Connection, Picture, Refresh, ArrowLeft, ArrowRight,
  Delete, Loading, CircleCheck, CircleClose
} from '@element-plus/icons-vue'

const router = useRouter()

// 相机预览组件引用
const cameraPreviewRef1 = ref(null)
const cameraPreviewRef2 = ref(null)

// 当前步骤
const currentStep = ref(0)

// 设备状态
const deviceStatus = reactive({
  camera: false,
  robot: false,
  board: false
})
const checking = ref(false)

// 采集状态
const capturing = ref(false)
const capturedCount = ref(0)
const requiredCount = ref(12)
const capturedData = ref([])

// 计算状态
const calculating = ref(false)
const calcProgress = ref(0)

// 结果状态
const calibrationSuccess = ref(false)
const errorMessage = ref('')
const calibrationResult = reactive({
  method: '',
  data_count: 0,
  reprojection_error: 0,
  calibration_time: ''
})

// 计算进度
const captureProgress = computed(() => {
  return Math.round((capturedCount.value / requiredCount.value) * 100)
})

// 是否所有设备就绪
const allDevicesReady = computed(() => {
  return deviceStatus.camera && deviceStatus.robot && deviceStatus.board
})

// 检查设备 - 调用后端 API
const checkDevices = async () => {
  checking.value = true
  try {
    const res = await api.checkDevices()
    deviceStatus.camera = res.camera
    deviceStatus.robot = res.robot
    deviceStatus.board = res.board
    if (deviceStatus.camera && deviceStatus.robot && deviceStatus.board) {
      ElMessage.success('设备检查完成，所有设备已就绪')
    } else {
      ElMessage.warning('部分设备未就绪，请检查连接')
    }
  } catch (error) {
    ElMessage.error('设备检查失败')
  } finally {
    checking.value = false
  }
}

// 开始标定 - 调用后端 API
const startCalibration = async () => {
  try {
    const res = await api.startCalibration()
    currentStep.value = 1
  } catch (error) {
    ElMessage.error('开始标定失败')
  }
}

// 返回上一步
const backToStep1 = () => {
  currentStep.value = 0
}

// 采集数据 - 调用后端 API
const captureData = async () => {
  if (capturedCount.value >= requiredCount.value) return

  capturing.value = true
  try {
    // 使用当前相机画面进行采集，机器人位姿从后端获取
    const res = await api.captureData({
      robot_pose: null,  // 后端会从机器人获取当前位姿
      image_corners: []
    })

    capturedCount.value++
    capturedData.value.push({
      index: capturedCount.value,
      timestamp: res.timestamp,
      position: res.position,
      corners: res.corners
    })

    ElMessage.success(`已采集第 ${capturedCount.value} 组数据`)
  } catch (error) {
    ElMessage.error('采集数据失败: ' + (error.message || '未知错误'))
  } finally {
    capturing.value = false
  }
}

// 清空数据 - 调用后端 API
const clearData = async () => {
  try {
    await api.clearCalibrationData()
    capturedCount.value = 0
    capturedData.value = []
    ElMessage.info('已清空所有采集数据')
  } catch (error) {
    ElMessage.error('清空数据失败')
  }
}

// 计算标定 - 调用后端 API
const calculateCalibration = async () => {
  currentStep.value = 2
  calculating.value = true
  calcProgress.value = 0

  // 模拟进度条
  const interval = setInterval(() => {
    calcProgress.value += 10
    if (calcProgress.value >= 100) {
      clearInterval(interval)
    }
  }, 200)

  try {
    const res = await api.calculateCalibration()
    calibrationResult.method = res.method
    calibrationResult.data_count = res.data_count
    calibrationResult.reprojection_error = res.reprojection_error
    calibrationResult.calibration_time = res.calibration_time
    calibrationSuccess.value = res.success
    currentStep.value = 3
  } catch (error) {
    calibrationSuccess.value = false
    errorMessage.value = error.message || '计算标定失败'
    currentStep.value = 3
  } finally {
    calculating.value = false
  }
}

// 重新标定
const retryCalibration = async () => {
  try {
    await api.clearCalibrationData()
  } catch (error) {
    // 忽略错误
  }
  capturedCount.value = 0
  capturedData.value = []
  calcProgress.value = 0
  currentStep.value = 0
}

// 跳转验证
const goToVerification = () => {
  router.push('/verification')
}
</script>

<style scoped>
.calibration-page {
  max-width: 1200px;
}

.step-section {
  margin-top: 30px;
}

.device-list {
  margin: 20px 0;
}

.board-config {
  margin: 20px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.board-config h4 {
  margin-bottom: 15px;
}

.device-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 10px;
}

.device-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: #fff;
  border-radius: 8px;
  margin-right: 15px;
}

.device-info {
  flex: 1;
}

.device-info h4 {
  margin-bottom: 4px;
}

.preview-section {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.preview-left {
  flex: 1;
  min-width: 0;
}

.preview-right {
  width: 320px;
  flex-shrink: 0;
}

.preview-container {
  position: relative;
  flex: 1;
  max-width: 640px;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.fps-display {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  color: #0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  font-family: monospace;
}

.capture-info {
  max-width: 600px;
  margin: 20px auto;
}

.progress-bar-container {
  margin: 15px 0;
}

.capture-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin: 20px 0;
}

.captured-list {
  margin-top: 20px;
}

.captured-list h4 {
  margin-bottom: 10px;
}

.calculating-section {
  text-align: center;
  padding: 40px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
  color: var(--primary-color);
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.calc-steps {
  max-width: 500px;
  margin: 30px auto;
}

.calc-status {
  margin-top: 15px;
  text-align: center;
  color: var(--primary-color);
}

.result-box {
  text-align: center;
  padding: 40px;
}

.result-box h3 {
  margin: 15px 0 10px;
}

.result-details {
  max-width: 600px;
  margin: 30px auto;
}

.result-details h4 {
  margin-bottom: 15px;
  text-align: center;
}
</style>
