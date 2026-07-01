import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '首页仪表盘', icon: 'Odometer' }
      },
      {
        path: 'image',
        name: 'ImageDetect',
        component: () => import('../views/ImageDetect.vue'),
        meta: { title: '图片检测', icon: 'Picture' }
      },
      {
        path: 'video',
        name: 'VideoDetect',
        component: () => import('../views/VideoDetect.vue'),
        meta: { title: '视频检测', icon: 'VideoCamera' }
      },
      {
        path: 'camera',
        name: 'CameraDetect',
        component: () => import('../views/CameraDetect.vue'),
        meta: { title: '摄像头检测', icon: 'Monitor' }
      },
      {
        path: 'records',
        name: 'Records',
        component: () => import('../views/Records.vue'),
        meta: { title: '检测记录', icon: 'Document' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      },
      {
        path: 'model',
        name: 'ModelStatus',
        component: () => import('../views/ModelStatus.vue'),
        meta: { title: '模型状态', icon: 'Cpu' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
