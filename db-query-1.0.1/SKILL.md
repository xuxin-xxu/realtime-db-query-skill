---
name: db-query
version: 1.0.1
description: Query Oracle and MySQL databases via JDBC thin driver using natural language. Supports chart generation (bar, pie, line) with automatic Feishu image delivery. Designed for large schemas (100+ tables) with token-optimized fuzzy matching and schema caching.
---

# db-query (v1.0.1)

> **READ-ONLY 数据库查询技能** — 仅支持 SELECT/SHOW/DESCRIBE/EXPLAIN
> 支持 Oracle (TCPS/Wallet) 和 MySQL，支持多数据库连接管理和 Schema 缓存。
>
> **安全设计 (v1.0.1)**：所有凭据存储在 `openclaw.json` 的 `skills.env` 中（不上磁盘），
> 字体安装改为用户级下载（无 sudo）。

---

## 核心功能

1. **自然语言 → SQL 查询**（JDBC Thin Driver）
2. **图表生成**（直方图 / 饼图 / 折线图，自动发送到飞书）
3. **多数据库连接管理**（Oracle + MySQL，支持多连接切换）
4. **Schema 缓存**（DDL + Comment，写入 memory/，避免重复扫描）

---

## 文件结构

```
skills/db-query/
  SKILL.md                    ← 本文件
  SECURITY.md                 ← 安全设计文档（必读）
  scripts/
    oracle_query.py           ← Oracle 查询
    chart_utils.py            ← 图表生成 + Feishu 发送
    connection_manager.py     ← 连接管理（纯 env var 模式）
    schema_discovery.py        ← Schema 抓取
  memory/
    connections.json          ← 仅作 legacy fallback（不含密码）
    schema_<alias>.md         ← Schema 缓存
  lib/                        ← JDBC JAR
    ojdbc11.jar
    oraclepki.jar
    osdt_core.jar
    osdt_cert.jar
    mysql-connector-java.jar
```

---

## ⚠️ 连接配置（必须先阅读）

**所有连接配置统一放在 `openclaw.json` 的 `skills.env` 中。`connections.json` 仅为旧版兼容 fallback，不存任何凭据。**

### 添加新连接

```python
from connection_manager import add_connection

add_connection(
    alias="生产库",
    db_type="oracle",
    user="wksp_xuxin",
    password="Jessica820608",
    jdbc_url="jdbc:oracle:thin:@(description=(address=(protocol=tcps)(port=1522)...",
    wallet_path="/home/ubuntu/adbwallet",
)
```

运行后会输出需要添加到 `openclaw.json` 的配置片段，例如：

```json
{
  "skills": {
    "env": {
      "CONN____": "{\"db_type\":\"oracle\",\"user\":\"wksp_xuxin\",\"password\":\"Jessica820608\",\"jdbc_url\":\"jdbc:oracle:thin:@(description=...)\",\"wallet_path\":\"/home/ubuntu/adbwallet\"}"
    }
  }
}
```

### 多连接配置示例

```json
{
  "skills": {
    "env": {
      "CONN_PROD_ORACLE": "{\"db_type\":\"oracle\",\"user\":\"wksp_xuxin\",\"password\":\"xxx\",\"jdbc_url\":\"jdbc:oracle:thin:@(description=...)\",\"wallet_path\":\"/home/ubuntu/adbwallet\"}",
      "CONN_DEV_MYSQL": "{\"db_type\":\"mysql\",\"user\":\"root\",\"password\":\"dev123\",\"jdbc_url\":\"jdbc:mysql://localhost:3306/test\"}",
      "CONN_REPORT_ORACLE": "{\"db_type\":\"oracle\",\"user\":\"rpt_user\",\"password\":\"xxx\",\"jdbc_url\":\"jdbc:oracle:thin:@...\",\"wallet_path\":\"/home/ubuntu/adbwallet\"}"
    }
  }
}
```

### Alias → Env Key 映射规则

| Alias | Env Key |
|-------|---------|
| `生产库` | `CONN____` |
| `prod-db` | `CONN_PROD_DB` |
| `MySQL测试库` | `CONN_MYSQL____` |
| `Oracle报数库` | `CONN_ORACLE____` |

规则：非字母数字字符 → `_`，前缀 `CONN_`，全大写。

### 切换活跃连接

```python
from connection_manager import switch_active, get_active

# 切换到指定连接
switch_active("MySQL测试库")

# 查看当前活跃连接
print(get_active()["alias"])
```

### 诊断连接状态

```python
from connection_manager import diagnose
print(diagnose())
```

---

## Schema 缓存机制

### 首次使用：自动发现 Schema

```python
from schema_discovery import discover_oracle, discover_mysql

discover_oracle(get_active())   # 写入 memory/schema_生产库.md
discover_mysql(get_active())    # 写入 memory/schema_<alias>.md
```

### Schema 文件内容

```markdown
# Schema: 生产库 (Oracle)
**用户:** `wksp_xuxin`
**发现时间:** `2026-04-01 14:09:25`

## 表清单
| 表名 | 行数 | 注释 |
|------|------|------|
| EMP | 14 | 员工表 |

## 表结构详情
### EMP
| 字段名 | 类型 | 可空 | 注释 |
|--------|------|------|------|
| EMPNO | NUMBER(4) | N | 主键 |
```

---

## 查询流程

```
Step 1：读取 openclaw.json CONN_* 环境变量
  └── 无连接 → 提示用 add_connection()

Step 2：从 CONN_<alias> 获取连接配置
  └── get_active() → jdbc_url + user + password（仅内存）

Step 3：检查 memory/schema_<alias>.md
  └── 有缓存 → 直接加载
  └── 无 → 询问是否执行 discover

Step 4：Schema 模糊匹配（≤60s）

Step 5：SQL 安全检查
  · 无 WHERE + 表行数 >10万 → 拒绝
  · 自动追加 FETCH FIRST 100 ROWS

Step 6：执行 + 返回
  · 表格 → format_results()
  · 图表 → render_bar_chart(send_to_feishu=True)
```

---

## 图表功能

```python
from chart_utils import render_bar_chart, render_pie_chart, render_line_chart

render_bar_chart(
    labels=["会计(北京)", "研发(深圳)", "销售(上海)"],
    values=[2916.67, 2175.0, 1566.67],
    title="各部门平均工资排名",
    ylabel="平均工资 (CNY)",
    sort_desc=True,
    send_to_feishu=True,
)
```

**字体**：优先用系统字体，缺失时从 GitHub 下载到 `~/.local/share/fonts/`（**无 sudo**）。

---

## 安全规则

| 规则 | 说明 |
|------|------|
| 只读强制 | INSERT/UPDATE/DELETE/DROP 等全部拒绝 |
| 大表保护 | 无 WHERE + 表行数 >10万 → 拒绝 |
| LIMIT 强制 | 自动追加 `FETCH FIRST 100 ROWS` |
| 深分页拒绝 | 禁止 `OFFSET N`（N>1000） |
| 密码不落地 | 全部存在 `openclaw.json` env，运行时读入内存 |
| 无 sudo 字体 | 字体下载到 `~/.local/share/fonts/` |

---

## 迁移指南（从 v1.0.0 升级）

### 1. 导出旧连接

```python
from connection_manager import list_connections
print(list_connections())
```

### 2. 重新添加（通过 openclaw.json）

对每个旧连接运行：

```python
from connection_manager import add_connection
add_connection(alias="生产库", db_type="oracle", user="wksp_xuxin",
               password="Jessica820608",
               jdbc_url="jdbc:oracle:thin:@(description=...)",
               wallet_path="/home/ubuntu/adbwallet")
# 复制输出的 JSON 到 openclaw.json
```

### 3. 重启网关

```bash
openclaw gateway restart
```

### 4. 验证

```python
from connection_manager import diagnose, get_active
print(diagnose())
print(get_active()["alias"])
```

---

## 📦 JDBC 驱动安装 / JDBC Driver Installation

**⚠️ `lib/` 目录下的 JAR 文件需要手动安装**，Oracle 驱动因 license 限制不支持自动下载。

**⚠️ JDBC JAR files in `lib/` must be installed manually** — Oracle drivers cannot be auto-downloaded due to license restrictions.

### 所需 JAR 文件 / Required JARs

| JAR | 来源 / Source | 下载地址 / Download URL |
|-----|--------------|------------------------|
| `ojdbc11.jar` | Oracle（需登录账号） | https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html |
| `oraclepki.jar` | Oracle（需登录账号） | 同上 / Same page |
| `osdt_core.jar` | Oracle（需登录账号） | 同上 / Same page |
| `osdt_cert.jar` | Oracle（需登录账号） | 同上 / Same page |
| `mysql-connector-java.jar` | Maven Central（免费） | https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar |

### 安装方式 / Installation Methods

**方式 A（推荐）：从 v1.0.0 复制 / From v1.0.0 (recommended if upgrading）**

```bash
cp /home/ubuntu/.openclaw/workspace_mayu/skills/db-query/lib/*.jar \
   /home/ubuntu/.openclaw/workspace_mayu/skills/db-query-1.0.1/lib/
```

**方式 B：手动下载 Oracle 驱动 / Manual Oracle driver download**

1. 访问 https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html
2. 使用 Oracle 账号登录并接受许可协议
3. 下载 `ojdbc11.jar`, `oraclepki.jar`, `osdt_core.jar`, `osdt_cert.jar`
4. 放入 `skills/db-query-1.0.1/lib/`

**方式 C：下载 MySQL 驱动 / Download MySQL driver**

```bash
curl -o /home/ubuntu/.openclaw/workspace_mayu/skills/db-query-1.0.1/lib/mysql-connector-java.jar \
  "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar"
```

### 验证 / Verification

```bash
ls -la /home/ubuntu/.openclaw/workspace_mayu/skills/db-query-1.0.1/lib/
# 应包含: ojdbc11.jar  oraclepki.jar  osdt_core.jar  osdt_cert.jar  mysql-connector-java.jar
```

---

## 当前已配置

- **生产库** (Oracle ADB, TCPS)
  - Env Key: `CONN____`
  - 用户: `wksp_xuxin`
  - Schema 已缓存: `memory/schema_生产库.md`
  - JAR 驱动: `lib/`（需手动安装，见上方说明）
