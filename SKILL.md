---
name: db-query
version: 1.1.0
description: Query Oracle and MySQL databases via JDBC thin driver using natural language. Supports chart generation (bar, pie, line) with native Markdown image delivery. Designed for large schemas (100+ tables) with token-optimized fuzzy matching and schema caching.
---

# db-query (v1.1)

> **READ-ONLY 数据库查询技能** — 仅支持 SELECT/SHOW/DESCRIBE/EXPLAIN
> 支持 Oracle (TCPS/Wallet) 和 MySQL，支持多数据库连接管理和 Schema 缓存。
>
> **安全设计与交互式配置 (v1.1)**：所有凭据存储在 `openclaw.json` 的 `skills.env` 中（不上磁盘）。新增了 `install.py` 引导程序完成环境全自动无痛沙盒安装。

---

## 核心功能

1. **自然语言 → SQL 查询**（JDBC Thin Driver）
2. **图表生成**（直方图 / 饼图 / 折线图，基于 Markdown 的动态原窗渲染）
3. **多数据库连接管理**（Oracle + MySQL，支持多连接切换）
4. **Schema 缓存**（DDL + Comment，写入 memory/，避免重复扫描）

---

## 文件结构

```
skills/db-query/
  install.py                  ← [NEW] 安装向导程序
  SKILL.md                    ← 本文件
  SECURITY.md                 ← 安全设计文档（必读）
  scripts/
    db_query.py               ← 统一个各种数据库引擎的查询入口
    chart_utils.py            ← 图表生成引擎 (渲染本地图片供 Agent 提取)
    connection_manager.py     ← 连接管理（纯 env var 模式）
    schema_discovery.py        ← Schema 抓取
  memory/
    connections.json          ← 仅作 legacy fallback（不含密码）
    schema_<alias>.md         ← Schema 缓存
  lib/                        ← JDBC JAR存放目录
    ojdbc11.jar / mysql-connector-java.jar 等等
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

## 🧠 交互与查询意图处理守则 (Agent 指令)

作为 OpenClaw 服务大模型，你在承接用户的查询意图时，**必须严格遵守**一下两步前置检查逻辑：

**Step 1（零连接强制询问）：检查配置**
- 在执行任何查询之前，必须先调用 `connection_manager.list_connections()` 探测系统中存在的数据库连接环境。
- 如果返回为空 (0 个连接)：立刻停止任何解析，原生回复用户：“抱歉，因为系统中尚未配置任何数据库连接信息，我无法为您查询。请您告诉我您的数据库连接详情，包含：1. 数据库类型(oracle 或 mysql) 2. 连接地址(JDBC URL 或 主机/端口) 3. 登录用户名 4. 登录密码。如果您使用的是需要 Wallet 鉴权的 Oracle TCPS 数据库，还需要告诉我 Wallet 的绝对路径。” 待用户提供完整后，你再根据提供的内容调用 `add_connection` 或组装设置。

**Step 2（多源库会话锁定）：多连接提示**
- 每次一个新的用户查询意图出现时（代表一个新的对话），如果你通过 `list_connections()` 发现存在**超过 1 个**的数据库连接 alias，并且用户并未在要求中明确说明用哪个库。
- **你必须立刻停下，向用户列出所有的数据库别名（Alias）清单，询问用户这次要查询哪个库。**
- 一旦用户做出了选定，在此后同一个连续的会话周期里，除非用户主动要求更换，否则不管用户追问任何问题，你**必须**在调用 `db_query.query(..., alias="用户选择的别名")` 时，锁死并永远挂带这个 alias 参数（不要用默认的 `get_active()`），直到用户进入下个无上下文的新会话。

---

## 查询内部底层执行流

```
Step 1：执行 db_query.query(..., alias=...)
  └── 未传入 alias 则底层读取当前内存中排第一的默认项

Step 2：检查 memory/schema_<alias>.md
  └── 有缓存 → 自动载入
  └── 无缓存 → 让用户等待，后台主动执行 discover 抓取 Schema

Step 3：Schema 结合用户问题生成 SQL 并拦截异常
  · 无 WHERE + 预测表行数 >10万 → 拦截并拒绝执行，保护内存
  · 默认自动追加 FETCH FIRST 100 ROWS 保护展示

Step 4：执行并渲染结果
  · 表格类结果 → 走 format_results() 函数输出 Markdown 表单
  · 图表类需求 → 自动调用 render_bar_chart() 等生成图表。随后，你必须用 Markdown 的图像语法返回产出的绝对路径，例如 `![统计图表](/Users/.../chart.png)`，OpenClaw 底层接管并负责将其发送到对应的用户窗。
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
    sort_desc=True
)

# 生成图片后，Agent 直接返回： ![各部门工资](/your/absolute/path/bar_chart.png)
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

---

## 📦 新版本特性：环境快速安装导览 (v1.1 新增)

直接在 `db-query` 的根目录下执行：
```bash
python install.py
```
这将会启动交互式的向导，它可以：
1. **自动为您检测 Java 版本**，如果不满足要求，它将在用户安全隔离沙箱内自动安装。对于 Mac，采用轻量安全的 `pip install install-jdk` 无感化下载。对于 Linux 则会自动尝试包管理器 `apt-get` 等等，绝不侵染原有内核。
2. **自动探测和下载所需 JDBC Jar 依赖** 且存放在本目录内的 `lib/` 夹下。告别过去复杂的下载链接。

---

## 当前已配置

- **生产库** (Oracle ADB, TCPS)
  - Env Key: `CONN____`
  - 用户: `wksp_xuxin`
  - Schema 已缓存: `memory/schema_生产库.md`
  - JAR 驱动: `lib/`（需手动安装，见上方说明）
