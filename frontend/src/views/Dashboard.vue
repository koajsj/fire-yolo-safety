<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="6" v-for="card in cards" :key="card.label">
        <div class="stat-card" :class="card.className">
          <div class="stat-icon">
            <el-icon :size="32"><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" class="score-card">
      <div class="score-main">
        <div>
          <div class="score-label">今日安全指数</div>
          <div class="score-value" :class="scoreClass">{{ safeScore(stats.safety_score) }}</div>
        </div>
        <el-progress
          type="dashboard"
          :percentage="safeScore(stats.safety_score)"
          :color="scoreColor"
          :width="116"
        />
      </div>
      <div class="risk-summary">
        <div class="risk-item high">
          <span>高风险</span>
          <b>{{ stats.high_risk_total }}</b>
        </div>
        <div class="risk-item medium">
          <span>中风险</span>
          <b>{{ stats.medium_risk_total }}</b>
        </div>
        <div class="risk-item low">
          <span>低风险</span>
          <b>{{ stats.low_risk_total }}</b>
        </div>
        <div class="risk-item">
          <span>平均耗时</span>
          <b>{{ stats.avg_processing_time_ms }} ms</b>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="info-bar">
      <div class="info-item">
        <el-icon><Cpu /></el-icon>
        <span>当前模型：<b>{{ stats.model_source || '未加载' }}</b></span>
      </div>
      <el-divider direction="vertical" />
      <div class="info-item">
        <el-icon><Monitor /></el-icon>
        <span>运行设备：<b>{{ stats.device_label || '未知' }}</b></span>
      </div>
    </el-card>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">风险等级分布</span></template>
          <div v-if="hasRisk" ref="riskRef" class="chart"></div>
          <el-empty v-else description="暂无风险数据" :image-size="90" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">检测类别分布</span></template>
          <div v-if="hasClass" ref="pieRef" class="chart"></div>
          <el-empty v-else description="暂无检测数据" :image-size="90" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">最近 7 天检测趋势</span></template>
          <div v-if="hasTrend" ref="lineRef" class="chart"></div>
          <el-empty v-else description="暂无检测数据" :image-size="90" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header><span class="card-title">检测方式占比</span></template>
          <div v-if="hasType" ref="typeRef" class="chart"></div>
          <el-empty v-else description="暂无检测数据" :image-size="90" />
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="chart-row">
      <template #header><span class="card-title">最近检测记录</span></template>
      <el-table :data="stats.recent" size="small" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTag(row.detect_type)">
              {{ typeText(row.detect_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="riskTag(row.risk_level)">
              {{ row.risk_level || '低风险' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="classes" label="类别" show-overflow-tooltip>
          <template #default="{ row }">{{ row.classes || '未检出' }}</template>
        </el-table-column>
        <el-table-column label="目标数" width="80">
          <template #default="{ row }">{{ row.num_detections || 0 }}</template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">{{ row.processing_time_ms || 0 }} ms</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <template #empty>
          <el-empty description="暂无记录" :image-size="70" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboard } from '../api'

const loading = ref(false)
const stats = reactive({
  total: 0,
  today_total: 0,
  abnormal_total: 0,
  safety_score: 100,
  high_risk_total: 0,
  medium_risk_total: 0,
  low_risk_total: 0,
  avg_processing_time_ms: 0,
  class_count: {},
  type_count: {},
  risk_count: {},
  daily_trend: [],
  recent: [],
  model_source: '',
  device_label: ''
})

const pieRef = ref()
const lineRef = ref()
const typeRef = ref()
const riskRef = ref()
let pieChart, lineChart, typeChart, riskChart

const safeNumber = (value, fallback = 0) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

const safeScore = (value) => Math.max(0, Math.min(100, safeNumber(value, 100)))

const cards = computed(() => [
  { label: '检测总次数', value: stats.total || 0, icon: 'DataLine', className: 'blue' },
  { label: '今日检测', value: stats.today_total || 0, icon: 'Calendar', className: 'green' },
  { label: '异常检测次数', value: stats.abnormal_total || 0, icon: 'WarnTriangleFilled', className: 'red' },
  { label: '检测类别数', value: Object.keys(stats.class_count || {}).length, icon: 'Collection', className: 'orange' }
])

const scoreClass = computed(() => {
  const score = safeScore(stats.safety_score)
  if (score < 60) return 'danger'
  if (score < 80) return 'warning'
  return 'success'
})
const scoreColor = computed(() => ({ danger: '#f56c6c', warning: '#e6a23c', success: '#67c23a' }[scoreClass.value]))

const hasClass = computed(() => Object.values(stats.class_count || {}).some((v) => Number(v) > 0))
const hasTrend = computed(() => (stats.daily_trend || []).length > 0)
const hasType = computed(() => Object.values(stats.type_count || {}).some((v) => Number(v) > 0))
const hasRisk = computed(() => Object.values(stats.risk_count || {}).some((v) => Number(v) > 0))

const typeText = (t) => ({ image: '图片', video: '视频', camera: '摄像头' }[t] || t || '-')
const typeTag = (t) => ({ image: '', video: 'warning', camera: 'success' }[t] || 'info')
const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')

const normalizeDashboard = (data = {}) => ({
  ...data,
  total: safeNumber(data.total),
  today_total: safeNumber(data.today_total),
  abnormal_total: safeNumber(data.abnormal_total),
  safety_score: safeScore(data.safety_score),
  high_risk_total: safeNumber(data.high_risk_total),
  medium_risk_total: safeNumber(data.medium_risk_total),
  low_risk_total: safeNumber(data.low_risk_total),
  avg_processing_time_ms: safeNumber(data.avg_processing_time_ms),
  class_count: data.class_count || {},
  type_count: data.type_count || {},
  risk_count: data.risk_count || {},
  daily_trend: Array.isArray(data.daily_trend) ? data.daily_trend : [],
  recent: Array.isArray(data.recent) ? data.recent : []
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDashboard()
    Object.assign(stats, normalizeDashboard(res.data))
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

const renderCharts = () => {
  if (hasRisk.value && riskRef.value) {
    riskChart = riskChart || echarts.init(riskRef.value)
    riskChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      color: ['#f56c6c', '#e6a23c', '#67c23a'],
      series: [{ type: 'pie', radius: ['38%', '62%'], center: ['50%', '45%'], data: ['高风险', '中风险', '低风险'].map((name) => ({ name, value: stats.risk_count[name] || 0 })) }]
    })
  }

  if (hasClass.value && pieRef.value) {
    pieChart = pieChart || echarts.init(pieRef.value)
    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      color: ['#f56c6c', '#e6a23c', '#67c23a', '#409eff', '#909399', '#3aa1ff'],
      series: [{ type: 'pie', radius: ['38%', '62%'], center: ['50%', '45%'], label: { formatter: '{b}\n{c}' }, data: Object.entries(stats.class_count).map(([name, value]) => ({ name, value })) }]
    })
  }

  if (hasTrend.value && lineRef.value) {
    lineChart = lineChart || echarts.init(lineRef.value)
    lineChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 30 },
      xAxis: { type: 'category', data: stats.daily_trend.map((d) => String(d.day || '').slice(5)) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.18 }, itemStyle: { color: '#409eff' }, data: stats.daily_trend.map((d) => d.count || 0) }]
    })
  }

  if (hasType.value && typeRef.value) {
    typeChart = typeChart || echarts.init(typeRef.value)
    typeChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      color: ['#409eff', '#e6a23c', '#67c23a'],
      series: [{ type: 'pie', radius: '60%', center: ['50%', '45%'], data: Object.entries(stats.type_count).map(([k, v]) => ({ name: typeText(k), value: v })) }]
    })
  }
}

const handleResize = () => {
  ;[pieChart, lineChart, typeChart, riskChart].forEach((chart) => chart && chart.resize())
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  ;[pieChart, lineChart, typeChart, riskChart].forEach((chart) => chart && chart.dispose())
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 104px;
  padding: 20px;
  border-radius: 8px;
  color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
}
.stat-card.blue { background: linear-gradient(135deg, #409eff, #2b6fd6); }
.stat-card.green { background: linear-gradient(135deg, #67c23a, #2f9e5f); }
.stat-card.red { background: linear-gradient(135deg, #f56c6c, #d93b3b); }
.stat-card.orange { background: linear-gradient(135deg, #e6a23c, #d77a1f); }
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  opacity: 0.92;
}
.score-card {
  margin-bottom: 16px;
}
.score-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
.score-main {
  display: flex;
  align-items: center;
  gap: 22px;
}
.score-label {
  color: #606266;
  font-size: 14px;
  margin-bottom: 6px;
}
.score-value {
  font-size: 42px;
  line-height: 1;
  font-weight: 800;
}
.score-value.success { color: #67c23a; }
.score-value.warning { color: #e6a23c; }
.score-value.danger { color: #f56c6c; }
.risk-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(110px, 1fr));
  gap: 12px;
  flex: 1;
}
.risk-item {
  padding: 14px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  color: #606266;
}
.risk-item span {
  display: block;
  font-size: 13px;
  margin-bottom: 6px;
}
.risk-item b {
  font-size: 20px;
  color: #303133;
}
.risk-item.high { background: #fef0f0; }
.risk-item.high b { color: #f56c6c; }
.risk-item.medium { background: #fdf6ec; }
.risk-item.medium b { color: #e6a23c; }
.risk-item.low { background: #f0f9eb; }
.risk-item.low b { color: #67c23a; }
.info-bar {
  margin-bottom: 16px;
}
.info-bar :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 14px;
}
.chart-row {
  margin-top: 16px;
}
.chart {
  height: 280px;
}
@media (max-width: 900px) {
  .score-card :deep(.el-card__body) {
    flex-direction: column;
    align-items: stretch;
  }
  .risk-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
