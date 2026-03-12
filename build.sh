#!/bin/bash
set -e

# ======================================================
# K8s Dashboard 打包脚本
# ======================================================

PACKAGE_NAME="k8s-dashboard-release"
BUILD_DIR="/tmp/k8s-dashboard-build"
PACKAGE_FILE="${PACKAGE_NAME}.tar.gz"

echo "=========================================="
echo "  K8s Dashboard 打包脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 清理旧的构建目录
echo_info "[1/6] 清理旧的构建目录..."
rm -rf $BUILD_DIR
rm -f $PACKAGE_FILE

mkdir -p $BUILD_DIR

# 构建前端
echo_info "[2/6] 构建前端..."
cd frontend

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo_error "未找到 Node.js，请先安装 Node.js"
    exit 1
fi

echo_info "  运行 npm install..."
npm install

echo_info "  运行 npm run build..."
npm run build

echo_info "  构建完成，复制前端文件..."
cp -r dist $BUILD_DIR/static

# 准备后端文件
echo_info "[3/6] 准备后端文件..."
cd ../backend

# 复制后端 Python 文件
for file in *.py; do
    if [ -f "$file" ]; then
        cp "$file" $BUILD_DIR/
    fi
done

# 复制 requirements.txt
if [ -f "requirements.txt" ]; then
    cp requirements.txt $BUILD_DIR/
    echo_info "  已复制 requirements.txt"
else
    echo_error "未找到 requirements.txt"
    exit 1
fi

# 复制 .env 示例文件
if [ -f ".env.example" ]; then
    cp .env.example $BUILD_DIR/.env
    echo_info "  已复制 .env 配置"
else
    # 创建默认 .env
    cat > $BUILD_DIR/.env << EOF
K8S_ENV=prod
EOF
    echo_info "  已创建默认 .env 文件"
fi

# 创建 kubeconfigs 目录
mkdir -p $BUILD_DIR/kubeconfigs
echo_info "  已创建 kubeconfigs 目录"

# 复制 systemd 服务文件
cd ..
if [ -f "k8s-dashboard.service" ]; then
    cp k8s-dashboard.service $BUILD_DIR/
    echo_info "  已复制 systemd 服务文件"
fi

# 复制安装脚本
if [ -f "../install.sh" ]; then
    cp ../install.sh $BUILD_DIR/
    chmod +x $BUILD_DIR/install.sh
    echo_info "  已复制安装脚本"
fi

# 创建启动脚本
echo_info "[4/6] 创建启动脚本..."
cat > $BUILD_DIR/start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x $BUILD_DIR/start.sh

# 创建停止脚本
cat > $BUILD_DIR/stop.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
PID=$!
kill $PID 2>/dev/null || true
EOF
chmod +x $BUILD_DIR/stop.sh

# 创建健康检查脚本
cat > $BUILD_DIR/healthcheck.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
EOF
chmod +x $BUILD_DIR/healthcheck.sh

# 打包
echo_info "[5/6] 打包文件..."
cd $BUILD_DIR
tar -czf /tmp/$PACKAGE_NAME.tar.gz .

# 移动到项目根目录
mv /tmp/$PACKAGE_NAME.tar.gz ../

echo_info "[6/6] 打包完成！"
echo ""
echo "=========================================="
echo -e "  ${GREEN}打包成功！${NC}"
echo "=========================================="
echo ""
echo "  包文件：../${PACKAGE_FILE}"
echo "  大小：$(du -h ../${PACKAGE_FILE} | cut -f1)"
echo ""
echo "  部署步骤："
echo "  1. 将 ${PACKAGE_FILE} 上传到 Linux 服务器 /tmp/ 目录"
echo "  2. 运行：cd /tmp && tar -xzf ${PACKAGE_FILE}"
echo "  3. 运行：cd ${PACKAGE_NAME} && sudo ./install.sh"
echo ""
echo "=========================================="
