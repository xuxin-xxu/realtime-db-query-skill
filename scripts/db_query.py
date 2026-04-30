#!/usr/bin/env python3
"""
Unified Database Query Script for db-query (thin driver version).
Supports Oracle and MySQL connections via native Python thin drivers.
"""

import sys
import os
import re

# Determine paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _guard_read_only(query_str: str):
    """Reject any non-SELECT SQL to enforce read-only access."""
    cleaned = query_str.strip().upper()
    blocked = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
               'TRUNCATE', 'MERGE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK']
    for kw in blocked:
        if re.match(rf'\b{kw}\b', cleaned):
            raise PermissionError(f"Only SELECT queries allowed. Blocked key phrase: {kw}")


def _parse_oracle_jdbc_url(jdbc_url: str) -> str:
    """
    Parse Oracle JDBC URL and return dsn for oracledb thin driver.

    Input:  jdbc:oracle:thin:@host:port/service
    Output: host:port/service

    Also handles full descriptor format: jdbc:oracle:thin:@(description=...)
    """
    if not jdbc_url:
        raise ValueError("jdbc_url is required for Oracle connection")

    # Strip jdbc:oracle:thin:@ prefix
    prefix = "jdbc:oracle:thin:@"
    if jdbc_url.startswith(prefix):
        dsn = jdbc_url[len(prefix):]
    else:
        # Maybe it's already a plain dsn
        dsn = jdbc_url

    return dsn


def _parse_mysql_jdbc_url(jdbc_url: str) -> dict:
    """
    Parse MySQL JDBC URL and return params for mysql.connector.

    Input:  jdbc:mysql://host:port/db?params
    Output: {host, port, database, (optional query params)}
    """
    if not jdbc_url:
        raise ValueError("jdbc_url is required for MySQL connection")

    prefix = "jdbc:mysql://"
    if jdbc_url.startswith(prefix):
        rest = jdbc_url[len(prefix):]
    else:
        rest = jdbc_url

    # Split off query parameters
    query_params = {}
    if "?" in rest:
        rest, qs = rest.split("?", 1)
        for pair in qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                query_params[k] = v

    # Parse host:port/database
    result = {"host": "localhost", "port": 3306, "database": None}
    if "/" in rest:
        hostport, db = rest.split("/", 1)
        result["database"] = db
    else:
        hostport = rest

    if ":" in hostport:
        result["host"], port_str = hostport.split(":", 1)
        try:
            result["port"] = int(port_str)
        except ValueError:
            pass
    else:
        result["host"] = hostport

    result.update(query_params)
    return result


def _query_oracle(query_str: str, conn_info: dict) -> list[dict]:
    """Query Oracle using oracledb thin driver (no JDBC)."""
    import oracledb

    user = conn_info.get("user", "")
    password = conn_info.get("password", "")
    jdbc_url = conn_info.get("jdbc_url", "")

    dsn = _parse_oracle_jdbc_url(jdbc_url)

    try:
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
    except oracledb.Error as e:
        raise RuntimeError(f"Oracle connection failed: {e}")

    try:
        cur = connection.cursor()
        cur.execute(query_str)
        cols = [_py_str(desc[0]) for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, [_py_str(v) for v in row])) for row in rows]
    finally:
        connection.close()


def _query_mysql(query_str: str, conn_info: dict) -> list[dict]:
    """Query MySQL using mysql.connector (no JDBC)."""
    import mysql.connector

    user = conn_info.get("user", "")
    password = conn_info.get("password", "")
    jdbc_url = conn_info.get("jdbc_url", "")

    params = _parse_mysql_jdbc_url(jdbc_url)

    config = {
        "host": params["host"],
        "port": params["port"],
        "user": user,
        "password": password,
        "database": params.get("database"),
    }

    try:
        connection = mysql.connector.connect(**config)
    except mysql.connector.Error as e:
        raise RuntimeError(f"MySQL connection failed: {e}")

    try:
        cur = connection.cursor()
        cur.execute(query_str)
        cols = [_py_str(desc[0]) for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, [_py_str(v) for v in row])) for row in rows]
    finally:
        connection.close()


def query(query_str: str, alias: str = None) -> list[dict]:
    """
    Execute SELECT query via Python thin driver (MySQL or Oracle).

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
