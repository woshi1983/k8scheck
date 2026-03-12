#!/usr/bin/env python3
"""
K8s Dashboard 部署脚本 - 跨平台版本
构建前端并打包发布文件
"""

import os
import shutil
import subprocess
import tarfile
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"运行：{' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.run(cmd, shell=isinstance(cmd, str), check=True, cwd=cwd)

def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print("=" * 50)
    print("  K8s 巡检 Dashboard 部署脚本")
    print("=" * 50)

    # 1. 清理
    print("\n[1/6] 清理旧的构建产物...")
    shutil.rmtree(script_dir / "frontend" / "dist", ignore_errors=True)
    shutil.rmtree(script_dir / "backend" / "static", ignore_errors=True)
    shutil.rmtree(script_dir / "release", ignore_errors=True)
    if (script_dir / "k8s-dashboard-release.tar.gz").exists():
        os.remove(script_dir / "k8s-dashboard-release.tar.gz")

    # 2. 构建前端
    print("\n[2/6] 构建前端...")
    frontend_dir = script_dir / "frontend"
    run_command("npm install --registry=https://registry.npmmirror.com", cwd=frontend_dir)
    run_command("npm run build", cwd=frontend_dir)

    # 3. 移动构建产物
    print("\n[3/6] 移动前端构建产物到后端...")
    shutil.copytree(frontend_dir / "dist", script_dir / "backend" / "static")

    # 4. 创建发布目录
    print("\n[4/6] 创建发布目录...")
    release_dir = script_dir / "release"
    release_dir.mkdir(exist_ok=True)

    # 5. 复制后端代码
    print("\n[5/6] 复制后端代码...")
    backend_dir = script_dir / "backend"
    exclude_dirs = {"__pycache__", "static"}
    exclude_files = {".pyc", ".env"}

    for item in backend_dir.iterdir():
        if item.name in exclude_dirs:
            continue
        if item.suffix in exclude_files:
            continue
        if item.is_dir():
            shutil.copytree(item, release_dir / item.name)
        else:
            shutil.copy2(item, release_dir / item.name)

    # 复制静态文件
    shutil.copytree(backend_dir / "static", release_dir / "static")

    # 创建 .env 示例
    env_content = "K8S_ENV=prod\n"
    (release_dir / ".env").write_text(env_content)

    # 6. 打包
    print("\n[6/6] 打包发布文件...")
    os.chdir(release_dir)
    with tarfile.open("../k8s-dashboard-release.tar.gz", "w:gz") as tar:
        for item in release_dir.iterdir():
            tar.add(item.name)

    # 清理
    os.chdir(script_dir)
    shutil.rmtree(release_dir)

    print("\n" + "=" * 50)
    print("  构建完成！")
    print("  发布文件：k8s-dashboard-release.tar.gz")
    print("=" * 50)

if __name__ == "__main__":
    main()
