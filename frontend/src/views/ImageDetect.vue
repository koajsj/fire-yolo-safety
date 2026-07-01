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
      <!-- 上传区 -->
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span class="card-title">第一步：上传图片</span></template>
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png"
            :on-change="onFileChange"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="el-upload__text">将图片拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="upload-tip">支持 jpg / jpeg / png 格式</div>
            </template>
          </el-upload>

          <div v-if="previewUrl" class="preview">
            <div class="preview-label">原图预览</div>
            <el-image :src="previewUrl" fit="contain" class="preview-img" />
          </div>

          <el-button
            type="primary"
            size="large"
            class="detect-btn"
            :loading="loading"
            :disabled="!file || loading"
            @click="handleDetect"
          >
            {{ loading ? '检测中，请稍候…' : '开始检测' }}
          </el-button>
        </el-card>
      </el-col>

      <!-- 结果区 -->
      <el-col :span="14">
        <el-card shadow="never" v-loading="loading" element-loading-text="正在检测，请稍候…">
          <template #header><span class="card-title">第二步：检测结果</span></template>

          <template v-if="result">
            <el-descriptions :column="2" border size="small" class="result-desc">
              <el-descriptions-item label="是否异常">
                <el-tag :type="result.abnormal ? 'danger' : 'success'">
                  {{ result.abnormal ? '存在异常' : '正常' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="风险等级">
                <el-tag :type="riskTag(result.risk_level)">
                  {{ result.risk_level }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="检测目标总数">
                {{ result.num_detections }}
              </el-descriptions-item>
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
              <el-descriptions-item label="检测耗时">
                {{ result.processing_time_ms }} ms
              </el-descriptions-item>
              <el-descriptions-item label="火焰 / 烟雾">
                火焰 {{ result.fire_count }}，烟雾 {{ result.smoke_count }}
              </el-descriptions-item>
              <el-descriptions-item label="抽烟 / 人员">
                抽烟 {{ result.smoking_count }}，人员 {{ result.person_count }}
              </el-descriptions-item>
              <el-descriptions-item label="风险提示" :span="2">
                {{ result.risk_message }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="result-img-wrap">
              <div class="preview-label">检测结果图</div>
              <el-image
                v-if="resultUrl"
                :src="resultUrl"
                fit="contain"
                class="result-img"
                :preview-src-list="[resultUrl]"
              />
              <el-empty v-else description="暂无结果图" :image-size="80" />
            </div>

            <el-table :data="result.detections" size="small" class="det-table">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="class_cn" label="类别" />
              <el-table-column label="置信度">
                <template #default="{ row }">
                  {{ percent(row.confidence) }}
                </template>
              </el-table-column>
              <el-table-column label="状态">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.abnormal ? 'danger' : 'info'">
                    {{ row.abnormal ? '异常' : '正常' }}
                  </el-tag>
                </template>
              </el-table-column>
              <template #empty>
                <el-empty description="未检出目标" :image-size="60" />
              </template>
            </el-table>
          </template>

          <el-empty v-else-if="!loading" description="请上传图片并开始检测" :image-size="120" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { detectImage } from '../api'

const file = ref(null)
const previewUrl = ref('')
const loading = ref(false)
const result = ref(null)

const resultUrl = computed(() => (result.value?.result_file ? `/${result.value.result_file}` : ''))

const defaultResult = {
  detections: [],
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
  result_file: ''
}

const normalizeResult = (data = {}) => ({
  ...defaultResult,
  ...data,
  detections: Array.isArray(data.detections) ? data.detections : [],
  classes_cn: Array.isArray(data.classes_cn) ? data.classes_cn : [],
  top_confidence: Number(data.top_confidence ?? data.max_confidence ?? 0) || 0,
  max_confidence: Number(data.max_confidence ?? data.top_confidence ?? 0) || 0,
  num_detections: Number(data.num_detections || 0),
  fire_count: Number(data.fire_count || 0),
  smoke_count: Number(data.smoke_count || 0),
  smoking_count: Number(data.smoking_count || 0),
  person_count: Number(data.person_count || 0),
  processing_time_ms: Number(data.processing_time_ms || Math.round((data.elapsed || 0) * 1000))
})

const percent = (value) => {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? `${(n * 100).toFixed(1)}%` : '-'
}

const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')
const riskAlertType = (level) => ({ 高风险: 'error', 中风险: 'warning', 低风险: 'success' }[level] || 'info')

const onFileChange = (uploadFile) => {
  if (!uploadFile.raw) {
    ElMessage.warning('图片文件读取失败，请重新选择')
    return
  }
  file.value = uploadFile.raw
  previewUrl.value = URL.createObjectURL(uploadFile.raw)
  result.value = null
}

const handleDetect = async () => {
  if (!file.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  loading.value = true
  result.value = null
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    const res = await detectImage(formData)
    result.value = normalizeResult(res.data)
    ElMessage.success('检测完成')
  } catch (e) {
    ElMessage.error(e.message || '图片检测失败，请检查后端服务和图片格式')
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
.preview {
  margin-top: 16px;
}
.preview-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}
.preview-img,
.result-img {
  width: 100%;
  max-height: 320px;
  background: #f5f7fa;
  border-radius: 6px;
}
.detect-btn {
  width: 100%;
  margin-top: 16px;
}
.result-desc {
  margin-bottom: 16px;
}
.result-img-wrap {
  margin-bottom: 16px;
}
.det-table {
  margin-top: 8px;
}
</style>
