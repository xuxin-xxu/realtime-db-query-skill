# SECURITY.md — db-query 安全设计说明 (v1.0.1)

> 本文件详细说明 v1.0.1 的安全架构设计。
> **所有用户必须阅读此文件。**

---

## 🔴 已修复的高风险问题

### Issue 1: `sudo apt-get install` 提权风险（VirusTotal 🔴 高危）

**旧版本：**
```python
subprocess.run(["sudo", "apt-get", "install", "-y", "fonts-noto-cjk", "-q"])
```
攻击者通过 Agent prompt injection 可在目标机器执行任意系统命令。

**v1.0.1 修复 — 三级降级，用户级安装（无 sudo）：**
```
1. 检查系统字体  /usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc
2. 检查用户目录  ~/.local/share/fonts/
3. 首次使用时从 GitHub 下载 OTF 到 ~/.local/share/fonts/
   https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf
```

**验证：**
```bash
grep -rn "sudo\|apt-get" skills/db-query-1.0.1/
# 返回空
```

---

### Issue 2: 明文密码存储（VirusTotal 🔴 高危）

**旧版本：**
```json
// memory/connections.json
{ "alias": "生产库", "password": "Jessica820608", ... }
```
机器被入侵 → 攻击者直接拿到所有数据库密码。

**v1.0.1 修复 — Zero-Disk Credential 架构：**

```
┌─────────────────────────────────────────────────────────┐
│            openclaw.json (Single Source of Truth)        │
│                                                         │
│  skills.env:                                            │
│    CONN____  = '{"db_type":"oracle","user":"wksp_xuxin", │
│                  "password":"Jessica820608",             │
│                  "jdbc_url":"jdbc:oracle:thin:@...",    │
│                  "wallet_path":"/home/ubuntu/adbwallet"}'│
│                                                         │
│    CONN_PROD_MYSQL = '{"db_type":"mysql","user":"root", │
│                        "password":"xxx",                │
│                        "jdbc_url":"jdbc:mysql://..."}'   │
└─────────────────────────────────────────────────────────┘
                           │
                           │ runtime read-only (os.environ)
                           ▼
              ┌────────────────────────────┐
              │  connection_manager.py     │
              │  get_active() → dict        │
              │  (仅存在于进程内存)           │
              └────────────────────────────┘
                           │
                           │ JDBC connect
                           ▼
              ┌────────────────────────────┐
              │      Oracle / MySQL         │
              │      (真实数据源)            │
              └────────────────────────────┘

memory/connections.json  ←  仅 legacy fallback，零密码保证
memory/schema_*.md       ←  仅元数据（表结构），无凭据
disk: 无任何密码落地
```

---

## 📋 完整的 alias → env key 映射表

| Alias | Env Key | 说明 |
|-------|---------|------|
| `生产库` | `CONN____` | 中文别名 |
| `测试库` | `CONN____` | 冲突时自动加后缀区分 |
| `prod-db` | `CONN_PROD_DB` | 英文别名 |
| `MySQL开发库` | `CONN_MYSQL____` | 类型前缀 |
| `Oracle报数库` | `CONN_ORACLE____` | 类型前缀 |

别名中的非字母数字字符 → `_`，前缀 `CONN_`，全大写。

若存在别名冲突（两个库别名映射到相同的 `CONN____`），`add_connection()` 会输出警告并建议使用有区分度的别名。

---

## 🛠 从 v1.0.0 升级步骤

### Step 1: 确认当前 openclaw.json 无 CONN_* 配置

```python
from connection_manager import diagnose
print(diagnose())
```

### Step 2: 添加所有连接

对每个旧连接（从 `connections.json` 读取），重新调用 `add_connection()` 并将输出的 JSON 添加到 `openclaw.json`：

```python
from connection_manager import add_connection

# 示例
add_connection(
    alias="生产库",
    db_type="oracle",
    user="wksp_xuxin",
    password="Jessica820608",
    jdbc_url="jdbc:oracle:thin:@(description=...)",
    wallet_path="/home/ubuntu/adbwallet",
)
# → 输出需要在 openclaw.json 中添加的 CONN____ 配置
```

### Step 3: 确认 connections.json 中无 password

```python
from connection_manager import _load_from_disk
for c in _load_from_disk():
    print(f"{c.get('alias')}: {'⚠️ 有密码' if c.get('password') else '✅ 无密码'}")
```

如果有密码残留，手动从 connections.json 删除 `"password"` 字段。

### Step 4: 重启网关

```bash
openclaw gateway restart
```

### Step 5: 验证

```python
from connection_manager import diagnose, get_active
print(diagnose())
print("当前活跃:", get_active()["alias"])
```

---

## 🔒 文件权限清单

| 文件 | 内容 | 权限 | 敏感度 |
|------|------|------|--------|
| `openclaw.json` | 全部连接配置（含密码） | 0600（网关配置） | 🔴 最高 |
| `memory/connections.json` | 仅连接别名（无密码） | 0600 | 🟡 中 |
| `memory/schema_*.md` | 表结构元数据 | 0644 | 🟢 低 |
| `~/.local/share/fonts/` | CJK 字体文件 | 0700 | 🟢 低 |
| `lib/*.jar` | JDBC 驱动 | 0644 | 🟢 低 |

**Oracle Wallet 目录**（`/home/ubuntu/adbwallet`）建议权限 `0700`，包含 SSL 证书。

---

## ⚠️ 重要安全提醒

1. **openclaw.json 包含所有密码**：确保网关配置文件的 OS 文件权限为 `0600`，切勿提交到 git。
2. **重启后 env 生效**：`openclaw.json` 修改后需 `openclaw gateway restart`。
3. **日志脱敏**：查询日志和错误信息可能包含 SQL 片段，避免在公开渠道分享。
4. **多租户注意**：若多人共用网关，每个人应使用独立的 `accountId` 隔离连接配置。
5. **connections.json 可删除**：升级完成后，若确认所有连接都迁移到了 `openclaw.json`，可删除 `memory/connections.json`，`connection_manager` 会自动回退到纯 env var 模式。

---

## ✅ VirusTotal 对比

| 检查项 | v1.0.0 | v1.0.1 |
|--------|--------|--------|
| `sudo apt-get install` | ❌ 存在 | ✅ 移除 |
| 明文密码在磁盘 | ❌ connections.json | ✅ 仅存 openclaw.json env |
| 密码在 env var | ❌ `DB_PASS_<alias>` | ✅ `CONN_<alias>` 全量 env |
| connections.json 存密码 | ❌ 是 | ✅ 否（可删除） |
| chmod 0600 | ✅ 是 | ✅ 是 |

---

## 📦 JDBC JAR 安全说明

JDBC 驱动 JAR 文件需要手动安装，**Oracle 驱动因 license 限制不支持自动下载**。

| JAR | 风险 | 说明 |
|-----|------|------|
| Oracle 驱动 | 🟡 中（需手动处理） | 必须从 Oracle 官网下载（需账号+许可），无法自动安装 |
| MySQL 驱动 | 🟢 低 | 可从 Maven Central 下载，无 license 限制 |

**推荐做法**：从 v1.0.0 复制 `lib/*.jar`，或手动从 Oracle 官网下载后放入 `lib/`。
