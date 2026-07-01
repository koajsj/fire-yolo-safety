# -*- coding: utf-8 -*-
"""
全局配置：路径、数据库、模型、异常类别等。
所有路径均使用 pathlib，兼容 Windows 与 macOS。
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# 基础目录
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent          # backend/
BASE_DIR = BACKEND_DIR.parent                          # 项目根目录

WEIGHTS_DIR = BASE_DIR / "weights"
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"
DATABASE_DIR = BASE_DIR / "database"

# 启动时确保目录存在
for _d in (WEIGHTS_DIR, UPLOAD_DIR, RESULT_DIR, DATABASE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_DIR / "fire_safety.db"

# ---------------------------------------------------------------------------
# 模型配置
# ---------------------------------------------------------------------------
# 优先加载自训练模型 best.pt，不存在则回退到官方 yolov8n.pt
BEST_MODEL_PATH = WEIGHTS_DIR / "best.pt"
FALLBACK_MODEL_NAME = "yolov8n.pt"   # ultralytics 会自动下载到本地

# 默认置信度阈值（可在系统设置中修改，写入数据库）
DEFAULT_CONF_THRESHOLD = 0.25

# ---------------------------------------------------------------------------
# 异常预警类别（消防安全场景）
# 键为模型输出的英文类别名，值为中文显示名
# 火焰、烟雾、抽烟为消防异常预警类别；人员（person）为普通识别类别，见 COCO_CN
# ---------------------------------------------------------------------------
ABNORMAL_CLASSES = {
    "fire": "火焰",
    "smoke": "烟雾",
    "smoking": "抽烟",
}

RISK_ORDER = {"低风险": 1, "中风险": 2, "高风险": 3}
CLASS_RISK_LEVEL = {
    "fire": "高风险",
    "smoke": "高风险",
    "smoking": "中风险",
    "person": "低风险",
}

# COCO 常见类别中文映射（使用官方 yolov8n.pt 跑通流程时用于友好显示）
COCO_CN = {
    "person": "人员",
    "bicycle": "自行车",
    "car": "汽车",
    "motorcycle": "摩托车",
    "bus": "公交车",
    "truck": "卡车",
    "backpack": "背包",
    "umbrella": "雨伞",
    "handbag": "手提包",
    "bottle": "瓶子",
    "cell phone": "手机",
    "laptop": "笔记本电脑",
    "chair": "椅子",
    "knife": "刀具",
}


def class_cn_name(name: str) -> str:
    """返回类别的中文名，找不到则原样返回英文。"""
    if name in ABNORMAL_CLASSES:
        return ABNORMAL_CLASSES[name]
    if name in COCO_CN:
        return COCO_CN[name]
    return name


def is_abnormal(name: str) -> bool:
    """判断类别是否属于异常类别。"""
    return name in ABNORMAL_CLASSES


def class_risk_level(name: str) -> str:
    """返回单个类别对应的消防风险等级。"""
    return CLASS_RISK_LEVEL.get(name, "低风险")


def highest_risk_level(class_names) -> str:
    """根据多个英文类别取最高风险等级。"""
    level = "低风险"
    for name in class_names:
        current = class_risk_level(name)
        if RISK_ORDER[current] > RISK_ORDER[level]:
            level = current
    return level


def risk_message(class_counts: dict) -> str:
    """根据类别计数生成答辩演示用中文风险提示。"""
    if class_counts.get("fire", 0) > 0:
        return "检测到火焰，请立即处理。"
    if class_counts.get("smoke", 0) > 0:
        return "检测到烟雾，请注意消防安全。"
    if class_counts.get("smoking", 0) > 0:
        return "检测到抽烟行为，请及时制止。"
    return "当前未发现明显异常。"


# ---------------------------------------------------------------------------
# 服务配置
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8000

# 允许跨域的前端地址
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

# 允许上传的文件类型
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}
