# K8s 巡检 Dashboard

一个基于 Vue 3 + FastAPI 的 Kubernetes 集群监控和巡检平台。

## 功能特性

- 📊 **实时监控**：节点、Pod、PVC、工作负载状态实时展示
- 📈 **资源视图**：集群资源使用率仪表盘 + Namespace Pod 分布饼图
- 🚨 **异常检测**：五大类异常分类（工作负载、网络、存储、节点压力、控制面）
- 🔐 **证书管理**：自动检测 SSL 证书过期风险
- 🐳 **日志终端**：集成终端风格日志查看器，支持查看 Pod 日志和资源描述
- 📋 **事件查看**：告警事件抽屉，查看 Warning 级别事件详情
- 🔄 **自动刷新**：支持配置自动刷新间隔（30秒/1分钟/5分钟）
- ⚙️ **集群管理**：支持多集群配置和快速切换
- 🔍 **Pod 状态检测**：异常工作负载会查询关联的 Pod 并显示实际状态和运行时长

## 技术栈

### 前端
- Vue 3 + Composition API
- Element Plus UI
- ECharts + vue-echarts 图表
- Axios HTTP 客户端

### 后端
- FastAPI (Python 3.9+)
- Kubernetes Python Client
- Pydantic 数据验证
- SQLite 持久化

## 快速开始

### Linux 部署（推荐）

```bash
# 1. 上传安装包
scp k8s-dashboard-release.tar.gz root@your-server:/tmp/

# 2. SSH 登录服务器
ssh root@your-server

# 3. 运行安装脚本
cd /tmp
sudo tar -xzf k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard/
cd /opt/k8s-dashboard
sudo ./install.sh
```

详细步骤请参考 [INSTALL.md](./INSTALL.md)

### 本地开发

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:8000 查看 Dashboard

## 访问地址

部署完成后，访问：

```
http://your-server-ip:8000
```

- Dashboard 主页：`/`
- API 文档：`/docs`
- 健康检查：`/health`

## 常用命令

```bash
# 查看服务状态
sudo systemctl status k8s-dashboard

# 查看实时日志
sudo journalctl -u k8s-dashboard -f

# 重启服务
sudo systemctl restart k8s-dashboard
```

## 更新说明

### v3.0 (最新)
- ✅ 修复工作负载异常检测中的 label selector 查询逻辑
- ✅ 新增 Pod 状态显示（显示关联 Pod 的实际运行状态）
- ✅ 新增运行时长显示（资源创建以来的时间）
- ✅ 优化日志获取逻辑，支持通过工作负载类型查询 Pod 日志
- ✅ 重新编写安装脚本，支持自动安装 Node.js
- ✅ 更新部署文档

### v2.1
- ✅ 改进查看 YAML 功能（使用终端弹窗显示）
- ✅ 支持通过 Deployment 名称查询关联 Pod 的日志

### v2.0
- ✅ 新增控制面核心组件状态展示（etcd, kube-apiserver, kube-controller-manager, kube-scheduler）
- ✅ 新增证书过期风险检测
- ✅ 新增自动刷新功能
- ✅ 优化告警事件查看体验

## 许可证

MIT License
