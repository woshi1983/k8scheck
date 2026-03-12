# K8s 巡检 Dashboard 后端

基于 FastAPI 的 Kubernetes 巡检服务。

## 环境要求

- Python 3.9+

## 安装

```bash
pip install -r requirements.txt
```

## 启动

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs
