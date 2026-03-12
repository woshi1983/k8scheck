# K8s 巡检 Dashboard - 安装手册

## 功能特性

- 📊 **实时监控**：节点、Pod、PVC、工作负载状态实时展示
- 📈 **资源视图**：集群资源使用率仪表盘 + Namespace Pod 分布饼图
- 🚨 **异常检测**：五大类异常分类（工作负载、网络、存储、节点压力、控制面）
- 🔐 **证书管理**：自动检测 SSL 证书过期风险
- 🐳 **日志终端**：集成终端风格日志查看器
- 🔍 **事件查看**：基于 Events 的资源详细描述，符合运维规范
- 🔄 **自动刷新**：支持配置自动刷新间隔（30秒/1分钟/5分钟）
- ⚙️ **集群管理**：支持多集群配置和快速切换
- 🔍 **Pod 状态检测**：异常工作负载会展示关联 Pod 的实际状态和运行时长
- 📋 **操作优化**：精简的操作列，采用链接样式按钮，支持 YAML/日志/事件快速查看

## 系统要求

- 操作系统：Ubuntu 20.04+ / Debian 11+ / CentOS 7+
- CPU：2 核心以上
- 内存：4GB 以上
- Python：3.9+
- Node.js：18.x+

## 安装步骤

### 1. 上传安装包

将 `k8s-dashboard-release.tar.gz` 上传到服务器的 `/tmp/` 目录：

```bash
scp k8s-dashboard-release.tar.gz root@your-server:/tmp/
```

### 2. SSH 登录服务器

```bash
ssh root@your-server
```

### 3. 运行安装脚本

```bash
cd /tmp
sudo tar -xzf k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard/
cd /opt/k8s-dashboard
sudo ./install.sh
```

安装脚本会自动：
1. 检测/安装 Node.js（如需要）
2. 安装 Python 依赖
3. 构建前端
4. 创建 Python 虚拟环境
5. 配置 systemd 服务
6. 启动服务

### 4. 配置 K8s 访问（生产模式）

确保 root 用户有 `~/.kube/config` 文件：

```bash
# 如果使用 kubeconfig 文件
sudo cp /path/to/your/kubeconfig /root/.kube/config
sudo chown root:root /root/.kube/config
sudo chmod 600 /root/.kube/config

# 测试连接
kubectl get nodes

# 重启服务生效
sudo systemctl restart k8s-dashboard
```

### 5. Mock 模式测试（如需要）

如果无法连接 K8s 集群，可以使用 Mock 模式进行测试：

```bash
# 编辑环境配置
sudo nano /opt/k8s-dashboard/.env

# 修改为
K8S_ENV=mock

# 重启服务
sudo systemctl restart k8s-dashboard
```

## 常用命令

```bash
# 查看服务状态
sudo systemctl status k8s-dashboard

# 启动服务
sudo systemctl start k8s-dashboard

# 停止服务
sudo systemctl stop k8s-dashboard

# 重启服务
sudo systemctl restart k8s-dashboard

# 查看实时日志
sudo journalctl -u k8s-dashboard -f

# 查看最近100条日志
sudo journalctl -u k8s-dashboard -n 100

# 查看事件接口（调试）
curl http://localhost:8000/api/diagnostics/Deployment/default/my-deploy/describe
```

## 访问地址

部署完成后，访问：

```
http://your-server-ip:8000
```

- Dashboard 主页：`/`
- API 文档：`/docs`
- 健康检查：`/health`

## 目录结构

```
/opt/k8s-dashboard/
├── main.py              # FastAPI 应用入口
├── routes.py            # API 路由
├── schemas.py           # Pydantic 数据模型
├── k8s_service.py       # K8s 服务（包含资源描述和事件查询）
├── cluster_manager.py   # 集群管理
├── database.py          # 数据库操作
├── config.py            # 配置
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量
├── venv/                # Python 虚拟环境
├── kubeconfigs/         # K8s 配置存储
├── static/              # 前端静态文件
│   ├── index.html
│   └── assets/
├── backend/             # 后端源码（安装后会移动到根目录）
└── k8s-dashboard.service # systemd 配置
```

## 故障排查

### 服务启动失败

```bash
# 查看详细日志
sudo journalctl -u k8s-dashboard -n 200 --no-pager

# 检查端口占用
sudo lsof -i:8000

# 检查 Python 依赖
cd /opt/k8s-dashboard
source venv/bin/activate
pip list | grep -i kubernetes
```

### 端口已被占用

编辑 `/etc/systemd/system/k8s-dashboard.service` 修改端口：

```ini
Environment="PORT=8000"  # 修改为你需要的端口
```

然后：

```bash
sudo systemctl daemon-reload
sudo firewall-cmd --permanent --add-port=<new-port>/tcp
sudo firewall-cmd --reload
sudo systemctl restart k8s-dashboard
```

### 防火墙配置

```bash
# Ubuntu
sudo ufw allow 8000/tcp

# CentOS
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### Kubernetes RBAC (如需要)

如果集群启用了 RBAC，可能需要为服务账户创建 ClusterRole：

```bash
# 确保 kubeconfig 有足够权限
kubectl cluster-info
kubectl get nodes
```

## 更新部署

```bash
# 1. 上传新的安装包
scp k8s-dashboard-release.tar.gz root@your-server:/tmp/

# 2. SSH 登录服务器
ssh root@your-server

# 3. 解压覆盖
cd /tmp
sudo tar -xzf k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard/

# 4. 重启服务
sudo systemctl restart k8s-dashboard
```

## v3.2 更新日志（2026-03-11）

- **修复事件接口**：重写 `/diagnostics/{kind}/{namespace}/{name}/describe` 接口，以 Events 为主展示资源详情
- **优化操作列 UI**：将操作按钮改为链接样式，減少视觉干扰
- **精简按钮**：使用 `[📄 YAML] | [📝 日志] | [🔍 事件]` 格式，添加垂直分隔符
- **事件显示优化**：前端弹窗直接渲染 Events 数据，符合运维规范
- **后端优化**：ResourceManager 添加 `get_resource_describe` 方法，支持查询资源相关 Events

## 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [Kubernetes API 文档](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/)
