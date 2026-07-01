# 项目结构说明

本项目保持前后端分离结构，核心代码、运行产物和说明文档分目录存放，便于毕业设计提交和答辩展示。

```text
fire-yolo-safety/
├─ backend/
│  ├─ main.py             FastAPI 入口、接口路由、静态资源挂载
│  ├─ config.py           路径、模型、类别、风险等级等全局配置
│  ├─ database.py         SQLite 建表、迁移、记录和统计查询
│  ├─ yolo_service.py     YOLOv8 加载、图片/视频/帧检测封装
│  ├─ detect.py           命令行检测辅助脚本
│  ├─ train.py            自训练模型脚本
│  └─ requirements.txt    后端依赖
├─ frontend/
│  ├─ src/
│  │  ├─ api/             Axios 接口封装
│  │  ├─ layouts/         主布局
│  │  ├─ router/          Vue Router 路由
│  │  ├─ views/           首页、检测、记录、设置、模型状态页面
│  │  ├─ App.vue
│  │  ├─ main.js
│  │  └─ style.css
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ weights/               模型权重目录，优先放置 best.pt
├─ database/              SQLite 数据库目录
├─ uploads/               上传的原始图片和视频
├─ results/               检测生成的结果图片和视频
├─ docs/                  项目结构、运行、演示等文档
├─ demo_files/            答辩演示素材目录
├─ scripts/               视频转码等辅助脚本
├─ README.md
├─ start.bat
└─ start.sh
```

## 不建议移动的文件

- `backend/main.py`：接口路径和静态资源挂载集中在这里。
- `backend/config.py`：定义 `weights/`、`uploads/`、`results/`、`database/` 等关键路径。
- `backend/yolo_service.py`：检测逻辑入口，前端检测功能依赖其返回结构。
- `frontend/src/router/index.js`：页面路由入口。
- `frontend/src/api/index.js`：前端接口路径封装。
- `uploads/`、`results/`、`database/`、`weights/`：运行数据目录，不能随意删除或移动。

## 运行产物说明

- `uploads/` 保存上传原文件。
- `results/` 保存检测结果图片和视频。
- `database/fire_safety.db` 保存检测记录和系统设置。
- `weights/best.pt` 是自训练消防安全模型，体积较大，通常按需单独提交。

