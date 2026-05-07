#!/usr/bin/env python3
"""
Connection Manager for db-query skill — v2.1 (thin driver).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  IMPORTANT: Connection credentials are now stored in memory/connections.json
  Uses Python thin drivers (oracledb / mysql-connector-python).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connection storage:
───────────────────────────────────────────────────────────────
  memory/connections.json  →  JSON file with full connection configs
  
  File permissions will be automatically locked to 0600.
"""

import json
import os
import re
import stat
import sys
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(SKILL_DIR, "memory")
CONNECTIONS_FILE = os.path.join(MEMORY_DIR, "connections.json")

# ─────────────────────────────────────────────────────────────────────────────
#  File permissions helper
# ─────────────────────────────────────────────────────────────────────────────

def _chmod0600(path: str):
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError as e:
        print(f"⚠️ Could not chmod {path}: {e}", file=sys.stderr)

# ─────────────────────────────────────────────────────────────────────────────
#  Core I/O
# ─────────────────────────────────────────────────────────────────────────────

def _load_all() -> list:
    """
    Load connections from connections.json.
    """
    if not os.path.exists(CONNECTIONS_FILE):
        return []
    try:
        with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("connections", [])
    except (json.JSONDecodeError, IOError):
        return []

def _save_all(connections: list, active_alias: any = None):
    """
    Save connections to connections.json.
    """
    os.makedirs(MEMORY_DIR, exist_ok=True)
    data = {
        "connections": connections,
        "active": active_alias
    }
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _chmod0600(CONNECTIONS_FILE)

def _detect_active(connections: list) -> any:
    """Return the alias of the active connection by disk marker."""
    if not connections:
        return None
        
    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                active_alias = data.get("active")
                if active_alias and any(c.get("alias") == active_alias for c in connections):
                    return active_alias
        except (json.JSONDecodeError, IOError):
            pass

    return connections[0].get("alias")

# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def list_connections() -> list:
    """
    Return all stored connections WITHOUT passwords (safe for display/logging).
    """
    conns = _load_all()
    safe = []
    for c in conns:
        safe.append({
            "alias":     c.get("alias", "UNKNOWN"),
            "db_type":   c.get("db_type", ""),
            "user":      c.get("user", ""),
            "host":      c.get("host", ""),
            "port":      c.get("port", ""),
            "database":  c.get("database", ""),
            "last_used": c.get("last_used"),
        })
    return safe

def get_active() -> any:
    """
    Return the currently active connection with resolved password.
    """
    conns = _load_all()
    if not conns:
        return None

    active_alias = _detect_active(conns)
    for c in conns:
        if c.get("alias") == active_alias:
            return c

    return conns[0] if conns else None

def get_connection(alias: str) -> any:
    """
    Get a specific connection by alias.
    """
    for c in _load_all():
        if c.get("alias") == alias:
            return c
    return None

def add_connection(
    alias: str,
    db_type: str,
    user: str,
    password: str,
    host: str,
    port: int,
    database: str,
    wallet_path: str = None,
    auto: bool = False,
) -> dict:
    """
    Add a new connection and save it to memory/connections.json.
    """
    conns = _load_all()
    
    # Remove existing with same alias
    conns = [c for c in conns if c.get("alias") != alias]
    
    conn = {
        "alias":       alias,
        "db_type":     db_type,
        "user":        user,
        "password":    password,
        "host":        host,
        "port":        port,
        "database":    database,
        "wallet_path": wallet_path,
        "last_used":   datetime.now().isoformat(),
    }
    
    conns.append(conn)
    _save_all(conns, alias)  # Make the newly added connection active
    
    print(f"✅ Connection '{alias}' saved securely to memory/connections.json")
    return conn

def remove_connection(alias: str) -> bool:
    """
    Remove a connection by alias.
    """
    conns = _load_all()
    before = len(conns)
    conns = [c for c in conns if c.get("alias") != alias]
    if len(conns) < before:
        _save_all(conns, _detect_active(conns))
        return True
    return False

def switch_active(alias: str) -> dict:
    """
    Switch active connection by alias.
    """
    conn = get_connection(alias)
    if not conn:
        raise KeyError(f"未找到连接：{alias}")
    
    conns = _load_all()
    for c in conns:
        if c.get("alias") == alias:
            c["last_used"] = datetime.now().isoformat()
            
    _save_all(conns, alias)
    return conn

def set_active_alias(alias: str):
    """
    Persist the active alias to disk.
    """
    conns = _load_all()
    _save_all(conns, alias)

def touch_active():
    """Update last_used on the active connection."""
    conns = _load_all()
    active_alias = _detect_active(conns)
    for c in conns:
        if c.get("alias") == active_alias:
            c["last_used"] = datetime.now().isoformat()
    _save_all(conns, active_alias)


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive helpers
# ─────────────────────────────────────────────────────────────────────────────

def prompt_add_oracle() -> str:
    return """
请提供 Oracle 连接信息（逐项填写或粘贴）：

  连接别名（给这个库起个名字，方便记忆）:
  用户名:
  密码:
  主机 IP (如果是 TCPS，可直接填入完整的 DESCRIPTION 字符串):
  端口:
  数据库名/服务名:
  TNS_ADMIN / Wallet 路径（TCPS 需要）:

"""

def prompt_add_mysql() -> str:
    return """
请提供 MySQL 连接信息：

  连接别名:
  用户名:
  密码:
  主机 IP:
  端口:
  数据库名:

"""

def format_connection_list(conns: list[dict]) -> str:
    """Format a list of connections for display (no passwords)."""
    if not conns:
        return "（暂无已配置的数据库连接）\n请使用 add_connection() 添加第一个连接。"
    lines = []
    for i, c in enumerate(conns, 1):
        last = c.get("last_used") or "从未使用"
        lines.append(
            f"  [{i}] {c['alias']} "
            f"({c.get('db_type','?').upper()}, "
            f"用户: {c.get('user','?')}, "
            f"上次: {last})"
        )
    return "\n".join(lines)

def diagnose() -> str:
    """
    Print a diagnostic report of current connection configuration.
    """
    conns = _load_all()
    active = get_active()

    lines = [
        "═══ db-query 连接诊断 (v2.1 thin driver) ═══",
        "",
        f"💾 memory/connections.json:  {len(conns)} 个连接",
        f"✅ 当前活跃连接: {active['alias'] if active else '(无)'}",
        "",
    ]

    if conns:
        lines.append("🔑 本地连接详情:")
        for c in conns:
            lines.append(f"  · {c['alias']} ({c.get('db_type','').upper()})")
            lines.append(f"    host    : {c.get('host','')}")
            lines.append(f"    port    : {c.get('port','')}")
            lines.append(f"    database: {c.get('database','')}")
            lines.append(f"    user    : {c.get('user','')}")
            has_pw = bool(c.get("password"))
            lines.append(f"    密码状态: {'⚠️ 已保存' if has_pw else '✅ 无密码'}")
    else:
        lines.append("⚠️  未检测到任何连接配置")

    lines.append("")
    lines.append("📝 下一步:")
    lines.append("   1. 确认 thin driver 依赖已安装: pip install -r requirements.txt")
    lines.append("   2. 使用 add_connection() 添加连接记录")
    lines.append("   3. 运行 diagnose() 确认检测到连接")

    return "\n".join(lines)

if __name__ == "__main__":
    print("=== db-query 连接管理 (v2.1 thin driver) ===")
    print()
    print(f"connections.json: {len(_load_all())} 个连接")
    print()
    print(format_connection_list(list_connections()))
    print()
    active = get_active()
    print(f"当前活跃: {active['alias'] if active else '(无)'}")
    print()
    print(diagnose())
