# 基于 YOLOv8 的消防安全风险分析与预警系统

本项目面向消防安全管理场景，基于 YOLOv8 实现图片、视频、摄像头检测，并提供风险等级分析、异常预警、检测记录、首页仪表盘、系统设置和模型状态展示。项目以本地稳定运行和毕业答辩演示为目标，不依赖云端部署。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Element Plus、Axios、ECharts、Vue Router |
| 后端 | Python、FastAPI、Uvicorn |
| 算法 | YOLOv8、OpenCV、PyTorch、Ultralytics |
| 数据库 | SQLite |
| 运行环境 | Windows / macOS 本地运行，自动适配 CUDA / Apple MPS / CPU |

## 核心功能

- 首页仪表盘：安全指数、检测统计、风险分布、类别分布、每日趋势、检测方式占比。
- 图片检测：上传图片后返回原图、检测结果图、风险等级和统计信息。
- 视频检测：上传短视频后逐帧检测，生成可播放的结果视频。
- 摄像头检测：浏览器摄像头按帧检测，实时显示风险预警。
- 检测记录：记录查询、筛选、详情查看、删除。
- 系统设置：配置置信度阈值，并影响后端检测过滤。
- 模型状态：展示模型来源、运行设备、加载状态、类别信息。

系统无登录流程，启动前后端后直接访问前端地址即可进入首页。

## 目录结构

```text
fire-yolo-safety/
├─ backend/              后端 FastAPI 代码
├─ frontend/             前端 Vue3 代码
├─ weights/              模型权重目录，优先放置 best.pt
├─ database/             SQLite 数据库目录
├─ uploads/              上传原始文件
├─ results/              检测结果图片和视频
├─ docs/                 项目说明文档
├─ demo_files/           答辩演示素材放置目录
├─ scripts/              辅助脚本
├─ README.md             项目总览
├─ start.bat             Windows 一键启动脚本
└─ start.sh              macOS / Linux 一键启动脚本
```

更完整的目录说明见 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)。

## 本地运行

环境要求：

- Python 3.10 或 3.11
- Node.js LTS
- Git
- FFmpeg 可选，用于视频转码
- CUDA 可选；macOS 可使用 CPU 或 MPS

后端：

```bash
cd fire-yolo-safety/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

前端：

```bash
cd fire-yolo-safety/frontend
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

详细步骤和常见问题见 [docs/RUN_GUIDE.md](docs/RUN_GUIDE.md)。

## 模型说明

- 系统优先加载 `weights/best.pt`，作为自训练消防安全模型。
- 如果 `weights/best.pt` 不存在，系统会回退到 `yolov8n.pt`，仅用于跑通检测流程，不代表消防专用识别能力。
- 模型状态页面会显示当前模型来源、运行设备、置信度阈值、加载状态和类别信息。

训练自己的模型可参考 `backend/train.py` 和 `docs/data.yaml.example`。

## 数据库说明

SQLite 数据库默认保存到：

```text
database/fire_safety.db
```

后端启动时会自动建表，并检查 `records` 表缺失字段，兼容旧数据库。检测记录包含检测类型、风险等级、目标数量、类别统计、最高置信度、文件路径和检测时间等信息。

## 答辩演示

建议按以下顺序演示：

1. 首页仪表盘：介绍安全指数、风险统计和模型状态。
2. 图片检测：上传消防风险图片，展示结果图和风险提示。
3. 视频检测：上传短视频，展示检测中状态和结果视频。
4. 摄像头检测：打开摄像头，演示实时预警和风险恢复。
5. 检测记录：查看详情、筛选记录、删除记录。
6. 系统设置：调整置信度阈值，说明阈值含义。
7. 模型状态：说明 `best.pt` 与 `yolov8n.pt` 的区别。

详细演示流程见 [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)。演示素材可放入 [demo_files/](demo_files/)。

