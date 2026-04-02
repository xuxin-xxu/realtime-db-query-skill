# db-query README — 安全加固与安装指南

> **db-query v1.0.1** — 安全加固版本（推荐升级）
>
> 所有凭据存储在 `openclaw.json`（不上磁盘） · CJK 字体用户级安装（无 sudo）

---

## 🔐 安全变更 (v1.0.1)

| 问题 | v1.0.0 | v1.0.1 |
|------|--------|--------|
| 🔴 `sudo apt-get install` 提权风险 | 存在 | ✅ 移除，改为 GitHub 用户级下载 |
| 🔴 明文密码在 `connections.json` | 存在 | ✅ 移除，改为 `openclaw.json` env |
| 🟢 JDBC JAR 安装 | 手动 | 需手动（Oracle 驱动需接受许可） |

### v1.0.1 安全架构

```
openclaw.json skills.env          ← 凭据唯一真相源
┌──────────────────────────────────────────────┐
│  CONN____ = '{"db_type":"oracle",            │
│              "user":"xxx",                    │
│              "password":"xxx",                │
│              "jdbc_url":"...",                │
│              "wallet_path":"..."}'             │
└──────────────────────────────────────────────┘
                ↓ 运行时 os.environ
         connection_manager.py (内存中)
                ↓ JDBC
           Oracle / MySQL
```

---

## 📦 JDBC 驱动安装指南

**JDBC JAR 文件需要手动安装**，Oracle 驱动因 license 限制不支持自动下载。

### 目录结构

```
lib/
├── ojdbc11.jar              # Oracle JDBC Thin Driver (Java 21)
├── oraclepki.jar            # Oracle PKI (TCPS/Wallet)
├── osdt_core.jar            # Oracle Security Core
├── osdt_cert.jar            # Oracle Security Certificate
└── mysql-connector-java.jar  # MySQL JDBC Driver
```

### 从 v1.0.0 升级（推荐）

如果你的系统已安装 db-query v1.0.0，JAR 文件可以直接复用：

```bash
cp /home/ubuntu/.openclaw/workspace_mayu/skills/db-query/lib/*.jar \
   /home/ubuntu/.openclaw/workspace_mayu/skills/db-query-1.0.1/lib/
```

### Oracle 驱动（需 Oracle 账号）

1. 访问 [Oracle JDBC Driver 下载](https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html)
2. 下载 **JDBC Thin Driver (ojdbc11.jar)** — 需要登录 Oracle 账号并接受许可协议
3. 同时下载：
   - `oraclepki.jar`
   - `osdt_core.jar`
   - `osdt_cert.jar`
4. 放入 `skills/db-query-1.0.1/lib/`

### MySQL 驱动（可自动下载）

MySQL Connector/J 可从 Maven Central 免费下载：

```bash
curl -o lib/mysql-connector-java.jar \
  "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar"
```

---

## ⚙️ 快速安装步骤

### Step 1: 复制 / 下载 JAR 文件

```bash
# 方式 A: 从 v1.0.0 复制（推荐）
cp skills/db-query/lib/*.jar skills/db-query-1.0.1/lib/

# 方式 B: 手动下载 Oracle 驱动
# → 访问 https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html
# → 登录后下载 ojdbc11.jar, oraclepki.jar, osdt_core.jar, osdt_cert.jar

# 方式 C: 下载 MySQL 驱动
curl -o skills/db-query-1.0.1/lib/mysql-connector-java.jar \
  "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar"
```

### Step 2: 添加连接配置到 openclaw.json

```bash
openclaw config edit
```

在 `skills.env` 中添加（以"生产库"为例）：

```json
{
  "skills": {
    "env": {
      "CONN____": "{\"db_type\":\"oracle\",\"user\":\"wksp_xuxin\",\"password\":\"Jessica820608\",\"jdbc_url\":\"jdbc:oracle:thin:@(description=(address=(protocol=tcps)(port=1522)(host=adb.ca-toronto-1.oraclecloud.com))(connect_data=(service_name=gdc4bbe84a839b8_xxuclawdb_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))\",\"wallet_path\":\"/home/ubuntu/adbwallet\"}"
    }
  }
}
```

### Step 3: 重启网关

```bash
openclaw gateway restart
```

### Step 4: 验证连接

```python
from connection_manager import diagnose, get_active
print(diagnose())
print(get_active()["alias"])
```

---

## 🔑 alias → Env Key 对照表

| Alias（连接别名） | Env Key | 示例 |
|-----------------|---------|------|
| `生产库` | `CONN____` | 中文别名 |
| `测试库` | `CONN____` | 中文别名（冲突时需区分） |
| `prod-db` | `CONN_PROD_DB` | 英文别名 |
| `MySQL开发库` | `CONN_MYSQL____` | 带类型前缀 |
| `Oracle报数库` | `CONN_ORACLE____` | 带类型前缀 |

**命名建议**：使用有区分度的别名，避免多个别名映射到相同的 `CONN____`。

---

## 📁 文件权限

| 文件 | 建议权限 |
|------|---------|
| `openclaw.json` | `0600`（含密码） |
| `lib/*.jar` | `0644` |
| `memory/connections.json` | `0600`（不含密码） |
| `~/.local/share/fonts/` | `0700` |

---

## 🆘 故障排查

**Q: `Missing required JARs` 报错？**
→ 确认所有 JAR 文件已放入 `lib/` 目录，重启网关。

**Q: 连接失败 `ORA-12560`？**
→ 检查 JDBC URL 和 TNS_ADMIN 路径是否正确。

**Q: 明文密码警告？**
→ 确认 `connections.json` 中已删除 `"password"` 字段，凭据仅在 `openclaw.json` 中。

---

## 📄 相关文档

- [SKILL.md](./SKILL.md) — 功能与 API 说明
- [SECURITY.md](./SECURITY.md) — 安全设计详解
