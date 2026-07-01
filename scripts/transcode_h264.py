# -*- coding: utf-8 -*-
"""
将 results 目录下的检测结果视频转码为 H.264（浏览器可直接播放）。

部分系统下 OpenCV 写出的 mp4v 编码浏览器无法播放，可用本脚本借助 FFmpeg 转码。
依赖：需先安装 FFmpeg 并加入系统 PATH（见 README）。

用法：
    python scripts/transcode_h264.py results/result_xxxx.mp4
    python scripts/transcode_h264.py            # 转码 results 目录下全部 mp4
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = BASE_DIR / "results"


def transcode(src: Path):
    dst = src.with_name(src.stem + "_h264.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(dst),
    ]
    print(f"[转码] {src.name} -> {dst.name}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[完成] {dst}")
    except FileNotFoundError:
        print("[错误] 未找到 ffmpeg，请先安装并加入 PATH。")
    except subprocess.CalledProcessError as e:
        print(f"[错误] 转码失败：{e}")


def main():
    if len(sys.argv) > 1:
        transcode(Path(sys.argv[1]))
    else:
        mp4s = [p for p in RESULT_DIR.glob("*.mp4") if "_h264" not in p.stem]
        if not mp4s:
            print("[信息] results 目录下没有需要转码的 mp4 文件。")
        for p in mp4s:
            transcode(p)


if __name__ == "__main__":
    main()
