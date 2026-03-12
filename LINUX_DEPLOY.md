# K8s 巡检 Dashboard - Linux 部署指南

## 目录
- [一、环境要求](#一环境要求)
- [二、打包步骤](#二打包步骤)
- [三、上传到服务器](#三上传到服务器)
- [四、安装部署](#四安装部署)
- [五、配置说明](#五配置说明)
- [六、启动服务](#六启动服务)
- [七、验证测试](#七验证测试)
- [八、常见问题](#八常见问题)

---

## 一、环境要求

### 1.1 本地开发环境（用于打包）
| 软件 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

### 1.2 Ubuntu 服务器环境
| 软件 | 版本要求 | 安装命令 |
|------|----------|----------|
| Ubuntu | 20.04+ | - |
| Python | 3.10+ | `sudo apt install -y python3 python3-venv python3-pip` |
| Git | 最新 | `sudo apt install -y git` |

### 1.3 K8s 集群访问
- 确保服务器可以访问 K8s 集群 API
- 需要配置 `kubeconfig` 文件
- 建议使用 ServiceAccount 或管理员权限

---

## 二、打包步骤

### 2.1 在本地执行打包

```bash
# 进入项目目录
cd D:\claude\test04

# 方式 1: 使用 Python 打包脚本（推荐）
python build_release.py

# 方式 2: 使用 Shell 脚本（Linux/Mac）
bash deploy.sh
```

打包完成后，生成两个文件：
- `k8s-dashboard-release.tar.gz` - 生产环境发布包
- `install.sh` - 快速安装脚本

### 2.2 打包产物结构

```
k8s-dashboard-release.tar.gz 包含：
├── main.py              # FastAPI 入口
├── requirements.txt     # Python 依赖
├── .env                 # 环境配置（自动创建）
├── static/              # 前端构建产物
├── install.sh           # 快速安装脚本
└── ...
```

---

## 三、上传到服务器

### 3.1 使用 scp 上传

```bash
# 在本地执行（上传两个文件）
scp k8s-dashboard-release.tar.gz ubuntu@<server-ip>:/tmp/
scp install.sh ubuntu@<server-ip>:/tmp/
```

### 3.2 使用 rsync 上传

```bash
rsync -avz k8s-dashboard-release.tar.gz install.sh ubuntu@<server-ip>:/tmp/
```

### 3.3 直接下载（如果有公网地址）

```bash
# 在服务器上执行
wget http://<your-server>/k8s-dashboard-release.tar.gz -O /tmp/k8s-dashboard-release.tar.gz
```

---

## 四、安装部署

### 4.1 登录服务器并执行安装脚本

```bash
# SSH 登录服务器
ssh ubuntu@<server-ip>

# 进入临时目录
cd /tmp

# 执行安装脚本
chmod +x install.sh
sudo ./install.sh
```

安装脚本会自动完成以下操作：
1. 创建安装目录 `/opt/k8s-dashboard`
2. 解压发布包
3. 创建 Python 虚拟环境并安装依赖
4. 配置 K8s 访问（如果存在 `/etc/kubernetes/admin.conf`）
5. 配置 systemd 服务
6. 配置防火墙（UFW 或 firewalld）
7. 启动服务

### 4.2 手动安装（可选）

如果自动安装脚本失败，请参考以下步骤手动安装：

```bash
# 1. 创建目录并解压
sudo mkdir -p /opt/k8s-dashboard
sudo tar -xzf /tmp/k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard

# 2. 安装 Python 依赖
cd /opt/k8s-dashboard
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置 K8s 访问
mkdir -p ~/.kube
if [ -f /etc/kubernetes/admin.conf ]; then
    sudo cp /etc/kubernetes/admin.conf ~/.kube/config
    sudo chown $(id -u):$(id -g) ~/.kube/config
    chmod 600 ~/.kube/config
fi

# 4. 配置 .env 文件
echo "K8S_ENV=prod" > .env

# 5. 配置 systemd 服务（见第五章）
```

---

## 五、配置说明

### 5.1 环境配置（backend/.env）

```bash
# 编辑配置文件
vi /opt/k8s-dashboard/backend/.env
```

| 配置项 | 说明 | 可选值 |
|--------|------|--------|
| `K8S_ENV` | 运行模式 | `mock` = 模拟数据，`prod` = 真实 K8s 集群 |

### 5.2 端口配置

默认端口：**8000**

如需修改，编辑 systemd 服务：
```ini
ExecStart=/opt/k8s-dashboard/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080
```

### 5.3 防火墙配置

```bash
# Ubuntu UFW
sudo ufw allow 8000/tcp
sudo ufw status

# CentOS Firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## 六、启动服务

### 6.1 启动 systemd 服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start k8s-dashboard

# 设置开机自启
sudo systemctl enable k8s-dashboard

# 查看服务状态
sudo systemctl status k8s-dashboard
```

### 6.2 查看日志

```bash
# 实时查看日志
sudo journalctl -u k8s-dashboard -f

# 查看最近 100 行日志
sudo journalctl -u k8s-dashboard -n 100

# 查看今天的日志
sudo journalctl -u k8s-dashboard --since today
```

### 6.3 服务管理命令

```bash
# 重启服务
sudo systemctl restart k8s-dashboard

# 停止服务
sudo systemctl stop k8s-dashboard

# 禁用开机自启
sudo systemctl disable k8s-dashboard
```

---

## 七、验证测试

### 7.1 测试 API 接口

```bash
# 测试首页
curl http://localhost:8000/

# 测试节点列表
curl http://localhost:8000/api/nodes

# 测试异常数据接口
curl http://localhost:8000/api/inspection/anomalies | python3 -m json.tool

# 测试资源使用率
curl http://localhost:8000/api/metrics/resource-usage
```

### 7.2 访问 Web 界面

浏览器访问：
```
http://<server-ip>:8000
```

### 7.3 预期输出示例

```json
{
  "workload_anomalies": [
    {
      "name": "api-server",
      "namespace": "kube-system",
      "kind": "Deployment",
      "status": "CrashLoopBackOff",
      "fatal_reason": "OOMKilled",
      "restarts": 15
    }
  ],
  "network_anomalies": [
    {
      "name": "backend-api",
      "namespace": "default",
      "kind": "Service",
      "status": "NoEndpoints",
      "reason": "无存活 Endpoint"
    }
  ],
  "storage_anomalies": [...],
  "node_pressures": [...],
  "control_plane_statuses": [...]
}
```

---

## 八、常见问题

### 8.1 服务启动失败

**问题：** `systemctl start k8s-dashboard` 失败

**排查步骤：**
```bash
# 查看详细错误
sudo journalctl -u k8s-dashboard -n 50 --no-pager

# 手动运行测试
cd /opt/k8s-dashboard
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 8.2 无法连接 K8s 集群

**问题：** `ConfigException: Invalid kube-config file`

**解决方案：**
```bash
# 检查 kubeconfig 文件
ls -la ~/.kube/config

# 测试 kubectl
kubectl get nodes

# 如果是 ServiceAccount，确保配置了正确的 token 和 CA
```

**ServiceAccount 配置示例：**
```yaml
# 创建 ServiceAccount
kubectl create sa k8s-dashboard -n kube-system

# 创建 ClusterRoleBinding
kubectl create clusterrolebinding k8s-dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=kube-system:k8s-dashboard

# 获取 Token
kubectl create token k8s-dashboard -n kube-system
```

### 8.3 端口被占用

**问题：** `Address already in use`

**解决方案：**
```bash
# 查找占用端口的进程
sudo netstat -tlnp | grep 8000
sudo lsof -i :8000

# 杀死占用进程
sudo kill -9 <PID>

# 或者修改配置使用其他端口
```

### 8.4 前端页面 404

**问题：** 访问页面显示 404

**检查事项：**
```bash
# 确认 static 目录存在
ls -la /opt/k8s-dashboard/backend/static/

# 应该有 index.html 文件
ls /opt/k8s-dashboard/backend/static/index.html
```

**重新构建前端：**
```bash
cd /opt/k8s-dashboard
# 如果源码中有 frontend 目录
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run build
cd ..
mv frontend/dist backend/static
sudo systemctl restart k8s-dashboard
```

### 8.5 内存不足

**问题：** 服务频繁重启，日志显示 OOM

**解决方案：**
```bash
# 在 systemd 服务中限制内存
sudo vi /etc/systemd/system/k8s-dashboard.service

# 添加以下行
[Service]
MemoryLimit=512M
MemoryHigh=400M
```

---

## 附录 A：快速部署脚本

将以下内容保存为 `install.sh`，在服务器上执行：

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "  K8s Dashboard 快速安装脚本"
echo "=========================================="

# 配置变量
INSTALL_DIR="/opt/k8s-dashboard"
SERVICE_NAME="k8s-dashboard"
PORT="8000"

# 1. 解压
echo "[1/6] 解压文件..."
sudo mkdir -p $INSTALL_DIR
sudo tar -xzf /tmp/k8s-dashboard-release.tar.gz -C $INSTALL_DIR --strip-components=1

# 2. 安装 Python 依赖
echo "[2/6] 安装 Python 依赖..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. 配置 K8s
echo "[3/6] 配置 K8s 访问..."
mkdir -p ~/.kube
if [ -f /etc/kubernetes/admin.conf ]; then
    sudo cp /etc/kubernetes/admin.conf ~/.kube/config
    sudo chown $(id -u):$(id -g) ~/.kube/config
    chmod 600 ~/.kube/config
fi

# 4. 配置 systemd
echo "[4/6] 配置 systemd 服务..."
sudo cp $INSTALL_DIR/k8s-dashboard.service /etc/systemd/system/

# 5. 配置防火墙
echo "[5/6] 配置防火墙..."
if command -v ufw &> /dev/null; then
    sudo ufw allow $PORT/tcp
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=$PORT/tcp
    sudo firewall-cmd --reload
fi

# 6. 启动服务
echo "[6/6] 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo ""
echo "=========================================="
echo "  安装完成！"
echo "  访问地址：http://$(hostname -I | awk '{print $1}'):${PORT}"
echo "=========================================="
```

执行：
```bash
chmod +x install.sh
sudo ./install.sh
```

---

## 附录 B：升级步骤

```bash
# 1. 备份当前配置
sudo cp /opt/k8s-dashboard/backend/.env /tmp/.env.backup

# 2. 停止服务
sudo systemctl stop k8s-dashboard

# 3. 解压新版本
sudo rm -rf /opt/k8s-dashboard/*
sudo tar -xzf /tmp/k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard --strip-components=1

# 4. 恢复配置
sudo cp /tmp/.env.backup /opt/k8s-dashboard/backend/.env

# 5. 安装依赖
cd /opt/k8s-dashboard
source venv/bin/activate
pip install -r backend/requirements.txt

# 6. 启动服务
sudo systemctl start k8s-dashboard
sudo systemctl status k8s-dashboard
```

---

## 附录 C：API 端点列表

| 端点 | 说明 |
|------|------|
| `GET /api/nodes` | 节点列表 |
| `GET /api/pods` | Pod 列表 |
| `GET /api/pvcs` | PVC 列表 |
| `GET /api/workloads` | 工作负载列表 |
| `GET /api/events?hours=1` | Warning 事件（过去 N 小时） |
| `GET /api/inspection/anomalies` | **五大分类异常数据** |
| `GET /api/metrics/resource-usage` | 资源使用率 |
| `GET /api/metrics/namespace-distribution` | Namespace 分布 |
| `GET /api/diagnostics/pod/{ns}/{name}/logs` | Pod 日志 |
| `GET /api/diagnostics/{kind}/{ns}/{name}/yaml` | 资源 YAML |

---

**文档版本：** v2.0
**最后更新：** 2026-03-11
