from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class NodeInfo(BaseModel):
    name: str
    status: str
    cpu: str
    memory: str
    pods: int
    message: Optional[str] = None


class PodInfo(BaseModel):
    name: str
    namespace: str
    status: str
    restarts: int
    node: str
    message: Optional[str] = None


class NodesResponse(BaseModel):
    nodes: List[NodeInfo]
    total: int
    healthy: int
    unhealthy: int


class PodsResponse(BaseModel):
    pods: List[PodInfo]
    total: int
    healthy: int
    unhealthy: int


# PVC 相关模型
class PVCInfo(BaseModel):
    name: str
    namespace: str
    status: str  # Bound, Pending, Lost
    capacity: Optional[str] = None
    storage_class: Optional[str] = None
    message: Optional[str] = None


class PVCsResponse(BaseModel):
    pvcs: List[PVCInfo]
    total: int
    healthy: int
    unhealthy: int


# 工作负载相关模型
class WorkloadInfo(BaseModel):
    name: str
    namespace: str
    kind: str  # Deployment, StatefulSet
    desired_replicas: int
    ready_replicas: int
    available_replicas: int
    message: Optional[str] = None


class WorkloadsResponse(BaseModel):
    workloads: List[WorkloadInfo]
    total: int
    healthy: int
    unhealthy: int


# 事件相关模型
class EventInfo(BaseModel):
    name: str
    namespace: str
    type: str  # Warning, Normal
    reason: str
    message: str
    object_kind: str
    object_name: str
    count: int
    first_time: datetime
    last_time: datetime


class EventsResponse(BaseModel):
    events: List[EventInfo]
    total: int


# 资源使用率相关模型
class ResourceUsage(BaseModel):
    cpu_capacity: float  # 总 CPU (核)
    cpu_requests: float  # 已请求 CPU (核)
    cpu_usage_percent: float  # CPU 使用率
    memory_capacity: float  # 总内存 (Gi)
    memory_requests: float  # 已请求内存 (Gi)
    memory_usage_percent: float  # 内存使用率


# Namespace 分布模型
class NamespacePodDist(BaseModel):
    namespace: str
    pod_count: int


class NamespaceDistResponse(BaseModel):
    distribution: List[NamespacePodDist]
    total_namespaces: int
    total_pods: int


# ===== 巡检异常相关模型 =====

class WorkloadAnomaly(BaseModel):
    """工作负载异常"""
    name: str
    namespace: str
    kind: str  # Deployment, StatefulSet, DaemonSet
    desired_replicas: int
    ready_replicas: int
    status: str  # ReplicaMismatch, ImagePullFailed, CrashLoopBackOff, OOMKilled
    message: Optional[str] = None
    fatal_reason: Optional[str] = None  # 致命原因：OOMKilled, 镜像拉取失败等
    restarts: int = 0
    pod_status: Optional[str] = None  # Pod 实际状态：Pending, Running, Failed 等
    age: Optional[str] = None  # 资源创建时间的易读字符串


class NetworkAnomaly(BaseModel):
    """网络服务异常"""
    name: str
    namespace: str
    kind: str  # Service, Ingress
    type: str  # ClusterIP, NodePort, LoadBalancer
    status: str  # NoEndpoints, IngressError
    reason: str  # 固定显示"无存活 Endpoint"等
    message: Optional[str] = None


class StorageAnomaly(BaseModel):
    """存储卷异常"""
    name: str
    namespace: str
    kind: str  # PVC, PV
    status: str  # Pending, Lost, BindingFailed
    capacity: Optional[str] = None
    storage_class: Optional[str] = None
    message: Optional[str] = None
    reason: str  # 原因：NoStorageClass, PVLost, BindingFailed


class NodePressure(BaseModel):
    """节点与资源压力"""
    name: str
    status: str  # Ready, NotReady, MemoryPressure, DiskPressure, PIDPressure
    cpu_capacity: str
    memory_capacity: str
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    pod_count: int
    pod_capacity: int
    message: Optional[str] = None
    pressure_type: Optional[str] = None  # MemoryPressure, DiskPressure, PIDPressure


class ControlPlaneStatus(BaseModel):
    """控制面状态"""
    component: str  # etcd, kube-apiserver, kube-scheduler, kube-controller-manager, coredns, kube-proxy
    status: str  # Running, NotReady, CrashLoopBackOff, Unhealthy
    namespace: str
    pod_name: str
    restarts: int
    message: Optional[str] = None
    is_core: bool = True  # 是否为核心组件


class AnomalyGroup(BaseModel):
    """分组异常数据"""
    category: str  # workload, network, storage, node_pressure, control_plane
    title: str  # 中文标题
    total: int
    unhealthy: int
    items: List


class InspectionAnomaliesResponse(BaseModel):
    """巡检异常响应"""
    workload_anomalies: List[WorkloadAnomaly]
    network_anomalies: List[NetworkAnomaly]
    storage_anomalies: List[StorageAnomaly]
    node_pressures: List[NodePressure]
    control_plane_statuses: List[ControlPlaneStatus]


# 证书相关模型
class CertificateInfo(BaseModel):
    """证书信息"""
    name: str  # Secret 名称
    namespace: str
    expire_time: datetime  # 过期时间
    remaining_days: int  # 剩余天数
    status: str  # Valid, Expired, ExpiringSoon
    message: Optional[str] = None
    secret_type: str = "kubernetes.io/tls"  # 证书类型


class CertificatesResponse(BaseModel):
    """证书响应"""
    certificates: List[CertificateInfo]
    total: int
    expired: int
    expiring_soon: int  # 30天内过期
