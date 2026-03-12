<template>
  <div class="dashboard">
    <!-- 集群管理页面 -->
    <ClusterManagement v-if="currentRoute === 'cluster-management'" />

    <!-- Dashboard 主页面 -->
    <template v-else>
    <header class="header">
      <div class="header-left">
        <div class="header-logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="#1890FF" fill-opacity="0.1"/>
            <circle cx="12" cy="12" r="8" stroke="#1890FF" stroke-width="2"/>
            <circle cx="12" cy="12" r="4" fill="#1890FF"/>
            <path d="M12 2V6M12 18V22M2 12H6M18 12H22" stroke="#1890FF" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h1>K8s 巡检 Dashboard</h1>
        <span class="mode-badge">{{ mode }}</span>
        <span class="update-time">最后更新: {{ lastUpdateTime }}</span>
      </div>
      <div class="header-controls">
        <!-- 自动刷新下拉框 -->
        <el-select
          v-model="autoRefreshInterval"
          placeholder="自动刷新"
          style="width: 120px"
          size="default"
          @change="handleAutoRefreshChange"
        >
          <el-option label="关闭自动刷新" :value="0" />
          <el-option label="每 30 秒" :value="30" />
          <el-option label="每 1 分钟" :value="60" />
          <el-option label="每 5 分钟" :value="300" />
        </el-select>
        <!-- 集群选择器 -->
        <el-select
          v-model="currentClusterId"
          placeholder="选择集群"
          style="width: 200px"
          @change="onClusterChange"
          :disabled="clusters.length === 0"
        >
          <el-option
            v-for="cluster in clusters"
            :key="cluster.id"
            :label="cluster.name"
            :value="cluster.id"
          >
            <span>{{ cluster.name }}</span>
            <el-tag v-if="cluster.is_active" type="success" size="small" style="margin-left: 8px">当前</el-tag>
          </el-option>
        </el-select>
        <!-- 集群管理按钮 -->
        <el-button @click="goToClusterManagement" type="info" :icon="Setting">
          集群管理
        </el-button>
        <!-- 刷新按钮 -->
        <el-button @click="fetchData" :loading="loading" type="primary" :icon="Refresh" size="default">
          刷新数据
        </el-button>
      </div>
    </header>

    <!-- 统计卡片 -->
    <div class="stats-container">
      <div class="stat-card-item">
        <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon nodes">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ nodesTotal }}</div>
            <div class="stat-label">总节点数</div>
          </div>
        </div>
      </el-card>
      </div>

      <div class="stat-card-item">
        <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon healthy">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ nodesHealthy }}</div>
            <div class="stat-label">健康节点</div>
          </div>
        </div>
      </el-card>
      </div>

      <div class="stat-card-item">
        <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon pods">
            <el-icon><Box /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ podsTotal }}</div>
            <div class="stat-label">总 Pod 数</div>
          </div>
        </div>
      </el-card>
      </div>

      <div class="stat-card-item">
        <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon storage">
            <el-icon><Finished /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ pvcsUnhealthy }}</div>
            <div class="stat-label">异常 PVC</div>
          </div>
        </div>
      </el-card>
      </div>

      <div class="stat-card-item">
        <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon workload">
            <el-icon><SetUp /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ workloadsUnhealthy }}</div>
            <div class="stat-label">异常工作负载</div>
          </div>
        </div>
      </el-card>
      </div>

      <!-- 告警事件卡片 -->
      <div class="stat-card-item">
        <el-card class="stat-card clickable" @click="viewWarningEvents">
          <div class="stat-content">
            <div class="stat-icon events">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ eventsTotal }}</div>
              <div class="stat-label">告警事件</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 证书风险卡片 -->
      <div class="stat-card-item">
        <el-card class="stat-card cert-card clickable" @click="certificateDrawerVisible = true">
        <div class="stat-content">
          <div class="stat-icon cert">
            <el-icon><Lock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ certRiskTotal }}</div>
            <div class="stat-label">证书风险</div>
          </div>
        </div>
        <el-tag v-if="certRiskNeedAttention" type="danger" size="small" style="position: absolute; top: 16px; right: 16px;">需关注</el-tag>
      </el-card>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <template #header>
          <div class="card-title">
            <el-icon><Cpu /></el-icon>
            <span>集群资源使用率</span>
          </div>
        </template>
        <v-chart
          v-if="resourceUsage"
          ref="gaugeChartRef"
          class="chart-container"
          style="height: 350px !important; width: 100%;"
          :option="gaugeChartOption"
        />
        <el-empty v-else description="暂无数据" />
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <div class="card-title">
            <el-icon><PieChart /></el-icon>
            <span>Namespace Pod 分布</span>
          </div>
        </template>
        <v-chart
          v-if="namespaceDist.length > 0"
          ref="pieChartRef"
          class="chart-container"
          style="height: 350px !important; width: 100%;"
          :option="pieChartOption"
        />
        <el-empty v-else description="暂无数据" />
      </el-card>
    </div>

    <!-- 多标签页 - 五大分类 -->
    <el-card class="tabs-card">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- Tab 1: 工作负载异常 -->
        <el-tab-pane name="workload">
          <template #label>
            <span class="tab-label">
              <el-icon><SetUp /></el-icon>
              工作负载异常 ({{ workloadAnomalies.length }})
            </span>
          </template>

          <el-table
            :data="workloadAnomalies"
            stripe
            border
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="namespace" label="Namespace" width="150" />
            <el-table-column prop="name" label="名称" min-width="200" />
            <el-table-column prop="kind" label="类型" width="120">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.kind }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="副本数" width="120" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.ready_replicas < row.desired_replicas }">
                  {{ row.ready_replicas }}/{{ row.desired_replicas }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="140">
              <template #default="{ row }">
                <el-tag :type="getAnomalyStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="fatal_reason" label="致命原因" width="150">
              <template #default="{ row }">
                <el-tag v-if="row.fatal_reason" type="danger" size="small">
                  {{ row.fatal_reason }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="restarts" label="重启次数" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.restarts > 5 }">{{ row.restarts }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="pod_status" label="Pod 状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.pod_status" type="info" size="small">
                  {{ row.pod_status }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="age" label="运行时长" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.age">{{ row.age }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="250" show-overflow-tooltip />
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="viewYaml(row.kind, row.namespace, row.name)"
                >
                  <el-icon><Document /></el-icon>
                  YAML
                </el-button>
                <el-divider direction="vertical" />
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="viewPodLogs(row.kind, row.namespace, row.name)"
                >
                  <el-icon><Document /></el-icon>
                  日志
                </el-button>
                <el-divider direction="vertical" />
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="viewDescribe(row.kind, row.namespace, row.name)"
                >
                  <el-icon><Message /></el-icon>
                  事件
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="workloadAnomalies.length === 0" description="暂无工作负载异常" />
        </el-tab-pane>

        <!-- Tab 2: 网络服务异常 -->
        <el-tab-pane name="network">
          <template #label>
            <span class="tab-label">
              <el-icon><Connection /></el-icon>
              网络服务异常 ({{ networkAnomalies.length }})
            </span>
          </template>

          <el-table
            :data="networkAnomalies"
            stripe
            border
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="namespace" label="Namespace" width="150" />
            <el-table-column prop="name" label="名称" min-width="200" />
            <el-table-column prop="kind" label="类型" width="100">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.kind }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="Service 类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="140">
              <template #default="{ row }">
                <el-tag :type="getNetworkStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" min-width="200">
              <template #default="{ row }">
                <el-tag type="warning" size="small">{{ row.reason }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="250" show-overflow-tooltip />
          </el-table>

          <el-empty v-if="networkAnomalies.length === 0" description="暂无网络服务异常" />
        </el-tab-pane>

        <!-- Tab 3: 存储卷异常 -->
        <el-tab-pane name="storage">
          <template #label>
            <span class="tab-label">
              <el-icon><Finished /></el-icon>
              存储卷异常 ({{ storageAnomalies.length }})
            </span>
          </template>

          <el-table
            :data="storageAnomalies"
            stripe
            border
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="namespace" label="Namespace" width="150" />
            <el-table-column prop="name" label="名称" min-width="200" />
            <el-table-column prop="kind" label="类型" width="100">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.kind }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStorageStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="capacity" label="容量" width="100" />
            <el-table-column prop="storage_class" label="存储类" width="150" />
            <el-table-column prop="reason" label="原因" width="150">
              <template #default="{ row }">
                <el-tag :type="getReasonType(row.reason)" size="small">{{ row.reason }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="250" show-overflow-tooltip />
          </el-table>

          <el-empty v-if="storageAnomalies.length === 0" description="暂无存储卷异常" />
        </el-tab-pane>

        <!-- Tab 4: 节点与资源压力 -->
        <el-tab-pane name="node_pressure">
          <template #label>
            <span class="tab-label">
              <el-icon><Monitor /></el-icon>
              节点与资源压力 ({{ nodePressures.filter(n => n.status !== 'Ready').length }})
            </span>
          </template>

          <el-table
            :data="nodePressures"
            stripe
            border
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="name" label="节点名称" min-width="150" />
            <el-table-column prop="status" label="状态" width="140">
              <template #default="{ row }">
                <el-tag :type="getNodeStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="pressure_type" label="压力类型" width="150">
              <template #default="{ row }">
                <el-tag v-if="row.pressure_type" type="warning" size="small">
                  {{ row.pressure_type }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="CPU" width="120" align="center">
              <template #default="{ row }">
                <div v-if="row.cpu_usage_percent !== null">
                  <el-progress
                    :percentage="row.cpu_usage_percent"
                    :status="row.cpu_usage_percent > 80 ? 'exception' : ''"
                    :format="(p: number) => `${p.toFixed(1)}%`"
                  />
                </div>
                <span v-else>{{ row.cpu_capacity }}</span>
              </template>
            </el-table-column>
            <el-table-column label="内存" width="120" align="center">
              <template #default="{ row }">
                <div v-if="row.memory_usage_percent !== null">
                  <el-progress
                    :percentage="row.memory_usage_percent"
                    :status="row.memory_usage_percent > 80 ? 'exception' : ''"
                    :format="(p: number) => `${p.toFixed(1)}%`"
                  />
                </div>
                <span v-else>{{ row.memory_capacity }}</span>
              </template>
            </el-table-column>
            <el-table-column label="Pod 数量" width="120" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-warning': row.pod_count > row.pod_capacity * 0.9 }">
                  {{ row.pod_count }} / {{ row.pod_capacity }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="250" show-overflow-tooltip />
          </el-table>

          <el-empty v-if="nodePressures.filter(n => n.status !== 'Ready').length === 0" description="节点状态正常" />
        </el-tab-pane>

        <!-- Tab 5: 控制面状态 -->
        <el-tab-pane name="control_plane">
          <template #label>
            <span class="tab-label">
              <el-icon><Setting /></el-icon>
              控制面状态 ({{ controlPlaneUnhealthyCount }})
            </span>
          </template>

          <!-- 核心组件状态概览 -->
          <div class="control-plane-overview">
            <div class="overview-title">核心组件健康状态 (四大金刚)</div>
            <div class="overview-grid">
              <div
                v-for="component in coreComponentStates"
                :key="component.name"
                class="component-card"
              >
                <div class="component-name">{{ component.label }}</div>
                <div class="component-status">
                  <el-icon :size="24">
                    <component
                      :is="component.status === 'Running' ? CircleCheck : Warning"
                      :class="[
                        'status-icon',
                        component.status === 'Running' ? 'healthy' : 'unhealthy'
                      ]"
                    />
                  </el-icon>
                </div>
                <div class="component-detail" v-if="component.status !== 'Running'">
                  <span class="detail-text">{{ component.statusText }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 所有控制面组件列表 -->
          <div class="all-components-title">所有控制面组件</div>
          <el-table
            :data="controlPlaneStatuses"
            stripe
            border
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column prop="component" label="组件" width="200">
              <template #default="{ row }">
                <el-tag :type="row.is_core ? 'warning' : 'info'" size="small">
                  {{ row.component }}
                  <span v-if="row.is_core" class="core-tag">核心</span>
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="namespace" label="Namespace" width="150" />
            <el-table-column prop="pod_name" label="Pod 名称" min-width="200" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getControlPlaneStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="restarts" label="重启次数" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-danger': row.restarts > 5 }">{{ row.restarts }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="200" show-overflow-tooltip />
          </el-table>

          <el-empty v-if="controlPlaneStatuses.length === 0" description="暂无控制面组件数据" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    </template>

    <!-- 终端风格弹窗 -->
    <TerminalDialog
      v-model="terminalDialogVisible"
      :title="terminalTitle"
      :content="terminalContent"
      :format-field="terminalField"
      :is-green-theme="terminalTheme"
    />

    <!-- 证书风险抽屉 -->
    <el-drawer
      v-model="certificateDrawerVisible"
      title="证书风险管理"
      direction="rtl"
      size="800"
      :with-header="true"
    >
      <div class="cert-drawer-content">
        <el-alert
          v-if="certRiskNeedAttention"
          title="发现证书风险"
          :description="`发现 ${certRiskTotal} 个证书需要关注（${certificates.filter(c => c.status === 'Expired').length} 个已过期，${certificates.filter(c => c.status === 'ExpiringSoon').length} 个即将过期）`"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-empty v-else description="所有证书状态正常" />

        <el-table
          v-if="certificates.length > 0"
          :data="certificates"
          stripe
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column prop="namespace" label="Namespace" width="120" />
          <el-table-column prop="name" label="Secret 名称" min-width="200" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag
                :type="getStatusType(row.status)"
                size="small"
              >
                {{ row.status === 'Valid' ? '有效' : row.status === 'Expired' ? '已过期' : '即将过期' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="expire_time" label="过期时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.expire_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="remaining_days" label="剩余天数" width="120">
            <template #default="{ row }">
              <span :class="{ 'text-danger': row.remaining_days < 30 }">{{ row.remaining_days }} 天</span>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="详细信息" min-width="250" />
        </el-table>
      </div>
    </el-drawer>

    <!-- 告警事件抽屉 -->
    <el-drawer
      v-model="eventsDrawerVisible"
      title="告警事件详情 (Warning)"
      size="60%"
      :with-header="true"
    >
      <div class="events-drawer-content">
        <el-table
          :data="warningEvents"
          stripe
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column prop="first_time" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.first_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="namespace" label="Namespace" width="120" />
          <el-table-column prop="object_kind" label="资源类型" width="120">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.object_kind }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="object_name" label="资源名称" min-width="200" />
          <el-table-column prop="reason" label="原因" width="150">
            <template #default="{ row }">
              <el-tag type="danger" size="small">{{ row.reason }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="详细信息" min-width="300">
            <template #default="{ row }">
              <div style="white-space: pre-wrap; word-wrap: break-word">{{ row.message }}</div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="warningEvents.length === 0" description="暂无告警事件" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Monitor, CircleCheck, Box, Finished, SetUp, Bell, Refresh,
  Cpu, PieChart, Connection, Setting, Document, Lock, Warning, Message
} from '@element-plus/icons-vue'
import {
  apiService,
  type ResourceUsage, type NamespacePodDist,
  type WorkloadAnomaly, type NetworkAnomaly, type StorageAnomaly,
  type NodePressure, type ControlPlaneStatus,
  type ClusterInfo
} from './api/client'
import { currentRoute } from './router'
import ClusterManagement from './views/ClusterManagement.vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'
import TerminalDialog from './components/TerminalDialog.vue'

// 状态数据
const mode = ref('mock')
const loading = ref(false)
const activeTab = ref('workload')

// 集群管理相关
const clusters = ref<ClusterInfo[]>([])
const currentClusterId = ref<number | null>(null)
const isClusterReady = ref(false)

// 统计数据
const nodesTotal = ref(0)
const nodesHealthy = ref(0)
const podsTotal = ref(0)
const pvcsUnhealthy = ref(0)
const workloadsUnhealthy = ref(0)
const eventsTotal = ref(0)

// 资源使用数据
const resourceUsage = ref<ResourceUsage | null>(null)

// Namespace 分布数据
const namespaceDist = ref<NamespacePodDist[]>([])

// 五大分类异常数据
const workloadAnomalies = ref<WorkloadAnomaly[]>([])
const networkAnomalies = ref<NetworkAnomaly[]>([])
const storageAnomalies = ref<StorageAnomaly[]>([])
const nodePressures = ref<NodePressure[]>([])
const controlPlaneStatuses = ref<ControlPlaneStatus[]>([])

// 自动刷新相关
const lastUpdateTime = ref('--:--:--')
const autoRefreshInterval = ref(0) // 0 = 关闭, 其他值 = 自动刷新间隔(秒)
let autoRefreshTimer: number | null = null

// 证书数据
const certificates = ref<any[]>([])
const certRiskTotal = ref(0)
const certRiskNeedAttention = ref(false)

// 证书抽屉状态
const certificateDrawerVisible = ref(false)

// 告警事件抽屉状态
const eventsDrawerVisible = ref(false)
const warningEvents = ref<any[]>([])

// 终端弹窗状态
const terminalDialogVisible = ref(false)
const terminalTitle = ref('')
const terminalContent = ref('')
const terminalField = ref('')
const terminalTheme = ref(true) // true = green, false = white

// ECharts 图表 ref
const gaugeChartRef = ref()
const pieChartRef = ref()

// 处理窗口缩放
const handleResize = () => {
  // 使用 getInstanceByDom 安全地获取并调整图表大小
  if (gaugeChartRef.value && gaugeChartRef.value.$el) {
    const chartEl = gaugeChartRef.value.$el
    const chartInstance = echarts.getInstanceByDom(chartEl)
    if (chartInstance) {
      chartInstance.resize()
    }
  }
  if (pieChartRef.value && pieChartRef.value.$el) {
    const chartEl = pieChartRef.value.$el
    const chartInstance = echarts.getInstanceByDom(chartEl)
    if (chartInstance) {
      chartInstance.resize()
    }
  }
}
const gaugeChartOption = computed(() => {
  if (!resourceUsage.value) return {}

  // 使用深拷贝确保触发响应式更新
  const cpuValue = resourceUsage.value.cpu_usage_percent ?? 0
  const memValue = resourceUsage.value.memory_usage_percent ?? 0

  return {
    tooltip: {
      formatter: '{a} <br/>{b} : {c}%'
    },
    series: [
      {
        name: 'CPU 使用率',
        type: 'gauge',
        center: ['25%', '55%'],
        radius: '90%',
        min: 0,
        max: 100,
        progress: { show: true },
        pointer: { show: true },
        axisTick: { show: true },
        splitLine: { show: true },
        axisLabel: { show: true },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          fontSize: 14
        },
        data: [{ value: cpuValue, name: 'CPU' }],
        title: { offsetCenter: ['0%', '0%'] }
      },
      {
        name: '内存使用率',
        type: 'gauge',
        center: ['75%', '55%'],
        radius: '90%',
        min: 0,
        max: 100,
        progress: { show: true },
        pointer: { show: true },
        axisTick: { show: true },
        splitLine: { show: true },
        axisLabel: { show: true },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          fontSize: 14
        },
        data: [{ value: memValue, name: '内存' }],
        title: { offsetCenter: ['0%', '0%'] }
      }
    ]
  }
})

// 饼图配置
const pieChartOption = computed(() => {
  // 使用深拷贝确保触发响应式更新
  const distCopy = [...(namespaceDist.value || [])]
  if (distCopy.length === 0) return {}

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: 'Pod 数量',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: distCopy.map(item => ({
          name: item.namespace || 'unknown',
          value: item.pod_count || 0
        }))
      }
    ]
  }
})

// 加载集群列表
const loadClusters = async () => {
  try {
    const res = await apiService.getClusters()
    clusters.value = res.data.clusters

    // 默认选中第一个集群或当前活跃集群
    if (clusters.value.length > 0 && !currentClusterId.value) {
      const activeCluster = clusters.value.find(c => c.is_active === 1 || c.is_active)
      currentClusterId.value = activeCluster?.id ?? clusters.value[0]?.id ?? null
      isClusterReady.value = true
    }
  } catch (error) {
    console.error('Load clusters error:', error)
  }
}

// 集群切换处理
const onClusterChange = async (id: number) => {
  if (!id) return

  try {
    // 调用激活接口
    await apiService.activateCluster(id)
    currentClusterId.value = id
    isClusterReady.value = true

    ElMessage.success('已切换到新集群')

    // 触发全局集群变更事件
    window.dispatchEvent(new CustomEvent('cluster-changed'))

    // 刷新 Dashboard 数据
    await fetchData()
  } catch (error: any) {
    console.error('Cluster change error:', error)
    // 恢复原选择
    loadClusters()
  }
}

// 跳转到集群管理页面
const goToClusterManagement = () => {
  // 使用简单的方式切换视图 - 通过 URL hash 或事件
  window.location.hash = '#/cluster-management'
  window.dispatchEvent(new CustomEvent('navigate-to-cluster-management'))
}

// 监听集群变更事件（从集群管理页面返回时刷新）
const setupClusterChangeListener = () => {
  window.addEventListener('cluster-changed', () => {
    loadClusters()
    fetchData()
  })
}

// 获取工作负载异常状态类型
const getAnomalyStatusType = (status: string): '' | 'success' | 'warning' | 'danger' => {
  if (status.includes('OOMKilled') || status.includes('CrashLoop')) return 'danger'
  if (status.includes('ImagePull')) return 'danger'
  if (status.includes('Mismatch')) return 'warning'
  return 'warning'
}

// 获取网络异常状态类型
const getNetworkStatusType = (status: string): '' | 'warning' | 'danger' => {
  if (status === 'NoEndpoints') return 'danger'
  if (status === 'IngressError') return 'warning'
  return 'warning'
}

// 获取存储异常状态类型
const getStorageStatusType = (status: string): '' | 'warning' | 'danger' => {
  if (status === 'Lost') return 'danger'
  if (status === 'Pending') return 'warning'
  return 'warning'
}

// 获取原因标签类型
const getReasonType = (reason: string): 'warning' | 'danger' => {
  if (reason === 'PVLost' || reason === 'NoStorageClass') return 'danger'
  return 'warning'
}

// 获取节点状态类型
const getNodeStatusType = (status: string): '' | 'success' | 'warning' | 'danger' => {
  if (status === 'Ready') return 'success'
  if (status === 'NotReady') return 'danger'
  if (status.includes('Pressure')) return 'warning'
  return 'success'
}

// 获取控制面状态类型
const getControlPlaneStatusType = (status: string): '' | 'success' | 'warning' | 'danger' => {
  if (status === 'Running') return 'success'
  if (status === 'CrashLoopBackOff') return 'danger'
  if (status === 'Unhealthy') return 'danger'
  if (status === 'NotReady') return 'warning'
  return 'warning'
}

// 控制面核心组件定义（按顺序）
const coreComponents = [
  { name: 'kube-apiserver', label: 'kube-apiserver', status: '', statusText: '' },
  { name: 'kube-controller-manager', label: 'kube-controller-manager', status: '', statusText: '' },
  { name: 'kube-scheduler', label: 'kube-scheduler', status: '', statusText: '' },
  { name: 'etcd', label: 'etcd', status: '', statusText: '' },
]

// 计算非健康控制面组件数量
const controlPlaneUnhealthyCount = computed(() => {
  return controlPlaneStatuses.value.filter(c => c.status !== 'Running').length
})

// 计算核心组件状态（按顺序填充）
const coreComponentStates = computed(() => {
  const states: Record<string, any> = {}
  controlPlaneStatuses.value.forEach((c) => {
    states[c.component] = c
  })
  return coreComponents.map(c => {
    const status = states[c.name] || { status: 'Unknown', message: '未找到组件' }
    return {
      ...c,
      status: status.status,
      statusText: status.message || '-',
      isCore: true,
      namespace: states[c.name]?.namespace || '-',
      podName: states[c.name]?.pod_name || '-',
      restarts: states[c.name]?.restarts || 0,
    }
  })
})

// 格式化日期
const getStatusType = (status: string): 'success' | 'warning' | 'danger' => {
  if (status === 'Valid') return 'success'
  if (status === 'Expired') return 'danger'
  if (status === 'ExpiringSoon') return 'warning'
  return 'warning'
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

// 查看 YAML（使用终端弹窗）
const viewYaml = async (kind: string, namespace: string, name: string) => {
  try {
    terminalTitle.value = `YAML: ${kind}/${namespace}/${name}`
    terminalField.value = 'YAML'
    terminalTheme.value = false // 白色主题
    terminalContent.value = '正在加载 YAML...'
    terminalDialogVisible.value = true

    const res = await apiService.getResourceYaml(kind, namespace, name)
    terminalContent.value = res.data.yaml || '暂无 YAML 数据'
  } catch (error) {
    ElMessage.error('获取 YAML 失败')
    console.error('Fetch yaml error:', error)
    terminalContent.value = '无法获取 YAML：' + (error as Error).message
  }
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // 获取节点数据
    try {
      const nodesRes = await apiService.getNodes()
      nodesTotal.value = nodesRes.data.total
      nodesHealthy.value = nodesRes.data.healthy
    } catch (err) {
      console.error('Get nodes error:', err)
    }

    // 获取 Pod 数据
    try {
      const podsRes = await apiService.getPods()
      podsTotal.value = podsRes.data.total
    } catch (err) {
      console.error('Get pods error:', err)
    }

    // 获取 PVC 数据
    try {
      const pvcsRes = await apiService.getPVCs()
      pvcsUnhealthy.value = pvcsRes.data.unhealthy
    } catch (err) {
      console.error('Get pvcs error:', err)
    }

    // 获取工作负载数据
    try {
      const workloadsRes = await apiService.getWorkloads()
      workloadsUnhealthy.value = workloadsRes.data.unhealthy
    } catch (err) {
      console.error('Get workloads error:', err)
    }

    // 获取事件数据
    try {
      const eventsRes = await apiService.getEvents(1)
      eventsTotal.value = eventsRes.data.total
    } catch (err) {
      console.error('Get events error:', err)
    }

    // 获取资源使用数据
    try {
      const usageRes = await apiService.getResourceUsage()
      resourceUsage.value = usageRes.data
    } catch (err) {
      console.error('Get resource usage error:', err)
    }

    // 获取 Namespace 分布
    try {
      const nsRes = await apiService.getNamespaceDistribution()
      namespaceDist.value = nsRes.data.distribution || []
    } catch (err) {
      console.error('Get namespace distribution error:', err)
    }

    // 获取五大分类异常数据（新接口）
    try {
      const anomaliesRes = await apiService.getAnomalies()
      workloadAnomalies.value = anomaliesRes.data.workload_anomalies
      networkAnomalies.value = anomaliesRes.data.network_anomalies
      storageAnomalies.value = anomaliesRes.data.storage_anomalies
      nodePressures.value = anomaliesRes.data.node_pressures
      controlPlaneStatuses.value = anomaliesRes.data.control_plane_statuses
    } catch (err) {
      console.error('Get anomalies error:', err)
    }

    // 获取证书数据
    try {
      const certRes = await apiService.getCertificates()
      certificates.value = certRes.data.certificates || []
      // 统计有风险的证书（已过期 + 即将过期）
      const riskTotal = certRes.data.expired + certRes.data.expiring_soon
      certRiskTotal.value = riskTotal
      certRiskNeedAttention.value = riskTotal > 0
    } catch (err) {
      console.error('Get certificates error:', err)
    }

    // 获取运行模式
    try {
      const rootRes = await fetch('/api/health')
      if (rootRes.ok) {
        const rootData = await rootRes.json()
        // 使用返回的 env 字段，优先使用后端返回的值
        mode.value = rootData.env || 'prod'
        console.log('Running mode:', mode.value, '(from server)')
      } else {
        mode.value = 'mock'
        console.log('Running mode: mock (fallback)')
      }
    } catch (err) {
      // 容错处理：请求失败时默认为 mock 模式
      console.warn('Health check failed, using mock mode:', err)
      mode.value = 'mock'
    }

    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('Fetch data error:', error)
  } finally {
    loading.value = false
    // 更新最后刷新时间
    const now = new Date()
    lastUpdateTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  }
}

// 处理自动刷新变化
const handleAutoRefreshChange = (interval: number) => {
  // 清除现有定时器
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }

  // 如果 interval > 0，启动自动刷新
  if (interval > 0) {
    autoRefreshTimer = window.setInterval(() => {
      fetchData()
    }, interval * 1000)
  }
}

// 查看告警事件
const viewWarningEvents = async () => {
  try {
    const res = await apiService.getEvents(1)
    warningEvents.value = res.data.events || []
    eventsDrawerVisible.value = true
  } catch (error) {
    ElMessage.error('获取告警事件失败')
    console.error('Get warning events error:', error)
  }
}

// ========== 终端弹窗相关方法 ==========

// 查看 Pod 日志（支持工作负载类型）
const viewPodLogs = async (kind: string, namespace: string, name: string) => {
  try {
    terminalTitle.value = `Pod Logs: ${kind}/${namespace}/${name}`
    terminalField.value = 'Logs'
    terminalTheme.value = true // 绿色主题
    terminalContent.value = '正在加载日志...'
    terminalDialogVisible.value = true

    // 优先使用工作负载日志接口
    const res = await apiService.getWorkloadLogs(kind, namespace, name, 500)
    terminalContent.value = res.data.logs || '暂无日志数据'
  } catch (error) {
    ElMessage.error('获取日志失败')
    console.error('Get pod logs error:', error)
    terminalContent.value = '无法获取日志：' + (error as Error).message
  }
}

// 查看资源详情（describe 格式）
const viewDescribe = async (kind: string, namespace: string, name: string) => {
  try {
    terminalTitle.value = `Resource Describe: ${namespace}/${name}`
    terminalField.value = 'Describe'
    terminalTheme.value = false // 白色主题
    terminalContent.value = '正在加载详情...'
    terminalDialogVisible.value = true

    const res = await apiService.getResourceDescribe(kind, namespace, name)
    // 格式化 describe 响应为文本显示
    const describeData = res.data || res
    let formattedContent = formatDescribeResponse(describeData)
    terminalContent.value = formattedContent
  } catch (error) {
    ElMessage.error('获取详情失败')
    console.error('Fetch describe error:', error)
    terminalContent.value = '无法获取详情：' + (error as Error).message
  }
}

// 格式化 describe 响应为文本
const formatDescribeResponse = (data: any): string => {
  const lines: string[] = []

  // 基本信息
  if (data.kind) lines.push(`Name: ${data.name}`)
  if (data.namespace) lines.push(`Namespace: ${data.namespace}`)
  if (data.apiVersion) lines.push(`API Version: ${data.apiVersion}`)
  if (data.kind) lines.push(`Kind: ${data.kind}`)
  lines.push('')

  // Labels
  if (data.labels && Object.keys(data.labels).length > 0) {
    lines.push('Labels:')
    Object.entries(data.labels).forEach(([key, value]) => {
      lines.push(`  ${key}=${value}`)
    })
    lines.push('')
  }

  // Annotations
  if (data.annotations && Object.keys(data.annotations).length > 0) {
    lines.push('Annotations:')
    Object.entries(data.annotations).forEach(([key, value]) => {
      lines.push(`  ${key}: ${value}`)
    })
    lines.push('')
  }

  // Status
  if (data.status && Object.keys(data.status).length > 0) {
    lines.push('Status:')
    lines.push(JSON.stringify(data.status, null, 2))
    lines.push('')
  }

  // Details
  if (data.details && Object.keys(data.details).length > 0) {
    lines.push('Details:')
    lines.push(JSON.stringify(data.details, null, 2))
    lines.push('')
  }

  // Events (核心内容)
  lines.push('Events:')
  if (data.events && Array.isArray(data.events) && data.events.length > 0) {
    data.events.forEach((event: any) => {
      const type = event.type || 'Normal'
      const reason = event.reason || 'Unknown'
      const message = event.message || ''
      const count = event.count || 1
      const firstSeen = event.first_seen || ''
      const lastSeen = event.last_seen || ''

      lines.push(`  Type: ${type}`)
      lines.push(`  Reason: ${reason}`)
      if (message) lines.push(`  Message: ${message}`)
      if (count > 1) lines.push(`  Count: ${count}`)
      if (firstSeen) lines.push(`  First Seen: ${firstSeen}`)
      if (lastSeen) lines.push(`  Last Seen: ${lastSeen}`)
      lines.push('')
    })
  } else {
    lines.push('  No events found.')
    lines.push('')
  }

  return lines.join('\n')
}

// 初始化
onMounted(() => {
  loadClusters()
  setupClusterChangeListener()
  fetchData()
  // 启动已配置的自动刷新
  if (autoRefreshInterval.value > 0) {
    handleAutoRefreshChange(autoRefreshInterval.value)
  }
})

// 清理 resize 监听和自动刷新定时器
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
})

</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.mode-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.header-logo {
  margin-right: 12px;
}

.update-time {
  font-size: 13px;
  color: #909399;
  background-color: #f5f7fa;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.stats-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  justify-content: center;
}

.stat-card-item {
  flex: 1 1 220px;
  max-width: 320px;
  min-width: 200px;
  width: 100%;
}

.stat-card-item .stat-card {
  height: 100%;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.stat-card.cert-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(233, 30, 99, 0.24);
  cursor: pointer;
  border: 1px solid #e91e63;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.nodes {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.healthy {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.stat-icon.pods {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-icon.storage {
  background: linear-gradient(135deg, #f5af19 0%, #f12711 100%);
  color: white;
}

.stat-icon.workload {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.stat-icon.events {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-icon.cert {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #e91e63;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 统计卡片 - 可点击样式 */
.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  border: 1px solid #409eff;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.tabs-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sub-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.text-danger {
  color: #f56c6c;
  font-weight: 500;
}

.events-header {
  margin-bottom: 16px;
  color: #606266;
}

.event-card {
  margin-bottom: 12px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-count {
  font-size: 13px;
  color: #909399;
}

.event-message {
  font-size: 14px;
  color: #303133;
  margin: 8px 0;
  line-height: 1.5;
}

.event-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
}

.event-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.text-warning {
  color: #e6a23c;
  font-weight: 500;
}

/* 终端风格弹窗样式 */
.terminal-dialog ::v-deep .el-dialog {
  background-color: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.terminal-dialog ::v-deep .el-dialog__header {
  background-color: #3c3c3c;
  padding: 10px 20px;
  border-bottom: 1px solid #2c2c2c;
}

.terminal-dialog ::v-deep .el-dialog__title {
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
}

.terminal-dialog ::v-deep .el-dialog__close {
  color: #ffffff;
  font-size: 16px;
}

.terminal-dialog ::v-deep .el-dialog__close:hover {
  color: #4caf50;
}

.terminal-window {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.terminal-header {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #3c3c3c;
  border-bottom: 1px solid #2c2c2c;
}

.terminal-dots {
  display: flex;
  gap: 6px;
  margin-right: 16px;
}

.terminal-dots .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.terminal-dots .dot.close {
  background-color: #ff5f56;
}

.terminal-dots .dot.minimize {
  background-color: #ffbd2e;
}

.terminal-dots .dot.maximize {
  background-color: #27c93f;
}

.terminal-title {
  color: #cccccc;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.terminal-content {
  flex: 1;
  overflow: auto;
  background-color: #000000;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.terminal-content .terminal-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #00ff00;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-content .green-text {
  color: #00ff00 !important;
  text-shadow: 0 0 2px rgba(0, 255, 0, 0.3);
}

.terminal-content .white-text {
  color: #ffffff !important;
}

.terminal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background-color: #3c3c3c;
  border-top: 1px solid #2c2c2c;
}

.terminal-footer .dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.terminal-footer .terminal-status {
  color: #cccccc;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.terminal-footer .terminal-status .el-icon {
  margin-right: 4px;
}

@media (max-width: 1024px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

/* 证书抽屉样式 */
.cert-drawer-content {
  padding: 20px;
}

.cert-drawer-content .el-alert {
  border-radius: 8px;
}

.cert-drawer-content .el-table {
  margin-top: 20px;
  border-radius: 8px;
  overflow: hidden;
}

.cert-drawer-content .el-table th.el-table__cell {
  background-color: #f5f7fa;
  color: #606266;
}

/* 告警事件抽屉样式 */
.events-drawer-content {
  padding: 20px;
}

.events-drawer-content .el-table {
  border-radius: 8px;
  overflow: hidden;
}

.events-drawer-content .el-table th.el-table__cell {
  background-color: #f5f7fa;
  color: #606266;
}

.events-drawer-content .el-table .el-table__cell {
  vertical-align: top;
}

.events-drawer-content .el-empty {
  margin-top: 30px;
}

/* 控制面状态样式 */
.control-plane-overview {
  margin-bottom: 24px;
}

.overview-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 4px;
  border-left: 4px solid #409eff;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.component-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 8px;
  padding: 20px 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.component-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.component-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.component-status {
  margin-bottom: 8px;
}

.status-icon {
  transition: all 0.3s ease;
}

.status-icon.healthy {
  color: #67c23a;
  text-shadow: 0 0 8px rgba(103, 194, 58, 0.3);
}

.status-icon.unhealthy {
  color: #f56c6c;
  text-shadow: 0 0 8px rgba(245, 108, 108, 0.3);
}

.component-detail {
  font-size: 12px;
  color: #909399;
  min-height: 18px;
}

.detail-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.all-components-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 24px 0 16px 0;
  padding-left: 4px;
  border-left: 4px solid #909399;
}

.core-tag {
  margin-left: 6px;
  font-size: 10px;
  padding: 2px 6px;
  background-color: #ffb800;
  color: #fff;
  border-radius: 3px;
  font-weight: 500;
}

@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
