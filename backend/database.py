"""
SQLite 数据库管理
用于存储集群配置等信息
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict

DB_PATH = Path(__file__).parent / "k8s_dashboard.db"


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                kubeconfig_path TEXT NOT NULL,
                kubeconfig_content TEXT,
                is_active INTEGER DEFAULT 0,
                api_server_url TEXT,
                k8s_version TEXT,
                node_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_connected_at TIMESTAMP,
                status TEXT DEFAULT 'unknown'
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clusters_active ON clusters(is_active)')
        conn.commit()
    finally:
        conn.close()


def create_cluster(name: str, kubeconfig_path: str, kubeconfig_content: Optional[str] = None,
                   description: Optional[str] = None) -> int:
    """创建集群配置"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM clusters')
        is_first = cursor.fetchone()[0] == 0

        cursor.execute('''
            INSERT INTO clusters (name, kubeconfig_path, kubeconfig_content, description, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, kubeconfig_path, kubeconfig_content, description, 1 if is_first else 0))

        cluster_id = cursor.lastrowid
        conn.commit()
        return cluster_id
    finally:
        conn.close()


def get_cluster(cluster_id: int) -> Optional[Dict]:
    """获取集群配置"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clusters WHERE id = ?', (cluster_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_clusters() -> List[Dict]:
    """获取所有集群"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clusters ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_active_cluster() -> Optional[Dict]:
    """获取当前活跃集群"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clusters WHERE is_active = 1 LIMIT 1')
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_active_cluster(cluster_id: int) -> bool:
    """设置活跃集群"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE clusters SET is_active = 0')
        cursor.execute('UPDATE clusters SET is_active = 1 WHERE id = ?', (cluster_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


def update_cluster(cluster_id: int, **kwargs) -> bool:
    """更新集群配置"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'description', 'kubeconfig_path', 'kubeconfig_content',
                       'api_server_url', 'k8s_version', 'node_count', 'status']:
                fields.append(f"{key} = ?")
                values.append(value)

        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(cluster_id)
            sql = f"UPDATE clusters SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()

        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_cluster(cluster_id: int) -> bool:
    """删除集群配置"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clusters WHERE id = ?', (cluster_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


def update_cluster_status(cluster_id: int, status: str, k8s_version: Optional[str] = None,
                          node_count: Optional[int] = None, api_server_url: Optional[str] = None) -> bool:
    """更新集群连接状态"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE clusters
            SET status = ?,
                k8s_version = ?,
                node_count = ?,
                api_server_url = ?,
                last_connected_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, k8s_version, node_count, api_server_url, cluster_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


# 初始化数据库
init_db()
