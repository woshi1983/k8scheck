#!/bin/bash
set -e

# ======================================================
# K8s 巡检 Dashboard 安装脚本
# 版本：v3.3 (修复文件整理冲突)
# ======================================================

INSTALL_DIR="/opt/k8s-dashboard"
SERVICE_NAME="k8s-dashboard"
PORT="8000"
LOG_DIR="/var/log/k8s-dashboard"
DATA_DIR="/var/lib/k8s-dashboard"
PACKAGE_NAME="k8s-dashboard-release"
NODE_VERSION="18"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否以 root 运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo_error "请使用 sudo 运行此脚本"
        echo "用法：sudo ./install.sh"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
        OS_VERSION=$(cat /etc/redhat-release | awk '{print $4}')
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        OS_VERSION=$(uname -r)
    fi

    echo_info "检测到操作系统：$OS $OS_VERSION"
}

# 安装 Node.js（如未安装）
install_nodejs() {
    echo_step "[2/8] 检查/安装 Node.js..."

    if command -v node &> /dev/null; then
        NODE_MAJOR=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_MAJOR" -ge "$NODE_VERSION" ] 2>/dev/null; then
            echo_info "  Node.js $NODE_MAJOR 已安装"
            return 0
        fi
        echo_warn "  当前 Node.js 版本低于 $NODE_VERSION，开始升级..."
    fi

    echo_info "  安装 Node.js $NODE_VERSION.x..."

    case $OS in
        ubuntu|debian)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -y
            apt-get install -y ca-certificates curl gnupg
            mkdir -p /etc/apt/keyrings
            curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
            echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_VERSION.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
            apt-get update -y
            apt-get install -y nodejs
            ;;
        rhel|centos|almalinux|rocky)
            yum install -y curl
            curl -fsSL https://rpm.nodesource.com/setup_$NODE_VERSION.x | bash -
            yum install -y nodejs
            ;;
        *)
            echo_warn "未知操作系统，尝试使用 nvm 安装..."
            export NVM_DIR="$HOME/.nvm"
            [ -s "/usr/local/nvm/nvm.sh" ] && \. "/usr/local/nvm/nvm.sh"
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            nvm install $NODE_VERSION
            nvm use $NODE_VERSION
            ;;
    esac

    if ! command -v node &> /dev/null; then
        echo_error "Node.js 安装失败"
        exit 1
    fi

    echo_info "  Node.js 版本：$(node --version)"
    echo_info "  npm 版本：$(npm --version)"
}

# 安装系统依赖
install_dependencies() {
    echo_step "[3/8] 安装 Python 依赖..."

    case $OS in
        ubuntu|debian)
            apt-get update -y
            apt-get install -y python3 python3-venv python3-pip curl wget
            ;;
        rhel|centos|almalinux|rocky)
            yum install -y python3 python3-venv python3-pip curl wget
            ;;
        *)
            echo_warn "未知操作系统，尝试使用默认命令"
            ;;
    esac

    # 验证 Python
    if ! command -v python3 &> /dev/null; then
        echo_error "Python3 安装失败"
        exit 1
    fi

    echo_info "  Python 版本：$(python3 --version)"
}

# 创建目录结构
create_directories() {
    echo_step "[4/8] 创建安装目录..."

    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    mkdir -p $DATA_DIR
    mkdir -p $DATA_DIR/kubeconfigs

    # 设置权限
    chown -R $(whoami):$(whoami) $INSTALL_DIR
    chmod -R 755 $INSTALL_DIR

    echo_info "  安装目录：$INSTALL_DIR"
    echo_info "  日志目录：$LOG_DIR"
    echo_info "  数据目录：$DATA_DIR"
}

# 解压安装包
extract_package() {
    echo_step "[5/8] 解压安装包..."

    # 假设安装包在 /tmp 目录
    PACKAGE_FILE="/tmp/k8s-dashboard-release.tar.gz"

    if [ ! -f "$PACKAGE_FILE" ]; then
        echo_error "未找到安装包：$PACKAGE_FILE"
        echo "请先将 k8s-dashboard-release.tar.gz 上传到 /tmp/ 目录"
        exit 1
    fi

    # 检查是否需要.strip-components=1 (当包内有 k8s-dashboard-release/ 前缀时)
    if tar -tzf $PACKAGE_FILE | grep -q "^k8s-dashboard-release/"; then
        tar -xzf $PACKAGE_FILE -C $INSTALL_DIR --strip-components=1
    else
        tar -xzf $PACKAGE_FILE -C $INSTALL_DIR
    fi

    echo_info "  解压完成"

    # 如果存在 backend/ 目录，将文件移动到根目录
    if [ -d "$INSTALL_DIR/backend" ]; then
        echo_info "  检测到 backend/ 目录，正在整理文件..."
        cd $INSTALL_DIR
        # 将 backend 目录下的所有文件和子目录移动到根目录
        for item in backend/*; do
            if [ -e "$item" ]; then
                item_name=$(basename "$item")
                # 如果目标已存在，先删除
                if [ -e "./$item_name" ]; then
                    if [ -d "./$item_name" ]; then
                        rm -rf "./$item_name"
                    else
                        rm -f "./$item_name"
                    fi
                fi
                mv "$item" ./
            fi
        done
        # 删除 backend 目录（包括空目录）
        rm -rf backend
        echo_info "  文件整理完成"
    fi
}

# 构建前端（如需要）
build_frontend() {
    echo_step "[6/8] 配置前端静态资源..."

    cd $INSTALL_DIR

    # 检查是否有已构建的前端资源
    if [ -d "frontend/dist" ] && [ -f "frontend/dist/index.html" ]; then
        echo_info "  检测到前端构建产物，开始配置..."

        # 创建 static 目录
        mkdir -p static

        # 复制构建产物到 static 目录
        cp -r frontend/dist/* static/
        echo_info "  前端静态资源配置完成"
    elif [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
        echo_info "  检测到前端源码，开始构建..."

        # 安装前端依赖
        cd frontend
        echo_info "  运行 npm install..."
        npm install --registry=https://registry.npmmirror.com

        # 构建前端
        echo_info "  运行 npm run build..."
        npm run build

        # 复制构建产物到 static 目录
        if [ -d "../static" ]; then
            cp -r dist ../static/
            echo_info "  前端构建完成"
        else
            echo_warn "  未找到 static 目录，跳过前端构建"
        fi
        cd ..
    else
        echo_warn "  未找到前端源码或构建产物，跳过前端配置"
    fi
}

# 创建虚拟环境并安装依赖
setup_python_env() {
    echo_step "[7/8] 配置 Python 环境..."

    cd $INSTALL_DIR

    # 检查 requirements.txt (可能在当前目录或 backend 子目录)
    if [ -f "requirements.txt" ]; then
        REQ_FILE="requirements.txt"
    elif [ -f "backend/requirements.txt" ]; then
        REQ_FILE="backend/requirements.txt"
    else
        echo_error "未找到 requirements.txt 文件"
        exit 1
    fi

    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate

    # 升级 pip
    pip install --upgrade pip

    # 安装依赖
    pip install -r $REQ_FILE

    echo_info "  Python 环境配置完成"
}

# 配置环境变量
configure_env() {
    echo_step "[8/8] 配置环境变量..."

    # 读取 .env 文件
    if [ -f "$INSTALL_DIR/.env" ]; then
        echo_info "  已存在 .env 文件"
        K8S_ENV=$(grep "^K8S_ENV=" $INSTALL_DIR/.env | cut -d'=' -f2)
        echo_info "  当前环境：$K8S_ENV"
    else
        echo_warn "  未找到 .env 文件，请手动配置"
    fi
}

# 配置 systemd 服务
configure_systemd() {
    echo_step "[9/9] 配置 systemd 服务..."

    # 创建 systemd 服务文件
    cat > /tmp/k8s-dashboard.service << EOF
[Unit]
Description=K8s 巡检 Dashboard - 提供 K8s 集群监控和巡检功能
Documentation=https://github.com/k8s-dashboard
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR

# 环境变量
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="K8S_ENV=prod"
Environment="DATA_DIR=$DATA_DIR"
EnvironmentFile=-$INSTALL_DIR/.env

# 执行命令
ExecStart=$INSTALL_DIR/venv/bin/python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 2

ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID

# 重启策略
Restart=always
RestartSec=5

# 资源限制
LimitNOFILE=65535
Nice=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=k8s-dashboard

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

# K8s 配置 (root 用户)
Environment="HOME=/root"
Environment="KUBECONFIG=/root/.kube/config"

[Install]
WantedBy=multi-user.target
EOF

    # 复制服务文件
    cp /tmp/k8s-dashboard.service /etc/systemd/system/k8s-dashboard.service

    # 重新加载 systemd
    systemctl daemon-reload

    echo_info "  Systemd 服务配置完成"
}

# 启动服务
start_service() {
    echo ""
    echo_info "启动服务..."

    systemctl enable $SERVICE_NAME
    systemctl restart $SERVICE_NAME

    # 等待服务启动
    sleep 3

    # 检查服务状态
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo_info "  服务启动成功"
    else
        echo_error "  服务启动失败"
        echo ""
        echo_warn "查看日志：journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
}

# 显示完成信息
show_completion() {
    echo ""
    echo "========================================================"
    echo -e "  ${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "  ${GREEN}║        K8s Dashboard 安装完成！              ║${NC}"
    echo -e "  ${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo "========================================================"
    echo ""

    # 获取服务器 IP
    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || hostname | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | head -1)

    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="your-server-ip"
    fi

    echo -e "  ${BLUE}服务信息：${NC}"
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │ 服务名称：  $SERVICE_NAME"
    echo "  │ 服务状态：  $(systemctl is-active $SERVICE_NAME)"
    echo "  │ 运行端口：  $PORT"
    echo "  │ 访问地址：  http://${SERVER_IP}:${PORT}"
    echo "  └─────────────────────────────────────────────┘"
    echo ""

    echo -e "  ${BLUE}常用命令：${NC}"
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │ 查看状态：  systemctl status $SERVICE_NAME"
    echo "  │ 启动服务：  systemctl start $SERVICE_NAME"
    echo "  │ 停止服务：  systemctl stop $SERVICE_NAME"
    echo "  │ 重启服务：  systemctl restart $SERVICE_NAME"
    echo "  │ 查看日志：  journalctl -u $SERVICE_NAME -f"
    echo "  └─────────────────────────────────────────────┘"
    echo ""

    echo -e "  ${BLUE}目录信息：${NC}"
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │ 安装目录：  $INSTALL_DIR"
    echo "  │ 日志目录：  $LOG_DIR"
    echo "  │ 数据目录：  $DATA_DIR"
    echo "  └─────────────────────────────────────────────┘"
    echo ""

    echo "========================================================"
    echo -e "  ${YELLOW}提示：${NC}"
    echo "  1. 访问 http://${SERVER_IP}:${PORT} 开始使用"
    echo "  2. 点击右上角「集群管理」添加 K8s 集群"
    echo "  3. 在异常表格中点击「查看日志」可查看 Pod 实际状态"
    echo "  4. 如果是 Mock 模式测试，修改 .env 文件中的 K8S_ENV=mock"
    echo "========================================================"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  K8s 巡检 Dashboard 安装脚本"
    echo "  版本：v3.3 (修复文件整理冲突)"
    echo "=========================================="
    echo ""

    # 前置检查
    check_root
    detect_os
    install_nodejs
    install_dependencies
    create_directories
    extract_package
    build_frontend
    setup_python_env
    configure_env
    configure_systemd

    # 启动服务
    start_service

    # 显示完成信息
    show_completion
}

# 显示帮助信息
show_help() {
    echo "K8s 巡检 Dashboard 安装脚本"
    echo ""
    echo "用法：sudo ./install.sh [选项]"
    echo ""
    echo "选项："
    echo "  --help, -h     显示帮助信息"
    echo ""
    echo "示例："
    echo "  sudo ./install.sh           # 安装"
    echo "  sudo ./install.sh --help    # 显示帮助"
    echo ""
}

# 解析参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 运行主函数
main
