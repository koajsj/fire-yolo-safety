<template>
  <div>
    <el-alert
      v-if="running && riskLevel !== '低风险'"
      :type="riskAlertType"
      effect="dark"
      show-icon
      :closable="false"
      class="warn-banner"
    >
      <template #title>
        {{ riskStateText }}：{{ riskMessage }}
      </template>
    </el-alert>

    <el-alert
      v-else-if="running && recoveryText"
      type="success"
      show-icon
      :closable="false"
      class="warn-banner"
      :title="recoveryText"
    />

    <el-card shadow="never">
      <template #header>
        <div class="header-flex">
          <span class="card-title">摄像头实时检测</span>
          <div class="controls">
            <el-button
              v-if="!running"
              type="primary"
              :icon="VideoPlay"
              @click="start"
            >开启摄像头</el-button>
            <el-button
              v-else
              type="danger"
              :icon="VideoPause"
              @click="stop"
            >停止检测</el-button>
            <el-tag v-if="running" type="success" effect="plain">检测中（每 {{ intervalMs }} ms 一帧）</el-tag>
          </div>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :span="12">
          <div class="video-label">摄像头画面</div>
          <div class="video-box">
            <video ref="videoRef" autoplay playsinline muted class="video-el"></video>
            <div v-if="!running" class="video-placeholder">
              <el-icon :size="46"><Monitor /></el-icon>
              <p>点击「开启摄像头」开始实时检测</p>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="video-label">检测结果（带框）</div>
          <div class="video-box">
            <img v-if="resultImg" :src="resultImg" class="video-el" />
            <div v-else class="video-placeholder">
              <el-icon :size="46"><Picture /></el-icon>
              <p>等待检测结果…</p>
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="detect-info" v-if="running">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="当前风险">
            <el-tag :type="riskTag(riskLevel)">{{ riskLevel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标数量">{{ frameStats.num_detections }}</el-descriptions-item>
          <el-descriptions-item label="主要类别">{{ frameStats.top_label }}</el-descriptions-item>
          <el-descriptions-item label="提示">{{ riskMessage }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="detect-info" v-if="running">
        <span>当前检测类别：</span>
        <el-tag
          v-for="c in classesCn"
          :key="c"
          size="small"
          :type="riskLevel === '高风险' ? 'danger' : riskLevel === '中风险' ? 'warning' : 'info'"
          class="cls-tag"
        >{{ c }}</el-tag>
        <span v-if="!classesCn.length" class="empty-text">未检出目标</span>
      </div>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="tip"
      >
        说明：本页使用浏览器摄像头逐帧上传后端检测。首次使用需在浏览器允许摄像头权限；
        检测到异常类别时会自动保存一条记录。若无摄像头，可改用「视频检测」演示。
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { detectFrame } from '../api'

const videoRef = ref()
const running = ref(false)
const resultImg = ref('')
const classesCn = ref([])
const abnormal = ref(false)
const riskLevel = ref('低风险')
const riskMessage = ref('当前未发现明显异常。')
const recoveryText = ref('')
const consecutiveRiskFrames = ref(0)
const frameStats = ref({
  num_detections: 0,
  top_label: '无'
})
const intervalMs = 800 // 每帧检测间隔，避免请求过密

let stream = null
let timer = null
let busy = false // 防止上一帧未返回又发新请求
let cameraErrorShown = false

const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')
const riskAlertType = computed(() => (riskLevel.value === '高风险' ? 'error' : 'warning'))
const riskStateText = computed(() => {
  if (consecutiveRiskFrames.value >= 3) return '持续风险状态'
  return riskLevel.value === '高风险' ? '消防高风险预警' : '消防中风险预警'
})

const resetFrameState = () => {
  resultImg.value = ''
  classesCn.value = []
  abnormal.value = false
  riskLevel.value = '低风险'
  riskMessage.value = '当前未发现明显异常。'
  recoveryText.value = ''
  consecutiveRiskFrames.value = 0
  frameStats.value = { num_detections: 0, top_label: '无' }
}

const start = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    videoRef.value.srcObject = stream
    running.value = true
    recoveryText.value = ''
    cameraErrorShown = false
    ElMessage.success('摄像头已开启')
    timer = setInterval(captureAndDetect, intervalMs)
  } catch (e) {
    ElMessage.error('无法访问摄像头，请检查设备或浏览器权限')
  }
}

const stop = () => {
  running.value = false
  busy = false
  cameraErrorShown = false
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
  if (videoRef.value) {
    videoRef.value.srcObject = null
  }
}

const captureAndDetect = async () => {
  if (!running.value || busy || !videoRef.value || videoRef.value.readyState < 2) return
  busy = true
  try {
    const video = videoRef.value
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7)

    const res = await detectFrame({ image: dataUrl, save: true })
    if (!running.value) return
    resultImg.value = res.data.image
    classesCn.value = Array.isArray(res.data.classes_cn) ? res.data.classes_cn : []
    abnormal.value = Boolean(res.data.abnormal)
    riskLevel.value = res.data.risk_level || '低风险'
    riskMessage.value = res.data.risk_message || '当前未发现明显异常。'
    frameStats.value = {
      num_detections: Number(res.data.num_detections || 0),
      top_label: res.data.top_label || '无'
    }

    if (riskLevel.value === '高风险' || riskLevel.value === '中风险') {
      consecutiveRiskFrames.value += 1
      recoveryText.value = ''
    } else {
      if (consecutiveRiskFrames.value > 0) {
        recoveryText.value = '风险解除，已恢复低风险。'
      }
      consecutiveRiskFrames.value = 0
    }
  } catch (e) {
    if (running.value && !cameraErrorShown) {
      cameraErrorShown = true
      ElMessage.error('实时检测请求失败，请检查后端服务、模型状态或 OpenCV 依赖')
    }
  } finally {
    busy = false
  }
}

onBeforeUnmount(() => {
  stop()
  resetFrameState()
})
</script>

<style scoped>
.warn-banner {
  margin-bottom: 16px;
  font-size: 15px;
}
.header-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.controls {
  display: flex;
  align-items: center;
  gap: 12px;
}
.video-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}
.video-box {
  position: relative;
  width: 100%;
  height: 340px;
  background: #1f2d3d;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-el {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.video-placeholder {
  position: absolute;
  color: #8a97a8;
  text-align: center;
}
.detect-info {
  margin-top: 14px;
  color: #606266;
  font-size: 14px;
}
.cls-tag {
  margin-left: 6px;
}
.empty-text {
  color: #909399;
}
.tip {
  margin-top: 16px;
}
</style>
