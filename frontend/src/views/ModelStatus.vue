<template>
  <el-row justify="center">
    <el-col :span="16">
      <el-card shadow="never" v-loading="loading">
        <template #header>
          <div class="header-flex">
            <span class="card-title">模型状态</span>
            <el-button :icon="Refresh" size="small" @click="load">刷新</el-button>
          </div>
        </template>

        <div class="status-banner" :class="status.loaded ? 'ok' : 'fail'">
          <el-icon :size="30">
            <component :is="status.loaded ? 'SuccessFilled' : 'CircleCloseFilled'" />
          </el-icon>
          <span>{{ status.loaded ? '模型已成功加载，系统可正常检测' : '模型未加载，请检查依赖与权重文件' }}</span>
        </div>

        <el-descriptions :column="1" border class="status-desc">
          <el-descriptions-item label="加载状态">
            <el-tag :type="status.loaded ? 'success' : 'danger'" size="small">
              {{ status.loaded ? '已加载' : '未加载' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模型文件">{{ status.model_path || '-' }}</el-descriptions-item>
          <el-descriptions-item label="模型类型">{{ status.model_kind || '-' }}</el-descriptions-item>
          <el-descriptions-item label="模型来源">{{ status.model_source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="模型说明">
            <el-alert
              :type="status.model_kind === 'best.pt' ? 'success' : 'warning'"
              :closable="false"
              show-icon
              class="inline-alert"
              :title="status.model_notice || '暂无模型说明'"
            />
          </el-descriptions-item>
          <el-descriptions-item label="运行设备">
            <el-tag size="small" type="warning">{{ status.device_label || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度阈值">{{ status.conf_threshold }}</el-descriptions-item>
          <el-descriptions-item label="可识别类别">
            <template v-if="status.class_names && status.class_names.length">
              <el-tag
                v-for="c in status.class_names"
                :key="c"
                size="small"
                class="cls-tag"
              >{{ c }}</el-tag>
            </template>
            <span v-else style="color:#909399">-</span>
          </el-descriptions-item>
          <el-descriptions-item v-if="status.error" label="错误信息">
            <span style="color:#f56c6c">{{ status.error }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="消防类别说明">
            <el-tag
              v-for="item in status.fire_classes"
              :key="item.class_en"
              size="small"
              :type="riskTag(item.risk_level)"
              class="cls-tag"
            >
              {{ item.class_cn }} / {{ item.class_en }} / {{ item.risk_level }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          class="tip"
        >
          说明：系统优先加载 weights/best.pt（自训练消防安全模型）；若不存在则自动回退官方
          yolov8n.pt 以跑通检测流程。训练自己的模型后，将 best.pt 放入 weights 目录并重启后端即可。
        </el-alert>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getModelStatus } from '../api'

const loading = ref(false)
const status = reactive({
  loaded: false,
  model_path: '',
  model_source: '',
  model_kind: '',
  model_notice: '',
  device_label: '',
  conf_threshold: 0,
  class_names: [],
  fire_classes: [],
  error: ''
})

const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')

const load = async () => {
  loading.value = true
  try {
    const res = await getModelStatus()
    Object.assign(status, res.data)
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.header-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.status-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 8px;
  font-size: 15px;
  margin-bottom: 18px;
}
.status-banner.ok {
  background: #f0f9eb;
  color: #67c23a;
}
.status-banner.fail {
  background: #fef0f0;
  color: #f56c6c;
}
.status-desc {
  margin-bottom: 16px;
}
.cls-tag {
  margin: 2px 6px 2px 0;
}
.inline-alert {
  margin: 0;
}
.tip {
  margin-top: 8px;
}
</style>
