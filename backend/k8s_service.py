from kubernetes import client, config
from typing import List, Optional, Dict, Union, Tuple
import logging
import re
from datetime import datetime, timedelta, timezone

from schemas import (
    NodeInfo, PodInfo, PVCInfo, WorkloadInfo, EventInfo,
    NamespacePodDist,
    WorkloadAnomaly, NetworkAnomaly, StorageAnomaly,
    NodePressure, ControlPlaneStatus, CertificateInfo
)
from cluster_manager import cluster_manager

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def parse_k8s_cpu(cpu_str: Union[str, int, float]) -> float:
    """
    解析 K8s CPU 资源字符串，返回核心数 (float)

    支持的格式:
    - "4" -> 4.0 核心
    - "4000m" -> 4.0 核心 (milliCPU)
    - "0.5" -> 0.5 核心
    - "500000000" -> 0.5 核心 (nanoCPU)
    - 4 (int) -> 4.0 核心
    """
    if cpu_str is None:
        return 0.0

    # 如果是数字类型直接返回
    if isinstance(cpu_str, (int, float)):
        return float(cpu_str)

    cpu_str = str(cpu_str).strip()
    if not cpu_str:
        return 0.0

    try:
        # 处理 milliCPU (例如 "4000m")
        if cpu_str.endswith("m"):
            return float(cpu_str[:-1]) / 1000

        # 处理 nanoCPU (纯数字但很大，例如 "500000000")
        if cpu_str.isdigit():
            value = float(cpu_str)
            # 如果值大于 100000，可能是 nanoCPU
            if value > 100000:
                return value / 1e9
            return value

        # 处理小数
        return float(cpu_str)
    except (ValueError, TypeError):
        logger.warning(f"无法解析 CPU 值：{cpu_str}")
        return 0.0


def parse_k8s_memory(mem_str: Union[str, int, float]) -> float:
    """
    解析 K8s 内存资源字符串，返回 GiB (float)

    支持的格式:
    - "8Gi" -> 8.0 GiB
    - "8192Mi" -> 8.0 GiB
    - "8388608Ki" -> 8.0 GiB
    - "8589934592" -> 8.0 GiB (bytes)
    - "8G" -> 8.0 GB (十进制，约 7.45 GiB)
    - "8M" -> 8.0 MB (十进制)
    - "8K" -> 8.0 KB (十进制)
    - 8589934592 (int) -> 8.0 GiB (bytes)

    K8s 使用二进制单位:
    - Ki = Kibibyte = 1024 bytes
    - Mi = Mebibyte = 1024 Ki = 1,048,576 bytes
    - Gi = Gibibyte = 1024 Mi = 1,073,741,824 bytes
    - Ti = Tebibyte = 1024 Gi
    """
    if mem_str is None:
        return 0.0

    # 如果是数字类型，假设是 bytes
    if isinstance(mem_str, (int, float)):
        return float(mem_str) / (1024 ** 3)

    mem_str = str(mem_str).strip()
    if not mem_str:
        return 0.0

    try:
        # 二进制单位 (K8s 标准)
        if mem_str.endswith("Ki"):
            return float(mem_str[:-2]) / (1024 ** 2)  # Ki -> Gi
        elif mem_str.endswith("Mi"):
            return float(mem_str[:-2]) / 1024  # Mi -> Gi
        elif mem_str.endswith("Gi"):
            return float(mem_str[:-2])  # Gi
        elif mem_str.endswith("Ti"):
            return float(mem_str[:-2]) * 1024  # Ti -> Gi

        # 十进制单位 (SI 标准，较少使用)
        elif mem_str.endswith("K") and not mem_str.endswith("Ki"):
            return float(mem_str[:-1]) * 1000 / (1024 ** 3)  # KB -> Gi
        elif mem_str.endswith("M") and not mem_str.endswith("Mi"):
            return float(mem_str[:-1]) * 1000000 / (1024 ** 3)  # MB -> Gi
        elif mem_str.endswith("G") and not mem_str.endswith("Gi"):
            return float(mem_str[:-1]) * 1000000000 / (1024 ** 3)  # GB -> Gi

        # 纯数字，假设是 bytes
        return float(mem_str) / (1024 ** 3)

    except (ValueError, TypeError):
        logger.warning(f"无法解析内存值：{mem_str}")
        return 0.0


class K8sService:
    def __init__(self):
        self._core_v1 = None
        self._apps_v1 = None
        self._batch_v1 = None

    def _get_core_client(self):
        """获取 CoreV1 客户端（使用集群管理器）"""
        return cluster_manager.get_core_client()

    def _get_apps_client(self):
        """获取 AppsV1 客户端（使用集群管理器）"""
        return cluster_manager.get_apps_client()

    def _get_batch_client(self):
        """获取 BatchV1 客户端（使用集群管理器）"""
        return cluster_manager.get_batch_client()

    async def get_nodes(self) -> List[NodeInfo]:
        """获取集群节点列表"""
        v1 = self._get_core_client()
        nodes_list = v1.list_node()

        result = []
        for node in nodes_list.items:
            status = "Ready"
            message = None

            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status != "True":
                    status = "NotReady"
                    message = condition.message
                    break

            cpu = node.status.allocatable.get("cpu", "unknown") if node.status.allocatable else "unknown"
            memory = node.status.allocatable.get("memory", "unknown") if node.status.allocatable else "unknown"

            result.append(NodeInfo(
                name=node.metadata.name,
                status=status,
                cpu=str(cpu),
                memory=str(memory),
                pods=0,
                message=message
            ))

        return result

    async def get_pods(self) -> List[PodInfo]:
        """获取集群所有 Pod 列表"""
        v1 = self._get_core_client()
        pods_list = v1.list_pod_for_all_namespaces()

        result = []
        for pod in pods_list.items:
            status = "Unknown"
            message = None
            restarts = 0

            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    restarts += cs.restart_count
                    if cs.state.waiting:
                        status = cs.state.waiting.reason
                        message = cs.state.waiting.message
                    elif cs.state.terminated:
                        status = cs.state.terminated.reason
                        message = cs.state.terminated.message
                    elif cs.state.running:
                        status = "Running"

            result.append(PodInfo(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace or "default",
                status=status,
                restarts=restarts,
                node=pod.spec.node_name or "unknown",
                message=message
            ))

        return result

    async def get_pvcs(self) -> List[PVCInfo]:
        """获取所有 PVC 列表"""
        v1 = self._get_core_client()
        pvcs_list = v1.list_persistent_volume_claim_for_all_namespaces()

        result = []
        for pvc in pvcs_list.items:
            status = pvc.status.phase
            message = None

            # 检查是否有绑定错误
            if status == "Pending" and pvc.spec.volume_name:
                message = "Waiting for PV binding"
            elif pvc.status.conditions:
                for cond in pvc.status.conditions:
                    if cond.type == "FileSystemResizePending":
                        message = cond.message

            # 获取容量
            capacity = None
            if pvc.status.capacity:
                capacity = pvc.status.capacity.get("storage", "unknown")
            elif pvc.spec.resources.requests:
                capacity = pvc.spec.resources.requests.get("storage", "unknown")

            result.append(PVCInfo(
                name=pvc.metadata.name,
                namespace=pvc.metadata.namespace or "default",
                status=status,
                capacity=capacity,
                storage_class=pvc.spec.storage_class_name,
                message=message
            ))

        return result

    async def get_workloads(self) -> List[WorkloadInfo]:
        """获取所有工作负载（Deployment 和 StatefulSet）"""
        apps_v1 = self._get_apps_client()
        result = []

        # 获取 Deployments
        deployments = apps_v1.list_deployment_for_all_namespaces()
        for deploy in deployments.items:
            desired = deploy.spec.replicas or 0
            ready = deploy.status.ready_replicas or 0
            available = deploy.status.available_replicas or 0

            message = None
            if ready < desired:
                message = f"{desired - ready} replicas are not ready"

            result.append(WorkloadInfo(
                name=deploy.metadata.name,
                namespace=deploy.metadata.namespace or "default",
                kind="Deployment",
                desired_replicas=desired,
                ready_replicas=ready,
                available_replicas=available,
                message=message
            ))

        # 获取 StatefulSets
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        for sts in statefulsets.items:
            desired = sts.spec.replicas or 0
            ready = sts.status.ready_replicas or 0
            available = sts.status.available_replicas or 0

            message = None
            if ready < desired:
                message = f"{desired - ready} replicas are not ready"

            result.append(WorkloadInfo(
                name=sts.metadata.name,
                namespace=sts.metadata.namespace or "default",
                kind="StatefulSet",
                desired_replicas=desired,
                ready_replicas=ready,
                available_replicas=available,
                message=message
            ))

        return result

    async def get_warning_events(self, hours: int = 1) -> List[EventInfo]:
        """获取过去 N 小时内的 Warning 事件"""
        v1 = self._get_core_client()
        events_list = v1.list_event_for_all_namespaces()

        result = []
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)

        for event in events_list.items:
            # 只筛选 Warning 类型事件
            if event.type != "Warning":
                continue

            # 获取事件时间
            event_time = None
            if event.last_timestamp:
                event_time = event.last_timestamp.replace(tzinfo=None)
            elif event.event_time:
                event_time = event.event_time.replace(tzinfo=None)

            # 过滤掉超出时间范围的事件
            if event_time and event_time < cutoff:
                continue

            # 转换时间为本地时间（近似）
            first_time = event.first_timestamp.replace(tzinfo=None) if event.first_timestamp else now
            last_time = event_time or now

            result.append(EventInfo(
                name=event.metadata.name,
                namespace=event.metadata.namespace or "default",
                type=event.type,
                reason=event.reason,
                message=event.message or "",
                object_kind=event.involved_object.kind,
                object_name=event.involved_object.name,
                count=event.count or 1,
                first_time=first_time,
                last_time=last_time
            ))

        # 按最后发生时间排序，最新的在前
        result.sort(key=lambda x: x.last_time, reverse=True)

        return result

    async def get_resource_usage(self) -> Dict:
        """获取集群资源使用情况"""
        v1 = self._get_core_client()

        cpu_capacity = 0.0
        memory_capacity = 0.0
        cpu_requests = 0.0
        memory_requests = 0.0

        # 获取节点资源容量
        nodes_list = v1.list_node()
        for node in nodes_list.items:
            if node.status.allocatable:
                cpu_str = node.status.allocatable.get("cpu", "0")
                mem_str = node.status.allocatable.get("memory", "0")

                # 使用辅助函数解析 CPU 和内存
                cpu_capacity += parse_k8s_cpu(cpu_str)
                memory_capacity += parse_k8s_memory(mem_str)

        # 获取 Pod 资源请求
        pods_list = v1.list_pod_for_all_namespaces()
        for pod in pods_list.items:
            if pod.status.phase == "Running":
                for container in pod.spec.containers:
                    if container.resources.requests:
                        cpu_req = container.resources.requests.get("cpu", "0")
                        mem_req = container.resources.requests.get("memory", "0")

                        # 使用辅助函数解析 CPU 和内存
                        cpu_requests += parse_k8s_cpu(cpu_req)
                        memory_requests += parse_k8s_memory(mem_req)

        # 计算使用率
        cpu_usage_percent = round((cpu_requests / cpu_capacity * 100) if cpu_capacity > 0 else 0, 1)
        memory_usage_percent = round((memory_requests / memory_capacity * 100) if memory_capacity > 0 else 0, 1)

        return {
            "cpu_capacity": round(cpu_capacity, 1),
            "cpu_requests": round(cpu_requests, 1),
            "cpu_usage_percent": cpu_usage_percent,
            "memory_capacity": round(memory_capacity, 1),
            "memory_requests": round(memory_requests, 1),
            "memory_usage_percent": memory_usage_percent
        }

    async def get_namespace_distribution(self) -> List[NamespacePodDist]:
        """获取各 Namespace 的 Pod 数量分布"""
        v1 = self._get_core_client()
        pods_list = v1.list_pod_for_all_namespaces()

        ns_count: Dict[str, int] = {}
        for pod in pods_list.items:
            ns = pod.metadata.namespace or "default"
            ns_count[ns] = ns_count.get(ns, 0) + 1

        result = [
            NamespacePodDist(namespace=ns, pod_count=count)
            for ns, count in ns_count.items()
        ]

        # 按 Pod 数量降序排序
        result.sort(key=lambda x: x.pod_count, reverse=True)

        return result

    async def get_pod_logs(self, namespace: str, pod_name: str, lines: int = 100) -> str:
        """获取指定 Pod 的最新日志"""
        v1 = self._get_core_client()
        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=lines,
                timestamps=True
            )
            return logs
        except Exception as e:
            return f"Error fetching logs: {str(e)}"

    async def get_workload_logs(self, kind: str, namespace: str, name: str, lines: int = 100) -> str:
        """获取指定工作负载的第一个 Pod 的日志"""
        v1 = self._get_core_client()
        apps_v1 = self._get_apps_client()
        batch_v1 = self._get_batch_client()

        kind_lower = kind.lower()
        label_selector = ""

        try:
            # 根据工作负载类型获取 label selector
            if kind_lower == "deployment":
                deploy = apps_v1.read_namespaced_deployment(name, namespace)
                if deploy.spec and deploy.spec.selector:
                    # 尝试 match_labels
                    if deploy.spec.selector.match_labels:
                        label_selector = ",".join(f"{k}={v}" for k, v in deploy.spec.selector.match_labels.items())
                    # 尝试 match_expressions（处理复杂选择器）
                    elif deploy.spec.selector.match_expressions:
                        exprs = []
                        for expr in deploy.spec.selector.match_expressions:
                            if expr.operator == "In":
                                exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                            elif expr.operator == "NotIn":
                                exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                            elif expr.operator == "Exists":
                                exprs.append(expr.key)
                        label_selector = ",".join(exprs)
            elif kind_lower == "statefulset":
                sts = apps_v1.read_namespaced_stateful_set(name, namespace)
                if sts.spec and sts.spec.selector:
                    if sts.spec.selector.match_labels:
                        label_selector = ",".join(f"{k}={v}" for k, v in sts.spec.selector.match_labels.items())
                    elif sts.spec.selector.match_expressions:
                        exprs = []
                        for expr in sts.spec.selector.match_expressions:
                            if expr.operator == "In":
                                exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                            elif expr.operator == "NotIn":
                                exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                            elif expr.operator == "Exists":
                                exprs.append(expr.key)
                        label_selector = ",".join(exprs)
            elif kind_lower == "daemonset":
                ds = apps_v1.read_namespaced_daemon_set(name, namespace)
                if ds.spec and ds.spec.selector:
                    if ds.spec.selector.match_labels:
                        label_selector = ",".join(f"{k}={v}" for k, v in ds.spec.selector.match_labels.items())
                    elif ds.spec.selector.match_expressions:
                        exprs = []
                        for expr in ds.spec.selector.match_expressions:
                            if expr.operator == "In":
                                exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                            elif expr.operator == "NotIn":
                                exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                            elif expr.operator == "Exists":
                                exprs.append(expr.key)
                        label_selector = ",".join(exprs)
            elif kind_lower == "job":
                job = batch_v1.read_namespaced_job(name, namespace)
                if job.spec and job.spec.selector:
                    if job.spec.selector.match_labels:
                        label_selector = ",".join(f"{k}={v}" for k, v in job.spec.selector.match_labels.items())
                    elif job.spec.selector.match_expressions:
                        exprs = []
                        for expr in job.spec.selector.match_expressions:
                            if expr.operator == "In":
                                exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                            elif expr.operator == "NotIn":
                                exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                            elif expr.operator == "Exists":
                                exprs.append(expr.key)
                        label_selector = ",".join(exprs)
            elif kind_lower == "pod":
                # 直接获取 pod 日志
                pods = v1.list_namespaced_pod(namespace, field_selector=f"metadata.name={name}")
                if not pods.items:
                    return "当前工作负载下没有找到任何运行中的 Pod。"
                pod_name = pods.items[0].metadata.name
                return await self.get_pod_logs(namespace, pod_name, lines)
            else:
                return f"不支持的工作负载类型: {kind}"
        except Exception as e:
            return f"获取工作负载信息失败: {str(e)}"

        # 如果没有 label selector，返回提示
        if not label_selector:
            return "无法获取工作负载的标签选择器。"

        # 根据 label selector 查询关联的 Pod
        try:
            pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)

            # 如果列表为空，返回提示
            if not pods.items:
                return "当前工作负载下没有找到任何运行中的 Pod。"

            # 取第一个 Pod 的名字，然后拉取日志
            first_pod_name = pods.items[0].metadata.name
            return await self.get_pod_logs(namespace, first_pod_name, lines)
        except Exception as e:
            return f"获取 Pod 日志失败: {str(e)}"

    async def get_resource_yaml(self, kind: str, namespace: str, name: str) -> str:
        """获取指定资源的 YAML 描述（运维规范版）"""
        from kubernetes.client import ApiClient

        v1 = self._get_core_client()
        apps_v1 = self._get_apps_client()
        api_client = ApiClient()

        try:
            kind_lower = kind.lower()
            if kind_lower == "pod":
                resource = v1.read_namespaced_pod(name=name, namespace=namespace)
            elif kind_lower == "node":
                resource = v1.read_node(name=name)
            elif kind_lower == "persistentvolumeclaim":
                resource = v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
            elif kind_lower == "service":
                resource = v1.read_namespaced_service(name=name, namespace=namespace)
            elif kind_lower == "configmap":
                resource = v1.read_namespaced_config_map(name=name, namespace=namespace)
            elif kind_lower == "secret":
                resource = v1.read_namespaced_secret(name=name, namespace=namespace)
            elif kind_lower == "deployment":
                resource = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            elif kind_lower == "statefulset":
                resource = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
            elif kind_lower == "daemonset":
                resource = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)
            elif kind_lower == "job":
                batch_v1 = self._get_batch_client()
                resource = batch_v1.read_namespaced_job(name=name, namespace=namespace)
            elif kind_lower == "persistentvolume":
                resource = v1.read_persistent_volume(name=name)
            else:
                return f"Unsupported resource kind: {kind}"

            # K8s 对象序列化为字典
            yaml_output = api_client.sanitize_for_serialization(resource)
            import yaml

            # 运维规范：剔除 managedFields（极度影响阅读）
            if isinstance(yaml_output, dict):
                if 'metadata' in yaml_output and 'managedFields' in yaml_output['metadata']:
                    del yaml_output['metadata']['managedFields']
                # 去除 status 如果为空或不需要
                if 'status' in yaml_output and yaml_output['status'] is None:
                    del yaml_output['status']

            return yaml.dump(yaml_output, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            return f"Error fetching resource: {str(e)}"

    async def get_resource_describe(self, kind: str, namespace: str, name: str) -> Dict:
        """
        获取资源的详细描述（Events 为主，符合运维规范）
        返回包含基本信息和相关 Events 的描述信息
        """
        v1 = self._get_core_client()
        apps_v1 = self._get_apps_client()
        batch_v1 = self._get_batch_client()

        result = {
            "kind": kind,
            "name": name,
            "namespace": namespace,
            "apiVersion": "",
            "labels": {},
            "annotations": {},
            "status": {},
            "events": [],
            "details": {}
        }

        try:
            kind_lower = kind.lower()

            # 获取资源基础信息
            resource = None
            if kind_lower == "pod":
                resource = v1.read_namespaced_pod(name=name, namespace=namespace)
                result["apiVersion"] = "v1"
                if resource.spec:
                    result["details"]["node_name"] = getattr(resource.spec, 'node_name', None)
                    result["details"]["service_account"] = getattr(resource.spec, 'service_account_name', None)
            elif kind_lower == "node":
                resource = v1.read_node(name=name)
                result["apiVersion"] = "v1"
            elif kind_lower == "persistentvolumeclaim":
                resource = v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
                result["apiVersion"] = "v1"
            elif kind_lower == "service":
                resource = v1.read_namespaced_service(name=name, namespace=namespace)
                result["apiVersion"] = "v1"
            elif kind_lower == "configmap":
                resource = v1.read_namespaced_config_map(name=name, namespace=namespace)
                result["apiVersion"] = "v1"
            elif kind_lower == "secret":
                resource = v1.read_namespaced_secret(name=name, namespace=namespace)
                result["apiVersion"] = "v1"
            elif kind_lower == "deployment":
                resource = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
                result["apiVersion"] = "apps/v1"
                if resource.spec:
                    result["details"]["replicas"] = {
                        "desired": getattr(resource.spec.replicas, 'nested_field', resource.spec.replicas) if resource.spec.replicas else 0,
                        "updated": getattr(resource.status, 'updated_replicas', None) if resource.status else 0,
                        "ready": getattr(resource.status, 'ready_replicas', None) if resource.status else 0,
                        "available": getattr(resource.status, 'available_replicas', None) if resource.status else 0,
                    }
            elif kind_lower == "statefulset":
                resource = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
                result["apiVersion"] = "apps/v1"
                if resource.spec:
                    result["details"]["replicas"] = {
                        "desired": getattr(resource.spec.replicas, 'nested_field', resource.spec.replicas) if resource.spec.replicas else 0,
                        "updated": getattr(resource.status, 'updated_replicas', None) if resource.status else 0,
                        "ready": getattr(resource.status, 'ready_replicas', None) if resource.status else 0,
                        "available": getattr(resource.status, 'available_replicas', None) if resource.status else 0,
                    }
            elif kind_lower == "daemonset":
                resource = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)
                result["apiVersion"] = "apps/v1"
                if resource.status:
                    result["details"]["desired"] = getattr(resource.status, 'desired_number_scheduled', None)
                    result["details"]["ready"] = getattr(resource.status, 'number_ready', None)
                    result["details"]["updated"] = getattr(resource.status, 'updated_number_scheduled', None)
            elif kind_lower == "job":
                batch_v1 = self._get_batch_client()
                resource = batch_v1.read_namespaced_job(name=name, namespace=namespace)
                result["apiVersion"] = "batch/v1"
                if resource.status:
                    result["details"]["completions"] = getattr(resource.status, 'succeeded', None)
                    result["details"]["active"] = getattr(resource.status, 'active', None)
                    result["details"]["failed"] = getattr(resource.status, 'failed', None)
            elif kind_lower == "persistentvolume":
                resource = v1.read_persistent_volume(name=name)
                result["apiVersion"] = "v1"
            else:
                return {"error": f"不支持的资源类型: {kind}"}

            # 提取资源元数据
            if resource and resource.metadata:
                if getattr(resource.metadata, 'labels', None):
                    result["labels"] = dict(resource.metadata.labels)
                if getattr(resource.metadata, 'annotations', None):
                    result["annotations"] = dict(resource.metadata.annotations)
                if getattr(resource.metadata, 'creation_timestamp', None):
                    result["details"]["created"] = str(resource.metadata.creation_timestamp)

            # 提取 status
            if resource and getattr(resource, 'status', None):
                status_dict = {}
                if hasattr(resource.status, 'to_dict'):
                    status_dict = resource.status.to_dict()
                else:
                    # 简单的属性提取
                    for attr in dir(resource.status):
                        if not attr.startswith('_'):
                            try:
                                val = getattr(resource.status, attr)
                                if not callable(val):
                                    status_dict[attr] = val
                            except:
                                pass
                result["status"] = status_dict

            # 获取 Events - 使用 field_selector 过滤
            try:
                now = datetime.now(timezone.utc)
                # 查询最近7天的 events
                fields = f"involvedObject.kind={kind},involvedObject.name={name},involvedObject.namespace={namespace}"
                events = v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=fields,
                    timeout_seconds=30
                )
                if events.items:
                    for event in events.items:
                        event_info = {
                            "type": getattr(event.type, 'nested_field', event.type) if event.type else "",
                            "reason": getattr(event.reason, 'nested_field', event.reason) if event.reason else "",
                            "message": getattr(event.message, 'nested_field', event.message) if event.message else "",
                            "count": getattr(event.count, 'nested_field', event.count) if event.count else 1,
                            "first_seen": "",
                            "last_seen": "",
                        }
                        if getattr(event, 'first_timestamp', None):
                            event_info["first_seen"] = str(event.first_timestamp)
                        if getattr(event, 'last_timestamp', None):
                            event_info["last_seen"] = str(event.last_timestamp)
                        result["events"].append(event_info)
            except Exception as e:
                logger.warning(f"获取 Events 失败: {e}")

            # 如果没有 Events，添加提示
            if not result["events"]:
                result["events"] = [{
                    "type": "Normal",
                    "reason": "NoEvents",
                    "message": "未找到相关Events，资源可能处于正常状态",
                    "count": 1,
                    "first_seen": "",
                    "last_seen": ""
                }]

        except Exception as e:
            logger.error(f"获取资源描述失败: {e}")
            result["error"] = f"获取资源描述失败: {str(e)}"

        return result

    def _get_pod_fatal_reason(self, pod) -> Tuple[Optional[str], Optional[str]]:
        """从 Pod 状态中提取致命原因和消息"""
        try:
            # 安全检查：确保 status 和 container_statuses 存在
            if not pod or not pod.status:
                return None, None
            if not pod.status.container_statuses:
                return None, None

            for cs in pod.status.container_statuses:
                # 检查等待状态
                if cs.state and cs.state.waiting:
                    reason = (cs.state.waiting.reason or "") if cs.state.waiting else ""
                    message = (cs.state.waiting.message or "") if cs.state.waiting else ""

                    if "ImagePullBackOff" in reason or "ImagePull" in reason:
                        return "镜像拉取失败", message or reason
                    elif "OOMKilled" in reason:
                        return "OOMKilled", message or reason
                    elif "CrashLoopBackOff" in reason:
                        return "CrashLoopBackOff", message or reason
                    elif "ErrImagePull" in reason:
                        return "镜像拉取失败", message or reason
                    elif "CreateContainerError" in reason:
                        return "容器创建失败", message or reason
                    elif "RunContainerError" in reason:
                        return "容器运行失败", message or reason

                # 检查终止状态
                if cs.state and cs.state.terminated:
                    reason = (cs.state.terminated.reason or "") if cs.state.terminated else ""
                    message = (cs.state.terminated.message or "") if cs.state.terminated else ""

                    if "ExitCode" in reason:
                        exit_code = cs.state.terminated.exit_code if cs.state.terminated else "unknown"
                        return f"容器退出 ({exit_code})", message or reason
                    elif "OOMKilled" in reason:
                        return "OOMKilled", message or reason
                    elif "Error" in reason:
                        return "容器错误", message or reason
        except Exception as e:
            logger.warning(f"提取 Pod 致命原因失败: {e}")

        return None, None

    def _calculate_age(self, creation_timestamp) -> str:
        """计算资源创建时间的易读字符串"""
        try:
            if creation_timestamp:
                # 处理不同格式的时间戳
                if isinstance(creation_timestamp, str):
                    if 'T' in creation_timestamp:
                        # 移除时区信息中的 +00:00 格式
                        ts = creation_timestamp.replace('Z', '+00:00')
                        if '.' in ts:
                            # 处理纳秒精度
                            parts = ts.split('.')
                            base = parts[0]
                            frac_and_tz = parts[1]
                            # 只保留毫秒精度
                            frac = frac_and_tz[:3] if len(frac_and_tz) > 3 else frac_and_tz
                            frac = frac.rstrip('0')  # 移除尾随零
                            if frac:
                                ts = f"{base}.{frac}+00:00"
                            else:
                                ts = f"{base}+00:00"
                        creation_time = datetime.fromisoformat(ts)
                    else:
                        creation_time = datetime.strptime(creation_timestamp, "%Y-%m-%d %H:%M:%S")
                else:
                    creation_time = creation_timestamp

                # 确保时区一致，使用 UTC
                if creation_time.tzinfo is None:
                    creation_time = creation_time.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                diff = now - creation_time
                total_seconds = int(diff.total_seconds())

                if total_seconds < 60:
                    return f"{total_seconds}秒"
                elif total_seconds < 3600:
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    return f"{minutes}分{seconds}秒" if seconds > 0 else f"{minutes}分"
                elif total_seconds < 86400:
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    return f"{hours}时{minutes}分" if minutes > 0 else f"{hours}时"
                else:
                    days = total_seconds // 86400
                    hours = (total_seconds % 86400) // 3600
                    return f"{days}天{hours}时" if hours > 0 else f"{days}天"
        except Exception as e:
            logger.warning(f"计算资源运行时间失败: {e}")

        return "-"

    async def get_workload_anomalies(self) -> List[WorkloadAnomaly]:
        """检测工作负载异常"""
        apps_v1 = self._get_apps_client()
        v1 = self._get_core_client()
        result = []

        # 核心组件列表
        core_components = ["coredns", "kube-proxy", "etcd", "kube-apiserver",
                          "kube-scheduler", "kube-controller-manager"]

        # 检查 Deployments
        try:
            deployments = apps_v1.list_deployment_for_all_namespaces()
        except Exception as e:
            logger.error(f"获取 Deployments 失败: {e}")
            deployments = type('obj', (object,), {'items': []})()

        for deploy in deployments.items:
            try:
                desired = deploy.spec.replicas or 0 if deploy.spec else 0
                ready = deploy.status.ready_replicas or 0 if deploy.status else 0

                if ready < desired:
                    # 使用正确的 label selector
                    fatal_reason = None
                    message = f"{desired - ready} replicas are not ready"
                    actual_pod_status = None
                    restarts = 0
                    age = "-"

                    # 获取 Deployment 的正确 label selector
                    pod_label_selector = ""
                    if deploy.spec and deploy.spec.selector:
                        if deploy.spec.selector.match_labels:
                            pod_label_selector = ",".join(f"{k}={v}" for k, v in deploy.spec.selector.match_labels.items())
                        elif deploy.spec.selector.match_expressions:
                            exprs = []
                            for expr in deploy.spec.selector.match_expressions:
                                if expr.operator == "In":
                                    exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                                elif expr.operator == "NotIn":
                                    exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                                elif expr.operator == "Exists":
                                    exprs.append(expr.key)
                            pod_label_selector = ",".join(exprs)

                    # 查找关联的 Pod 状态
                    if pod_label_selector:
                        try:
                            pods = v1.list_namespaced_pod(namespace=deploy.metadata.namespace or "default",
                                                          label_selector=pod_label_selector)
                            if pods.items:
                                # 取第一个异常的 Pod
                                for pod in pods.items:
                                    # 计算 age
                                    pod_age = self._calculate_age(pod.metadata.creation_timestamp)
                                    # 统计重启次数
                                    if pod.status and pod.status.container_statuses:
                                        for cs in pod.status.container_statuses:
                                            restarts += cs.restart_count or 0

                                    # 提取致命原因
                                    reason, msg = self._get_pod_fatal_reason(pod)
                                    if reason:
                                        fatal_reason = reason
                                        message = msg or reason
                                        if pod.status:
                                            actual_pod_status = pod.status.phase or "Unknown"
                                        break
                        except Exception as e:
                            logger.warning(f"查询 Pod 状态失败: {e}")

                    # 检查是否为核心组件
                    deploy_name = deploy.metadata.name.lower() if deploy.metadata else ""
                    is_core = any(comp in deploy_name for comp in core_components)

                    if is_core and fatal_reason:
                        result.append(WorkloadAnomaly(
                            name=deploy.metadata.name,
                            namespace=deploy.metadata.namespace or "default",
                            kind="Deployment",
                            desired_replicas=desired,
                            ready_replicas=ready,
                            status=fatal_reason if fatal_reason in ["CrashLoopBackOff", "OOMKilled"] else "ReplicaMismatch",
                            message=message,
                            fatal_reason=fatal_reason,
                            restarts=restarts,
                            pod_status=actual_pod_status,
                            age=age if age != "-" else self._calculate_age(deploy.metadata.creation_timestamp)
                        ))
                    elif fatal_reason or ready < desired:
                        result.append(WorkloadAnomaly(
                            name=deploy.metadata.name,
                            namespace=deploy.metadata.namespace or "default",
                            kind="Deployment",
                            desired_replicas=desired,
                            ready_replicas=ready,
                            status="ReplicaMismatch",
                            message=message,
                            fatal_reason=fatal_reason,
                            restarts=restarts,
                            pod_status=actual_pod_status,
                            age=self._calculate_age(deploy.metadata.creation_timestamp)
                        ))
            except Exception as e:
                logger.error(f"处理 Deployment 异常: {e}")
                continue

        # 检查 StatefulSets
        try:
            statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        except Exception as e:
            logger.error(f"获取 StatefulSets 失败: {e}")
            statefulsets = type('obj', (object,), {'items': []})()

        for sts in statefulsets.items:
            try:
                desired = sts.spec.replicas or 0 if sts.spec else 0
                ready = sts.status.ready_replicas or 0 if sts.status else 0

                if ready < desired:
                    fatal_reason = None
                    message = f"{desired - ready} replicas are not ready"
                    actual_pod_status = None
                    restarts = 0

                    # 获取 StatefulSet 的正确 label selector
                    pod_label_selector = ""
                    if sts.spec and sts.spec.selector:
                        if sts.spec.selector.match_labels:
                            pod_label_selector = ",".join(f"{k}={v}" for k, v in sts.spec.selector.match_labels.items())
                        elif sts.spec.selector.match_expressions:
                            exprs = []
                            for expr in sts.spec.selector.match_expressions:
                                if expr.operator == "In":
                                    exprs.append(f"{expr.key} in ({','.join(expr.values)})")
                                elif expr.operator == "NotIn":
                                    exprs.append(f"{expr.key} notin ({','.join(expr.values)})")
                                elif expr.operator == "Exists":
                                    exprs.append(expr.key)
                            pod_label_selector = ",".join(exprs)

                    # 查找关联的 Pod 状态
                    if pod_label_selector:
                        try:
                            pods = v1.list_namespaced_pod(namespace=sts.metadata.namespace or "default",
                                                          label_selector=pod_label_selector)
                            if pods.items:
                                for pod in pods.items:
                                    if pod.status and pod.status.container_statuses:
                                        restarts += sum(cs.restart_count or 0 for cs in pod.status.container_statuses)
                                    reason, msg = self._get_pod_fatal_reason(pod)
                                    if reason:
                                        fatal_reason = reason
                                        message = msg or reason
                                        if pod.status:
                                            actual_pod_status = pod.status.phase or "Unknown"
                                        break
                        except Exception as e:
                            logger.warning(f"查询 StatefulSet Pod 状态失败: {e}")

                    result.append(WorkloadAnomaly(
                        name=sts.metadata.name,
                        namespace=sts.metadata.namespace or "default",
                        kind="StatefulSet",
                        desired_replicas=desired,
                        ready_replicas=ready,
                        status="ReplicaMismatch",
                        message=message,
                        fatal_reason=fatal_reason,
                        restarts=restarts,
                        pod_status=actual_pod_status,
                        age=self._calculate_age(sts.metadata.creation_timestamp)
                    ))
            except Exception as e:
                logger.error(f"处理 StatefulSet 异常: {e}")
                continue

        return result

    async def get_network_anomalies(self) -> List[NetworkAnomaly]:
        """检测网络服务异常"""
        v1 = self._get_core_client()
        result = []

        # 获取所有 Service
        services = v1.list_service_for_all_namespaces()
        for svc in services.items:
            svc_type = svc.spec.type or "ClusterIP"
            has_endpoints = False
            message = None

            # 检查 Endpoints
            try:
                eps = v1.read_namespaced_endpoints(
                    name=svc.metadata.name,
                    namespace=svc.metadata.namespace or "default"
                )
                if eps.subsets:
                    for subset in eps.subsets:
                        if subset.addresses and len(subset.addresses) > 0:
                            has_endpoints = True
                            break
            except Exception:
                pass

            # 如果没有存活 Endpoint
            if not has_endpoints and svc_type in ["ClusterIP", "NodePort", "LoadBalancer"]:
                # 跳过 kubernetes 默认服务
                if svc.metadata.name == "kubernetes":
                    continue

                result.append(NetworkAnomaly(
                    name=svc.metadata.name,
                    namespace=svc.metadata.namespace or "default",
                    kind="Service",
                    type=svc_type,
                    status="NoEndpoints",
                    reason="无存活 Endpoint",
                    message="Service 没有可用的后端 Pod"
                ))

        # 检查 Ingress（如果有）
        try:
            networking_v1 = client.NetworkingV1Api()
            ingresses = networking_v1.list_ingress_for_all_namespaces()
            for ing in ingresses.items:
                # 检查 Ingress 状态
                if ing.status.load_balancer.ingress is None or len(ing.status.load_balancer.ingress) == 0:
                    result.append(NetworkAnomaly(
                        name=ing.metadata.name,
                        namespace=ing.metadata.namespace or "default",
                        kind="Ingress",
                        type="Ingress",
                        status="IngressError",
                        reason="Ingress 未分配 IP",
                        message="Ingress Controller 可能未正常运行"
                    ))
        except Exception:
            pass

        return result

    async def get_storage_anomalies(self) -> List[StorageAnomaly]:
        """检测存储卷异常"""
        v1 = self._get_core_client()
        result = []

        # 获取所有 PVC
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        for pvc in pvcs.items:
            status = pvc.status.phase
            message = None
            reason = None

            # 检查 Pending 状态
            if status == "Pending":
                # 尝试获取详细原因
                if pvc.status.conditions:
                    for cond in pvc.status.conditions:
                        if cond.type == "FileSystemResizePending":
                            message = cond.message
                            reason = "等待文件系统扩容"
                        elif cond.type == "Resizing":
                            message = cond.message
                            reason = "正在扩容"

                # 检查是否缺少 StorageClass
                if not pvc.spec.storage_class_name:
                    reason = "NoStorageClass"
                    message = "未指定 StorageClass"
                elif pvc.spec.volume_name:
                    message = "Waiting for PV binding"
                    reason = "等待 PV 绑定"
                else:
                    reason = "ProvisioningFailed"
                    if not message:
                        message = "PVC 处于 Pending 状态，可能缺少可用的 PV 或 StorageClass"

                result.append(StorageAnomaly(
                    name=pvc.metadata.name,
                    namespace=pvc.metadata.namespace or "default",
                    kind="PVC",
                    status=status,
                    capacity=pvc.spec.resources.requests.get("storage", "unknown") if pvc.spec.resources.requests else "unknown",
                    storage_class=pvc.spec.storage_class_name,
                    message=message,
                    reason=reason or "Pending"
                ))

            # 检查 Lost 状态
            elif status == "Lost":
                result.append(StorageAnomaly(
                    name=pvc.metadata.name,
                    namespace=pvc.metadata.namespace or "default",
                    kind="PVC",
                    status=status,
                    capacity=pvc.status.capacity.get("storage", "unknown") if pvc.status.capacity else "unknown",
                    storage_class=pvc.spec.storage_class_name,
                    message="底层 PV 已丢失或被删除",
                    reason="PVLost"
                ))

        return result

    async def get_node_pressures(self) -> List[NodePressure]:
        """检测节点压力"""
        v1 = self._get_core_client()
        result = []

        nodes_list = v1.list_node()
        for node in nodes_list.items:
            status = "Ready"
            pressure_type = None
            message = None
            pod_count = 0

            # 检查节点状态条件
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status != "True":
                    status = "NotReady"
                    message = condition.message
                elif condition.type == "MemoryPressure" and condition.status == "True":
                    pressure_type = "MemoryPressure"
                    status = "MemoryPressure"
                    message = condition.message or "节点存在内存压力"
                elif condition.type == "DiskPressure" and condition.status == "True":
                    pressure_type = "DiskPressure"
                    status = "DiskPressure"
                    message = condition.message or "节点存在磁盘压力"
                elif condition.type == "PIDPressure" and condition.status == "True":
                    pressure_type = "PIDPressure"
                    status = "PIDPressure"
                    message = condition.message or "节点存在 PID 压力"

            # 获取节点资源
            cpu_capacity = "unknown"
            memory_capacity = "unknown"
            pod_capacity = 0

            if node.status.allocatable:
                cpu_capacity = str(node.status.allocatable.get("cpu", "unknown"))
                memory_capacity = str(node.status.allocatable.get("memory", "unknown"))
                pod_capacity = int(node.status.allocatable.get("pods", 110))

            # 计算当前 Pod 数量
            try:
                pods = v1.list_pod_for_all_namespaces(
                    field_selector=f"spec.nodeName={node.metadata.name}"
                )
                pod_count = len(pods.items)
            except Exception:
                pod_count = 0

            # 计算资源使用率（近似）
            cpu_usage_percent = None
            memory_usage_percent = None

            if node.status.allocatable and node.status.capacity:
                # 这里可以根据需要进一步计算实际使用率
                pass

            result.append(NodePressure(
                name=node.metadata.name,
                status=status,
                cpu_capacity=cpu_capacity,
                memory_capacity=memory_capacity,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_percent=memory_usage_percent,
                pod_count=pod_count,
                pod_capacity=pod_capacity,
                message=message,
                pressure_type=pressure_type
            ))

        return result

    async def get_control_plane_statuses(self) -> List[ControlPlaneStatus]:
        """检测控制面组件状态"""
        v1 = self._get_core_client()
        result = []

        # 核心组件关键词
        core_components = {
            "etcd": ["etcd"],
            "kube-apiserver": ["kube-apiserver", "apiserver"],
            "kube-scheduler": ["kube-scheduler", "scheduler"],
            "kube-controller-manager": ["kube-controller-manager", "controller-manager"],
            "coredns": ["coredns", "kube-dns"],
            "kube-proxy": ["kube-proxy"]
        }

        # 获取 kube-system namespace 的 Pod
        try:
            pods = v1.list_namespaced_pod(namespace="kube-system")
        except Exception:
            pods = v1.list_pod_for_all_namespaces()

        for pod in pods.items:
            pod_name = pod.metadata.name
            component_name = None

            # 识别组件
            for comp, keywords in core_components.items():
                for keyword in keywords:
                    if keyword in pod_name.lower():
                        component_name = comp
                        break
                if component_name:
                    break

            if not component_name:
                continue

            # 检查 Pod 状态
            status = "Running"
            message = None
            restarts = 0

            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    restarts += cs.restart_count
                    if cs.state.waiting:
                        status = cs.state.waiting.reason or "Waiting"
                        message = cs.state.waiting.message
                    elif cs.state.terminated:
                        status = cs.state.terminated.reason or "Terminated"
                        message = cs.state.terminated.message

            # 检查是否频繁重启
            if restarts > 5:
                status = "CrashLoopBackOff"
                message = f"组件频繁重启，已重启 {restarts} 次"

            # 判断是否为核心组件
            is_core = component_name in ["etcd", "kube-apiserver", "kube-scheduler", "kube-controller-manager"]

            result.append(ControlPlaneStatus(
                component=component_name,
                status=status,
                namespace=pod.metadata.namespace or "kube-system",
                pod_name=pod_name,
                restarts=restarts,
                message=message,
                is_core=is_core
            ))

        # 去重（同一组件可能有多个 Pod）
        seen = set()
        unique_result = []
        for item in result:
            key = f"{item.component}-{item.pod_name}"
            if key not in seen:
                seen.add(key)
                unique_result.append(item)

        return unique_result

    async def get_certificates(self) -> List[CertificateInfo]:
        """获取集群证书状态，检测即将过期或已过期的证书"""
        v1 = self._get_core_client()
        result = []

        now = datetime.now()
        expiry_threshold = timedelta(days=30)  # 30天阈值

        # 获取所有 Secret，查找 TLS 类型的 Secret
        try:
            secrets = v1.list_secret_for_all_namespaces()

            for secret in secrets.items:
                # 只处理 TLS 证书 Secret
                if secret.type != "kubernetes.io/tls":
                    continue

                secret_name = secret.metadata.name
                namespace = secret.metadata.namespace or "default"

                # 从注解中获取过期时间（k8s 会自动在注解中添加 kubernetes.io/certificate-expiry）
                expire_time = None
                if secret.metadata.annotations:
                    # Kubernetes 1.21+ 会在注解中添加证书过期时间
                    for key, value in secret.metadata.annotations.items():
                        if "certificate-expiry" in key or "expiry" in key.lower():
                            try:
                                # 解析时间格式：2026-03-10 10:00:00+00:00
                                expire_time = datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
                                break
                            except (ValueError, AttributeError):
                                continue

                # 如果没有注解，尝试从 TLS 证书数据中解析
                if not expire_time and secret.data:
                    # tls.crt 包含证书数据
                    if 'tls.crt' in secret.data:
                        try:
                            import base64
                            cert_data = base64.b64decode(secret.data['tls.crt'])
                            try:
                                from cryptography import x509
                                from cryptography.hazmat.backends import default_backend

                                cert = x509.load_der_x509_certificate(cert_data, default_backend())
                                expire_time = cert.not_valid_after.replace(tzinfo=None)
                            except ImportError:
                                # 如果没有安装 cryptography，尝试使用其他方式解析
                                # 这里跳过证书解析，避免阻塞
                                logger.debug("cryptography 库未安装，跳过证书解析")
                                continue
                        except Exception:
                            # 如果解析失败，跳过此证书
                            continue

                # 如果还是没有过期时间，跳过
                if not expire_time:
                    continue

                # 计算剩余天数
                remaining_days = (expire_time - now).days

                # 确定状态
                if remaining_days < 0:
                    status = "Expired"
                    message = f"证书已过期 {abs(remaining_days)} 天"
                elif remaining_days < 30:
                    status = "ExpiringSoon"
                    message = f"证书将在 {remaining_days} 天后过期"
                else:
                    status = "Valid"
                    message = f"证书有效期至 {expire_time.strftime('%Y-%m-%d')}"

                result.append(CertificateInfo(
                    name=secret_name,
                    namespace=namespace,
                    expire_time=expire_time,
                    remaining_days=remaining_days,
                    status=status,
                    message=message,
                    secret_type="kubernetes.io/tls"
                ))

        except Exception as e:
            logger.warning(f"获取证书信息失败: {e}")

        # 按剩余天数排序
        result.sort(key=lambda x: x.remaining_days)

        return result
