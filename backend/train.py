# -*- coding: utf-8 -*-
"""
消防安全行为检测模型训练脚本。

说明：
- 训练得到的最优权重 runs/detect/train/weights/best.pt
  需要复制到 weights/best.pt，系统即可自动加载。
- 数据集需为 YOLO 格式，并提供 data.yaml（见 docs/data.yaml.example）。

用法示例：
    python train.py --data ../docs/data.yaml --epochs 100 --imgsz 640 --batch 16

类别建议（消防安全场景，与 config.ABNORMAL_CLASSES 对应）：
    0: fire      火焰
    1: smoke     烟雾
    2: smoking   抽烟
    3: person    人员
"""
import argparse

import config


def main():
    parser = argparse.ArgumentParser(description="消防安全行为检测 - 模型训练")
    parser.add_argument(
        "--data", required=True, help="数据集配置文件 data.yaml 路径"
    )
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图像尺寸")
    parser.add_argument("--batch", type=int, default=16, help="批大小")
    parser.add_argument(
        "--weights", default="yolov8n.pt", help="预训练权重，默认 yolov8n.pt"
    )
    parser.add_argument(
        "--device", default="", help="训练设备，如 0 / cpu / mps，留空自动选择"
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except Exception as e:
        print(f"[错误] 未安装 ultralytics：{e}")
        return

    # 自动选择设备
    device = args.device
    if not device:
        try:
            import torch

            if torch.cuda.is_available():
                device = 0
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        except Exception:
            device = "cpu"

    print(f"[信息] 使用预训练权重：{args.weights}")
    print(f"[信息] 训练设备：{device}")

    model = YOLO(args.weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        project="runs/detect",
        name="fire_safety",
    )

    print("[完成] 训练结束。")
    print("[提示] 请将 runs/detect/fire_safety/weights/best.pt 复制到：")
    print(f"        {config.BEST_MODEL_PATH}")
    print("        然后重启后端，系统会自动加载自训练模型。")


if __name__ == "__main__":
    main()
