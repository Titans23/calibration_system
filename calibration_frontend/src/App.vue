<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <header class="main-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="24"><Setting /></el-icon>
          <span class="logo-text">手眼标定平台</span>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          class="header-menu"
          :ellipsis="false"
          :router="true"
        >
          <el-menu-item index="/learning">
            <el-icon><VideoCamera /></el-icon>
            <span>学习示例</span>
          </el-menu-item>
          <el-menu-item index="/calibration">
            <el-icon><Aim /></el-icon>
            <span>开始标定</span>
          </el-menu-item>
          <el-menu-item index="/verification">
            <el-icon><CircleCheck /></el-icon>
            <span>标定验证</span>
          </el-menu-item>
        </el-menu>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧侧边栏 -->
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          :router="true"
        >
          <el-menu-item index="/learning">
            <el-icon><VideoCamera /></el-icon>
            <span>学习示例</span>
          </el-menu-item>
          <el-menu-item index="/calibration">
            <el-icon><Aim /></el-icon>
            <span>开始标定</span>
          </el-menu-item>
          <el-menu-item index="/verification">
            <el-icon><CircleCheck /></el-icon>
            <span>标定验证</span>
          </el-menu-item>
        </el-menu>

        <!-- 状态提示 -->
        <div class="sidebar-status">
          <div class="status-title">系统状态</div>
          <div class="status-item">
            <span class="status-indicator status-success"></span>
            <span>系统就绪</span>
          </div>
        </div>
      </aside>

      <!-- 右侧内容区 -->
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Setting, VideoCamera, Aim, CircleCheck } from '@element-plus/icons-vue'

const route = useRoute()

// 当前激活的菜单（基于路径）
const activeMenu = computed(() => {
  return route.path || '/learning'
})
</script>

<style scoped>
.main-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
  max-width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--primary-color);
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
}

.header-menu {
  border-bottom: none;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-status {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  margin-top: auto;
}

.status-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.status-item {
  display: flex;
  align-items: center;
  font-size: 14px;
}
</style>
