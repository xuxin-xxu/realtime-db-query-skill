#!/usr/bin/env python3
"""
Oracle ADB JDBC Query Script for db-query skill.
Uses JayDeBeApi + JPype + Oracle JDBC Thin Driver with TCPS/Wallet.
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

# Oracle ADB connection parameters (for xxuclawdb_high)
DEFAULT_DSN = "(description=(address=(protocol=tcps)(port=1522)(host=adb.ca-toronto-1.oraclecloud.com))(connect_data=(service_name=gdc4bbe84a839b8_xxuclawdb_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"

REQUIRED_JARS = [
    "ojdbc11.jar",       # JDBC driver (Java 21 compatible)
    "oraclepki.jar",      # Oracle PKI for wallet operations
    "osdt_core.jar",      # Oracle security core
    "osdt_cert.jar",      # Oracle security cert
]


def _guard_read_only(query: str):
    """Reject any non-SELECT SQL to enforce read-only access."""
    cleaned = query.strip().upper()
    blocked = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
               'TRUNCATE', 'MERGE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK']
    for kw in blocked:
        if re.match(rf'\b{kw}\b', cleaned):
            raise PermissionError(f"Only SELECT queries allowed. Blocked: {kw}")


def _find_jars():
    """Find Oracle JARs in lib directory."""
    found = []
    missing = []
    for jar in REQUIRED_JARS:
        path = os.path.join(LIB_DIR, jar)
        if os.path.exists(path):
            found.append(path)
        else:
            missing.append(jar)
    if missing:
        raise RuntimeError(f"Missing required JARs: {', '.join(missing)}")
    return found


def _build_jdbc_url(user: str, password: str, dsn: str = None) -> str:
    """Build Oracle JDBC thin URL with TCPS descriptor."""
    if dsn:
        return f"jdbc:oracle:thin:@{dsn}"
    return f"jdbc:oracle:thin:@{DEFAULT_DSN}"


def _get_jdbc_properties(user: str, password: str) -> dict:
    """Build Java Properties for Oracle JDBC connection."""
    return {
        "user": user,
        "password": password,
        "oracle.net.tns_admin": WALLET_PATH,
        "oracle.net.wallet_location": f"(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY={WALLET_PATH})))",
        "oracle.jdbc.ssl_server_dn_match": "true",
    }


def query(query_str: str, user: str, password: str, dsn: str = None) -> list[dict]:
    """
    Execute SELECT query on Oracle ADB via JDBC thin driver with wallet.

    Args:
        query_str: SQL SELECT statement
        user: database username
        password: database password
        dsn: optional Oracle descriptor (default: xxuclawdb_high)

    Returns:
        List of dicts representing rows
    """
    _guard_read_only(query_str)

    import jpype

    jars = _find_jars()
    for jar in jars:
        jpype.addClassPath(jar)

    if not jpype.isJVMStarted():
        jpype.startJVM()

    # Use jpype.JProxy/JClass approach to avoid jpype.imports issues at module load
    import jaydebeapi

    jdbc_driver = "oracle.jdbc.OracleDriver"
    jdbc_url = _build_jdbc_url(user, password, dsn)

    # Build Java Properties using dict approach
    jdbc_props = _get_jdbc_properties(user, password)

    # Use a workaround: pass properties as a JProperties object
    # We create it via reflection since we can't import java.* before JVM start
    jprops = jpype.java.util.Properties()
    for k, v in jdbc_props.items():
        jprops.setProperty(k, v)

    conn = jaydebeapi.connect(jdbc_driver, jdbc_url, [jprops])
    try:
        cur = conn.cursor()
        cur.execute(query_str)
        cols = [_py_str(desc[0]) for desc in cur.description]
        rows = cur.fetchall()
        # Convert java.sql.Row items to Python str
        return [dict(zip(cols, [_py_str(v) for v in row])) for row in rows]
    finally:
        conn.close()


def _py_str(val):
    """Convert Java String to Python str if needed."""
    if hasattr(val, '__str__'):
        return str(val)
    return val


def format_results(rows: list[dict], max_rows: int = 100) -> str:
    """Format query results as readable markdown table."""
    if not rows:
        return "(empty result set)"

    # Convert all values to Python str for formatting
    rows = [{k: _py_str(v) for k, v in row.items()} for row in rows]

    if len(rows) > max_rows:
        rows = rows[:max_rows]
        footer = f"\n_... truncated to {max_rows} rows (total available)_"
    else:
        footer = ""

    headers = list(rows[0].keys())
    col_widths = {h: max(len(h), max(len(str(r.get(h, ''))) for r in rows)) for h in headers}

    header_line = "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |"
    sep_line = "|" + "|".join("-" * (col_widths[h] + 2) for h in headers) + "|"
    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(str(row.get(h, '')).ljust(col_widths[h]) for h in headers) + " |")

    return "\n".join([header_line, sep_line] + data_lines) + footer


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: oracle_query.py <query> <user> <password> [dsn]")
        sys.exit(1)

    q, user, password = sys.argv[1], sys.argv[2], sys.argv[3]
    dsn = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        rows = query(q, user, password, dsn)
        print(format_results(rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
