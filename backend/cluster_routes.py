"""
集群管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
import shutil

from database import (
    create_cluster, get_cluster, get_all_clusters, get_active_cluster,
    set_active_cluster, update_cluster, delete_cluster, update_cluster_status
)
from cluster_manager import cluster_manager

router = APIRouter(prefix="/api/clusters")


class ClusterCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    kubeconfig_content: str


class ClusterUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    kubeconfig_content: Optional[str] = None


class ClusterTestRequest(BaseModel):
    kubeconfig_content: str


@router.get("")
async def list_clusters():
    """获取所有集群列表"""
    clusters = get_all_clusters()

    # 隐藏 kubeconfig_content 字段（敏感信息）
    for cluster in clusters:
        if 'kubeconfig_content' in cluster:
            cluster['kubeconfig_content'] = "***" if cluster['kubeconfig_content'] else None

    return {
        "clusters": clusters,
        "total": len(clusters)
    }


@router.get("/active")
async def get_active():
    """获取当前活跃集群"""
    cluster = get_active_cluster()

    if not cluster:
        return {"cluster": None}

    # 隐藏敏感信息
    if 'kubeconfig_content' in cluster:
        cluster['kubeconfig_content'] = "***" if cluster['kubeconfig_content'] else None

    return {"cluster": cluster}


@router.get("/{cluster_id}")
async def get_cluster_detail(cluster_id: int):
    """获取集群详情"""
    cluster = get_cluster(cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    # 隐藏敏感信息
    if 'kubeconfig_content' in cluster:
        cluster['kubeconfig_content'] = "***" if cluster['kubeconfig_content'] else None

    return {"cluster": cluster}


@router.post("")
async def create_cluster_api(request: ClusterCreateRequest):
    """创建新集群"""
    import os
    import tempfile

    # 生成 kubeconfig 文件路径
    kubeconfig_dir = os.path.join(os.path.dirname(__file__), "kubeconfigs")
    os.makedirs(kubeconfig_dir, exist_ok=True)

    # 生成唯一文件名
    import hashlib
    file_hash = hashlib.md5(request.kubeconfig_content.encode()).hexdigest()[:8]
    kubeconfig_path = os.path.join(kubeconfig_dir, f"{request.name}-{file_hash}.yaml")

    # 写入 kubeconfig 文件
    with open(kubeconfig_path, 'w', encoding='utf-8') as f:
        f.write(request.kubeconfig_content)

    # 创建集群记录
    cluster_id = create_cluster(
        name=request.name,
        description=request.description,
        kubeconfig_path=kubeconfig_path,
        kubeconfig_content=request.kubeconfig_content
    )

    # 测试连接并更新状态
    result = cluster_manager.test_connection(kubeconfig_path, request.kubeconfig_content)
    if result['success']:
        update_cluster_status(
            cluster_id,
            status='connected',
            k8s_version=result['k8s_version'],
            node_count=result['node_count'],
            api_server_url=result['api_server_url']
        )

        # 如果是第一个集群，自动设为活跃
        clusters = get_all_clusters()
        if len(clusters) == 1:
            set_active_cluster(cluster_id)
            cluster_manager.set_current_cluster(cluster_id, kubeconfig_path, request.kubeconfig_content)

    return {
        "cluster_id": cluster_id,
        "status": result['status'] if not result['success'] else 'created',
        "connection_test": result
    }


@router.put("/{cluster_id}")
async def update_cluster_api(cluster_id: int, request: ClusterUpdateRequest):
    """更新集群配置"""
    cluster = get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    update_data = {}

    if request.name is not None:
        update_data['name'] = request.name

    if request.description is not None:
        update_data['description'] = request.description

    if request.kubeconfig_content is not None:
        import os
        import tempfile
        import hashlib

        # 删除旧的 kubeconfig 文件
        if cluster.get('kubeconfig_path') and os.path.exists(cluster['kubeconfig_path']):
            try:
                os.unlink(cluster['kubeconfig_path'])
            except:
                pass

        # 创建新的 kubeconfig 文件
        kubeconfig_dir = os.path.join(os.path.dirname(__file__), "kubeconfigs")
        os.makedirs(kubeconfig_dir, exist_ok=True)

        file_hash = hashlib.md5(request.kubeconfig_content.encode()).hexdigest()[:8]
        kubeconfig_path = os.path.join(kubeconfig_dir, f"{request.name or cluster['name']}-{file_hash}.yaml")

        with open(kubeconfig_path, 'w', encoding='utf-8') as f:
            f.write(request.kubeconfig_content)

        update_data['kubeconfig_path'] = kubeconfig_path
        update_data['kubeconfig_content'] = request.kubeconfig_content

        # 测试新连接
        result = cluster_manager.test_connection(kubeconfig_path, request.kubeconfig_content)
        if result['success']:
            update_data['status'] = 'connected'
            update_data['k8s_version'] = result['k8s_version']
            update_data['node_count'] = result['node_count']
            update_data['api_server_url'] = result['api_server_url']

    update_cluster(cluster_id, **update_data)

    # 如果更新的是当前活跃集群，重新加载配置
    active = get_active_cluster()
    if active and active['id'] == cluster_id and request.kubeconfig_content:
        cluster_manager.set_current_cluster(cluster_id, update_data.get('kubeconfig_path', cluster['kubeconfig_path']),
                                             request.kubeconfig_content)

    return {"status": "updated"}


@router.delete("/{cluster_id}")
async def delete_cluster_api(cluster_id: int):
    """删除集群"""
    cluster = get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    # 删除 kubeconfig 文件
    import os
    if cluster.get('kubeconfig_path') and os.path.exists(cluster['kubeconfig_path']):
        try:
            os.unlink(cluster['kubeconfig_path'])
        except:
            pass

    delete_cluster(cluster_id)

    # 如果删除的是活跃集群，设置第一个可用的集群为活跃
    active = get_active_cluster()
    if not active:
        clusters = get_all_clusters()
        if clusters:
            set_active_cluster(clusters[0]['id'])
            cluster_manager.set_current_cluster(
                clusters[0]['id'],
                clusters[0]['kubeconfig_path'],
                clusters[0].get('kubeconfig_content')
            )

    return {"status": "deleted"}


@router.post("/{cluster_id}/activate")
async def activate_cluster(cluster_id: int):
    """切换活跃集群"""
    cluster = get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    # 测试连接
    result = cluster_manager.test_connection(
        cluster['kubeconfig_path'],
        cluster.get('kubeconfig_content')
    )

    if not result['success']:
        raise HTTPException(status_code=400, detail=f"无法连接到集群：{result['message']}")

    # 设置活跃集群
    set_active_cluster(cluster_id)

    # 更新集群管理器
    cluster_manager.set_current_cluster(
        cluster_id,
        cluster['kubeconfig_path'],
        cluster.get('kubeconfig_content')
    )

    return {"status": "activated"}


@router.post("/test")
async def test_cluster_connection(request: ClusterTestRequest):
    """测试集群连接"""
    import tempfile
    import os

    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='kubeconfig_test_')
    try:
        os.write(fd, request.kubeconfig_content.encode('utf-8'))
        os.close(fd)

        result = cluster_manager.test_connection(temp_path)
        return result
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


@router.get("/{cluster_id}/info")
async def get_cluster_info(cluster_id: int):
    """获取集群详细信息"""
    cluster = get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="集群不存在")

    # 测试连接并获取最新信息
    result = cluster_manager.test_connection(
        cluster['kubeconfig_path'],
        cluster.get('kubeconfig_content')
    )

    if result['success']:
        # 更新数据库中的信息
        update_cluster_status(
            cluster_id,
            status='connected',
            k8s_version=result['k8s_version'],
            node_count=result['node_count'],
            api_server_url=result['api_server_url']
        )

    return {
        "cluster": cluster,
        "connection": result
    }
