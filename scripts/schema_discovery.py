#!/usr/bin/env python3
"""
Schema Discovery for db-query skill.

Fetches DDL, column info, and comments from Oracle/MySQL
and writes them to skill/memory/schema_<alias>.md.

Usage:
    discover_oracle(conn: dict) -> str  # returns path to schema file
    discover_mysql(conn: dict)  -> str
"""

import os
import sys
import time
import re

# scripts/ is at skills/db-query/scripts/
# lib/ is at skills/db-query/lib/ (installed skill, not workspace)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)  # .../workspace_mayu/skills/db-query
_INSTALLED_SKILL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(_WORKSPACE_SKILL_DIR))),
    "skills", "db-query"
)  # /home/ubuntu/.openclaw/skills/db-query
SKILL_DIR = _INSTALLED_SKILL_DIR
MEMORY_DIR = os.path.join(_WORKSPACE_SKILL_DIR, "memory")


# ── Shared helpers ───────────────────────────────────────────────────────────

def _safe(val) -> str:
    if val is None:
        return ""
    if hasattr(val, '__str__'):
        return str(val)
    return val


def _to_markdown_table(headers: list, rows: list[list]) -> str:
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |")
    return "\n".join([header_line, sep_line] + data_lines)


# ── Oracle Discovery ─────────────────────────────────────────────────────────

def _run_oracle_query(query_sql: str, conn: dict, max_retries: int = 2) -> list[dict]:
    """Execute query using JayDeBeApi with Oracle wallet.
    TCPS connections can take 30-60s due to SSL handshake; retries with longer timeout.
    """
    import jpype
    import jaydebeapi
    import socket

    jar_dir = os.path.join(SKILL_DIR, "lib")
    jars = [os.path.join(jar_dir, f) for f in os.listdir(jar_dir)
            if f.endswith(".jar") and f.startswith(("ojdbc", "oraclepki", "osdt"))]

    # Ensure JVM is started with correct classpath
    for jar in jars:
        if os.path.exists(jar):
            jpype.addClassPath(jar)

    if not jpype.isJVMStarted():
        jpype.startJVM()

    jdbc_driver = "oracle.jdbc.OracleDriver"
    jdbc_url = conn["jdbc_url"]
    wallet = conn.get("wallet_path")

    jprops = jpype.java.util.Properties()
    jprops.setProperty("user", conn["user"])
    jprops.setProperty("password", conn["password"])
    if wallet:
        jprops.setProperty("oracle.net.tns_admin", wallet)
        jprops.setProperty("oracle.net.wallet_location",
                          f"(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY={wallet})))")
        jprops.setProperty("oracle.jdbc.ssl_server_dn_match", "true")

    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            conn_jdbc = jaydebeapi.connect(jdbc_driver, jdbc_url, [jprops])
            try:
                cur = conn_jdbc.cursor()
                cur.execute(query_sql)
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(cols, [_safe(v) for v in row])) for row in rows]
            finally:
                conn_jdbc.close()
        except (socket.timeout, OSError, jpype.JavaException) as e:
            last_exc = e
            if attempt < max_retries:
                import time
                print(f"Query attempt {attempt+1} failed ({type(e).__name__}), retrying...", file=sys.stderr)
                time.sleep(5)
            continue

    raise RuntimeError(f"Query failed after {max_retries+1} attempts: {last_exc}")


def _oracle_exec(conn: dict, query_sql: str, jdbc_conn):
    """Execute a query using an existing JDBC connection (no new connection needed)."""
    cur = jdbc_conn.cursor()
    cur.execute(query_sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, [_safe(v) for v in row])) for row in rows]


def discover_oracle(conn: dict, timeout_sec: int = 300) -> str:
    """
    Discover all table DDL + comments for an Oracle connection.
    Uses a SINGLE JDBC connection for all queries to avoid repeated TCPS handshakes.
    Writes to memory/schema_<alias>.md and returns the path.

    timeout_sec: Overall timeout for the entire discovery process.
    """
    import jpype
    import jaydebeapi

    alias = conn["alias"]
    user = conn["user"]
    start_time = time.time()

    def elapsed():
        return time.time() - start_time

    def check_timeout():
        if elapsed() > timeout_sec:
            raise TimeoutError(f"Schema discovery 超时（{timeout_sec}s），已停止。")

    # ── Establish a SINGLE JDBC connection (reused for all queries) ──
    jar_dir = os.path.join(SKILL_DIR, "lib")
    jars = [os.path.join(jar_dir, f) for f in os.listdir(jar_dir)
            if f.endswith(".jar") and f.startswith(("ojdbc", "oraclepki", "osdt"))]
    for jar in jars:
        if os.path.exists(jar):
            jpype.addClassPath(jar)

    if not jpype.isJVMStarted():
        jpype.startJVM()

    jdbc_driver = "oracle.jdbc.OracleDriver"
    jdbc_url = conn["jdbc_url"]
    wallet = conn.get("wallet_path")

    jprops = jpype.java.util.Properties()
    jprops.setProperty("user", conn["user"])
    jprops.setProperty("password", conn["password"])
    if wallet:
        jprops.setProperty("oracle.net.tns_admin", wallet)
        jprops.setProperty("oracle.net.wallet_location",
                          f"(SOURCE=(METHOD=FILE)(METHOD_DATA=(DIRECTORY={wallet})))")
        jprops.setProperty("oracle.jdbc.ssl_server_dn_match", "true")

    print(f"[{elapsed():.1f}s] Establishing JDBC connection (TCPS, may take 30-60s)...", file=sys.stderr)
    jdbc_conn = jaydebeapi.connect(jdbc_driver, jdbc_url, [jprops])
    print(f"[{elapsed():.1f}s] Connected! Proceeding with metadata queries...", file=sys.stderr)

    try:
        lines = []
        lines.append(f"# Schema: {alias} (Oracle)\n")
        lines.append(f"**用户:** `{user}`")
        lines.append(f"**发现时间:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")

        # ── 1. Table list ──
        check_timeout()
        print(f"[{elapsed():.1f}s] Fetching table list...", file=sys.stderr)
        tables_query = """
        SELECT t.TABLE_NAME, t.NUM_ROWS, c.COMMENTS AS TABLE_COMMENT
        FROM USER_TABLES t
        LEFT JOIN USER_TAB_COMMENTS c ON t.TABLE_NAME = c.TABLE_NAME
        ORDER BY t.NUM_ROWS DESC NULLS LAST
        """
        tables = _oracle_exec(conn, tables_query, jdbc_conn)
        lines.append("## 表清单\n")
        lines.append("| 表名 | 行数 | 注释 |")
        lines.append("|------|------|------|")
        for t in tables:
            comment = _safe(t.get("TABLE_COMMENT", ""))
            rows = t.get("NUM_ROWS") or "?"
            lines.append(f"| {t['TABLE_NAME']} | {rows} | {comment} |")
        lines.append("")

        # ── 2. Per-table column details ──
        check_timeout()
        print(f"[{elapsed():.1f}s] Fetching column details for {len(tables)} tables...", file=sys.stderr)
        lines.append("## 表结构详情\n")

        for i, t in enumerate(tables):
            check_timeout()
            tbl = t["TABLE_NAME"]
            print(f"[{elapsed():.1f}s]  [{i+1}/{len(tables)}] Processing {tbl}...", file=sys.stderr)

            col_query = f"""
            SELECT c.COLUMN_NAME, c.DATA_TYPE, c.DATA_LENGTH,
                   c.DATA_PRECISION, c.DATA_SCALE, c.NULLABLE, c.COLUMN_ID,
                   col.COMMENTS AS COLUMN_COMMENT
            FROM USER_TAB_COLUMNS c
            LEFT JOIN USER_COL_COMMENTS col
                ON c.TABLE_NAME = col.TABLE_NAME AND c.COLUMN_NAME = col.COLUMN_NAME
            WHERE c.TABLE_NAME = '{tbl}'
            ORDER BY c.COLUMN_ID
            """
            cols = _oracle_exec(conn, col_query, jdbc_conn)
            if not cols:
                continue

            table_comment = _safe(t.get("TABLE_COMMENT", ""))
            lines.append(f"### {tbl}")
            if table_comment:
                lines.append(f"**注释:** {table_comment}")
            lines.append("")
            lines.append("| 字段名 | 类型 | 可空 | 注释 |")
            lines.append("|--------|------|------|------|")
            for c in cols:
                dtype = _safe(c.get("DATA_TYPE", ""))
                dlen = _safe(c.get("DATA_LENGTH", ""))
                dprec = _safe(c.get("DATA_PRECISION", ""))
                dscale = _safe(c.get("DATA_SCALE", ""))
                nullable = "Y" if _safe(c.get("NULLABLE", "")) == "Y" else "N"
                comment = _safe(c.get("COLUMN_COMMENT", ""))

                if dprec and dprec != "0":
                    dtype_full = f"{dtype}({dprec}"
                    if dscale and dscale != "0":
                        dtype_full += f",{dscale}"
                    dtype_full += ")"
                elif dlen:
                    dtype_full = f"{dtype}({dlen})"
                else:
                    dtype_full = dtype

                lines.append(f"| {c['COLUMN_NAME']} | {dtype_full} | {nullable} | {comment} |")
            lines.append("")

        # ── 3. Foreign keys ──
        check_timeout()
        print(f"[{elapsed():.1f}s] Fetching foreign keys...", file=sys.stderr)
        fk_query = """
        SELECT a.TABLE_NAME AS CHILD_TABLE,
               a.COLUMN_NAME AS CHILD_COLUMN,
               b.TABLE_NAME AS PARENT_TABLE,
               b.COLUMN_NAME AS PARENT_COLUMN,
               cons.CONSTRAINT_NAME
        FROM USER_CONSTRAINTS cons
        JOIN USER_CONS_COLUMNS a ON cons.CONSTRAINT_NAME = a.CONSTRAINT_NAME
        JOIN USER_CONS_COLUMNS b ON cons.R_CONSTRAINT_NAME = b.CONSTRAINT_NAME
        WHERE cons.CONSTRAINT_TYPE = 'R'
        ORDER BY a.TABLE_NAME, a.POSITION
        """
        fks = _oracle_exec(conn, fk_query, jdbc_conn)

        # Build FK graph (for QueryOptimizer)
        fk_graph = {}  # child_table -> {child_col: {parent_table, parent_col}}
        if fks:
            for fk in fks:
                child = fk["CHILD_TABLE"]
                child_col = fk["CHILD_COLUMN"]
                parent = fk["PARENT_TABLE"]
                parent_col = fk["PARENT_COLUMN"]
                if child not in fk_graph:
                    fk_graph[child] = {}
                fk_graph[child][child_col] = {"parent_table": parent, "parent_column": parent_col}

        # Also build reverse index (parent -> list of children)
        fk_graph_reversed = {}
        for child, cols in fk_graph.items():
            for child_col, parent_info in cols.items():
                parent = parent_info["parent_table"]
                if parent not in fk_graph_reversed:
                    fk_graph_reversed[parent] = {}
                fk_graph_reversed[parent][child] = {"on_column": child_col, "parent_column": parent_info["parent_column"]}

        # Display FK table in markdown
        if fks:
            lines.append("## 外键关系\n")
            lines.append("| 子表 | 子表字段 | 父表 | 父表字段 |")
            lines.append("|------|---------|------|---------|")
            for fk in fks:
                lines.append(
                    f"| {fk['CHILD_TABLE']} | {fk['CHILD_COLUMN']} | "
                    f"{fk['PARENT_TABLE']} | {fk['PARENT_COLUMN']} |"
                )
            lines.append("")

        # ── 4. Primary keys ──
        check_timeout()
        print(f"[{elapsed():.1f}s] Fetching primary keys...", file=sys.stderr)
        pk_query = """
        SELECT c.TABLE_NAME, c.COLUMN_NAME, c.POSITION
        FROM USER_CONS_COLUMNS c
        JOIN USER_CONSTRAINTS cons ON c.CONSTRAINT_NAME = cons.CONSTRAINT_NAME
        WHERE cons.CONSTRAINT_TYPE = 'P'
        ORDER BY c.TABLE_NAME, c.POSITION
        """
        pks = _oracle_exec(conn, pk_query, jdbc_conn)
        if pks:
            lines.append("## 主键\n")
            lines.append("| 表名 | 字段 | 位置 |")
            lines.append("|------|------|------|")
            cur_tbl = None
            pk_cols = []
            for pk in pks:
                if pk["TABLE_NAME"] != cur_tbl:
                    if pk_cols:
                        lines.append(f"| {cur_tbl} | {', '.join(pk_cols)} | - |")
                    cur_tbl = pk["TABLE_NAME"]
                    pk_cols = []
                pk_cols.append(pk["COLUMN_NAME"])
            if pk_cols:
                lines.append(f"| {cur_tbl} | {', '.join(pk_cols)} | - |")
            lines.append("")

        # ── 4. Build structured metadata (for QueryOptimizer) ──
        # Build pk_map from pks
        pk_map = {}
        if pks:
            for pk in pks:
                t = pk["TABLE_NAME"]
                if t not in pk_map:
                    pk_map[t] = []
                pk_map[t].append(pk["COLUMN_NAME"])

        # Build tables_metadata from previous column queries
        tables_metadata = {}
        for t in tables:
            tbl = t["TABLE_NAME"]
            tables_metadata[tbl] = {
                "columns": [],  # filled below
                "pk": pk_map.get(tbl, []),
            }

        col_meta_query = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE, NULLABLE
        FROM USER_TAB_COLUMNS
        ORDER BY TABLE_NAME, COLUMN_ID
        """
        all_cols = _oracle_exec(conn, col_meta_query, jdbc_conn)
        col_map = {}
        for row in all_cols:
            t = row["TABLE_NAME"]
            if t not in col_map:
                col_map[t] = []
            col_map[t].append(row["COLUMN_NAME"])
            if t in tables_metadata:
                tables_metadata[t]["columns"] = col_map.get(t, [])

        # JSON data block
        import json as _json
        schema_json = {
            "schema_name": alias,
            "db_type": "oracle",
            "tables": tables_metadata,
            "fk_graph": fk_graph,
            "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        lines.append("")
        lines.append("<!--")
        lines.append("```json")
        lines.append(_json.dumps(schema_json, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("-->")

        # ── Write to file ──
        schema_file = os.path.join(MEMORY_DIR, f"schema_{alias.replace(' ', '_').replace('/', '_')}.md")
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(schema_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        total = time.time() - start_time
        print(f"[{total:.1f}s] Done! Schema written to {schema_file}", file=sys.stderr)
        return schema_file

    finally:
        jdbc_conn.close()


# ── MySQL Discovery ─────────────────────────────────────────────────────────

def _run_mysql_query(query_sql: str, conn: dict) -> list[dict]:
    import jaydebeapi

    jar_dir = os.path.join(SKILL_DIR, "lib")
    jar_path = os.path.join(jar_dir, "mysql-connector-java.jar")
    if not os.path.exists(jar_path):
        raise RuntimeError(f"MySQL JDBC driver not found: {jar_path}")

    jdbc_driver = "com.mysql.cj.jdbc.Driver"
    jdbc_url = conn["jdbc_url"]

    conn_jdbc = jaydebeapi.connect(jdbc_driver, jdbc_url, [], jar_path)
    try:
        cur = conn_jdbc.cursor()
        cur.execute(query_sql)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, [_safe(v) for v in row])) for row in rows]
    finally:
        conn_jdbc.close()


def discover_mysql(conn: dict, timeout_sec: int = 60) -> str:
    """
    Discover all table DDL + comments for a MySQL connection.
    Writes to memory/schema_<alias>.md and returns the path.
    """
    alias = conn["alias"]
    start_time = time.time()

    def elapsed():
        return time.time() - start_time

    def check_timeout():
        if elapsed() > timeout_sec:
            raise TimeoutError(f"Schema discovery 超时（{timeout_sec}s），已停止。")

    db_name = conn.get("jdbc_url", "").split("/")[-1].split("?")[0]
    lines = []
    lines.append(f"# Schema: {alias} (MySQL)\n")
    lines.append(f"**数据库:** `{db_name}`")
    lines.append(f"**用户:** `{conn['user']}`")
    lines.append(f"**发现时间:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")

    # Table list
    check_timeout()
    print(f"[{elapsed():.1f}s] Fetching table list...", file=sys.stderr)
    tables_query = f"""
    SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = '{db_name}'
    ORDER BY TABLE_ROWS DESC
    """
    tables = _run_mysql_query(tables_query, conn)

    lines.append("## 表清单\n")
    lines.append("| 表名 | 行数(估) | 注释 |")
    lines.append("|------|----------|------|")
    for t in tables:
        rows = t.get("TABLE_ROWS") or "?"
        comment = _safe(t.get("TABLE_COMMENT", ""))
        lines.append(f"| {t['TABLE_NAME']} | {rows} | {comment} |")
    lines.append("")

    # Column details
    check_timeout()
    print(f"[{elapsed():.1f}s] Fetching column details...", file=sys.stderr)
    lines.append("## 表结构详情\n")

    for i, t in enumerate(tables):
        check_timeout()
        tbl = t["TABLE_NAME"]
        print(f"[{elapsed():.1f}s]  [{i+1}/{len(tables)}] Processing {tbl}...", file=sys.stderr)

        col_query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, COLUMN_KEY,
               COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{tbl}'
        ORDER BY ORDINAL_POSITION
        """
        cols = _run_mysql_query(col_query, conn)
        if not cols:
            continue

        table_comment = _safe(t.get("TABLE_COMMENT", ""))
        lines.append(f"### {tbl}")
        if table_comment:
            lines.append(f"**注释:** {table_comment}")
        lines.append("")
        lines.append("| 字段名 | 类型 | 可空 | 主键 | 注释 |")
        lines.append("|--------|------|------|------|------|")
        for c in cols:
            dtype = _safe(c.get("DATA_TYPE", ""))
            charmax = c.get("CHARACTER_MAXIMUM_LENGTH")
            numprec = c.get("NUMERIC_PRECISION")
            numscale = c.get("NUMERIC_SCALE")
            nullable = "N" if _safe(c.get("IS_NULLABLE", "")) == "NO" else "Y"
            pk = "PK" if _safe(c.get("COLUMN_KEY", "")) == "PRI" else ""
            comment = _safe(c.get("COLUMN_COMMENT", ""))

            if charmax:
                dtype_full = f"{dtype}({charmax})"
            elif numprec:
                dtype_full = f"{dtype}({numprec}"
                if numscale:
                    dtype_full += f",{numscale}"
                dtype_full += ")"
            else:
                dtype_full = dtype

            lines.append(f"| {c['COLUMN_NAME']} | {dtype_full} | {nullable} | {pk} | {comment} |")
        lines.append("")

    # ── FK discovery (MySQL) ──
    check_timeout()
    print(f"[{elapsed():.1f}s] Fetching foreign keys...", file=sys.stderr)
    fk_query = f"""
    SELECT TABLE_NAME AS CHILD_TABLE, COLUMN_NAME AS CHILD_COLUMN,
           REFERENCED_TABLE_NAME AS PARENT_TABLE,
           REFERENCED_COLUMN_NAME AS PARENT_COLUMN
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = '{db_name}'
      AND REFERENCED_TABLE_NAME IS NOT NULL
    ORDER BY TABLE_NAME
    """
    fks = _run_mysql_query(fk_query, conn)

    fk_graph = {}
    if fks:
        for fk in fks:
            child = fk["CHILD_TABLE"]
            child_col = fk["CHILD_COLUMN"]
            parent = fk["PARENT_TABLE"]
            parent_col = fk["PARENT_COLUMN"]
            if child not in fk_graph:
                fk_graph[child] = {}
            fk_graph[child][child_col] = {"parent_table": parent, "parent_column": parent_col}

        lines.append("## 外键关系\n")
        lines.append("| 子表 | 子表字段 | 父表 | 父表字段 |")
        lines.append("|------|---------|------|---------|")
        for fk in fks:
            lines.append(
                f"| {fk['CHILD_TABLE']} | {fk['CHILD_COLUMN']} | "
                f"{fk['PARENT_TABLE']} | {fk['PARENT_COLUMN']} |"
            )
        lines.append("")

    # ── Build structured metadata (for QueryOptimizer) ──
    tables_metadata = {}
    for t in tables:
        tbl = t["TABLE_NAME"]
        tables_metadata[tbl] = {"columns": [], "pk": []}

    col_meta_query = f"""
    SELECT TABLE_NAME, COLUMN_NAME, COLUMN_KEY
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{db_name}'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    all_cols = _run_mysql_query(col_meta_query, conn)
    col_map = {}
    pk_map = {}
    for row in all_cols:
        t = row["TABLE_NAME"]
        if t not in col_map:
            col_map[t] = []
        col_map[t].append(row["COLUMN_NAME"])
        if row.get("COLUMN_KEY") == "PRI":
            if t not in pk_map:
                pk_map[t] = []
            pk_map[t].append(row["COLUMN_NAME"])
        if t in tables_metadata:
            tables_metadata[t]["columns"] = col_map.get(t, [])
            tables_metadata[t]["pk"] = pk_map.get(t, [])

    # JSON data block
    import json as _json
    schema_json = {
        "schema_name": alias,
        "db_type": "mysql",
        "tables": tables_metadata,
        "fk_graph": fk_graph,
        "discovered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    lines.append("")
    lines.append("<!--")
    lines.append("```json")
    lines.append(_json.dumps(schema_json, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("-->")

    schema_file = os.path.join(MEMORY_DIR, f"schema_{alias.replace(' ', '_').replace('/', '_')}.md")
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    elapsed = time.time() - start_time
    print(f"[{elapsed:.1f}s] Done! Schema written to {schema_file}", file=sys.stderr)
    return schema_file


if __name__ == "__main__":
    print("schema_discovery.py is a module, not run directly.")
