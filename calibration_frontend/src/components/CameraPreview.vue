<template>
  <div class="camera-preview-wrapper">
    <div class="preview-container">
      <img v-if="cameraFrame" :src="cameraFrame" class="camera-preview" alt="Camera Preview" />
      <div v-else class="preview-placeholder">
        <el-icon :size="48"><VideoCamera /></el-icon>
        <p>{{ placeholderText }}</p>
      </div>
      <div class="fps-display" v-if="showFps && fps > 0">
        <span>FPS: {{ fps }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'

const props = defineProps({
  // 是否显示 FPS
  showFps: {
    type: Boolean,
    default: true
  },
  // 占位文字
  placeholderText: {
    type: String,
    default: '等待相机连接...'
  },
  // WebSocket 路径
  wsPath: {
    type: String,
    default: '/ws/camera'
  },
  // 是否自动连接
  autoConnect: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['connected', 'disconnected', 'error', 'frame'])

const cameraFrame = ref('')
const fps = ref(0)
let ws = null

// 初始化 WebSocket 连接
const initSocket = () => {
  if (!props.autoConnect) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}${props.wsPath}`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('相机 WebSocket 已连接')
    emit('connected')
  }

  ws.onerror = (error) => {
    console.error('相机 WebSocket 连接错误:', error)
    emit('error', error)
  }

  ws.onclose = () => {
    console.log('相机 WebSocket 已断开')
    emit('disconnected')
  }

  ws.onmessage = (event) => {
    if (event.data) {
      // 检查是否是 FPS 数据
      if (event.data.startsWith('{"type":"fps"')) {
        const data = JSON.parse(event.data)
        fps.value = data.value
      } else {
        cameraFrame.value = event.data
        emit('frame', event.data)
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

// 手动连接
const connect = () => {
  if (ws) {
    ws.close()
  }
  initSocket()
}

// 断开连接
const disconnect = () => {
  stopCameraStream()
}

// 组件挂载时自动连接
onMounted(() => {
  if (props.autoConnect) {
    initSocket()
  }
})

// 组件卸载时清理
onUnmounted(() => {
  stopCameraStream()
})

// 暴露方法供父组件使用
defineExpose({
  connect,
  disconnect,
  stopCameraStream,
  initSocket,
  cameraFrame,
  fps
})
</script>

<style scoped>
.camera-preview-wrapper {
  width: 100%;
}

.preview-container {
  position: relative;
  width: 100%;
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

.preview-placeholder p {
  margin-top: 10px;
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
</style>
