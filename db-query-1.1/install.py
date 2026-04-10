#!/usr/bin/env python3
"""
Headless installation script for db-query 1.1.
Designed to be executed by the OpenClaw Agent via command-line arguments.
"""

import os
import sys
import platform
import subprocess
import urllib.request
import re
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(SCRIPT_DIR, "lib")
os.makedirs(LIB_DIR, exist_ok=True)

MAVEN_BASE = "https://repo1.maven.org/maven2"
ORACLE_JDBC_BASE = "https://repo1.maven.org/maven2/com/oracle/database/jdbc"
ORACLE_SEC_BASE = "https://repo1.maven.org/maven2/com/oracle/database/security"

JARS_TO_CHECK = {
    "mysql-connector-java.jar": f"{MAVEN_BASE}/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar",
    "ojdbc11.jar": f"{ORACLE_JDBC_BASE}/ojdbc11/21.21.0.0/ojdbc11-21.21.0.0.jar",
    "oraclepki.jar": f"{ORACLE_SEC_BASE}/oraclepki/21.21.0.0/oraclepki-21.21.0.0.jar",
    "osdt_core.jar": f"{ORACLE_SEC_BASE}/osdt_core/21.21.0.0/osdt_core-21.21.0.0.jar",
    "osdt_cert.jar": f"{ORACLE_SEC_BASE}/osdt_cert/21.21.0.0/osdt_cert-21.21.0.0.jar",
}

def check_java_version() -> bool:
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, check=True)
        output = result.stderr if result.stderr else result.stdout
        
        match = re.search(r'version "(\d+)\.', output)
        if match:
            major_version = int(match.group(1))
            return major_version >= 18
        return False
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def install_java():
    system = platform.system()
    try:
        if system == "Linux":
            print("[install] 正在尝试使用 apt-get 安装 OpenJDK 21...")
            res = subprocess.run(["sudo", "apt-get", "update"], capture_output=True)
            res = subprocess.run(["sudo", "apt-get", "install", "-y", "openjdk-21-jre"], capture_output=True)
            if res.returncode == 0:
                print("[install] ✅ 成功通过 apt-get 安装 Java 21。")
                return
            
            print("[install] ⚠️ apt-get 安装失败或不存在，正在尝试 dnf 方式...")
            res = subprocess.run(["sudo", "dnf", "install", "-y", "java-21-openjdk-headless"], capture_output=True)
            if res.returncode == 0:
                print("[install] ✅ 成功通过 dnf 安装 Java 21。")
                return
            
            print("[install] ❌ 包管理器自动安装均失败，需手动安装。")
            sys.exit(1)
        
        else:
            print("[install] 正在使用 Python pip 安装 JDK 包 (无需 sudo)...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "install-jdk", "--quiet"])
            
            import jdk
            print("[install] 正在从 Eclipse Temurin 下载并安装 JDK 21 到 ~/.jdk ...")
            installed_path = jdk.install('21', jre=True)
            print(f"[install] ✅ 成功下载 JDK 到: {installed_path}")
            print(f"[install] \n⚠️ 注意：安装后重新开启 terminal 或使大模型重试查询即可利用此环境。")

    except Exception as e:
        print(f"[install] ❌ 自动安装 Java 时出错: {e}")
        sys.exit(1)

def get_missing_jars() -> list[str]:
    return [jar for jar in JARS_TO_CHECK.keys() if not os.path.exists(os.path.join(LIB_DIR, jar))]

def install_jars():
    missing_jars = get_missing_jars()
    if not missing_jars:
        print("[install] ✅ 所有所需 JDBC JAR 文件完备，跳过下载。")
        return

    print(f"[install] 准备下载缺少的 {len(missing_jars)} 个文件到: {LIB_DIR}")
    for jar in missing_jars:
        url = JARS_TO_CHECK[jar]
        dest = os.path.join(LIB_DIR, jar)
        print(f"[install]   ↓ 正在下载 {jar} ...", end="", flush=True)
        try:
            urllib.request.urlretrieve(url, dest)
            size = os.path.getsize(dest) / (1024 * 1024)
            print(f" 完成 ({size:.1f} MB)")
        except Exception as e:
            print(f"\n[install]   ❌ 下载 {jar} 失败: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Headless DB-Query dependencies installer")
    parser.add_argument("--auto-java", action="store_true", help="Automatically install Java dependencies safely")
    parser.add_argument("--auto-jdbc", action="store_true", help="Automatically download JDBC drivers safely")
    args = parser.parse_args()

    if not args.auto_java and not args.auto_jdbc:
        print("未指定动作。请使用 --auto-java 或 --auto-jdbc，通过 Agent 指令进行依赖补充。")
        sys.exit(0)

    if args.auto_java:
        print("=== 开始自动化处理 Java 安装 ===")
        if check_java_version():
            print("=> 检测到符合要求的 Java 运行时，无需安装。")
        else:
            install_java()
            
    if args.auto_jdbc:
        print("=== 开始自动化处理 JDBC 连接包 ===")
        install_jars()

if __name__ == "__main__":
    main()
