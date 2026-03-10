<template>
  <div class="verification-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>标定验证</h2>
      <p class="text-secondary">验证手眼标定的准确度</p>
    </div>

    <!-- 验证内容 -->
    <div class="content-card">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="选择" description="选择验证方式" />
        <el-step title="执行" description="执行验证" />
        <el-step title="结果" description="查看验证结果" />
      </el-steps>

      <!-- 步骤1: 选择验证方式 -->
      <div v-show="currentStep === 0" class="step-section">
        <div class="instruction-box">
          <h4>验证方式</h4>
          <p>选择一种验证方式来检验标定结果的准确度</p>
        </div>

        <div class="verification-options">
          <el-radio-group v-model="verificationType">
            <el-radio-button value="reprojection">
              <div class="option-content">
                <el-icon :size="32"><Aim /></el-icon>
                <div>
                  <h4>重投影验证</h4>
                  <p class="text-secondary">通过重投影误差评估标定精度</p>
                </div>
              </div>
            </el-radio-button>

            <el-radio-button value="target">
              <div class="option-content">
                <el-icon :size="32"><Position /></el-icon>
                <div>
                  <h4>目标点验证</h4>
                  <p class="text-secondary">移动机械臂到指定位置进行验证</p>
                </div>
              </div>
            </el-radio-button>
          </el-radio-group>
        </div>

        <!-- 标定结果信息 -->
        <div class="calibration-info">
          <h4>当前标定结果</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="标定时间">{{ calibrationInfo.time }}</el-descriptions-item>
            <el-descriptions-item label="数据组数">{{ calibrationInfo.dataCount }}</el-descriptions-item>
            <el-descriptions-item label="重投影误差">{{ calibrationInfo.error }}</el-descriptions-item>
            <el-descriptions-item label="标定方法">{{ calibrationInfo.method }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="action-buttons">
          <el-button type="primary" size="large" @click="startVerification" :disabled="!hasCalibration">
            <el-icon><ArrowRight /></el-icon>
            开始验证
          </el-button>
        </div>
      </div>

      <!-- 步骤2: 执行验证 -->
      <div v-show="currentStep === 1" class="step-section">
        <div class="instruction-box">
          <h4>{{ verificationType === 'reprojection' ? '重投影验证' : '目标点验证' }}</h4>
          <p>{{ verificationType === 'reprojection' ? '系统将计算所有标定数据的重投影误差' : '请移动机械臂到指定位置进行验证' }}</p>
        </div>

        <!-- 重投影验证界面 -->
        <div v-if="verificationType === 'reprojection'" class="reprojection-section">
          <div class="preview-container">
            <div class="preview-placeholder">
              <el-icon :size="48"><VideoCamera /></el-icon>
              <p>标定板图像</p>
            </div>
          </div>

          <div class="verify-controls">
            <el-button type="primary" size="large" @click="runReprojectionVerify" :loading="verifying">
              <el-icon><VideoCamera /></el-icon>
              计算重投影误差
            </el-button>
          </div>
        </div>

        <!-- 目标点验证界面 -->
        <div v-else class="target-section">
          <!-- 相机预览 + 机械臂控制 -->
          <div class="preview-section">
            <div class="preview-left">
              <div class="camera-preview-container">
                <img v-if="cameraFrame" :src="cameraFrame" class="camera-preview" alt="Camera Preview" />
                <div v-else class="preview-placeholder">
                  <el-icon :size="48"><VideoCamera /></el-icon>
                  <p>等待相机连接...</p>
                </div>
              </div>
            </div>
            <div class="preview-right">
              <RobotControl :step="10" :rot-step="5" />
            </div>
          </div>

          <!-- 自动检测模式说明 -->
          <div class="auto-detect-tip">
            <el-alert
              title="目标点验证说明"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                1. 将机械臂末端调整为 RX≈0°, RY≈0°（与基座X、Y轴对齐）<br>
                2. 将标定板平铺在水平桌面上<br>
                3. 点击"自动检测目标点"计算坐标<br>
                4. 确认目标坐标后，点击"确认移动到目标点"或手动输入坐标移动
              </template>
            </el-alert>
          </div>

          <div class="verify-controls auto-detect-btn">
            <el-button type="success" size="large" @click="autoDetectTarget" :loading="detecting">
              <el-icon><Search /></el-icon>
              自动检测目标点
            </el-button>
          </div>

          <!-- 检测结果展示 -->
          <div v-if="detectedTarget" class="detected-result">
            <!-- 姿态对齐提示 -->
            <div v-if="detectedTarget.alignment_tip" class="alignment-tip">
              <el-alert
                :title="detectedTarget.is_aligned ? '姿态已对齐' : '姿态未对齐'"
                :type="detectedTarget.is_aligned ? 'success' : 'warning'"
                :closable="false"
                show-icon
              >
                <template #default>
                  {{ detectedTarget.alignment_tip }}
                </template>
              </el-alert>
            </div>

            <!-- 当前机械臂姿态 -->
            <div class="current-pose">
              <h4>当前机械臂姿态</h4>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="X (mm)">{{ detectedTarget.current_pose?.x }}</el-descriptions-item>
                <el-descriptions-item label="Y (mm)">{{ detectedTarget.current_pose?.y }}</el-descriptions-item>
                <el-descriptions-item label="Z (mm)">{{ detectedTarget.current_pose?.z }}</el-descriptions-item>
                <el-descriptions-item label="RX (°)">{{ detectedTarget.current_pose?.rx }}</el-descriptions-item>
                <el-descriptions-item label="RY (°)">{{ detectedTarget.current_pose?.ry }}</el-descriptions-item>
                <el-descriptions-item label="RZ (°)">{{ detectedTarget.current_pose?.rz }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 目标坐标 -->
            <div class="target-coord">
              <h4>目标坐标（请手动移动机械臂到此位置）</h4>
              <el-descriptions :column="3" border>
                <el-descriptions-item label="X (mm)">
                  <span class="target-value">{{ detectedTarget.target_pose?.x }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="Y (mm)">
                  <span class="target-value">{{ detectedTarget.target_pose?.y }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="Z (mm)">
                  <span class="target-value">{{ detectedTarget.target_pose?.z }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="RX (°)">0</el-descriptions-item>
                <el-descriptions-item label="RY (°)">0</el-descriptions-item>
                <el-descriptions-item label="RZ (°)">{{ detectedTarget.target_pose?.rz }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 一键确认移动按钮 -->
            <div class="confirm-move-btn">
              <el-button type="primary" size="large" @click="confirmAndMove" :loading="moving">
                <el-icon><Position /></el-icon>
                确认移动到目标点
              </el-button>
            </div>

            <!-- 坐标差异说明 -->
            <div class="coord-diff">
              <p class="text-secondary">
                <el-icon><InfoFilled /></el-icon>
                坐标差异: ΔX={{ (detectedTarget.target_pose?.x - detectedTarget.current_pose?.x).toFixed(1) }}mm,
                ΔY={{ (detectedTarget.target_pose?.y - detectedTarget.current_pose?.y).toFixed(1) }}mm,
                ΔZ={{ (detectedTarget.target_pose?.z - detectedTarget.current_pose?.z).toFixed(1) }}mm
              </p>
            </div>
          </div>

          <el-divider v-if="detectedTarget" />

          <div class="target-input" :class="{ 'with-detection': detectedTarget }">
            <h4>手动输入目标点坐标</h4>
            <el-form :model="targetForm" label-width="80px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="X (mm)">
                    <el-input-number v-model="targetForm.x" :min="-500" :max="500" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Y (mm)">
                    <el-input-number v-model="targetForm.y" :min="-500" :max="500" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Z (mm)">
                    <el-input-number v-model="targetForm.z" :min="0" :max="500" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="RX (°)">
                    <el-input-number v-model="targetForm.rx" :min="-180" :max="180" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>

        <div class="action-buttons">
          <el-button size="large" @click="backToStep1">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
        </div>
      </div>

      <!-- 步骤3: 验证结果 -->
      <div v-show="currentStep === 2" class="step-section">
        <!-- 重投影验证结果 -->
        <div v-if="verificationType === 'reprojection'" class="result-section">
          <div class="result-box" :class="{ error: !verificationResult.pass }">
            <el-icon :size="48" :color="verificationResult.pass ? '#52c41a' : '#f5222d'">
              <CircleCheck v-if="verificationResult.pass" />
              <CircleClose v-else />
            </el-icon>
            <h3>{{ verificationResult.pass ? '验证通过' : '验证未通过' }}</h3>
          </div>

          <div class="result-details">
            <h4>验证详情</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="平均误差">
                <el-tag :type="verificationResult.avgError < 0.5 ? 'success' : 'warning'">
                  {{ verificationResult.avgError }} mm
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最大误差">
                <el-tag :type="verificationResult.maxError < 1.0 ? 'success' : 'danger'">
                  {{ verificationResult.maxError }} mm
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="标准差">{{ verificationResult.stdDev }} mm</el-descriptions-item>
              <el-descriptions-item label="验证点数">{{ verificationResult.pointCount }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 误差图表 -->
          <div class="error-chart">
            <h4>误差分布</h4>
            <div class="chart-placeholder">
              <el-table :data="errorData" style="width: 100%" max-height="200">
                <el-table-column prop="index" label="序号" width="80" />
                <el-table-column prop="error" label="误差 (mm)" />
                <el-table-column prop="status" label="状态">
                  <template #default="scope">
                    <el-tag :type="scope.row.error < 0.5 ? 'success' : 'warning'" size="small">
                      {{ scope.row.error < 0.5 ? '合格' : '偏高' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>

        <!-- 目标点验证结果 -->
        <div v-else class="result-section">
          <div class="result-box" :class="{ error: !verificationResult.pass }">
            <el-icon :size="48" :color="verificationResult.pass ? '#52c41a' : '#f5222d'">
              <CircleCheck v-if="verificationResult.pass" />
              <CircleClose v-else />
            </el-icon>
            <h3>{{ verificationResult.pass ? '验证通过' : '验证未通过' }}</h3>
          </div>

          <div class="result-details">
            <h4>坐标对比</h4>
            <el-table :data="positionCompare" style="width: 100%">
              <el-table-column prop="axis" label="轴" />
              <el-table-column prop="target" label="目标值 (mm)" />
              <el-table-column prop="actual" label="实际值 (mm)" />
              <el-table-column prop="diff" label="误差 (mm)">
                <template #default="scope">
                  <el-tag :type="scope.row.diff < 1 ? 'success' : 'danger'" size="small">
                    {{ scope.row.diff }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>

        <div class="action-buttons">
          <el-button size="large" @click="retryVerification">
            <el-icon><Refresh /></el-icon>
            重新验证
          </el-button>
          <el-button type="primary" size="large" @click="finishVerification">
            <el-icon><Check /></el-icon>
            完成
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import RobotControl from '../components/RobotControl.vue'
import {
  ArrowLeft, ArrowRight, VideoCamera, Position, Aim,
  CircleCheck, CircleClose, Refresh, Check, Camera, Search, InfoFilled
} from '@element-plus/icons-vue'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 验证类型
const verificationType = ref('reprojection')

// 是否有标定结果
const hasCalibration = ref(false)

// 标定信息
const calibrationInfo = reactive({
  time: 'N/A',
  dataCount: 0,
  error: 'N/A',
  method: 'N/A'
})

// 目标点表单
const targetForm = reactive({
  x: 100,
  y: 200,
  z: 300,
  rx: 0
})

// 状态
const verifying = ref(false)
const moving = ref(false)
const capturing = ref(false)
const detecting = ref(false)

// 检测到的目标点
const detectedTarget = ref(null)

// 相机预览
const cameraFrame = ref('')
let ws = null

// 初始化 WebSocket 连接
const initSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/camera`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket 已连接')
  }

  ws.onerror = (error) => {
    console.error('WebSocket 连接错误:', error)
  }

  ws.onclose = () => {
    console.log('WebSocket 已断开')
  }

  ws.onmessage = (event) => {
    if (event.data) {
      // 检查是否是 FPS 数据
      if (event.data.startsWith('{"type":"fps"')) {
        // FPS 数据，跳过
      } else {
        cameraFrame.value = event.data
      }
    }
  }
}

// 停止相机流
const stopCameraStream = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

onMounted(() => {
  // 进入页面时启动相机预览
  initSocket()
})

onUnmounted(() => {
  // 离开页面时停止相机预览
  stopCameraStream()
})

// 验证结果
const verificationResult = reactive({
  pass: true,
  avgError: 0,
  maxError: 0,
  stdDev: 0,
  pointCount: 0
})

// 误差数据
const errorData = ref([])

// 坐标对比数据
const positionCompare = ref([])

// 页面加载时获取标定信息
onMounted(async () => {
  try {
    const res = await api.getVerificationInfo()
    calibrationInfo.time = res.time || 'N/A'
    calibrationInfo.dataCount = res.data_count || 0
    calibrationInfo.error = res.error || 'N/A'
    calibrationInfo.method = res.method || 'N/A'
    hasCalibration.value = res.data_count > 0
  } catch (error) {
    hasCalibration.value = false
  }
})

// 返回上一步
const backToStep1 = () => {
  currentStep.value = 0
}

// 开始验证
const startVerification = () => {
  currentStep.value = 1
}

// 运行重投影验证 - 调用后端 API
const runReprojectionVerify = async () => {
  verifying.value = true
  try {
    const res = await api.verifyReprojection()
    const result = res.result
    const errorList = res.error_data

    verificationResult.pass = result.pass
    verificationResult.avgError = result.avg_error
    verificationResult.maxError = result.max_error
    verificationResult.stdDev = result.std_dev
    verificationResult.pointCount = result.point_count

    errorData.value = errorList.map(item => ({
      index: item.index,
      error: item.error,
      status: item.status
    }))

    currentStep.value = 2
    ElMessage.success('验证完成')
  } catch (error) {
    ElMessage.error('验证失败: ' + (error.message || '请先完成标定'))
  } finally {
    verifying.value = false
  }
}


// 自动检测目标点 - 调用后端 API
const autoDetectTarget = async () => {
  detecting.value = true
  try {
    const res = await api.detectTarget()

    detectedTarget.value = res

    // 自动填入目标点表单（使用推荐的目标姿态）
    targetForm.x = res.target_pose.x
    targetForm.y = res.target_pose.y
    targetForm.z = res.target_pose.z
    targetForm.rx = res.target_pose.rx

    ElMessage.success('检测完成，已计算目标点坐标，请确认后手动移动机械臂')
  } catch (error) {
    ElMessage.error('检测失败: ' + (error.message || '请确保标定板在视野内'))
  } finally {
    detecting.value = false
  }
}

// 确认并移动到目标点
const confirmAndMove = async () => {
  moving.value = true
  try {
    await api.moveToTarget({
      x: targetForm.x,
      y: targetForm.y,
      z: targetForm.z,
      rx: targetForm.rx
    })
    ElMessage.success('已移动到目标点')
  } catch (error) {
    ElMessage.error('移动失败')
  } finally {
    moving.value = false
  }
}

// 拍摄验证 - 调用后端 API
const captureVerify = async () => {
  capturing.value = true
  try {
    const res = await api.verifyTarget({
      x: targetForm.x,
      y: targetForm.y,
      z: targetForm.z,
      rx: targetForm.rx
    })

    verificationResult.pass = res.pass
    positionCompare.value = res.position_compare

    currentStep.value = 2
    ElMessage.success('验证完成')
  } catch (error) {
    ElMessage.error('验证失败: ' + (error.message || '请先完成标定'))
  } finally {
    capturing.value = false
  }
}

// 重新验证
const retryVerification = () => {
  currentStep.value = 0
}

// 完成
const finishVerification = () => {
  ElMessage.success('验证流程结束')
  router.push('/learning')
}
</script>

<style scoped>
.verification-page {
  max-width: 1200px;
}

.step-section {
  margin-top: 30px;
}

.verification-options {
  margin: 20px 0;
}

.el-radio-group {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.el-radio-button {
  flex: 1;
  min-width: 280px;
}

:deep(.el-radio-button__inner) {
  width: 100%;
  padding: 20px;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 15px;
  text-align: left;
}

.option-content h4 {
  margin-bottom: 4px;
}

.calibration-info {
  margin-top: 30px;
}

.calibration-info h4 {
  margin-bottom: 15px;
}

.reprojection-section,
.target-section {
  margin-top: 20px;
}

.preview-container {
  width: 100%;
  max-width: 640px;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  margin: 0 auto;
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

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.verify-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.preview-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.preview-left {
  flex: 1;
  min-width: 0;
}

.preview-right {
  width: 320px;
  flex-shrink: 0;
}

.camera-preview-container {
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.auto-detect-tip {
  margin-bottom: 20px;
}

.auto-detect-btn {
  margin-top: 20px;
}

.detected-result {
  max-width: 600px;
  margin: 20px auto;
}

.detected-result h4 {
  margin-bottom: 15px;
  text-align: center;
}

.alignment-tip {
  margin-bottom: 15px;
}

.current-pose,
.target-coord {
  margin-bottom: 20px;
}

.current-pose h4,
.target-coord h4 {
  margin-bottom: 10px;
  text-align: center;
  font-size: 14px;
}

.target-value {
  color: #409eff;
  font-weight: bold;
  font-size: 16px;
}

.confirm-move-btn {
  text-align: center;
  margin: 20px 0;
}

.coord-diff {
  text-align: center;
  margin-top: 10px;
}

.coord-diff .text-secondary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.target-input.with-detection {
  margin-top: 20px;
}

.target-input {
  max-width: 500px;
  margin: 0 auto;
}

.target-input h4 {
  margin-bottom: 15px;
}

.result-section {
  margin-top: 20px;
}

.result-details {
  max-width: 600px;
  margin: 30px auto;
}

.result-details h4 {
  margin-bottom: 15px;
  text-align: center;
}

.error-chart {
  max-width: 600px;
  margin: 30px auto;
}

.error-chart h4 {
  margin-bottom: 15px;
}

.chart-placeholder {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}
</style>
