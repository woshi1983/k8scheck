# K8s 巡检 Dashboard 部署指南

## 环境说明

- **开发环境** (`K8S_ENV=mock`): 使用模拟数据，适用于本地开发测试
- **生产环境** (`K8S_ENV=prod`): 连接真实 K8s 集群，获取实际数据

## 一、Ubuntu 服务器部署步骤

### 1. 准备环境

```bash
# 安装 Python 3.10+
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# 安装 Node.js (用于构建前端)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs

# 安装 Git
sudo apt install -y git
```

### 2. 配置 K8s 访问权限

```bash
# 确保当前用户可以访问 K8s 集群
kubectl get nodes

# 如果需要，配置 KUBECONFIG
export KUBECONFIG=/etc/kubernetes/admin.conf
# 或复制到用户目录
mkdir -p ~/.kube
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
```

### 3. 部署应用

```bash
# 上传代码到服务器
# 方式 1: 使用 scp
scp k8s-dashboard-release.tar.gz ubuntu@<server-ip>:/tmp/

# 方式 2: 使用 Git 克隆
git clone <your-repo-url> /opt/k8s-dashboard

# 解压 (如果使用 tar.gz)
cd /opt
sudo mkdir -p k8s-dashboard
sudo tar -xzf /tmp/k8s-dashboard-release.tar.gz -C k8s-dashboard --strip-components=1
```

### 4. 安装依赖

```bash
cd /opt/k8s-dashboard

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装后端依赖
pip install -r backend/requirements.txt

# 安装前端依赖并构建
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run build
cd ..

# 将前端构建产物移动到 backend/static
mv frontend/dist backend/static
```

### 5. 配置文件

```bash
# 编辑 .env 文件
cd /opt/k8s-dashboard/backend
cat > .env << EOF
K8S_ENV=prod
EOF

# 编辑 systemd 服务配置
sudo cp /opt/k8s-dashboard/k8s-dashboard.service /etc/systemd/system/
sudo vi /etc/systemd/system/k8s-dashboard.service
```

确保 `k8s-dashboard.service` 内容如下：

```ini
[Unit]
Description=K8s Inspection Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/k8s-dashboard
Environment="K8S_ENV=prod"
Environment="KUBECONFIG=/home/ubuntu/.kube/config"
ExecStart=/opt/k8s-dashboard/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6. 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start k8s-dashboard

# 设置开机自启
sudo systemctl enable k8s-dashboard

# 查看状态
sudo systemctl status k8s-dashboard

# 查看日志
sudo journalctl -u k8s-dashboard -f
```

### 7. 配置防火墙（如需要）

```bash
# 开放 8000 端口
sudo ufw allow 8000/tcp
sudo ufw status
```

### 8. 访问 Dashboard

浏览器访问：`http://<server-ip>:8000`

## 二、本地开发模式

### 1. 启动后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端（新终端）

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

访问：`http://localhost:5173`

## 三、切换环境模式

### 从 Mock 切换到生产

```bash
# 编辑 .env 文件
vi backend/.env

# 修改为
K8S_ENV=prod

# 重启服务
sudo systemctl restart k8s-dashboard
```

### 从生产切换回 Mock

```bash
# 编辑 .env 文件
vi backend/.env

# 修改为
K8S_ENV=mock

# 重启服务
sudo systemctl restart k8s-dashboard
```

## 四、API 端点说明

| 端点 | 说明 |
|------|------|
| GET `/api/nodes` | 节点列表 |
| GET `/api/pods` | Pod 列表 |
| GET `/api/pvcs` | PVC 列表 |
| GET `/api/workloads` | 工作负载列表 |
| GET `/api/events?hours=1` | 过去 N 小时的 Warning 事件 |
| GET `/api/inspection/summary` | 巡检摘要 |
| GET `/api/metrics/resource-usage` | 资源使用情况 |
| GET `/api/metrics/namespace-distribution` | Namespace 分布 |
| GET `/api/diagnostics/pod/{namespace}/{name}/logs` | Pod 日志 |
| GET `/api/diagnostics/{kind}/{namespace}/{name}/yaml` | 资源 YAML |

## 五、故障排查

### 查看服务日志

```bash
sudo journalctl -u k8s-dashboard -f
```

### 测试 K8s 连接

```bash
source /opt/k8s-dashboard/venv/bin/activate
cd /opt/k8s-dashboard/backend
python -c "from kubernetes import client, config; config.load_kube_config(); v1 = client.CoreV1Api(); print(v1.list_node().items)"
```

### 测试 API 端点

```bash
curl http://localhost:8000/api/nodes
curl http://localhost:8000/api/inspection/summary
```

### 常见问题

1. **Permission denied**: 确保 KUBECONFIG 文件权限正确
   ```bash
   chmod 600 ~/.kube/config
   ```

2. **Module not found**: 重新安装依赖
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **端口被占用**: 修改 uvicorn 启动端口
   ```bash
   ExecStart=/opt/k8s-dashboard/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
   ```

## 六、构建发布包

### Windows (使用 Python 脚本)

```bash
python build_release.py
```

### Linux (使用 Shell 脚本)

```bash
bash deploy.sh
```

生成的 `k8s-dashboard-release.tar.gz` 包含完整的生产环境代码。
