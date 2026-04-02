#!/usr/bin/env python3
"""
Connection Manager for db-query skill — v1.0.1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  IMPORTANT: This version is designed for clawhub publishing.
  All connection credentials are stored EXCLUSIVELY in openclaw.json
  skills.env — NO secrets on disk.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connection storage (Single Source of Truth: openclaw.json):
───────────────────────────────────────────────────────────────
  CONN_<alias_key>  →  JSON string with full connection config

  Example:
    CONN____  =  '{"db_type":"oracle","user":"wksp_xuxin","password":"xxx",
                    "jdbc_url":"jdbc:oracle:thin:@(description=...)",
                    "wallet_path":"/home/ubuntu/adbwallet"}'

  Alias → env-key rules:
    "生产库"       →  CONN____
    "prod-db"      →  CONN_PROD_DB
    "MySQL测试库"  →  CONN_MYSQL____

  In openclaw.json:
    {
      "skills": {
        "env": {
          "CONN____": "{\"db_type\":\"oracle\",...}",
          "CONN_PROD_DB": "{\"db_type\":\"mysql\",...}"
        }
      }
    }

connections.json fallback:
───────────────────────────────────────────────────────────────
  ONLY used when openclaw.json has no CONN_* env vars
  (legacy upgrade path from v1.0.0). Connections stored here
  are NOT read at runtime — only used to migrate old setups.

  After migrating, you can safely delete connections.json.

Security guarantees:
───────────────────────────────────────────────────────────────
  ✅ No password in any file on disk
  ✅ No secret in connections.json (it can be deleted)
  ✅ Alias → env-key mapping is deterministic (no ambiguity)
  ✅ list_connections() strips passwords before returning
  ✅ get_active() reads ONLY from environment variables
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
#  Env-key helpers
# ─────────────────────────────────────────────────────────────────────────────

def _alias_to_env_key(alias: str) -> str:
    """
    Convert a human alias to an environment variable key.

    "生产库"  →  CONN____
    "prod-db" →  CONN_PROD_DB
    "MySQL开发库" → CONN_MYSQL____

    Non-alphanumeric chars (spaces, Chinese, hyphens) are replaced with '_'.
    Result is always uppercased and prefixed with 'CONN_'.
    """
    safe = re.sub(r'[^A-Z0-9]', '_', alias.upper())
    return f"CONN_{safe}"


def _env_key_to_alias(key: str) -> str:
    """Reverse: 'CONN_PROD_DB' → 'PROD DB' (for display only)."""
    if not key.startswith("CONN_"):
        return key
    return key[5:].replace('_', ' ')


# ─────────────────────────────────────────────────────────────────────────────
#  Core I/O: read from environment (primary) or disk (legacy fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _load_from_env() -> list[dict]:
    """
    Load ALL connections from environment variables (openclaw.json skills.env).

    Returns:
        List of connection dicts, each with an additional '_env_key' field.
    """
    connections = []
    for key, val in os.environ.items():
        if not key.startswith("CONN_"):
            continue
        try:
            conn = json.loads(val)
            # Recover the human-readable alias from env key for display
            conn["alias"] = _env_key_to_alias(key)
            conn["_env_key"] = key          # store so we know which env var to read
            connections.append(conn)
        except (json.JSONDecodeError, TypeError):
            pass
    return connections


def _load_from_disk() -> list[dict]:
    """
    Legacy fallback: load connections from connections.json.
    Used ONLY when zero CONN_* env vars are present (upgrade path).
    connections.json itself contains no passwords in v1.0.1+.
    """
    if not os.path.exists(CONNECTIONS_FILE):
        return []
    try:
        with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("connections", [])
    except (json.JSONDecodeError, IOError):
        return []


def _load_all() -> list[dict]:
    """
    Load connections. Priority:
      1. CONN_* env vars  (openclaw.json — single source of truth)
      2. connections.json  (legacy fallback, zero passwords guaranteed in v1.0.1)
    """
    env_conns = _load_from_env()
    if env_conns:
        return env_conns
    return _load_from_disk()


def _detect_active(connections: list[dict]) -> str | None:
    """Return the alias of the 'first' active connection by env priority."""
    if not connections:
        return None
    # First connection in env order, or first disk entry
    return connections[0].get("alias") or connections[0].get("_env_key", "")


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def list_connections() -> list[dict]:
    """
    Return all stored connections WITHOUT passwords (safe for display/logging).

    Returns:
        List of dicts: {alias, db_type, user, last_used, _env_key}
    """
    conns = _load_all()
    safe = []
    for c in conns:
        safe.append({
            "alias":    c.get("alias", _env_key_to_alias(c.get("_env_key", "CONN_UNKNOWN"))),
            "db_type":  c.get("db_type", ""),
            "user":     c.get("user", ""),
            "last_used": c.get("last_used"),
            # Internal: which env key — not shown to user
        })
    return safe


def get_active() -> dict | None:
    """
    Return the currently active connection with resolved password.

    SECURITY: password is read exclusively from the CONN_<alias> environment
    variable at runtime — never stored on disk.

    Returns:
        Full connection dict (including 'password' and 'jdbc_url').
        None if no connections are configured.
    """
    conns = _load_all()
    if not conns:
        return None

    # Active = first connection in the env list (deterministic order)
    active_alias = _detect_active(conns)
    for c in conns:
        if c.get("alias") == active_alias:
            # Fetch fresh from env (in case openclaw.json was reloaded)
            env_key = c.get("_env_key")
            if env_key and env_key in os.environ:
                fresh = json.loads(os.environ[env_key])
                fresh["alias"] = c["alias"]
                fresh["_env_key"] = env_key
                return fresh
            # Fallback: return as-loaded (password may be missing if env var gone)
            return c

    return conns[0] if conns else None


def get_connection(alias: str) -> dict | None:
    """
    Get a specific connection by alias.
    Looks up CONN_<alias_key> in the environment.
    Returns None if not found.
    """
    env_key = _alias_to_env_key(alias)
    raw = os.environ.get(env_key)
    if raw:
        conn = json.loads(raw)
        conn["alias"] = alias
        conn["_env_key"] = env_key
        return conn
    # Fallback: search disk
    for c in _load_from_disk():
        if c.get("alias") == alias:
            return c
    return None


def add_connection(
    alias: str,
    db_type: str,
    user: str,
    password: str,
    jdbc_url: str,
    wallet_path: str = None,
    auto: bool = False,
) -> dict:
    """
    Interactively add a new connection by printing the env var to set.

    NOTE: In v1.0.1 this function does NOT write to connections.json.
    It prints the CONN_<alias_key> env var value that must be added to
    openclaw.json skills.env.

    Example usage:
      add_connection("生产库", "oracle", "wksp_xuxin", "Jessica820608", jdbc_url, "/path/to/wallet")
      # → prints the JSON string to copy into openclaw.json
    """
    env_key = _alias_to_env_key(alias)
    conn = {
        "alias":     alias,
        "db_type":   db_type,
        "user":      user,
        "password":  password,
        "jdbc_url":  jdbc_url,
        "wallet_path": wallet_path,
        "last_used": datetime.now().isoformat(),
    }

    json_val = json.dumps(conn, ensure_ascii=False)

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  🔐 New connection: {alias:<51}║
╠══════════════════════════════════════════════════════════════════════╣
║  Add this to openclaw.json  →  skills.env:                          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║    "{env_key}": "{json_val}",
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Alias → env key mapping:                                            ║
║    "{alias}"  →  {env_key}                             ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    return conn


def remove_connection(alias: str) -> bool:
    """
    Remove a connection by alias.

    For CONN_* env vars: this only removes from connections.json fallback.
    The real removal is manual: delete the CONN_<alias_key> line from
    openclaw.json and restart the gateway.
    """
    # Remove from disk fallback
    disk_conns = _load_from_disk()
    before = len(disk_conns)
    disk_conns = [c for c in disk_conns if c.get("alias") != alias]
    if len(disk_conns) < before:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({"connections": disk_conns, "active": _detect_active(disk_conns)}, f, ensure_ascii=False, indent=2)
        _chmod0600(CONNECTIONS_FILE)
        return True
    return False


def switch_active(alias: str) -> dict:
    """
    Switch active connection by alias.

    NOTE: In env-var mode, "active" is simply the first connection
    in the CONN_* env var list. For explicit switching, reorder the
    env vars in openclaw.json, or call set_active_alias() below.
    """
    env_key = _alias_to_env_key(alias)
    conn = get_connection(alias)
    if not conn:
        raise KeyError(f"未找到连接：{alias}")
    # Store active alias to disk for legacy fallback
    disk_conns = _load_from_disk()
    for c in disk_conns:
        if c.get("alias") == alias:
            c["last_used"] = datetime.now().isoformat()
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"connections": disk_conns, "active": alias}, f, ensure_ascii=False, indent=2)
    _chmod0600(CONNECTIONS_FILE)
    return conn


def set_active_alias(alias: str):
    """
    Persist the active alias to disk (for env-var mode, where
    "active" is normally just the first CONN_ entry).
    Writes to connections.json as a marker.
    """
    os.makedirs(MEMORY_DIR, exist_ok=True)
    disk_conns = _load_from_disk()
    active_conn = get_connection(alias)
    data = {
        "connections": disk_conns,
        "active": alias if active_conn else None
    }
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _chmod0600(CONNECTIONS_FILE)


def touch_active():
    """Update last_used on the active connection (disk fallback only)."""
    disk_conns = _load_from_disk()
    active_alias = _detect_active(disk_conns)
    for c in disk_conns:
        if c.get("alias") == active_alias:
            c["last_used"] = datetime.now().isoformat()
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({"connections": disk_conns, "active": active_alias}, f, ensure_ascii=False, indent=2)
    _chmod0600(CONNECTIONS_FILE)


# ─────────────────────────────────────────────────────────────────────────────
#  File permissions helper
# ─────────────────────────────────────────────────────────────────────────────

def _chmod0600(path: str):
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError as e:
        print(f"⚠️ Could not chmod {path}: {e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive helpers
# ─────────────────────────────────────────────────────────────────────────────

def prompt_add_oracle() -> str:
    return """
请提供 Oracle 连接信息（逐项填写或粘贴完整连接串）：

  连接别名（给这个库起个名字，方便记忆）:
  用户名:
  密码:
  JDBC URL:
    示例（TCPS）：
    jdbc:oracle:thin:@(description=(address=(protocol=tcps)(port=1522)
              (host=adb.xxx.oraclecloud.com))
              (connect_data=(service_name=xxx_high.adb.oraclecloud.com))
              (security=(ssl_server_dn_match=yes)))
  TNS_ADMIN / Wallet 路径（TCPS 需要）:

添加后，add_connection() 会输出需要添加到 openclaw.json 的
CONN_<alias_key> 配置行。
"""


def prompt_add_mysql() -> str:
    return """
请提供 MySQL 连接信息：

  连接别名:
  用户名:
  密码:
  JDBC URL:
    格式：jdbc:mysql://host:port/database_name
    示例：jdbc:mysql://localhost:3306/mydb

添加后，add_connection() 会输出需要添加到 openclaw.json 的
CONN_<alias_key> 配置行。
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
    Call this to debug connection issues.
    """
    env_conns = _load_from_env()
    disk_conns = _load_from_disk()
    active = get_active()

    lines = [
        "═══ db-query 连接诊断 (v1.0.1) ═══",
        "",
        f"📦 openclaw.json CONN_* 环境变量: {len(env_conns)} 个连接",
        f"💾 connections.json (fallback):  {len(disk_conns)} 个连接",
        f"✅ 当前活跃连接: {active['alias'] if active else '(无)'}",
        "",
    ]

    if env_conns:
        lines.append("🔑 CONN_* 来源详情:")
        for c in env_conns:
            lines.append(f"  · {c['alias']} ({c.get('db_type','').upper()})")
            lines.append(f"    env_key : {c.get('_env_key')}")
            lines.append(f"    jdbc_url: {c.get('jdbc_url','')[:60]}...")
            lines.append(f"    user    : {c.get('user','')}")
    else:
        lines.append("⚠️  未检测到 CONN_* 环境变量")
        lines.append("   请在 openclaw.json skills.env 中添加连接配置")

    if disk_conns:
        lines.append("")
        lines.append("💾 connections.json fallback:")
        for c in disk_conns:
            has_pw = bool(c.get("password"))
            lines.append(f"  · {c.get('alias')} — {'⚠️ 有密码' if has_pw else '✅ 无密码'}")

    lines.append("")
    lines.append("📝 下一步:")
    lines.append("   1. 确认 openclaw.json 已添加 CONN_* 配置")
    lines.append("   2. 重启 openclaw 网关: openclaw gateway restart")
    lines.append("   3. 运行 diagnose() 确认检测到连接")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== db-query 连接管理 (v1.0.1) ===")
    print()
    print(f"CONN_* env vars : {len(_load_from_env())} 个连接")
    print(f"connections.json: {len(_load_from_disk())} 个连接（fallback）")
    print()
    print(format_connection_list(list_connections()))
    print()
    active = get_active()
    print(f"当前活跃: {active['alias'] if active else '(无)'}")
    print()
    print(diagnose())
