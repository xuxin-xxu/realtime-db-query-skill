#!/usr/bin/env python3
"""
Headless installation script for db-query (thin driver version).
Designed to be executed by the OpenClaw Agent via command-line arguments.

Pure Python implementation.
"""

import os
import sys
import subprocess
import argparse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_FILE = os.path.join(SCRIPT_DIR, "requirements.txt")


def install_python_deps():
    """Install Python dependencies using pip."""
    print("[install] 正在安装 Python 依赖...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE, "--quiet"]
        )
        print("[install] ✅ Python 依赖安装完成。")
    except subprocess.CalledProcessError as e:
        print(f"[install] ❌ pip 安装失败: {e}")
        sys.exit(1)


def install_cjk_fonts():
    """Ensure CJK fonts are installed for matplotlib during setup."""
    print("[install] 正在检查/安装中文字体支持 (Noto Sans CJK)...")
    system_font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    if any(os.path.exists(p) for p in system_font_paths):
        print("[install] ✅ 系统已存在 CJK 字体，跳过下载。")
        return

    user_font_dir = os.path.expanduser("~/.local/share/fonts")
    user_font_ttc = os.path.join(user_font_dir, "NotoSansCJK-Regular.ttc")
    user_font_otf = os.path.join(user_font_dir, "NotoSansCJKsc-Regular.otf")

    if os.path.exists(user_font_ttc) or os.path.exists(user_font_otf):
        print("[install] ✅ 用户目录已存在 CJK 字体，跳过下载。")
        return

    os.makedirs(user_font_dir, exist_ok=True)
    font_url_regular = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
    font_url_bold = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
    user_font_bold_otf = os.path.join(user_font_dir, "NotoSansCJKsc-Bold.otf")
    
    print(f"[install] 📦 正在下载 Noto Sans CJK 字体 (~60MB)，请稍候...")
    try:
        urllib.request.urlretrieve(font_url_regular, user_font_otf)
        urllib.request.urlretrieve(font_url_bold, user_font_bold_otf)
        print(f"[install] ✅ 字体已成功下载到 {user_font_dir}。")
    except Exception as e:
        print(f"[install] ⚠️ 字体下载失败: {e}。将尝试备用链接...")
        try:
            fallback_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJK-Regular.otf"
            fallback_bold_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJK-Bold.otf"
            urllib.request.urlretrieve(fallback_url, user_font_otf)
            urllib.request.urlretrieve(fallback_bold_url, user_font_bold_otf)
            print(f"[install] ✅ 备用字体已成功下载。")
        except Exception as fallback_e:
            print(f"[install] ⚠️ 备用字体下载亦失败: {fallback_e}。图表中的中文可能无法正常显示。")


def main():
    parser = argparse.ArgumentParser(description="DB-Query dependencies installer (thin driver)")
    parser.add_argument("--auto-pip", action="store_true", help="Automatically install Python dependencies via pip")
    args = parser.parse_args()

    if not args.auto_pip:
        print("未指定动作。请使用 --auto-pip 安装 Python 依赖。")
        print()
        print("  用法: python install.py --auto-pip")
        sys.exit(0)

    if args.auto_pip:
        print("=== 开始安装 Python 依赖 ===")
        install_python_deps()
        
        print("\n=== 开始安装中文字体 ===")
        install_cjk_fonts()


if __name__ == "__main__":
    main()
