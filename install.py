#!/usr/bin/env python3
"""
Headless installation script for db-query (thin driver version).
Designed to be executed by the OpenClaw Agent via command-line arguments.

No Java / JDBC / JAR dependencies needed.
"""

import os
import sys
import subprocess
import argparse

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


if __name__ == "__main__":
    main()
