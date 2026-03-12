import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import router
from cluster_routes import router as cluster_router
from config import K8S_ENV

app = FastAPI(title="K8s 巡检 Dashboard API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router)
app.include_router(cluster_router)  # 集群管理路由


# 挂载前端静态文件 (生产环境)
# 会覆盖根路径 /，但 /api 路由优先级更高不会被覆盖
def find_static_path():
    """查找静态文件目录"""
    import os

    # 1. 优先检查环境变量 K8S_STATIC_DIR
    static_dir = os.environ.get('K8S_STATIC_DIR')
    if static_dir:
        static_path = Path(static_dir)
        if static_path.exists() and (static_path / "index.html").exists():
            return static_path

    # 2. 检查当前工作目录下的 static
    cwd = Path.cwd()
    static_path = cwd / "static"
    if static_path.exists() and (static_path / "index.html").exists():
        return static_path

    # 3. 检查 backend/static (传统方式，前端源码在项目中)
    base = Path(__file__).parent
    static_path = base / "static"
    if static_path.exists() and (static_path / "index.html").exists():
        return static_path

    # 4. 检查 frontend/dist (前端构建产物在项目中)
    frontend_dist = base.parent / "frontend" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        return frontend_dist

    return None


static_path = find_static_path()
if static_path:
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
    print(f"Static files mounted from: {static_path}")
else:
    print("Warning: No static files directory found")
