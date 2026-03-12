import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface NodeInfo {
  name: string
  status: string
  cpu: string
  memory: string
  pods: number
  message?: string | null
}

export interface PodInfo {
  name: string
  namespace: string
  status: string
  restarts: number
  node: string
  message?: string | null
}

export interface PVCInfo {
  name: string
  namespace: string
  status: string
  capacity: string | null
  storage_class: string | null
  message?: string | null
}

export interface WorkloadInfo {
  name: string
  namespace: string
  kind: string
  desired_replicas: number
  ready_replicas: number
  available_replicas: number
  message?: string | null
}

export interface EventInfo {
  name: string
  namespace: string
  type: string
  reason: string
  message: string
  object_kind: string
  object_name: string
  count: number
  first_time: string
  last_time: string
}

export interface NodesResponse {
  nodes: NodeInfo[]
  total: number
  healthy: number
  unhealthy: number
}

export interface PodsResponse {
  pods: PodInfo[]
  total: number
  healthy: number
  unhealthy: number
}

export interface PVCsResponse {
  pvcs: PVCInfo[]
  total: number
  healthy: number
  unhealthy: number
}

export interface WorkloadsResponse {
  workloads: WorkloadInfo[]
  total: number
  healthy: number
  unhealthy: number
}

export interface EventsResponse {
  events: EventInfo[]
  total: number
}

export interface InspectionSummary {
  nodes: { total: number; unhealthy: number }
  pods: { total: number; unhealthy: number }
  pvcs: { total: number; unhealthy: number }
  workloads: { total: number; unhealthy: number }
  events: { total: number }
}

export interface ResourceUsage {
  cpu_capacity: number
  cpu_requests: number
  cpu_usage_percent: number
  memory_capacity: number
  memory_requests: number
  memory_usage_percent: number
}

export interface NamespacePodDist {
  namespace: string
  pod_count: number
}

export interface NamespaceDistResponse {
  distribution: NamespacePodDist[]
  total_namespaces: number
  total_pods: number
}

export interface PodLogsResponse {
  logs: string
}

export interface ResourceYamlResponse {
  yaml: string
}

// ===== 巡检异常相关类型 =====

export interface WorkloadAnomaly {
  name: string
  namespace: string
  kind: string
  desired_replicas: number
  ready_replicas: number
  status: string
  message?: string | null
  fatal_reason?: string | null
  restarts: number
  pod_status?: string | null  // Pod 实际状态
  age?: string | null  // 资源创建时间的易读字符串
}

export interface NetworkAnomaly {
  name: string
  namespace: string
  kind: string
  type: string
  status: string
  reason: string
  message?: string | null
}

export interface StorageAnomaly {
  name: string
  namespace: string
  kind: string
  status: string
  capacity?: string | null
  storage_class?: string | null
  message?: string | null
  reason: string
}

export interface NodePressure {
  name: string
  status: string
  cpu_capacity: string
  memory_capacity: string
  cpu_usage_percent?: number | null
  memory_usage_percent?: number | null
  pod_count: number
  pod_capacity: number
  message?: string | null
  pressure_type?: string | null
}

export interface ControlPlaneStatus {
  component: string
  status: string
  namespace: string
  pod_name: string
  restarts: number
  message?: string | null
  is_core: boolean
}

export interface CertificateInfo {
  name: string
  namespace: string
  expire_time: string
  remaining_days: number
  status: 'Valid' | 'Expired' | 'ExpiringSoon'
  message?: string | null
  secret_type: string
}

export interface CertificatesResponse {
  certificates: CertificateInfo[]
  total: number
  expired: number
  expiring_soon: number
}

export interface InspectionAnomaliesResponse {
  workload_anomalies: WorkloadAnomaly[]
  network_anomalies: NetworkAnomaly[]
  storage_anomalies: StorageAnomaly[]
  node_pressures: NodePressure[]
  control_plane_statuses: ControlPlaneStatus[]
}

export const apiService = {
  getNodes: () => api.get<NodesResponse>('/nodes'),
  getPods: () => api.get<PodsResponse>('/pods'),
  getPVCs: () => api.get<PVCsResponse>('/pvcs'),
  getWorkloads: () => api.get<WorkloadsResponse>('/workloads'),
  getEvents: (hours: number = 1) => api.get<EventsResponse>(`/events?hours=${hours}`),
  getSummary: () => api.get<InspectionSummary>('/inspection/summary'),
  getResourceUsage: () => api.get<ResourceUsage>('/metrics/resource-usage'),
  getNamespaceDistribution: () => api.get<NamespaceDistResponse>('/metrics/namespace-distribution'),
  getAnomalies: () => api.get<InspectionAnomaliesResponse>('/inspection/anomalies'),
  getCertificates: () => api.get<CertificatesResponse>('/inspection/certificates'),
  getPodLogs: (namespace: string, name: string, lines: number = 100) =>
    api.get<PodLogsResponse>(`/diagnostics/pod/${namespace}/${name}/logs?lines=${lines}`),
  getWorkloadLogs: (kind: string, namespace: string, name: string, lines: number = 100) =>
    api.get<PodLogsResponse>(`/diagnostics-workload/${kind}/${namespace}/${name}/logs?lines=${lines}`),
  getResourceYaml: (kind: string, namespace: string, name: string) =>
    api.get<ResourceYamlResponse>(`/diagnostics/${kind}/${namespace}/${name}/yaml`),
  getResourceDescribe: (kind: string, namespace: string, name: string) =>
    api.get<any>(`/diagnostics/${kind}/${namespace}/${name}/describe`),

  // 集群管理 API
  getClusters: () => api.get<ClustersResponse>('/clusters'),
  getActiveCluster: () => api.get<ActiveClusterResponse>('/clusters/active'),
  getClusterDetail: (id: number) => api.get<{ cluster: ClusterInfo }>(`/clusters/${id}`),
  createCluster: (data: ClusterCreateRequest) => api.post('/clusters', data),
  updateCluster: (id: number, data: ClusterUpdateRequest) => api.put(`/clusters/${id}`, data),
  deleteCluster: (id: number) => api.delete(`/clusters/${id}`),
  activateCluster: (id: number) => api.post(`/clusters/${id}/activate`),
  testClusterConnection: (kubeconfigContent: string) =>
    api.post<ClusterTestResult>('/clusters/test', { kubeconfig_content: kubeconfigContent }),
  getClusterInfo: (id: number) =>
    api.get<{ cluster: ClusterInfo; connection: ClusterTestResult }>(`/clusters/${id}/info`),
}

// ===== 集群管理相关类型 =====

export interface ClusterInfo {
  id: number
  name: string
  description?: string | null
  kubeconfig_path: string
  kubeconfig_content?: string | null
  is_active: number
  api_server_url?: string | null
  k8s_version?: string | null
  node_count?: number | null
  created_at: string
  updated_at: string
  last_connected_at?: string | null
  status: string
}

export interface ClustersResponse {
  clusters: ClusterInfo[]
  total: number
}

export interface ActiveClusterResponse {
  cluster: ClusterInfo | null
}

export interface ClusterTestResult {
  success: boolean
  message: string
  k8s_version: string
  node_count: number
  api_server_url: string
}

export interface ClusterCreateRequest {
  name: string
  description?: string
  kubeconfig_content: string
}

export interface ClusterUpdateRequest {
  name?: string
  description?: string
  kubeconfig_content?: string
}
