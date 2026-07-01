<template>
  <el-row justify="center">
    <el-col :span="14">
      <el-card shadow="never" v-loading="loading">
        <template #header><span class="card-title">系统设置</span></template>

        <el-form label-width="140px" class="settings-form">
          <el-form-item label="置信度阈值">
            <div class="slider-wrap">
              <el-slider
                v-model="confThreshold"
                :min="0.05"
                :max="0.95"
                :step="0.05"
                show-input
              />
            </div>
            <div class="form-tip">
              低于该置信度的检测结果将被过滤。阈值越高，检测越严格但可能漏检；
              阈值越低，检测越敏感但可能误检。推荐 0.25 ~ 0.5。
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
            <el-button @click="reset">恢复默认 (0.25)</el-button>
          </el-form-item>
        </el-form>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="提示：保存后立即生效，后续所有图片、视频、摄像头检测均按新阈值过滤结果。"
        />
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings } from '../api'

const loading = ref(false)
const saving = ref(false)
const confThreshold = ref(0.25)

const load = async () => {
  loading.value = true
  try {
    const res = await getSettings()
    confThreshold.value = Number(res.data.conf_threshold || 0.25)
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

const save = async () => {
  saving.value = true
  try {
    const value = Number(confThreshold.value)
    if (!Number.isFinite(value)) {
      ElMessage.warning('置信度阈值格式不正确')
      return
    }
    await updateSettings({ conf_threshold: value })
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error(e.message || '设置保存失败，请检查后端服务')
  } finally {
    saving.value = false
  }
}

const reset = () => {
  confThreshold.value = 0.25
  save()
}

onMounted(load)
</script>

<style scoped>
.settings-form {
  margin-top: 10px;
}
.slider-wrap {
  width: 100%;
}
.form-tip {
  color: #909399;
  font-size: 12px;
  line-height: 1.7;
  margin-top: 6px;
}
</style>
