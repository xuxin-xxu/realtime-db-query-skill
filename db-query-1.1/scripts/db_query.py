#!/usr/bin/env python3
"""
Unified Database Query Script for db-query 1.1.
Supports Oracle ADB (TCPS/Wallet) and MySQL connections natively.
"""

import sys
import os
import re

# Determine paths: scripts live in workspace, lib lives in installed skill
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_SKILL_DIR = os.path.dirname(SCRIPT_DIR)  # workspace_mayu/skills/db-query
INSTALLED_SKILL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(WORKSPACE_SKILL_DIR))), "skills", "db-query")
LIB_DIR = os.path.join(INSTALLED_SKILL_DIR, "lib")
WALLET_PATH = os.environ.get("TNS_ADMIN", "/home/ubuntu/adbwallet")

ORACLE_DEFAULT_DSN = "(description=(address=(protocol=tcps)(port=1522)(host=adb.ca-toronto-1.oraclecloud.com))(connect_data=(service_name=gdc4bbe84a839b8_xxuclawdb_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"

ORACLE_REQUIRED_JARS = [
    "ojdbc11.jar",       # JDBC driver (Java 21 compatible)
    "oraclepki.jar",      # Oracle PKI for wallet operations
    "osdt_core.jar",      # Oracle security core
    "osdt_cert.jar",      # Oracle security cert
]

MYSQL_REQUIRED_JARS = [
    "mysql-connector-java.jar"
]

def _guard_read_only(query_str: str):
    """Reject any non-SELECT SQL to enforce read-only access."""
    cleaned = query_str.strip().upper()
    blocked = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
               'TRUNCATE', 'MERGE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK']
    for kw in blocked:
        if re.match(rf'\b{kw}\b', cleaned):
            raise PermissionError(f"Only SELECT queries allowed. Blocked key phrase: {kw}")

def _find_jars(jar_list: list[str]) -> list[str]:
    """Find required JARs in lib directory. Raise Agent-tailored error if missing."""
    found = []
    missing = []
    for jar in jar_list:
        path = os.path.join(LIB_DIR, jar)
        if os.path.exists(path):
            found.append(path)
        else:
            missing.append(jar)
    if missing:
        raise RuntimeError(
            f"缺少必需的 JDBC 组件: {', '.join(missing)}。 请对用户说：'查询需要本地依赖支持，请问您允许我自动下载缺失的 JDBC 驱动，还是您稍后自己手动解决？' 如果用户同意自动下载，请您在后台替用户运行终端命令：\n"
            f"python install.py --auto-jdbc"
        )
    return found

def _check_jvm_before_start():
    import subprocess
    try:
        res = subprocess.run(["java", "-version"], capture_output=True, text=True, check=True)
        output = res.stderr if res.stderr else res.stdout
        match = re.search(r'version "(\d+)\.', output)
        if match and int(match.group(1)) >= 18:
            return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    raise RuntimeError(
        "检测到本机未提供 Java(>=18) 生产环境，无法驱动查询组件。请立刻对用户说：'系统尚未安装符合要求的 Java 依赖库。请问您允许我立刻使用底层沙盒为您全自动下载安装，还是您希望稍后自己手动处理？' 如果用户指示同意自动安装，请您在后台替用户执行终端指令：\n"
        "python install.py --auto-java"
    )

def _build_oracle_jdbc_url(user: str, password: str, dsn: str = None) -> str:
    """Build Oracle JDBC thin URL with TCPS descriptor."""
    # If the user's connection already provided a full JDBC URL starting with jdbc:, use it
    if dsn and dsn.startswith("jdbc:oracle:"):
        return dsn
    if dsn:
        return f"jdbc:oracle:thin:@{dsn}"
    return f"jdbc:oracle:thin:@{ORACLE_DEFAULT_DSN}"

def _get_oracle_jdbc_properties(user: str, password: str, wallet: str = None) -> dict:
    """Build Java Properties for Oracle JDBC connection."""
    w = wallet or WALLET_PATH
    return {
        "user": user,
        "password": password,
        "oracle.net.tns_admin": w,
        "oracle.net.wallet_location": f"(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY={w})))",
        "oracle.jdbc.ssl_server_dn_match": "true",
    }

def _query_oracle(query_str: str, conn_info: dict) -> list[dict]:
    import jpype
    import jaydebeapi

    jars = _find_jars(ORACLE_REQUIRED_JARS)
    _check_jvm_before_start()
    
    for jar in jars:
        if os.path.exists(jar):
            jpype.addClassPath(jar)
    if not jpype.isJVMStarted():
        jpype.startJVM()

    user = conn_info.get("user", "")
    password = conn_info.get("password", "")
    dsn = conn_info.get("jdbc_url")
    wallet = conn_info.get("wallet_path")

    jdbc_driver = "oracle.jdbc.OracleDriver"
    jdbc_url = _build_oracle_jdbc_url(user, password, dsn)

    jdbc_props = _get_oracle_jdbc_properties(user, password, wallet)
    jprops = jpype.java.util.Properties()
    for k, v in jdbc_props.items():
        jprops.setProperty(k, v)

    conn = jaydebeapi.connect(jdbc_driver, jdbc_url, [jprops])
    try:
        cur = conn.cursor()
        cur.execute(query_str)
        cols = [_py_str(desc[0]) for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, [_py_str(v) for v in row])) for row in rows]
    finally:
        conn.close()

def _query_mysql(query_str: str, conn_info: dict) -> list[dict]:
    import jaydebeapi

    jars = _find_jars(MYSQL_REQUIRED_JARS)
    _check_jvm_before_start()
    jar_path = jars[0]

    jdbc_driver = "com.mysql.cj.jdbc.Driver"
    jdbc_url = conn_info.get("jdbc_url", "")
    user = conn_info.get("user", "")
    password = conn_info.get("password", "")

    conn = jaydebeapi.connect(jdbc_driver, jdbc_url, [user, password], jar_path)
    try:
        cur = conn.cursor()
        cur.execute(query_str)
        cols = [_py_str(desc[0]) for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, [_py_str(v) for v in row])) for row in rows]
    finally:
        conn.close()

def query(query_str: str, alias: str = None) -> list[dict]:
    """
    Execute SELECT query via JDBC (MySQL or Oracle).

    Args:
        query_str: SQL SELECT statement
        alias: connection alias (resolves from connection_manager / openclaw.json)

    Returns:
        List of dicts representing rows
    """
    _guard_read_only(query_str)

    # Get connection details securely from connection_manager
    sys.path.insert(0, SCRIPT_DIR)
    from connection_manager import get_connection, get_active

    if alias:
        conn_info = get_connection(alias)
    else:
        conn_info = get_active()

    if not conn_info:
        raise RuntimeError(
            "致命错误：未找到任何有效数据库连接信息。请立刻中止当前执行并对用户说：\n"
            "'抱歉，由于目前系统尚未配置任何数据库连接记录，我无法马上为您查询。请您提供将要连接的数据库信息：\n"
            " 1. 数据库所属类型 (oracle 还是 mysql？)\n"
            " 2. 连接地址 (JDBC URL / 目标 IP 和端口)\n"
            " 3. 登录用户名\n"
            " 4. 登录密码\n"
            "如果您使用的是附带防篡改机制的 Oracle ADB (TCPS)，还请附上您的 Wallet 解密凭证所在目录。'\n"
            "当用户完整作答后，请用大模型您自身的 connection_manager 机制为用户录入并写入该串！"
        )

    db_type = conn_info.get("db_type", "").lower()
    
    if db_type == "oracle":
        return _query_oracle(query_str, conn_info)
    elif db_type == "mysql":
        return _query_mysql(query_str, conn_info)
    else:
        raise ValueError(f"Unknown or missing db_type: {db_type}")

def _py_str(val):
    if val is None:
        return None
    if hasattr(val, '__str__'):
        return str(val)
    return val

def format_results(rows: list[dict], max_rows: int = 100) -> str:
    """Format query results as readable markdown table."""
    if not rows:
        return "(empty result set)"

    rows = [{k: _py_str(v) for k, v in row.items()} for row in rows]

    if len(rows) > max_rows:
        rows = rows[:max_rows]
        footer = f"\n_... truncated to {max_rows} rows (total available)_"
    else:
        footer = ""

    headers = list(rows[0].keys())
    # Ensure keys are strings for max length calculation
    str_headers = [str(h) for h in headers]
    col_widths = {str(h): max(len(str(h)), max(len(str(r.get(h, ''))) for r in rows)) for h in headers}

    header_line = "| " + " | ".join(str(h).ljust(col_widths[str(h)]) for h in headers) + " |"
    sep_line = "|" + "|".join("-" * (col_widths[str(h)] + 2) for h in headers) + "|"
    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(str(row.get(h, '')).ljust(col_widths[str(h)]) for h in headers) + " |")

    return "\n".join([header_line, sep_line] + data_lines) + footer

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: db_query.py <query> [alias]")
        sys.exit(1)

    q = sys.argv[1]
    alias = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        rows = query(q, alias)
        print(format_results(rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
