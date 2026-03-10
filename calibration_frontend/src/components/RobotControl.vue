<template>
  <div class="robot-control">
    <div class="control-header">
      <h4>机械臂控制</h4>
    </div>

    <!-- 当前位姿显示 -->
    <div class="current-pose" v-if="currentPose">
      <div class="pose-label">当前位姿</div>
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="X">{{ currentPose.x?.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="Y">{{ currentPose.y?.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="Z">{{ currentPose.z?.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="RX">{{ currentPose.rx?.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="RY">{{ currentPose.ry?.toFixed(1) }}</el-descriptions-item>
        <el-descriptions-item label="RZ">{{ currentPose.rz?.toFixed(1) }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 微调按钮 -->
    <div class="fine-tune">
      <div class="pose-label">位置微调 (步长: {{ step }}mm)</div>
      <div class="tune-buttons">
        <div class="button-row">
          <el-button @click="moveByKeyword('px')" :loading="loading">+X</el-button>
          <el-button @click="moveByKeyword('nx')" :loading="loading">-X</el-button>
        </div>
        <div class="button-row">
          <el-button @click="moveByKeyword('py')" :loading="loading">+Y</el-button>
          <el-button @click="moveByKeyword('ny')" :loading="loading">-Y</el-button>
        </div>
        <div class="button-row">
          <el-button @click="moveByKeyword('pz')" :loading="loading">+Z</el-button>
          <el-button @click="moveByKeyword('nz')" :loading="loading">-Z</el-button>
        </div>
      </div>
    </div>

    <!-- 姿态微调 -->
    <div class="fine-tune">
      <div class="pose-label">姿态微调 (步长: {{ rotStep }}°)</div>
      <div class="tune-buttons">
        <div class="button-row">
          <el-button @click="moveByKeyword('prx')" :loading="loading">+RX</el-button>
          <el-button @click="moveByKeyword('nrx')" :loading="loading">-RX</el-button>
        </div>
        <div class="button-row">
          <el-button @click="moveByKeyword('pry')" :loading="loading">+RY</el-button>
          <el-button @click="moveByKeyword('nry')" :loading="loading">-RY</el-button>
        </div>
        <div class="button-row">
          <el-button @click="moveByKeyword('prz')" :loading="loading">+RZ</el-button>
          <el-button @click="moveByKeyword('nrz')" :loading="loading">-RZ</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const props = defineProps({
  step: {
    type: Number,
    default: 10
  },
  rotStep: {
    type: Number,
    default: 5
  }
})

const loading = ref(false)

// 当前位姿
const currentPose = ref(null)

// 通过关键词移动
const moveByKeyword = async (keyword) => {
  loading.value = true
  try {
    const res = await api.moveRobotByKeyword(keyword)
    console.log('移动响应:', res)
    // move_by_keyword 返回 current_pose
    if (res && res.current_pose) {
      currentPose.value = res.current_pose
    } else if (res) {
      // 如果没有 current_pose 字段，尝试刷新位置
      await refreshPose()
    }
    ElMessage.success('移动成功')
  } catch (error) {
    console.error('移动失败:', error)
    ElMessage.error('移动失败')
  } finally {
    loading.value = false
  }
}

// 初始化时获取当前位姿
onMounted(async () => {
  try {
    const res = await api.getRobotPose()
    currentPose.value = res
  } catch (e) {
    console.log('获取机械臂位姿失败，等待操作后更新')
  }
})

// 暴露方法供父组件调用
const refreshPose = async () => {
  // 直接获取当前位置
  try {
    const res = await api.getRobotPose()
    console.log('刷新位置:', res)
    currentPose.value = res
  } catch (e) {
    console.error('获取位置失败:', e)
  }
}

defineExpose({
  refreshPose
})
</script>

<style scoped>
.robot-control {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.control-header h4 {
  margin: 0;
}

.pose-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.current-pose {
  margin-bottom: 15px;
}

.fine-tune {
  margin-bottom: 15px;
}

.tune-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.button-row {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.button-row .el-button {
  flex: 1;
}
</style>
