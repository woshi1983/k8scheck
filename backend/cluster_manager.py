"""
集群管理器 - 单例模式
管理当前选中的集群配置和 K8s 客户端
"""
import logging
from typing import Optional, Dict, List
from pathlib import Path
import tempfile
import os

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

logger = logging.getLogger(__name__)


class ClusterManager:
    """集群管理器单例类"""

    _instance = None
    _current_cluster_id: Optional[int] = None
    _current_kubeconfig_path: Optional[str] = None
    _core_v1 = None
    _apps_v1 = None
    _batch_v1 = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_current_cluster_id(self) -> Optional[int]:
        """获取当前集群 ID"""
        return self._current_cluster_id

    def set_current_cluster(self, cluster_id: int, kubeconfig_path: str,
                            kubeconfig_content: str = None) -> bool:
        """
        设置当前集群

        Args:
            cluster_id: 集群 ID
            kubeconfig_path: kubeconfig 文件路径
            kubeconfig_content: kubeconfig 文件内容（如果路径不存在，则创建临时文件）

        Returns:
            bool: 是否设置成功
        """
        try:
            # 如果提供了内容，写入临时文件
            if kubeconfig_content and not Path(kubeconfig_path).exists():
                # 创建临时 kubeconfig 文件
                fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='kubeconfig_')
                try:
                    os.write(fd, kubeconfig_content.encode('utf-8'))
                    os.close(fd)
                    kubeconfig_path = temp_path
                except Exception as e:
                    logger.error(f"创建临时 kubeconfig 文件失败：{e}")
                    os.close(fd)
                    return False

            # 验证 kubeconfig 文件
            if not Path(kubeconfig_path).exists():
                logger.error(f"kubeconfig 文件不存在：{kubeconfig_path}")
                return False

            # 加载 kubeconfig 验证连接
            config.load_kube_config(config_file=kubeconfig_path)
            v1 = client.CoreV1Api()
            v1.list_node()  # 测试连接

            # 更新当前集群配置
            self._current_cluster_id = cluster_id
            self._current_kubeconfig_path = kubeconfig_path
            self._core_v1 = None  # 重置客户端
            self._apps_v1 = None
            self._batch_v1 = None

            logger.info(f"已切换到集群 ID: {cluster_id}, kubeconfig: {kubeconfig_path}")
            return True

        except ConfigException as e:
            logger.error(f"Kubeconfig 配置错误：{e}")
            return False
        except Exception as e:
            logger.error(f"连接集群失败：{e}")
            return False

    def get_core_client(self) -> client.CoreV1Api:
        """获取 CoreV1 API 客户端"""
        if self._core_v1 is None:
            if not self._current_kubeconfig_path:
                raise RuntimeError("未设置当前集群，请先调用 set_current_cluster()")

            config.load_kube_config(config_file=self._current_kubeconfig_path)
            self._core_v1 = client.CoreV1Api()

        return self._core_v1

    def get_apps_client(self) -> client.AppsV1Api:
        """获取 AppsV1 API 客户端"""
        if self._apps_v1 is None:
            if not self._current_kubeconfig_path:
                raise RuntimeError("未设置当前集群")

            config.load_kube_config(config_file=self._current_kubeconfig_path)
            self._apps_v1 = client.AppsV1Api()

        return self._apps_v1

    def get_batch_client(self) -> client.BatchV1Api:
        """获取 BatchV1 API 客户端（用于 Job）"""
        if self._batch_v1 is None:
            if not self._current_kubeconfig_path:
                raise RuntimeError("未设置当前集群")

            config.load_kube_config(config_file=self._current_kubeconfig_path)
            self._batch_v1 = client.BatchV1Api()

        return self._batch_v1

    def test_connection(self, kubeconfig_path: str, kubeconfig_content: str = None) -> Dict:
        """
        测试集群连接

        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'k8s_version': str,
                'node_count': int,
                'api_server_url': str
            }
        """
        result = {
            'success': False,
            'message': '',
            'k8s_version': '',
            'node_count': 0,
            'api_server_url': ''
        }

        try:
            # 如果提供了内容，写入临时文件
            if kubeconfig_content and not Path(kubeconfig_path).exists():
                fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='kubeconfig_')
                try:
                    os.write(fd, kubeconfig_content.encode('utf-8'))
                    os.close(fd)
                    kubeconfig_path = temp_path
                except Exception as e:
                    result['message'] = f"创建临时文件失败：{e}"
                    return result
                finally:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

            # 加载 kubeconfig
            config.load_kube_config(config_file=kubeconfig_path)

            # 获取集群信息
            v1 = client.CoreV1Api()

            # 获取节点数量
            nodes = v1.list_node()
            result['node_count'] = len(nodes.items)

            # 获取 API Server URL
            if nodes.items and nodes.items[0].status.addresses:
                for addr in nodes.items[0].status.addresses:
                    if addr.type == 'InternalIP':
                        result['api_server_url'] = addr.address
                        break

            # 获取 K8s 版本
            version_api = client.VersionApi()
            version_info = version_api.get_code()
            result['k8s_version'] = f"v{version_info.major}.{version_info.minor}"

            result['success'] = True
            result['message'] = '连接成功'

        except ConfigException as e:
            result['message'] = f"配置错误：{e}"
        except Exception as e:
            result['message'] = f"连接失败：{str(e)}"

        return result


# 全局单例
cluster_manager = ClusterManager()
