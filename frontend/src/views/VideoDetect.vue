<template>
  <div>
    <el-alert
      v-if="result"
      :type="riskAlertType(result.risk_level)"
      effect="dark"
      show-icon
      :closable="false"
      class="warn-banner"
    >
      <template #title>
        {{ result.risk_level }}：{{ result.risk_message }}
      </template>
    </el-alert>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span class="card-title">第一步：上传视频</span></template>
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".mp4,.avi,.mov,.mkv"
            :on-change="onFileChange"
          >
            <el-icon class="upload-icon"><VideoCamera /></el-icon>
            <div class="el-upload__text">将视频拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="upload-tip">支持 mp4 / avi / mov / mkv，建议时长 30 秒内</div>
            </template>
          </el-upload>

          <div v-if="fileName" class="file-name">
            <el-icon><Document /></el-icon> {{ fileName }}
          </div>

          <el-button
            type="primary"
            size="large"
            class="detect-btn"
            :loading="loading"
            :disabled="!file || loading"
            @click="handleDetect"
          >
            {{ loading ? '检测中，请耐心等待…' : '开始检测' }}
          </el-button>

          <el-alert
            v-if="loading"
            type="info"
            :closable="false"
            show-icon
            class="loading-tip"
          >
            视频逐帧检测耗时较长（与时长、设备相关），界面未卡死，请耐心等待结果。
          </el-alert>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card shadow="never" v-loading="loading" element-loading-text="正在逐帧检测视频，请稍候…">
          <template #header><span class="card-title">第二步：检测结果</span></template>

          <template v-if="result">
            <el-descriptions :column="2" border size="small" class="result-desc">
              <el-descriptions-item label="是否异常">
                <el-tag :type="result.abnormal ? 'danger' : 'success'">
                  {{ result.abnormal ? '存在异常' : '正常' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="整体风险等级">
                <el-tag :type="riskTag(result.risk_level)">
                  {{ result.risk_level }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="检测目标总数">{{ result.num_detections }}</el-descriptions-item>
              <el-descriptions-item label="最高置信度">
                {{ percent(result.top_confidence) }}
              </el-descriptions-item>
              <el-descriptions-item label="最高置信度类别">
                {{ result.top_label }}
              </el-descriptions-item>
              <el-descriptions-item label="检测类别">
                <span v-if="result.classes_cn.length">{{ result.classes_cn.join('、') }}</span>
                <span v-else style="color:#909399">未检出目标</span>
              </el-descriptions-item>
              <el-descriptions-item label="总帧数">{{ result.frames }}</el-descriptions-item>
              <el-descriptions-item label="含目标帧数">{{ result.detected_frames }}</el-descriptions-item>
              <el-descriptions-item label="检测耗时">{{ result.processing_time_ms }} ms</el-descriptions-item>
              <el-descriptions-item label="火焰 / 烟雾">火焰 {{ result.fire_count }}，烟雾 {{ result.smoke_count }}</el-descriptions-item>
              <el-descriptions-item label="抽烟 / 人员">抽烟 {{ result.smoking_count }}，人员 {{ result.person_count }}</el-descriptions-item>
              <el-descriptions-item label="风险摘要" :span="2">{{ result.risk_message }}</el-descriptions-item>
            </el-descriptions>

            <div class="preview-label">检测结果视频</div>
            <video
              v-if="resultUrl"
              :src="resultUrl"
              controls
              class="result-video"
              @error="onVideoError"
            ></video>
            <el-empty v-else description="暂无结果视频" :image-size="80" />
            <el-alert
              v-if="videoError"
              type="warning"
              :closable="false"
              show-icon
              class="loading-tip"
            >
              浏览器无法直接播放该视频编码，可在
              <code>results/</code> 目录中找到结果文件，或参考 README 用 FFmpeg 转码为 H.264。
            </el-alert>
          </template>

          <el-empty v-else-if="!loading" description="请上传视频并开始检测" :image-size="120" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { detectVideo } from '../api'

const file = ref(null)
const fileName = ref('')
const loading = ref(false)
const result = ref(null)
const videoError = ref(false)

const resultUrl = computed(() => (result.value?.result_file ? `/${result.value.result_file}` : ''))

const defaultResult = {
  classes_cn: [],
  max_confidence: 0,
  top_confidence: 0,
  top_label: '无',
  abnormal: false,
  risk_level: '低风险',
  num_detections: 0,
  fire_count: 0,
  smoke_count: 0,
  smoking_count: 0,
  person_count: 0,
  processing_time_ms: 0,
  risk_message: '当前未发现明显异常。',
  frames: 0,
  detected_frames: 0,
  result_file: ''
}

const normalizeResult = (data = {}) => ({
  ...defaultResult,
  ...data,
  classes_cn: Array.isArray(data.classes_cn) ? data.classes_cn : [],
  top_confidence: Number(data.top_confidence ?? data.max_confidence ?? 0) || 0,
  max_confidence: Number(data.max_confidence ?? data.top_confidence ?? 0) || 0,
  num_detections: Number(data.num_detections || 0),
  fire_count: Number(data.fire_count || 0),
  smoke_count: Number(data.smoke_count || 0),
  smoking_count: Number(data.smoking_count || 0),
  person_count: Number(data.person_count || 0),
  processing_time_ms: Number(data.processing_time_ms || Math.round((data.elapsed || 0) * 1000)),
  frames: Number(data.frames || 0),
  detected_frames: Number(data.detected_frames || 0)
})

const percent = (value) => {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? `${(n * 100).toFixed(1)}%` : '-'
}

const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')
const riskAlertType = (level) => ({ 高风险: 'error', 中风险: 'warning', 低风险: 'success' }[level] || 'info')

const onFileChange = (uploadFile) => {
  if (!uploadFile.raw) {
    ElMessage.warning('视频文件读取失败，请重新选择')
    return
  }
  file.value = uploadFile.raw
  fileName.value = uploadFile.name
  result.value = null
  videoError.value = false
}

const onVideoError = () => {
  videoError.value = true
}

const handleDetect = async () => {
  if (!file.value) {
    ElMessage.warning('请先上传视频')
    return
  }
  loading.value = true
  result.value = null
  videoError.value = false
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    const res = await detectVideo(formData)
    result.value = normalizeResult(res.data)
    ElMessage.success('视频检测完成')
  } catch (e) {
    ElMessage.error(e.message || '视频检测失败，请检查后端服务和视频格式')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.warn-banner {
  margin-bottom: 16px;
  font-size: 15px;
}
.upload-icon {
  font-size: 46px;
  color: #c0c4cc;
}
.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 6px;
}
.file-name {
  margin-top: 14px;
  color: #606266;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.detect-btn {
  width: 100%;
  margin-top: 16px;
}
.loading-tip {
  margin-top: 14px;
}
.result-desc {
  margin-bottom: 16px;
}
.preview-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}
.result-video {
  width: 100%;
  max-height: 360px;
  background: #000;
  border-radius: 6px;
}
</style>
