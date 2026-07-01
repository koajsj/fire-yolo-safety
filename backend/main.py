# -*- coding: utf-8 -*-
"""
FastAPI 主入口。

- 启动时初始化数据库、加载模型
- 配置 CORS、静态文件
- 提供仪表盘、图片/视频/摄像头检测、记录、设置、模型状态等接口
- 所有接口统一 JSON 返回，异常给出中文友好提示，不让服务崩溃
"""
import base64
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import database
from yolo_service import yolo_service

try:
    import cv2
except Exception as e:
    cv2 = None
    CV2_IMPORT_ERROR = e
else:
    CV2_IMPORT_ERROR = None

app = FastAPI(title="消防安全风险分析与预警系统", version="1.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 启动事件：建表 + 加载模型
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    database.init_db()
    yolo_service.load_model()
    print(f"[模型] 加载状态：{yolo_service.loaded} | 来源：{yolo_service.model_source}")
    print(f"[设备] 运行设备：{yolo_service.device}")


# ---------------------------------------------------------------------------
# 统一响应工具
# ---------------------------------------------------------------------------
def ok(data=None, msg="成功"):
    return {"code": 0, "msg": msg, "data": data}


def err(msg="操作失败", code=1):
    return {"code": code, "msg": msg, "data": None}


STAT_FIELDS = (
    "risk_level",
    "num_detections",
    "fire_count",
    "smoke_count",
    "smoking_count",
    "person_count",
    "processing_time_ms",
    "top_label",
    "top_confidence",
    "risk_message",
)


def record_stats(res: dict) -> dict:
    """从检测结果中提取可落库的统计字段。"""
    return {key: res.get(key) for key in STAT_FIELDS}


# ---------------------------------------------------------------------------
# 仪表盘
# ---------------------------------------------------------------------------
@app.get("/api/dashboard")
def dashboard():
    try:
        stats = database.dashboard_stats()
        stats["model_source"] = yolo_service.model_source
        stats["device_label"] = yolo_service.status()["device_label"]
        return ok(stats)
    except Exception as e:
        return err(f"获取统计数据失败：{e}")


# ---------------------------------------------------------------------------
# 图片检测
# ---------------------------------------------------------------------------
@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.IMAGE_EXTS:
        return err("仅支持 jpg、jpeg、png 格式的图片")

    # 保存上传文件
    save_name = f"img_{uuid.uuid4().hex[:12]}{ext}"
    save_path = config.UPLOAD_DIR / save_name
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return err(f"文件保存失败：{e}")

    conf = database.get_conf_threshold()
    res = yolo_service.detect_image(save_path, conf)
    if not res.get("ok"):
        return err(res.get("msg", "检测失败"))

    classes_cn = res["classes_cn"]
    record_id = database.add_record(
        detect_type="image",
        classes=",".join(classes_cn),
        confidence=res["max_confidence"],
        is_abnormal=res["abnormal"],
        file_path=res["result_file"],
        origin_path=f"uploads/{save_name}",
        detail=json.dumps(res["detections"], ensure_ascii=False),
        **record_stats(res),
    )

    return ok(
        {
            "record_id": record_id,
            "origin_file": f"uploads/{save_name}",
            "result_file": res["result_file"],
            "detections": res["detections"],
            "classes_cn": classes_cn,
            "max_confidence": res["max_confidence"],
            "abnormal": res["abnormal"],
            "elapsed": res["elapsed"],
            **record_stats(res),
        },
        "检测完成",
    )


# ---------------------------------------------------------------------------
# 视频检测
# ---------------------------------------------------------------------------
@app.post("/api/detect/video")
async def detect_video(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.VIDEO_EXTS:
        return err("仅支持 mp4、avi、mov、mkv 格式的视频")

    save_name = f"vid_{uuid.uuid4().hex[:12]}{ext}"
    save_path = config.UPLOAD_DIR / save_name
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return err(f"文件保存失败：{e}")

    conf = database.get_conf_threshold()
    res = yolo_service.detect_video(save_path, conf)
    if not res.get("ok"):
        return err(res.get("msg", "检测失败"))

    classes_cn = res["classes_cn"]
    record_id = database.add_record(
        detect_type="video",
        classes=",".join(classes_cn),
        confidence=res["max_confidence"],
        is_abnormal=res["abnormal"],
        file_path=res["result_file"],
        origin_path=f"uploads/{save_name}",
        detail=json.dumps(
            {
                "frames": res["frames"],
                "detected_frames": res["detected_frames"],
                "risk_level": res["risk_level"],
                "num_detections": res["num_detections"],
            },
            ensure_ascii=False,
        ),
        **record_stats(res),
    )

    return ok(
        {
            "record_id": record_id,
            "origin_file": f"uploads/{save_name}",
            "result_file": res["result_file"],
            "classes_cn": classes_cn,
            "max_confidence": res["max_confidence"],
            "abnormal": res["abnormal"],
            "frames": res["frames"],
            "detected_frames": res["detected_frames"],
            "elapsed": res["elapsed"],
            **record_stats(res),
        },
        "检测完成",
    )


# ---------------------------------------------------------------------------
# 摄像头检测（浏览器按帧上传 base64 图像）
# ---------------------------------------------------------------------------
class FrameReq(BaseModel):
    image: str          # data:image/jpeg;base64,xxx 或纯 base64
    save: bool = False  # 是否保存为一条记录


@app.post("/api/detect/frame")
def detect_frame(req: FrameReq):
    if cv2 is None:
        return err(f"OpenCV 未正确安装，无法进行摄像头帧检测：{CV2_IMPORT_ERROR}")
    try:
        raw = req.image.split(",")[-1]  # 去掉 data:image/...;base64, 前缀
        img_bytes = base64.b64decode(raw)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return err("帧解码失败")
    except Exception as e:
        return err(f"图像数据无效：{e}")

    conf = database.get_conf_threshold()
    res = yolo_service.detect_frame(frame, conf)
    if not res.get("ok"):
        return err(res.get("msg", "检测失败"))

    result_b64 = base64.b64encode(res["image_bytes"]).decode()

    # 仅在检测到异常且请求要求保存时落库，避免记录爆炸
    record_id = None
    if req.save and res["abnormal"]:
        save_name = f"cam_{uuid.uuid4().hex[:12]}.jpg"
        save_path = config.RESULT_DIR / save_name
        try:
            with open(save_path, "wb") as f:
                f.write(res["image_bytes"])
            record_id = database.add_record(
                detect_type="camera",
                classes=",".join(res["classes_cn"]),
                confidence=res["max_confidence"],
                is_abnormal=res["abnormal"],
                file_path=f"results/{save_name}",
                origin_path="",
                detail=json.dumps(res["detections"], ensure_ascii=False),
                **record_stats(res),
            )
        except Exception:
            record_id = None

    return ok(
        {
            "image": f"data:image/jpeg;base64,{result_b64}",
            "detections": res["detections"],
            "classes_cn": res["classes_cn"],
            "max_confidence": res["max_confidence"],
            "abnormal": res["abnormal"],
            "record_id": record_id,
            **record_stats(res),
        },
        "检测完成",
    )


# ---------------------------------------------------------------------------
# 检测记录
# ---------------------------------------------------------------------------
@app.get("/api/records")
def records(keyword: str = "", detect_type: str = "", page: int = 1, page_size: int = 10):
    try:
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 10)))
        total, rows = database.list_records(
            keyword=keyword or None,
            detect_type=detect_type or None,
            page=page,
            page_size=page_size,
        )
        return ok({"total": total, "list": rows, "page": page, "page_size": page_size})
    except Exception as e:
        return err(f"查询记录失败：{e}")


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    try:
        if database.delete_record(record_id):
            return ok(msg="删除成功")
        return err("记录不存在")
    except Exception as e:
        return err(f"删除失败：{e}")


# ---------------------------------------------------------------------------
# 系统设置
# ---------------------------------------------------------------------------
class SettingsReq(BaseModel):
    conf_threshold: float


@app.get("/api/settings")
def get_settings():
    return ok({"conf_threshold": database.get_conf_threshold()})


@app.post("/api/settings")
def update_settings(req: SettingsReq):
    if not (0.05 <= req.conf_threshold <= 0.95):
        return err("置信度阈值需在 0.05 ~ 0.95 之间")
    database.set_conf_threshold(round(req.conf_threshold, 2))
    return ok({"conf_threshold": database.get_conf_threshold()}, "设置已保存")


# ---------------------------------------------------------------------------
# 模型状态
# ---------------------------------------------------------------------------
@app.get("/api/model/status")
def model_status():
    return ok(yolo_service.status())


# ---------------------------------------------------------------------------
# 静态文件：结果图、结果视频、原图预览
# 必须放在路由定义之后挂载
# ---------------------------------------------------------------------------
app.mount("/results", StaticFiles(directory=str(config.RESULT_DIR)), name="results")
app.mount("/uploads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="uploads")


@app.get("/")
def root():
    return ok({"service": "消防安全风险分析与预警系统 API", "version": "1.1.0"})


# 全局异常兜底，避免任何未捕获异常导致 500 无中文提示
@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=200,
        content=err(f"服务器内部错误：{exc}"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False)
