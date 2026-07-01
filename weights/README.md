# weights 权重目录

本目录用于存放模型权重文件。

## best.pt（自训练消防安全模型，可选）

- 这是你使用 `backend/train.py` 训练消防安全行为数据集后得到的最优权重。
- 训练完成后，将 `runs/detect/fire_safety/weights/best.pt` 复制到本目录，命名为 `best.pt`。
- 系统启动时会**优先加载** `weights/best.pt`，用于检测火焰、烟雾、抽烟、人员等消防安全类别。

## 没有 best.pt 时

- 系统会**自动回退**到官方预训练模型 `yolov8n.pt`（首次运行由 ultralytics 自动下载）。
- 此时仅用于**跑通整个检测流程**（识别 COCO 通用类别，如人、车等），不具备消防安全专用识别能力。

> 提示：`yolov8n.pt` 无需手动放置，程序会自动下载到本地缓存。
