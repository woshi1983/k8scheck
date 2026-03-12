<template>
  <div class="cluster-management">
    <el-card class="header-card">
      <div class="header-content">
        <div class="title">
          <el-button text @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回 Dashboard
          </el-button>
          <el-icon><Monitor /></el-icon>
          <h2>集群管理</h2>
        </div>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加集群
        </el-button>
      </div>
    </el-card>

    <!-- 集群列表 -->
    <el-card class="table-card">
      <el-table
        :data="clusters"
        stripe
        border
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="name" label="集群名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="k8s_version" label="K8s 版本" width="120">
          <template #default="{ row }">
            <span v-if="row.k8s_version">{{ row.k8s_version }}</span>
            <el-tag v-else size="small" type="info">未知</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="node_count" label="节点数" width="100" align="center">
          <template #default="{ row }">
            {{ row.node_count || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="api_server_url" label="API Server" width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'connected' ? 'success' : row.status === 'disconnected' ? 'danger' : 'info'"
              size="small"
            >
              {{ row.status === 'connected' ? '已连接' : row.status === 'disconnected' ? '连接失败' : '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前集群" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">活跃</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="success"
              size="small"
              @click="activateCluster(row.id)"
              :loading="activatingId === row.id"
            >
              切换
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="testConnection(row)"
              :loading="testingId === row.id"
            >
              测试连接
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="editCluster(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteCluster(row.id)"
              :disabled="row.is_active"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="clusters.length === 0 && !loading" description="暂无集群配置，请添加集群" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑集群' : '添加集群'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="clusterForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="集群名称" prop="name">
          <el-input v-model="clusterForm.name" placeholder="例如：prod-cluster-01" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="clusterForm.description" placeholder="集群描述信息" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Kubeconfig" prop="kubeconfig_content">
          <el-input
            v-model="clusterForm.kubeconfig_content"
            type="textarea"
            :rows="12"
            placeholder="请粘贴 kubeconfig 文件内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试连接结果 -->
    <el-dialog v-model="testResultVisible" title="测试连接结果" width="500px" :show-close="false">
      <div class="test-result">
        <el-result
          :icon="testResult.success ? 'success' : 'error'"
          :title="testResult.success ? '连接成功' : '连接失败'"
          :sub-title="testResult.message"
        >
          <template v-if="testResult.success" #extra>
            <div class="result-info">
              <p><strong>K8s 版本：</strong>{{ testResult.k8s_version }}</p>
              <p><strong>节点数量：</strong>{{ testResult.node_count }}</p>
              <p><strong>API Server：</strong>{{ testResult.api_server_url }}</p>
            </div>
          </template>
        </el-result>
      </div>
      <template #footer>
        <el-button type="primary" @click="testResultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, Plus, ArrowLeft } from '@element-plus/icons-vue'
import {
  apiService,
  type ClusterInfo,
  type ClusterCreateRequest,
  type ClusterUpdateRequest,
  type ClusterTestResult
} from '../api/client'

const clusters = ref<ClusterInfo[]>([])
const loading = ref(false)
const activatingId = ref<number | null>(null)
const testingId = ref<number | null>(null)
const submitting = ref(false)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const editClusterId = ref<number | null>(null)

// 返回 Dashboard
const goBack = () => {
  window.location.hash = '#'
}

// 表单
const formRef = ref<any>(null)
const clusterForm = ref<ClusterCreateRequest & { description?: string }>({
  name: '',
  description: '',
  kubeconfig_content: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入集群名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  kubeconfig_content: [
    { required: true, message: '请输入 Kubeconfig 内容', trigger: 'blur' }
  ]
}

// 测试结果
const testResultVisible = ref(false)
const testResult = ref<ClusterTestResult>({
  success: false,
  message: '',
  k8s_version: '',
  node_count: 0,
  api_server_url: ''
})

// 加载集群列表
const loadClusters = async () => {
  loading.value = true
  try {
    const res = await apiService.getClusters()
    clusters.value = res.data.clusters
  } catch (error) {
    ElMessage.error('加载集群列表失败')
    console.error('Load clusters error:', error)
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  editClusterId.value = null
  clusterForm.value = {
    name: '',
    description: '',
    kubeconfig_content: ''
  }
  dialogVisible.value = true
}

// 编辑集群
const editCluster = (cluster: ClusterInfo) => {
  isEdit.value = true
  editClusterId.value = cluster.id
  clusterForm.value = {
    name: cluster.name,
    description: cluster.description || '',
    kubeconfig_content: ''  // 不显示原有内容
  }
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value && editClusterId.value) {
        // 更新集群
        const data: ClusterUpdateRequest = {
          name: clusterForm.value.name,
          description: clusterForm.value.description
        }
        if (clusterForm.value.kubeconfig_content) {
          data.kubeconfig_content = clusterForm.value.kubeconfig_content
        }
        await apiService.updateCluster(editClusterId.value, data)
        ElMessage.success('更新成功')
      } else {
        // 创建集群
        await apiService.createCluster(clusterForm.value as ClusterCreateRequest)
        ElMessage.success('添加成功')
      }
      dialogVisible.value = false
      loadClusters()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 切换集群
const activateCluster = async (id: number) => {
  activatingId.value = id
  try {
    await apiService.activateCluster(id)
    ElMessage.success('切换成功')
    loadClusters()

    // 触发集群切换事件
    window.dispatchEvent(new CustomEvent('cluster-changed'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '切换失败')
  } finally {
    activatingId.value = null
  }
}

// 测试连接
const testConnection = async (cluster: ClusterInfo) => {
  testingId.value = cluster.id
  try {
    const res = await apiService.getClusterInfo(cluster.id)
    testResult.value = res.data.connection
    testResultVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '测试失败')
  } finally {
    testingId.value = null
  }
}

// 删除集群
const deleteCluster = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此集群吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await apiService.deleteCluster(id)
    ElMessage.success('删除成功')
    loadClusters()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadClusters()
})
</script>

<style scoped>
.cluster-management {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.header-card {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.test-result {
  padding: 20px;
}

.result-info {
  text-align: left;
  margin-top: 16px;
}

.result-info p {
  margin: 8px 0;
  color: #606266;
}
</style>
