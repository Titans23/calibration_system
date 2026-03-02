import { createRouter, createWebHistory } from 'vue-router'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: '/learning'
  },
  {
    path: '/learning',
    name: 'Learning',
    component: () => import('../views/LearningPage.vue'),
    meta: { title: '学习示例' }
  },
  {
    path: '/calibration',
    name: 'Calibration',
    component: () => import('../views/CalibrationPage.vue'),
    meta: { title: '开始标定' }
  },
  {
    path: '/verification',
    name: 'Verification',
    component: () => import('../views/VerificationPage.vue'),
    meta: { title: '标定验证' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 更新页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 手眼标定平台` : '手眼标定平台'
  next()
})

export default router
