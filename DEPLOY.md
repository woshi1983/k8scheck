# K8s Dashboard 部署指南

## 快速开始

### 1. 打包（本地 Windows）

```bash
# 在项目根目录运行
bash build.sh
```

打包完成后会生成 `k8s-dashboard-release.tar.gz` 文件（约 500KB）。

### 2. 上传到服务器

```bash
# 使用 scp 上传
scp k8s-dashboard-release.tar.gz root@your-server:/tmp/

# 或使用其他工具上传到 /tmp/ 目录
```

### 3. 安装部署（Linux 服务器）

```bash
# 解压安装包
cd /tmp
tar -xzf k8s-dashboard-release.tar.gz
cd k8s-dashboard-release

# 运行安装脚本
sudo ./install.sh
```

安装完成后，访问 `http://your-server-ip:8000` 即可。

---

## 详细部署步骤

### 环境要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Ubuntu 18.04+, Debian 10+, CentOS 7+, RHEL 8+ |
| **Python** | 3.8+ |
| **Node.js** | 16+ (仅打包时需要) |
| **内存** | 至少 512MB |
| **磁盘** | 至少 1GB 可用空间 |
| **端口** | 8000 (可配置) |

### 系统依赖

安装脚本会自动安装以下依赖：

```bash
# Ubuntu/Debian
apt-get install -y python3 python3-venv python3-pip curl wget

# CentOS/RHEL
yum install -y python3 python3-venv python3-pip curl wget
```

### 端口要求

- **默认端口**: 8000
- 确保防火墙已开放此端口

---

## 安装后配置

### 1. 配置 Kubernetes 访问

**方式一：使用现有 kubeconfig（推荐用于单集群）**

```bash
# 将 kubeconfig 复制到用户目录
mkdir -p ~/.kube
cp /path/to/kubeconfig ~/.kube/config
chmod 600 ~/.kube/config
```

**方式二：通过 Web 界面配置（推荐用于多集群）**

1. 访问 `http://your-server-ip:8000`
2. 点击右上角「集群管理」按钮
3. 点击「添加集群」
4. 填写集群名称和 kubeconfig 内容
5. 点击确定

### 2. 修改服务端口

编辑 `/opt/k8s-dashboard/.env` 文件：

```bash
sudo vim /opt/k8s-dashboard/.env
```

修改 PORT 值：

```
PORT=8080
```

重启服务：

```bash
sudo systemctl restart k8s-dashboard
```

### 3. 配置 HTTPS（可选）

使用 Nginx 反向代理：

```bash
# 安装 Nginx
sudo apt-get install -y nginx

# 创建配置文件
sudo vim /etc/nginx/sites-available/k8s-dashboard
```

Nginx 配置示例：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# 重定向 HTTP 到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/k8s-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 运维管理

### 服务管理命令

```bash
# 查看状态
systemctl status k8s-dashboard

# 启动服务
systemctl start k8s-dashboard

# 停止服务
systemctl stop k8s-dashboard

# 重启服务
systemctl restart k8s-dashboard

# 开机自启
systemctl enable k8s-dashboard

# 禁用自启
systemctl disable k8s-dashboard
```

### 日志查看

```bash
# 实时查看日志
journalctl -u k8s-dashboard -f

# 查看最近 100 行
journalctl -u k8s-dashboard -n 100

# 查看今天的日志
journalctl -u k8s-dashboard --since today

# 查看特定时间的日志
journalctl -u k8s-dashboard --since "2024-01-01 00:00:00" --until "2024-01-01 23:59:59"
```

### 备份数据

```bash
# 备份 kubeconfig 文件
tar -czf kubeconfigs-backup.tar.gz /var/lib/k8s-dashboard/kubeconfigs/

# 备份数据库
tar -czf dashboard-db-backup.tar.gz /var/lib/k8s-dashboard/*.db
```

### 升级

```bash
# 1. 停止服务
sudo systemctl stop k8s-dashboard

# 2. 备份数据
sudo tar -czf /tmp/dashboard-backup.tar.gz /opt/k8s-dashboard

# 3. 上传新版本并解压
cd /tmp
tar -xzf k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard --strip-components=1

# 4. 重新安装依赖
cd /opt/k8s-dashboard
source venv/bin/activate
pip install -r requirements.txt

# 5. 启动服务
sudo systemctl start k8s-dashboard
```

---

## 故障排除

### 服务无法启动

```bash
# 检查日志
journalctl -u k8s-dashboard -n 100

# 检查端口占用
sudo netstat -tlnp | grep 8000
sudo lsof -i :8000

# 检查 Python 环境
cd /opt/k8s-dashboard
source venv/bin/activate
python -m pip list
```

### 无法访问 K8s 集群

1. 检查 kubeconfig 文件是否存在：
   ```bash
   ls -la ~/.kube/config
   ```

2. 测试 K8s 连接：
   ```bash
   kubectl --kubeconfig=~/.kube/config get nodes
   ```

3. 通过 Web 界面重新上传 kubeconfig

### 防火墙问题

```bash
# UFW
sudo ufw status
sudo ufw allow 8000/tcp

# firewalld
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -L -n | grep 8000
```

### 内存不足

```bash
# 查看内存使用
free -h
systemctl status k8s-dashboard

# 限制服务内存（编辑 systemd 配置）
sudo vim /etc/systemd/system/k8s-dashboard.service

# 添加以下行：
MemoryLimit=512M

# 重新加载并重启
sudo systemctl daemon-reload
sudo systemctl restart k8s-dashboard
```

### 图表不显示

如果访问页面时图表区域显示空白：

1. 检查浏览器控制台是否有错误
2. 确保已选择或添加集群
3. 刷新页面数据
4. 检查后端服务是否正常运行

---

## 卸载

```bash
# 停止服务
sudo systemctl stop k8s-dashboard
sudo systemctl disable k8s-dashboard

# 删除服务文件
sudo rm /etc/systemd/system/k8s-dashboard.service
sudo systemctl daemon-reload

# 删除安装目录
sudo rm -rf /opt/k8s-dashboard
sudo rm -rf /var/lib/k8s-dashboard
sudo rm -rf /var/log/k8s-dashboard

# 删除用户（可选）
sudo userdel k8s-dashboard 2>/dev/null || true
```

---

## 功能特性

- **多集群管理**: 支持添加、切换、删除多个 K8s 集群
- **集群巡检**: 自动检测节点、Pod、PVC、工作负载异常
- **五大分类**: 工作负载、网络、存储、节点压力、控制面状态
- **资源监控**: CPU/内存使用率仪表盘
- **可视化**: Namespace Pod 分布饼图
- **告警事件**: Warning 事件实时展示
- **YAML 导出**: 支持下载资源 YAML 描述

---

## 技术支持

- 项目文档：`README.md`
- 快速部署：`快速部署.md`
- 问题反馈：提交 Issue
