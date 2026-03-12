# K8s Dashboard 发布说明

## v2.0 - 多集群管理版

### 新增功能

1. **多集群管理**
   - 支持添加多个 K8s 集群
   - 集群列表展示（名称、版本、节点数、状态）
   - 一键切换当前查看的集群
   - 集群连接测试功能
   - 支持编辑和删除集群

2. **集群选择器**
   - 顶部下拉框快速切换集群
   - 当前活跃集群标记
   - 切换时自动刷新 Dashboard 数据

3. **数据持久化**
   - SQLite 存储集群配置
   - Kubeconfig 文件加密存储
   - 自动备份机制

### 前端优化

1. **图表组件升级**
   - 改用 vue-echarts 组件方式渲染
   - 支持自动响应式调整
   - 修复图表空白问题
   - 添加空数据占位提示

2. **运行模式标识**
   - 移除硬编码 mock 标签
   - 从后端健康检查接口获取真实状态

3. **代码优化**
   - 删除冗余的图表初始化代码
   - 使用 computed 实现响应式图表配置
   - 优化 TypeScript 类型定义

### 后端优化

1. **集群管理器**
   - 单例模式管理集群连接
   - 临时 kubeconfig 文件处理
   - 连接验证机制

2. **API 路由**
   - 完整的集群 CRUD 接口
   - 集群激活切换接口
   - 连接测试接口

3. **数据库**
   - SQLite 集群配置存储
   - 活跃集群标记
   - 状态更新机制

### 部署改进

1. **打包脚本 (build.sh)**
   - 自动化前端构建
   - 完整文件打包
   - 生成标准化安装包

2. **安装脚本 (install.sh)**
   - 支持 Ubuntu/Debian/CentOS/RHEL
   - 自动安装系统依赖
   - 自动配置 systemd 服务
   - 自动配置防火墙
   - 友好的安装提示

3. **部署文档**
   - DEPLOY.md - 详细部署指南
   - 快速部署.md - 快速上手指南
   - 故障排查章节

### 文件结构

```
k8s-dashboard-release.tar.gz
├── main.py
├── routes.py
├── cluster_routes.py
├── k8s_service.py
├── cluster_manager.py
├── database.py
├── schemas.py
├── mock_data.py
├── config.py
├── requirements.txt
├── .env
├── install.sh              # 安装脚本
├── k8s-dashboard.service   # systemd 服务
├── start.sh                # 启动脚本
├── stop.sh                 # 停止脚本
├── healthcheck.sh          # 健康检查
├── static/                 # 前端静态文件
└── kubeconfigs/            # Kubeconfig 存储
```

### 安装包大小

- v2.0: ~500KB

### 兼容性

- Python 3.8+
- Node.js 16+
- Vue 3.5+
- Element Plus 2.13+
- ECharts 6.0+

### 升级步骤

```bash
# 1. 停止服务
sudo systemctl stop k8s-dashboard

# 2. 备份数据
sudo tar -czf /tmp/backup.tar.gz /opt/k8s-dashboard

# 3. 解压新版本
cd /tmp
tar -xzf k8s-dashboard-release.tar.gz -C /opt/k8s-dashboard --strip-components=1

# 4. 重新安装依赖
cd /opt/k8s-dashboard
source venv/bin/activate
pip install -r requirements.txt

# 5. 启动服务
sudo systemctl start k8s-dashboard
```

### 已知问题

- 无

### 后续计划

- [ ] 支持集群导入/导出
- [ ] 添加集群健康度评分
- [ ] 支持更多 K8s 资源类型
- [ ] 添加用户认证系统

---

## v1.0 - 初始版本

### 功能特性

- K8s 集群巡检 Dashboard
- 节点、Pod、PVC、工作负载监控
- 五大分类异常检测
- 资源使用率仪表盘
- Namespace Pod 分布饼图
- Warning 事件展示

### 技术栈

- 后端：FastAPI + Python
- 前端：Vue 3 + TypeScript + Element Plus
- 图表：ECharts
- 部署：systemd + uvicorn
