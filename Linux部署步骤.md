# K8s Dashboard Linux 部署步骤

## 前置要求

### 系统要求
- Ubuntu 18.04+ / Debian 10+ / CentOS 7+ / RHEL 8+
- Python 3.8+
- 至少 512MB 内存
- 至少 1GB 磁盘空间

### 网络要求
- 确保服务器可以访问 K8s API Server
- 开放端口 8000（或自定义端口）
- 确保可以访问外网（用于安装依赖）

---

## 部署步骤

### 1. 上传安装包

将 `k8s-dashboard-release.tar.gz` 上传到服务器的 `/tmp/` 目录：

```bash
# 在本地上传到服务器
scp k8s-dashboard-release.tar.gz root@your-server-ip:/tmp/
```

### 2. 解压安装包

```bash
cd /tmp
tar -xzf k8s-dashboard-release.tar.gz
cd k8s-dashboard-release
```

### 3. 执行安装脚本

```bash
sudo ./install.sh
```

安装脚本会自动完成：
1. 安装系统依赖（Python3、pip 等）
2. 创建安装目录 `/opt/k8s-dashboard/`
3. 解压后端代码
4. 创建 Python 虚拟环境并安装依赖
5. 配置 systemd 服务
6. 启动服务

### 4. 配置 K8s 集群

安装完成后，访问 `http://your-server-ip:8000`

首次使用需要配置 K8s 集群：

1. **获取 kubeconfig**
   ```bash
   # 在 K8s master 节点执行
   cat ~/.kube/config
   ```

2. **添加集群**
   - 点击右上角「集群管理」
   - 点击「添加集群」
   - 填写集群名称
   - 粘贴 kubeconfig 内容
   - 点击确定

3. **选择集群**
   - 在顶部选择器中选择已添加的集群
   - 页面自动刷新显示集群数据

---

## 常用命令

### 服务管理

```bash
# 查看服务状态
systemctl status k8s-dashboard

# 启动服务
systemctl start k8s-dashboard

# 停止服务
systemctl stop k8s-dashboard

# 重启服务
systemctl restart k8s-dashboard

# 查看实时日志
journalctl -u k8s-dashboard -f

# 查看今天日志
journalctl -u k8s-dashboard --since today
```

### 目录结构

```bash
# 安装目录
/opt/k8s-dashboard/

# 日志目录
/var/log/k8s-dashboard/

# 数据目录
/var/lib/k8s-dashboard/
```

---

## 故障排查

### 1. 服务无法启动

```bash
# 查看服务状态
systemctl status k8s-dashboard

# 查看错误日志
journalctl -u k8s-dashboard -n 50

# 检查端口占用
netstat -tlnp | grep 8000
```

### 2. K8s 连接失败

```bash
# 检查 kubeconfig 文件
ls -la /var/lib/k8s-dashboard/kubeconfigs/

# 重新添加集群
# 访问 http://your-server-ip:8000 -> 集群管理 -> 重新上传 kubeconfig
```

### 3. 防火墙问题

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 4. 图表不显示

- 确保已添加并选择集群
- 刷新页面数据
- 检查浏览器控制台是否有错误
- 确保 K8s 集群有 Pod、Node 等资源

---

## 环境配置

### 修改端口

编辑 `/opt/k8s-dashboard/.env` 文件：

```bash
sudo nano /opt/k8s-dashboard/.env
```

修改 PORT 参数：

```
PORT=8000  # 修改为你需要的端口
```

重启服务：

```bash
sudo systemctl restart k8s-dashboard
```

### 修改运行模式

默认为生产模式（`K8S_ENV=prod`），如需使用 mock 数据：

```bash
sudo nano /opt/k8s-dashboard/.env
```

修改为：

```
K8S_ENV=mock
```

---

## 卸载服务

如需卸载：

```bash
# 停止服务
sudo systemctl stop k8s-dashboard
sudo systemctl disable k8s-dashboard

# 删除服务文件
sudo rm -f /etc/systemd/system/k8s-dashboard.service
sudo systemctl daemon-reload

# 删除安装目录
sudo rm -rf /opt/k8s-dashboard

# 删除数据目录
sudo rm -rf /var/lib/k8s-dashboard
sudo rm -rf /var/log/k8s-dashboard
```

---

## 功能特性

### 集群管理
- 添加多个 K8s 集群
- 快速切换集群
- 集群连接测试
- 编辑/删除集群

### 资源监控
- 节点状态监控
- Pod 运行状态
- PVC 存储卷
- 工作负载状态

### 异常检测（五大分类）
1. **工作负载异常** - 容器重启、副本不匹配等
2. **网络服务异常** - Service、Ingress 异常
3. **存储卷异常** - PVC 绑定失败等
4. **节点压力** - CPU、内存、Pod 密度过高
5. **控制面状态** - CoreDNS、kube-apiserver 等组件状态

### 终端排障
- 查看 Pod 日志
- 查看资源 YAML
- 查看资源详情（describe）

---

## 注意事项

1. **首次部署**需要上传 kubeconfig 文件才能获取真实的 K8s 数据
2. **生产环境**建议使用 HTTPS 访问
3. **定期备份** `/var/lib/k8s-dashboard/` 中的集群配置
4. **日志位置** `/var/log/k8s-dashboard/`
5. **端口冲突**检查：确保 8000 端口未被其他服务占用

---

## 技术支持

如有问题，请检查：
1. 服务是否正常运行：`systemctl status k8s-dashboard`
2. 日志输出：`journalctl -u k8s-dashboard -f`
3. 浏览器控制台是否有错误
