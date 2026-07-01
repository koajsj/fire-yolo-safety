# 本地运行指南

## 环境要求

- Python 3.10 或 3.11
- Node.js LTS
- Git
- FFmpeg 可选，用于视频转码
- CUDA 可选；无 GPU 时自动使用 CPU，macOS Apple Silicon 可使用 MPS

## 后端启动

Windows PowerShell：

```powershell
cd D:\毕设\fire-yolo-safety\backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

macOS / Linux：

```bash
cd /path/to/fire-yolo-safety/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
```

后端接口文档：

```text
http://127.0.0.1:8000/docs
```

## 前端启动

```bash
cd fire-yolo-safety/frontend
npm install
npm run dev
```

前端访问地址：

```text
http://127.0.0.1:5173
```

## 一键启动

依赖安装完成后，可使用根目录脚本：

```powershell
.\start.bat
```

或：

```bash
bash start.sh
```

## 模型放置

- 自训练模型放到 `weights/best.pt`。
- 没有 `best.pt` 时，系统回退到 `yolov8n.pt`，仅用于流程演示。
- 修改模型文件后建议重启后端。

## 数据库说明

- 数据库文件：`database/fire_safety.db`。
- 后端启动时自动建表。
- 旧数据库缺少新字段时会自动补充，不需要手动删库。

## 常见问题

### 依赖安装失败

可尝试国内镜像：

```bash
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
npm install --registry=https://registry.npmmirror.com
```

### 端口被占用

默认后端端口为 `8000`，前端端口为 `5173`。如果修改后端端口，需要同步修改 `frontend/vite.config.js` 中的代理地址。

### 摄像头打不开

确认浏览器已允许摄像头权限，并关闭占用摄像头的会议软件。建议使用 Chrome 或 Edge。

### 视频无法播放

部分浏览器不支持 OpenCV 写出的 `mp4v` 编码。安装 FFmpeg 后可使用：

```bash
python scripts/transcode_h264.py results/结果视频.mp4
```

生成的 `_h264.mp4` 更适合浏览器播放。

### 中文乱码

源码和文档均使用 UTF-8。Windows 终端如显示乱码，可先执行：

```powershell
chcp 65001
```

