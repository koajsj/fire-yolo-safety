<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="header-flex">
          <span class="card-title">检测记录</span>
          <div class="filters">
            <el-input
              v-model="query.keyword"
              placeholder="按类别搜索"
              clearable
              style="width: 160px"
              @keyup.enter="search"
            />
            <el-select
              v-model="query.detect_type"
              placeholder="检测类型"
              clearable
              style="width: 130px"
            >
              <el-option label="图片" value="image" />
              <el-option label="视频" value="video" />
              <el-option label="摄像头" value="camera" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="search">查询</el-button>
            <el-button :icon="Refresh" @click="reset">重置</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="64" />
        <el-table-column label="检测类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTag(row.detect_type)">
              {{ typeText(row.detect_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="classes" label="检测类别" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.classes">{{ row.classes }}</span>
            <span v-else style="color:#909399">未检出</span>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">
            {{ percent(row.confidence) }}
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="riskTag(row.risk_level)">
              {{ row.risk_level || '低风险' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="num_detections" label="目标数" width="80" />
        <el-table-column label="耗时" width="100">
          <template #default="{ row }">{{ row.processing_time_ms || 0 }} ms</template>
        </el-table-column>
        <el-table-column label="是否异常" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_abnormal ? 'danger' : 'success'">
              {{ row.is_abnormal ? '异常' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="检测时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="view(row)">查看</el-button>
            <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无检测记录" :image-size="100" />
        </template>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="query.page_size"
          :current-page="query.page"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="dialogVisible" title="检测结果详情" width="640px">
      <template v-if="current">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="ID">{{ current.id }}</el-descriptions-item>
          <el-descriptions-item label="检测类型">{{ typeText(current.detect_type) }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ current.classes || '未检出' }}</el-descriptions-item>
          <el-descriptions-item label="置信度">
            {{ percent(current.confidence) }}
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="riskTag(current.risk_level)" size="small">
              {{ current.risk_level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标总数">{{ current.num_detections }}</el-descriptions-item>
          <el-descriptions-item label="检测耗时">{{ current.processing_time_ms }} ms</el-descriptions-item>
          <el-descriptions-item label="最高置信度类别">{{ current.top_label }}</el-descriptions-item>
          <el-descriptions-item label="最高置信度">{{ percent(current.top_confidence) }}</el-descriptions-item>
          <el-descriptions-item label="火焰数量">{{ current.fire_count }}</el-descriptions-item>
          <el-descriptions-item label="烟雾数量">{{ current.smoke_count }}</el-descriptions-item>
          <el-descriptions-item label="抽烟数量">{{ current.smoking_count }}</el-descriptions-item>
          <el-descriptions-item label="人员数量">{{ current.person_count }}</el-descriptions-item>
          <el-descriptions-item label="是否异常">
            <el-tag :type="current.is_abnormal ? 'danger' : 'success'" size="small">
              {{ current.is_abnormal ? '异常' : '正常' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="检测时间">{{ current.created_at }}</el-descriptions-item>
          <el-descriptions-item label="风险提示" :span="2">{{ current.risk_message }}</el-descriptions-item>
        </el-descriptions>

        <div class="dialog-result" v-if="current.file_path">
          <div class="preview-label">检测结果</div>
          <video
            v-if="current.detect_type === 'video'"
            :src="`/${current.file_path}`"
            controls
            class="dialog-media"
          ></video>
          <el-image
            v-else
            :src="`/${current.file_path}`"
            fit="contain"
            class="dialog-media"
            :preview-src-list="[`/${current.file_path}`]"
          />
        </div>
        <el-empty v-else description="该记录暂无结果文件" :image-size="80" />
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRecords, deleteRecord } from '../api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const current = ref(null)

const query = reactive({
  keyword: '',
  detect_type: '',
  page: 1,
  page_size: 10
})

const typeText = (t) => ({ image: '图片', video: '视频', camera: '摄像头' }[t] || t)
const typeTag = (t) => ({ image: '', video: 'warning', camera: 'success' }[t] || 'info')
const riskTag = (level) => ({ 高风险: 'danger', 中风险: 'warning', 低风险: 'success' }[level] || 'info')
const percent = (value) => {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? `${(n * 100).toFixed(1)}%` : '-'
}

const normalizeRecord = (row = {}) => ({
  ...row,
  classes: row.classes || '',
  confidence: Number(row.confidence || 0),
  is_abnormal: Number(row.is_abnormal || 0),
  risk_level: row.risk_level || '低风险',
  num_detections: Number(row.num_detections || 0),
  fire_count: Number(row.fire_count || 0),
  smoke_count: Number(row.smoke_count || 0),
  smoking_count: Number(row.smoking_count || 0),
  person_count: Number(row.person_count || 0),
  processing_time_ms: Number(row.processing_time_ms || 0),
  top_label: row.top_label || '无',
  top_confidence: Number(row.top_confidence || 0),
  risk_message: row.risk_message || '当前未发现明显异常。'
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getRecords(query)
    list.value = Array.isArray(res.data.list) ? res.data.list.map(normalizeRecord) : []
    total.value = Number(res.data.total || 0)
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

const reset = () => {
  query.keyword = ''
  query.detect_type = ''
  query.page = 1
  loadData()
}

const search = () => {
  query.page = 1
  loadData()
}

const onPageChange = (p) => {
  query.page = p
  loadData()
}

const view = (row) => {
  current.value = normalizeRecord(row)
  dialogVisible.value = true
}

const remove = (row) => {
  ElMessageBox.confirm(`确定删除记录 #${row.id} 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      await deleteRecord(row.id)
      ElMessage.success('删除成功')
      loadData()
    })
    .catch(() => {})
}

onMounted(loadData)
</script>

<style scoped>
.header-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.dialog-result {
  margin-top: 16px;
}
.preview-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}
.dialog-media {
  width: 100%;
  max-height: 360px;
  background: #f5f7fa;
  border-radius: 6px;
}
</style>
