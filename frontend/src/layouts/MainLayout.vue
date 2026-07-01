<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">
          <path d="M12.5 1.5c.6 3.2 2.4 4.6 3.9 6.3 1.6 1.8 2.6 3.6 2.6 6 0 3.9-3.1 6.7-7 6.7s-7-2.8-7-6.7c0-1.8.7-3.3 1.8-4.8.2 1.2.9 2 2 2.3-.7-2.6.3-5 2.1-6.6-.2 1.8.5 2.9 1.5 3.7.8-2.6.2-4.8-.9-6.9z"/>
        </svg>
        <span class="logo-text">消防安全预警</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="menu"
        background-color="#1f2d3d"
        text-color="#c0c9d6"
        active-text-color="#ffffff"
      >
        <el-menu-item
          v-for="item in menus"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-right">
          <el-tag type="success" effect="plain" size="small">
            系统运行中
          </el-tag>
          <span class="user">
            <el-icon><UserFilled /></el-icon>
            本地演示
          </span>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const menus = [
  { path: '/dashboard', title: '首页仪表盘', icon: 'Odometer' },
  { path: '/image', title: '图片检测', icon: 'Picture' },
  { path: '/video', title: '视频检测', icon: 'VideoCamera' },
  { path: '/camera', title: '摄像头检测', icon: 'Monitor' },
  { path: '/records', title: '检测记录', icon: 'Document' },
  { path: '/settings', title: '系统设置', icon: 'Setting' },
  { path: '/model', title: '模型状态', icon: 'Cpu' }
]

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '消防安全风险分析与预警系统')
</script>

<style scoped>
.layout {
  height: 100%;
}
.aside {
  background: #1f2d3d;
  overflow: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  font-size: 17px;
  font-weight: 600;
  background: #18222e;
  letter-spacing: 1px;
}
.menu {
  border-right: none;
}
.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 24px;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
  outline: none;
}
.main {
  padding: 20px;
  background: #f0f2f5;
  overflow-y: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
