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
          <div class="target-input">
            <h4>输入目标点坐标</h4>
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

          <div class="verify-controls">
            <el-button type="primary" size="large" @click="moveToTarget" :loading="moving">
              <el-icon><Position /></el-icon>
              移动到目标点
            </el-button>
            <el-button size="large" @click="captureVerify" :loading="capturing">
              <el-icon><Camera /></el-icon>
              拍摄验证
            </el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import {
  ArrowLeft, ArrowRight, VideoCamera, Position, Aim,
  CircleCheck, CircleClose, Refresh, Check, Camera
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

// 移动到目标点 - 调用后端 API
const moveToTarget = async () => {
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

.verify-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
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
