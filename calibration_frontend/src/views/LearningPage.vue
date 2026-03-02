<template>
  <div class="learning-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>学习示例</h2>
      <p class="text-secondary">观看下面的示例视频，了解手眼标定的完整流程</p>
    </div>

    <!-- 学习内容区域 -->
    <div class="content-card">
      <!-- 视频/动画演示区域 -->
      <div class="video-section">
        <div class="video-container">
          <!-- 这里可以放置示例视频或动画 -->
          <div class="video-placeholder">
            <el-icon :size="64"><VideoCamera /></el-icon>
            <p>手眼标定示例演示</p>
            <p class="text-secondary">（请观看下方文字说明了解完整流程）</p>
          </div>
        </div>
      </div>

      <!-- 步骤说明 -->
      <div class="steps-explanation">
        <h3>标定流程说明</h3>

        <el-steps :active="currentStep" finish-status="success" align-center class="step-container">
          <el-step title="步骤1" description="准备工作" />
          <el-step title="步骤2" description="采集数据" />
          <el-step title="步骤3" description="计算标定" />
          <el-step title="步骤4" description="验证结果" />
        </el-steps>

        <!-- 步骤详情 -->
        <div class="step-detail">
          <div v-show="currentStep === 0" class="step-content">
            <h4>准备工作</h4>
            <ul>
              <li>确保相机和机械臂都已正确连接</li>
              <li>将标定板放置在相机视野范围内</li>
              <li>检查系统是否正常供电</li>
              <li>确认标定板平整且无遮挡</li>
            </ul>
          </div>

          <div v-show="currentStep === 1" class="step-content">
            <h4>采集数据</h4>
            <ul>
              <li>移动机械臂到不同位置</li>
              <li>在每个位置拍摄标定板图片</li>
              <li>记录机械臂末端的位姿信息</li>
              <li>建议采集 10-15 组数据以保证精度</li>
            </ul>
          </div>

          <div v-show="currentStep === 2" class="step-content">
            <h4>计算标定</h4>
            <ul>
              <li>系统自动识别标定板角点</li>
              <li>计算相机内参和位姿</li>
              <li>求解手眼矩阵（AX=XB）</li>
              <li>输出标定结果文件</li>
            </ul>
          </div>

          <div v-show="currentStep === 3" class="step-content">
            <h4>验证结果</h4>
            <ul>
              <li>使用新位置的机械臂进行验证</li>
              <li>比较计算值与实际值的误差</li>
              <li>如果误差在允许范围内，标定成功</li>
              <li>否则需要重新进行标定</li>
            </ul>
          </div>
        </div>

        <!-- 步骤切换 -->
        <div class="step-controls">
          <el-button @click="prevStep" :disabled="currentStep === 0">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
          <el-button @click="nextStep" :disabled="currentStep === 3">
            下一步
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 重要提示 -->
      <div class="instruction-box">
        <h4>温馨提示</h4>
        <p>手眼标定是将相机坐标系与机械臂基坐标系关联起来的过程。只有完成正确的标定，机械臂才能准确抓取视觉系统识别到的物体。</p>
      </div>

      <!-- 开始标定按钮 -->
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="goToCalibration">
          <el-icon><Aim /></el-icon>
          开始实操标定
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { VideoCamera, ArrowLeft, ArrowRight, Aim } from '@element-plus/icons-vue'

const router = useRouter()
const currentStep = ref(0)

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 下一步
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

// 跳转到标定页面
const goToCalibration = () => {
  router.push('/calibration')
}
</script>

<style scoped>
.learning-page {
  max-width: 1200px;
}

.video-section {
  margin-bottom: 30px;
}

.video-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #999;
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
}

.video-placeholder p {
  margin-top: 15px;
}

.steps-explanation {
  margin: 30px 0;
}

.steps-explanation h3 {
  margin-bottom: 20px;
}

.step-detail {
  margin-top: 30px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.step-content h4 {
  color: var(--primary-color);
  margin-bottom: 15px;
}

.step-content ul {
  list-style: none;
  padding: 0;
}

.step-content li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
}

.step-content li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--primary-color);
}

.step-controls {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 20px;
}
</style>
