from typing import List, Dict
from schemas import NodeInfo, PodInfo, PVCInfo, WorkloadInfo, EventInfo, CertificateInfo
from datetime import datetime, timedelta


def get_mock_nodes() -> List[NodeInfo]:
    """返回模拟节点数据"""
    return [
        NodeInfo(
            name="node-1",
            status="Ready",
            cpu="4",
            memory="8Gi",
            pods=15,
            message=None
        ),
        NodeInfo(
            name="node-2",
            status="Ready",
            cpu="4",
            memory="8Gi",
            pods=12,
            message=None
        ),
        NodeInfo(
            name="node-3",
            status="Ready",
            cpu="8",
            memory="16Gi",
            pods=20,
            message=None
        ),
        NodeInfo(
            name="node-4",
            status="NotReady",
            cpu="4",
            memory="8Gi",
            pods=0,
            message="Kubelet stopped posting node status"
        ),
    ]


def get_mock_pods() -> List[PodInfo]:
    """返回模拟 Pod 数据"""
    return [
        PodInfo(
            name="nginx-deployment-7d5c8b9f4-abc12",
            namespace="default",
            status="Running",
            restarts=0,
            node="node-1",
            message=None
        ),
        PodInfo(
            name="nginx-deployment-7d5c8b9f4-def34",
            namespace="default",
            status="Running",
            restarts=0,
            node="node-2",
            message=None
        ),
        PodInfo(
            name="redis-master-0",
            namespace="default",
            status="Running",
            restarts=2,
            node="node-3",
            message=None
        ),
        PodInfo(
            name="api-server-5f6g7h8i9-xyz99",
            namespace="kube-system",
            status="CrashLoopBackOff",
            restarts=15,
            node="node-1",
            message="Back-off restarting failed container"
        ),
        PodInfo(
            name="worker-6j7k8l9m0-qwe88",
            namespace="default",
            status="CrashLoopBackOff",
            restarts=8,
            node="node-2",
            message="Error: CrashLoopBackOff"
        ),
        PodInfo(
            name="database-0",
            namespace="data",
            status="Pending",
            restarts=0,
            node="node-4",
            message="0/4 nodes are available: 1 node(s) had untolerated taint"
        ),
    ]


def get_mock_pvcs() -> List[PVCInfo]:
    """返回模拟 PVC 数据"""
    return [
        PVCInfo(
            name="data-redis-master-0",
            namespace="default",
            status="Bound",
            capacity="10Gi",
            storage_class="standard",
            message=None
        ),
        PVCInfo(
            name="data-redis-master-1",
            namespace="default",
            status="Bound",
            capacity="10Gi",
            storage_class="standard",
            message=None
        ),
        PVCInfo(
            name="data-mysql-0",
            namespace="data",
            status="Pending",
            capacity="50Gi",
            storage_class="fast-ssd",
            message="no persistent volumes available for this claim and no storage class is set"
        ),
        PVCInfo(
            name="logs-elasticsearch-0",
            namespace="logging",
            status="Lost",
            capacity="100Gi",
            storage_class="standard",
            message="the underlying PV is lost or deleted"
        ),
        PVCInfo(
            name="backup-postgres-0",
            namespace="data",
            status="Pending",
            capacity="20Gi",
            storage_class="nfs-storage",
            message="waiting for first consumer to be created before binding"
        ),
    ]


def get_mock_workloads() -> List[WorkloadInfo]:
    """返回模拟工作负载数据"""
    return [
        WorkloadInfo(
            name="nginx-deployment",
            namespace="default",
            kind="Deployment",
            desired_replicas=3,
            ready_replicas=3,
            available_replicas=3,
            message=None
        ),
        WorkloadInfo(
            name="api-server",
            namespace="kube-system",
            kind="Deployment",
            desired_replicas=3,
            ready_replicas=1,
            available_replicas=1,
            message="2 replicas are not ready"
        ),
        WorkloadInfo(
            name="redis-master",
            namespace="default",
            kind="StatefulSet",
            desired_replicas=3,
            ready_replicas=2,
            available_replicas=2,
            message="1 replica is pending"
        ),
        WorkloadInfo(
            name="mysql-primary",
            namespace="data",
            kind="StatefulSet",
            desired_replicas=1,
            ready_replicas=1,
            available_replicas=1,
            message=None
        ),
        WorkloadInfo(
            name="elasticsearch",
            namespace="logging",
            kind="StatefulSet",
            desired_replicas=3,
            ready_replicas=0,
            available_replicas=0,
            message="All replicas are failing to start"
        ),
    ]


def get_mock_events() -> List[EventInfo]:
    """返回模拟事件数据（过去 1 小时内的 Warning 事件）"""
    now = datetime.now()

    return [
        EventInfo(
            name="api-server-5f6g7h8i9-xyz99.17a2b3c4d5e6f7g8",
            namespace="kube-system",
            type="Warning",
            reason="BackOff",
            message="Back-off restarting failed container",
            object_kind="Pod",
            object_name="api-server-5f6g7h8i9-xyz99",
            count=15,
            first_time=now - timedelta(minutes=45),
            last_time=now - timedelta(minutes=2)
        ),
        EventInfo(
            name="worker-6j7k8l9m0-qwe88.17a2b3c4d5e6f7g9",
            namespace="default",
            type="Warning",
            reason="CrashLoopBackOff",
            message="Error: container exited with code 1",
            object_kind="Pod",
            object_name="worker-6j7k8l9m0-qwe88",
            count=8,
            first_time=now - timedelta(minutes=30),
            last_time=now - timedelta(minutes=5)
        ),
        EventInfo(
            name="data-mysql-0.17a2b3c4d5e6f7h0",
            namespace="data",
            type="Warning",
            reason="ProvisioningFailed",
            message="storageclass.storage.k8s.io \"fast-ssd\" not found",
            object_kind="PersistentVolumeClaim",
            object_name="data-mysql-0",
            count=3,
            first_time=now - timedelta(minutes=20),
            last_time=now - timedelta(minutes=10)
        ),
        EventInfo(
            name="elasticsearch-0.17a2b3c4d5e6f7h1",
            namespace="logging",
            type="Warning",
            reason="FailedScheduling",
            message="0/4 nodes are available: 4 Insufficient memory",
            object_kind="Pod",
            object_name="elasticsearch-0",
            count=12,
            first_time=now - timedelta(minutes=55),
            last_time=now - timedelta(minutes=1)
        ),
        EventInfo(
            name="node-4.17a2b3c4d5e6f7h2",
            namespace="",
            type="Warning",
            reason="NodeNotReady",
            message="Node node-4 status is now: NodeNotReady",
            object_kind="Node",
            object_name="node-4",
            count=1,
            first_time=now - timedelta(minutes=15),
            last_time=now - timedelta(minutes=15)
        ),
    ]


def get_mock_resource_usage() -> dict:
    """返回模拟资源使用数据"""
    # 总资源：4 个节点，共 20 核 CPU, 40Gi 内存
    # 已分配：CPU 14 核 (70%), 内存 28Gi (70%)
    return {
        "cpu_capacity": 20.0,
        "cpu_requests": 14.0,
        "cpu_usage_percent": 70.0,
        "memory_capacity": 40.0,
        "memory_requests": 28.0,
        "memory_usage_percent": 70.0
    }


def get_mock_namespace_dist() -> List[dict]:
    """返回模拟 Namespace Pod 分布"""
    return [
        {"namespace": "default", "pod_count": 5},
        {"namespace": "kube-system", "pod_count": 3},
        {"namespace": "data", "pod_count": 2},
        {"namespace": "logging", "pod_count": 3},
        {"namespace": "monitoring", "pod_count": 2},
    ]


def get_mock_pod_logs(pod_name: str) -> str:
    """返回模拟 Pod 日志"""
    from datetime import datetime, timedelta

    now = datetime.now()
    logs = []

    # 生成 50 行模拟日志
    for i in range(50):
        timestamp = (now - timedelta(seconds=i * 10)).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")

        if "api-server" in pod_name:
            log_messages = [
                "INFO Starting API server on port 8080",
                "INFO Connected to database",
                "WARN High latency detected: 500ms",
                "ERROR Failed to process request: timeout",
                "INFO Request processed successfully",
                "ERROR Connection reset by peer",
                "INFO Health check passed",
                "WARN Memory usage above threshold: 85%",
                "ERROR Panic: nil pointer dereference",
                "INFO Recovered from panic, restarting handler",
            ]
        elif "worker" in pod_name:
            log_messages = [
                "INFO Worker started",
                "INFO Processing job #12345",
                "INFO Job #12345 completed",
                "WARN Queue backlog increasing",
                "ERROR Failed to connect to Redis",
                "INFO Reconnected to Redis",
                "ERROR Out of memory while processing large payload",
                "FATAL Container OOMKilled",
            ]
        else:
            log_messages = [
                "INFO Application started",
                "INFO Listening on port 3000",
                "INFO Received SIGTERM, shutting down gracefully",
                "INFO Shutdown complete",
            ]

        log_msg = log_messages[i % len(log_messages)]
        logs.append(f"{timestamp} {log_msg}")

    # 反转日志，最新的在最后
    logs.reverse()
    return "\n".join(logs)


def get_mock_resource_yaml(kind: str, name: str) -> str:
    """返回模拟资源 YAML"""

    if kind.lower() == "pod":
        return f"""apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: default
  labels:
    app: demo
    version: v1
  annotations:
    kubernetes.io/created-by: "controller-manager"
spec:
  containers:
  - name: main
    image: nginx:1.21
    ports:
    - containerPort: 80
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
  restartPolicy: Always
  serviceAccountName: default
  nodeSelector:
    kubernetes.io/os: linux
status:
  phase: Running
  podIP: 10.244.1.15
  hostIP: 192.168.1.100
  startTime: "2026-03-10T10:00:00Z"
  conditions:
  - type: Initialized
    status: "True"
  - type: Ready
    status: "True"
  - type: ContainersReady
    status: "True"
  - type: PodScheduled
    status: "True"
  containerStatuses:
  - name: main
    ready: true
    restartCount: 3
    image: nginx:1.21
    state:
      running:
        startedAt: "2026-03-10T12:00:00Z"
"""
    elif kind.lower() == "node":
        return f"""apiVersion: v1
kind: Node
metadata:
  name: {name}
  labels:
    kubernetes.io/hostname: {name}
    node-role.kubernetes.io/worker: ""
  annotations:
    node.alpha.kubernetes.io/ttl: "0"
spec:
  taints:
  - key: node.kubernetes.io/not-ready
    effect: NoSchedule
  podCIDR: 10.244.1.0/24
status:
  conditions:
  - type: MemoryPressure
    status: "False"
  - type: DiskPressure
    status: "False"
  - type: PIDPressure
    status: "False"
  - type: Ready
    status: "True"
  addresses:
  - type: InternalIP
    address: 192.168.1.100
  - type: Hostname
    address: {name}
  daemonEndpoints:
    kubeletEndpoint:
      Port: 10250
  nodeInfo:
    machineID: abc123
    systemUUID: def456
    bootID: ghi789
    kernelVersion: 5.4.0-generic
    osImage: Ubuntu 22.04 LTS
    containerRuntimeVersion: containerd://1.6.0
    kubeletVersion: v1.28.0
    kubeProxyVersion: v1.28.0
    operatingSystem: linux
    architecture: amd64
  allocatable:
    cpu: "4"
    memory: 8Gi
    ephemeral-storage: 100Gi
    pods: "110"
"""
    else:
        return f"# Unsupported or unknown resource kind: {kind}\n"


def get_mock_resource_describe(kind: str, name: str) -> Dict:
    """返回模拟资源描述（Events 为主）"""
    import datetime

    base_event = {
        "type": "Normal",
        "reason": "MockEvent",
        "message": "This is a mock event for testing purposes",
        "count": 1,
        "first_seen": "",
        "last_seen": ""
    }

    if kind.lower() == "pod":
        return {
            "kind": "Pod",
            "name": name,
            "namespace": "default",
            "apiVersion": "v1",
            "labels": {
                "app": "demo",
                "version": "v1"
            },
            "annotations": {
                "kubernetes.io/created-by": "controller-manager"
            },
            "status": {
                "phase": "Running",
                "conditions": [
                    {"type": "Ready", "status": "True"},
                    {"type": "ContainersReady", "status": "True"}
                ]
            },
            "details": {
                "node_name": "node-1",
                "service_account": "default",
                "created": str(datetime.datetime.now(datetime.timezone.utc))
            },
            "events": [
                {
                    "type": "Normal",
                    "reason": "Scheduled",
                    "message": f"Successfully assigned default/{name} to node-1",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                },
                {
                    "type": "Normal",
                    "reason": "Pulling",
                    "message": f"Pulling image \"nginx:1.21\"",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                },
                {
                    "type": "Normal",
                    "reason": "Pulled",
                    "message": "Container image \"nginx:1.21\" already present on machine",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                },
                {
                    "type": "Normal",
                    "reason": "Created",
                    "message": "Created container main",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                },
                {
                    "type": "Normal",
                    "reason": "Started",
                    "message": "Started container main",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                }
            ]
        }
    elif kind.lower() == "deployment":
        return {
            "kind": "Deployment",
            "name": name,
            "namespace": "default",
            "apiVersion": "apps/v1",
            "labels": {
                "app": "demo"
            },
            "annotations": {},
            "status": {
                "replicas": 3,
                "updated_replicas": 3,
                "ready_replicas": 3,
                "available_replicas": 3
            },
            "details": {
                "replicas": {
                    "desired": 3,
                    "updated": 3,
                    "ready": 3,
                    "available": 3
                },
                "created": str(datetime.datetime.now(datetime.timezone.utc))
            },
            "events": [
                {
                    "type": "Normal",
                    "reason": "ScalingReplicaSet",
                    "message": f"Set replica count for {name}-abc123 to 3",
                    "count": 1,
                    "first_seen": str(datetime.datetime.now(datetime.timezone.utc)),
                    "last_seen": str(datetime.datetime.now(datetime.timezone.utc))
                }
            ]
        }
    elif kind.lower() == "service":
        return {
            "kind": "Service",
            "name": name,
            "namespace": "default",
            "apiVersion": "v1",
            "labels": {},
            "annotations": {},
            "status": {
                "loadBalancer": {}
            },
            "details": {
                "cluster_ip": "10.96.0.1",
                "created": str(datetime.datetime.now(datetime.timezone.utc))
            },
            "events": [base_event]
        }
    elif kind.lower() == "node":
        return {
            "kind": "Node",
            "name": name,
            "namespace": "",
            "apiVersion": "v1",
            "labels": {
                "kubernetes.io/hostname": name,
                "node-role.kubernetes.io/worker": ""
            },
            "annotations": {},
            "status": {
                "conditions": [
                    {"type": "Ready", "status": "True"}
                ]
            },
            "details": {
                "created": str(datetime.datetime.now(datetime.timezone.utc))
            },
            "events": [base_event]
        }
    else:
        return {
            "kind": kind,
            "name": name,
            "namespace": "default",
            "apiVersion": "",
            "labels": {},
            "annotations": {},
            "status": {},
            "details": {},
            "events": [base_event]
        }


# ===== 模拟巡检异常数据 =====

def get_mock_workload_anomalies() -> List:
    """返回模拟工作负载异常数据"""
    from schemas import WorkloadAnomaly

    return [
        WorkloadAnomaly(
            name="api-server",
            namespace="kube-system",
            kind="Deployment",
            desired_replicas=3,
            ready_replicas=1,
            status="CrashLoopBackOff",
            message="Back-off restarting failed container",
            fatal_reason="OOMKilled",
            restarts=15
        ),
        WorkloadAnomaly(
            name="payment-service",
            namespace="default",
            kind="Deployment",
            desired_replicas=2,
            ready_replicas=0,
            status="ImagePullFailed",
            message="Error: ImagePullBackOff: failed to pull image registry.example.com/payment:v2.1.0",
            fatal_reason="镜像拉取失败",
            restarts=0
        ),
        WorkloadAnomaly(
            name="redis-cluster",
            namespace="data",
            kind="StatefulSet",
            desired_replicas=6,
            ready_replicas=4,
            status="ReplicaMismatch",
            message="2 replicas are not ready",
            fatal_reason=None,
            restarts=3
        ),
    ]


def get_mock_network_anomalies() -> List:
    """返回模拟网络服务异常数据"""
    from schemas import NetworkAnomaly

    return [
        NetworkAnomaly(
            name="backend-api",
            namespace="default",
            kind="Service",
            type="ClusterIP",
            status="NoEndpoints",
            reason="无存活 Endpoint",
            message="Service 没有可用的后端 Pod"
        ),
        NetworkAnomaly(
            name="metrics-server",
            namespace="kube-system",
            kind="Service",
            type="ClusterIP",
            status="NoEndpoints",
            reason="无存活 Endpoint",
            message="Service 没有可用的后端 Pod"
        ),
    ]


def get_mock_storage_anomalies() -> List:
    """返回模拟存储卷异常数据"""
    from schemas import StorageAnomaly

    return [
        StorageAnomaly(
            name="data-mysql-0",
            namespace="data",
            kind="PVC",
            status="Pending",
            capacity="50Gi",
            storage_class="fast-ssd",
            message="no persistent volumes available for this claim and no storage class is set",
            reason="NoStorageClass"
        ),
        StorageAnomaly(
            name="logs-elasticsearch-0",
            namespace="logging",
            kind="PVC",
            status="Lost",
            capacity="100Gi",
            storage_class="standard",
            message="底层 PV 已丢失或被删除",
            reason="PVLost"
        ),
        StorageAnomaly(
            name="backup-postgres-0",
            namespace="data",
            kind="PVC",
            status="Pending",
            capacity="20Gi",
            storage_class="nfs-storage",
            message="waiting for first consumer to be created before binding",
            reason="等待 PV 绑定"
        ),
    ]


def get_mock_node_pressures() -> List:
    """返回模拟节点压力数据"""
    from schemas import NodePressure

    return [
        NodePressure(
            name="node-1",
            status="Ready",
            cpu_capacity="4",
            memory_capacity="8Gi",
            cpu_usage_percent=75.0,
            memory_usage_percent=82.0,
            pod_count=25,
            pod_capacity=110,
            message=None,
            pressure_type=None
        ),
        NodePressure(
            name="node-2",
            status="Ready",
            cpu_capacity="4",
            memory_capacity="8Gi",
            cpu_usage_percent=45.0,
            memory_usage_percent=55.0,
            pod_count=18,
            pod_capacity=110,
            message=None,
            pressure_type=None
        ),
        NodePressure(
            name="node-3",
            status="MemoryPressure",
            cpu_capacity="8",
            memory_capacity="16Gi",
            cpu_usage_percent=60.0,
            memory_usage_percent=95.0,
            pod_count=35,
            pod_capacity=110,
            message="kubelet has insufficient memory available",
            pressure_type="MemoryPressure"
        ),
        NodePressure(
            name="node-4",
            status="NotReady",
            cpu_capacity="4",
            memory_capacity="8Gi",
            cpu_usage_percent=None,
            memory_usage_percent=None,
            pod_count=0,
            pod_capacity=110,
            message="Kubelet stopped posting node status",
            pressure_type=None
        ),
    ]


def get_mock_control_plane_statuses() -> List:
    """返回模拟控制面状态数据"""
    from schemas import ControlPlaneStatus

    return [
        ControlPlaneStatus(
            component="etcd",
            status="Running",
            namespace="kube-system",
            pod_name="etcd-node-1",
            restarts=0,
            message=None,
            is_core=True
        ),
        ControlPlaneStatus(
            component="kube-apiserver",
            status="Running",
            namespace="kube-system",
            pod_name="kube-apiserver-node-1",
            restarts=0,
            message=None,
            is_core=True
        ),
        ControlPlaneStatus(
            component="kube-scheduler",
            status="Running",
            namespace="kube-system",
            pod_name="kube-scheduler-node-1",
            restarts=2,
            message=None,
            is_core=True
        ),
        ControlPlaneStatus(
            component="kube-controller-manager",
            status="Running",
            namespace="kube-system",
            pod_name="kube-controller-manager-node-1",
            restarts=1,
            message=None,
            is_core=True
        ),
        ControlPlaneStatus(
            component="coredns",
            status="CrashLoopBackOff",
            namespace="kube-system",
            pod_name="coredns-7d5c8b9f4-abc12",
            restarts=8,
            message="Back-off restarting failed container",
            is_core=True
        ),
        ControlPlaneStatus(
            component="kube-proxy",
            status="Running",
            namespace="kube-system",
            pod_name="kube-proxy-node-1",
            restarts=0,
            message=None,
            is_core=True
        ),
    ]


def get_mock_certificates() -> List[CertificateInfo]:
    """返回模拟证书数据"""
    now = datetime.now()

    return [
        CertificateInfo(
            name="apiserver-secret",
            namespace="kube-system",
            expire_time=now + timedelta(days=15),
            remaining_days=15,
            status="ExpiringSoon",
            message="证书将在 15 天后过期",
            secret_type="kubernetes.io/tls"
        ),
        CertificateInfo(
            name="controller-manager-secret",
            namespace="kube-system",
            expire_time=now + timedelta(days=25),
            remaining_days=25,
            status="ExpiringSoon",
            message="证书将在 25 天后过期",
            secret_type="kubernetes.io/tls"
        ),
        CertificateInfo(
            name="scheduler-secret",
            namespace="kube-system",
            expire_time=now + timedelta(days=60),
            remaining_days=60,
            status="Valid",
            message="证书有效期至 2026-05-10",
            secret_type="kubernetes.io/tls"
        ),
        CertificateInfo(
            name="ingress-tls-secret",
            namespace="default",
            expire_time=now - timedelta(days=5),
            remaining_days=-5,
            status="Expired",
            message="证书已过期 5 天",
            secret_type="kubernetes.io/tls"
        ),
        CertificateInfo(
            name="monitoring-cert",
            namespace="monitoring",
            expire_time=now + timedelta(days=45),
            remaining_days=45,
            status="Valid",
            message="证书有效期至 2026-04-25",
            secret_type="kubernetes.io/tls"
        ),
    ]
