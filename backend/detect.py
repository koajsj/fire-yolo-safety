# -*- coding: utf-8 -*-
"""
命令行检测脚本（独立于 Web 服务）。

用途：方便在答辩前快速验证模型、生成示例结果图，或写论文时批量出图。

用法示例：
    # 检测单张图片
    python detect.py --source ../docs/demo.jpg

    # 检测视频
    python detect.py --source ../docs/demo.mp4

    # 指定置信度阈值
    python detect.py --source demo.jpg --conf 0.4
"""
import argparse
from pathlib import Path

import config
from yolo_service import yolo_service


def main():
    parser = argparse.ArgumentParser(description="消防安全行为检测 - 命令行工具")
    parser.add_argument("--source", required=True, help="图片或视频路径")
    parser.add_argument(
        "--conf", type=float, default=config.DEFAULT_CONF_THRESHOLD, help="置信度阈值"
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"[错误] 文件不存在：{source}")
        return

    print("[信息] 正在加载模型……")
    yolo_service.load_model()
    if not yolo_service.loaded:
        print(f"[错误] 模型加载失败：{yolo_service.load_error}")
        return
    print(f"[信息] 模型来源：{yolo_service.model_source}")
    print(f"[信息] 运行设备：{yolo_service.device}")

    ext = source.suffix.lower()
    if ext in config.IMAGE_EXTS:
        res = yolo_service.detect_image(source, args.conf)
    elif ext in config.VIDEO_EXTS:
        res = yolo_service.detect_video(source, args.conf)
    else:
        print(f"[错误] 不支持的文件类型：{ext}")
        return

    if not res.get("ok"):
        print(f"[错误] {res.get('msg')}")
        return

    print("[完成] 检测结果：")
    print(f"  类别：{res.get('classes_cn')}")
    print(f"  最高置信度：{res.get('max_confidence')}")
    print(f"  是否异常：{'是' if res.get('abnormal') else '否'}")
    print(f"  结果文件：{config.BASE_DIR / res.get('result_file')}")
    print(f"  耗时：{res.get('elapsed')} 秒")


if __name__ == "__main__":
    main()
