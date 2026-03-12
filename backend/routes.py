from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from config import K8S_ENV
from database import get_active_cluster, init_db
from cluster_manager import cluster_manager
import traceback
import logging

from schemas import (
    NodesResponse, PodsResponse,
    PVCsResponse, WorkloadsResponse, EventsResponse,
    NamespaceDistResponse, InspectionAnomaliesResponse,
    CertificatesResponse
)
from mock_data import (
    get_mock_nodes, get_mock_pods,
    get_mock_pvcs, get_mock_workloads, get_mock_events,
    get_mock_resource_usage, get_mock_namespace_dist,
    get_mock_pod_logs, get_mock_resource_yaml,
    get_mock_workload_anomalies, get_mock_network_anomalies,
    get_mock_storage_anomalies, get_mock_node_pressures,
    get_mock_control_plane_statuses, get_mock_certificates,
    get_mock_resource_describe
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()


def ensure_cluster_loaded():
    """确保集群已加载（生产模式）"""
    if K8S_ENV == "mock":
        return

    active_cluster = get_active_cluster()
    if not active_cluster:
        raise HTTPException(status_code=400, detail="请先配置集群")

    current_id = cluster_manager.get_current_cluster_id()
    if current_id != active_cluster['id']:
        # 加载集群配置
        success = cluster_manager.set_current_cluster(
            active_cluster['id'],
            active_cluster['kubeconfig_path'],
            active_cluster.get('kubeconfig_content')
        )
        if not success:
            raise HTTPException(status_code=500, detail="无法连接到 K8s 集群")


async def safe_api_call(func, *args, **kwargs):
    """安全地执行 API 调用，捕获异常并返回空列表"""
    try:
        result = await func(*args, **kwargs)
        return result, None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API 调用失败: {e}")
        logger.debug(traceback.format_exc())
        return [], str(e)


@router.get("/nodes", response_model=NodesResponse)
async def list_nodes():
    """获取节点列表"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        nodes = get_mock_nodes()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        nodes = await service.get_nodes()

    healthy = sum(1 for n in nodes if n.status == "Ready")

    return NodesResponse(
        nodes=nodes,
        total=len(nodes),
        healthy=healthy,
        unhealthy=len(nodes) - healthy
    )


@router.get("/pods", response_model=PodsResponse)
async def list_pods():
    """获取 Pod 列表"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        pods = get_mock_pods()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        pods = await service.get_pods()

    healthy = sum(1 for p in pods if p.status == "Running")

    return PodsResponse(
        pods=pods,
        total=len(pods),
        healthy=healthy,
        unhealthy=len(pods) - healthy
    )


@router.get("/pvcs", response_model=PVCsResponse)
async def list_pvcs():
    """获取 PVC 列表"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        pvcs = get_mock_pvcs()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        pvcs = await service.get_pvcs()

    healthy = sum(1 for p in pvcs if p.status == "Bound")

    return PVCsResponse(
        pvcs=pvcs,
        total=len(pvcs),
        healthy=healthy,
        unhealthy=len(pvcs) - healthy
    )


@router.get("/workloads", response_model=WorkloadsResponse)
async def list_workloads():
    """获取工作负载列表"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        workloads = get_mock_workloads()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        workloads = await service.get_workloads()

    healthy = sum(1 for w in workloads if w.ready_replicas == w.desired_replicas)

    return WorkloadsResponse(
        workloads=workloads,
        total=len(workloads),
        healthy=healthy,
        unhealthy=len(workloads) - healthy
    )


@router.get("/events", response_model=EventsResponse)
async def list_events(hours: int = Query(default=1, ge=1, le=24)):
    """获取 Warning 事件列表"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        events = get_mock_events()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        events = await service.get_warning_events(hours)

    return EventsResponse(
        events=events,
        total=len(events)
    )


@router.get("/inspection/summary")
async def inspection_summary():
    """获取巡检摘要"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        nodes = get_mock_nodes()
        pods = get_mock_pods()
        pvcs = get_mock_pvcs()
        workloads = get_mock_workloads()
        events = get_mock_events()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        nodes = await service.get_nodes()
        pods = await service.get_pods()
        pvcs = await service.get_pvcs()
        workloads = await service.get_workloads()
        events = await service.get_warning_events(1)

    return {
        "nodes": {
            "total": len(nodes),
            "unhealthy": len([n for n in nodes if n.status != "Ready"])
        },
        "pods": {
            "total": len(pods),
            "unhealthy": len([p for p in pods if p.status != "Running"])
        },
        "pvcs": {
            "total": len(pvcs),
            "unhealthy": len([p for p in pvcs if p.status != "Bound"])
        },
        "workloads": {
            "total": len(workloads),
            "unhealthy": len([w for w in workloads if w.ready_replicas != w.desired_replicas])
        },
        "events": {
            "total": len(events)
        }
    }


@router.get("/metrics/resource-usage")
async def get_resource_usage():
    """获取集群资源使用情况"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        return get_mock_resource_usage()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        try:
            return await service.get_resource_usage()
        except Exception as e:
            logger.error(f"获取资源使用情况失败: {e}")
            # 返回默认值而不是抛出错误
            return {
                "cpu_capacity": 0,
                "cpu_requests": 0,
                "cpu_usage_percent": 0,
                "memory_capacity": 0,
                "memory_requests": 0,
                "memory_usage_percent": 0
            }


@router.get("/metrics/namespace-distribution", response_model=NamespaceDistResponse)
async def get_namespace_distribution():
    """获取 Namespace Pod 分布"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        dist = get_mock_namespace_dist()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        try:
            dist = await service.get_namespace_distribution()
        except Exception as e:
            logger.error(f"获取 Namespace 分布失败: {e}")
            dist = []

    return {
        "distribution": dist,
        "total_namespaces": len(dist),
        "total_pods": sum(item["pod_count"] if isinstance(item, dict) else item.pod_count for item in dist)
    }


@router.get("/diagnostics-workload/{kind}/{namespace}/{name}/logs")
async def get_workload_logs(kind: str, namespace: str, name: str, lines: int = Query(default=100, ge=1, le=1000)):
    """获取指定工作负载的第一个 Pod 的日志"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        return {"logs": get_mock_pod_logs(name)}
    else:
        ensure_cluster_loaded()
        service = K8sService()
        logs = await service.get_workload_logs(kind, namespace, name, lines)
        return {"logs": logs}


@router.get("/diagnostics/pod/{namespace}/{name}/logs")
async def get_pod_logs(namespace: str, name: str, lines: int = Query(default=100, ge=1, le=1000)):
    """获取指定 Pod 的日志"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        return {"logs": get_mock_pod_logs(name)}
    else:
        ensure_cluster_loaded()
        service = K8sService()
        logs = await service.get_pod_logs(namespace, name, lines)
        return {"logs": logs}


@router.get("/diagnostics/{kind}/{namespace}/{name}/yaml")
async def get_resource_yaml(kind: str, namespace: str, name: str):
    """获取指定资源的 YAML 描述"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        return {"yaml": get_mock_resource_yaml(kind, name)}
    else:
        ensure_cluster_loaded()
        service = K8sService()
        yaml_content = await service.get_resource_yaml(kind, namespace, name)
        return {"yaml": yaml_content}


@router.get("/diagnostics/{kind}/{namespace}/{name}/describe")
async def get_resource_describe(kind: str, namespace: str, name: str):
    """获取指定资源的详细描述（Events 为主）"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        return {"describe": get_mock_resource_describe(kind, name)}
    else:
        ensure_cluster_loaded()
        service = K8sService()
        describe_data = await service.get_resource_describe(kind, namespace, name)
        return describe_data


@router.get("/inspection/anomalies", response_model=InspectionAnomaliesResponse)
async def get_inspection_anomalies():
    """获取巡检异常数据（五大分类）"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        workload_anomalies = get_mock_workload_anomalies()
        network_anomalies = get_mock_network_anomalies()
        storage_anomalies = get_mock_storage_anomalies()
        node_pressures = get_mock_node_pressures()
        control_plane_statuses = get_mock_control_plane_statuses()
    else:
        ensure_cluster_loaded()
        service = K8sService()

        # 每个分类单独处理异常，避免一个失败影响全部
        try:
            workload_anomalies = await service.get_workload_anomalies()
        except Exception as e:
            logger.error(f"获取工作负载异常失败: {e}")
            workload_anomalies = []

        try:
            network_anomalies = await service.get_network_anomalies()
        except Exception as e:
            logger.error(f"获取网络异常失败: {e}")
            network_anomalies = []

        try:
            storage_anomalies = await service.get_storage_anomalies()
        except Exception as e:
            logger.error(f"获取存储异常失败: {e}")
            storage_anomalies = []

        try:
            node_pressures = await service.get_node_pressures()
        except Exception as e:
            logger.error(f"获取节点压力失败: {e}")
            node_pressures = []

        try:
            control_plane_statuses = await service.get_control_plane_statuses()
        except Exception as e:
            logger.error(f"获取控制面状态失败: {e}")
            control_plane_statuses = []

    return InspectionAnomaliesResponse(
        workload_anomalies=workload_anomalies,
        network_anomalies=network_anomalies,
        storage_anomalies=storage_anomalies,
        node_pressures=node_pressures,
        control_plane_statuses=control_plane_statuses
    )


@router.get("/inspection/certificates", response_model=CertificatesResponse)
async def get_certificates():
    """获取证书状态，检测即将过期或已过期的证书"""
    from k8s_service import K8sService

    if K8S_ENV == "mock":
        certificates = get_mock_certificates()
    else:
        ensure_cluster_loaded()
        service = K8sService()
        try:
            certificates = await service.get_certificates()
        except Exception as e:
            logger.error(f"获取证书信息失败: {e}")
            certificates = []

    expired = sum(1 for c in certificates if c.status == "Expired")
    expiring_soon = sum(1 for c in certificates if c.status == "ExpiringSoon")

    return CertificatesResponse(
        certificates=certificates,
        total=len(certificates),
        expired=expired,
        expiring_soon=expiring_soon
    )


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "running", "env": K8S_ENV}
