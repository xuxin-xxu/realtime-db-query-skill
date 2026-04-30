#!/usr/bin/env python3
"""
Schema Discovery for db-query skill (thin driver version).

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
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
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


def _parse_oracle_jdbc_url(jdbc_url: str) -> str:
    """Parse Oracle JDBC URL and return dsn for oracledb thin driver."""
    if not jdbc_url:
        raise ValueError("jdbc_url is required for Oracle connection")
    prefix = "jdbc:oracle:thin:@"
    if jdbc_url.startswith(prefix):
        return jdbc_url[len(prefix):]
    return jdbc_url


def _parse_mysql_jdbc_url(jdbc_url: str) -> dict:
    """Parse MySQL JDBC URL and return params for mysql.connector."""
    if not jdbc_url:
        raise ValueError("jdbc_url is required for MySQL connection")
    prefix = "jdbc:mysql://"
    if jdbc_url.startswith(prefix):
        rest = jdbc_url[len(prefix):]
    else:
        rest = jdbc_url
    if "?" in rest:
        rest = rest.split("?", 1)[0]
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
    return result


def _oracle_exec(conn: dict, query_sql: str, oracledb_conn):
    """Execute a query using an existing oracledb connection."""
    cur = oracledb_conn.cursor()
    cur.execute(query_sql)
    cols = [_safe(desc[0]) for desc in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, [_safe(v) for v in row])) for row in rows]


def _mysql_exec(conn: dict, query_sql: str, mysql_conn):
    """Execute a query using an existing mysql.connector connection."""
    cur = mysql_conn.cursor()
    cur.execute(query_sql)
    cols = [_safe(desc[0]) for desc in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, [_safe(v) for v in row])) for row in rows]


# ── Oracle Discovery ─────────────────────────────────────────────────────────

def discover_oracle(conn: dict, timeout_sec: int = 300) -> str:
    """
    Discover all table DDL + comments for an Oracle connection.
    Uses a SINGLE oracledb connection for all queries.
    Writes to memory/schema_<alias>.md and returns the path.
    """
    import oracledb

    alias = conn["alias"]
    user = conn["user"]
    password = conn["password"]
    jdbc_url = conn["jdbc_url"]
    start_time = time.time()

    def elapsed():
        return time.time() - start_time

    def check_timeout():
        if elapsed() > timeout_sec:
            raise TimeoutError(f"Schema discovery 超时（{timeout_sec}s），已停止。")

    dsn = _parse_oracle_jdbc_url(jdbc_url)

    print(f"[{elapsed():.1f}s] Connecting to Oracle ({dsn})...", file=sys.stderr)
    oracledb_conn = oracledb.connect(user=user, password=password, dsn=dsn)
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
        tables = _oracle_exec(conn, tables_query, oracledb_conn)
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
            cols = _oracle_exec(conn, col_query, oracledb_conn)
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
        fks = _oracle_exec(conn, fk_query, oracledb_conn)

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
        pks = _oracle_exec(conn, pk_query, oracledb_conn)
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

        # ── Build structured metadata ──
        pk_map = {}
        if pks:
            for pk in pks:
                t = pk["TABLE_NAME"]
                if t not in pk_map:
                    pk_map[t] = []
                pk_map[t].append(pk["COLUMN_NAME"])

        tables_metadata = {}
        for t in tables:
            tbl = t["TABLE_NAME"]
            tables_metadata[tbl] = {
                "columns": [],
                "pk": pk_map.get(tbl, []),
            }

        col_meta_query = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE, NULLABLE
        FROM USER_TAB_COLUMNS
        ORDER BY TABLE_NAME, COLUMN_ID
        """
        all_cols = _oracle_exec(conn, col_meta_query, oracledb_conn)
        col_map = {}
        for row in all_cols:
            t = row["TABLE_NAME"]
            if t not in col_map:
                col_map[t] = []
            col_map[t].append(row["COLUMN_NAME"])
            if t in tables_metadata:
                tables_metadata[t]["columns"] = col_map.get(t, [])

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
        oracledb_conn.close()


# ── MySQL Discovery ─────────────────────────────────────────────────────────

def discover_mysql(conn: dict, timeout_sec: int = 60) -> str:
    """
    Discover all table DDL + comments for a MySQL connection.
    Writes to memory/schema_<alias>.md and returns the path.
    """
    import mysql.connector

    alias = conn["alias"]
    start_time = time.time()

    def elapsed():
        return time.time() - start_time

    def check_timeout():
        if elapsed() > timeout_sec:
            raise TimeoutError(f"Schema discovery 超时（{timeout_sec}s），已停止。")

    jdbc_url = conn["jdbc_url"]
    params = _parse_mysql_jdbc_url(jdbc_url)
    db_name = params.get("database")

    config = {
        "host": params["host"],
        "port": params["port"],
        "user": conn["user"],
        "password": conn["password"],
        "database": db_name,
    }

    print(f"[{elapsed():.1f}s] Connecting to MySQL ({params['host']}:{params['port']}/{db_name})...", file=sys.stderr)
    mysql_conn = mysql.connector.connect(**config)
    print(f"[{elapsed():.1f}s] Connected!", file=sys.stderr)

    try:
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
        tables = _mysql_exec(conn, tables_query, mysql_conn)

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
            cols = _mysql_exec(conn, col_query, mysql_conn)
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
        fks = _mysql_exec(conn, fk_query, mysql_conn)

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

        # ── Build structured metadata ──
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
        all_cols = _mysql_exec(conn, col_meta_query, mysql_conn)
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

    finally:
        mysql_conn.close()


if __name__ == "__main__":
    print("schema_discovery.py is a module, not run directly.")
