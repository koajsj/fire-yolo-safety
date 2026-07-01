# -*- coding: utf-8 -*-
"""
YOLOv8 检测服务封装。

职责：
- 加载模型（优先 best.pt，回退 yolov8n.pt）
- 自动识别运行设备（CUDA / Apple MPS / CPU）
- 提供图片、视频、单帧（摄像头）检测方法
- 所有异常都捕获并返回友好提示，保证服务不崩溃
"""
import time
import uuid
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np

import config

try:
    import cv2
except Exception as e:
    cv2 = None
    CV2_IMPORT_ERROR = e
else:
    CV2_IMPORT_ERROR = None


def _select_device() -> str:
    """自动选择运行设备：CUDA > Apple MPS > CPU。"""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        # Apple Silicon MPS
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


class YoloService:
    """全局单例式检测服务。"""

    def __init__(self):
        self.model = None
        self.model_path = ""        # 实际加载的模型文件
        self.model_source = ""      # 'best.pt（自训练）' 或 'yolov8n.pt（官方预训练）'
        self.device = _select_device()
        self.loaded = False
        self.load_error = ""
        self.names = {}             # 类别 id -> 英文名

    # ------------------------------------------------------------------
    # 模型加载
    # ------------------------------------------------------------------
    def load_model(self) -> None:
        """加载模型，优先 best.pt，失败回退 yolov8n.pt。"""
        try:
            from ultralytics import YOLO
        except Exception as e:  # ultralytics 未安装
            self.loaded = False
            self.load_error = f"ultralytics 未正确安装：{e}"
            return

        # 1) 优先尝试自训练模型
        if config.BEST_MODEL_PATH.exists():
            try:
                self.model = YOLO(str(config.BEST_MODEL_PATH))
                self.model_path = str(config.BEST_MODEL_PATH)
                self.model_source = "best.pt（自训练消防安全模型）"
                self._after_load()
                return
            except Exception as e:
                self.load_error = f"best.pt 加载失败，已回退官方模型：{e}"

        # 2) 回退官方预训练模型（首次会自动下载）
        try:
            self.model = YOLO(config.FALLBACK_MODEL_NAME)
            self.model_path = config.FALLBACK_MODEL_NAME
            self.model_source = "yolov8n.pt（官方预训练，仅用于跑通检测流程）"
            self._after_load()
        except Exception as e:
            self.loaded = False
            self.load_error = f"模型加载失败：{e}"

    def _after_load(self) -> None:
        """加载成功后的公共处理。"""
        try:
            self.names = dict(self.model.names)
        except Exception:
            self.names = {}
        self.loaded = True
        self.load_error = ""

    def status(self) -> Dict:
        """返回模型状态，供前端「模型状态」页展示。"""
        import database

        is_best = Path(self.model_path).name == "best.pt"
        model_kind = "best.pt" if is_best else ("yolov8n.pt" if self.model_path else "未加载")
        return {
            "loaded": self.loaded,
            "model_path": self.model_path,
            "model_source": self.model_source,
            "model_kind": model_kind,
            "device": self.device,
            "device_label": {
                "cuda": "NVIDIA GPU (CUDA)",
                "mps": "Apple GPU (MPS)",
                "cpu": "CPU",
            }.get(self.device, self.device),
            "conf_threshold": database.get_conf_threshold(),
            "class_names": list(self.names.values()) if self.names else [],
            "fire_classes": [
                {"class_en": "fire", "class_cn": "火焰", "risk_level": "高风险"},
                {"class_en": "smoke", "class_cn": "烟雾", "risk_level": "高风险"},
                {"class_en": "smoking", "class_cn": "抽烟", "risk_level": "中风险"},
                {"class_en": "person", "class_cn": "人员", "risk_level": "低风险"},
            ],
            "model_notice": (
                "当前使用自训练消防安全模型。"
                if is_best else
                "当前为默认模型，仅用于流程演示，不代表消防专用识别能力。"
                if self.model_path else
                "模型未加载，请检查依赖安装、网络或权重文件。"
            ),
            "error": self.load_error,
        }

    # ------------------------------------------------------------------
    # 检测结果解析
    # ------------------------------------------------------------------
    def _parse_result(self, result) -> Tuple[List[Dict], float, bool, set]:
        """
        解析单张图的检测结果。
        返回：detections 列表、最高置信度、是否异常、出现的中文类别集合
        """
        detections = []
        max_conf = 0.0
        abnormal = False
        cn_classes = set()

        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return detections, max_conf, abnormal, cn_classes

        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            en_name = self.names.get(cls_id, str(cls_id))
            cn_name = config.class_cn_name(en_name)
            xyxy = [float(x) for x in box.xyxy[0].tolist()]

            detections.append(
                {
                    "class_en": en_name,
                    "class_cn": cn_name,
                    "confidence": round(conf, 4),
                    "bbox": [round(v, 1) for v in xyxy],
                    "abnormal": config.is_abnormal(en_name),
                    "risk_level": config.class_risk_level(en_name),
                }
            )
            cn_classes.add(cn_name)
            max_conf = max(max_conf, conf)
            if config.is_abnormal(en_name):
                abnormal = True

        return detections, max_conf, abnormal, cn_classes

    def _summary(self, detections: List[Dict], elapsed: float = 0.0) -> Dict:
        """生成统一的风险等级与检测统计字段。"""
        counts = {"fire": 0, "smoke": 0, "smoking": 0, "person": 0}
        top_label = ""
        top_confidence = 0.0
        class_names = []

        for det in detections:
            class_en = det.get("class_en", "")
            class_names.append(class_en)
            if class_en in counts:
                counts[class_en] += 1
            conf = float(det.get("confidence") or 0)
            if conf > top_confidence:
                top_confidence = conf
                top_label = det.get("class_cn") or config.class_cn_name(class_en)

        risk_level = config.highest_risk_level(class_names)
        abnormal = any(config.is_abnormal(name) for name in class_names)
        return {
            "risk_level": risk_level,
            "num_detections": len(detections),
            "fire_count": counts["fire"],
            "smoke_count": counts["smoke"],
            "smoking_count": counts["smoking"],
            "person_count": counts["person"],
            "processing_time_ms": int(round(elapsed * 1000)),
            "top_label": top_label or "无",
            "top_confidence": round(top_confidence, 4),
            "risk_message": config.risk_message(counts),
            "abnormal": abnormal,
        }

    # ------------------------------------------------------------------
    # 图片检测
    # ------------------------------------------------------------------
    def detect_image(self, image_path: Path, conf: float) -> Dict:
        """
        检测一张图片，保存带框结果图。
        返回 dict，包含结果图相对路径、检测明细等。
        """
        if cv2 is None:
            return {"ok": False, "msg": f"OpenCV 未正确安装，无法检测：{CV2_IMPORT_ERROR}"}
        if not self.loaded:
            return {"ok": False, "msg": "模型未加载，无法检测"}

        try:
            t0 = time.time()
            results = self.model.predict(
                source=str(image_path), conf=conf, device=self.device, verbose=False
            )
            result = results[0]
            detections, max_conf, abnormal, cn_classes = self._parse_result(result)

            # 绘制并保存结果图
            plotted = result.plot()  # BGR ndarray
            result_name = f"result_{uuid.uuid4().hex[:12]}.jpg"
            result_path = config.RESULT_DIR / result_name
            cv2.imwrite(str(result_path), plotted)

            elapsed = round(time.time() - t0, 3)
            summary = self._summary(detections, elapsed)
            return {
                "ok": True,
                "detections": detections,
                "classes_cn": list(cn_classes),
                "max_confidence": round(max_conf, 4),
                "result_file": f"results/{result_name}",
                "elapsed": elapsed,
                **summary,
            }
        except Exception as e:
            return {"ok": False, "msg": f"图片检测失败：{e}"}

    # ------------------------------------------------------------------
    # 视频检测
    # ------------------------------------------------------------------
    def detect_video(self, video_path: Path, conf: float) -> Dict:
        """
        逐帧检测视频，输出带框视频（mp4）。
        为保证答辩演示流畅，对长视频做抽帧上限控制。
        """
        if cv2 is None:
            return {"ok": False, "msg": f"OpenCV 未正确安装，无法检测：{CV2_IMPORT_ERROR}"}
        if not self.loaded:
            return {"ok": False, "msg": "模型未加载，无法检测"}

        cap = None
        writer = None
        try:
            t0 = time.time()
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return {"ok": False, "msg": "无法打开视频文件"}

            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

            result_name = f"result_{uuid.uuid4().hex[:12]}.mp4"
            result_path = config.RESULT_DIR / result_name
            # 使用 mp4v 编码，兼容大多数浏览器（配合 README 中 FFmpeg 说明）
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(result_path), fourcc, fps, (width, height))
            if not writer.isOpened():
                return {"ok": False, "msg": "无法创建结果视频文件，请检查 OpenCV 视频编码支持或 results 目录权限"}

            cn_classes = set()
            max_conf = 0.0
            abnormal = False
            all_detections = []
            frame_idx = 0
            detected_frames = 0

            # 抽帧策略：超过 600 帧时跳帧，避免演示等待过久
            stride = 1
            if total_frames > 600:
                stride = max(1, total_frames // 600)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % stride == 0:
                    results = self.model.predict(
                        source=frame, conf=conf, device=self.device, verbose=False
                    )
                    result = results[0]
                    dets, mc, ab, ccs = self._parse_result(result)
                    cn_classes |= ccs
                    max_conf = max(max_conf, mc)
                    abnormal = abnormal or ab
                    all_detections.extend(dets)
                    if dets:
                        detected_frames += 1
                    frame_out = result.plot()
                    writer.write(frame_out)
                else:
                    writer.write(frame)
                frame_idx += 1

            elapsed = round(time.time() - t0, 3)
            summary = self._summary(all_detections, elapsed)
            return {
                "ok": True,
                "classes_cn": list(cn_classes),
                "max_confidence": round(max_conf, 4),
                "result_file": f"results/{result_name}",
                "frames": frame_idx,
                "detected_frames": detected_frames,
                "elapsed": elapsed,
                **summary,
            }
        except Exception as e:
            return {"ok": False, "msg": f"视频检测失败：{e}"}
        finally:
            if cap is not None:
                cap.release()
            if writer is not None:
                writer.release()

    # ------------------------------------------------------------------
    # 单帧检测（浏览器摄像头按帧上传）
    # ------------------------------------------------------------------
    def detect_frame(self, frame_bgr: np.ndarray, conf: float) -> Dict:
        """
        检测单帧画面（摄像头方案）。返回带框图的 jpg 字节及检测明细。
        不写入数据库，由调用方决定是否保存。
        """
        if cv2 is None:
            return {"ok": False, "msg": f"OpenCV 未正确安装，无法检测：{CV2_IMPORT_ERROR}"}
        if not self.loaded:
            return {"ok": False, "msg": "模型未加载，无法检测"}
        try:
            results = self.model.predict(
                source=frame_bgr, conf=conf, device=self.device, verbose=False
            )
            result = results[0]
            detections, max_conf, abnormal, cn_classes = self._parse_result(result)
            plotted = result.plot()
            ok, buf = cv2.imencode(".jpg", plotted)
            if not ok:
                return {"ok": False, "msg": "检测结果图编码失败"}
            img_bytes = buf.tobytes() if ok else b""
            summary = self._summary(detections, 0.0)
            return {
                "ok": True,
                "detections": detections,
                "classes_cn": list(cn_classes),
                "max_confidence": round(max_conf, 4),
                "image_bytes": img_bytes,
                **summary,
            }
        except Exception as e:
            return {"ok": False, "msg": f"实时检测失败：{e}"}


# 全局单例
yolo_service = YoloService()
